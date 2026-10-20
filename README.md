# TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation

*Calibration Floors and Collateral on a CDN Operator's Endpoints*: a paper prepared for
IEEE/IFIP NOMS 2027, with its ontology, pipeline and experiments.

When a low-rate distributed flood raises an alarm, the scope of the mitigation is the set of
**TLS fingerprints (JA4) over-represented among the alarm's origins** relative to the endpoint's
normal traffic, selected by a test whose level is **calibrated to a 1% false-alarm budget**. An
OWL ontology specifies the counts the decision reads, and the log store's query is compiled from it.

Released under the [MIT license](LICENSE); [NOTICE](NOTICE) lists the files that keep their own
licenses (the vendored LaTeX files and the distributions derived from CICIDS2017).

---

## The problem and the approach

A distributed Slow HTTP DoS campaign keeps every source below any per-source threshold, and each
session, examined alone, looks legitimate. Detectors at most flag the attack. The operator's
decision is the scope: *which* clients to block, on *what* evidence, with a filter narrow enough
to spare legitimate users, and where no such filter exists, when to fall back to a rate limit or
a challenge.

Per endpoint and five-minute window, a volume trigger (the distinct-origin gate) raises the alarm.
The scope is the set of fingerprints the binomial enrichment test selects, joined with fingerprints
absent from the profile (the unseen filter).

| | Prior mitigation scopes (Table I) | This work |
|---|---|---|
| Filter matches | header fields, prefixes, flow features | TLS fingerprints (JA4) |
| Chosen by | congestion, a filter budget, the requesting party | an enrichment test against the endpoint's profile, calibrated per endpoint |
| Cost to legitimate users | the aggregate, the prefix or every client | measured per alarm and per window |
| Specification | code | an OWL ontology compiled into the count query |

Of the exchange standards examined, STIX 2.1, DOTS and BGP Flowspec have no JA4 property in their
core vocabulary, and OCSF records JA4 but defines no filter over it.

## Headline results

**Generated campaigns** (Section V-A, Table III)
- Blocking the alarm's most common fingerprint stops no attackers and blocks 39% of legitimate
  traffic once the botnet spans five TLS stacks.
- Profile-relative scoping covers 90% of attackers on up to 25 new stacks, with no observed
  collateral and no labels.

**Production traffic, 23 days of four CDN endpoints** (Sections V-B to V-D)

| Measure | Result |
|---|---|
| False alarms, 5 test days | 0.1% of clean windows (5 of 5,643); pooled, gate and scope each exceed the 1% budget alone |
| False alarms, 14 later pre-specified days | 0.19% (31 of 16,103): about twice the test-day rate, inconsistent with it, within the budget |
| Clients a misfire blocks | a median 33–39% of the window |
| Calibration floor, rare shared fingerprints | 8% of the busiest endpoint's median window; 4–19 median windows on the others |
| Tenth-size botnet on the busiest endpoint | 11.8% blocked, since the gate opens in only 6–13% of its windows |
| Botnet on the most common fingerprints | mostly missed: 7.0% of 100 attackers |

The current candidate, a cross-fitted beta-binomial behind a seasonal gate, was built post hoc and
fixed before the 14-day block. [`FINDINGS.md`](experiments/FINDINGS.md#the-current-candidate-vi)
gives its results and limits.

## Repository map

```
papers/
  http-session-noms/            the NOMS submission: LaTeX, figures, draw.io sources, checklist
  http-session-noms-pt/         Portuguese translation (one round behind) and the study guide
  http-session/                 earlier, superseded manuscript
experiments/
  sprint-1/ … sprint-5/         pipeline, generator, baselines, full run, KLAGE comparison
  sprint-6-noms/                the paper's evaluation, the production results, the audit
  pillar2-symbolic-reasoning/   the sub-relations as SWRL rules, Ω as a SPARQL aggregation
  pillar4-evidence-mitigation/  evidence chain, scope derivation, JSON-LD and STIX export
docs/                           concepts, metrics, evaluation design, runtime, positioning, references
ontology/                       ddos_ontology.owl
shared/                         bibliography master of the superseded manuscript
scripts/                        sync-bib.sh (copies shared/references.bib into papers/http-session/)
```

## Where things are

| To find | Go to |
|---|---|
| Definitions and formulas: Ω, the gates, the test, calibration, the floor, the ontology | [`docs/concepts.md`](docs/concepts.md) |
| Metrics, statistical tests and the columns of Tables IV–VII | [`docs/metrics.md`](docs/metrics.md) |
| The experimental design and the two pre-specified protocols | [`docs/evaluation.md`](docs/evaluation.md) |
| Windows, the compiled query, measured cost, and where each formula lives in the code | [`docs/runtime.md`](docs/runtime.md) |
| Positioning against related work and the exchange standards | [`docs/prior-art.md`](docs/prior-art.md) |
| What each reference supports | [`docs/references.md`](docs/references.md) |
| The results in prose, negative ones included | [`experiments/FINDINGS.md`](experiments/FINDINGS.md) |
| How the evaluation was built and corrected | [`experiments/METHODOLOGY.md`](experiments/METHODOLOGY.md) |
| Each stage, and what runs without the data drive | [`experiments/README.md`](experiments/README.md) |
| Every run and review round, in order | [`experiments/sprint-6-noms/README.md`](experiments/sprint-6-noms/README.md) |
| The paper's layout, build and submission checklist | [`papers/http-session-noms/README.md`](papers/http-session-noms/README.md) |

### Figures, tables and listings

Every data figure and table regenerates from a committed result file in
[`experiments/sprint-6-noms/results/`](experiments/sprint-6-noms/results/); none is drawn by hand.

| Paper element | Source |
|---|---|
| Fig. 1, the scoping pipeline | draw.io source in [`figures/src-drawio/`](papers/http-session-noms/figures/src-drawio/) |
| Figs. 2–4 | [`make_figures_en.py`](papers/http-session-noms/figures/make_figures_en.py), from `production_tables.json` and `latency_summary.json` |
| Table III, the scope on generated traffic | `symbolic_detector.json` ([`symbolic_detector.py`](experiments/sprint-6-noms/scripts/symbolic_detector.py)), `unseen_synth_summary.csv` ([`unseen_synth.py`](experiments/sprint-6-noms/scripts/unseen_synth.py)) |
| Tables IV–VI, production | `production_tables.json` ([`production_tables.py`](experiments/sprint-6-noms/scripts/production_tables.py)), `floor_bands.json` ([`floor_bands.py`](experiments/sprint-6-noms/scripts/floor_bands.py)), `waf_labels.json` ([`waf_labels.py`](experiments/sprint-6-noms/scripts/waf_labels.py)) |
| Table VII, the 14-day block | `production_tables_block.json`, `block_report.json` ([`block_report.py`](experiments/sprint-6-noms/scripts/block_report.py)), under [`heldout_block_protocol.md`](experiments/sprint-6-noms/results/heldout_block_protocol.md) |
| App. C, the ablation and cross-M tests | `canonical_realistic.json`, `canonical_baselines.json`, `cross_m_generalization.json` |
| App. D, the cost model | `latency_summary.json`, `latency_raw.csv` ([`bench_latency.py`](experiments/sprint-6-noms/scripts/bench_latency.py)) |
| App. D, Listing 1, the evidence chain | [`example_chain.py`](experiments/sprint-6-noms/scripts/example_chain.py) → `example_chain.jsonld` |
| App. E, the rule per window | `rule_detection_*.json` ([`rule_detection.py`](experiments/sprint-6-noms/scripts/rule_detection.py)) |

The [Sprint 6 README](experiments/sprint-6-noms/README.md#results-by-paper-element) maps every
result file and its make target. Figure conventions, including the scale rule that keeps text
legible at print size, are in [`figures/README.md`](papers/http-session-noms/figures/README.md).

## Reproducing

The checks below need no data drive, once `experiments/.venv` exists
([`experiments/README.md`](experiments/README.md#python-environment)):

```bash
cd experiments/sprint-6-noms
make audit                      # about 250 numbers of the paper against results/
make block-report-check         # the 14-day block's report code on the paper's numbers
make compile-check stix-check   # the compiled query and the STIX 2.1 export
make latency                    # the cost model (long)
```

The other targets read the laboratory captures, the scenario caches or the operator's exports on
the data drive, and [`experiments/README.md`](experiments/README.md) says what each stage needs.
The production exports stay with the operator's data; only anonymized summaries (E1–E4, counts
and rates) are committed.

## Building the paper

```bash
cd papers/http-session-noms
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

`IEEEtran.cls`, `IEEEtran.bst` and `stfloats.sty` are vendored so that local and Overleaf builds
place floats identically. The PDFs stay out of the repository while the paper is under review.

## Status

Prepared for IEEE/IFIP NOMS 2027, submission through JEMS3 by 9 November 2026: 12 pages, the main
text and Acknowledgment on the first 8, then references and appendices A–F. The checklist is in
[`papers/http-session-noms/README.md`](papers/http-session-noms/README.md).
