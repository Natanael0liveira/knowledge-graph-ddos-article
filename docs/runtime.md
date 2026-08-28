# Runtime

How the knowledge graph is built and evaluated while traffic flows. The
distinction that organizes everything here is that the system runs **two layers
at two different rates**, with different complexity and different purposes, and
keeping them separate is what makes the approach deployable.

| | Layer 1 — admission | Layer 2 — symbolic evaluation |
|---|---|---|
| Runs | per request / per new session | once per operational window |
| Path | hot path, in-memory, indexed | auditable path, RDF + SPARQL |
| Produces | `relatedBy_*` candidate edges | Ω(S), the verdict and its derivation |
| Measured cost | 14–19 ns per candidate pair | ~187 µs per materialized RDF edge |
| Grows with | \|S_W\| (linear) | pairs in the fired cluster (quadratic) |

Layer 1 decides *what is related*. Layer 2 decides *whether that adds up to a
coordinated campaign*, and leaves behind the derivation that justifies the
answer. Only clusters that fire ever reach Layer 2.

## The operational window

Sessions and relations live inside a **sliding window**, `W = 5 min` by default,
and are purged incrementally as they age out, following an RDF
stream-processing discipline. Nothing is retained across windows except the
background traffic profile the enrichment test needs (see
[`concepts.md`](concepts.md)).

The window is not a tuning knob for detection quality. Sweeping it over a 30×
range (60 s to 1800 s) moves AUC by less than 0.002, while mean cluster occupancy
grows 6.6× and the quadratic term of Layer 2 grows with it. The reason is that
the discriminative feature is a **fraction** — the share of the cluster carrying
one JA4 — which is invariant to cluster scale.

> **Operational rule: keep W as small as the traffic permits.** A larger window
> buys no detection and costs roughly the square. W must only be large enough for
> a cluster to form, which at W = 60 s already meant ~132 sessions in the
> evaluated scenarios.

Full sweep in
[`../experiments/sprint-6-noms/`](../experiments/sprint-6-noms/#3-window-sweep).

## Layer 1 — admission

Admitting a new session into a window holding `|S_W|` active sessions costs
**O(|S_W| · c)**: the new session is tested against the sessions already in the
window, and `c` is the per-pair cost of deciding every sub-relation. What grows
with traffic is the number of *candidates*, not the cost of each decision.

Candidates are not drawn by scanning the window. Inverted indexes — a JA4
bucket, an endpoint bucket, a /24 bucket — narrow the comparison set before any
per-pair work happens. This is the difference between a hot path that costs
microseconds and one that costs milliseconds.

### Per-pair decision procedures

Each sub-relation is instantiated independently from its own evidence, so a pair
may end up linked by one, several or all six. `c` is amortized O(1) for every
sub-relation **except the temporal one**.

| Sub-relation | Decision | Cost |
|---|---|---|
| `relatedByTLSFingerprint` | Exact JA4 equality; failing that, near variants — same transport/TLS-version/ALPN prefix, at most one symbol of difference in the ordered cipher or extension blocks, annotated `ja4_distance = 1` | O(1) |
| `relatedByReusedIdentity` | Non-empty overlap of the identity sets (cookies ∪ tokens ∪ usernames); JWTs decoded and compared by the `sub` claim; cookies and usernames normalized | O(1) amortized, inverted index |
| `relatedByTemporalPattern` | Normalized DTW over inter-arrival sequences, `d_DTW ≤ τ_DTW`; sessions with fewer than three requests skipped | **O(n)** — see below |
| `relatedByPayloadSignature` | Cosine similarity over (mean body size, sd body size, hash of dominant User-Agent, hash of Content-Type) above `τ_payload` | O(1), precomputed vectors |
| `relatedByEndpointConvergence` | Same endpoint under path-pattern normalization (`/api/users/12345` → `/api/users/{id}`); exact-path match additionally annotates `exact = true` | O(1), prefix-tree index |
| `relatedByNetworkProximity` | Shared IPv4 /24 (or IPv6 /48) prefix, or shared ASN, or both; both holding annotates `strong = true`; ASN resolution from current BGP tables | O(1), inverted prefix index |

The **temporal** relation is the only one that is not constant-time per pair.
Two mitigations keep it tractable: FastDTW under a constant-width Sakoe–Chiba
band reduces the per-pair cost from O(n²) to O(n), and locality-sensitive hashing
over summary vectors (δ̄, σ_δ, δ_min, δ_max, entropy) avoids all-pairs
comparison in the first place.

The near-variant matching on JA4 deserves a note: it absorbs version drift within
one client library without admitting spurious matches across genuinely distinct
TLS stacks. Exact-only matching would fragment a single botnet stack across minor
version changes; unbounded fuzzy matching would merge unrelated ones.

### Measured cost

Three repeats, one core, `rdflib` reference implementation:

| \|S_W\| | admission p50 | edges/adm | ns/pair | sessions/s |
|---|---|---|---|---|
| 100 | 2.1 µs | 148 | 14.3 | 470,578 |
| 500 | 6.1 µs | 396 | 15.3 | 164,950 |
| 1,000 | 11.9 µs | 741 | 16.0 | 84,207 |
| 5,000 | 61.7 µs | 3,373 | 18.3 | 16,205 |
| 10,000 | 122.1 µs | 6,495 | 18.8 | 8,188 |

**Per-pair cost is flat at 14–19 ns across a 100× range of window occupancy**,
which is the empirical confirmation that `c` is genuinely O(1). Admission
latency grows because the candidate count grows, exactly as O(|S_W| · c)
predicts.

## Layer 2 — symbolic evaluation

Once per window, the edges materialize in RDF via SPARQL `CONSTRUCT` and the
weighted aggregation runs:

> **Ω(S) = Σᵢ wᵢ · |Eᵢ(S)|**

summed over the sub-relations, where `Eᵢ(S)` is the set of unordered session
pairs in S linked by sub-relation *i*. The rule fires when Ω(S) clears
`τ_cluster` and the remaining conditions hold (same endpoint, aggregate rate,
coherent `BotBehavior` profile). Calibration of `τ_cluster` and the weights is in
[`concepts.md`](concepts.md).

The split between the two languages is forced, not stylistic: **SWRL is Horn and
cannot aggregate**, so it instantiates the sub-relations one pair at a time,
while the summation and the comparison against `τ_cluster` are expressed in
SPARQL, which reads the weights from the ontology itself. See
[`../experiments/pillar2-symbolic-reasoning/`](../experiments/pillar2-symbolic-reasoning/).

### Measured cost, and where the quadratic term comes from

| \|S_W\| | symbolic total | RDF edges | µs/edge |
|---|---|---|---|
| 100 | 0.56 s | 2,703 | 208 |
| 250 | 3.10 s | 17,221 | 180 |
| 500 | 12.09 s | 65,115 | 186 |
| 1,000 | 49.69 s | 265,328 | 187 |

Cost per materialized edge is flat at ~187 µs, so this layer is also linear **in
its own unit of work**. What explodes is the edge count: 2,703 edges at 100
sessions, 265,328 at 1,000.

That quadratic growth belongs to **neither the implementation nor the backend**.
Ω(S) is defined over *pairs*, so the number of edges grows with the square of
|S_W| by construction. This is what makes the window a structural necessity
rather than a convenience, and what forces the design consequence below.

> **Design consequence.** Detect on the indexed path (microseconds) and
> materialize RDF only for the clusters that actually fire — which is exactly the
> evidence-chain subset. Running Layer 2 over every window unconditionally is not
> viable and was never the intent.

## Backends

Materialization in production is declared over **Apache Jena Fuseki with TDB2**
storage. The latency numbers above were measured on **`rdflib`**, the in-memory
reference implementation, so the Layer-2 figures are an upper bound of the
reference implementation and are reported as such, not as Fuseki numbers.

The reasoning profile is **OWL 2 RL**, whose materialization is polynomial. That
is what makes bounded materialization tractable at runtime where OWL 2 DL would
not be.

## Where to look in the code

| Concern | Location |
|---|---|
| Latency benchmark, both layers | [`../experiments/sprint-6-noms/scripts/bench_latency.py`](../experiments/sprint-6-noms/scripts/bench_latency.py) |
| Window sweep | [`../experiments/sprint-6-noms/scripts/window_sweep.py`](../experiments/sprint-6-noms/scripts/window_sweep.py) |
| Ω(S) aggregation and verdict | [`../experiments/pillar2-symbolic-reasoning/scripts/reason.py`](../experiments/pillar2-symbolic-reasoning/scripts/reason.py) |
| SWRL sub-relation rules | [`../experiments/pillar2-symbolic-reasoning/rules/relatedBy.swrl`](../experiments/pillar2-symbolic-reasoning/rules/relatedBy.swrl) |
| SPARQL detection query | [`../experiments/sprint-1/queries/coordinatedHTTPFlood.rq`](../experiments/sprint-1/queries/coordinatedHTTPFlood.rq) |
| Ontology (classes, weights) | [`../ontology/ddos_ontology.owl`](../ontology/ddos_ontology.owl) |
