#!/usr/bin/env python3
"""#3 — Calibração de pesos w_i com objetivo a NÍVEL DE SESSÃO (mais difícil).

A calibração anterior (AUC de cluster attack-dominante) saturava. Aqui o objetivo é
mais duro e mais natural: um score de coordenação POR SESSÃO,
    score(s) = w_tls·z(share_ja4) + w_ep·z(cluster_size) + w_net·z(share_net),
com cada feature padronizada (z-score) para que os pesos reflitam importância relativa
(não escala). Buscamos no grid {0.3..1.0}³ os pesos que maximizam o ROC AUC de separar
ataque-vs-benigno POR SESSÃO, sobre cenários de sinais parciais (scenario_hard).

Honesto: se o grid voltar a saturar ou indicar pesos degenerados, reportamos — a
conclusão (pesos teóricos) já está no paper; este passo testa se um objetivo mais
difícil muda isso.

Uso: python weight_calibration_session.py --scenarios <dir-com-*.parquet>
"""
import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sprint-1" / "scripts"))
from compute_coordination import assign_detection_clusters, session_features, _is_attack  # noqa: E402

GRID = [0.3, 0.5, 0.7, 0.9, 1.0]
FEATS = ["share_ja4", "cluster_size", "share_net"]  # TLS, endpoint(proxy), rede


def build(parquet):
    df = pd.read_parquet(parquet)
    df["start_ts"] = pd.to_datetime(df["start_ts"]); df["end_ts"] = pd.to_datetime(df["end_ts"])
    d = session_features(assign_detection_clusters(df, 300))
    y = _is_attack(d["label_first"]).astype(int).values
    X = d[FEATS].astype(float).values
    # z-score por feature (sobre este cenário)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    return Z, y


def auc_w(Z, y, w):
    if len(np.unique(y)) < 2:
        return np.nan
    return roc_auc_score(y, Z @ np.array(w))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", required=True, type=Path)
    ap.add_argument("--max-files", type=int, default=12)
    args = ap.parse_args()
    files = sorted(p for p in args.scenarios.glob("*.parquet") if not p.name.startswith("._"))[: args.max_files]
    data = [build(f) for f in files]
    print(f"cenários: {len(files)} | sessões totais: {sum(len(y) for _,y in data)}")

    def mean_auc(w):
        v = [auc_w(Z, y, w) for Z, y in data]
        v = [x for x in v if not np.isnan(x)]
        return float(np.mean(v)) if v else np.nan

    results = sorted(((w, mean_auc(w)) for w in itertools.product(GRID, repeat=3)),
                     key=lambda x: -(x[1] if not np.isnan(x[1]) else -1))
    best_w, best = results[0]
    paper = mean_auc((1.0, 0.6, 0.3))
    # sensibilidade ±20% no melhor
    sens = []
    for i in range(3):
        for f in (0.8, 1.2):
            w = list(best_w); w[i] = round(w[i]*f, 3); sens.append((tuple(w), mean_auc(tuple(w))))
    max_drop = max(best - a for _, a in sens)
    # importância individual: AUC de cada feature sozinha
    solo = {FEATS[i]: mean_auc(tuple(1.0 if j == i else 0.0 for j in range(3))) for i in range(3)}

    print("\n" + "=" * 64)
    print("#3 — CALIBRAÇÃO DE PESOS (objetivo: AUC por SESSÃO, features z-score)")
    print("=" * 64)
    print(f"  MELHOR: w(tls,ep,net)={best_w}  AUC={best:.4f}")
    print(f"  paper (1.0, 0.6, 0.3):           AUC={paper:.4f}")
    print(f"  AUC de cada sinal sozinho: " + ", ".join(f"{k}={v:.3f}" for k, v in solo.items()))
    print("  Top 5:")
    for w, a in results[:5]:
        print(f"    w={w}  AUC={a:.4f}")
    print(f"\n  Sensibilidade ±20% no melhor: queda máx = {max_drop:.4f}")
    spread = best - results[-1][1]
    print(f"  Spread (melhor − pior do grid): {spread:.4f}  "
          f"→ {'DISCRIMINATIVO' if spread > 0.02 else 'SATURADO (pesos não importam)'}")


if __name__ == "__main__":
    main()
