# NOMS paper — Portuguese version

A sentence-by-sentence Portuguese translation of
[`../http-session-noms/article.tex`](../http-session-noms/article.tex): same order, same claims,
every qualifier, number, table and figure, in Brazilian Portuguese. It follows the English
article of round 74 (2026-10-18).

**This is not the submission.** NOMS requires English and caps the main text at 8 pages;
Portuguese runs longer, and that limit was not pursued here (14 pages). Submit the English
article. This copy exists for reading, internal review and discussion with readers who prefer
Portuguese. Like the English PDF, `article.pdf` stays local while the paper is under review.

## How it was translated

Each English sentence has one Portuguese sentence, in the same order. The fixed glossary is in
the header comment of `article.tex`: fingerprint = impressão digital, stack = pilha TLS,
trigger and gate = gatilho, held-out day = dia novo, unseen filter = filtro de impressões
inéditas, misfire = disparo indevido, fallback = recurso de contingência, versus = contra, and
others. Decimals take a comma (`$0{,}1\%$`) and thousands a thin space (`1\,000`).

Two deliberate departures:
- the Acknowledgment adds that the AI assistant also translated this version, since that is
  what happened;
- the tables use shorter labels where the Portuguese would overflow the column (`Comp.`,
  `Aprend.`), and Table I wraps its cells. The notes define each abbreviation.

Checks: every number of the English body appears in the Portuguese one (only table spacing
parameters differ), and an independent reviewer compared the two texts paragraph by paragraph.

## What differs

| | English (submission) | Portuguese (this) |
|---|---|---|
| Pages | 12 (body 8, then references and appendices A–F) | 14 (not bound by the page limit) |
| babel | — | `[brazilian]`, with `\figurename` pinned to `Fig.` |
| Decimals | point (`0.982`) | comma (`0{,}982`) |
| Code block | `Listing 1` | `Listagem 1` |
| Figures | English labels | the same four figures, English labels |

The figures (`fig1_scoping`, `fig6_stops`, `fig4_operating`, `fig5_latency`) are binary copies of
the English ones and keep English labels. To draw them in Portuguese, adapt the strings in
`../http-session-noms/figures/make_figures_en.py` and in
`../http-session-noms/figures/src-drawio/fig1_scoping.drawio`.

## Building

```bash
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

`IEEEtran.cls`, `IEEEtran.bst`, `stfloats.sty` and `references.bib` are copies of the English
version's.

## Keeping in sync

Any content change made in English has to be replicated here by hand, sentence by sentence,
with the glossary above. After each port, compare the numbers of the two bodies and reread the
changed paragraphs against the English.
