#!/usr/bin/env python3
"""Sprint 5 — comparação com KLAGE em DDoS Slowloris (CIC-IoT2023).

KLAGE (Belcastro et al., FGCS 2026) é node-level (porta/IP/fluxo), Graph-BERT +
LIME, e reporta F1 = 84,1% em DDoS Slowloris (RT-IoT2022 + CIC-IoT2023). Aqui
rodamos NOSSO arcabouço (session-level, features cross-session relatedBy_*) no
mesmo dataset/ataque e reportamos F1 lado a lado, MAIS a métrica distintiva de
dano colateral (FPR em tráfego BENIGN).

Detecção de Slowloris one-vs-rest (análogo ao F1 por classe do KLAGE). Comparamos
a config (a) ML por-sessão vs (d) arcabouço completo: no CIC-IoT2023 o Slowloris é
per-sessão indistinguível do benigno (n_req≈1, dur≈0), distribuído em 143 /24s —
exatamente onde a estrutura cross-session importa.

Mapeamento de granularidade (honesto): KLAGE classifica NÓS DE REDE; nós
classificamos SESSÕES. Os F1 não são diretamente comutáveis — a comparação é de
ordem de grandeza + a vantagem qualitativa (símbolo auditável + dano colateral).

Usage:
    python run_klage_comparison.py --sessions cic-iot-2023.parquet --out report.json
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sprint-3" / "scripts"))
from run_ablation import build_features, FEATURE_SETS, FLOW  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

KLAGE_F1 = 0.841
ATTACK = "Slowloris"
# baseline por-sessão FORTE (8 features de fluxo) — o honesto, não os 3 de FLOW.
STRONG_FLOW = FLOW + ["fwd_bytes_sum", "bwd_bytes_sum", "fwd_pkts_sum",
                      "bwd_pkts_sum", "iat_mean_mean", "iat_std_mean"]


def evaluate(df, feats, y, benign_mask, rng=42):
    X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
    idx = np.arange(len(df))
    Xtr, Xte, ytr, yte, itr, ite = train_test_split(
        X, y, idx, test_size=0.3, random_state=rng, stratify=y)
    clf = RandomForestClassifier(n_estimators=300, random_state=rng,
                                 class_weight="balanced", n_jobs=-1).fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    # dano colateral: FPR sobre sessões BENIGN no conjunto de teste
    benign_te = benign_mask[ite]
    fpr_benign = float(pred[benign_te].mean()) if benign_te.sum() else float("nan")
    return {
        "f1": float(f1_score(yte, pred)),
        "precision": float(precision_score(yte, pred, zero_division=0)),
        "recall": float(recall_score(yte, pred, zero_division=0)),
        "auc": float(roc_auc_score(yte, proba)),
        "collateral_fpr_benign": fpr_benign,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    df = build_features(pd.read_parquet(args.sessions))
    lab = df["label_first"]
    y = (lab == ATTACK).astype(int).values
    benign_mask = (lab == "BENIGN").values
    log.info("%d sessões | Slowloris=%d | BENIGN=%d | outros=%d",
             len(df), int(y.sum()), int(benign_mask.sum()),
             len(df) - int(y.sum()) - int(benign_mask.sum()))

    configs = {"a_ml_sem_ontologia": FLOW,
               "a_ml_forte": STRONG_FLOW,
               "d_completo": FEATURE_SETS["d_completo"]}
    res = {c: evaluate(df, feats, y, benign_mask) for c, feats in configs.items()}

    print("\n" + "=" * 72)
    print("SPRINT 5 — NOSSO ARCABOUÇO × KLAGE  (DDoS Slowloris, CIC-IoT2023)")
    print("=" * 72)
    print(f"{'método':<34}{'F1':>8}{'prec':>8}{'rec':>8}{'AUC':>8}{'dano colat.':>13}")
    print("-" * 72)
    print(f"{'KLAGE (node-level, Graph-BERT)':<34}{KLAGE_F1:>8.3f}{'—':>8}{'—':>8}{'—':>8}{'não reportado':>13}")
    names = {"a_ml_sem_ontologia": "nosso (a) ML por-sessão (3 feat)",
             "a_ml_forte": "nosso (a') ML por-sessão FORTE (8 feat)",
             "d_completo": "nosso (d) cross-session completo"}
    for c, r in res.items():
        print(f"{names[c]:<40}{r['f1']:>8.3f}{r['precision']:>8.3f}{r['recall']:>8.3f}"
              f"{r['auc']:>8.3f}{r['collateral_fpr_benign']:>13.4f}")
    print("-" * 72)
    d = res["d_completo"]; a = res["a_ml_sem_ontologia"]; af = res["a_ml_forte"]
    print(f"\nΔF1 (d − a magro) = {d['f1']-a['f1']:+.3f}  |  ΔF1 (d − a FORTE) = {d['f1']-af['f1']:+.3f}")
    print(f"nosso (d) vs KLAGE: {d['f1']-KLAGE_F1:+.3f}  |  a FORTE vs KLAGE: {af['f1']-KLAGE_F1:+.3f}")
    print("\n⚠️ HONESTO: em DADOS REAIS o ML por-sessão FORTE NÃO colapsa (Slowloris do")
    print("   CIC-IoT2023 tem assinatura de fluxo por-sessão). O 'colapso por-sessão' só")
    print("   vale com baseline magro OU no regime furtivo sintético. Aqui (d) ainda supera")
    print("   KLAGE, mas a vantagem sobre o per-session forte é pequena — reportar sem maquiar.")
    print("\n⚠️ MAPEAMENTO DE GRANULARIDADE (honesto): KLAGE classifica NÓS DE REDE;")
    print("   nós classificamos SESSÕES. F1 não é diretamente comutável — comparação")
    print("   é de ordem de grandeza. Nossa vantagem qualitativa: símbolo auditável")
    print("   (regra SPARQL) + dano colateral mensurável; KLAGE não reporta colateral.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(
            {"dataset": "CIC-IoT2023", "attack": ATTACK, "klage_f1": KLAGE_F1,
             "ours": res}, indent=2))
        log.info("✅ %s", args.out)


if __name__ == "__main__":
    main()
