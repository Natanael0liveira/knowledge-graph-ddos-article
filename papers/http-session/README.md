# Superseded manuscript

**Status: superseded.** This was the earlier, Portuguese manuscript aimed at a
journal (Computers & Security). It is kept for provenance only.

The active work is the NOMS submission in
[`../http-session-noms/`](../http-session-noms/), which reframed the contribution
around six weighted `relatedBy` sub-properties, Ω(S) as the firing condition,
enrichment-based scope derivation and a collateral-damage metric. None of those
exist here.

Documents that described this manuscript section by section were removed in the
repository remodel; recover them from git history if needed.

## Building, if you need to

```bash
export LC_ALL=C
pdflatex -interaction=nonstopmode article.tex && bibtex article
pdflatex -interaction=nonstopmode article.tex
pdflatex -interaction=nonstopmode article.tex
```

`references.bib` here is a **copy** of `../../shared/references.bib`; Overleaf
does not import repositories with symlinks. Sync with `./scripts/sync-bib.sh`
from the repository root.

Only the abstract and introduction were written in full; the remaining sections
are outlines marked `\textit{[Esqueleto.]}`.
