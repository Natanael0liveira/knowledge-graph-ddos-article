#!/usr/bin/env python3
"""Sprint 6 (NOMS) — production tables by test day, with calibrated baselines.

production_summary.py reduces one run pooled over all of its test days. This script
recomputes the paper's production numbers from the per-window CSVs that rule_detection_production.py writes, for a chosen subset of test days. The test days (2026-09-20 to 2026-09-24) and the fresh day (2026-09-25) are then reported apart, as fresh_day_protocol.md requires.

Per scope (enrichment, enrichment united with the unseen filter, the z-score, the
z-score calibrated to the enrichment test's budget, the per-fingerprint historical
z-score, the unseen filter) and per gate (Omega >= tau, distinct origins >= their
p99) it gives, per endpoint and pooled:
- the firing rate on clean windows and the median share of clients a firing blocks;
- the firing rate with a flash crowd of 100 and of 1,000 users;
- per botnet cell (new or shared stacks; 100 or 1,000 attackers, or 1x or 0.1x the
  endpoint's median window): the mean blocked share, and the median share of the
  window's legitimate clients a firing blocks (collateral in attack windows).

It also gives:
- the WAF cross-check: the share of the clients the scope matches that the WAF also
  blocked (precision against the WAF), and the share of WAF-blocked clients it
  matches (coverage);
- the calibration floor per endpoint: the smallest stack, and the smallest 25-stack botnet, the calibrated test can name, from the level, profile and typical window of each fold, with the number of known fleets the fold exempted.

Only rates, shares and counts leave. Endpoints are E1..E4, as in production_summary.py.

Usage:
    python production_tables.py --results $DATA_ROOT/azion/results --roles $DATA_ROOT/azion/roles.json \\
        --base rule_production_windows_rolling_origin_v2.csv \\
        --fleets rule_production_windows_rolling_origin_fleets0.05_v2.csv \\
        --test-folds 2026-09-20 2026-09-21 2026-09-22 2026-09-23 2026-09-24 \\
        --fresh-folds 2026-09-25 --out ../results/production_tables.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

SCOPES = {"enrichment": "scope", "union": "union", "zscore": "zscore", "zcal": "zcal",
          "zhist": "zhist", "unseen": "unseen"}
GATES = ("omega", "origins", "none")
CELLS = [("attack", "fresh", 100), ("attack", "fresh", 1000), ("attack_rel", "fresh", 1.0),
         ("attack_rel", "fresh", 0.1), ("attack", "tail", 100), ("attack", "tail", 1000),
         ("attack_rel", "tail", 1.0), ("attack_rel", "tail", 0.1)]


def cell_name(kind, source, x):
    return f"{'new' if source == 'fresh' else 'shared'}:{'A' if kind == 'attack' else 'x'}{x:g}"


def load(path, k_min=5):
    need = {"kind", "fold", "host", "window", "size", "omega", "flash", "source", "stacks", "attackers", "fraction",
            "waf_sessions", "matched", "matched_waf", "matched_union", "matched_waf_union"}
    need |= {f"{c}_{k}" for c in SCOPES.values() for k in ("named", "recall", "collateral")}
    W = pd.read_csv(path, usecols=lambda c: c in need, dtype={"fold": str})
    W = W[W["size"] >= k_min]
    cal = W[W["kind"] == "calib"].groupby(["fold", "host"])
    keys = list(zip(W["fold"], W["host"]))
    W = W.assign(gate_omega=W["omega"].to_numpy() >= cal["omega"].quantile(0.99).reindex(keys).to_numpy(),
                 gate_origins=W["size"].to_numpy() >= cal["size"].quantile(0.99).reindex(keys).to_numpy(),
                 gate_none=True)          # the scope alone triggers (|S| >= k_min already holds)
    for c in SCOPES.values():
        if f"{c}_named" in W:
            W[f"{c}_named"] = W[f"{c}_named"].astype(bool)
    return W


def select(W, kind, source=None, x=None):
    m = W["kind"] == kind
    if source is not None:
        m &= (W["source"] == source) & (W["stacks"] == 25)
        m &= (W["attackers"] == x) if kind == "attack" else (W["fraction"] == x)
    return W[m]


def rates(W):
    """Every scope under every gate, over the windows of W."""
    out = {}
    clean = select(W, "clean")
    for scope, col in SCOPES.items():
        if f"{col}_named" not in W:
            continue
        for gate in GATES:
            fired = lambda d: d[f"gate_{gate}"] & d[f"{col}_named"]
            f = fired(clean)
            r = {"clean_windows": int(len(clean)), "clean_fires": int(f.sum()),
                 "clean_rate": float(f.mean()) if len(clean) else None,
                 "clean_collateral_median": float(clean.loc[f, f"{col}_collateral"].median()) if f.any() else None}
            for N in (100, 1000):
                fl = W[(W["kind"] == "flash") & (W["flash"] == N)]
                r[f"flash{N}"] = float(fired(fl).mean()) if len(fl) else None
            coll = []
            for kind, source, x in CELLS:
                d = select(W, kind, source, x)
                if not len(d):
                    continue
                fd = fired(d)
                coll.append(d.loc[fd, f"{col}_collateral"])
                r[cell_name(kind, source, x)] = {
                    "windows": int(len(d)), "fires": float(fd.mean()),
                    "gate": float(d[f"gate_{gate}"].mean()), "named": float(d[f"{col}_named"].mean()),
                    "blocked": float((d[f"{col}_recall"] * fd).mean()),
                    "collateral_median": float(d.loc[fd, f"{col}_collateral"].median()) if fd.any() else None}
            # collateral in attack windows, over every firing of the eight cells
            coll = pd.concat(coll) if coll else pd.Series(dtype=float)
            r["attack_collateral_median"] = float(coll.median()) if len(coll) else None
            r["attack_collateral_p90"] = float(coll.quantile(0.9)) if len(coll) else None
            out[f"{scope}|{gate}"] = r
    return out


def waf(W):
    w = W[W["kind"] == "waf"]
    out = {"windows": int(len(w)), "waf_clients": int(w["waf_sessions"].sum())}
    for scope, (named, m, mw) in {"enrichment": ("scope_named", "matched", "matched_waf"),
                                  "union": ("union_named", "matched_union", "matched_waf_union")}.items():
        if m not in w:
            continue
        x = w[w[named]]
        out[scope] = {"precision": float(x[mw].sum() / x[m].sum()) if x[m].sum() else None,
                      "coverage": float(x[mw].sum() / w["waf_sessions"].sum()) if w["waf_sessions"].sum() else None}
    return out


def min_count(n, b, level, family, rho):
    """Smallest count c the test names among n origins for prevalence b."""
    c = np.arange(1, n + 1)
    ok = (binom.sf(c - 1, n, min(b, 1.0)) * family < level) & (c / n >= rho * b)
    return int(c[ok][0]) if ok.any() else None


def floor(rec, rho=3.0, M=25, share=0.9):
    """The calibration floor of one endpoint in one fold.

    A 25-stack botnet of A attackers puts about share*A/M origins on each stack in
    a window of n0 + A origins. The smallest A whose stacks the level names is
    the floor, for stacks absent from the profile (b = 1/N) and for stacks drawn
    from its tail (b = the median prevalence past the ten most common, plus 1/N).
    Under --overdispersion the floor on new stacks stays exact, since a stack absent
    from the profile keeps the binomial; the shared floor ignores the tail's
    correlation, and the paper reports only the first.
    """
    n0, N = int(round(rec["median_origins"])), rec["profile_sessions"]
    fam, lvl = rec["profile_fingerprints"] + M, rec["scope_level"]
    out = {"median_origins": n0, "level": lvl, "known_fleets": rec.get("fleets", 0)}
    for kind, b in (("new", 1.0 / N), ("shared", (rec.get("tail_prevalence_median") or 0.0) + 1.0 / N)):
        A_min = None
        for A in np.unique(np.round(np.geomspace(1, max(100 * n0, 10_000), 400)).astype(int)):
            c = min_count(n0 + A, b, lvl, fam, rho)
            if c is not None and share * A / M >= c:
                A_min = int(A)
                break
        out[kind] = {"min_attackers": A_min,
                     "min_fraction_of_window": (A_min / n0) if A_min else None,
                     "min_stack_origins": (min_count(n0 + A_min, b, lvl, fam, rho) if A_min else None)}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--roles", required=True, type=Path)
    ap.add_argument("--base", required=True)
    ap.add_argument("--fleets", required=True)
    ap.add_argument("--od", default=None, help="the base run with the overdispersed background (--overdispersion)")
    ap.add_argument("--od-fleets", default=None, help="the same with known fleets")
    ap.add_argument("--test-folds", nargs="+", required=True)
    ap.add_argument("--fresh-folds", nargs="+", default=[])
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    roles = json.loads(args.roles.read_text())
    runs = {"base": args.base, "fleets": args.fleets}
    runs |= {k: v for k, v in (("od", args.od), ("od_fleets", args.od_fleets)) if v}
    fired = {}
    J = {k: json.loads((args.results / v.replace("_windows", "").replace(".csv", ".json")).read_text())
         for k, v in runs.items()}
    # The endpoints the paper evaluates: those of every test fold. A host that first
    # qualifies on a fresh day is not added to it (fresh_day_protocol.md).
    evaluated = set.intersection(*(set(J["base"]["folds"][f]) for f in args.test_folds))
    hosts = sorted((h for h in evaluated if h in roles),
                   key=lambda h: -J["base"]["hosts"][h]["median_test_size"])
    alias = {h: f"E{i + 1}" for i, h in enumerate(hosts)}
    out = {"endpoints": {alias[h]: roles[h] for h in hosts},
           "folds": {"test": len(args.test_folds), "fresh": args.fresh_folds}}
    for run, csv in runs.items():
        W = load(args.results / csv)
        W = W[W["host"].isin(hosts)]
        # clean windows where each origin-gated scope fires, to compare the frozen
        # configuration with the calibrated z-score window by window
        c = select(W, "clean")
        for col in ("union", "zcal"):
            f = c[c["gate_origins"] & c[f"{col}_named"]]
            fired[(run, col)] = set(zip(f["fold"], f["host"], f["window"]))
        f = c[c["gate_omega"] & c["scope_named"]]          # the base rule, the protocol's reference
        fired[(run, "rule")] = set(zip(f["fold"], f["host"], f["window"]))
        for block, folds in (("test_days", args.test_folds), ("fresh_day", args.fresh_folds)):
            if not folds:
                continue
            S = W[W["fold"].isin(folds)]
            if not len(S):
                raise SystemExit(f"{csv}: no windows in folds {folds}")
            out.setdefault(block, {})[run] = {
                "all": rates(S), "waf": {"all": waf(S), **{alias[h]: waf(S[S["host"] == h]) for h in hosts}},
                "per_endpoint": {alias[h]: rates(S[S["host"] == h]) for h in hosts}}
        # The stealthy regime per test day on the busiest endpoint: how often the
        # distinct-origin gate fires, how often the scope names the botnet, and what
        # it blocks where it does (Section V-D).
        e1 = hosts[0]
        out.setdefault("stealth_E1", {})[run] = {
            f"{source}:x0.1": {
                fo: {"gate": float(g["gate_origins"].mean()), "named": float(g["union_named"].mean()),
                     "recall_where_named": (float(g.loc[g["union_named"], "union_recall"].mean())
                                            if g["union_named"].any() else None),
                     "blocked": float((g["union_recall"] * (g["gate_origins"] & g["union_named"])).mean()),
                     "blocked_no_gate": float((g["union_recall"] * g["union_named"]).mean())}
                for fo, g in select(W[W["host"] == e1], "attack_rel", source, 0.1).groupby("fold")}
            for source in ("fresh", "tail")}
        out["stealth_E1"][run]["clean_no_gate"] = {
            fo: float(g["union_named"].mean()) for fo, g in select(W[W["host"] == e1], "clean").groupby("fold")}
        out.setdefault("floor", {})[run] = {
            alias[h]: {f: floor(J[run]["folds"][f][h]) for f in args.test_folds + args.fresh_folds
                       if h in J[run]["folds"].get(f, {})} for h in hosts}
    # Do the frozen configuration (known fleets, union, origin gate) and the calibrated
    # z-score (no fleet profile) fire on the same clean windows? Counts only.
    a, b = fired[("fleets", "union")], fired[("base", "zcal")]
    for block, folds in (("test_days", args.test_folds), ("fresh_day", args.fresh_folds)):
        if folds:
            A = {x for x in a if x[0] in folds}; B = {x for x in b if x[0] in folds}
            out[block]["overlap_frozen_zcal"] = {"frozen": len(A), "zcal": len(B), "both": len(A & B)}
            C = {x for x in fired[("base", "rule")] if x[0] in folds}
            out[block]["overlap_frozen_rule"] = {"frozen": len(A), "rule": len(C), "both": len(A & C)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"OK: {args.out}")


if __name__ == "__main__":
    main()
