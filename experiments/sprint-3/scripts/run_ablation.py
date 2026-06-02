#!/usr/bin/env python3
"""Sprint 3 — ablation (a/b/c/d) + academic baselines on the same input.

The four ablation configs differ ONLY in the feature set fed to a common
classifier (RandomForest), isolating the contribution of the relatedBy_* family:

  (a) ML sem ontologia          : flow features only (per-session)
  (b) ontologia sem relatedBy_* : (a) + per-session ontology attrs (identity, target)
  (c) só relatedByNetworkProximity : (a) + share_net
  (d) arcabouço completo        : (a) + share_ja4 + share_net + cluster_size

The three baselines (Fernandes/Bharathi/Kemp) run on the (a) feature set and
should match (a) — sanity. Thesis prediction: (d) ≫ (a)/(b) on distributed
scenarios (B/C); all similar on the concentrated scenario (A).

Cross-session features come from Sprint-1's compute_coordination (detection
clusters are label-agnostic, assigned WITHIN each scenario file).

Usage:
    python run_ablation.py --scenario A=/path/A.parquet B=/path/B.parquet ...
"""
import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sprint-1" / "scripts"))
from compute_coordination import (assign_detection_clusters, session_features,  # noqa: E402
                                  _is_attack)
sys.path.insert(0, str(Path(__file__).parent))
from baselines import BASELINES  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

FLOW = ["n_requests", "duration_s", "req_per_s"]
FEATURE_SETS = {
    "a_ml_sem_ontologia":      FLOW,
    "b_ontologia_sem_related": FLOW + ["has_identity", "dst_port_first"],
    "c_so_network_proximity":  FLOW + ["share_net"],
    "d_completo":              FLOW + ["share_ja4", "share_net", "cluster_size"],
}


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["start_ts"] = pd.to_datetime(df["start_ts"])
    df["end_ts"] = pd.to_datetime(df["end_ts"])
    df = assign_detection_clusters(df, window_s=300)
    df = session_features(df)  # adds cluster_size, share_ja4, share_net, req_per_s
    df["has_identity"] = df["ja4"].notna().astype(int)
    return df


def auc_for(feats, df, y, rng=42):
    X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3,
                                          random_state=rng, stratify=y)
    clf = RandomForestClassifier(n_estimators=200, random_state=rng,
                                 class_weight="balanced", n_jobs=-1).fit(Xtr, ytr)
    return roc_auc_score(yte, clf.predict_proba(Xte)[:, 1]), (Xtr, Xte, ytr, yte)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenario", nargs="+", required=True,
                    help="pares NOME=caminho.parquet (ex: A=a.parquet C=c.parquet)")
    args = ap.parse_args()

    scenarios = {}
    for pair in args.scenario:
        name, _, path = pair.partition("=")
        scenarios[name] = Path(path)

    configs = list(FEATURE_SETS) + [f"base:{b}" for b in BASELINES]
    table = {}
    for name, path in scenarios.items():
        df = build_features(pd.read_parquet(path))
        y = _is_attack(df["label_first"]).astype(int).values
        n_atk = int(y.sum())
        if n_atk < 2 or n_atk == len(y):
            log.warning("Cenário %s: %d ataques — pulando (precisa ≥2 e <total)",
                        name, n_atk)
            table[name] = {"_n_attack": n_atk}
            continue
        log.info("Cenário %s: %d sessões, %d ataque", name, len(df), n_atk)
        row = {"_n_attack": n_atk}
        # ablation configs
        split = None
        for cfg, feats in FEATURE_SETS.items():
            auc, split = auc_for(feats, df, y)
            row[cfg] = auc
        # baselines on (a) feature set, same split as (a) for fairness
        Xa = df[FLOW].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
        Xtr, Xte, ytr, yte = train_test_split(Xa, y, test_size=0.3,
                                              random_state=42, stratify=y)
        for bname, (fn, _) in BASELINES.items():
            try:
                scores = fn(Xtr, Xte, ytr)
                row[f"base:{bname}"] = roc_auc_score(yte, scores)
            except Exception as e:
                log.warning("baseline %s falhou: %s", bname, e)
                row[f"base:{bname}"] = float("nan")
        table[name] = row

    # ---- relatório ----
    print("\n" + "=" * 78)
    print("SPRINT 3 — ABLAÇÃO + BASELINES (ROC AUC, detecção de ataque por sessão)")
    print("=" * 78)
    hdr = f"{'config':<28}" + "".join(f"{n:>12}" for n in scenarios)
    print(hdr); print("-" * len(hdr))
    for cfg in configs:
        line = f"{cfg:<28}"
        for name in scenarios:
            v = table[name].get(cfg)
            line += f"{v:>12.4f}" if isinstance(v, float) and not np.isnan(v) else f"{'—':>12}"
        print(line)
    print("-" * len(hdr))
    print(f"{'(nº ataques)':<28}" + "".join(f"{table[n].get('_n_attack',0):>12}" for n in scenarios))

    # sanity check do plano: em A, (a)–(d) similares; ganho de (d) cresce com K
    print("\nSANITY (plano Sprint 3): em A as configs devem ser similares; o ganho")
    print("de (d) sobre (a) deve crescer de A→B→C.")
    for name in scenarios:
        r = table[name]
        if "d_completo" in r and "a_ml_sem_ontologia" in r:
            print(f"  {name}: Δ(d−a) = {r['d_completo']-r['a_ml_sem_ontologia']:+.4f}")


if __name__ == "__main__":
    main()
