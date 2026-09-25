#!/usr/bin/env python3
"""Sprint 6 (NOMS) — choose the known-fleet share on design days, test it on held-out days.

The calibrated level is set by legitimate fleets (Appendix E): at a tenth of the
typical window it holds enrichment to 0.6% on the one endpoint in the stealth
regime. ``rule_detection_production.py --fleets SHARE`` takes the fingerprints the
test names, at the nominal level, in at least SHARE of the calibration windows as
known fleets: they leave the scope and the level's calibration.

The protocol was fixed before any fleet run was looked at:

- design days: the first three test days; held-out days: the last two;
- on design days, among the shares whose clean false alarms (Omega >= tau and a
  non-empty scope) do not exceed the base rule's, choose the one with the largest
  mean blocked share over the eight cells the paper reports (stacks new and
  shared, times 100 and 1,000 attackers, 1x and 0.1x the typical window); ties go
  to the smaller share, which excludes fewer fingerprints;
- report that share, and the base rule, on the held-out days.

Only rates and counts leave; endpoints are E1..E4 as in production_summary.py.

Usage:
    python fleet_selection.py --results $DATA_ROOT/azion/results --roles $DATA_ROOT/azion/roles.json \\
        --shares 0.005 0.01 0.02 0.05 --out ../results/fleet_profile.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CELLS = [("attack", "fresh", 100), ("attack", "fresh", 1000), ("attack_rel", "fresh", 1.0),
         ("attack_rel", "fresh", 0.1), ("attack", "tail", 100), ("attack", "tail", 1000),
         ("attack_rel", "tail", 1.0), ("attack_rel", "tail", 0.1)]
COLS = ["kind", "fold", "host", "size", "omega", "scope_named", "scope_recall", "scope_collateral",
        "union_named", "union_recall", "union_collateral", "source", "stacks", "attackers",
        "fraction", "flash"]


def load(path, k_min=5):
    W = pd.read_csv(path, usecols=lambda c: c in COLS, dtype={"fold": str})
    W = W[W["size"] >= k_min]
    cal = W[W["kind"] == "calib"].groupby(["fold", "host"])
    keys = list(zip(W["fold"], W["host"]))
    W = W.assign(om=W["omega"].to_numpy() >= cal["omega"].quantile(0.99).reindex(keys).to_numpy(),
                 org=W["size"].to_numpy() >= cal["size"].quantile(0.99).reindex(keys).to_numpy())
    for c in ("scope_named", "union_named"):
        W[c] = W[c].astype(bool)
    return W


def cell(W, kind, source, x):
    m = (W["kind"] == kind) & (W["source"] == source) & (W["stacks"] == 25)
    return W[m & ((W["attackers"] == x) if kind == "attack" else (W["fraction"] == x))]


def rates(W, gate="om", scope="scope"):
    """False alarms, collateral, flash firing and blocked shares of one configuration."""
    f = lambda d: d[gate] & d[f"{scope}_named"]
    c = W[W["kind"] == "clean"]
    fl = W[(W["kind"] == "flash") & (W["flash"] == 100)]
    out = {"clean_windows": int(len(c)), "false_alarms": int(f(c).sum()),
           "collateral_median": float(c.loc[f(c), f"{scope}_collateral"].median()) if f(c).any() else None,
           "flash100": float(f(fl).mean())}
    for kind, src, x in CELLS:
        d = cell(W, kind, src, x)
        out[f"{src}:{'A' if kind == 'attack' else 'x'}{x:g}"] = float((d[f"{scope}_recall"] * f(d)).mean())
    out["mean_blocked"] = float(np.mean([out[f"{s}:{'A' if k == 'attack' else 'x'}{x:g}"] for k, s, x in CELLS]))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--roles", required=True, type=Path)
    ap.add_argument("--base", default="rule_production_windows_rolling_origin.csv")
    ap.add_argument("--shares", nargs="+", default=["0.005", "0.01", "0.02", "0.05"])
    ap.add_argument("--design-folds", type=int, default=3)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    base = load(args.results / args.base)
    runs = {s: load(args.results / f"rule_production_windows_rolling_origin_fleets{s}.csv") for s in args.shares}
    folds = sorted(base["fold"].unique())
    design, held = folds[:args.design_folds], folds[args.design_folds:]
    sub = lambda W, fs: W[W["fold"].isin(fs)]

    # 1. choose on design days only
    b_design = rates(sub(base, design))
    cands = {s: rates(sub(W, design)) for s, W in runs.items()}
    ok = [s for s, r in cands.items() if r["false_alarms"] <= b_design["false_alarms"]]
    chosen = max(ok, key=lambda s: (round(cands[s]["mean_blocked"], 12), -float(s))) if ok else None

    # 2. then look at the held-out days
    roles = json.loads(args.roles.read_text())
    J = json.loads((args.results / "rule_production_rolling_origin.json").read_text())
    hosts = sorted((h for h in J["hosts"] if h in roles), key=lambda h: -J["hosts"][h]["median_test_size"])
    alias = {h: f"E{i + 1}" for i, h in enumerate(hosts)}
    out = {"protocol": {"design_days": len(design), "held_out_days": len(held),
                        "rule": "largest mean blocked over the eight cells, clean false alarms not above "
                                "the base rule's, on design days; ties to the smaller share"},
           "design": {"base": b_design, **{s: r for s, r in cands.items()}},
           "eligible": ok, "chosen_share": chosen}
    if chosen is not None:
        W = runs[chosen]
        out["held_out"] = {"base": rates(sub(base, held)), "fleets": rates(sub(W, held)),
                           "base_origins_union": rates(sub(base, held), "org", "union"),
                           "fleets_origins_union": rates(sub(W, held), "org", "union")}
        out["held_out_per_endpoint"] = {
            alias[h]: {"base": rates(sub(base[base["host"] == h], held)),
                       "fleets": rates(sub(W[W["host"] == h], held))} for h in hosts}
        # fleets per endpoint, from the run's fold records
        F = json.loads((args.results / f"rule_production_rolling_origin_fleets{chosen}.json").read_text())
        out["fleets_per_endpoint"] = {
            alias[h]: {"fleets": [F["folds"][f][h]["fleets"] for f in folds if h in F["folds"].get(f, {})],
                       "profile_share": [round(F["folds"][f][h]["fleet_share"], 4) for f in folds
                                         if h in F["folds"].get(f, {})],
                       "level": [F["folds"][f][h]["scope_level"] for f in folds if h in F["folds"].get(f, {})]}
            for h in hosts}
        out["self_check"] = F["self_check"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "held_out_per_endpoint"}, indent=2)[:6000])


if __name__ == "__main__":
    main()
