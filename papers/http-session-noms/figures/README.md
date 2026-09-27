# Figures

Two categories with different workflows. Do not mix them.

## 1. Schematics — drawn in draw.io

Sources in `src-drawio/*.drawio`.

| Figure | Source | Canvas |
|---|---|---|
| `fig1_scoping` | `src-drawio/fig1_scoping.drawio` | 1032 × 265, included at `\textwidth` |

`fig1_scoping` is the calibrated scoping pipeline (round 10): log, count query
compiled from the ontology, class sizes, trigger, scope, challenge or block, with the
calibration on attack-free days feeding the trigger and the scope. It replaced
`fig1_ontology` (`src-drawio/fig1_ontology.drawio`, the ontology schematic), which
is kept in the repository but is no longer in the paper. `fig2_pipeline`
(`src-drawio/fig_pipeline.drawio`) left the paper in round 7 and describes the
retired RDF layer.

**Workflow.** Open the `.drawio` at [app.diagrams.net](https://app.diagrams.net)
or in the desktop app, edit, then *File ▸ Export as ▸ PDF* with **Crop** on and
**Include a copy of my diagram** on, so the export stays editable and the source
is not lost.

### Scale rule — read before drawing

Text shrinks with the figure, and it is easy to produce something illegible
without noticing. An earlier `fig1_ontology.png` was 2100 px included at
0.72`\textwidth`: a factor of 0.18, body text at roughly **5 pt printed**, below
the IEEE floor.

The convention adopted is: **draw at 2× the final size and include at twice the
width.** For a full-width `figure*`, `\textwidth` ≈ 516 pt, so the canvas is
**1032 pt** and draw.io fonts come out at half their nominal size:

| draw.io | printed |
|---|---|
| 21 pt (panel title) | 10.5 pt |
| 15 pt (node label) | 7.5 pt |
| 13 pt (caption, annotation) | 6.5 pt |
| 12 pt (edge label) | 6 pt |

Nothing below 12 pt in draw.io. Check the page size under *File ▸ Page Setup*
before exporting.

### Visual grammar

- Nodes as ellipses, **no fill**, thin black stroke (1.2–1.3 pt)
- Solid black arrows for model relations
- **Dashed grey** only for meta-comment: what quantifies, annotates or explains
- Panel titles in bold, left-aligned, at the top
- **Dotted vertical** divider between panels
- Helvetica / Liberation Sans; no decorative colour
- Wide and short proportions

Colour only when it carries meaning, never for emphasis.

## 2. Data plots — generated from code

`fig6_stops` (Fig. 2), `fig5_latency` (Fig. 3) and `fig4_operating` (Fig. 4) come from
`make_figures_en.py`, reading the results in
`experiments/sprint-6-noms/results/` (`unseen_synth_summary.csv`,
`production_tables.json`, `latency_summary.json`). `fig4_regime` is no longer in
the paper.

```bash
python make_figures_en.py
```

**Do not redraw these by hand.** Appendix F of the paper promises that every
figure regenerates from one command; drawing them would turn a measured number
into an illustration and break that promise. To bring them closer to the
schematics, change matplotlib settings — font family, line weight, palette — not
the result.

### Palette, shared by both categories

Monochrome, matched to Fig. 1. Contrast comes from tone and marker, never from
hue, so it survives greyscale printing and colour-blind readers.

| Role | Hex | Where |
|---|---|---|
| Main series / ours | `#1a1a1a` | Bars and lines for our method; model stroke in Fig. 1 |
| Comparison series | `#bdbdbd` | Per-session baseline, frequency rule |
| Annotation | `#595959` | Grey notes, chance line, explanatory arrows, `NetworkProximity` |

In `make_figures_en.py` the constants keep their historical names (`NAVY`,
`BAR_GRAY`, `CHANCE`) so the function bodies did not have to change; only the
values did.

### Numbering: printed number and file

The filenames no longer match the printed numbers since the pipeline figure left;
they will be renamed once the figure set settles. Until then this table is the
mapping:

| Printed | Source | Type |
|---|---|---|
| Fig. 1 | `src-drawio/fig1_scoping.drawio` | draw.io schematic |
| Fig. 2 | `fig6_stops.png` | generated (Section V-B, from the `sweep` block; drawn at print size, one column of 3.45 in, fonts 6.5–7 pt) |
| Fig. 3 | `fig5_latency.png` | generated (Appendix D) |
| Fig. 4 | `fig4_operating.png` | generated (Appendix E; grey markers and arrows: the cross-fitted calibration) |
| (none) | `fig3_collateral.png` | generated, no longer in the paper: Table III carries its modal column |
| Listing 1 | `verbatim` block, Appendix A | SWRL / SPARQL rules |
| Listing 2 | `verbatim` block, Appendix D | evidence chain |

**If you add or remove a float, check the numbering in the PDF and update this
table.**
