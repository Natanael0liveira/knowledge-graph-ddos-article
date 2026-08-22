#!/usr/bin/env python3
"""Sprint 6 (NOMS) — is the per-session collapse specific to Random Forest?

The paper's central claim is that in the stealthy distributed regime NO
per-session detector separates attack from benign. Sprint 4 supports that with a
single hypothesis class (Random Forest). A reviewer can reasonably object that
one model family does not license a universal claim, so this script re-runs the
ablation across four families over the SAME strong flow feature set and the SAME
train/test split:

    rf      RandomForest                  (what Sprint 4 used)
    hgb     HistGradientBoosting          (histogram GBDT, LightGBM-style)
    mlp     MLPClassifier                 (non-linear, standardised inputs)
    logreg  LogisticRegression            (linear, standardised inputs)

xgboost is installed in the venv but its shared library does not load on this
machine (missing libomp), so HistGradientBoosting stands in for the boosted-tree
family; it is the same algorithm class and ships with scikit-learn.

Configurations (a) and (d) are the contrast that matters, but all four ablation
configs are computed so the table stays comparable with Sprint 4.

Reuses the scenario cache produced by run_sprint4.py: if the (K, seed) parquets
already exist under --work, nothing is regenerated.

Usage:
    python run_ml_families.py --seeds 30 --K 50 1000 \\
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
from scipy.stats import wilcoxon
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path.insert(0, str(EXP / "sprint-3" / "scripts"))
sys.path.insert(0, str(EXP / "sprint-4" / "scripts"))
sys.path.insert(0, str(EXP / "sprint-1" / "scripts"))
from run_ablation import build_features  # noqa: E402
from run_sprint4 import STRONG_SETS, ensure_scenario, boot_ci, cohens_d  # noqa: E402
from compute_coordination import _is_attack  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def models(seed):
    """Estimator factories. Scale-sensitive models get a StandardScaler."""
    return {
        "rf": RandomForestClassifier(n_estimators=200, random_state=seed,
                                     class_weight="balanced", n_jobs=-1),
        "hgb": HistGradientBoostingClassifier(random_state=seed,
                                              class_weight="balanced"),
        "mlp": make_pipeline(
            StandardScaler(),
            MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=600,
                          random_state=seed, early_stopping=True)),
        "logreg": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=2000, class_weight="balanced",
                               random_state=seed)),
    }


def one_run(parquet, seed=42):
    """AUC per (model, config) on one scenario, sharing the split across models."""
    df = build_features(pd.read_parquet(parquet))
    y = _is_attack(df["label_first"]).astype(int).values
    if y.sum() < 2 or y.sum() == len(y):
        return None
    idx = np.arange(len(y))
    itr, ite = train_test_split(idx, test_size=0.3, random_state=seed, stratify=y)
    out = {}
    for cfg, feats in STRONG_SETS.items():
        X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
        for mname, est in models(seed).items():
            try:
                est.fit(X[itr], y[itr])
                out[f"{mname}|{cfg}"] = roc_auc_score(
                    y[ite], est.predict_proba(X[ite])[:, 1])
            except Exception as e:  # a family may fail to converge on a seed
                log.warning("%s/%s failed: %s", mname, cfg, e)
                out[f"{mname}|{cfg}"] = float("nan")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--K", type=int, nargs="+", default=[50, 1000])
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
            r = one_run(p)
            if r:
                r.update({"K": K, "seed": seed})
                rows.append(r)
        log.info("K=%d: %d runs", K, sum(1 for x in rows if x["K"] == K))

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "ml_families_runs.csv", index=False)

    fams = list(models(0))
    cfgs = list(STRONG_SETS)
    agg, tests = {}, {}
    n_tests = len(fams) * len(args.K)
    for K in args.K:
        sub = df[df["K"] == K]
        agg[f"K={K}"] = {"n": int(len(sub))}
        tests[f"K={K}"] = {}
        for m in fams:
            for c in cfgs:
                col = f"{m}|{c}"
                mean, lo, hi = boot_ci(sub[col].dropna().values)
                agg[f"K={K}"][col] = {"mean": mean, "ci95": [lo, hi]}
            a, d = sub[f"{m}|a_ml_sem_ontologia"].values, sub[f"{m}|d_completo"].values
            try:
                _, p = wilcoxon(d, a)
            except ValueError:
                p = 1.0
            tests[f"K={K}"][m] = {"wilcoxon_p": float(p),
                                  "p_bonferroni": float(min(1.0, p * n_tests)),
                                  "cohens_d": cohens_d(d, a),
                                  "mean_delta": float((d - a).mean())}

    (args.out_dir / "ml_families.json").write_text(json.dumps(
        {"seeds": args.seeds, "K": args.K, "families": fams,
         "n_tests_bonferroni": n_tests, "aggregate": agg, "tests": tests}, indent=2))

    print("\n" + "=" * 82)
    print(f"ML FAMILIES — per-session ROC AUC [95% CI], n={args.seeds} seeds")
    print("=" * 82)
    for K in args.K:
        print(f"\nK = {K}")
        print(f"{'family':<8}" + "".join(f"{c.split('_')[0]:>18}" for c in cfgs))
        print("-" * 80)
        for m in fams:
            line = f"{m:<8}"
            for c in cfgs:
                cc = agg[f"K={K}"][f"{m}|{c}"]
                line += f"{cc['mean']:.3f}[{cc['ci95'][0]:.2f},{cc['ci95'][1]:.2f}]".rjust(18)
            print(line)
        print("  (d)-(a) per family:")
        for m in fams:
            t = tests[f"K={K}"][m]
            print(f"    {m:<8} delta={t['mean_delta']:+.3f}  "
                  f"p_bonf={t['p_bonferroni']:.2e}  d={t['cohens_d']:+.2f}")
    print(f"\nOK: {args.out_dir}/ml_families.json + ml_families_runs.csv")


if __name__ == "__main__":
    main()
