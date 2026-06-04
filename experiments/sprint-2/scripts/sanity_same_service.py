#!/usr/bin/env python3
"""Sanity check (NÃO-calibrado, sem HD): cenário REALISTA de mesmo serviço.

Corrige o artefato de porta do config (b): aqui benigno E ataque atingem o MESMO
endpoint (10.0.0.1:443) — como um serviço web real sob ataque, onde usuários legítimos
continuam acessando. Cada sessão atacante é mimética (features por-sessão sorteadas da
MESMA distribuição do benigno). JA4 benigno diverso (pool grande); atacantes compartilham
um JA4 (90%). Ambos dispersos em rede.

Expectativa: como a porta/endpoint não separam mais (constantes) e o per-session é
mimético, (a) e (b) caem ao acaso (~0,50); só (d), via share_ja4 entre sessões, detecta.
Isto mostra que o 0,88 do (b) na money figure era artefato sintético de portas.

NOTA: distribuições por-sessão são plausíveis, NÃO as calibradas do CIC (que ficam no HD).
O resultado do mecanismo independe disso (ataque e benigno saem da mesma distribuição).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1].parent / "sprint-3" / "scripts"))
from run_ablation import build_features, auc_for, FLOW  # noqa: E402

STRONG_FLOW = FLOW + ["fwd_bytes_sum", "bwd_bytes_sum", "fwd_pkts_sum",
                      "bwd_pkts_sum", "iat_mean_mean", "iat_std_mean"]
SETS = {
    "a_ml (forte)":            STRONG_FLOW,
    "b_ontologia_sem_related": STRONG_FLOW + ["has_identity", "dst_port_first"],
    "c_so_network":            STRONG_FLOW + ["share_net"],
    "d_completo":              STRONG_FLOW + ["share_ja4", "share_net", "cluster_size"],
}

rng = np.random.default_rng(42)
N_BEN, N_ATK = 1000, 1000
T0 = pd.Timestamp("2026-06-04T12:00:00")


def per_session_flow(n):
    """Distribuição plausível por-sessão — IDÊNTICA para benigno e ataque (mimético)."""
    n_req = np.maximum(1, rng.geometric(0.5, n))
    dur = rng.exponential(8.0, n) * (n_req > 1)
    fwd_b = rng.lognormal(5.2, 1.0, n)          # ~180 B mediana
    bwd_b = rng.lognormal(5.8, 1.2, n)          # ~330 B mediana
    fwd_p = np.maximum(1, np.round(fwd_b / 700)).astype(int)
    bwd_p = np.maximum(1, np.round(bwd_b / 700)).astype(int)
    iat_m = dur / np.maximum(1, n_req - 1)
    iat_s = iat_m * rng.uniform(0.1, 0.5, n)
    return n_req, dur, fwd_b, bwd_b, fwd_p, bwd_p, iat_m, iat_s


def build(n, attack):
    nq, dur, fb, bb, fp, bp, im, is_ = per_session_flow(n)
    # MESMO serviço para todos: 10.0.0.1:443 (usuários legítimos + atacantes)
    start = T0 + pd.to_timedelta(rng.uniform(0, 250, n), unit="s")
    if attack:
        # JA4 compartilhado em 90%; rede dispersa em 10.0.0.0/8
        ja4 = np.where(rng.random(n) < 0.9, "shared_botnet_ja4",
                       [f"atk_uniq_{i}" for i in range(n)])
        src = [f"10.{rng.integers(0,256)}.{rng.integers(0,256)}.{rng.integers(1,255)}" for _ in range(n)]
    else:
        # JA4 diverso (pool 2000); rede dispersa em 100.64.0.0/10
        ja4 = [f"benign_{rng.integers(0,2000)}" for _ in range(n)]
        src = [f"100.{rng.integers(64,128)}.{rng.integers(0,256)}.{rng.integers(1,255)}" for _ in range(n)]
    return pd.DataFrame(dict(
        session_id=[("a" if attack else "b") + str(i) for i in range(n)],
        src_ip_first=src, dst_ip_first="10.0.0.1", dst_port_first=443,
        start_ts=start, end_ts=start + pd.to_timedelta(dur, unit="s"),
        n_requests=nq, duration_s=dur, ja4=ja4,
        fwd_bytes_sum=fb, bwd_bytes_sum=bb, fwd_pkts_sum=fp, bwd_pkts_sum=bp,
        iat_mean_mean=im, iat_std_mean=is_,
        is_attack=attack, label_first=("ATTACK" if attack else "BENIGN")))


df = pd.concat([build(N_BEN, False), build(N_ATK, True)], ignore_index=True)
feat = build_features(df)
y = (feat["label_first"] == "ATTACK").astype(int).values

print("=" * 64)
print("SANITY — cenário REALISTA mesmo serviço (benigno+ataque em :443)")
print("=" * 64)
print(f"dst_port distinto: {feat['dst_port_first'].nunique()} (=1 → não separa) | "
      f"has_identity distinto: {feat['has_identity'].nunique()} (=1 → não separa)")
print(f"{'config':<26}{'ROC AUC':>10}")
print("-" * 36)
for name, fs in SETS.items():
    auc, _ = auc_for(fs, feat, y)
    print(f"{name:<26}{auc:>10.3f}")
print("-" * 36)
print("share_ja4: ataque mediana=%.0f  benigno mediana=%.0f"
      % (feat[y == 1]["share_ja4"].median(), feat[y == 0]["share_ja4"].median()))
