#!/usr/bin/env python3
"""Sprint 6 (NOMS) — sensitivity to the operational window W.

Appendix C of the paper states that sensitivity to W is not characterised. It is
cheap to characterise: the window only enters through assign_detection_clusters,
so sweeping it means recomputing the cross-session features on the SAME cached
scenarios and re-running the ablation. Nothing is regenerated.

W too small starves the cross-session evidence (few pairs inside a cluster, so
Omega stays below tau); W too large merges unrelated traffic into one cluster and
dilutes the discriminator. The sweep reports both the detection effect (per-config
ROC AUC) and the cost side (number of clusters and mean cluster size, which drive
the quadratic pair term measured by bench_latency.py).

Usage:
    python window_sweep.py --seeds 10 --K 1000 --W 60 120 300 600 1800 \\
        --dist-dir $DATA_ROOT/synth/distributions \\
        --work $DATA_ROOT/synth/sprint4 --out-dir ../results
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
from sklearn.ensemble import RandomForestClassifier

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path.insert(0, str(EXP / "sprint-3" / "scripts"))
sys.path.insert(0, str(EXP / "sprint-4" / "scripts"))
sys.path.insert(0, str(EXP / "sprint-1" / "scripts"))
from run_sprint4 import STRONG_SETS, ensure_scenario, boot_ci  # noqa: E402
from compute_coordination import (assign_detection_clusters,  # noqa: E402
                                  session_features, _is_attack)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def build_features_w(df: pd.DataFrame, window_s: int) -> pd.DataFrame:
    """Same as run_ablation.build_features, with the window as a parameter."""
    df = df.copy()
    df["start_ts"] = pd.to_datetime(df["start_ts"])
    df["end_ts"] = pd.to_datetime(df["end_ts"])
    df = assign_detection_clusters(df, window_s=window_s)
    df = session_features(df)
    df["has_identity"] = df["ja4"].notna().astype(int)
    return df


def auc_for(feats, df, y, itr, ite, seed=42):
    X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
    clf = RandomForestClassifier(n_estimators=200, random_state=seed,
                                 class_weight="balanced", n_jobs=-1)
    clf.fit(X[itr], y[itr])
    return roc_auc_score(y[ite], clf.predict_proba(X[ite])[:, 1])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--K", type=int, nargs="+", default=[1000])
    ap.add_argument("--W", type=int, nargs="+", default=[60, 120, 300, 600, 1800],
                    help="operational window in seconds")
    ap.add_argument("--dist-dir", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    rows = []
    for K in args.K:
        for seed in range(1, args.seeds + 1):
            p = ensure_scenario(py, args.dist_dir, args.work, K, seed)
            raw = pd.read_parquet(p)
            for W in args.W:
                df = build_features_w(raw, W)
                y = _is_attack(df["label_first"]).astype(int).values
                if y.sum() < 2 or y.sum() == len(y):
                    continue
                idx = np.arange(len(y))
                itr, ite = train_test_split(idx, test_size=0.3, random_state=42,
                                            stratify=y)
                row = {"K": K, "seed": seed, "W_s": W,
                       "n_clusters": int(df["det_cluster"].nunique()),
                       "mean_cluster_size": float(df.groupby("det_cluster").size().mean()),
                       "max_cluster_size": int(df.groupby("det_cluster").size().max())}
                for cfg, feats in STRONG_SETS.items():
                    row[cfg] = auc_for(feats, df, y, itr, ite)
                rows.append(row)
            log.info("K=%d seed=%d done (%d windows)", K, seed, len(args.W))

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "window_sweep_runs.csv", index=False)

    cfgs = list(STRONG_SETS)
    agg = {}
    for K in args.K:
        agg[f"K={K}"] = {}
        for W in args.W:
            sub = df[(df["K"] == K) & (df["W_s"] == W)]
            if not len(sub):
                continue
            e = {"n": int(len(sub)),
                 "n_clusters": float(sub["n_clusters"].mean()),
                 "mean_cluster_size": float(sub["mean_cluster_size"].mean()),
                 "max_cluster_size": float(sub["max_cluster_size"].mean())}
            for c in cfgs:
                m, lo, hi = boot_ci(sub[c].dropna().values)
                e[c] = {"mean": m, "ci95": [lo, hi]}
            agg[f"K={K}"][f"W={W}"] = e

    (args.out_dir / "window_sweep.json").write_text(json.dumps(
        {"seeds": args.seeds, "K": args.K, "W": args.W, "aggregate": agg}, indent=2))

    print("\n" + "=" * 84)
    print(f"WINDOW SWEEP — per-session ROC AUC [95% CI], n={args.seeds} seeds")
    print("=" * 84)
    for K in args.K:
        print(f"\nK = {K}")
        print(f"{'W (s)':>7} {'clusters':>9} {'mean |S|':>9} " +
              "".join(f"{c.split('_')[0]:>18}" for c in cfgs))
        print("-" * 84)
        for W in args.W:
            e = agg[f"K={K}"].get(f"W={W}")
            if not e:
                continue
            line = f"{W:>7} {e['n_clusters']:>9.0f} {e['mean_cluster_size']:>9.1f} "
            for c in cfgs:
                line += f"{e[c]['mean']:.3f}[{e[c]['ci95'][0]:.2f},{e[c]['ci95'][1]:.2f}]".rjust(18)
            print(line)
    print(f"\nOK: {args.out_dir}/window_sweep.json + window_sweep_runs.csv")


if __name__ == "__main__":
    main()
