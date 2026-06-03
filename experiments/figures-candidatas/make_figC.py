#!/usr/bin/env python3
"""figC (honesta): ML por-sessão FORTE (8 features) × cross-session.

Contraste decisivo: em ataques reais convencionais um ML por-sessão completo
(bytes/pacotes/IAT) já basta — a coordenação não acrescenta. SÓ no regime
furtivo-distribuído (cada sessão calibrada para parecer benigna) o per-session
colapsa e a coordenação cross-session é necessária. Baseline FORTE nos dois lados,
para não inflar o gap. Paleta cinza + navy estratégico. NÃO está no .tex (revisão).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAVY = "#1f3a5f"
GRAY = "#b0b0b0"
CHANCE = "#6e6e6e"

real = pd.read_csv("experiments/sprint-3/results/real_multiattack_strong.csv")
stealth = pd.read_csv("experiments/sprint-4/results/stealth_flow_strong.csv")


def auc(df, ds, atk, cfg):
    return df[(df.dataset == ds) & (df.attack == atk) & (df.config == cfg)]["auc"].iloc[0]


rows = []  # (rótulo, per-session forte, cross-session, destaque?)
for _, r in real.iterrows():
    if r.config != "a_ml_sem_ontologia":
        continue
    ds = r.dataset.replace("cic-iot-2023", "CIC-IoT2023").replace("cicids2017", "CICIDS2017")
    rows.append((f"{r.attack} ({ds})",
                 r.auc, auc(real, r.dataset, r.attack, "d_completo"), False))
rows.sort(key=lambda x: x[0])
rows.append(("Campanha furtiva-distribuída\n(sintética, mimética)",
             auc(stealth, "stealth", "ATTACK", "a_ml_sem_ontologia"),
             auc(stealth, "stealth", "ATTACK", "d_completo"), True))

labels = [r[0] for r in rows]
ps = [r[1] for r in rows]
cs = [r[2] for r in rows]
y = np.arange(len(labels))[::-1]
h = 0.38

fig, ax = plt.subplots(figsize=(9.2, 5.2))
ax.barh(y + h/2, ps, height=h, color=GRAY, label="ML por sessão (forte, 8 features)", zorder=3)
ax.barh(y - h/2, cs, height=h, color=NAVY, label="cross-session (nosso)", zorder=3)
for yi, (vp, vc, hi) in zip(y, [(r[1], r[2], r[3]) for r in rows]):
    ax.text(vp + .006, yi + h/2, f"{vp:.2f}".replace(".", ","), va="center",
            fontsize=8, fontweight="bold" if hi else "normal",
            color=CHANCE if hi else "#333")
    ax.text(min(vc + .006, 1.0), yi - h/2, f"{vc:.2f}".replace(".", ","), va="center",
            fontsize=8, fontweight="bold", color=NAVY)
ax.axvline(0.5, color=CHANCE, ls="--", lw=1.2)
ax.text(0.5, y.max() + 0.45, "acaso", color=CHANCE, fontsize=8, ha="center")
# faixa de destaque na linha furtiva
ax.axhspan(y.min() - 0.55, y.min() + 0.55, color=NAVY, alpha=0.06, zorder=0)
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=8.5)
ax.set_xlim(0.4, 1.04)
ax.set_xlabel("ROC AUC por sessão (ataque-vs-benigno)")
ax.set_title("Um ML por-sessão FORTE já resolve ataques convencionais;\n"
             "só no regime furtivo-distribuído a coordenação cross-session é necessária",
             color=NAVY, fontsize=11)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=9, frameon=False)
ax.grid(axis="x", alpha=.3)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("experiments/figures-candidatas/figC_multiataque_real.png", dpi=160,
            bbox_inches="tight")
print("OK: figC honesta (baseline forte + linha furtiva)")
