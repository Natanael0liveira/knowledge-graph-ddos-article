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
  four classifier families given the full flow-feature set (AUC 0.471–0.502),
  while the cross-session representation reaches **0.98 against 0.50**
  (Cohen's *d* = 22.4, all 30 paired runs in the same direction).
- **A negative result on mitigation scope.** Scoping by the property most of the
  cluster shares, the obvious choice, selects a *legitimate* fingerprint once the
  botnet spans several TLS stacks: **0% of the attack blocked, 39% of legitimate
  traffic hit**. Choosing the discriminator by **enrichment** over a profile of
  normal traffic blocks 85–90% with no collateral observed.
- **The rule as a detector.** At the same zero-false-positive operating point the
  symbolic path recovers **90% of a 25-stack campaign where the learned model
  recovers 36%**, a gap that AUC hides.
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
docs/                     concepts, runtime, metrics, evaluation design, prior art
ontology/                 ddos_ontology.owl
shared/                   shared bibliography
```

## Finding what you need

Three entry points: a formulation you want the definition of, a claim you want
the experiment behind, or a figure you want the source of.

### Formulations and where each is defined

| Formulation | What it is | Paper | Docs | Code |
|---|---|---|---|---|
| Ω(S) = Σᵢ wᵢ·\|Eᵢ(S)\| | Coordination mass of a candidate cluster | §III-F, eq. (1) | [`concepts.md`](docs/concepts.md) | [`reason.py`](experiments/pillar2-symbolic-reasoning/scripts/reason.py) |
| wᵢ ∈ [0,1], the six weights | Evasion-cost ordering of the sub-relations | §III-D, Fig. 1; App. B | [`concepts.md`](docs/concepts.md) | [`ddos_ontology.owl`](ontology/ddos_ontology.owl) |
| τ_cluster | Firing threshold: 99th percentile of Ω over legitimate clusters | §IV-B | [`concepts.md`](docs/concepts.md) | `reason.py --tau` |
| c(f)/b(f) ≥ ρ, c(f) ≥ σ | Scope derivation by enrichment (ρ = 3, σ = 0.002) | §III-H | [`concepts.md`](docs/concepts.md) | [`evidence_mitigation.py`](experiments/pillar4-evidence-mitigation/scripts/evidence_mitigation.py) |
| σ < 1/M | Why the support floor depends on botnet fragmentation | §III-H, §V-D | [`evaluation.md`](docs/evaluation.md) | — |
| Per-pair decision procedures | JA4 near-match, identity overlap, DTW, cosine, prefix match | App. A | [`runtime.md`](docs/runtime.md) | see note below |
| O(\|S_W\|·c) admission cost | Why the hot path is linear and the symbolic layer quadratic | §III-E, §V-E; App. D | [`runtime.md`](docs/runtime.md) | [`bench_latency.py`](experiments/sprint-6-noms/scripts/bench_latency.py) |
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
| [`sprint-5/`](experiments/sprint-5/) | Comparison against KLAGE on CIC-IoT2023 Slowloris | §V-C | `make run` |
| [`sprint-6-noms/`](experiments/sprint-6-noms/) | Latency of both layers, four ML families, window sweep, canonical realistic scenario, profile drift | §V-E; App. D | `make latency`, `make all-hd`, `make drift` |
| [`pillar2-symbolic-reasoning/`](experiments/pillar2-symbolic-reasoning/) | Verdict as derivation: SWRL instantiates, SPARQL aggregates Ω(S) ≥ τ | §III-G, §V-B | `make demo` |
| [`pillar4-evidence-mitigation/`](experiments/pillar4-evidence-mitigation/) | Evidence chain (JSON-LD + STIX 2.1) and scope derivation, frequency rule against enrichment | §III-H, §V-D | `make demo` |

Cross-cutting write-ups: [`experiments/METHODOLOGY.md`](experiments/METHODOLOGY.md)
for how the evaluation was built and what was corrected along the way, and
[`experiments/FINDINGS.md`](experiments/FINDINGS.md) for the results in prose,
including the negative ones.

### Figures, tables and listings

Nothing here is drawn by hand from a number; every data figure regenerates from
its result file.

| Artifact | Source |
|---|---|
| Fig. 1 (ontology), Fig. 2 (pipeline) | draw.io sources in [`figures/src-drawio/`](papers/http-session-noms/figures/src-drawio/) |
| Fig. 3 (scope derivation), Fig. 4 (regime), Fig. 5 (cost) | [`make_figures_en.py`](papers/http-session-noms/figures/make_figures_en.py) |
| Ablation AUC table | `sprint-6-noms/results/canonical_realistic.json` |
| Symbolic rule vs learned model table | `sprint-6-noms/results/realistic_consolidated.csv` via [`symbolic_detector.py`](experiments/sprint-6-noms/scripts/symbolic_detector.py) |
| Cost tables and window sweep | `sprint-6-noms/results/latency_summary.json` |
| Listing 1 (SWRL + SPARQL) | [`relatedBy.swrl`](experiments/pillar2-symbolic-reasoning/rules/relatedBy.swrl), [`coordinatedHTTPFlood.rq`](experiments/sprint-1/queries/coordinatedHTTPFlood.rq) |
| Listing 2 (evidence chain) | `pillar4-evidence-mitigation/results/chains/` |

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
cd ../sprint-6-noms && make latency # cost model; runs without the data drive
cd ../sprint-6-noms && make drift   # background-profile sensitivity
```

Stages needing the large captures are gated behind `make check-data`; see each
stage's README for what it expects on disk.

Both scope derivations ship side by side, the frequency rule that fails and the
enrichment rule that replaces it, so the negative result is reproducible rather
than asserted. The background profile the enrichment test needs comes from an
attack-free generator run, so no labels enter the decision path.

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

Submitted to IEEE/IFIP NOMS. The manuscript is 11 pages, with the main text in
the first 8. See `papers/http-session-noms/README.md` for the submission
checklist and `docs/` for the conceptual and experimental background.
