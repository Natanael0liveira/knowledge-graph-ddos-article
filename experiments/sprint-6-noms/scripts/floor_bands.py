#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the calibration floor on shared stacks, by popularity band.

The shared cells of production_tables.py draw a botnet's 25 stacks uniformly from the
profile past its ten most common fingerprints. The floor on shared stacks takes one
prevalence, the median past rank ten, so it describes mostly rare fingerprints. This
script gives the test's floor for stacks in three popularity bands of each fold's
rolling profile:
- ranks 11 to 35, the 25 fingerprints after the ten most common;
- ranks 36 to 100;
- ranks past 100;
- and, for comparison with production_tables.py, every rank past ten.

Each band is evaluated at the level the run calibrated in that fold, and at the band's
median prevalence (plus 1/N, as the test adds). Under the binomial background it uses
the binomial tail. Under the beta-binomial (the od run) it also uses the beta-binomial
tail at the band's median intra-window correlation phi, estimated as the run estimates
it. That floor is the one the test applies to such a stack, not a lower bound.

The profile is rebuilt from the exports as rule_detection_production.py builds it
(the clean origin-fingerprint counts of every day before the test day), and every fold
is checked against the run's own record: the profile size and the tail prevalence
must match.

It also counts, per fold, the fingerprints no M-stack botnet can enrich whatever its
size: each stack holds at most share / M of the window (0.9 / 25 = 3.6%), so the ratio
c/n >= rho * b fails for every b above share / (rho * M), 1.2% for M = 25. It gives
their number and the share of the profile's origins they carry.

Only prevalences, correlations and floors leave; endpoints are E1..E4.

Usage:
    python floor_bands.py --data-dir $DATA_ROOT/azion --results $DATA_ROOT/azion/results \\
        --roles $DATA_ROOT/azion/roles.json --fleets rule_production_rolling_origin_fleets0.05_v2.json \\
        --od rule_production_rolling_origin_od_v2.json \\
        --xfit-od rule_production_crossfit_origin_od_v2.json --out ../results/floor_bands.json
"""
import argparse
import json
import re
import statistics as st
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import betabinom

sys.path.insert(0, str(Path(__file__).resolve().parent))
from production_tables import min_count  # noqa: E402
from rule_detection_production import build_windows, intra_window_correlation, load_day, log_tail  # noqa: E402

# ranks_11_plus is the band the shared cells draw from and Table V's floor uses
BANDS = {"ranks_11_plus": (10, None), "ranks_11_35": (10, 35), "ranks_36_100": (35, 100), "ranks_101_plus": (100, None)}


def min_count_bb(n, b, phi, log_level, family, rho):
    """Smallest count the test names under a beta-binomial of mean b and correlation phi."""
    if phi <= 1e-9:
        return min_count(n, b, log_level, family, rho)
    b = min(b, 1.0 - 1e-12)
    shape = (1.0 - phi) / phi
    # the tail falls with c, so search upward instead of evaluating every count
    for c in range(max(1, int(np.ceil(rho * b * n))), n + 1):
        lp = log_tail(betabinom, np.array([c]), n, b * shape, (1.0 - b) * shape)[0]
        if lp + np.log(family) < log_level:
            return c
    return None


def floor_at(n0, count, M=25, share=0.9, cap=None, b=None, rho=3.0):
    """Smallest botnet whose mean stack, share * A / M, reaches count(n0 + A).

    None at once when b is past the ratio limit, share / M <= rho * b: a stack's share
    of the window then stays below rho * b at every size.
    """
    if b is not None and share / M <= rho * b:
        return None
    cap = cap or max(100 * n0, 10_000)
    for A in np.unique(np.round(np.geomspace(1, cap, 400)).astype(int)):
        c = count(n0 + int(A))
        if c is not None and share * A / M >= c:
            return int(A)
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--roles", required=True, type=Path)
    ap.add_argument("--fleets", required=True, help="the binomial configuration's run JSON (known fleets)")
    ap.add_argument("--od", required=True, help="the beta-binomial run JSON")
    ap.add_argument("--xfit-od", default=None,
                    help="the cross-fitted beta-binomial run JSON: its levels, on the same test-day profile")
    ap.add_argument("--test-folds", nargs="+", default=["2026-09-20", "2026-09-21", "2026-09-22",
                                                        "2026-09-23", "2026-09-24"])
    ap.add_argument("--k-min", type=int, default=5)
    ap.add_argument("--rho", type=float, default=3.0)
    ap.add_argument("--stacks", type=int, default=25)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    roles = json.loads(args.roles.read_text())
    runs = {"fleets": json.loads((args.results / args.fleets).read_text()),
            "od": json.loads((args.results / args.od).read_text())}
    if args.xfit_od:
        runs["xfit_od"] = json.loads((args.results / args.xfit_od).read_text())
    J = runs["fleets"]
    evaluated = set.intersection(*(set(J["folds"][f]) for f in args.test_folds))
    hosts = sorted((h for h in evaluated if h in roles), key=lambda h: -J["hosts"][h]["median_test_size"])
    alias = {h: f"E{i + 1}" for i, h in enumerate(hosts)}

    days = sorted(p for p in args.data_dir.iterdir()
                  if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}(_\d{4}-\d{2}-\d{2})?", p.name))
    recs = []
    for day in days:
        recs += build_windows(*load_day(day, "origin"))
    recs = [r for r in recs if r["host"] in alias]

    M = args.stacks
    out = {"stacks": M, "bands": {k: [lo + 1, hi] for k, (lo, hi) in BANDS.items()},
           "endpoints": {alias[h]: roles[h] for h in hosts}, "per_endpoint": {}, "check": {"folds": 0, "mismatches": 0}}
    for h in hosts:
        per = {}
        for f in args.test_folds:
            d = pd.Timestamp(f).date()
            cal = [r for r in recs if r["host"] == h and r["window"].date() < d]
            bg = pd.concat([r["clean"] for r in cal]).groupby(level=0).sum()
            P = (bg / bg.sum()).sort_values(ascending=False)
            N = int(bg.sum())
            phi = intra_window_correlation(cal, P, args.k_min)
            limit = 0.9 / (args.rho * M)
            above = (P + 1.0 / N) >= limit
            fold = {"profile_fingerprints": len(P), "tail_prevalence_median": float(P.iloc[10:].median()),
                    "enrichment_limit": limit, "fingerprints_above_limit": int(above.sum()),
                    "origin_share_above_limit": float(P[above].sum())}
            for run, R in runs.items():
                rec = R["folds"][f][h]
                out["check"]["folds"] += 1
                same = (rec["profile_fingerprints"] == len(P) and rec["profile_sessions"] == N
                        and np.isclose(rec["tail_prevalence_median"], fold["tail_prevalence_median"]))
                out["check"]["mismatches"] += not same
                # the level in logs; runs before the log-space test stored only the float
                log_lvl = (rec["scope_log10_level"] * np.log(10) if "scope_log10_level" in rec
                           else float(np.log(rec["scope_level"])))
                n0 = int(round(rec["median_origins"]))
                fam = rec["profile_fingerprints"] + M
                bands = {}
                for name, (lo, hi) in BANDS.items():
                    sel = P.iloc[lo:hi]
                    if len(sel) < M:
                        bands[name] = None      # too few fingerprints for a 25-stack botnet
                        continue
                    b = float(sel.median()) + 1.0 / N
                    row = {"fingerprints": int(len(sel)), "prevalence_median": b,
                           "binomial": floor_at(n0, lambda n: min_count(n, b, log_lvl, fam, args.rho), M=M, b=b, rho=args.rho)}
                    if run in ("od", "xfit_od"):
                        ph = float(phi.reindex(sel.index).median())
                        row["phi_median"] = ph
                        row["beta_binomial"] = floor_at(n0, lambda n: min_count_bb(n, b, ph, log_lvl, fam, args.rho),
                                                        M=M, b=b, rho=args.rho)
                    row["binomial_windows"] = row["binomial"] / n0 if row["binomial"] else None
                    if "beta_binomial" in row:
                        row["beta_binomial_windows"] = row["beta_binomial"] / n0 if row["beta_binomial"] else None
                    bands[name] = row
                fold[run] = {"median_origins": n0, "log10_level": float(log_lvl / np.log(10)), "bands": bands}
            per[f] = fold
        out["per_endpoint"][alias[h]] = per
    if out["check"]["mismatches"]:
        raise SystemExit(f"profile rebuild differs from the run in {out['check']['mismatches']} folds")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"OK: {args.out} ({out['check']['folds']} folds checked against the runs)")


if __name__ == "__main__":
    main()
