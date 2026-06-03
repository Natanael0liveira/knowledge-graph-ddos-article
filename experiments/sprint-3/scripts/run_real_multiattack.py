#!/usr/bin/env python3
"""Passo A do HARDENING-PLAN — generalização multi-ataque em dados REAIS.

Para CADA tipo de ataque rotulado em CADA dataset real, mede a detecção
(ataque-vs-BENIGN) com a config (a) ML por-sessão e a (d) cross-session completa.
Se (d) ≫ (a) se mantém em ataques que NÃO fabricamos, a tese deixa de depender do
sintético (possivelmente circular). Esperado: vantagem grande em ataques
furtivos/distribuídos (Slowloris), pequena em ataques de assinatura óbvia
(Hulk/flood) — coerente com a tese, reportado sem maquiar.

Tarefa: para o ataque L, subconjunto {sessões L} ∪ {sessões BENIGN}, binário
L-vs-BENIGN. Isola a separabilidade de cada ataque em relação ao tráfego legítimo.

Reusa build_features (clusters de detecção label-agnósticos) de run_ablation.

Usage:
    python run_real_multiattack.py \
        --dataset cicids2017=/.../cicids2017.parquet \
        --dataset cic-iot-2023=/.../cic-iot-2023.parquet \
        --out results/real_multiattack.csv
"""
import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent))
from run_ablation import build_features, FEATURE_SETS, FLOW  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

NON_ATTACK = {"BENIGN", "UNLABELED"}
# Baseline por-sessão FORTE e justo: todas as features de fluxo disponíveis por sessão
# (não só taxa/duração). Evita inflar o gap cross-session com um baseline sub-dimensionado.
STRONG_FLOW = FLOW + ["fwd_bytes_sum", "bwd_bytes_sum", "fwd_pkts_sum",
                      "bwd_pkts_sum", "iat_mean_mean", "iat_std_mean"]
COORD = ["share_ja4", "share_net", "cluster_size"]
CONFIGS = {"a_ml_sem_ontologia": FLOW, "d_completo": FEATURE_SETS["d_completo"]}


def eval_config(df_sub, feats, y, benign_mask, rng=42):
    X = df_sub[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
    idx = np.arange(len(df_sub))
    Xtr, Xte, ytr, yte, _, ite = train_test_split(
        X, y, idx, test_size=0.3, random_state=rng, stratify=y)
    clf = RandomForestClassifier(n_estimators=300, random_state=rng,
                                 class_weight="balanced", n_jobs=-1).fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    bte = benign_mask[ite]
    return {
        "f1": float(f1_score(yte, pred, zero_division=0)),
        "precision": float(precision_score(yte, pred, zero_division=0)),
        "recall": float(recall_score(yte, pred, zero_division=0)),
        "auc": float(roc_auc_score(yte, proba)) if yte.sum() and (yte == 0).any() else float("nan"),
        "collateral_fpr_benign": float(pred[bte].mean()) if bte.sum() else float("nan"),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", nargs="+", required=True,
                    help="pares NOME=caminho.parquet")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--min-attack", type=int, default=50,
                    help="mínimo de sessões do ataque para avaliar")
    ap.add_argument("--strong-baseline", action="store_true",
                    help="(a) usa TODAS as features de fluxo por sessão (baseline justo); "
                         "(d) = essas + coordenação. Mede o ganho da coordenação sobre um "
                         "ML por-sessão forte, sem inflar o gap.")
    args = ap.parse_args()

    configs = ({"a_ml_sem_ontologia": STRONG_FLOW, "d_completo": STRONG_FLOW + COORD}
               if args.strong_baseline else CONFIGS)

    rows = []
    for pair in args.dataset:
        name, _, path = pair.partition("=")
        df = build_features(pd.read_parquet(path))
        lab = df["label_first"]
        attacks = sorted(set(lab.unique()) - NON_ATTACK)
        log.info("[%s] %d sessões | ataques: %s", name, len(df), attacks)
        for atk in attacks:
            sub = df[lab.isin([atk, "BENIGN"])].reset_index(drop=True)
            y = (sub["label_first"] == atk).astype(int).values
            if y.sum() < args.min_attack or (y == 0).sum() < args.min_attack:
                log.warning("  %s: amostra insuficiente (atk=%d), pulando", atk, int(y.sum()))
                continue
            benign_mask = (sub["label_first"] == "BENIGN").values
            for cfg, feats in configs.items():
                r = eval_config(sub, feats, y, benign_mask)
                r.update({"dataset": name, "attack": atk, "config": cfg,
                          "n_attack": int(y.sum()), "n_benign": int((y == 0).sum())})
                rows.append(r)
            log.info("  %s: a.AUC=%.3f d.AUC=%.3f a.F1=%.3f d.F1=%.3f",
                     atk,
                     *[next(x["auc"] for x in rows if x["attack"] == atk and x["config"] == c)
                       for c in configs],
                     *[next(x["f1"] for x in rows if x["attack"] == atk and x["config"] == c)
                       for c in configs])

    res = pd.DataFrame(rows)
    # ---- relatório: pivot por (dataset, ataque) com a e d lado a lado ----
    print("\n" + "=" * 84)
    print("PASSO A — GENERALIZAÇÃO MULTI-ATAQUE EM DADOS REAIS (ataque-vs-BENIGN)")
    print("=" * 84)
    print(f"{'dataset':<14}{'ataque':<14}{'n_atk':>7}{'AUC(a)':>9}{'AUC(d)':>9}"
          f"{'F1(a)':>8}{'F1(d)':>8}{'Δd-a(F1)':>10}")
    print("-" * 84)
    for (ds, atk), g in res.groupby(["dataset", "attack"]):
        a = g[g["config"] == "a_ml_sem_ontologia"].iloc[0]
        d = g[g["config"] == "d_completo"].iloc[0]
        print(f"{ds:<14}{atk:<14}{a['n_attack']:>7}{a['auc']:>9.3f}{d['auc']:>9.3f}"
              f"{a['f1']:>8.3f}{d['f1']:>8.3f}{d['f1']-a['f1']:>+10.3f}")
    print("-" * 84)
    print("Leitura: Δd-a grande = vantagem cross-session (ataque furtivo/distribuído);")
    print("Δd-a ~0 = ataque já separável por-sessão (assinatura de fluxo óbvia). Ambos válidos.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        res.to_csv(args.out, index=False)
        log.info("✅ %s", args.out)


if __name__ == "__main__":
    main()
