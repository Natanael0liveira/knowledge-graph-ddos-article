#!/usr/bin/env python3
"""Sprint 4 — figures from the ablation runs (sprint4_runs.csv).

money figure: per-session ROC AUC vs K, one line per config, with 95% bootstrap
CI bands. Shows per-session/baselines collapsing while the full cross-session
framework stays near 1.0 on stealthy distributed campaigns.

Usage:
    python make_figures.py --runs results/sprint4_runs.csv --out results/figures
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

LABELS = {
    "a_ml_sem_ontologia": "(a) ML por-sessão",
    "b_ontologia_sem_related": "(b) ontologia s/ relatedBy",
    "c_so_network_proximity": "(c) só network proximity",
    "d_completo": "(d) arcabouço completo",
    "base:fernandes2015": "baseline Fernandes 2015",
    "base:bharathi2012": "baseline Bharathi 2012",
    "base:kemp2023": "baseline Kemp 2023",
}
STYLE = {
    "d_completo": dict(color="#1b7837", lw=2.6, marker="o", zorder=5),
    "c_so_network_proximity": dict(color="#762a83", lw=1.8, marker="s"),
    "b_ontologia_sem_related": dict(color="#2166ac", lw=1.8, marker="^"),
    "a_ml_sem_ontologia": dict(color="#b2182b", lw=2.2, marker="D"),
}


def ci(vals, rng):
    m = [rng.choice(vals, len(vals), replace=True).mean() for _ in range(2000)]
    return vals.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(args.runs)
    Ks = sorted(df["K"].unique())
    rng = np.random.default_rng(42)

    fig, ax = plt.subplots(figsize=(8, 5))
    configs = [c for c in LABELS if c in df.columns]
    for c in configs:
        ms, los, his = [], [], []
        for K in Ks:
            v = df[df["K"] == K][c].dropna().values
            m, lo, hi = ci(v, rng)
            ms.append(m); los.append(lo); his.append(hi)
        st = dict(STYLE.get(c, dict(color="grey", lw=1.2, marker=".")))  # copy
        ls = "--" if c.startswith("base") else "-"
        color = st.get("color", "grey")
        ax.plot(Ks, ms, label=LABELS[c], linestyle=ls, **st)
        ax.fill_between(Ks, los, his, alpha=0.12, color=color)

    ax.axhline(0.5, color="grey", ls=":", lw=1, alpha=0.7)
    ax.text(Ks[0], 0.51, "acaso", color="grey", fontsize=8)
    ax.set_xscale("log")
    ax.set_xticks(Ks); ax.set_xticklabels([str(k) for k in Ks])
    ax.set_xlabel("K (grau de distribuição da campanha)")
    ax.set_ylabel("ROC AUC (detecção por sessão)")
    ax.set_title("Detecção de campanha furtiva: por-sessão colapsa, cross-session detecta")
    ax.set_ylim(0.4, 1.02)
    ax.legend(loc="center right", fontsize=8, framealpha=0.9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = args.out / "money_figure_auc_vs_k.png"
    fig.savefig(out, dpi=150)
    print(f"✅ {out}")


if __name__ == "__main__":
    main()
