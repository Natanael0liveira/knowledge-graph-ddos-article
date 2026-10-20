# Superseded manuscript

**Status: superseded.** This is the earlier Portuguese manuscript aimed at a journal (Computers &
Security), kept for provenance only.

The active work is the NOMS submission in [`../http-session-noms/`](../http-session-noms/). It
keeps this manuscript's session ontology and weighted `relatedBy` sub-relations, but selects the
mitigation scope with a binomial enrichment test calibrated to a false-alarm budget against each
endpoint's normal traffic, gates it on distinct origins (Ω(S) is only the base rule's gate), and
evaluates it on 23 days of four CDN endpoints. This manuscript has no production evaluation and no
calibrated scope.

The abstract and introduction are complete. Sections 2–6 hold draft prose; their source headers say
`(esqueleto a desenvolver)`, an outline still to develop. Documents that described the manuscript
section by section were removed in the repository remodel; recover them from git history if needed.

## Building, if you need to

```bash
export LC_ALL=C
pdflatex -interaction=nonstopmode article.tex && bibtex article
pdflatex -interaction=nonstopmode article.tex
pdflatex -interaction=nonstopmode article.tex
```

`references.bib` here is a copy of `../../shared/references.bib`, since Overleaf does not import
repositories with symlinks. Sync it with `./scripts/sync-bib.sh` from the repository root;
`./scripts/sync-bib.sh --check` reports any divergence.
