# NOMS 2027 submission

*TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation: Calibration Floors and Collateral
on a CDN Operator's Endpoints*, round 76 (2026-10-20). The title names what the paper
measures; the session ontology is the specification the count query is compiled from (Section III-E).

## Status

```
pp. 1–8    main text (Sections I–VII) and the Acknowledgment   <- AT the 8-page limit
pp. 8–12   references (from below the Acknowledgment), then appendices A–F
total      12 pages                                            <- AT the 12-page limit
```

The Acknowledgment ends on page 8 and the references (37) start below it; page 12 is full, with
about one line to spare in all. Sections I and II fill page 1 and page 2's left column exactly,
so a line cut or added there stretches that column: cut from Section III onward. The PDF is 12
pages of US letter, all 25 fonts embedded, no Type 3 font.

## Paper map

| Part | Holds | Floats (page) |
|---|---|---|
| I, II | the problem and three contributions; prior work | Table I (2) |
| III | threat model, trigger (distinct-origin gate, base rule), scope and calibration, floor and enrichment limit, ontology; Ω in words | Fig. 1 (3) |
| IV | generator, production days, configurations, metrics | Table II (5) |
| V-A | the scope on generated traffic | Table III (5) |
| V-B | false alarms and the calibration floor | Table IV (5), Table V (6) |
| V-C | what is stopped: the trigger decides ("No gate" is the scope as its own trigger) | Fig. 2 (6), Table VI (6) |
| V-D | post hoc analyses, held-out day, 14-day block, the comparison fixed in advance, this WAF's verdicts | Fig. 3 (7) |
| VI | recommendation, what each evaluation shows, fingerprints, exchange and what the ontology adds | Table VII (7) |
| VII, Acknowledgment | conclusion and future work | ends on p. 8 |
| App. A | sub-relation specification, Eq. 1 (Ω) and the weights | p. 9 |
| App. B, C, D | weight calibration and generator inputs; instrumentation, coverage, laboratory captures, KLAGE, the learned models across stack counts; cost model and CDN-scale partitioning | p. 10; Fig. 4 and Listing 1 (11) |
| App. E, F | the rule per window and the production details left out of Section V; reproducibility | pp. 11–12 |

Table I is declared in Section I so that it lands on page 2. Fig. 3 is declared inside V-D, and
Table VII right after Section VI's heading, so that neither stretches a column. `dbltopnumber` is
capped at 1, so two full-width floats never share a page top.

## Build

```bash
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

Three files are vendored so that local and Overleaf builds are identical:
- `IEEEtran.cls` and `IEEEtran.bst`, because the local TeX Live is the *basic* scheme and does
  not ship them;
- `stfloats.sty` (from `sttools`, LPPL), which allows double-column floats at the bottom of a
  page. Without it Table I and Fig. 1 can only sit at page tops, and they stack.

The preamble falls back on `lmtt` when URW Courier (`pcr`) metrics are absent, which avoids Type 3
bitmap fonts. `references.bib` holds only the entries this paper or its Portuguese translation
cites. The PDFs stay out of the repository while the paper is under review. Figures: see
[`figures/README.md`](figures/README.md).

## Before submitting

### Done

- **The NOMS 2027 rules**, read 27 Sep 2026 and rechecked on the official pages 18 Oct 2026:
  - 8 pages of main text plus references and an optional appendix, 12 in total, with the
    Acknowledgment inside the 8; over-length papers are rejected without review;
  - the 8-page main part must be self-contained, since reviewers need not read past it;
  - registration and submission on the same day, 9 November 2026, via JEMS3
    (https://jems3.sbc.org.br/noms2027), which the CFP and the TPC's announcement link (the
    Submission Guidelines page still says EDAS);
  - notification 15 February 2027, camera-ready 28 February 2027 (Montréal, 10–14 May 2027).
- **Repository.** The public `main` and `noms-submission` carry this version, so Appendix F's URL
  shows it; push both after each commit (`git push origin noms-submission noms-submission:main`). `LICENSE` is the plain MIT text GitHub detects; `NOTICE` lists the files
  under their own licenses (the vendored LaTeX files under LPPL, the distributions derived from
  CICIDS2017).
- **Acknowledgment.** It thanks Azion Technologies "for authorizing the measurements and traffic
  statistics used in this study"; there is no funding to acknowledge. The AI-use disclosure follows
  IEEE's policy: the assistant was used "to draft and revise text throughout the manuscript, extend
  the ontology, and write all code and figures", and the authors reviewed and verified all content.
  The git history supports it (sprint-6 notebook, §72).
- **Affiliation.** The first author, also with the operator whose endpoints are evaluated, is marked
  "Also with Azion Technologies, Brazil".
- **Preprint.** IEEE asks a posted preprint to carry, on its first screen, "This work has been
  submitted to the IEEE for possible publication. Copyright may be transferred without notice, after
  which this version may no longer be accessible." GitHub is not among the places IEEE lists, so the
  PDFs (English and Portuguese) are untracked since `a5b1fcc`. Still public: the PDFs in the commits
  before it, and the LaTeX sources.

### Open

1. **Tag** the submitted commit on submission day. Before tagging, decide whether the early history
   needs a rewrite (details are kept outside the repository).
2. **JEMS3.** Register the exact title and every co-author; the author list must match the PDF and
   cannot change after acceptance, and IEEE needs an ORCID for every author at camera-ready. Confirm
   JEMS3 against EDAS with the TPC chairs.
3. **Ethics statement.** IEEE asks for one on research involving human subjects. The data are
   aggregated counts from the operator's own services, with its authorization; decide with the
   advisor whether the paper needs a sentence (the body has about one free line).
4. **Camera-ready.** IEEE PDF eXpress may flag hyperref's links and bookmarks. The Event Policies
   page's "six printed pages, plus one at US$100" contradicts the CFP and is unfinished (its dates
   say TBD): ask the chairs with the JEMS3 question.
5. **Artifact Evaluation**, before submitting the artifact:
   - confirm that NOMS 2027 keeps the track Appendix F names;
   - commit the JA4 pair comparison: Appendix F reports that the compiled query reproduced the JA4
     pair counts in the 288 windows of each day on the endpoint where the WAF blocked no client, and
     `compile_production_check*.json` records it, but the comparison ran ad hoc
     (`compile_counts.py --compare` checks only origins and /24 pairs); it needs the operator's
     exports, so it runs on the drive;
   - chain the seeded scenario caches to the targets that read them, so that every generated-traffic
     table and figure regenerates from its make target, as Appendix F says;
   - give Listing 1 and Appendix E's weight variants a make target;
   - reconcile the two binding examples in `bindings/`, which treat WAF-blocked requests differently.
6. **Portuguese version.** Port round 75's text to the translation; its floats and the study guide
   already follow round 76.

## Portuguese version

[`../http-session-noms-pt/`](../http-session-noms-pt/) holds a sentence-by-sentence translation of
round 74, one round behind, and a study guide in Portuguese for this paper.
