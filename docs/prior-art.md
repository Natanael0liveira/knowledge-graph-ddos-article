# Prior art and novelty

Why each component of the contribution is defensible, and where it is not.
Distilled from a prior-art sweep run in May 2026 and revised after reading KLAGE
in full. These are the axes that became the columns of Table I in the paper.

---

## The insight that motivated the sweep

> Without this contribution, the attack is mitigated at the configuration's
> global threshold: no benefit from the relation between sessions, and legitimate
> traffic is hit.

The question was whether *deriving the mitigation scope from the evidence chain*
had already been done, in academia or in industry.

## Verdict by component

| Component | Prior art? | Where | How the paper positions it |
|---|---|---|---|
| HTTP session as a first-class OWL entity | **Not found** in peer-reviewed work | KLAGE models the network node, not the HTTP session | Defensible as the primary contribution |
| Runtime KG construction for detection | **Close neighbour** | KLAGE (FGCS 2026) builds a KG from logs and detects Slowloris | Reposition: ours is session-level, not node-level |
| Cross-session reasoning by identity / JA4 / prefix | **Industry, and implicit in KLAGE** | Cloudflare, DataDome, Castle, Auth0; KLAGE captures coordination in embeddings without naming it | Claim the first auditable, reproducible academic formalization of what products do in a black box |
| Explicit symbolic rules in SPARQL/SWRL over a traffic KG | **Neighbour** | KnowGraph (CCS '24, weighted FOL); KLAGE (Graph-BERT + LIME) | Differentiate: ours is OWL-native, the verdict *is* the derivation |
| Evidence chain in STIX 2.1 / JSON-LD from the fired rule | **Standard exists**; textual in KLAGE | OASIS STIX 2.1; KLAGE generates natural language via LLM | Derivation exported without a translation step |
| **Automatic derivation of `mitigatedBy` scope from the cluster discriminator** | **Not found** in academia | AWS scope-down statements exist but are discouraged for lack of a metric | Defensible, and the paper's operational core |
| **Academic collateral-damage metric for L7 DDoS** | **Not found** systematically | Vendors self-report (DataDome FPR < 0.01%); KLAGE reports only Acc/Prec/Rec/F1 | Defensible as a methodological contribution |

## What changed after reading KLAGE in full

KLAGE builds knowledge graphs from network logs, classifies nodes with
Graph-BERT, and produces natural-language reports via LIME and LLMs, reaching
F₁ = 84.1% on IoT benchmarks including DDoS Slowloris. It is solid evidence that
knowledge graphs are a viable runtime detection substrate, and it rules out any
claim of being "the first framework" to do so.

What survives is a contribution differentiated on four axes:

1. **Reasoning unit.** KLAGE models the traffic graph at the level of the
   **network node** (port, IP, flow). This work models the **HTTP session** as a
   first-class ontological entity with identity, target, behaviour and typed
   relations.
2. **Semantic representation.** KLAGE uses Graph-BERT embeddings and LIME, a
   post-hoc explanation of a classifier. This work is symbolic: the rule fires and
   the derivation is the verdict, with no explanation step after the fact.
3. **Derived mitigation scope.** KLAGE ends at a report and does not address
   mitigation. This work couples detection, evidence chain and automatic scope
   derivation in one pass over the same graph.
4. **Methodology.** KLAGE reports Acc/Prec/Rec/F1 and does not measure collateral
   damage on legitimate traffic. That metric remains a methodological
   contribution here.

## Framing rules that follow

- **Never claim "first framework".** KLAGE precedes us on runtime KGs for
  detection. Claim the session as the reasoning unit, the symbolic path, the
  derived scope and the collateral metric.
- **Cross-session reasoning is not new to industry.** State it as the first
  auditable and reproducible academic formalization, not as an invention.
- **The head-to-head with KLAGE is favourable but uncontrolled.** Our 0.911 beats
  the published 0.841, but so does our own strong per-session baseline at 0.900,
  so the margin cannot be attributed to the cross-session representation. The
  paper says this explicitly. A controlled rerun is not currently possible: the
  released code starts from a pre-built graph whose construction is unpublished
  and ships no weights.

## Risks to watch in peer review

- A reviewer asking why a feature-based configuration is called the framework.
  Addressed: configuration (d) is named "cross-session representation" and the
  table notes that the symbolic path is evaluated separately.
- A reviewer asking for the stealthy distributed regime in captured traffic. No
  public benchmark provides it; see [`evaluation.md`](evaluation.md).
- A reviewer noting that the advantage is regime-specific. Stated as the first
  limitation in the paper.
