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
docs/                     concepts, evaluation design, prior art, references
ontology/                 ddos_ontology.owl
shared/                   shared bibliography
```

## Reproducing

Each experimental stage is driven by a Makefile and fixed seeds, so every table
and data figure in the paper regenerates from one command per stage.

```bash
cd experiments && pip install -r requirements.txt
cd sprint-3 && make            # ablation and baselines
cd ../sprint-6-noms && make    # cost model, window sweep, drift
```

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
