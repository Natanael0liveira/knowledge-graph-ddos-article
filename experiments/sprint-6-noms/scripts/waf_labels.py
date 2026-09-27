#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the WAF's verdicts as labels for the scope on production traffic.

The production evaluation injects its botnets; the only malicious populations the
exports carry are the clients the operator's WAF blocked. This script takes those
verdicts as labels and scores each calibrated scope against them on the full test
windows (blocked clients included), under two profiles:

- ``clean_profile``: the rolling runs of the paper, whose profile, level and
  thresholds come from the clients the WAF did NOT block. A fingerprint the WAF
  blocks is then rare in the profile by construction, so agreement with the WAF is
  partly built in: with ratio rho, a stable fingerprint is enriched on full traffic
  only if its blocked share exceeds 1 - (1 - S)/rho, S the endpoint's blocked share;
- ``all_profile``: runs with ``--waf-in-profile``, whose profile, level and
  thresholds come from every client, blocked ones included, as a scope deployed in
  front of the WAF would see them. This is the analysis the paper reports.

Per endpoint, for each configuration of Table II (the binomial configuration, the
beta-binomial, the calibrated z-score) and for trivial filters on the same windows
(the window's most common fingerprint, its three most common, and the unseen filter
alone), it gives:

- the share of windows where the filter names something, the share of the
  WAF-blocked clients it covers (recall), the share of the clients it matches that
  the WAF blocked (precision), and the share of the other clients it matches;
- the base rate: the blocked share of all clients, the precision of a filter that
  picks clients at random, and each filter's lift over it;
- the ceiling of any fingerprint filter: the share of blocked clients on
  fingerprints no unblocked client presents in that window (coverable at no
  collateral), and on fingerprints where blocked clients are the majority;
- surges as labeled events: windows where the WAF blocked at least k_min clients
  and at least the 99th percentile of the endpoint's blocked count on the days
  before, grouped into episodes of consecutive windows. An episode is detected when
  the filter names a fingerprint carrying blocked clients in one of its windows; the
  detection expected by chance, from the rate at which it does so in non-surge
  windows, is given next to it.

The binomial configuration and the beta-binomial are read from the runs' WAF rows;
the z-score's filter is recomputed from its per-fold threshold and checked against
the run's firing flag, window by window.

Only counts and rates leave; the endpoints are E1..E4 as in production_tables.py.

Usage:
    python waf_labels.py --data-dir $DATA_ROOT/azion --results $DATA_ROOT/azion/results \\
        --roles $DATA_ROOT/azion/roles.json --out ../results/waf_labels.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rule_detection_production import build_windows, load_day  # noqa: E402

BASE = "rule_production_windows_rolling_origin_v2.csv"
PROFILES = {
    "clean_profile": {"waf_in_profile": False,
                      "runs": {"binomial": "rule_production_windows_rolling_origin_fleets0.05_v2.csv",
                               "beta-binomial": "rule_production_windows_rolling_origin_od_v2.csv"},
                      "zscore": "rule_production_windows_rolling_origin_fleets0.05_v2.csv"},
    "all_profile": {"waf_in_profile": True,
                    "runs": {"binomial": "rule_production_windows_rolling_origin_wafprof_fleets0.05_v2.csv",
                             "beta-binomial": "rule_production_windows_rolling_origin_wafprof_od_v2.csv"},
                    "zscore": "rule_production_windows_rolling_origin_wafprof_fleets0.05_v2.csv"},
}
TRIVIAL = ("modal", "top3", "unseen")


def zcal_named(all_, profile, thr, n_all, k_min):
    """The calibrated z-score's filter on one window (rule_detection_production.baseline_scopes)."""
    c = all_[all_ > 0]
    if n_all < k_min or not c.sum():
        return set()
    n = float(c.sum())
    b = profile.reindex(c.index).fillna(0.0).to_numpy() + 1.0 / max(profile.attrs["n"], 1)
    z = (c.to_numpy(dtype=float) - n * b) / np.sqrt(n * b * (1 - np.minimum(b, 0.999999)))
    return set(c.index[z > thr])


def scores(rows, cfgs):
    """Recall, precision, collateral and lift of each filter over a set of windows."""
    waf = sum(r["waf"] for r in rows)
    size = sum(r["size"] for r in rows)
    other = size - waf
    base = waf / size if size else None
    out = {}
    for cfg in cfgs:
        m = sum(r["m"][cfg] for r in rows)
        mw = sum(r["mw"][cfg] for r in rows)
        prec = mw / m if m else None
        out[cfg] = {"named": float(np.mean([r["named"][cfg] for r in rows])),
                    "recall": mw / waf if waf else None,
                    "precision": prec,
                    "lift": (prec / base) if (prec is not None and base) else None,
                    "collateral": (m - mw) / other if other else None}
    return out


def surge_episodes(rows, blocked, folds, k_min):
    """Runs of consecutive windows with at least k_min blocked clients and at least the
    99th percentile of the blocked count on the days before."""
    episodes = []
    for f in folds:
        d = pd.Timestamp(f).date()
        thr = max(k_min, float(np.percentile([c for t, c in blocked if t.date() < d], 99)))
        s = sorted((w for w in rows if w["fold"] == f and w["waf"] >= thr), key=lambda w: w["window"])
        for w in s:
            if episodes and episodes[-1][-1]["fold"] == f and \
                    w["window"] - episodes[-1][-1]["window"] == pd.Timedelta("5min"):
                episodes[-1].append(w)
            else:
                episodes.append([w])
    return episodes


def analyze(mode, spec, recs_of, alias, hosts, J, args):
    """Every window's counts under one profile, and the per-endpoint summary."""
    recs = recs_of[spec["waf_in_profile"]]
    rec = {(r["host"], r["window"]): r for r in recs if r["host"] in alias}
    cols = {"kind", "fold", "host", "window", "size", "waf_sessions", "matched_union",
            "matched_waf_union", "union_named", "zcal_named"}
    rows_of = {}
    for cfg, csv in {**spec["runs"], "z-score": spec["zscore"]}.items():
        W = pd.read_csv(args.results / csv, usecols=lambda c: c in cols, dtype={"fold": str})
        W = W[(W["kind"] == "waf") & W["host"].isin(hosts) & (W["size"] >= args.k_min)
              & W["fold"].isin(args.test_folds + args.fresh_folds)]
        W["window"] = pd.to_datetime(W["window"], utc=True)
        rows_of[cfg] = W.set_index(["fold", "host", "window"])
    Jz = json.loads((args.results / spec["zscore"].replace("_windows", "").replace(".csv", ".json")).read_text())
    cfgs = list(spec["runs"]) + ["z-score"] + list(TRIVIAL)
    windows, checked, mismatches, profiles = [], 0, 0, {}
    for (fold, host, win), b in rows_of["z-score"].iterrows():
        r = rec[(host, win)]
        key = (fold, host)
        if key not in profiles:
            d = pd.Timestamp(fold).date()
            bg = pd.concat([x["clean"] for x in recs if x["host"] == host and x["window"].date() < d])
            bg = bg.groupby(level=0).sum()
            P = (bg / bg.sum()).sort_values(ascending=False)
            P.attrs["n"] = int(bg.sum())
            profiles[key] = P
        named = zcal_named(r["all"], profiles[key], Jz["folds"][fold][host]["zcal_threshold"], r["n_all"], args.k_min)
        checked += 1
        mismatches += bool(named) != bool(b["zcal_named"])
        allc = r["all"][r["all"] > 0].sort_values(ascending=False)
        clean = r["all"] - r["waf"]
        w = {"fold": fold, "host": host, "window": win, "size": int(b["size"]), "waf": int(b["waf_sessions"]),
             "no_clean": int(r["waf"][clean <= 0].sum()), "majority": int(r["waf"][r["waf"] >= clean].sum()),
             "m": {}, "mw": {}, "named": {}}
        for cfg in spec["runs"]:
            x = rows_of[cfg].loc[(fold, host, win)]
            w["m"][cfg], w["mw"][cfg] = int(x["matched_union"]), int(x["matched_waf_union"])
            w["named"][cfg] = bool(x["union_named"])
        picks = {"z-score": named, "modal": set(allc.index[:1]), "top3": set(allc.index[:3]),
                 "unseen": set(allc.index[~allc.index.isin(profiles[key].index) & (allc.to_numpy() >= args.k_min)])}
        for cfg, picked in picks.items():
            hit = r["all"].index.isin(list(picked))
            w["m"][cfg], w["mw"][cfg] = int(r["all"][hit].sum()), int(r["waf"][hit].sum())
            w["named"][cfg] = bool(picked)
        windows.append(w)
    if mismatches:
        raise SystemExit(f"{mode}: z-score recomputation: {mismatches} of {checked} windows differ from the run")

    blocked = {}
    for r in recs:
        if r["host"] in alias:
            blocked.setdefault(r["host"], []).append((r["window"], int(r["waf"].sum())))
    out = {"check": {"zscore_windows": checked, "zscore_mismatches": mismatches}}
    for block, folds in (("test_days", args.test_folds), ("fresh_day", args.fresh_folds)):
        out[block] = {}
        for h in hosts:
            rows = [w for w in windows if w["host"] == h and w["fold"] in folds]
            waf = sum(w["waf"] for w in rows)
            e = {"windows": len(rows), "windows_with_waf": sum(w["waf"] > 0 for w in rows), "waf_clients": waf}
            if not waf:
                out[block][alias[h]] = e
                continue
            e["waf_share_median"] = float(np.median([w["waf"] / w["size"] for w in rows]))
            e["base_rate"] = waf / sum(w["size"] for w in rows)
            e["ceiling"] = {"no_clean": sum(w["no_clean"] for w in rows) / waf,
                            "majority": sum(w["majority"] for w in rows) / waf}
            e["scores"] = scores(rows, cfgs)
            episodes = surge_episodes(rows, blocked[h], folds, args.k_min)
            in_surge = {(w["fold"], w["window"]) for ep in episodes for w in ep}
            quiet = [w for w in rows if (w["fold"], w["window"]) not in in_surge]
            e["surges"] = {"episodes": len(episodes), "windows": sum(map(len, episodes))}
            if episodes:
                flat = [w for ep in episodes for w in ep]
                e["surges"]["scores"] = scores(flat, cfgs)
                e["surges"]["detected"] = {c: sum(any(w["mw"][c] > 0 for w in ep) for ep in episodes) for c in cfgs}
                # the same rate outside surges, and the detections it would give by chance
                p0 = {c: (float(np.mean([w["mw"][c] > 0 for w in quiet])) if quiet else None) for c in cfgs}
                e["surges"]["quiet_hit_rate"] = p0
                e["surges"]["expected_by_chance"] = {
                    c: (float(sum(1 - (1 - p0[c]) ** len(ep) for ep in episodes)) if p0[c] is not None else None)
                    for c in cfgs}
            out[block][alias[h]] = e
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--roles", required=True, type=Path)
    ap.add_argument("--test-folds", nargs="+", default=["2026-09-20", "2026-09-21", "2026-09-22",
                                                        "2026-09-23", "2026-09-24"])
    ap.add_argument("--fresh-folds", nargs="+", default=["2026-09-25"])
    ap.add_argument("--k-min", type=int, default=5)
    ap.add_argument("--rho", type=float, default=3.0)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    roles = json.loads(args.roles.read_text())
    J = json.loads((args.results / BASE.replace("_windows", "").replace(".csv", ".json")).read_text())
    evaluated = set.intersection(*(set(J["folds"][f]) for f in args.test_folds))
    hosts = sorted((h for h in evaluated if h in roles), key=lambda h: -J["hosts"][h]["median_test_size"])
    alias = {h: f"E{i + 1}" for i, h in enumerate(hosts)}

    days = sorted(p for p in args.data_dir.iterdir()
                  if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}(_\d{4}-\d{2}-\d{2})?", p.name))
    recs_of = {}
    for flag in (False, True):
        recs = []
        for day in days:
            recs += build_windows(*load_day(day, "origin"), waf_in_profile=flag)
        recs_of[flag] = [r for r in recs if r["host"] in alias]

    out = {"k_min": args.k_min, "rho": args.rho, "endpoints": {alias[h]: roles[h] for h in hosts}}
    for mode, spec in PROFILES.items():
        out[mode] = analyze(mode, spec, recs_of, alias, hosts, J, args)
        # with the profile built without blocked clients, a stable fingerprint is
        # enriched on full traffic only past this blocked share (see the docstring)
        if mode == "clean_profile":
            out[mode]["implied_precision_floor"] = {
                e: 1 - (1 - v["waf_share_median"]) / args.rho
                for e, v in out[mode]["test_days"].items() if "waf_share_median" in v}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    for mode in PROFILES:
        c = out[mode]["check"]
        print(f"{mode}: z-score recomputation: {c['zscore_windows']} windows, {c['zscore_mismatches']} mismatches")
    print(f"OK: {args.out}")


if __name__ == "__main__":
    main()
