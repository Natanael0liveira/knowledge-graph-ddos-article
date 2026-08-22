#!/usr/bin/env python3
"""Sprint 6 (NOMS) — collateral damage as a function of discriminator purity.

The headline collateral result (0% surgical vs 100% global) is, in the synthetic
setting, close to definitional: the generator draws the botnet JA4 from a
namespace disjoint from the benign pool, so ZERO benign sessions carry it, and a
filter on that fingerprint cannot hit anyone but attackers. Meanwhile every
benign session sits on the attacked endpoint, so a global endpoint rate limit
hits 100% of them by construction. Neither number measures how the mechanism
behaves when the discriminator is imperfect --- which is the realistic case: a
botnet on stock Chrome, or one using curl-impersonate, shares its fingerprint
with a real legitimate population.

This sweep makes the result empirical. For each cached scenario we plant the
attacker's modal JA4 in a fraction p of BENIGN sessions --- simulating a botnet
whose fingerprint is also carried by legitimate users --- and measure what the
derived scope then costs. Flow attributes are untouched: the question here is
mitigation precision, not detection.

Two things are worth watching, and only the second is predictable:
  1. surgical collateral should track p (the benign prevalence of the
     discriminator), giving an operator decision rule;
  2. at some p the scope derivation may BREAK --- benign sessions enter the
     coordinated subset, or the JA4 coverage test fails and the scope falls back
     to endpoint-only, at which point surgical collapses onto global. Where that
     happens is the non-obvious result.

Usage:
    python collateral_purity_sweep.py --scenarios $DATA_ROOT/synth/sprint4_realistic_work \\
        --p 0 0.001 0.005 0.01 0.05 0.1 0.25 0.5 --max-files 30 --out-dir ../results
"""
import argparse
import json
import logging
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path.insert(0, str(EXP / "sprint-1" / "scripts"))
sys.path.insert(0, str(EXP / "pillar4-evidence-mitigation" / "scripts"))
from compute_coordination import assign_detection_clusters, compute_omega  # noqa: E402
from evidence_mitigation import derive_scope, matches_scope  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def plant_ja4(df, p, seed):
    """Give a fraction p of benign sessions the attacker's modal JA4."""
    df = df.copy()
    atk = df[df["label_first"] == "ATTACK"]
    if not len(atk) or atk["ja4"].isna().all():
        return df, None
    botnet_ja4 = atk["ja4"].value_counts().index[0]
    ben_idx = df.index[df["label_first"] == "BENIGN"]
    k = int(round(p * len(ben_idx)))
    if k > 0:
        rng = np.random.default_rng(seed)
        chosen = rng.choice(ben_idx.values, size=min(k, len(ben_idx)), replace=False)
        df.loc[chosen, "ja4"] = botnet_ja4
    return df, botnet_ja4


def eval_one(df, coverage):
    df = df.copy()
    df["start_ts"] = pd.to_datetime(df["start_ts"])
    df["end_ts"] = pd.to_datetime(df["end_ts"])
    d = assign_detection_clusters(df, 300)
    cl = compute_omega(d)
    atk = cl[cl["attack_frac"] >= 0.5]
    if not len(atk):
        return None
    top = atk.sort_values("omega", ascending=False).iloc[0]
    cluster = d[d["det_cluster"] == top["det_cluster"]]
    scope = derive_scope(cluster, coverage=coverage)
    benign = df[df["label_first"] == "BENIGN"]
    if not len(benign):
        return None
    surgical = float(matches_scope(benign, scope).mean())
    ep = scope.get("endpoint")
    bep = benign["dst_ip_first"].astype(str) + ":" + benign["dst_port_first"].astype(str)
    glob = float((bep == ep).mean()) if ep else 0.0
    return {"surgical": surgical, "global": glob,
            "ja4_in_scope": "tlsJa4" in scope,
            "scope_keys": "+".join(sorted(scope)),
            "cluster_attack_frac": float(top["attack_frac"]),
            "cluster_size": int(len(cluster))}


def boot_ci(v, rng):
    v = np.asarray(v, dtype=float)
    if not len(v):
        return (float("nan"),) * 3
    m = [rng.choice(v, len(v), replace=True).mean() for _ in range(2000)]
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", required=True, type=Path)
    ap.add_argument("--p", type=float, nargs="+",
                    default=[0.0, 0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5])
    ap.add_argument("--coverage", type=float, default=0.5)
    ap.add_argument("--max-files", type=int, default=30)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(p for p in args.scenarios.glob("K1000_*.parquet")
                   if not p.name.startswith("._"))[: args.max_files]
    if not files:
        log.error("no scenarios in %s", args.scenarios)
        return
    log.info("%d scenarios, %d purity levels", len(files), len(args.p))

    rows = []
    for i, f in enumerate(files):
        raw = pd.read_parquet(f)
        for p in args.p:
            df, ja4 = plant_ja4(raw, p, seed=1000 + i)
            r = eval_one(df, args.coverage)
            if r:
                r.update({"scenario": f.stem, "p": p, "botnet_ja4": ja4})
                rows.append(r)
        log.info("[%d/%d] %s", i + 1, len(files), f.stem)

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "collateral_purity_runs.csv", index=False)

    rng = np.random.default_rng(42)
    agg = {}
    for p in args.p:
        sub = df[df["p"] == p]
        if not len(sub):
            continue
        sm, slo, shi = boot_ci(sub["surgical"].values, rng)
        gm, glo, ghi = boot_ci(sub["global"].values, rng)
        agg[str(p)] = {
            "n": int(len(sub)),
            "surgical": {"mean": sm, "ci95": [slo, shi]},
            "global": {"mean": gm, "ci95": [glo, ghi]},
            "ja4_in_scope_frac": float(sub["ja4_in_scope"].mean()),
            "scope_shapes": sub["scope_keys"].value_counts().to_dict(),
            "cluster_attack_frac": float(sub["cluster_attack_frac"].mean()),
        }

    (args.out_dir / "collateral_purity.json").write_text(json.dumps(
        {"coverage": args.coverage, "p": args.p, "n_scenarios": len(files),
         "aggregate": agg}, indent=2))

    print("\n" + "=" * 88)
    print("COLLATERAL vs DISCRIMINATOR PURITY  (p = benign prevalence of the botnet JA4)")
    print("=" * 88)
    print(f"{'p':>7} {'surgical':>20} {'global':>20} {'JA4 in scope':>13} {'scope shape':>22}")
    print("-" * 88)
    for p in args.p:
        a = agg.get(str(p))
        if not a:
            continue
        s, g = a["surgical"], a["global"]
        shape = max(a["scope_shapes"], key=a["scope_shapes"].get)
        print(f"{p:>7.3f} "
              f"{s['mean']*100:>7.2f}% [{s['ci95'][0]*100:5.2f},{s['ci95'][1]*100:5.2f}] "
              f"{g['mean']*100:>7.2f}% [{g['ci95'][0]*100:5.2f},{g['ci95'][1]*100:5.2f}] "
              f"{a['ja4_in_scope_frac']*100:>12.0f}% {shape:>22}")
    print(f"\nOK: {args.out_dir}/collateral_purity.json + collateral_purity_runs.csv")


if __name__ == "__main__":
    main()
