#!/usr/bin/env python3
"""English figures for the NOMS submission (papers/http-session-noms).

Generates the three DATA figures. fig1_ontology is a draw.io schematic and is NOT
produced here -- see figures/README.md and figures/src-drawio/.
  fig3_collateral.png -- single column: the modal scope, the unseen-fingerprint filter and
                         the enrichment scope on generated traffic, fresh and shared stacks.
  fig4_operating.png  -- single column: operating points on production traffic, false
                         alarms against blocked share (test days and the fresh day).
  fig5_latency.png    -- single column: the cost of both layers.
  (fig_regime, the earlier Fig. 4, is kept for reference and no longer drawn.)

Run from the repository root:
    experiments/.venv/bin/python papers/http-session-noms/figures/make_figures_en.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Patch

# Paleta monocromatica, casada com a Fig.1 (esquema draw.io):
#   INK   -- serie principal / "ours"      (preto do diagrama)
#   MUTED -- serie de comparacao / baseline
#   NOTE  -- anotacoes e linhas de referencia (mesmo cinza das notas da Fig.1)
# Sem cor: o contraste vem de tom e de marcador, entao sobrevive a impressao em
# escala de cinza e a leitores daltonicos.
NAVY = "#1a1a1a"      # INK   (nome mantido para nao tocar o corpo das funcoes)
NAVY2 = "#4d4d4d"
GRAY = "#ececec"
GRAYB = "#9a9a9a"
BAR_GRAY = "#bdbdbd"  # MUTED
CHANCE = "#595959"    # NOTE
TXT = "#222222"

OUT = os.path.dirname(os.path.abspath(__file__))


# --------------------------------------------------------------------------- fig 1
def fig_regime(root):
    real = pd.read_csv(os.path.join(root, "experiments/sprint-3/results/real_multiattack_strong.csv"))
    conv_a = real[real.config == "a_ml_sem_ontologia"]["auc"].mean()
    conv_d = real[real.config == "d_completo"]["auc"].mean()
    # canonical = production-realistic scenario (Zipf benign JA4, 25 botnet stacks)
    agg = json.load(open(os.path.join(
        root, "experiments/sprint-6-noms/results/canonical_realistic.json")))
    cfgK = agg["aggregate"]["K=1000"]
    stealth_a = cfgK["rf|a_ml_sem_ontologia"]["mean"]
    stealth_d = cfgK["rf|d_completo"]["mean"]

    groups = [
        ("Conventional real attacks\n(mean of 6 - CICIDS2017 + CIC-IoT2023)", conv_a, conv_d, False),
        ("Stealthy distributed campaign\n(realistic synthetic, n=30, K=1000)", stealth_a, stealth_d, True),
    ]
    y = np.arange(len(groups))[::-1].astype(float)
    h = 0.34

    fig, ax = plt.subplots(figsize=(7.6, 3.0))
    ax.barh(y + h / 2, [g[1] for g in groups], height=h, color=BAR_GRAY,
            label="strong per-session ML (8-9 features)", zorder=3)
    ax.barh(y - h / 2, [g[2] for g in groups], height=h, color=NAVY,
            label="cross-session representation (ours)", zorder=3)
    for yi, (_, vp, vc, hi) in zip(y, groups):
        ax.text(vp + .008, yi + h / 2, f"{vp:.2f}", va="center", fontsize=9,
                fontweight="bold" if hi else "normal", color=CHANCE if hi else "#333")
        ax.text(min(vc + .008, 1.0), yi - h / 2, f"{vc:.2f}", va="center", fontsize=9,
                fontweight="bold", color=NAVY)
    ax.axvline(0.5, color=CHANCE, ls="--", lw=1.2)
    # rotulo deslocado para a DIREITA da linha: centrado sobre ela, o texto
    # partia a tracejada ao meio e a figura lia como quebrada.
    ax.text(0.512, y.max() + 0.46, "chance", color=CHANCE, fontsize=8,
            ha="left", va="center")
    ax.axhspan(y.min() - 0.5, y.min() + 0.5, color=NAVY, alpha=0.06, zorder=0)
    ax.set_yticks(y)
    ax.set_yticklabels([g[0] for g in groups], fontsize=8.5)
    ax.set_xlim(0.4, 1.05)
    ax.set_xlabel("per-session ROC AUC (attack vs. benign)", fontsize=9)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.30), ncol=2, fontsize=8.5,
              frameon=False)
    ax.grid(axis="x", alpha=.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = os.path.join(OUT, "fig4_regime.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out} | conventional a={conv_a:.3f} d={conv_d:.3f} | "
          f"stealthy a={stealth_a:.3f} d={stealth_d:.3f}")


# --------------------------------------------------------------------------- fig 3 (v2)
def fig_collateral(root):
    """Modal, unseen-filter and enrichment scopes across the realism axis.

    unseen_synth.py reproduces the committed modal and enrichment runs exactly and
    adds the unseen filter and the shared-stacks mode on the same scenarios."""
    path = os.path.join(root, "experiments/sprint-6-noms/results/unseen_synth_summary.csv")
    d = pd.read_csv(path)

    def get(mode, stacks, adv, method):
        r = d[(d["mode"] == mode) & (d["alpha"] == 1.5) & (d["stacks"] == stacks)
              & (d["adv"] == adv) & (d["method"] == method)]
        return r.iloc[0] if len(r) else None

    points = [("original", 1, 0, "M=1"), ("original", 5, 0, "M=5"), ("original", 25, 0, "M=25"),
              ("original", 100, 0, "M=100"), ("shared_profile_tail", 25, 0, "M=25\nshared"),
              ("original", 25, 1, "M=25\nadversarial")]
    methods = [("modal", "modal (frequency)", "white", "#555", None),
               ("unseen", "unseen fingerprints", BAR_GRAY, "#777", None),
               ("enrichment", "enrichment (ours)", NAVY, NAVY, None)]
    labels = [p[3] for p in points]
    cov = {m: [get(mo, s, a, m)["recall"] * 100 for mo, s, a, _ in points] for m, *_ in methods}
    col = {m: [get(mo, s, a, m)["fpr"] * 100 for mo, s, a, _ in points] for m, *_ in methods}

    x = np.arange(len(labels))
    w = 0.26
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 4.1), sharex=True,
                                   gridspec_kw={"hspace": 0.16})
    for k, (m, lab, face, edge, _) in enumerate(methods):
        off = (k - 1) * w
        ax1.bar(x + off, cov[m], w, color=face, edgecolor=edge, lw=0.8, zorder=3, label=lab)
        ax2.bar(x + off, col[m], w, color=face, edgecolor=edge, lw=0.8, zorder=3)
        for xi, v in zip(x, cov[m]):
            ax1.text(xi + off, v + 2.5, f"{v:.0f}", ha="center", fontsize=6.8,
                     color=NAVY if m == "enrichment" else "#555",
                     fontweight="bold" if m == "enrichment" else None)
        for xi, v in zip(x, col[m]):
            ax2.text(xi + off, v + 2.5, f"{v:.0f}" if v >= 1 else f"{v:.1f}", ha="center",
                     fontsize=6.8, color=NAVY if m == "enrichment" else "#555",
                     fontweight="bold" if m == "enrichment" else None)
    ax1.set_ylabel("attack blocked (%)", fontsize=9)
    ax1.set_ylim(0, 112)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.24), ncol=3, fontsize=8.2,
               frameon=False)
    ax1.grid(axis="y", alpha=.25, zorder=0)
    ax1.spines[["top", "right"]].set_visible(False)
    ax2.set_ylabel("legitimate hit (%)", fontsize=9)
    ax2.set_ylim(0, 50)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=8.2)
    ax2.set_xlabel("botnet TLS stacks, realistic benign traffic ($\\alpha=1.5$)", fontsize=9)
    ax2.grid(axis="y", alpha=.25, zorder=0)
    ax2.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT, "fig3_collateral.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


def fig_operating(root):
    """False alarms against blocked share on production traffic, 100 attackers."""
    T = json.load(open(os.path.join(root, "experiments/sprint-6-noms/results/production_tables.json")))
    scopes = [  # (label, run, key, marker)
        ("binomial, $\\Omega$ gate (rule)", "base", "enrichment|omega", "o"),
        ("binomial $\\cup$ unseen, origin gate", "base", "union|origins", "s"),
        ("  + known fleets", "fleets", "union|origins", "D"),
        ("beta-binomial $\\cup$ unseen, origin gate", "od", "union|origins", "h"),
        ("$z$-score, calibrated", "base", "zcal|origins", "^"),
        ("unseen JA4", "base", "unseen|origins", "P"),
        ("scope alone, known fleets", "fleets", "union|none", "*"),
        ("scope alone, beta-binomial", "od", "union|none", "X"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
    for ax, cell, title in ((axes[0], "new:A100", "new stacks"), (axes[1], "shared:A100", "shared stacks")):
        for lab, run, key, mk in scopes:
            for block, filled in (("test_days", True), ("fresh_day", False)):
                r = T[block][run]["all"][key]
                fa = max(r["clean_rate"] * 100, 0.01)
                y = r[cell]["blocked"] * 100
                face = (NAVY if filled else "white") if mk not in ("x",) else NAVY
                ax.scatter(fa, y, marker=mk, s=40 if mk != "*" else 90, facecolors=face,
                           edgecolors=NAVY, linewidths=0.9, zorder=3,
                           label=lab if (filled and ax is axes[0]) else None)
        ax.set_xscale("log")
        ax.set_xlim(0.008, 15)
        ax.set_ylim(-3, 100)
        ax.set_title(title + ", 100 attackers", fontsize=10)
        ax.set_xlabel("clean windows with a false alarm (%)", fontsize=9.5)
        ax.tick_params(labelsize=9)
        ax.grid(alpha=.25, zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("botnet blocked (%)", fontsize=9.5)
    fig.legend(loc="lower center", bbox_to_anchor=(0.5, -0.27), ncol=3, fontsize=8.6, frameon=False)
    fig.text(0.99, 0.005, "filled: test days; open: fresh day", ha="right", fontsize=8.4, color="#555")
    fig.tight_layout()
    out = os.path.join(OUT, "fig4_operating.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


def fig_latency(root):
    import json
    d = json.load(open(os.path.join(
        root, "experiments/sprint-6-noms/results/latency_summary.json")))["by_window_size"]
    sizes = sorted((int(k) for k in d), key=int)
    adm = [d[str(n)]["admission_p50_us"] / 1e6 for n in sizes]
    adm_c = [d[str(n)]["admission_class_p50_us"] / 1e6 for n in sizes]
    sym_c = [d[str(n)]["class_total_s"] for n in sizes]
    sym_n = [n for n in sizes if "symbolic_total_s" in d[str(n)]]
    sym = [d[str(n)]["symbolic_total_s"] for n in sym_n]

    fig, ax = plt.subplots(figsize=(7.0, 2.7))
    # comparison series (grey): pair edges enumerated or materialized
    ax.loglog(sym_n, sym, "s-", color=BAR_GRAY, lw=2, ms=6, markeredgecolor="#777",
              label="symbolic layer, pair edges materialized")
    ax.loglog(sizes, adm, "o-", color=BAR_GRAY, lw=2, ms=6, markeredgecolor="#777",
              label="admission, peers enumerated")
    # proposed series (ink): equality-based sub-relations kept as classes
    ax.loglog(sizes, sym_c, "s-", color=NAVY, lw=2, ms=6,
              label="symbolic layer, class aggregation")
    ax.loglog(sizes, adm_c, "o-", color=NAVY, lw=2, ms=6,
              label="admission, class counters")

    # reference slopes anchored on the first point of each series
    def ref(xs, y0, k, color, label, dy):
        x = [xs[0], xs[-1]]
        y = [y0, y0 * (x[1] / x[0]) ** k]
        ax.loglog(x, y, ":", color=color, lw=1, alpha=.7)
        ax.text(x[1], y[1] * dy, label, color=color, fontsize=8, ha="right",
                style="italic")
    ref(sym_n, sym[0], 2, "#777", "slope 2", 1.6)
    ref(sizes, sym_c[0], 1, NAVY, "slope 1", 1.6)
    ref(sizes, adm[0], 1, "#777", "slope 1", 1.6)
    ax.text(sizes[-1], adm_c[-1] * 2.6, "constant", color=NAVY, fontsize=8,
            ha="right", style="italic")
    ax.set_ylim(bottom=min(adm_c) / 4)     # room under the flat series

    ax.set_xlabel("active sessions in the window, $|S_W|$", fontsize=9)
    ax.set_ylabel("latency (s)", fontsize=9)
    ax.grid(True, which="both", alpha=.25)
    # legenda abaixo dos eixos: dentro do grafico ela competia com os dados.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2,
              fontsize=8.2, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = os.path.join(OUT, "fig5_latency.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(OUT, "..", "..", ".."))
    # fig1_ontology and fig2_pipeline are draw.io schematics, not generated here.
    # Sources live in src-drawio/; see README.md for the export procedure.
    fig_collateral(root)
    fig_operating(root)
    fig_latency(root)
