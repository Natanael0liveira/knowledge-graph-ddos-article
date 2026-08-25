# NOMS paper — Portuguese version

A faithful rendering of [`../http-session-noms/`](../http-session-noms/): same
two-column IEEEtran format, same numbers, same figures.

**This is not the submission.** NOMS requires English, and caps the main text at
8 pages; Portuguese runs 15–20% longer and that constraint was not pursued here.
Submit `../http-session-noms/article.pdf`. This copy exists for reading, internal
review and discussion with readers who prefer Portuguese.

## What differs

Nothing in content. Every correction made to the English version is ported here.

| | English (submission) | Portuguese (this) |
|---|---|---|
| Pages | 11 (body 8, refs 9–10, appendices 9–11) | 12 |
| babel | — | `[brazilian]`, with `\figurename` pinned to `Fig.` |
| Decimals | point (`0.982`) | comma (`0{,}982`) |
| Code blocks | `Listing 1-2` | `Listagem 1-2` |
| Figures | English labels | **same figures, English labels** |

Figures are binary copies of the English ones and keep English labels. To
generate them in Portuguese, adapt the strings in
`../http-session-noms/figures/make_figures_en.py` and in
`src-drawio/fig1_ontology.drawio`.

## Building

```bash
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

`IEEEtran.cls`, `IEEEtran.bst` and `references.bib` are copies of the English
version's; the `.bib` is identical, the references being the same.

## Keeping in sync

Any content change made in English has to be replicated here by hand. There is no
automatic generation: the translation was done by reading, not by tooling, and a
mechanical diff would not follow it.
