#!/usr/bin/env python3
"""figB (opção A, honesta): dano colateral da mitigação — sintético × real lado a lado.

Mostra a CONDIÇÃO DE APLICABILIDADE, não um ganho universal:
  - Sintético (há discriminador de peso alto: JA4 de botnet distinto): a mitigação
    cirúrgica (escopo derivado) zera o colateral (0%) vs 22,5% do bloqueio global.
  - Real CIC-IoT2023 (LAN, sem TLS observável → sem discriminador): a cirúrgica
    recai sobre os mesmos legítimos e IGUALA o global (31,8% ambos, redução nula).
Números do §5.5 do artigo. Paleta cinza + navy. NÃO está no .tex (revisão).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

NAVY = "#1f3a5f"   # mitigação cirúrgica (nossa)
GRAY = "#b0b0b0"   # rate-limit global (baseline rombudo)

# (rótulo do cenário, colateral cirúrgico %, colateral global %, err_global(lo,hi), nota)
groups = [
    ("Sintético\n(discriminador presente:\nJA4 de botnet distinto)", 0.0, 22.5, (22.1, 23.0), "redução total"),
    ("Real — CIC-IoT2023\n(LAN, sem TLS observável:\nsem discriminador)", 31.8, 31.8, None, "redução nula"),
]
x = np.arange(len(groups))
w = 0.36

fig, ax = plt.subplots(figsize=(8, 4.6))
for i, (lab, surg, glob, err, nota) in enumerate(groups):
    yerr = [[glob - err[0]], [err[1] - glob]] if err else None
    ax.bar(i - w/2, surg, w, color=NAVY, zorder=3)
    ax.bar(i + w/2, glob, w, color=GRAY, zorder=3,
           yerr=yerr, error_kw=dict(ecolor="#333", lw=1, capsize=3))
    ax.text(i - w/2, surg + 0.6, f"{surg:.1f}%".replace(".", ","),
            ha="center", fontsize=9, fontweight="bold", color=NAVY)
    ax.text(i + w/2, glob + 0.6, f"{glob:.1f}%".replace(".", ","),
            ha="center", fontsize=9, color="#444")
    # seta/nota da redução entre as duas barras
    col = NAVY if nota == "redução total" else "#8a8a8a"
    ax.text(i, max(surg, glob) + 3.0, nota, ha="center", fontsize=9,
            style="italic", color=col)

ax.set_xticks(x)
ax.set_xticklabels([g[0] for g in groups], fontsize=9)
ax.set_ylabel("Dano colateral — % do tráfego legítimo atingido")
ax.set_ylim(0, 38)
ax.set_title("Mitigação cirúrgica zera o colateral SÓ quando há discriminador de peso alto;\n"
             "sem ele (LAN/não-TLS), iguala-se ao bloqueio global", color=NAVY, fontsize=10.5)
ax.legend(handles=[Patch(color=NAVY, label="mitigação cirúrgica (escopo derivado)"),
                   Patch(color=GRAY, label="rate-limit global no endpoint")],
          loc="upper left", fontsize=9, frameon=False)
ax.grid(axis="y", alpha=.3, zorder=0)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig("experiments/figures-candidatas/figB_colateral.png", dpi=160, bbox_inches="tight")
print("OK: figB (sintético 0%/22,5% × real 31,8%/31,8%)")
