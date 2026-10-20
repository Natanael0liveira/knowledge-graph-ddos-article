#!/usr/bin/env python3
"""English figures for the NOMS submission (papers/http-session-noms).

Generates the DATA figures. Fig. 1 (fig1_scoping) is a draw.io schematic and is NOT
produced here -- see figures/README.md and figures/src-drawio/.
  fig6_stops.png      -- Fig. 2 (Section V-C), one column at print size: what the binomial
                         configuration stops per endpoint, by botnet size, against what the
                         scope alone would block, with the gap the gate lets through shaded.
  fig4_operating.png  -- Fig. 3 (Section V-D), one column at print size: operating points
                         on production traffic, false alarms against blocked share (test
                         days and the cross-fitted calibration), with the 1% budget.
  fig5_latency.png    -- Fig. 4 (Appendix D), single column: the cost of both layers.

Run from the repository root:
    experiments/.venv/bin/python papers/http-session-noms/figures/make_figures_en.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Monochrome palette, matched to Fig. 1 (the draw.io schematic):
#   INK   -- the main series                 (the schematic's black)
#   MUTED -- comparison series
#   NOTE  -- annotations and reference lines (the gray of Fig. 1's notes)
# No hue: contrast comes from tone and marker, so the figures survive grayscale
# printing and color-blind readers. NAVY2, GRAY, GRAYB and TXT are unused.
NAVY = "#1a1a1a"      # INK   (historical name, kept so the function bodies need not change)
NAVY2 = "#4d4d4d"
GRAY = "#ececec"
GRAYB = "#9a9a9a"
BAR_GRAY = "#bdbdbd"  # MUTED
CHANCE = "#595959"    # NOTE
TXT = "#222222"

OUT = os.path.dirname(os.path.abspath(__file__))


def fig_operating(root):
    """False alarms against blocked share on production traffic, 100 attackers.

    Drawn at print size (one column, 3.45 in). Black markers: test days, calibrated in
    sample; grey, joined by an arrow to its in-sample point: the cross-fitted calibration.
    The dashed line is the 1% false-alarm budget. The held-out day is left to Tables IV and
    VI: its gate barely opened, so its zero rates would sit in the best corner of the plot.
    """
    T = json.load(open(os.path.join(root, "experiments/sprint-6-noms/results/production_tables.json")))
    scopes = [  # (label, run, key, marker, size)
        ("base rule ($\\Omega$ gate)", "base", "enrichment|omega", "o", 16),
        ("binomial configuration", "fleets", "union|origins", "D", 13),
        ("$z$-score, calibrated", "base", "zcal|origins", "^", 18),
        ("beta-binomial$^{*}$", "od", "union|origins", "h", 18),
        ("unseen filter (origin gate)", "base", "unseen|origins", "P", 18),
        ("scope alone, binomial$^{*}$", "fleets", "union|none", "*", 34),
        ("scope alone, beta-binomial$^{*}$", "od", "union|none", "X", 18),
        ("unseen filter alone$^{*}$", "fleets", "unseen|none", "s", 14),
    ]
    xfit = [("fleets", "xfit_fleets", "union|origins", "D", 13), ("od", "xfit_od", "union|origins", "h", 18),
            ("base", "xfit", "zcal|origins", "^", 18), ("od", "xfit_od", "union|none", "X", 18),
            ("fleets", "xfit_fleets", "union|none", "*", 34), ("base", "xfit", "enrichment|omega", "o", 16)]
    fig, axes = plt.subplots(1, 2, figsize=(3.45, 2.5), sharey=True)
    for ax, cell, title in ((axes[0], "new:A100", "new stacks"), (axes[1], "shared:A100", "shared stacks")):
        ax.axvline(1, color=CHANCE, lw=0.7, ls=(0, (3, 2)), zorder=1)
        for lab, run, key, mk, s in scopes:
            r = T["test_days"][run]["all"][key]
            # the base rule, the protocol's reference, is the one open marker, so it reads apart
            # from the beta-binomial's filled hexagon at print size
            ax.scatter(max(r["clean_rate"] * 100, 0.01), r[cell]["blocked"] * 100, marker=mk, s=s,
                       facecolors="white" if key == "enrichment|omega" else NAVY, edgecolors=NAVY,
                       linewidths=0.8 if key == "enrichment|omega" else 0.6, zorder=3,
                       label=lab if ax is axes[0] else None)
        for run0, run, key, mk, s in xfit:
            r0, r = T["test_days"][run0]["all"][key], T["test_days"][run]["all"][key]
            p0 = (max(r0["clean_rate"] * 100, 0.01), r0[cell]["blocked"] * 100)
            p1 = (max(r["clean_rate"] * 100, 0.01), r[cell]["blocked"] * 100)
            ax.annotate("", xy=p1, xytext=p0, zorder=2,
                        arrowprops=dict(arrowstyle="-|>", color=CHANCE, lw=0.5, mutation_scale=5,
                                        shrinkA=2.5, shrinkB=2.5))
            ax.scatter(*p1, marker=mk, s=s, facecolors=BAR_GRAY, edgecolors=NAVY, linewidths=0.6, zorder=3)
        ax.set_xscale("log")
        ax.set_xlim(0.007, 15)
        ax.set_xticks([0.01, 0.1, 1, 10])
        ax.set_xticklabels(["0.01", "0.1", "1", "10"])
        ax.set_ylim(-4, 100)
        ax.set_title(title, fontsize=7, pad=2)
        ax.tick_params(labelsize=6.5, length=2, pad=1.5)
        ax.grid(alpha=.25, lw=0.5, zorder=0)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("% of 100 attackers blocked", fontsize=7, labelpad=1)
    axes[0].text(0.8, 99, "1% budget", fontsize=6.5, ha="right", va="top", color=CHANCE)
    h, l = axes[0].get_legend_handles_labels()
    # one x label for both panels, just under the tick labels, then a clear gap before the legend
    fig.tight_layout(pad=0.2, w_pad=0.5, rect=(0, 0.29, 1, 1))
    y0 = axes[0].get_position().y0
    fig.text(0.5, y0 - 0.105, "false alarms (% of clean windows)", ha="center", va="center", fontsize=6.8)
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, y0 - 0.125), ncol=2, fontsize=6.3, borderpad=0.2,
               frameon=False, handletextpad=0.3, columnspacing=0.8, labelspacing=0.3)
    out = os.path.join(OUT, "fig4_operating.png")
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


def fig_stops(root):
    """What the binomial configuration stops per endpoint, by botnet size (test days).

    Drawn at print size (one column, 3.45 in) from the `sweep` block of
    production_tables.json: run `fleets`, scope union, distinct-origin gate, 25 new stacks.
    Two lines per endpoint, what the scope alone would block in every window and what the
    configuration stops, and the shaded gap between them, what the gate lets through.
    The gate's own rate and the shared stacks are left to the text and Table V, so that
    every line is a share of the botnet. The absolute sizes (25-1,000) and the relative ones
    (a tenth, half and the whole median window) share the x axis in attackers per window.
    """
    T = json.load(open(os.path.join(root, "experiments/sprint-6-noms/results/production_tables.json")))
    S = T["sweep"]["fleets"]
    n0 = {"E1": 2983, "E2": 62, "E3": 41, "E4": 20}          # Table V, median origins per window
    names = {"E1": "E1, RUM beacons (busiest)", "E2": "E2, web console", "E3": "E3, API", "E4": "E4, SSO"}
    fig, axes = plt.subplots(2, 2, figsize=(3.45, 2.6), sharex=True, sharey=True)
    for ax, e in zip(axes.flat, ("E1", "E2", "E3", "E4")):
        pts = [(A, f"M25:A{A}") for A in (25, 50, 100, 250, 1000)]
        pts += [(x * n0[e], f"M25:x{x:g}") for x in (0.1, 0.5, 1)]
        pts.sort()
        xs = [p[0] for p in pts]
        alone = [S[e][f"new:{k}"]["blocked_alone"] * 100 for _, k in pts]
        conf = [S[e][f"new:{k}"]["blocked"] * 100 for _, k in pts]
        # what the scope names but the gate lets through: the paper's point on the busiest endpoint
        ax.fill_between(xs, conf, alone, where=[a > c for a, c in zip(alone, conf)], interpolate=True,
                        color="#d6d6d6", lw=0, zorder=1)
        ax.plot(xs, alone, "--", color=CHANCE, lw=1.2, label="the scope alone would block")
        ax.plot(xs, conf, "o-", color=NAVY, lw=1.2, ms=2.6, label="the configuration stops")
        ax.plot([0.1 * n0[e]], [-6], marker="^", color=NAVY, mfc="white", mew=0.6, ms=3.5, clip_on=False, zorder=4)
        ax.set_xscale("log")
        ax.set_xlim(1.5, 4000)
        ax.set_ylim(-6, 100)
        ax.set_title(names[e], fontsize=7, pad=2)
        ax.grid(alpha=.25, lw=0.5, zorder=0)
        ax.tick_params(labelsize=6.5, length=2, pad=1.5)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].text(420, 58, "lost to\nthe gate", fontsize=6, ha="center", va="center", color=NAVY, zorder=5)
    for ax in axes[1]:
        ax.set_xlabel("attackers per window", fontsize=7, labelpad=1)
    for ax in axes[:, 0]:
        ax.set_ylabel("% of the botnet", fontsize=7, labelpad=1)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.005), ncol=2, fontsize=6.5,
               frameon=False, handlelength=2.2, columnspacing=1.2)
    fig.tight_layout(pad=0.2, h_pad=0.5, w_pad=0.4, rect=(0, 0.07, 1, 1))
    out = os.path.join(OUT, "fig6_stops.png")
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    e1 = S["E1"]
    print(f"OK: {out} | E1 new A100 alone {e1['new:M25:A100']['blocked_alone']:.3f} conf {e1['new:M25:A100']['blocked']:.3f}"
          f" | x0.1 alone {e1['new:M25:x0.1']['blocked_alone']:.3f} conf {e1['new:M25:x0.1']['blocked']:.3f}")


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

    # drawn at the width it prints (one column), with fonts of about 7 pt
    fig, ax = plt.subplots(figsize=(3.45, 1.9))
    # comparison series (grey): pair edges enumerated or materialized
    ax.loglog(sym_n, sym, "s-", color=BAR_GRAY, lw=1.2, ms=3.6, markeredgecolor="#777",
              label="aggregation, pair edges")
    ax.loglog(sizes, adm, "o-", color=BAR_GRAY, lw=1.2, ms=3.6, markeredgecolor="#777",
              label="admission, pair edges")
    # proposed series (ink): equality-based sub-relations kept as classes
    ax.loglog(sizes, sym_c, "s-", color=NAVY, lw=1.2, ms=3.6,
              label="aggregation, class counts")
    ax.loglog(sizes, adm_c, "o-", color=NAVY, lw=1.2, ms=3.6,
              label="admission, class counts")

    # reference slopes anchored on the first point of each series
    def ref(xs, y0, k, color, label, dy):
        x = [xs[0], xs[-1]]
        y = [y0, y0 * (x[1] / x[0]) ** k]
        ax.loglog(x, y, ":", color=color, lw=0.8, alpha=.7)
        ax.text(x[1], y[1] * dy, label, color=color, fontsize=6.3, ha="right",
                style="italic")
    ref(sym_n, sym[0], 2, "#777", "slope 2", 2.2)
    ref(sizes, sym_c[0], 1, NAVY, "slope 1", 2.2)
    ref(sizes, adm[0], 1, "#777", "slope 1", 2.2)
    ax.text(sizes[-1], adm_c[-1] * 3.0, "constant", color=NAVY, fontsize=6.3,
            ha="right", style="italic")
    ax.set_ylim(bottom=min(adm_c) / 4)     # room under the flat series
    ax.set_yticks([1e-6, 1e-4, 1e-2, 1, 100])   # one label every two decades

    ax.set_xlabel("active sessions in the window, $|S_W|$", fontsize=7, labelpad=1)
    ax.set_ylabel("latency (s)", fontsize=7, labelpad=1)
    ax.tick_params(labelsize=6.5, length=2, pad=1.5)
    ax.grid(True, which="both", alpha=.25, lw=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    # legend below the axes, with a clear gap after the x label
    h, l = ax.get_legend_handles_labels()
    fig.tight_layout(pad=0.2, rect=(0, 0.2, 1, 1))
    y0 = ax.get_position().y0
    fig.legend(h, l, loc="upper center", bbox_to_anchor=(0.5, y0 - 0.15), ncol=2, fontsize=6.3,
               frameon=False, handletextpad=0.3, columnspacing=1.0, labelspacing=0.3, borderpad=0.2)
    out = os.path.join(OUT, "fig5_latency.png")
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"OK: {out}")


if __name__ == "__main__":
    root = os.path.abspath(os.path.join(OUT, "..", "..", ".."))
    # Fig. 1 (fig1_scoping) is a draw.io schematic, not generated here.
    # Sources live in src-drawio/; see README.md for the export procedure.
    fig_stops(root)
    fig_operating(root)
    fig_latency(root)
