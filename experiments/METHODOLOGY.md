# Methodology and decisions

Why each stage is built the way it is, what its numbers represent, and which
caveats travel with them. Results and scenarios are in
[`../docs/evaluation.md`](../docs/evaluation.md); real-capture outcomes are in
[`FINDINGS.md`](FINDINGS.md).

---

## Principles that cut across every stage

**Scientific honesty over a good-looking number.** Limitations are reported, not
buried: scoped mitigation does not manifest on CIC captures, the KLAGE comparison
is not controlled, and weight calibration corroborates the *ordering* rather than
the absolute values. A defensible result is worth more than a high one, because
it is what survives a sceptical reviewer.

**Reproducibility by construction.** Fixed seeds, a Makefile per stage, logs,
versioned artifacts. Any stage reruns with one command and yields the same
number.

**The stealth realization.** The most important methodological finding: against
an attack with an obvious flow signature, per-session detection already suffices,
so the thesis is only genuinely tested when the attack is *stealthy*, meaning
per-session indistinguishable from benign. That insight reoriented the whole
evaluation onto the stealthy distributed regime.

---

## Sprint 1 — Extraction pipeline and knowledge graph

Turns raw captures into graph instances: PCAP → JA4 and flows → sessions →
graph, loaded into Apache Jena Fuseki with TDB2.

Validation runs as gates G1–G4 in `validate.ipynb`. G3 and G4 cover coordination:
G3 checks that the coordination-only signal separates, G4 that clusters form as
expected. Both were exercised on CICIDS2017 and CIC-IoT2023.

Large KGs load through the bulk path (`make load-kg-bulk`); the naive per-triple
HTTP path does not finish on graphs of this size.

## Sprint 2 — Calibrated synthetic generator

Produces distributed Slow HTTP DoS campaigns with known coordination ground
truth. Legitimate distributions are fitted to CICIDS2017 and verified by
Kolmogorov–Smirnov tests, so the gain cannot come from artificially easy benign
traffic. Stealth mode draws attacker sessions from the same per-session
distributions as benign traffic.

The two realism parameters, benign fingerprint popularity (Zipf α) and botnet
composition (M TLS stacks), are calibrated rather than assumed. See
[`../docs/evaluation.md`](../docs/evaluation.md).

## Sprint 3 — Baselines and ablation

To show the gain comes from **structure between sessions** rather than from more
features or a better classifier, four configurations run over the same input and
the same classifier, varying only the feature set:

| | Configuration |
|---|---|
| (a) | Per-session flow features only. A **strong** baseline: all 8–9 flow attributes, not a lean 3-feature strawman |
| (b) | Ontology, but with no `relatedBy_*` relation; sessions as isolated nodes |
| (c) | `relatedByNetworkProximity` only, the low-weight network signal |
| (d) | Full weighted `relatedBy_*` family |

Three academic baselines (Fernandes, Bharathi, Kemp) run alongside as external
reference.

**Anti-circularity decision, and it is critical.** Detection clusters are formed
**label-agnostically**, by endpoint and window, never using the label. Forming
them any other way would make the result trivially circular.

**Why only three sub-relations.** Of the six in the family, only three have
session-level data in these datasets: TLSFingerprint (JA4), EndpointConvergence
and NetworkProximity. The other three, ReusedIdentity (cookie or token),
TemporalPattern (per-request cadence) and PayloadSignature (user agent,
content-type), would require instrumentation the captures lack. We use only the
three that compute exactly instead of approximating the rest, which would add
noise and drift from the paper's definitions. This applies to both Ω(S) and the
features of (c) and (d), and it is declared as a limitation.

**What the numbers mean.** ROC AUC per configuration isolates contributions:
(a)→(d) is the total contribution, (b)→(d) the gain of representing cross-session
structure at all, (c)→(d) the specific gain of high-weight signals over network
proximity.

## Sprint 4 — Statistical run

n = 30 seeds per configuration, paired Wilcoxon tests with Bonferroni correction,
Cohen's *d* and matched-pairs rank-biserial correlation. Effect sizes of the
magnitude observed reflect the near-perfect separation of controlled synthetic
traffic and should not be read as an expectation of field performance.

Weight calibration maximizes per-session attack-vs-benign ROC AUC over a grid of
weight vectors. It corroborates the proposed **ordering** (TLS-dominant); in the
pure same-service regime the medium and low weights are not separately
identifiable, since in isolation both sit near chance.

## Sprint 5 — Comparison with KLAGE

Runs CIC-IoT2023 through the same pipeline and compares against KLAGE's published
F₁ = 84.1% for DDoS Slowloris.

The comparison is favourable but **uncontrolled**, and the paper says so: our
0.911 beats 0.841, but so does our own strong per-session baseline at 0.900, so
the margin cannot be attributed to the cross-session representation. A controlled
rerun is not currently possible, because the released code starts from a
pre-built graph whose construction is unpublished and ships no weights.

## Sprint 6 — Additions for the NOMS submission

The realistic same-service scenario that became canonical (legitimate users on
the attacked service, same port, so neither volume nor destination port
separates), the cost model and window sweep, and the profile-drift experiment
that quantifies how much background-profile staleness the enrichment test
tolerates.

## Pillar 2 — Symbolic reasoning

The rule evaluated **as a detector**, with no model training and no learned score
threshold: the sessions matching the derived scope *are* the flagged set. Since
AUC is a ranking measure and the rule emits a hard decision, the classifier is
forced onto the rule's own operating point for comparison.

Pair-wise materialization of the `relatedBy` family is expressed as SWRL rules.
Relations over categorical attributes are pure Horn; numeric ones such as DTW
distance and payload cosine similarity are precomputed and the rule performs the
comparison against a threshold. Aggregation is not Horn at all, so Ω(S) is
computed by a SPARQL query whose weights are read from the `coordinationWeight`
annotations in the ontology rather than hard-coded.

## Pillar 4 — Evidence chain and scoped mitigation

Both scope derivations ship side by side, the frequency rule that fails and the
enrichment rule that replaces it, so the negative result is reproducible rather
than asserted. The background profile the enrichment test needs comes from an
attack-free generator run, so no labels enter the decision path at any point.

## Validity hardening

A sceptical self-audit that changed several conclusions:

- An early apparent advantage on real data turned out to be an artifact of a
  3-feature baseline. A fair 8-feature model reaches 0.98–1.0 on those captures.
  The fix was not to weaken the baseline but to enrich the generator, after which
  stealth survives the strong baseline.
- Deriving the mitigation scope from the modal property of the whole cluster is
  actively harmful once the botnet spans several stacks. That finding became a
  reported result rather than a bug to hide.
- Randomizing JA4 collapses the framework, and endpoint convergence does not
  compensate, because legitimate users converge on the endpoint too.
