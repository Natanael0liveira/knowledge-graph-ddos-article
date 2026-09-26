# Session-Centric Knowledge Graphs for Distributed Application-Layer DDoS

Model the **HTTP session as a first-class ontological entity** and reason over
**sets of correlated sessions**, not over sessions in isolation.

This repository holds the ontology, the runtime pipeline, the experiments and the
manuscript for a paper submitted to IEEE/IFIP NOMS.

---

## The problem

A distributed Slow HTTP DoS campaign keeps every source below any reasonable
per-session threshold. Examined one at a time, each session is statistically
indistinguishable from a legitimate one: the discriminative signal lives in the
structure *between* sessions, in reused identities, shared TLS fingerprints and
many origins converging on one endpoint.

Detectors discard that structure by flattening the session into a feature vector.
Recent knowledge-graph detectors reason at the network-node level and stop at a
textual report, leaving the operational half open: *which* clients to act on, on
*what* evidence, and with a filter narrow enough not to disconnect the legitimate
users of the service under attack.

## The approach

| | State of the art | This work |
|---|---|---|
| Reasoning unit | Session as a feature vector | `ApplicationSession` as an OWL entity |
| Relations between sessions | None, or implicit in learned embeddings | **Six typed sub-properties**, weighted by the attacker's cost of breaking each signal |
| Verdict | Opaque label, or a post-hoc explanation | The **derivation** that satisfied a SPARQL/SWRL rule |
| Mitigation scope | Global threshold, hits legitimate users | **Derived from the same graph** by an enrichment test |
| Collateral damage | Not reported | Measured and reported |

A rule fires on the weighted coordination mass Ω(S) of a candidate cluster. One
derivation serves at once as the verdict, the evidence chain (JSON-LD and
STIX 2.1) and the scope of the mitigation.

## Headline results

- **Stealthy distributed campaigns.** Per-session detection sits at chance across
  four classifier families given the full flow-feature set (ROC AUC 0.488–0.503),
  while cross-session features reach 0.93–0.98 (Cohen's *d* = 13.5 and 22.3 at
  K = 1000, all 30 paired runs in the same direction). That model does not carry
  across botnet structures: trained on one number of TLS stacks and tested on
  another, it falls to 0.48–0.75.
- **A negative result on mitigation scope.** Scoping by the property most of the
  cluster shares, the obvious choice, selects a *legitimate* fingerprint once the
  botnet spans five or more TLS stacks: **0% of the attack blocked, 39% of
  legitimate traffic hit**. A binomial enrichment test over a profile of normal
  traffic blocks 90% up to 25 stacks with no collateral observed. On generated
  stacks a per-fingerprint z-score against the same profile does the same, and a
  filter of fingerprints unseen in the profile blocks as much at 0.03% collateral.
  On stacks real clients share, the test blocks 85% at 2% collateral and the unseen
  filter none.
- **Production traffic.** On eight days of four endpoints of a CDN, fleets of
  legitimate clients that switch on together set a calibration floor on the
  smallest botnet the test can name: 16% of the busiest endpoint's window under the
  binomial, 3% under a beta-binomial that models the fleets. Above the floor a
  z-score calibrated to the same false-alarm budget does as well. A ninth day,
  analyzed with the configuration fixed in advance, gave 2 false alarms in 1,152
  windows.
- **The boundary, stated explicitly.** On conventional attacks in public datasets
  a strong per-session classifier already reaches AUC ≥ 0.98, so the gain is
  marginal there. The advantage holds only when the campaign is distributed *and*
  stealthy.

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
| Ω(S) = Σᵢ wᵢ·\|Eᵢ(S)\| | Coordination mass of a candidate cluster | §III-E, eq. (1) | [`concepts.md`](docs/concepts.md) | [`reason.py`](experiments/pillar2-symbolic-reasoning/scripts/reason.py) |
| wᵢ ∈ [0,1], the six weights | Evasion-cost ordering of the sub-relations | §III-D, Fig. 1; App. B | [`concepts.md`](docs/concepts.md) | [`ddos_ontology.owl`](ontology/ddos_ontology.owl) |
| τ_cluster | Firing threshold: 99th percentile of Ω over legitimate clusters | §III-E, §IV-B | [`concepts.md`](docs/concepts.md) | `reason.py --tau` |
| c(f)/n ≥ ρ·b(f), P[Bin(n, b(f)) ≥ c(f)] < λₑ/\|F\| | Scope derivation by a binomial enrichment test (ρ = 3, level λₑ calibrated per endpoint, never above 0.01) | §III-G | [`concepts.md`](docs/concepts.md) | [`evidence_mitigation.py`](experiments/pillar4-evidence-mitigation/scripts/evidence_mitigation.py) |
| Profile size vs. M | Why a 100-stack botnet needs a larger background profile | §V-C | [`evaluation.md`](docs/evaluation.md) | [`profile_drift.py`](experiments/sprint-6-noms/scripts/profile_drift.py) |
| Ω(S) ≥ τ per window | The rule end to end, with flash crowds (App. E) | §V-B; App. E | [`sprint-6 README`](experiments/sprint-6-noms/README.md) | [`rule_detection.py`](experiments/sprint-6-noms/scripts/rule_detection.py) |
| Per-pair decision procedures | JA4 near-match, identity overlap, DTW, cosine, prefix match | App. A | [`runtime.md`](docs/runtime.md) | see note below |
| Σₖ C(nₖ, 2) class counting | Why admission is constant and the symbolic layer linear | §III-F, §V-E; App. D | [`runtime.md`](docs/runtime.md) | [`bench_latency.py`](experiments/sprint-6-noms/scripts/bench_latency.py) |
| AUC, recall @ FPR = 0, collateral damage | The metrics every result is reported in | §IV-B | [`metrics.md`](docs/metrics.md) | — |

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
| [`sprint-3/`](experiments/sprint-3/) | Baselines and the (a)–(d) ablation — the AUC 0.50 vs 0.98 result | §V-A | `make ablation`, `make multiattack` |
| [`sprint-4/`](experiments/sprint-4/) | Full run, weight calibration, JA4 isolation, robustness sweep | §V-A; App. B | `make all` |
| [`sprint-5/`](experiments/sprint-5/) | Comparison against KLAGE on CIC-IoT2023 Slowloris | App. C | `make run` |
| [`sprint-6-noms/`](experiments/sprint-6-noms/) | The canonical scenario and ablation, the rule as a detector, the unseen filter, profile drift, cross-M generalization, the production evaluation (calibrated level and baselines, floor, beta-binomial, fresh day), the compiled count query, the STIX export, latency, and the audit of every number | §V; Apps. C–F | `make help` |
| [`pillar2-symbolic-reasoning/`](experiments/pillar2-symbolic-reasoning/) | Verdict as derivation on a toy graph: the SWRL rules run as SPARQL CONSTRUCT, SPARQL aggregates Ω(S) ≥ τ | §III-E, §V-B | `make demo` |
| [`pillar4-evidence-mitigation/`](experiments/pillar4-evidence-mitigation/) | Evidence chain (JSON-LD + STIX 2.1) and scope derivation, frequency rule against enrichment | §III-G, §V-C | `make demo` |

Cross-cutting write-ups: [`experiments/METHODOLOGY.md`](experiments/METHODOLOGY.md)
for how the evaluation was built and what was corrected along the way, and
[`experiments/FINDINGS.md`](experiments/FINDINGS.md) for the results in prose,
including the negative ones.

### Figures, tables and listings

Nothing here is drawn by hand from a number; every data figure regenerates from
its result file.

| Artifact | Source |
|---|---|
| Fig. 1 (ontology) | draw.io source in [`figures/src-drawio/`](papers/http-session-noms/figures/src-drawio/) |
| Fig. 2 (collateral), Fig. 3 (cost), Fig. 4 (production operating points) | [`make_figures_en.py`](papers/http-session-noms/figures/make_figures_en.py), from `unseen_synth_summary.csv`, `latency_summary.json` and `production_tables.json` in `experiments/sprint-6-noms/results/` |
| Ablation numbers (Section V-A) | `canonical_realistic.json`, `canonical_baselines.json`, `cross_m_generalization.json` |
| Table II (the rule as a detector) | `symbolic_detector.json` via [`symbolic_detector.py`](experiments/sprint-6-noms/scripts/symbolic_detector.py), `unseen_synth_summary.csv` via [`unseen_synth.py`](experiments/sprint-6-noms/scripts/unseen_synth.py) |
| Tables III and IV (production) | `production_tables.json` via [`production_tables.py`](experiments/sprint-6-noms/scripts/production_tables.py); its inputs are the operator's exports and stay off the repository |
| Table V (the rule per window) | `rule_detection_*.json` via [`rule_detection.py`](experiments/sprint-6-noms/scripts/rule_detection.py) |
| Cost numbers (Section V-E, App. D) | `latency_summary.json`, `latency_raw.csv` via [`bench_latency.py`](experiments/sprint-6-noms/scripts/bench_latency.py) |
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
the evaluation: the scripts behind Table II pick the cluster of largest Ω with no
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
