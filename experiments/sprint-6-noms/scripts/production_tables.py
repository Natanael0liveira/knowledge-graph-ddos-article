#!/usr/bin/env python3
"""Sprint 6 (NOMS) — production tables by test day, with calibrated baselines.

production_summary.py reduces one run pooled over all of its test days. This script
recomputes the paper's production numbers from the per-window CSVs that rule_detection_production.py writes, for a chosen subset of test days. The test days (2026-09-20 to 2026-09-24) and the fresh day (2026-09-25) are then reported apart, as fresh_day_protocol.md requires.

Per scope (enrichment, enrichment united with the unseen filter, the z-score, the
z-score calibrated to the enrichment test's budget, the per-fingerprint historical
z-score, the unseen filter) and per gate (Omega >= tau; distinct origins >= their
p99; the seasonal gate, distinct origins against the median of the same hour of day
on the fold's calibration windows, past the p99 of that ratio; none, the scope as its
own trigger) it gives, per endpoint and pooled:
- the firing rate on clean windows, with its 95% Clopper-Pearson interval and its
  count per test day, and the median and largest share of clients a firing blocks;
- the firing rate with a flash crowd of 100 and of 1,000 users, and the median and
  90th percentile of the share of the window's clients those firings block, with,
  for the frozen configuration, the share of its 1,000-user firings that name the
  fingerprint most often named there (a count, no fingerprint leaves);
- per botnet cell (new or shared stacks; 100 or 1,000 attackers, or 1x or 0.1x the
  endpoint's median window): the mean blocked share, and the median share of the
  window's legitimate clients a firing blocks (collateral in attack windows, whose
  90th percentile and maximum over the cells are also given);
- the same for a botnet on the endpoint's 25 most common profile fingerprints
  (adversarial, 100 or 1,000 attackers), the boundary of the threat model. It is
  reported apart and left out of the attack-window collateral of the other cells.

It also gives:
- the WAF cross-check: the share of the clients the scope matches that the WAF also
  blocked (precision against the WAF), and the share of WAF-blocked clients it
  matches (coverage);
- the calibration floor per endpoint: the smallest stack, and the smallest 25-stack botnet, the calibrated test can name, from the level, profile and typical window of each fold, with the number of known fleets the fold exempted;
- the floor of the deployed configuration, the test joined with the unseen filter,
  on new and shared stacks, for botnets of 5, 25 and 100 stacks;
- how often each gate alone fires on clean windows, and the mean next to the median
  share of clients a clean-window firing blocks;
- for each false-alarm rate, an interval from a bootstrap over endpoint-days
  (resampling the days of each endpoint), since misfires cluster by day, next to the
  exact interval that treats windows as independent;
- how many clean windows the gate opens, and how many joint misfires of gate and
  scope independence would give (per endpoint, the gate's rate times the scope's
  alone times the windows), to set against the observed ones;
- a sweep over the injected botnet sizes (25 to 1,000 attackers on 1, 5, 25 or 100
  stacks, and 0.1, 0.5 or 1 times the median window on 25): how often the gate
  fires and the scope names, and what the configuration and its scope alone block,
  with, for new stacks, the share a binomial model of stack sizes predicts.

Further runs (``--run NAME CSV``, e.g. the cross-fitted calibration of
rule_detection_production.py --split crossfit) are reduced the same way.

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
from scipy.stats import beta, binom

SCOPES = {"enrichment": "scope", "union": "union", "zscore": "zscore", "zcal": "zcal",
          "zhist": "zhist", "unseen": "unseen"}
GATES = ("omega", "origins", "seasonal", "none")
CELLS = [("attack", "fresh", 100), ("attack", "fresh", 1000), ("attack_rel", "fresh", 1.0),
         ("attack_rel", "fresh", 0.1), ("attack", "tail", 100), ("attack", "tail", 1000),
         ("attack_rel", "tail", 1.0), ("attack_rel", "tail", 0.1)]
ADV_CELLS = [("attack", "adversarial", 100), ("attack", "adversarial", 1000)]


def cell_name(kind, source, x):
    name = {"fresh": "new", "tail": "shared", "adversarial": "adv"}[source]
    return f"{name}:{'A' if kind == 'attack' else 'x'}{x:g}"


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
    # The seasonal gate: distinct origins against the median of the same hour of day
    # (UTC) over the fold's calibration windows, firing past the 99th percentile of
    # that ratio on the calibration windows (never below 1), the same 1% budget.
    W["hour"] = W["window"].astype(str).str.slice(11, 13).astype(int)
    hk = list(zip(W["fold"], W["host"], W["hour"]))
    med = W[W["kind"] == "calib"].groupby(["fold", "host", "hour"])["size"].median()
    W["size_ratio"] = W["size"].to_numpy() / med.reindex(hk).to_numpy()
    thr = W[W["kind"] == "calib"].groupby(["fold", "host"])["size_ratio"].quantile(0.99).clip(lower=1.0)
    W["gate_seasonal"] = W["size_ratio"].to_numpy() >= thr.reindex(keys).to_numpy()
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


def clopper_pearson(k, n, level=0.95):
    """Exact two-sided interval for a binomial proportion k/n."""
    if not n:
        return None
    a = (1 - level) / 2
    return [float(beta.ppf(a, k, n - k + 1)) if k else 0.0,
            float(beta.ppf(1 - a, k + 1, n - k)) if k < n else 1.0]


def cluster_ci(clean, fired, B=10_000, seed=0, level=0.95):
    """Percentile interval for a false-alarm rate from a bootstrap over endpoint-days.

    Windows of one endpoint and day share their fleets, so misfires cluster. The
    days of each endpoint are resampled with replacement (the endpoints stay fixed),
    and the rate is recomputed as misfires over windows. None with fewer than two
    days per endpoint (the fresh day).
    """
    g = pd.DataFrame({"host": clean["host"].to_numpy(), "fold": clean["fold"].to_numpy(),
                      "f": np.asarray(fired, dtype=float)})
    agg = g.groupby(["host", "fold"])["f"].agg(["sum", "count"])
    strata = [agg.xs(h, level="host") for h in agg.index.get_level_values("host").unique()]
    if not strata or min(len(s) for s in strata) < 2:
        return None
    rng = np.random.default_rng(seed)
    tf, tn = np.zeros(B), np.zeros(B)
    for s in strata:
        idx = rng.integers(0, len(s), size=(B, len(s)))
        tf += s["sum"].to_numpy()[idx].sum(axis=1)
        tn += s["count"].to_numpy()[idx].sum(axis=1)
    a = (1 - level) / 2
    return [float(np.quantile(tf / tn, a)), float(np.quantile(tf / tn, 1 - a))]


def joint_expected(clean, gate, col):
    """Joint misfires of gate and scope if they were independent within each endpoint."""
    e = 0.0
    for _, h in clean.groupby("host"):
        e += float(h[f"gate_{gate}"].mean()) * float(h[f"{col}_named"].mean()) * len(h)
    return e


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
                 "clean_ci95": clopper_pearson(int(f.sum()), int(len(clean))),
                 "clean_ci95_cluster": cluster_ci(clean, f),
                 "clean_gate_windows": int(clean[f"gate_{gate}"].sum()),
                 "clean_joint_expected": (joint_expected(clean, gate, col) if gate != "none" else None),
                 "clean_fires_by_fold": {fo: int(g.sum()) for fo, g in f.groupby(clean["fold"])},
                 "clean_collateral_median": float(clean.loc[f, f"{col}_collateral"].median()) if f.any() else None,
                 "clean_collateral_mean": float(clean.loc[f, f"{col}_collateral"].mean()) if f.any() else None,
                 "clean_collateral_max": float(clean.loc[f, f"{col}_collateral"].max()) if f.any() else None}
            for N in (100, 1000):
                fl = W[(W["kind"] == "flash") & (W["flash"] == N)]
                ff = fired(fl)
                r[f"flash{N}"] = float(ff.mean()) if len(fl) else None
                # what a firing on a flash crowd blocks: the share of the window's
                # legitimate clients, the crowd included
                r[f"flash{N}_collateral_median"] = float(fl.loc[ff, f"{col}_collateral"].median()) if ff.any() else None
                r[f"flash{N}_collateral_p90"] = float(fl.loc[ff, f"{col}_collateral"].quantile(0.9)) if ff.any() else None
            coll = []
            for kind, source, x in CELLS + ADV_CELLS:
                d = select(W, kind, source, x)
                if not len(d):
                    continue
                fd = fired(d)
                if (kind, source, x) in CELLS:
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
            r["attack_collateral_max"] = float(coll.max()) if len(coll) else None
            out[f"{scope}|{gate}"] = r
    # how often each gate alone fires on clean windows (its nominal rate is 1%)
    out["gates_clean"] = {g: (float(clean[f"gate_{g}"].mean()) if len(clean) else None) for g in ("omega", "origins", "seasonal")}
    return out


def flash_concentration(path, W, hosts, alias, blocks, N=1000):
    """How concentrated the configuration's firings on flash crowds of N users are.

    Among the flash-crowd windows where the distinct-origin gate and the union fire,
    the share whose enrichment scope holds the fingerprint most often named there, per
    endpoint and block. The named fingerprints are read in chunks for the flash rows
    only, and only counts and shares leave.
    """
    parts = [ch[(ch["kind"] == "flash") & (ch["flash"] == N)]
             for ch in pd.read_csv(path, usecols=["kind", "fold", "host", "window", "flash", "named"],
                                   dtype={"fold": str, "named": str}, chunksize=500_000)]
    F = pd.concat(parts).merge(
        W.loc[(W["kind"] == "flash") & (W["flash"] == N), ["fold", "host", "window", "flash", "gate_origins", "union_named"]],
        on=["fold", "host", "window", "flash"])
    out = {}
    for block, folds in blocks:
        for h in hosts:
            f = F[F["fold"].isin(folds) & (F["host"] == h) & F["gate_origins"] & F["union_named"]]
            count = {}
            for s in f["named"].fillna(""):
                for x in set(s.split(";")) - {""}:
                    count[x] = count.get(x, 0) + 1
            top = max(count.values()) if count else 0
            out.setdefault(block, {})[alias[h]] = {"fires": int(len(f)),
                                                   "top_fingerprint_share": (top / len(f)) if len(f) else None}
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


def min_count(n, b, log_level, family, rho):
    """Smallest count c the test names among n origins for prevalence b.

    In logs, as the test runs (rule_detection_production.log_tail): where the tail
    probability underflows a float it is summed from the log pmf.
    """
    c = np.arange(1, n + 1)
    b = min(b, 1.0)
    with np.errstate(divide="ignore"):
        lp = np.log(binom.sf(c - 1, n, b))
    if np.isneginf(lp).any():
        lpmf = binom.logpmf(np.arange(n + 1), n, b)
        rev = np.logaddexp.accumulate(lpmf[::-1])[::-1]         # log P[X >= k], k = 0..n
        lp = np.where(np.isneginf(lp), rev[c], lp)
    ok = (lp + np.log(family) < log_level) & (c / n >= rho * b)
    return int(c[ok][0]) if ok.any() else None


def floor(rec, rho=3.0, M=25, share=0.9):
    """The calibration floor of one endpoint in one fold.

    A 25-stack botnet of A attackers puts about share*A/M origins on each stack in
    a window of n0 + A origins. The smallest A whose stacks the level names is
    the floor, for stacks absent from the profile (b = 1/N) and for stacks drawn
    from its tail (b = the median prevalence past the ten most common, plus 1/N).
    Under --overdispersion the floor on new stacks stays exact, since a stack absent
    from the profile keeps the binomial; the shared floor here ignores the tail's
    correlation, so it is a lower bound. Table V's beta-binomial shared floor is the
    exact one from floor_bands.py, which differs from this bound only on E4 (84
    against 56).
    """
    n0, N = int(round(rec["median_origins"])), rec["profile_sessions"]
    fam, lvl = rec["profile_fingerprints"] + M, rec["scope_level"]
    # the level in logs: runs before the log-space test stored only the float
    log_lvl = rec["scope_log10_level"] * np.log(10) if "scope_log10_level" in rec else np.log(lvl)
    out = {"median_origins": n0, "level": lvl, "log10_level": float(log_lvl / np.log(10)),
           "known_fleets": rec.get("fleets", 0), "zcal_threshold": rec.get("zcal_threshold")}
    for kind, b in (("new", 1.0 / N), ("shared", (rec.get("tail_prevalence_median") or 0.0) + 1.0 / N)):
        A_min = None
        for A in np.unique(np.round(np.geomspace(1, max(100 * n0, 10_000), 400)).astype(int)):
            c = min_count(n0 + A, b, log_lvl, fam, rho)
            if c is not None and share * A / M >= c:
                A_min = int(A)
                break
        out[kind] = {"min_attackers": A_min,
                     "min_fraction_of_window": (A_min / n0) if A_min else None,
                     "min_stack_origins": (min_count(n0 + A_min, b, log_lvl, fam, rho) if A_min else None)}
    return out


def deployed_floor(rec, M=25, share=0.9, k_min=5, rho=3.0):
    """The floor of a configuration that joins the test with the unseen filter.

    On new stacks the unseen filter names a stack once it holds k_min origins,
    whatever the level, so the configuration's floor is the smaller of the test's
    and ceil(k_min * M / share) attackers. On stacks drawn from the profile's tail
    the unseen filter names nothing, and the floor is the test's (a lower bound
    under --overdispersion, see floor).
    """
    f = floor(rec, rho=rho, M=M, share=share)
    n0 = f["median_origins"]
    A_u = int(np.ceil(k_min * M / share))
    t = f["new"]["min_attackers"]
    A = A_u if t is None else min(t, A_u)
    return {"M": M, "median_origins": n0,
            "new": {"min_attackers": A, "min_fraction_of_window": A / n0,
                    "set_by": "unseen" if (t is None or A_u < t) else "test", "test_alone": t},
            "shared": {"min_attackers": f["shared"]["min_attackers"],
                       "min_fraction_of_window": f["shared"]["min_fraction_of_window"]}}


SWEEP_M = (5, 25, 100)
SWEEP_A = (25, 50, 100, 250, 1000)
SWEEP_X = (0.1, 0.5, 1.0)


def model_new(rec, A, M, share=0.9, k_min=5, rho=3.0):
    """Share of a botnet on new stacks its scope alone blocks, from stack sizes.

    Each attacker sits on a stack with probability share, and its stack then holds
    it and Bin(A - 1, share / M) others. The union names a new stack once it holds
    the smaller of k_min and the test's smallest count at the fold's level, in a
    window of n0 + A origins (n0 the fold's median window).
    """
    n0, N = int(round(rec["median_origins"])), rec["profile_sessions"]
    fam = rec["profile_fingerprints"] + M
    log_lvl = rec["scope_log10_level"] * np.log(10) if "scope_log10_level" in rec else np.log(rec["scope_level"])
    t = min_count(n0 + A, 1.0 / N, log_lvl, fam, rho)
    c = k_min if t is None else min(k_min, t)
    return float(share * binom.sf(c - 2, A - 1, share / M))


def sweep(W, col, recs=None, folds=()):
    """Gate, naming and blocking over the injected botnet sizes (see the docstring)."""
    out = {}
    fired = lambda d: d["gate_origins"] & d[f"{col}_named"]
    for source in ("fresh", "tail", "adversarial"):
        name = {"fresh": "new", "tail": "shared", "adversarial": "adv"}[source]
        for M in SWEEP_M:
            for A in SWEEP_A:
                d = W[(W["kind"] == "attack") & (W["source"] == source) & (W["stacks"] == M) & (W["attackers"] == A)]
                if not len(d):
                    continue
                r = {"windows": int(len(d)), "gate": float(d["gate_origins"].mean()),
                     "named": float(d[f"{col}_named"].mean()),
                     "blocked": float((d[f"{col}_recall"] * fired(d)).mean()),
                     "blocked_alone": float((d[f"{col}_recall"] * d[f"{col}_named"]).mean()),
                     "gate_seasonal": float(d["gate_seasonal"].mean()),
                     "blocked_seasonal": float((d[f"{col}_recall"] * (d["gate_seasonal"] & d[f"{col}_named"])).mean())}
                if source == "fresh" and recs:
                    r["model_blocked_alone"] = float(np.mean([model_new(recs[f], A, M) for f in folds if f in recs]))
                out[f"{name}:M{M}:A{A}"] = r
        if source == "adversarial":
            continue
        for x in SWEEP_X:
            d = W[(W["kind"] == "attack_rel") & (W["source"] == source) & (W["stacks"] == 25) & (W["fraction"] == x)]
            if len(d):
                out[f"{name}:M25:x{x:g}"] = {
                    "windows": int(len(d)), "attackers_median": float(d["attackers"].median()),
                    "gate": float(d["gate_origins"].mean()), "named": float(d[f"{col}_named"].mean()),
                    "blocked": float((d[f"{col}_recall"] * fired(d)).mean()),
                    "blocked_alone": float((d[f"{col}_recall"] * d[f"{col}_named"]).mean()),
                    "gate_seasonal": float(d["gate_seasonal"].mean()),
                    "blocked_seasonal": float((d[f"{col}_recall"] * (d["gate_seasonal"] & d[f"{col}_named"])).mean())}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--roles", required=True, type=Path)
    ap.add_argument("--base", required=True)
    ap.add_argument("--fleets", required=True)
    ap.add_argument("--od", default=None, help="the base run with the overdispersed background (--overdispersion)")
    ap.add_argument("--od-fleets", default=None, help="the same with known fleets")
    ap.add_argument("--run", nargs=2, action="append", default=[], metavar=("NAME", "CSV"),
                    help="a further run to reduce the same way, e.g. xfit and the --split crossfit CSV")
    ap.add_argument("--test-folds", nargs="+", required=True)
    ap.add_argument("--fresh-folds", nargs="+", default=[])
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    roles = json.loads(args.roles.read_text())
    runs = {"base": args.base, "fleets": args.fleets}
    runs |= {k: v for k, v in (("od", args.od), ("od_fleets", args.od_fleets)) if v}
    runs |= dict(args.run)
    fired = {}
    J = {k: json.loads((args.results / v.replace("_windows", "").replace(".csv", ".json")).read_text())
         for k, v in runs.items()}
    # The endpoints the paper evaluates: those of every test fold. A host that first
    # qualifies on a fresh day is not added to it (fresh_day_protocol.md).
    evaluated = set.intersection(*(set(J["base"]["folds"][f]) for f in args.test_folds))
    hosts = sorted((h for h in evaluated if h in roles),
                   key=lambda h: -J["base"]["hosts"][h]["median_test_size"])
    alias = {h: f"E{i + 1}" for i, h in enumerate(hosts)}
    # how many endpoints the exports hold, evaluated or not (a count only)
    exported = set(J["base"]["hosts"]) | {h for v in J["base"].get("excluded_hosts", {}).values() for h in v}
    out = {"endpoints": {alias[h]: roles[h] for h in hosts}, "endpoints_exported": len(exported),
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
                     "blocked_no_gate": float((g["union_recall"] * g["union_named"]).mean()),
                     "gate_seasonal": float(g["gate_seasonal"].mean()),
                     "blocked_seasonal": float((g["union_recall"] * (g["gate_seasonal"] & g["union_named"])).mean())}
                for fo, g in select(W[W["host"] == e1], "attack_rel", source, 0.1).groupby("fold")}
            for source in ("fresh", "tail")}
        out["stealth_E1"][run]["clean_no_gate"] = {
            fo: float(g["union_named"].mean()) for fo, g in select(W[W["host"] == e1], "clean").groupby("fold")}
        if run == "fleets":
            out["flash_concentration"] = flash_concentration(
                args.results / csv, W, hosts, alias,
                [(k, v) for k, v in (("test_days", args.test_folds), ("fresh_day", args.fresh_folds)) if v])
        out.setdefault("floor", {})[run] = {
            alias[h]: {f: floor(J[run]["folds"][f][h]) for f in args.test_folds + args.fresh_folds
                       if h in J[run]["folds"].get(f, {})} for h in hosts}
        # the floor of the deployed configuration (test joined with the unseen
        # filter), on new and shared stacks, for 5, 25 and 100 botnet stacks
        out.setdefault("floor_deployed", {})[run] = {
            alias[h]: {f: {str(M): deployed_floor(J[run]["folds"][f][h], M=M) for M in (5, 25, 100)}
                       for f in args.test_folds + args.fresh_folds if h in J[run]["folds"].get(f, {})}
            for h in hosts}
        # the injected sizes, on the test days: the union for the runs that join the
        # test with the unseen filter, the calibrated z-score for the others
        col = "union" if run in ("fleets", "od", "od_fleets") or run.endswith(("_fleets", "_od")) else "zcal"
        T = W[W["fold"].isin(args.test_folds)]
        out.setdefault("sweep", {})[run] = {"scope": col, "all": sweep(T, col), **{
            alias[h]: sweep(T[T["host"] == h], col,
                            {f: J[run]["folds"][f][h] for f in args.test_folds if h in J[run]["folds"].get(f, {})},
                            args.test_folds) for h in hosts}}
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
