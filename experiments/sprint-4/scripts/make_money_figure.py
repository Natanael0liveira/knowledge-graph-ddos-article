#!/usr/bin/env python3
"""Money figure (v2) a partir do sprint4_aggregated.json.

Em vez de uma linha com 2 pontos (pobre), um gráfico de barras horizontais
agrupado: 7 métodos × 2 graus de distribuição (K=50, K=1000), com barras de erro
(IC 95%) e a linha do acaso (0.5). Conta a história inteira da ablação: por-sessão
e baselines no acaso; proximidade de rede fraca; arcabouço completo no topo.

Uso: python make_money_figure.py --in results/sprint4_aggregated.json --out fig.png
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

# ordem de baixo (pior) p/ cima (melhor) — ascensão visual
ORDER = ["base:bharathi2012", "base:fernandes2015", "base:kemp2023",
         "a_ml_sem_ontologia", "c_so_network_proximity",
         "b_ontologia_sem_related", "d_completo"]
LABELS = {
    "base:bharathi2012": "Bharathi 2012 (baseline)",
    "base:fernandes2015": "Fernandes 2015 (baseline)",
    "base:kemp2023": "Kemp 2023 (baseline)",
    "a_ml_sem_ontologia": "(a) ML por sessão (forte, 8–9 feat)",
    "c_so_network_proximity": "(c) só proximidade de rede",
    "b_ontologia_sem_related": "(b) ontologia sem relatedBy",
    "d_completo": "(d) arcabouço completo",
}
C50, C1000 = "#b0b0b0", "#1f3a5f"  # cinza claro (K=50) / navy (K=1000)
CHANCE = "#6e6e6e"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    agg = json.loads(args.inp.read_text())["aggregate"]
    Ks = list(agg.keys())  # ['K=50','K=1000']

    fig, ax = plt.subplots(figsize=(9, 5.5))
    h = 0.38
    for i, cfg in enumerate(ORDER):
        for j, K in enumerate(Ks):
            c = agg[K]["configs"][cfg]
            m, lo, hi = c["mean"], c["ci95"][0], c["ci95"][1]
            y = i + (h/2 if j == 0 else -h/2)
            ax.barh(y, m, height=h, color=(C50 if j == 0 else C1000),
                    xerr=[[m-lo], [hi-m]], error_kw=dict(ecolor="#333", lw=1, capsize=2),
                    zorder=3)
            ax.text(min(hi+0.012, 1.005), y, f"{m:.2f}".replace(".", ","),
                    va="center", ha="left", fontsize=8, color="#222")
    ax.axvline(0.5, color=CHANCE, ls="--", lw=1.4, zorder=2)
    ax.text(0.5, len(ORDER)-0.35, " acaso (0,5)", color=CHANCE, fontsize=9, va="top")
    ax.axvline(1.0, color="#999", ls=":", lw=1, zorder=1)

    ax.set_yticks(range(len(ORDER)))
    ax.set_yticklabels([LABELS[c] for c in ORDER])
    # destacar (d)
    ax.get_yticklabels()[ORDER.index("d_completo")].set_fontweight("bold")
    ax.set_xlim(0.4, 1.04)
    ax.set_xlabel("ROC AUC por sessão (detecção de campanha furtiva)")
    ax.set_title("Ablação (baseline por-sessão FORTE, n=30): per-session e baselines\n"
                 "ficam no acaso; só o raciocínio cross-session (d) detecta", fontsize=11.5,
                 color="#1f3a5f")
    ax.legend(handles=[Patch(color=C50, label="K = 50 (moderado)"),
                       Patch(color=C1000, label="K = 1000 (distribuído)")],
              loc="lower right", fontsize=9, framealpha=0.95)
    ax.grid(axis="x", alpha=0.3, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"✅ {args.out}")


if __name__ == "__main__":
    main()
