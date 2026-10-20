# NOMS paper, Portuguese version

**Status: one round behind.** `article.tex` is a sentence-by-sentence Portuguese translation of
the English article of round 74 (2026-10-18). The English paper is now at round 75 (`59a5b1a`,
2026-10-20), a fluency rewrite of the whole body (the enrichment limit, "selects" and "covers",
the abstract's 33–39%, Table VII's post hoc marks), which this translation has not followed yet.

**This is not the submission.** NOMS requires English and caps the main text at 8 pages;
Portuguese runs longer, and that limit was not pursued here (14 pages). Submit the English
article. This copy exists for reading, internal review and discussion with readers who prefer
Portuguese. Like the English PDF, `article.pdf` stays local while the paper is under review.

The directory also holds `guia-de-estudo.md`, a study guide in Portuguese for the English paper,
revised for round 75 (2026-10-20): from the story in 15 minutes to how the method works and to
each table and figure, with a self-test at the end of each part. Its terms follow the English
paper of round 75 ("limite de enriquecimento" for the enrichment limit), so where it differs from
this translation, the translation is the one behind.

## How it was translated, and how to keep it in sync

Each English sentence has one Portuguese sentence, in the same order. The fixed glossary is in the
header comment of `article.tex`: fingerprint = impressão digital, stack = pilha TLS, trigger and
gate = gatilho, held-out day = dia novo, unseen filter = filtro de impressões inéditas, misfire =
disparo indevido, fallback = recurso de contingência, versus = contra, and others. Decimals take a
comma (`$0{,}1\%$`) and thousands a thin space (`1\,000`).

Two deliberate departures:
- the Acknowledgment adds that the AI assistant also translated this version, since that is what
  happened;
- the tables use shorter labels where the Portuguese would overflow the column (`Comp.`,
  `Aprend.`), and Table I wraps its cells. The notes define each abbreviation.

Checks, for round 74: every number of the English body appears in the Portuguese one (only table
spacing parameters differ), and an independent reviewer compared the two texts paragraph by
paragraph. A later English change has to be ported by hand, sentence by sentence, with the
glossary; then compare the numbers of the two bodies and reread the changed paragraphs against
the English.

## What differs

| | English (submission) | Portuguese (this) |
|---|---|---|
| Pages | 12 (body 8, then references and appendices A–F) | 14 (not bound by the page limit) |
| babel | not loaded | `[brazilian]`, with `\figurename` pinned to `Fig.` |
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

`IEEEtran.cls`, `IEEEtran.bst`, `stfloats.sty` and `references.bib` are identical copies of the
English version's.
