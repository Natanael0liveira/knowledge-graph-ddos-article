#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the anonymized summary of the production evaluation.

rule_detection_production.py writes its results next to the exports, on the data
drive, because they carry host names and volumes. This script reduces them to
what the paper reports and writes that to results/, where audit_paper.py checks
the paper against it:

- endpoints become E1, E2, ... in decreasing order of origins per window, each
  with a generic role read from a file kept on the drive and a volume band;
- only rates and shares leave: no host name, fingerprint, address, date or
  absolute volume.

Usage:
    python production_summary.py --results $DATA_ROOT/azion/results \\
        --roles $DATA_ROOT/azion/roles.json --out ../results/production_summary.json
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

BANDS = [(10, "< 10"), (100, "10-100"), (1000, "100-1,000"), (np.inf, "> 1,000")]


def band(v):
    return next(label for top, label in BANDS if v < top)


def pick(r, keys):
    return {k: r[k] for k in keys if k in r}


RATES = ["windows", "omega", "pipeline", "enrichment", "blocked_pipeline", "blocked_enrichment",
         "coverage_pipeline",
         "collateral_pipeline_median", "collateral_pipeline_max"] + \
        [f"{b}_{k}" for b in ("zscore", "unseen", "union")
         for k in ("pipeline", "blocked", "collateral_median", "collateral_max")] + \
        ["origins"] + [f"origins_{b}_{k}" for b in ("enrichment", "zscore", "unseen", "union")
                       for k in ("pipeline", "blocked", "collateral_median")]


def volume_baseline(windows_csv, k_min):
    """Omega >= tau against a plain threshold on the number of distinct origins.

    Both thresholds are the 99th percentile over the same calibration windows of
    each host and fold. Omega's endpoint term grows as the square of the origin
    count, so the two should nearly coincide; the summary says how nearly.
    """
    cols = ["kind", "fold", "host", "size", "omega", "scope_named", "source", "stacks", "attackers",
            "fraction"]
    W = pd.read_csv(windows_csv, usecols=lambda c: c in cols, dtype={"fold": str})
    W = W[W["size"] >= k_min]
    cal = W[W["kind"] == "calib"].groupby(["fold", "host"])
    keys = list(zip(W["fold"], W["host"]))
    W = W.assign(by_omega=W["omega"].to_numpy() >= cal["omega"].quantile(0.99).reindex(keys).to_numpy(),
                 by_origins=W["size"].to_numpy() >= cal["size"].quantile(0.99).reindex(keys).to_numpy())
    def rates(d):
        return {"windows": int(len(d)), "omega": float(d["by_omega"].mean()),
                "origins": float(d["by_origins"].mean()),
                "agreement": float((d["by_omega"] == d["by_origins"]).mean())}
    att = (W["kind"] == "attack") & (W["source"] == "fresh") & (W["stacks"] == 25)
    rel = (W["kind"] == "attack_rel") & (W["source"] == "fresh")
    out = {"clean": rates(W[W["kind"] == "clean"]),
           "attack_fresh_M25": {str(int(A)): rates(g) for A, g in W[att].groupby("attackers")},
           "attack_relative_M25": {f"x{f:g}": rates(g) for f, g in W[rel].groupby("fraction")}}
    agree = [out["clean"]["agreement"]] + [v["agreement"] for v in out["attack_fresh_M25"].values()] + \
            [v["agreement"] for v in out["attack_relative_M25"].values()]
    out["agreement_range"] = [min(agree), max(agree)]
    # Clean windows that only one gate admits, and how much of their Omega is not the
    # endpoint term (TLS and /24 pairs): fleets concentrate on one fingerprint.
    c = W[W["kind"] == "clean"]
    rest = 1 - 0.6 * c["size"] * (c["size"] - 1) / 2 / c["omega"]
    for name, m in (("omega_only", c["by_omega"] & ~c["by_origins"]),
                    ("origins_only", c["by_origins"] & ~c["by_omega"]),
                    ("both", c["by_omega"] & c["by_origins"])):
        out[f"clean_{name}"] = {"windows": int(m.sum()), "scope_named": int(c.loc[m, "scope_named"].sum()),
                                "non_endpoint_share_median": float(rest[m].median())}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", required=True, type=Path)
    ap.add_argument("--roles", required=True, type=Path, help="host -> generic role (kept on the drive)")
    ap.add_argument("--method", default="rule_production_rolling_origin.json")
    ap.add_argument("--nominal", nargs=2, default=["rule_production_rolling_session.json",
                                                   "rule_production_rolling_origin_nominal.json"],
                    help="the session count and the origin count at the nominal level")
    ap.add_argument("--rho", nargs="+", default=["rule_production_rolling_origin_rho2.json",
                                                 "rule_production_rolling_origin_rho5.json"],
                    help="the method at other enrichment ratios, for the sensitivity to rho")
    ap.add_argument("--attackers", type=int, nargs="+", default=[25, 50, 100, 250, 1000])
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    roles = json.loads(args.roles.read_text())
    J = json.loads((args.results / args.method).read_text())
    res = next(iter(J["by_percentile"].values()))        # tau at the first percentile
    hosts = sorted((h for h in J["hosts"] if h in roles),
                   key=lambda h: -J["hosts"][h]["median_test_size"])
    alias = {h: f"E{i + 1}" for i, h in enumerate(hosts)}

    endpoints = {}
    for h in hosts:
        v = J["hosts"][h]
        e = {"role": roles[h], "origins_per_window": band(v["median_test_size"]),
             "folds": v["folds"], "scope_level_median": v["scope_level"],
             # distinct fingerprints of the endpoint's profile, fewest and most over folds
             "profile_fingerprints": [min(f[h]["profile_fingerprints"] for f in J["folds"].values() if h in f),
                                      max(f[h]["profile_fingerprints"] for f in J["folds"].values() if h in f)],
             "waf_matched_share": res["waf"][h]["matched_waf_share"],
             "clean": pick(res["clean"][h], RATES),
             "flash": {N: pick(x[h], RATES) for N, x in res["flash"].items() if h in x},
             "attack_fresh_M25": {str(A): pick(res["attack"][f"fresh:M25:A{A}"][h], RATES)
                                  for A in args.attackers if h in res["attack"][f"fresh:M25:A{A}"]},
             "attack_tail_M25": {str(A): pick(res["attack"][f"tail:M25:A{A}"][h], RATES)
                                 for A in args.attackers if h in res["attack"].get(f"tail:M25:A{A}", {})},
             "attack_relative_M25": {k: pick(v[h], RATES) for k, v in res.get("attack_rel", {}).items()
                                     if h in v}}
        endpoints[alias[h]] = e

    def pooled(r):
        """Rates over the method's endpoints, weighted by windows, so variants that
        admit other hosts are compared on the same traffic."""
        def over(cells):
            cells = [c for c in cells if c and c.get("windows")]
            w = sum(c["windows"] for c in cells)
            out = {"windows": w}
            for k in ("omega", "pipeline", "enrichment", "blocked_pipeline",
                      "zscore_pipeline", "zscore_blocked", "unseen_pipeline", "unseen_blocked"):
                if all(c.get(k) is not None for c in cells):
                    out[k] = sum(c[k] * c["windows"] for c in cells) / w
            return out
        return {"clean": over([r["clean"].get(h) for h in hosts]),
                "flash": {N: over([x.get(h) for h in hosts]) for N, x in r["flash"].items()},
                "attack_fresh_M25": {str(A): over([r["attack"][f"fresh:M25:A{A}"].get(h) for h in hosts])
                                     for A in args.attackers}}

    variants = {"origin_calibrated": pooled(res)}
    for name, f in zip(("session_nominal", "origin_nominal"), args.nominal):
        if (args.results / f).exists():
            variants[name] = pooled(next(iter(json.loads((args.results / f).read_text())["by_percentile"].values())))
    # The method's own pooled row keeps medians and maxima, which do not aggregate.
    def all_row(r):
        return {"clean": pick(r["clean"]["all"], RATES),
                "flash": {N: pick(x["all"], RATES) for N, x in r["flash"].items()},
                "attack_fresh_M25": {str(A): pick(r["attack"][f"fresh:M25:A{A}"]["all"], RATES)
                                     for A in args.attackers},
                "attack_tail_M25": {str(A): pick(r["attack"][f"tail:M25:A{A}"]["all"], RATES)
                                    for A in args.attackers},
                "attack_relative_M25": {k: pick(v["all"], RATES) for k, v in r.get("attack_rel", {}).items()}}

    variants["origin_calibrated_all"] = all_row(res)
    for f in args.rho:
        if (args.results / f).exists():
            R = json.loads((args.results / f).read_text())
            if sorted(R["hosts"]) != sorted(J["hosts"]):
                raise SystemExit(f"{f} evaluates other hosts than {args.method}")
            variants[f"rho{R['config']['rho']:g}"] = all_row(next(iter(R["by_percentile"].values())))

    csv = args.results / args.method.replace("rule_production_", "rule_production_windows_").replace(".json", ".csv")
    volume = volume_baseline(csv, J["config"]["k_min"]) if csv.exists() else None
    waf = res["waf"]["all"]
    out = {"source": "aggregated access-log exports of a CDN operator, anonymized",
           "days": len(J["dates"]), "test_days": len(J["folds"]),
           "split": J["config"]["split"], "unit": J["config"]["unit"],
           "calibrate_level": J["config"]["calibrate_level"],
           "significance_cap": J["config"]["significance"], "k_min": J["config"]["k_min"],
           "self_check": J["self_check"],
           "endpoints": endpoints, "variants": variants, "volume_baseline": volume,
           "waf": {"matched_waf_share": waf["matched_waf_share"],
                   "waf_covered_share": waf["waf_covered_share"]}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(f"OK: {args.out} ({len(endpoints)} endpoints)")


if __name__ == "__main__":
    main()
