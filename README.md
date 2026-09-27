# TLS-Fingerprint Scoping of Application-Layer DDoS Mitigation: Calibration Floors and Collateral on a CDN Operator's Endpoints

Scope the mitigation of a low-rate distributed application-layer flood by the **TLS
fingerprints over-represented among the alarm's origins**, relative to a profile of
the endpoint's normal traffic, at a level **calibrated to a false-alarm budget**. The
sessions, their typed relations and the counts the decision reads are specified in an
OWL ontology, from which the per-window count query a log store runs is compiled.

This repository holds the ontology, the pipeline, the experiments and the manuscript
for a paper submitted to IEEE/IFIP NOMS. It is released under the [MIT license](LICENSE);
the vendored LaTeX class and style files keep their own (LPPL).

---

## The problem

A distributed Slow HTTP DoS campaign keeps every source below any reasonable
per-source threshold. Examined one at a time, each session is statistically
indistinguishable from a legitimate one: the discriminative signal lives in the
structure *between* sessions, in shared TLS fingerprints and many origins converging
on one endpoint.

Flagging the endpoint is the easy part. The operator's decision is the scope of the
mitigation: *which* clients to challenge or block, on *what* evidence, with a filter
narrow enough to spare the legitimate users of the service under attack, and where
no such filter can be built, so that it falls back to a rate limit or a challenge.
Prior mitigation scopes match network and transport header fields, source prefixes
or flow features; none reads the fingerprints of an application's clients.

## The approach

| | Prior mitigation scopes | This work |
|---|---|---|
| Filter matches | Header fields, source prefixes, flow features | TLS fingerprints (JA4) of the endpoint's clients |
| Chosen by | Congestion, aggregate scores, the requesting operator | A binomial or beta-binomial enrichment test against the endpoint's own profile |
| Threshold | Fixed | Level λₑ set per endpoint to an empirical quantile: the scope alone names a filter in at most 1% of calibration windows |
| Cost to legitimate users | Rarely measured | Collateral per alarm, expected collateral per window, and the calibration floor |
| Specification | Code | OWL ontology compiled into the count query; evidence chain in JSON-LD and STIX 2.1 |

Per endpoint and five-minute window a volume trigger (distinct origins, or the
coordination mass Ω(S)) raises the alarm, and the scope is the set of fingerprints the
test names, joined with fingerprints absent from the profile.

## Headline results

- **A negative result on mitigation scope.** On generated traffic, scoping by the
  fingerprint most of the alarm shares selects a *legitimate* one once the botnet
  spans a few TLS stacks: **0% of the attack blocked, 39% of legitimate traffic hit**
  at five stacks. Profile-relative scopes (the binomial test, a z-score) block 90% up
  to 25 stacks with no collateral observed and no labels. A learned cross-session
  model reaches AUC 0.93–0.98 on its own botnet structure and falls to 0.48–0.75 on
  another number of stacks.
- **False alarms on production traffic.** On eight days of four of a CDN operator's
  own endpoints, the recommended configuration (the binomial test joined with a filter
  for fingerprints absent from the profile, behind a distinct-origin gate) raises false
  alarms on 0.1% of clean windows (5 of 5,643), in sample and cross-fitted. Each
  calibrated component alone exceeds its 1% target on the days after calibration (the
  scope alone fires on 2.2%), and gate and scope misfire together more often than if
  they were independent: the conjunction is rare, not the errors independent. Misfires
  cluster by endpoint-day, so intervals come from a bootstrap over endpoint-days too.
- **The calibration floor, and a harder limit.** Fleets of legitimate clients that
  switch on together set a floor below which the scope names only the stacks chance
  makes larger. A 25-stack botnet on stacks real clients also present is named only past
  8% of the busiest endpoint's window (254 attackers) and past 4 to 19 whole windows on
  the small ones; on new stacks the unseen filter names it from 139 attackers. Each
  stack holds at most 0.9/M of the window, so no fingerprint more common than
  0.9/(ρM) = 1.2% can be enriched by a 25-stack botnet: those are the 4 to 28 most common
  fingerprints of each endpoint, and they carry 86–94% of its origins. A beta-binomial
  background, built post hoc, nearly meets its 1% target out of sample (1.1%) and lowers
  the shared-stack floor to 6% and at most 4.4 windows.
- **Naming a botnet is not stopping it.** On the busiest endpoint the scope names a
  botnet of a tenth of the window in every window, but the distinct-origin gate opens in
  only 6–13% of the windows of such small botnets, so the configuration stops 11.8% of
  it. On the small endpoints the gate opens, and the floor decides.
- **The WAF's verdicts cannot label floods.** The clients the operator's WAF blocks sit
  mostly on common fingerprints. With a profile of all clients the scopes name a filter
  in 2–3% of the windows of the two endpoints where the WAF blocks most, fewer of the
  clients they would block were blocked than a random pick would give, and they catch
  the WAF's surges at chance. The agreement a profile without the blocked clients shows
  (84–99%) is built in.
- **A held-out day.** A ninth day, analyzed with the configuration fixed in advance,
  gave 2 false alarms in 1,152 windows, consistent with the test days' rate (P = 0.27).
  The test is weak (power 37% against a tripled rate), and the gate opened in only 3 of
  the day's clean windows, where the scope misfired twice (against 5 of 168 on the test
  days).
- **The boundary, stated explicitly.** Bots that present the endpoint's most common
  fingerprints are mostly missed, on generated and on production traffic. On
  conventional attacks in public datasets a strong per-session classifier already
  reaches AUC ≥ 0.98, so the method matters only when the campaign is distributed
  *and* stealthy.

## Repository map

```
papers/
  http-session-noms/      NOMS submission (LaTeX, figures, draw.io sources)
  http-session-noms-pt/   Portuguese rendering of the same paper
  http-session/           earlier, superseded manuscript
experiments/
  sprint-1/               extraction pipeline: PCAP -> JA4 + flows -> sessions -> graph
  sprint-2/               calibrated synthetic generator
  sprint-3/               baselines and ablation
  sprint-4/               full run and weight calibration
  sprint-5/               comparison against KLAGE on CIC-IoT2023
  sprint-6-noms/          experiments added for the submission
  pillar2-symbolic-reasoning/   verdict as derivation (SWRL + SPARQL)
  pillar4-evidence-mitigation/  evidence chain and derived mitigation scope
docs/                     concepts, runtime, metrics, evaluation design, writing style
ontology/                 ddos_ontology.owl
shared/                   shared bibliography
```

## Finding what you need

Three entry points: a formulation you want the definition of, a claim you want
the experiment behind, or a figure you want the source of.

### Formulations and where each is defined

| Formulation | What it is | Paper | Docs | Code |
|---|---|---|---|---|
| Ω(S) = Σᵢ wᵢ·\|Eᵢ(S)\| | Coordination mass of a candidate cluster | §III-B, eq. (1) | [`concepts.md`](docs/concepts.md) | [`reason.py`](experiments/pillar2-symbolic-reasoning/scripts/reason.py) |
| wᵢ ∈ [0,1], the six weights | Evasion-cost ordering of the sub-relations | §III-E; App. B | [`concepts.md`](docs/concepts.md) | [`ddos_ontology.owl`](ontology/ddos_ontology.owl) |
| τ, the two gates | Firing thresholds: the 99th percentile of distinct origins (the deployed gate) or of Ω over attack-free windows | §III-B | [`concepts.md`](docs/concepts.md) | `reason.py --tau`, [`rule_detection_production.py`](experiments/sprint-6-noms/scripts/rule_detection_production.py) |
| c(f)/n ≥ ρ·b(f), P[Bin(n, b(f)) ≥ c(f)] < λₑ/\|F\| | Scope derivation by a binomial enrichment test (ρ = 3, level λₑ calibrated per endpoint, never above 0.01), its z-score and beta-binomial variants, the calibration floor | §III-C | [`concepts.md`](docs/concepts.md) | [`evidence_mitigation.py`](experiments/pillar4-evidence-mitigation/scripts/evidence_mitigation.py) |
| Var[c] = n·b(1−b)·(1+(n−1)φ) | The beta-binomial background and its moment estimator of φ | §III-C | [`concepts.md`](docs/concepts.md) | [`rule_detection_production.py`](experiments/sprint-6-noms/scripts/rule_detection_production.py) |
| Smallest A with 0.9A/M ≥ c_min(n₀ + A) | The calibration floor, and ⌈k_min·M/0.9⌉ for new stacks under the unseen filter | §III-D; §V-B | [`concepts.md`](docs/concepts.md) | [`production_tables.py`](experiments/sprint-6-noms/scripts/production_tables.py) (`floor`, `deployed_floor`), [`floor_bands.py`](experiments/sprint-6-noms/scripts/floor_bands.py) |
| b > 0.9/(ρM) | The ratio limit: no M-stack botnet enriches a fingerprint more common than 1.2% (M = 25) | §III-D; §V-B | [`concepts.md`](docs/concepts.md) | [`floor_bands.py`](experiments/sprint-6-noms/scripts/floor_bands.py) |
| 0.9 · P[Bin(A − 1, 0.9/M) ≥ c_min − 1] | Share of a botnet on new stacks the scope names below and above the floor | §V-B | [`concepts.md`](docs/concepts.md) | `production_tables.model_new` |
| Leave one calibration day out | Cross-fitted calibration of λₑ, the z threshold and the known fleets | §V-B | [`sprint-6 README`](experiments/sprint-6-noms/README.md) §15 | `rule_detection_production.py --split crossfit` |
| Profile size vs. M | Why a 100-stack botnet needs a larger background profile | §V-A | [`evaluation.md`](docs/evaluation.md) | [`profile_drift.py`](experiments/sprint-6-noms/scripts/profile_drift.py) |
| Ω(S) ≥ τ per window | The rule end to end, with flash crowds (App. E) | §V-A; App. E | [`sprint-6 README`](experiments/sprint-6-noms/README.md) | [`rule_detection.py`](experiments/sprint-6-noms/scripts/rule_detection.py) |
| Per-pair decision procedures | JA4 near-match, identity overlap, DTW, cosine, prefix match | App. A | [`runtime.md`](docs/runtime.md) | see note below |
| Σₖ C(nₖ, 2) class counting | Why admission is constant and aggregation linear | §III-E, §V-C; App. D | [`runtime.md`](docs/runtime.md) | [`bench_latency.py`](experiments/sprint-6-noms/scripts/bench_latency.py) |
| AUC, recall @ FPR = 0, collateral, Clopper–Pearson and endpoint-day bootstrap intervals | The metrics every result is reported in, with expected collateral per clean window | §IV-B | [`metrics.md`](docs/metrics.md) | [`production_tables.py`](experiments/sprint-6-noms/scripts/production_tables.py) | [`metrics.md`](docs/metrics.md) | — |

> **Note on sub-relation coverage.** All six sub-relations are specified in
> Appendix A and implemented in
> [`evidence_mitigation.py`](experiments/pillar4-evidence-mitigation/scripts/evidence_mitigation.py).
> The detection and cost paths — `compute_coordination.py`, `reason.py`,
> `bench_latency.py` — instantiate the **three computable from session-granularity
> data** (TLS fingerprint, endpoint convergence, network proximity); reused
> identity, temporal pattern and payload signature need per-request fields the
> public captures do not carry, and are reported inactive rather than imputed.

### Experiments by stage

Each stage is self-contained, has its own README explaining what gap it closes,
and is driven by a Makefile with fixed seeds.

| Stage | What it establishes | Paper | Run |
|---|---|---|---|
| [`sprint-1/`](experiments/sprint-1/) | Extraction pipeline: PCAP → JA4 + flows → sessions → graph; Ω on real captures | §IV-A | `make help` — staged: `extract-ja4` → `sessions` → `clusters` → `coordination` → `validate` |
| [`sprint-2/`](experiments/sprint-2/) | Calibrated synthetic generator: Zipf α, M stacks, stealth and adversarial modes; KS-verified against CICIDS2017 | §IV-A; App. B | `make calibrate`, `make validate` |
| [`sprint-3/`](experiments/sprint-3/) | Baselines and the (a)–(d) ablation — the AUC 0.50 vs 0.98 result | App. C | `make ablation`, `make multiattack` |
| [`sprint-4/`](experiments/sprint-4/) | Full run, weight calibration, JA4 isolation, robustness sweep | §V-A; App. B | `make all` |
| [`sprint-5/`](experiments/sprint-5/) | Comparison against KLAGE on CIC-IoT2023 Slowloris | App. C | `make run` |
| [`sprint-6-noms/`](experiments/sprint-6-noms/) | The canonical scenario and ablation, the rule as a detector, the unseen filter, profile drift, cross-M generalization, the production evaluation (calibrated level and baselines, floor, beta-binomial, cross-fitted calibration, WAF verdicts as labels, fresh day), the compiled count query, the STIX export, latency, and the audit of every number | §V; Apps. C–F | `make help` |
| [`pillar2-symbolic-reasoning/`](experiments/pillar2-symbolic-reasoning/) | Verdict as derivation on a toy graph: the SWRL rules run as SPARQL CONSTRUCT, SPARQL aggregates Ω(S) ≥ τ | §III-E; App. A | `make demo` |
| [`pillar4-evidence-mitigation/`](experiments/pillar4-evidence-mitigation/) | Evidence chain (JSON-LD + STIX 2.1) and scope derivation, frequency rule against enrichment | §III-C, §V-B | `make demo` |

Cross-cutting write-ups: [`experiments/METHODOLOGY.md`](experiments/METHODOLOGY.md)
for how the evaluation was built and what was corrected along the way, and
[`experiments/FINDINGS.md`](experiments/FINDINGS.md) for the results in prose,
including the negative ones.

### Figures, tables and listings

Nothing here is drawn by hand from a number; every data figure regenerates from
its result file.

| Artifact | Source |
|---|---|
| Fig. 1 (the scoping pipeline) | draw.io source in [`figures/src-drawio/`](papers/http-session-noms/figures/src-drawio/) |
| Fig. 2 (cost, App. D), Fig. 3 (production operating points, in sample and cross-fitted, App. E) | [`make_figures_en.py`](papers/http-session-noms/figures/make_figures_en.py), from `unseen_synth_summary.csv`, `production_tables.json` and `latency_summary.json` in `experiments/sprint-6-noms/results/` |
| Ablation numbers (Appendix C) | `canonical_realistic.json`, `canonical_baselines.json`, `cross_m_generalization.json` |
| Table III (the scope on generated traffic, with the modal fingerprint's column) | `symbolic_detector.json` via [`symbolic_detector.py`](experiments/sprint-6-noms/scripts/symbolic_detector.py), `unseen_synth_summary.csv` via [`unseen_synth.py`](experiments/sprint-6-noms/scripts/unseen_synth.py) |
| Table II (configurations), Tables IV, V and VI (production) | `production_tables.json` via [`production_tables.py`](experiments/sprint-6-noms/scripts/production_tables.py), `floor_bands.json` via [`floor_bands.py`](experiments/sprint-6-noms/scripts/floor_bands.py), `waf_labels.json` via [`waf_labels.py`](experiments/sprint-6-noms/scripts/waf_labels.py), `ja4_churn.json`; their inputs are the operator's exports and stay off the repository |
| Table VII (the rule per window, App. E) | `rule_detection_*.json` via [`rule_detection.py`](experiments/sprint-6-noms/scripts/rule_detection.py) |
| Cost numbers (Section V-C, App. D) | `latency_summary.json`, `latency_raw.csv` via [`bench_latency.py`](experiments/sprint-6-noms/scripts/bench_latency.py) |
| Listing 1 (SWRL + SPARQL) | the SWRL of [`relatedBy.swrl`](experiments/pillar2-symbolic-reasoning/rules/relatedBy.swrl); the aggregation as printed in the paper, whose session-counting form the cost model times in `bench_latency.py` |
| Listing 2 (evidence chain) | [`example_chain.py`](experiments/sprint-6-noms/scripts/example_chain.py) → `experiments/sprint-6-noms/results/example_chain.jsonld` |

The Sprint-1 query [`coordinatedHTTPFlood.rq`](experiments/sprint-1/queries/coordinatedHTTPFlood.rq)
is the legacy gate of the laboratory pipeline, not Listing 1.

Conventions for adding or redrawing a figure — including the scale rule that
keeps text above the IEEE floor — are in
[`figures/README.md`](papers/http-session-noms/figures/README.md).

## Reproducing

Each experimental stage is driven by a Makefile and fixed seeds, so every table
and data figure in the paper regenerates from one command per stage. **`make`
with no target prints that stage's help** — every Makefile lists its own targets.

```bash
cd experiments && pip install -r requirements.txt
cd sprint-3 && make ablation        # the (a)-(d) ablation and baselines
cd ../sprint-6-noms && make audit   # every sprint-6 number of the paper against results/
cd ../sprint-6-noms && make compile-check stix-check   # compiled query and STIX 2.1 export
cd ../sprint-6-noms && make latency # cost model; runs without the data drive, and long
cd ../sprint-6-noms && make drift   # background-profile sensitivity (data drive)
```

Stages needing the large captures are gated behind `make check-data`; see each
stage's README for what it expects on disk.

Both scope derivations ship side by side, the frequency rule that fails and the
enrichment rule that replaces it, so the negative result is reproducible rather
than asserted. The background profile the enrichment test needs comes from
attack-free generator runs, so the test itself reads no labels. Labels enter only
the evaluation: the scripts behind Table III pick the cluster of largest Ω with no
label (`CLUSTER ?= label-free`), and the per-window evaluation uses none before
scoring.

Large captures live outside the repository; `experiments/data/` is ignored.
Third-party papers under `docs/pdfs/` are kept locally and not redistributed.

## Building the paper

```bash
cd papers/http-session-noms
pdflatex article && bibtex article && pdflatex article && pdflatex article
```

`stfloats.sty` is vendored in that directory so local and Overleaf builds place
floats identically.

## Status

Prepared for IEEE/IFIP NOMS. The manuscript is 12 pages, with the main text in
the first 8. See `papers/http-session-noms/README.md` for the submission
checklist and `docs/` for the conceptual and experimental background.
