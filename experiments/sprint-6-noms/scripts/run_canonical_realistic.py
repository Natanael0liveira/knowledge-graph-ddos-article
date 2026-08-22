#!/usr/bin/env python3
"""Sprint 6 (NOMS) — canonical ablation on the PRODUCTION-REALISTIC scenario.

Replaces the historical canonical run (sprint-4, alpha=0 flat benign JA4 pool,
monolithic botnet) with the corrected scenario: Zipf-shaped benign fingerprint
popularity and a heterogeneous botnet. Reports the four ablation configurations
across four model families, with bootstrap CIs, paired Wilcoxon and Cohen's d.

Defaults: alpha=1.5 (39% head share; the calibrated real distribution measured
over ~322k benign sessions has a 52.7% head) and 25 botnet stacks.

Resource discipline: sequential, nice'd externally, estimators capped at
n_jobs=2, one scenario in memory at a time.

Usage:
    python run_canonical_realistic.py --seeds 30 --K 50 1000 --alpha 1.5 --stacks 25 \\
        --dist-dir $DATA_ROOT/synth/distributions \\
        --work $DATA_ROOT/synth/sprint6_realistic --out-dir ../results
"""
import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
S2 = EXP / "sprint-2" / "scripts"
sys.path[:0] = [str(EXP / "sprint-1" / "scripts"), str(EXP / "sprint-3" / "scripts"),
                str(EXP / "sprint-4" / "scripts"), str(HERE.parent)]
from run_ablation import build_features  # noqa: E402
from run_sprint4 import STRONG_SETS, boot_ci, cohens_d  # noqa: E402
from compute_coordination import _is_attack  # noqa: E402
from run_ml_families import models  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
STEALTH_CFG = S2.parent / "configs" / "scenario_stealth.yaml"


def ensure(py, dist_dir, work, alpha, stacks, K, seed):
    tag = f"a{alpha}_m{stacks}_adv0_K{K}_seed{seed}"
    pq = work / f"{tag}.parquet"
    if pq.exists():
        return pq
    jl = work / f"{tag}.jsonl"
    subprocess.run([py, str(S2 / "generator.py"), "--config", str(STEALTH_CFG),
                    "--param", f"K={K}",
                    "--param", f"benign_ja4_zipf_alpha={alpha}",
                    "--param", f"botnet_ja4_stacks={stacks}",
                    "--param", "botnet_ja4_adversarial=false",
                    "--seed", str(seed), "--distributions", str(dist_dir),
                    "--out", str(jl)], check=True, capture_output=True)
    subprocess.run([py, str(S2 / "synth_to_sessions.py"), "--jsonl", str(jl),
                    "--out", str(pq)], check=True, capture_output=True)
    jl.unlink(missing_ok=True)
    return pq


def one_run(pq, seed=42):
    df = build_features(pd.read_parquet(pq))
    y = _is_attack(df["label_first"]).astype(int).values
    if y.sum() < 2 or y.sum() == len(y):
        return None
    itr, ite = train_test_split(np.arange(len(y)), test_size=0.3,
                                random_state=seed, stratify=y)
    out = {}
    for cfg, feats in STRONG_SETS.items():
        X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
        for mname, est in models(seed).items():
            try:
                est.fit(X[itr], y[itr])
                out[f"{mname}|{cfg}"] = roc_auc_score(
                    y[ite], est.predict_proba(X[ite])[:, 1])
            except Exception as e:
                log.warning("%s/%s: %s", mname, cfg, e)
                out[f"{mname}|{cfg}"] = float("nan")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--K", type=int, nargs="+", default=[50, 1000])
    ap.add_argument("--alpha", type=float, default=1.5)
    ap.add_argument("--stacks", type=int, default=25)
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
            pq = ensure(py, args.dist_dir, args.work, args.alpha, args.stacks, K, seed)
            r = one_run(pq)
            if r:
                r.update({"K": K, "seed": seed})
                rows.append(r)
        log.info("K=%d done (%d runs)", K, sum(1 for x in rows if x["K"] == K))

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "canonical_realistic_runs.csv", index=False)

    fams, cfgs = list(models(0)), list(STRONG_SETS)
    n_tests = 2 * len(args.K)
    agg, tests = {}, {}
    for K in args.K:
        sub = df[df["K"] == K]
        agg[f"K={K}"] = {"n": int(len(sub))}
        for m in fams:
            for c in cfgs:
                mean, lo, hi = boot_ci(sub[f"{m}|{c}"].dropna().values)
                agg[f"K={K}"][f"{m}|{c}"] = {"mean": mean, "ci95": [lo, hi]}
        tests[f"K={K}"] = {}
        for rival in ("c_so_network_proximity", "a_ml_sem_ontologia"):
            d, r = sub["rf|d_completo"].values, sub[f"rf|{rival}"].values
            try:
                _, p = wilcoxon(d, r)
            except ValueError:
                p = 1.0
            tests[f"K={K}"][f"d_vs_{rival[0]}"] = {
                "wilcoxon_p": float(p), "p_bonferroni": float(min(1.0, p * n_tests)),
                "cohens_d": cohens_d(d, r), "mean_delta": float((d - r).mean())}

    (args.out_dir / "canonical_realistic.json").write_text(json.dumps(
        {"alpha": args.alpha, "stacks": args.stacks, "seeds": args.seeds,
         "K": args.K, "families": fams, "aggregate": agg, "tests": tests}, indent=2))

    print("\n" + "=" * 86)
    print(f"CANONICAL (REALISTIC) — alpha={args.alpha}, {args.stacks} stacks, "
          f"n={args.seeds} seeds. Per-session ROC AUC [95% CI]")
    print("=" * 86)
    for K in args.K:
        print(f"\nK = {K}")
        print(f"{'family':<8}" + "".join(f"{c.split('_')[0]:>19}" for c in cfgs))
        print("-" * 84)
        for m in fams:
            line = f"{m:<8}"
            for c in cfgs:
                cc = agg[f"K={K}"][f"{m}|{c}"]
                line += f"{cc['mean']:.3f}[{cc['ci95'][0]:.2f},{cc['ci95'][1]:.2f}]".rjust(19)
            print(line)
        for k2, t in tests[f"K={K}"].items():
            print(f"   {k2}: delta={t['mean_delta']:+.3f}  "
                  f"p_bonf={t['p_bonferroni']:.2e}  d={t['cohens_d']:+.2f}")
    print(f"\nOK: {args.out_dir}/canonical_realistic.json")


if __name__ == "__main__":
    main()
