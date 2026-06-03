#!/usr/bin/env python3
"""figC (honesta, enxuta): ML por-sessão FORTE (8-9 features) × entre sessões.

Dois regimes, baseline forte nos dois lados:
  - Ataques reais convencionais (média de 6, CIC): per-session já basta — coordenação
    não acrescenta (ambos ~1.0). Floods de assinatura óbvia.
  - Furtivo-distribuído (sintético, n=30 seeds, K=1000): cada sessão calibrada para
    parecer benigna -> per-session no acaso (0.50); só a coordenação entre sessões
    detecta (0.99). É o regime que datasets públicos não contêm.
Paleta cinza + navy estratégico. NÃO está no .tex (revisão).
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAVY = "#1f3a5f"
GRAY = "#b0b0b0"
CHANCE = "#6e6e6e"

# --- convencionais: média dos 6 ataques reais (baseline forte) ---
real = pd.read_csv("experiments/sprint-3/results/real_multiattack_strong.csv")
conv_a = real[real.config == "a_ml_sem_ontologia"]["auc"].mean()
conv_d = real[real.config == "d_completo"]["auc"].mean()
# --- furtivo: Sprint 4 forte, n=30, K=1000 ---
agg = json.load(open("experiments/sprint-4/results/strong/sprint4_aggregated.json"))
cfgK = agg["aggregate"]["K=1000"]["configs"]
stealth_a = cfgK["a_ml_sem_ontologia"]["mean"]
stealth_d = cfgK["d_completo"]["mean"]

groups = [
    ("Ataques reais convencionais\n(média de 6 — CICIDS2017 + CIC-IoT2023)", conv_a, conv_d, False),
    ("Campanha furtiva-distribuída\n(sintética, n=30 seeds, K=1000)", stealth_a, stealth_d, True),
]
labels = [g[0] for g in groups]
ps = [g[1] for g in groups]
cs = [g[2] for g in groups]
y = np.arange(len(groups))[::-1].astype(float)
h = 0.34

fig, ax = plt.subplots(figsize=(9, 3.4))
ax.barh(y + h/2, ps, height=h, color=GRAY, label="ML por sessão (forte, 8–9 features)", zorder=3)
ax.barh(y - h/2, cs, height=h, color=NAVY, label="entre sessões (nosso)", zorder=3)
for yi, (lab, vp, vc, hi) in zip(y, groups):
    ax.text(vp + .008, yi + h/2, f"{vp:.2f}".replace(".", ","), va="center",
            fontsize=9, fontweight="bold" if hi else "normal", color=CHANCE if hi else "#333")
    ax.text(min(vc + .008, 1.0), yi - h/2, f"{vc:.2f}".replace(".", ","), va="center",
            fontsize=9, fontweight="bold", color=NAVY)
ax.axvline(0.5, color=CHANCE, ls="--", lw=1.2)
ax.text(0.5, y.max() + 0.42, "acaso", color=CHANCE, fontsize=8, ha="center")
ax.axhspan(y.min() - 0.5, y.min() + 0.5, color=NAVY, alpha=0.06, zorder=0)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlim(0.4, 1.05)
ax.set_xlabel("ROC AUC por sessão (ataque-vs-benigno)")
ax.set_title("ML por-sessão forte já resolve ataques convencionais;\n"
             "só no regime furtivo-distribuído a coordenação entre sessões é necessária",
             color=NAVY, fontsize=10.5)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2, fontsize=9, frameon=False)
ax.grid(axis="x", alpha=.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("experiments/figures-candidatas/figC_multiataque_real.png", dpi=160,
            bbox_inches="tight")
print(f"OK: figC enxuta | conv a={conv_a:.3f} d={conv_d:.3f} | furtivo a={stealth_a:.3f} d={stealth_d:.3f}")
