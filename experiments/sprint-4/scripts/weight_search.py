#!/usr/bin/env python3
"""Sprint 4 — grid search of the Ω(S) sub-relation weights w_i + sensitivity.

Ω(S) = w_tls·pairs_ja4 + w_endpoint·pairs_endpoint + w_net·pairs_net.
We grid-search (w_tls, w_endpoint, w_net) ∈ {0.3,0.5,0.7,0.9,1.0}³ on a VALIDATION
set of synthetic scenarios, scoring each weight vector by the ROC AUC of cluster-Ω
predicting whether a detection cluster is attack-dominant. Reports the best vector
and a ±20% perturbation sensitivity around it.

compute_omega already returns the pairs_* columns, so weights recombine without
recomputation.

Usage:
    python weight_search.py --scenarios <dir-with-*.parquet>  [--max-files N]
"""
import argparse
import itertools
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sprint-1" / "scripts"))
from compute_coordination import assign_detection_clusters, compute_omega  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

GRID = [0.3, 0.5, 0.7, 0.9, 1.0]


def cluster_table(parquets):
    frames = []
    for p in parquets:
        df = pd.read_parquet(p)
        df["start_ts"] = pd.to_datetime(df["start_ts"])
        df["end_ts"] = pd.to_datetime(df["end_ts"])
        cl = compute_omega(assign_detection_clusters(df, 300))
        cl = cl[cl["size"] >= 2]
        frames.append(cl[["pairs_ja4", "pairs_endpoint", "pairs_net", "attack_frac"]])
    t = pd.concat(frames, ignore_index=True)
    t["y"] = (t["attack_frac"] >= 0.5).astype(int)
    return t


def auc_for_weights(t, w):
    omega = w[0]*t["pairs_ja4"] + w[1]*t["pairs_endpoint"] + w[2]*t["pairs_net"]
    if t["y"].nunique() < 2:
        return float("nan")
    return roc_auc_score(t["y"], omega)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", required=True, type=Path)
    ap.add_argument("--max-files", type=int, default=20)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    # filtra lixo AppleDouble (._*) que o exfat cria e o glob casa
    files = sorted(p for p in args.scenarios.glob("*.parquet")
                   if not p.name.startswith("._"))[: args.max_files]
    if not files:
        log.error("Sem parquets em %s", args.scenarios); sys.exit(1)
    log.info("Validação: %d cenários", len(files))
    t = cluster_table(files)
    log.info("Clusters (|S|≥2): %d (attack-dom: %d)", len(t), int(t["y"].sum()))

    results = []
    for w in itertools.product(GRID, repeat=3):
        results.append((w, auc_for_weights(t, w)))
    results.sort(key=lambda x: -(x[1] if not np.isnan(x[1]) else -1))
    best_w, best_auc = results[0]

    # sensibilidade ±20% em torno do melhor
    sens = []
    for i in range(3):
        for f in (0.8, 1.2):
            w = list(best_w); w[i] = round(w[i]*f, 3)
            sens.append({"perturb": f"w{i}×{f}", "w": w, "auc": auc_for_weights(t, tuple(w))})
    max_drop = max((best_auc - s["auc"]) for s in sens)

    # referência: os pesos do paper (1.0, 0.6, 0.3)
    paper_auc = auc_for_weights(t, (1.0, 0.6, 0.3))

    print("\n" + "=" * 64)
    print("SPRINT 4 — GRID SEARCH DE PESOS Ω(S)  (AUC cluster attack-dom)")
    print("=" * 64)
    print(f"  domínio: {GRID}³ = {len(results)} combinações")
    print(f"  MELHOR: w_tls={best_w[0]} w_endpoint={best_w[1]} w_net={best_w[2]}  AUC={best_auc:.4f}")
    print(f"  paper (1.0, 0.6, 0.3): AUC={paper_auc:.4f}")
    print("\n  Top 5:")
    for w, a in results[:5]:
        print(f"    w={w}  AUC={a:.4f}")
    print(f"\n  Sensibilidade ±20% em torno do melhor: queda máx de AUC = {max_drop:.4f}")
    for s in sens:
        print(f"    {s['perturb']:<10} w={s['w']}  AUC={s['auc']:.4f}  (Δ={best_auc-s['auc']:+.4f})")
    print(f"\n  GATE [robusto a ±20%]: {'✅' if max_drop < 0.05 else '⚠️'} (queda {max_drop:.4f}, limiar 0.05)")

    if args.out:
        args.out.write_text(json.dumps({
            "grid": GRID, "best_weights": list(best_w), "best_auc": best_auc,
            "paper_weights_auc": paper_auc, "max_drop_pm20pct": max_drop,
            "top5": [{"w": list(w), "auc": a} for w, a in results[:5]],
            "sensitivity": sens,
        }, indent=2))
        log.info("✅ %s", args.out)


if __name__ == "__main__":
    main()
