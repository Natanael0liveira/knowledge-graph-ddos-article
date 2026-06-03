#!/usr/bin/env python3
"""Sprint 4 — full statistical execution of the ablation (n≥30 seeds).

For each (K, seed): generate a stealthy scenario (Sprint-2 generator), convert to
sessions, run the a/b/c/d ablation + baselines, collect per-session ROC AUC.
Then aggregate with bootstrap CIs and test (d)−(c) and (d)−(a) with the paired
Wilcoxon signed-rank test (+ Bonferroni + Cohen's d).

Gates: n≥30/config; (d)−(c) significant in Scenario C at p<0.01 after Bonferroni.

Usage:
    python run_sprint4.py --seeds 30 --K 50 1000 --out-dir $DATA_ROOT/results
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

HERE = Path(__file__).resolve()
S2 = HERE.parents[2] / "sprint-2" / "scripts"
S3 = HERE.parents[2] / "sprint-3" / "scripts"
sys.path.insert(0, str(S3))
from run_ablation import build_features, FEATURE_SETS, auc_for, FLOW  # noqa: E402
from baselines import BASELINES  # noqa: E402
sys.path.insert(0, str(HERE.parents[2] / "sprint-1" / "scripts"))
from compute_coordination import _is_attack  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

STEALTH_CFG = S2.parent / "configs" / "scenario_stealth.yaml"

# Baseline por-sessão FORTE (8 features de fluxo) — para não inflar o gap cross-session
# com um baseline sub-dimensionado. Espelha STRONG_FLOW de run_real_multiattack.
STRONG_FLOW = FLOW + ["fwd_bytes_sum", "bwd_bytes_sum", "fwd_pkts_sum",
                      "bwd_pkts_sum", "iat_mean_mean", "iat_std_mean"]
STRONG_SETS = {
    "a_ml_sem_ontologia":      STRONG_FLOW,
    "b_ontologia_sem_related": STRONG_FLOW + ["has_identity", "dst_port_first"],
    "c_so_network_proximity":  STRONG_FLOW + ["share_net"],
    "d_completo":              STRONG_FLOW + ["share_ja4", "share_net", "cluster_size"],
}


def ensure_scenario(py, dist_dir, work, K, seed):
    """Generate + convert one (K,seed) stealth scenario; cached."""
    parquet = work / f"K{K}_seed{seed}.parquet"
    if parquet.exists():
        return parquet
    jsonl = work / f"K{K}_seed{seed}.jsonl"
    subprocess.run([py, str(S2 / "generator.py"), "--config", str(STEALTH_CFG),
                    "--param", f"K={K}", "--seed", str(seed),
                    "--distributions", str(dist_dir), "--out", str(jsonl)],
                   check=True, capture_output=True)
    subprocess.run([py, str(S2 / "synth_to_sessions.py"), "--jsonl", str(jsonl),
                    "--out", str(parquet)], check=True, capture_output=True)
    jsonl.unlink(missing_ok=True)
    return parquet


def one_run(parquet, feature_sets=FEATURE_SETS, base_flow=FLOW):
    df = build_features(pd.read_parquet(parquet))
    y = _is_attack(df["label_first"]).astype(int).values
    if y.sum() < 2 or y.sum() == len(y):
        return None
    out = {}
    for cfg, feats in feature_sets.items():
        out[cfg], _ = auc_for(feats, df, y)
    Xa = df[base_flow].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
    Xtr, Xte, ytr, yte = train_test_split(Xa, y, test_size=0.3, random_state=42,
                                          stratify=y)
    for bname, (fn, _) in BASELINES.items():
        try:
            out[f"base:{bname}"] = roc_auc_score(yte, fn(Xtr, Xte, ytr))
        except Exception:
            out[f"base:{bname}"] = float("nan")
    return out


def boot_ci(vals, n=2000, rng=None):
    rng = rng or np.random.default_rng(42)
    vals = np.asarray(vals)
    means = [rng.choice(vals, len(vals), replace=True).mean() for _ in range(n)]
    return float(vals.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def cohens_d(a, b):
    a, b = np.asarray(a), np.asarray(b)
    diff = a - b
    return float(diff.mean() / (diff.std(ddof=1) + 1e-12))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--K", type=int, nargs="+", default=[50, 1000])
    ap.add_argument("--dist-dir", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--strong", action="store_true",
                    help="usa baseline por-sessão FORTE (8 features de fluxo) em todas as "
                         "configs — gap cross-session honesto, não inflado por baseline magro")
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    feature_sets = STRONG_SETS if args.strong else FEATURE_SETS
    base_flow = STRONG_FLOW if args.strong else FLOW
    log.info("Baseline por-sessão: %s (%d features)",
             "FORTE" if args.strong else "magro", len(base_flow))

    rows = []
    for K in args.K:
        for seed in range(1, args.seeds + 1):
            p = ensure_scenario(py, args.dist_dir, args.work, K, seed)
            r = one_run(p, feature_sets, base_flow)
            if r:
                r.update({"K": K, "seed": seed})
                rows.append(r)
        log.info("K=%d: %d runs concluídos", K, sum(1 for x in rows if x["K"] == K))

    df = pd.DataFrame(rows)
    configs = list(feature_sets) + [f"base:{b}" for b in BASELINES]

    # ---- agregação + CIs ----
    agg = {}
    for K in args.K:
        sub = df[df["K"] == K]
        agg[f"K={K}"] = {"n": int(len(sub)), "configs": {}}
        for c in configs:
            m, lo, hi = boot_ci(sub[c].dropna().values)
            agg[f"K={K}"]["configs"][c] = {"mean": m, "ci95": [lo, hi]}

    # ---- testes pareados (d vs c) e (d vs a) por cenário ----
    n_tests = 2 * len(args.K)  # Bonferroni
    tests = {}
    for K in args.K:
        sub = df[df["K"] == K]
        tests[f"K={K}"] = {}
        for rival in ("c_so_network_proximity", "a_ml_sem_ontologia"):
            d, r = sub["d_completo"].values, sub[rival].values
            try:
                stat, p = wilcoxon(d, r)
            except ValueError:  # all-zero diffs
                stat, p = float("nan"), 1.0
            tests[f"K={K}"][f"d_vs_{rival[0]}"] = {
                "wilcoxon_p": float(p),
                "p_bonferroni": float(min(1.0, p * n_tests)),
                "cohens_d": cohens_d(d, r),
                "mean_delta": float((d - r).mean()),
            }

    result = {"seeds": args.seeds, "K": args.K, "n_tests_bonferroni": n_tests,
              "aggregate": agg, "tests": tests}
    (args.out_dir / "sprint4_aggregated.json").write_text(json.dumps(result, indent=2))
    df.to_csv(args.out_dir / "sprint4_runs.csv", index=False)

    # ---- relatório ----
    print("\n" + "=" * 76)
    print(f"SPRINT 4 — ABLAÇÃO ESTATÍSTICA (n={args.seeds} seeds/config)  ROC AUC [IC95%]")
    print("=" * 76)
    hdr = f"{'config':<26}" + "".join(f"{('K='+str(k)):>22}" for k in args.K)
    print(hdr); print("-" * len(hdr))
    for c in configs:
        line = f"{c:<26}"
        for K in args.K:
            cc = agg[f"K={K}"]["configs"][c]
            line += f"{cc['mean']:.3f} [{cc['ci95'][0]:.3f},{cc['ci95'][1]:.3f}]".rjust(22)
        print(line)
    print("\nTESTES PAREADOS (Wilcoxon, Bonferroni n=%d, Cohen's d):" % n_tests)
    for K in args.K:
        for k2, t in tests[f"K={K}"].items():
            sig = "✅ p<0.01" if t["p_bonferroni"] < 0.01 else ("• p<0.05" if t["p_bonferroni"] < 0.05 else "✗ ns")
            print(f"  K={K} {k2}: Δ={t['mean_delta']:+.3f}  p_bonf={t['p_bonferroni']:.2e}  d={t['cohens_d']:+.2f}  {sig}")

    cC = tests.get("K=1000", {}).get("d_vs_c", {})
    if cC:
        gate = cC["p_bonferroni"] < 0.01
        print(f"\nGATE Sprint 4 [(d)−(c) sig. em C, p<0.01 Bonferroni]: "
              f"{'PASS ✅' if gate else 'FAIL ❌'} (p_bonf={cC['p_bonferroni']:.2e})")
    print(f"\n✅ {args.out_dir}/sprint4_aggregated.json + sprint4_runs.csv")


if __name__ == "__main__":
    main()
