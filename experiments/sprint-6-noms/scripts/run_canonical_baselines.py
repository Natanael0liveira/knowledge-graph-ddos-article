#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the academic baselines on the canonical realistic scenario.

Table II reported three baseline rows that no committed result file produced:
run_canonical_realistic.py never ran them, and the sprint-4 figures come from the
superseded monolithic scenario. This script runs them on the same cached
scenarios (alpha = 1.5, 25 stacks, n = 30, K in {50, 1000}), with the same strong
flow features and the same 70/30 stratified split (random_state = 42) that
run_canonical_realistic.py uses for the classifier families.

Usage:
    python run_canonical_baselines.py --work $DATA_ROOT/synth/sprint6_realistic \\
        --out-dir ../results
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "sprint-1" / "scripts"), str(EXP / "sprint-3" / "scripts"),
                str(EXP / "sprint-4" / "scripts")]
from baselines import BASELINES  # noqa: E402
from compute_coordination import _is_attack  # noqa: E402
from run_ablation import build_features  # noqa: E402
from run_sprint4 import STRONG_FLOW, boot_ci  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--alpha", type=float, default=1.5)
    ap.add_argument("--stacks", type=int, default=25)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--K", type=int, nargs="+", default=[50, 1000])
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for K in args.K:
        for seed in range(1, args.seeds + 1):
            pq = args.work / f"a{args.alpha}_m{args.stacks}_adv0_K{K}_seed{seed}.parquet"
            df = build_features(pd.read_parquet(pq))
            y = _is_attack(df["label_first"]).astype(int).values
            X = df[STRONG_FLOW].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
            itr, ite = train_test_split(np.arange(len(y)), test_size=0.3,
                                        random_state=42, stratify=y)
            r = {"K": K, "seed": seed}
            for name, (fn, _) in BASELINES.items():
                try:
                    r[name] = roc_auc_score(y[ite], fn(X[itr], X[ite], y[itr]))
                except Exception as e:                       # noqa: BLE001
                    log.warning("%s K=%d seed=%d: %s", name, K, seed, e)
                    r[name] = float("nan")
            rows.append(r)
        log.info("K=%d done", K)

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "canonical_baselines_runs.csv", index=False)
    agg = {}
    for K in args.K:
        sub = df[df["K"] == K]
        agg[f"K={K}"] = {"n": int(len(sub))}
        for name in BASELINES:
            mean, lo, hi = boot_ci(sub[name].dropna().values)
            agg[f"K={K}"][name] = {"mean": mean, "ci95": [lo, hi]}
    (args.out_dir / "canonical_baselines.json").write_text(json.dumps(
        {"alpha": args.alpha, "stacks": args.stacks, "seeds": args.seeds, "K": args.K,
         "features": STRONG_FLOW, "aggregate": agg}, indent=2))
    print(f"\n{'baseline':<20}" + "".join(f"{f'K={K}':>22}" for K in args.K))
    for name in BASELINES:
        print(f"{name:<20}" + "".join(
            f"{agg[f'K={K}'][name]['mean']:.3f} [{agg[f'K={K}'][name]['ci95'][0]:.2f},"
            f"{agg[f'K={K}'][name]['ci95'][1]:.2f}]".rjust(22) for K in args.K))
    print(f"\nOK: {args.out_dir}/canonical_baselines.json")


if __name__ == "__main__":
    main()
