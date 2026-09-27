#!/usr/bin/env python3
"""Sprint 6 (NOMS) — how many fingerprints the rolling profile has never seen.

The unseen filter names every fingerprint absent from the endpoint's profile that
reaches k_min origins in a window, so a browser or application release that gives
a large population a new JA4 would reach it at once. This script measures that
churn on the production exports, fold by fold, with the same profile the rule
uses: each test day against the clean origin-fingerprint counts of every day
before it (rolling split, the first test day after three days of history).

Per endpoint and test day it reports, over the windows of at least k_min origins:
- how many distinct fingerprints absent from the profile appear at all, and how
  many reach k_min origins in some window (the unseen filter's candidates);
- the share of windows holding at least one such candidate;
- the median and largest share of a window's origins on fingerprints absent from
  the profile.

Only counts and rates leave; the endpoints are E1..E4 as in production_tables.py.

Usage:
    python ja4_churn.py --results $DATA_ROOT/azion/results --roles $DATA_ROOT/azion/roles.json \\
        --data-dir $DATA_ROOT/azion --base rule_production_rolling_origin_v2.json \\
        --out ../results/ja4_churn.json
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


def churn(recs, host, day, k_min):
    """The unseen-fingerprint churn of one host on one test day."""
    cal = [r for r in recs if r["host"] == host and r["window"].date() < day]
    test = [r for r in recs if r["host"] == host and r["window"].date() == day and r["n"] >= k_min]
    seen = set().union(*(set(r["clean"].index) for r in cal)) if cal else set()
    new_any, new_kmin, share, with_cand = set(), set(), [], 0
    for r in test:
        c = r["clean"]
        unseen = c[~c.index.isin(seen)]
        new_any |= set(unseen.index)
        cand = set(unseen[unseen >= k_min].index)
        new_kmin |= cand
        with_cand += bool(cand)
        share.append(float(unseen.sum() / r["n"]) if r["n"] else 0.0)
    return {"windows": len(test), "profile_fingerprints": len(seen),
            "new_fingerprints": len(new_any), "new_fingerprints_kmin": len(new_kmin),
            "windows_with_candidate": with_cand,
            "windows_with_candidate_share": (with_cand / len(test)) if test else None,
            "unseen_origin_share_median": float(np.median(share)) if share else None,
            "unseen_origin_share_max": float(max(share)) if share else None}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--roles", required=True, type=Path)
    ap.add_argument("--base", required=True, help="the base run's JSON, for the endpoints and their order")
    ap.add_argument("--test-folds", nargs="+", default=["2026-09-20", "2026-09-21", "2026-09-22",
                                                        "2026-09-23", "2026-09-24"])
    ap.add_argument("--fresh-folds", nargs="+", default=["2026-09-25"])
    ap.add_argument("--k-min", type=int, default=5)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    roles = json.loads(args.roles.read_text())
    J = json.loads((args.results / args.base).read_text())
    evaluated = set.intersection(*(set(J["folds"][f]) for f in args.test_folds))
    hosts = sorted((h for h in evaluated if h in roles), key=lambda h: -J["hosts"][h]["median_test_size"])
    alias = {h: f"E{i + 1}" for i, h in enumerate(hosts)}

    days = sorted(p for p in args.data_dir.iterdir()
                  if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}(_\d{4}-\d{2}-\d{2})?", p.name))
    recs = []
    for day in days:
        recs += build_windows(*load_day(day, "origin"))
    recs = [r for r in recs if r["host"] in alias]

    out = {"k_min": args.k_min, "endpoints": {alias[h]: roles[h] for h in hosts}, "per_endpoint": {}}
    for h in hosts:
        out["per_endpoint"][alias[h]] = {
            f: churn(recs, h, pd.Timestamp(f).date(), args.k_min) for f in args.test_folds + args.fresh_folds}
    for block, folds in (("test_days", args.test_folds), ("fresh_day", args.fresh_folds)):
        rows = [out["per_endpoint"][e][f] for e in out["per_endpoint"] for f in folds]
        w = sum(r["windows"] for r in rows)
        out[block] = {"windows": w,
                      "windows_with_candidate_share": sum(r["windows_with_candidate"] for r in rows) / w if w else None,
                      "new_fingerprints_kmin_per_endpoint_day": [r["new_fingerprints_kmin"] for r in rows]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"OK: {args.out}")


if __name__ == "__main__":
    main()
