#!/usr/bin/env python3
"""Candidata figC: generalização multi-ataque em dados reais (ML por sessão × nosso).
Paleta tons de cinza + navy estratégico. NÃO referenciada no .tex (revisão)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAVY = "#1f3a5f"
GRAY = "#b0b0b0"   # ML por sessão (baseline)
CHANCE = "#6e6e6e"

df = pd.read_csv("experiments/sprint-3/results/real_multiattack.csv")
piv = {}
for _, r in df.iterrows():
    piv.setdefault((r["dataset"], r["attack"]), {})[r["config"]] = r["auc"]
labels = [f"{a} ({d.replace('cic-iot-2023','CIC-IoT2023').replace('cicids2017','CICIDS2017')})"
          for (d, a) in piv]
a = [v["a_ml_sem_ontologia"] for v in piv.values()]
dd = [v["d_completo"] for v in piv.values()]
y = np.arange(len(labels)); h = 0.38

fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(y + h/2, a, height=h, color=GRAY, label="ML por sessão (baseline)", zorder=3)
ax.barh(y - h/2, dd, height=h, color=NAVY, label="arcabouço cross-session (nosso)", zorder=3)
for i, (va, vd) in enumerate(zip(a, dd)):
    ax.text(va + .008, i + h/2, f"{va:.2f}".replace(".", ","), va="center", fontsize=8, color="#333")
    ax.text(min(vd + .008, 1.0), i - h/2, f"{vd:.2f}".replace(".", ","), va="center",
            fontsize=8, fontweight="bold", color=NAVY)
ax.axvline(0.5, color=CHANCE, ls="--", lw=1.3)
ax.text(0.5, len(labels) - .4, " acaso", color=CHANCE, fontsize=8, va="top")
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8)
ax.set_xlim(0.4, 1.05)
ax.set_xlabel("ROC AUC por sessão (ataque-vs-benigno, dados reais)")
ax.set_title("Generalização em dados reais: ML por sessão fica no acaso,\n"
             "o arcabouço cross-session detecta — 6 ataques, 2 datasets", color=NAVY)
ax.legend(loc="lower right", fontsize=9)
ax.grid(axis="x", alpha=.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("experiments/figures-candidatas/figC_multiataque_real.png", dpi=160)
print("OK: figC")
