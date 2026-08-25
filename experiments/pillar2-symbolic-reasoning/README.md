# Pillar 2 — Symbolic reasoning (verdict as derivation)

The `coordinatedHTTPFlood` rule is evaluated as a **weighted sum over the
`relatedBy_*` sub-relations**, and the verdict is the **derivation** that
satisfied the rule, not the output of a classifier.

## Design, and where SWRL ends

| Step | Language | What |
|---|---|---|
| 1. Instantiate `relatedBy_*` pair-wise | **SWRL** (Horn rules) | "if ?a and ?b share a JA4 → `relatedByTLSFingerprint(?a,?b)`" |
| 2. Aggregate Ω(S) = Σ wᵢ·\|pairsᵢ\| ≥ τ | **SPARQL** | SWRL cannot aggregate; SPARQL sums, reading the weights from the ontology |

The formal SWRL rules are in [`rules/relatedBy.swrl`](rules/relatedBy.swrl).
Because rdflib has no native SWRL reasoner and these rules are CONSTRUCTs, step 1
runs as a SPARQL CONSTRUCT, **semantically equivalent** to the Horn rules.

Weights are read from `coordinationWeight` in `ddos_ontology.owl`. **Nothing is
hard-coded**: the weighting is governed by the ontology.

## Demo

```bash
make demo
```

```
Weights (from the ontology): TLS=1.0 ... NetworkProximity=0.3
Materialized edges: relatedByTLSFingerprint=10, relatedByEndpointConvergence=28, NetworkProximity=0
> RULE FIRED: coordinatedHTTPFlood @ 10.0.0.1_443
  Omega(S) = 26.8 >= tau=5.0   (|S|=8)
  DERIVATION:
    relatedByTLSFingerprint        10 pairs x 1.0 = 10.0
    relatedByEndpointConvergence   28 pairs x 0.6 = 16.8
  verdict = the derivation above, not a score
```

## The rule evaluated AS a detector

Every detection number elsewhere in the paper comes from a classifier over
features, which measures the **representation** and says nothing about this layer.
Sprint 6 evaluated the rule end to end: the sessions matching the derived scope
**are** the flagged set, with no training and no threshold. To be fair, the
classifier was forced onto the **same operating point**:

| Scenario | Rule: recall / FPR / F₁ | RF AUC | RF recall @ FPR = 0 |
|---|---|---|---|
| Monolithic (M = 1) | 84.0% / 0.00% / 0.885 | 0.997 | **91.7%** |
| M = 5 | 90.0% / 0.00% / 0.948 | 0.996 | 88.6% |
| M = 25 | 90.3% / 0.00% / **0.949** | 0.979 | **36.4%** |
| M = 100 | 85.0% / 0.00% / 0.919 | 0.961 | **17.6%** |
| M = 25, adversarial | 30.4% / 3.78% / 0.452 | 0.862 | **7.8%** |

**This is not a uniform win.** In the monolithic regime the Random Forest ties or
beats the rule; there is no symbolic advantage there. From 25 stacks on the
ordering reverses. What AUC hides is exactly this: 0.979 corresponds to recovering
**a third** of the attack at zero false positives, because the score distribution
overlaps benign traffic in the tail. The rule produces no score to threshold; it
produces a set defined by an enrichment test against an explicit background, so
its zero FPR follows **from the criterion, not from tuning**.

The adversarial row is **not** a like-for-like comparison and no claim is made
from it: there the rule itself incurs 3.78% FPR.

See
[`../sprint-6-noms/scripts/symbolic_detector.py`](../sprint-6-noms/scripts/symbolic_detector.py).

## How it composes with Pillar 4

The cluster (sessions on the same endpoint) includes benign users, so endpoint
convergence alone does not discriminate. The high-weight signal, TLS, is what
[Pillar 4](../pillar4-evidence-mitigation/) uses to derive the scope and separate
attackers from legitimate users.

Full flow: **detection (G3/G4) → symbolic reasoning (Pillar 2, here) → evidence
and mitigation (Pillar 4)**.

## Caveats

- The demo runs on a toy graph; running over the real KG needs the drive.
- The SWRL step executes as SPARQL CONSTRUCT, equivalent for Horn rules. A formal
  SWRL/OWL reasoner (owlready2 + Pellet) would require Java and would not change
  the semantics.
- Temporal and payload sub-relations are omitted, having no session-level data.
- The cluster here is "same endpoint"; refining the definition of S is open work.
