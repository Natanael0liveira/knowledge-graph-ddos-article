# Runtime

How the knowledge graph is built and evaluated while traffic flows. The
distinction that organizes everything here is that the system runs **two layers
at two different rates**, with different complexity and different purposes, and
keeping them separate is what makes the approach deployable.

| | Layer 1 — admission | Layer 2 — symbolic evaluation |
|---|---|---|
| Runs | per request / per new session | once per operational window |
| Path | hot path, in-memory, indexed | auditable path, RDF + SPARQL |
| Produces | class counts (and candidate pairs for non-transitive relations) | Ω(S), the verdict and its derivation |
| Measured cost, class counting | about 0.4 µs per session, constant | linear in \|S_W\| |
| Measured cost, pair edges | 15–21 ns per candidate pair | about 200 µs per materialized RDF edge |

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
grows 6.6×. The reason is that
the discriminative feature is a **fraction** — the share of the cluster carrying
one JA4 — which is invariant to cluster scale.

> **Operational rule: keep W as small as the traffic permits.** A larger window
> buys no detection and adds state. With class counting that cost is linear in
> the window; with pair edges it was quadratic. W must only be large enough for
> a cluster to form, which at W = 60 s already meant ~132 sessions in the
> evaluated scenarios.

Full sweep in
[`../experiments/sprint-6-noms/`](../experiments/sprint-6-noms/#3-window-sweep).

## Layer 1 — admission

Three of the sub-relations, exact JA4, endpoint and /24 prefix, are
**equivalence relations**: two sessions are related when they share a value. Each
one therefore partitions a cluster S into classes, and the number of pairs it
links follows from the class sizes alone, `|Eᵢ(S)| = Σₖ C(nₖ, 2)`. Admitting a
session means incrementing one counter per such sub-relation. The cost does not
depend on `|S_W|`, and no pair is ever enumerated. This is also how the evaluation
computes Ω (`compute_coordination.py` groups by value and counts).

The non-transitive relations (near-variant JA4, temporal pattern, payload
signature) still compare the new session with candidates. Inverted indexes and
locality-sensitive hashing narrow that comparison set before any per-pair work
happens, so the per-pair cost `c` stays O(1) and the candidate count is what grows.

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

Three repeats, one core, on AC power, with the `rdflib` reference implementation.
"Peers enumerated" is the pair path, as the rules are written; "class counters"
is the path above.

| \|S_W\| | peers enumerated, p50 | edges/adm | ns/pair | class counters, p50 |
|---|---|---|---|---|
| 100 | 2.3 µs | 148 | 15.3 | 0.42 µs |
| 250 | 3.8 µs | 239 | 15.9 | 0.38 µs |
| 500 | 6.7 µs | 396 | 17.0 | 0.38 µs |
| 1,000 | 12.0 µs | 741 | 16.2 | 0.37 µs |
| 2,500 | 31.0 µs | 1,660 | 18.7 | 0.38 µs |
| 5,000 | 64.2 µs | 3,373 | 19.0 | 0.33 µs |
| 10,000 | 126.9 µs | 6,495 | 19.5 | 0.37 µs |
| 25,000 | 293.9 µs | 16,321 | 18.0 | 0.33 µs |
| 50,000 | 608.8 µs | 32,156 | 18.9 | 0.33 µs |
| 100,000 | 1364.6 µs | 65,020 | 21.0 | 0.38 µs |

**Class admission is flat at 0.33–0.42 µs from 100 to 100,000 sessions.** The pair
path is linear in `|S_W|` at a constant 15–21 ns per candidate pair, which confirms
that `c` is O(1) and that the growth comes from the candidate count.

## Layer 2 — symbolic evaluation

Once per window, class membership (and, for the non-transitive relations, pair
edges) materializes in RDF and the weighted aggregation runs:

> **Ω(S) = Σᵢ wᵢ · |Eᵢ(S)|**

summed over the sub-relations, where `Eᵢ(S)` is the set of unordered session
pairs in S linked by sub-relation *i*. The rule fires when Ω(S) clears
`τ_cluster` and the remaining conditions hold (same endpoint, aggregate rate,
coherent `BotBehavior` profile). Calibration of `τ_cluster` and the weights is in
[`concepts.md`](concepts.md).

The split between the two languages is forced by what each can express. **SWRL
is Horn and cannot aggregate**, so it defines the sub-relations one pair at a
time, while the summation and the comparison against `τ_cluster` are written in
SPARQL, which reads the weights from the ontology. For the equality-based
sub-relations the query counts pairs from class membership (`kg:inClass`,
`kg:ofRelation`), so no pair edge is materialized. See Listing 1 of the paper and
[`../experiments/pillar2-symbolic-reasoning/`](../experiments/pillar2-symbolic-reasoning/).

### Measured cost

| \|S_W\| | pair edges: total | RDF edges | per edge | class aggregation: total |
|---|---|---|---|---|
| 100 | 0.84 s | 2,703 | 309 µs | 0.07 s |
| 250 | 3.67 s | 17,221 | 213 µs | 0.09 s |
| 500 | 12.89 s | 65,115 | 198 µs | 0.16 s |
| 1,000 | 52.78 s | 265,328 | 199 µs | 0.33 s |
| 2,500 | 357.76 s | 1,641,169 | 218 µs | 0.81 s |
| 5,000 | not run | |  | 1.38 s |
| 10,000 | not run | |  | 2.86 s |
| 25,000 | not run | |  | 6.77 s |
| 50,000 | not run | |  | 13.22 s |
| 100,000 | not run | |  | 26.37 s |

Both paths give the same Ω(S) for every endpoint, to within 7e-12.

Materializing pair edges costs about 200 µs per edge, so that path is linear in
edges, and the edge count grows with the square of `|S_W|`: 52.8 s at 1,000
sessions and 358 s at 2,500. Class aggregation is linear in sessions: 0.33 s at
1,000, 160 times faster, and 26.4 s at 100,000.

An earlier version of this page, and of the paper, said the quadratic term
belonged to the rule itself and that no backend could remove it. That was wrong
for the equality-based sub-relations. The quadratic growth is real in the *value*
of Ω(S), which counts pairs, and in the pair edges of the non-transitive
relations. Computing Ω from class sizes avoids it, and the evidence chain needs
only the per-relation pair counts, which the classes give directly.

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
