# NOMS paper — Portuguese version

A faithful rendering of [`../http-session-noms/`](../http-session-noms/): same
two-column IEEEtran format, same numbers, same figures.

**This is not the submission.** NOMS requires English, and caps the main text at
8 pages; Portuguese runs 15–20% longer and that constraint was not pursued here.
Submit `../http-session-noms/article.pdf`. This copy exists for reading, internal
review and discussion with readers who prefer Portuguese.

## Status

The Portuguese article lags the English one. It predates the current title
(*TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation: Calibration Floors and
Collateral on a CDN Operator's Endpoints*), the restructured Sections III and V, the
configuration table, the cross-fitted calibration, the floors of the configurations,
the ratio limit, the analysis of the WAF's verdicts under both profiles and the
endpoint-day intervals, and its `references.bib` lacks the references added
since. Until it is ported, read the English article, or the study guide
[`guia-de-estudo.md`](guia-de-estudo.md), which teaches the current English version
in Portuguese, formula by formula.

## What differs

| | English (submission) | Portuguese (this) |
|---|---|---|
| Pages | 12 (body 8, references from p. 9, appendices A–F) | 15 (not bound by the page limit) |
| babel | — | `[brazilian]`, with `\figurename` pinned to `Fig.` |
| Decimals | point (`0.982`) | comma (`0{,}982`) |
| Code blocks | `Listing 1-2` | `Listagem 1-2` |
| Figures | English labels | **same figures, English labels** |

Figures are binary copies of the English ones and keep English labels. To
generate them in Portuguese, adapt the strings in
`../http-session-noms/figures/make_figures_en.py` and in
`../http-session-noms/figures/src-drawio/fig1_scoping.drawio`.

## Building

```bash
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

`IEEEtran.cls` and `IEEEtran.bst` are copies of the English version's. The
`references.bib` must be brought level with the English one when the article is
ported.

## Keeping in sync

Any content change made in English has to be replicated here by hand. There is no
automatic generation: the translation was done by reading, not by tooling, and a
mechanical diff would not follow it.
