#!/usr/bin/env python3
"""English figures for the NOMS submission (papers/http-session-noms).

Generates the three DATA figures. fig1_ontology is a draw.io schematic and is NOT
produced here -- see figures/README.md and figures/src-drawio/.
  fig4_regime.png     -- single column: strong per-session ML already solves conventional
                         real attacks; only the stealthy-distributed regime needs
                         cross-session reasoning.
  fig3_collateral.png -- single column: derived-scope mitigation zeroes collateral damage
                         when a high-weight discriminator exists; without one it ties the
                         global rate limit.

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
def fig_ontology():
    fig, ax = plt.subplots(figsize=(10.6, 4.10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    def box(x, y, w, h, label, fc=GRAY, ec=GRAYB, tc=TXT, fs=8.6, bold=False, lw=1.3):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.04,rounding_size=0.10",
                                    linewidth=lw, edgecolor=ec, facecolor=fc, zorder=3))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fs,
                color=tc, fontweight="bold" if bold else "normal", zorder=4)

    def arrow(p1, p2, color=GRAYB, lw=1.4, rad=0.0, style="-|>", ms=13):
        ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=ms,
                                     linewidth=lw, color=color,
                                     connectionstyle=f"arc3,rad={rad}", zorder=2))

    def plabel(x, y, t, color="#555", fs=7.4):
        ax.text(x, y, t, ha="center", va="center", fontsize=fs, color=color, style="italic",
                zorder=5, bbox=dict(boxstyle="round,pad=0.10", fc="white", ec="none", alpha=.92))

    # --- satellites of S_i ---------------------------------------------------
    sat = [
        (4.85, "Identity\n(Cookie / Token / JA4)", "hasIdentity"),
        (3.95, "IPAddress / Host", "originatesFrom"),
        (3.05, "Endpoint\n(API / Login / Checkout)", "targets"),
        (2.15, "Behavior\n(BotBehavior, ...)", "exhibitsBehavior"),
    ]
    for yc, lab, prop in sat:
        box(0.10, yc - 0.32, 2.05, 0.66, lab, fs=7.4)
        arrow((2.17, yc), (2.85, 3.30), rad=0.0)
        plabel(2.42, yc + 0.22, prop, fs=6.8)

    # --- the two sessions ----------------------------------------------------
    box(2.85, 2.85, 2.35, 0.90, "ApplicationSession\n$S_i$", fc=NAVY, ec=NAVY, tc="white",
        fs=9.4, bold=True)
    box(7.75, 2.85, 2.35, 0.90, "ApplicationSession\n$S_j$", fc=NAVY2, ec=NAVY, tc="white",
        fs=9.4, bold=True)
    ax.text(8.93, 2.66, "(same primary relations as $S_i$)", ha="center", fontsize=6.8,
            style="italic", color="#777")

    ax.add_patch(FancyArrowPatch((4.85, 3.75), (8.15, 3.75), arrowstyle="<|-|>",
                                 mutation_scale=15, linewidth=2.6, color=NAVY,
                                 connectionstyle="arc3,rad=-0.42", zorder=2))
    ax.text(6.50, 5.00, "relatedTo  (cross-session)", ha="center", fontsize=9.6,
            fontweight="bold", color=NAVY, zorder=6,
            bbox=dict(boxstyle="round,pad=0.20", fc="white", ec=NAVY, lw=1.2))

    # --- weighted family strip ----------------------------------------------
    ax.add_patch(FancyBboxPatch((2.85, 0.55), 7.30, 1.85,
                                boxstyle="round,pad=0.05,rounding_size=0.08",
                                linewidth=1.4, edgecolor=NAVY, facecolor="#f4f7fb", zorder=3))
    ax.text(3.05, 2.24, "relatedTo family: six typed, weighted sub-properties",
            ha="left", va="top", fontsize=8.4, fontweight="bold", color=NAVY)
    ax.text(3.05, 1.94, "weight = attacker's cost to break the signal",
            ha="left", va="top", fontsize=7.6, style="italic", color="#555")
    rows = [
        ("relatedByTLSFingerprint", "1.0", NAVY),
        ("relatedByReusedIdentity", "1.0", NAVY),
        ("relatedByTemporalPattern", "0.9", NAVY),
        ("relatedByEndpointConvergence", "0.6", "#6b6b6b"),
        ("relatedByPayloadSignature", "0.6", "#6b6b6b"),
        ("relatedByNetworkProximity", "0.3", "#a5a5a5"),
    ]
    for i, (name, w, col) in enumerate(rows):
        cx = 3.05 + (i // 3) * 3.65
        cy = 1.55 - (i % 3) * 0.33
        ax.text(cx, cy, "*", fontsize=10, color=col, va="center")
        ax.text(cx + 0.22, cy, name.replace("relatedBy", ""), fontsize=8.0,
                family="monospace", color=TXT, va="center")
        ax.text(cx + 3.35, cy, f"w={w}", fontsize=8.0, family="monospace", color=col,
                va="center", fontweight="bold", ha="right")
    arrow((6.50, 3.55), (6.50, 2.45), color=NAVY, lw=1.2, rad=0.10)

    # --- rule -> verdict -> mitigation --------------------------------------
    box(10.60, 3.10, 3.30, 1.05,
        "DetectionRule CoordinatedHTTPFlood\n"
        r"fires iff $\Omega(S)=\sum_i w_i\,|E_i(S)|\geq\tau$",
        fc=GRAY, ec=NAVY, fs=7.6, lw=1.4)
    box(10.60, 1.80, 3.30, 0.95,
        "Verdict = symbolic derivation\nevidence chain: JSON-LD / STIX 2.1",
        fc="white", ec=NAVY, fs=7.6, lw=1.4)
    box(10.60, 0.55, 3.30, 0.90,
        "CourseOfAction: scoped mitigation\nderived from the coordinated subset",
        fc=NAVY, ec=NAVY, tc="white", fs=7.6, lw=1.4)
    arrow((10.15, 3.62), (10.60, 3.62), color=NAVY, lw=1.6)
    arrow((12.25, 3.10), (12.25, 2.75), color=NAVY, lw=1.6)
    arrow((12.25, 1.80), (12.25, 1.45), color=NAVY, lw=1.6)
    plabel(13.20, 1.62, "mitigatedBy", color=NAVY, fs=6.8)

    # --- attack hierarchy ----------------------------------------------------
    ax.add_patch(FancyBboxPatch((0.10, 0.30), 2.66, 1.25,
                                boxstyle="round,pad=0.05,rounding_size=0.08",
                                linewidth=1.1, edgecolor=GRAYB, facecolor="white", zorder=3))
    ax.text(0.26, 1.44, "Attack hierarchy", ha="left", fontsize=8.0, fontweight="bold",
            color="#444")
    hier = ("ApplicationLayerAttack\n"
            " > SlowHTTPDoSFamily\n"
            "   > ConnectionExhaustionAttack\n"
            "   > CoordinatedHTTPFlood\n"
            " > LoginFlood > CredentialStuffing")
    ax.text(0.26, 1.22, hier, ha="left", va="top", fontsize=5.9, color=TXT, family="monospace")

    fig.tight_layout()
    out = os.path.join(OUT, "fig1_ontology.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


# --------------------------------------------------------------------------- fig 2
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
    """Modal vs enrichment scope derivation across the realism axis."""
    import csv
    path = os.path.join(root, "experiments/sprint-6-noms/results/realistic_consolidated.csv")
    rows = list(csv.DictReader(open(path)))

    def get(alpha, stacks, adv):
        for r in rows:
            if (float(r["alpha"]) == alpha and int(r["stacks"]) == stacks
                    and int(r["adv"]) == adv):
                return r
        return None

    points = [(1, 0, "M=1"), (5, 0, "M=5"), (25, 0, "M=25"), (100, 0, "M=100"),
              (25, 1, "M=25\nadversarial")]
    labels, m_cov, m_col, e_cov, e_col = [], [], [], [], []
    for stacks, adv, lab in points:
        r = get(1.5, stacks, adv)
        if not r:
            continue
        labels.append(lab)
        m_cov.append(float(r["modal_cov"]) * 100)
        m_col.append(float(r["modal_coll"]) * 100)
        e_cov.append(float(r["enr_cov"]) * 100)
        e_col.append(float(r["enr_coll"]) * 100)

    x = np.arange(len(labels))
    w = 0.36
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True,
                                   gridspec_kw={"hspace": 0.16})

    ax1.bar(x - w/2, m_cov, w, color=BAR_GRAY, zorder=3, label="modal (frequency)")
    ax1.bar(x + w/2, e_cov, w, color=NAVY, zorder=3, label="enrichment (ours)")
    for xi, v in zip(x, m_cov):
        ax1.text(xi - w/2, v + 2.5, f"{v:.0f}", ha="center", fontsize=8, color="#555")
    for xi, v in zip(x, e_cov):
        ax1.text(xi + w/2, v + 2.5, f"{v:.0f}", ha="center", fontsize=8,
                 color=NAVY, fontweight="bold")
    ax1.set_ylabel("attack blocked (%)", fontsize=9)
    ax1.set_ylim(0, 112)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.24), ncol=2, fontsize=8.5,
               frameon=False)
    ax1.grid(axis="y", alpha=.25, zorder=0)
    ax1.spines[["top", "right"]].set_visible(False)

    ax2.bar(x - w/2, m_col, w, color=BAR_GRAY, zorder=3)
    ax2.bar(x + w/2, e_col, w, color=NAVY, zorder=3)
    for xi, v in zip(x, m_col):
        ax2.text(xi - w/2, v + 2.5, f"{v:.0f}", ha="center", fontsize=8, color="#555")
    for xi, v in zip(x, e_col):
        ax2.text(xi + w/2, v + 2.5, f"{v:.2f}", ha="center", fontsize=8,
                 color=NAVY, fontweight="bold")
    ax2.set_ylabel("legitimate hit (%)", fontsize=9)
    ax2.set_ylim(0, 78)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=8.5)
    ax2.set_xlabel("botnet TLS stacks, realistic benign traffic ($\\alpha=1.5$)", fontsize=9)
    ax2.grid(axis="y", alpha=.25, zorder=0)
    ax2.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    out = os.path.join(OUT, "fig3_collateral.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


# --------------------------------------------------------------------------- fig 4
def fig_latency(root):
    import json
    d = json.load(open(os.path.join(
        root, "experiments/sprint-6-noms/results/latency_summary.json")))["by_window_size"]
    sizes = sorted((int(k) for k in d), key=int)
    adm = [d[str(n)]["admission_p50_us"] / 1e6 for n in sizes]
    sym_n = [n for n in sizes if "symbolic_total_s" in d[str(n)]]
    sym = [d[str(n)]["symbolic_total_s"] for n in sym_n]

    fig, ax = plt.subplots(figsize=(7.0, 3.1))
    ax.loglog(sizes, adm, "o-", color=NAVY, lw=2, ms=6,
              label="admission, per request (indexed)")
    ax.loglog(sym_n, sym, "s-", color=BAR_GRAY, lw=2, ms=6,
              markeredgecolor="#777",
              label="symbolic materialization, per window (rdflib)")

    # reference slopes anchored on the first point of each series
    xs = [sizes[0], sizes[-1]]
    ax.loglog(xs, [adm[0], adm[0] * (xs[1] / xs[0])], ":", color=NAVY, lw=1, alpha=.7)
    ax.text(sizes[-1], adm[-1] * 1.45, "slope 1", color=NAVY, fontsize=8,
            ha="right", style="italic")
    xs2 = [sym_n[0], sym_n[-1]]
    ax.loglog(xs2, [sym[0], sym[0] * (xs2[1] / xs2[0]) ** 2], ":", color="#777",
              lw=1, alpha=.7)
    ax.text(sym_n[-1], sym[-1] * 1.6, "slope 2", color="#666", fontsize=8,
            ha="right", style="italic")

    ax.set_xlabel("active sessions in the window, $|S_W|$", fontsize=9)
    ax.set_ylabel("latency (s)", fontsize=9)
    ax.grid(True, which="both", alpha=.25)
    # legenda abaixo dos eixos: dentro do grafico ela ocupava a faixa vazia
    # entre as duas series e competia com os dados.
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1,
              fontsize=8.2, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    out = os.path.join(OUT, "fig5_latency.png")
    fig.savefig(out, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(OUT, "..", "..", ".."))
    # fig1_ontology is NOT generated here anymore: it is a draw.io schematic,
    # source in figures/src-drawio/fig1_ontology.drawio (see figures/README.md).
    # fig_ontology() below is kept only as the historical matplotlib version and
    # must not run, or it would overwrite the draw.io export.
    fig_regime(root)
    fig_collateral(root)
    fig_latency(root)
