# Figures

Two kinds, with different workflows: one schematic drawn in draw.io, and data plots generated from
code. Do not mix them.

## Printed number and file

The file names keep the numbers of an earlier figure set. Renaming touches `article.tex`, the
Portuguese copy and the script, so it waits until after submission. Until then this is the mapping:

| Printed | File | Source | Section |
|---|---|---|---|
| Fig. 1, the scoping pipeline | `fig1_scoping.png` | exported from `src-drawio/fig1_scoping.drawio` | III |
| Fig. 2, what the binomial configuration stops | `fig6_stops.png` | `make_figures_en.py`, the `sweep` block of `production_tables.json` | V-C |
| Fig. 3, the production operating points | `fig4_operating.png` | `make_figures_en.py`, `production_tables.json` (gray markers and arrows: cross-fitted) | V-D |
| Fig. 4, the cost model | `fig5_latency.png` | `make_figures_en.py`, `latency_summary.json` | App. D |
| Listing 1, the evidence chain | `verbatim` block in `article.tex` | `experiments/sprint-6-noms/scripts/example_chain.py` | App. D |

Figs. 2 and 3 are drawn at print size, one column of 3.45 in, with fonts of 6–7 pt.
`src-drawio/fig1_ontology.drawio`, the earlier ontology schematic, is kept but no longer printed.
**If you add or remove a float, check the numbering in the PDF and update this table.**

## Data plots, generated from code

```bash
# from the repository root
experiments/.venv/bin/python papers/http-session-noms/figures/make_figures_en.py
```

The script reads the committed results in `experiments/sprint-6-noms/results/`
(`production_tables.json`, `latency_summary.json`). **Do not redraw these by hand.** Appendix F
states that every generated-traffic table and figure regenerates from its make target, and Figs.
2–4 read committed result files; drawing them would turn a measured number into an illustration. To
bring them closer to the schematic, change matplotlib settings (font family, line weight, palette),
never the result.

## The schematic, drawn in draw.io

Edit `src-drawio/fig1_scoping.drawio` (page 1032 × 250) at [app.diagrams.net](https://app.diagrams.net)
or in the desktop app. Export the PNG the paper includes with

```bash
drawio -x -f png -s 3 -b 6 -o fig1_scoping.png src-drawio/fig1_scoping.drawio
```

which reproduces the committed `fig1_scoping.png` (3104 × 797 px) pixel for pixel (sprint-6
notebook, §44). Commit the `.drawio` with the PNG.

**Scale rule, read before drawing.** Text shrinks with the figure, and it is easy to produce
something illegible without noticing: an earlier schematic, 2100 px included at 0.72`\textwidth`,
printed its body text at about 5 pt, below the IEEE floor. Draw at twice the final size and include
at full width: a `figure*` is `\textwidth` ≈ 516 pt wide, so the page is 1032 pt and draw.io fonts
print at half their size.

| draw.io | printed | used for |
|---|---|---|
| 16 pt | 8 pt | the window label ("per endpoint and five-minute window") |
| 14 pt | 7 pt | node labels |
| 12 pt | 6 pt | annotations and edge labels |

Nothing below 12 pt in draw.io. Check the page size under *File ▸ Page Setup* before exporting.

**Visual grammar.**
- Nodes as ellipses, **no fill**, thin black stroke (1.2–1.3 pt).
- Solid black arrows for model relations; **dashed gray** only for what quantifies, annotates or
  explains.
- Panel titles in bold, left-aligned at the top; a **dotted vertical** divider between panels.
- Helvetica or Liberation Sans; wide and short proportions.
- Color only when it carries meaning, never for emphasis.

## Palette, shared by both kinds

Monochrome, matched to Fig. 1: contrast comes from tone and marker, never from hue, so it survives
grayscale printing and color-blind readers.

| Hex | Where |
|---|---|
| `#1a1a1a` | Fig. 2's configuration line and tenth-size triangle; Fig. 3's in-sample markers and every marker edge; Fig. 4's class-count paths and reference slope |
| `#bdbdbd` | Fig. 3's cross-fitted markers; Fig. 4's pair-edge paths |
| `#595959` | Fig. 2's dashed scope-alone line; Fig. 3's budget line, arrows and "1% budget" label |
| `#000000` | Fig. 1's strokes, with `#595959` annotations |

In `make_figures_en.py` the constants keep their historical names (`NAVY`, `BAR_GRAY`, `CHANCE`),
so the function bodies did not have to change; `NAVY2`, `GRAY`, `GRAYB` and `TXT` are defined but
unused.
