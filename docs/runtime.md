# Runtime

How the method runs on traffic: the windows and the state it keeps, the count query the
evaluation runs, and what a live deployment would add. The formulas themselves (Ω, the gates, the
enrichment test, calibration) are defined in [`concepts.md`](concepts.md). The cost tables come
from [`latency_summary.json`](../experiments/sprint-6-noms/results/latency_summary.json) (paper,
App. D and Fig. 4).

## 1. Windows and state

The paper decides per endpoint and per fixed five-minute window (W = 300 s), so each endpoint has
288 windows a day. Classes count distinct origins, that is, source addresses. The gate's n counts
each address once per fingerprint it presents. On production it also counts plain-HTTP clients
(III-B, App. A).

On generated traffic, the scopes of Table III read the alarm's cluster instead. The cluster chains
the sessions of one endpoint while consecutive starts stay within 300 s of one another (IV-A).
Appendix E runs the rule per fixed window, as a deployment would.

Calibration on attack-free days leaves a small state per endpoint. Nothing else carries over from
one window to the next.

| State | What it holds | Paper |
|---|---|---|
| Profile | b(f), the share of fingerprint f among the N pooled origin–fingerprint pairs, plus 1/N | III-C |
| τ_cluster | 99th percentile of Ω over the calibration windows (base rule) | III-B |
| Gate threshold | 99th percentile of the distinct origins n; the gate also needs n ≥ k_min = 5 | III-B |
| λ_e | the test's level: the largest value up to 0.01 that keeps the 1% budget | III-C |
| z threshold | 99th percentile of each window's largest z, never below 3 | III-C |
| Known fleets | fingerprints selected at level 0.01 in at least 5% of calibration windows | III-D |
| φ(f) | within-window correlation of each profile fingerprint, clipped to [0, 0.99] (beta-binomial, post hoc) | III-D |
| Hourly medians | median n at each hour of the calibration days, and the 99th percentile of the ratio (seasonal gate, post hoc) | V-C |

Under cross-fitting (post hoc), λ_e, the z threshold and the known fleets are fitted with each
calibration day judged against a profile of the other days (IV-B).

A deployment could keep a sliding window and purge sessions as they age out. That design is not
evaluated. The paper does not tune W either. A sweep from 60 s to 1,800 s kept the per-session AUC
of configuration (d) at 0.976–0.978
([`window_sweep.json`](../experiments/sprint-6-noms/results/window_sweep.json)). It ran on the
superseded sprint-4 scenario cache, where the generator packs benign starts early, so W never
operated (sprint-6 lab notebook, [§3](../experiments/sprint-6-noms/README.md#3-window-sweep) and
[§6](../experiments/sprint-6-noms/README.md#6-the-rule-as-a-detector)).

## 2. The evaluated path: a count query compiled from the ontology

No reasoner runs in the evaluation (III-E). The trigger and the scope read class sizes, and a
log-store query compiled from the ontology returns them. The production trigger is the
distinct-origin gate. The base rule, Ω(S) ≥ τ_cluster on one endpoint's window, is the reference of
the held-out protocol (III-B).

1. The three relations the paper uses are equalities: a shared JA4, endpoint or /24 prefix. Each
   one partitions a window's sessions into classes.
2. The ontology annotates each of them with the session property it compares (`kg:classKey`:
   `tlsJa4`, `targets`, `srcPrefix`) and with its weight (`kg:coordinationWeight`). It annotates
   `relatedTo` with the unit classes are counted in (`kg:countUnit`: `originatesFrom`), so the
   sessions of one client count once.
3. [`compile_counts.py`](../experiments/sprint-6-noms/scripts/compile_counts.py) reads these
   annotations and a binding that maps each property to a column of the log table
   ([`bindings/`](../experiments/sprint-6-noms/bindings/), with placeholder names). It emits SQL
   that returns, per window and endpoint, the distinct origins and Ω(S). Per window, endpoint and
   class value, it returns the class size in distinct origins, which the scope tests.
4. Sub-properties without a class key need pairwise evaluation. The compiler lists them and
   compiles nothing for them.

A new equality signal costs four triples, plus a column binding if it reads a new session property.
The query-generation code does not change. `make compile-check` tests both points without data. On
generated sessions, the compiled query run in DuckDB matches `decompose_omega(unit="origin")`. A
fourth equality relation, added as four triples with no code line changed, then enters the
recompiled query ([`compile_check.json`](../experiments/sprint-6-noms/results/compile_check.json)).

In the operator's log store, the compiled query reproduced the exported address and /24-pair counts
in every window of two production days, 1,152 windows each. It reproduced the JA4 pair counts in
the 288 windows of each day on the endpoint where the WAF blocked no client. Elsewhere the export
drops clients the WAF partly blocked, and the compiled query keeps them. Pair counts constrain the
per-fingerprint counts the scope tests. They do not identify them (App. F;
[`compile_production_check.json`](../experiments/sprint-6-noms/results/compile_production_check.json),
[`compile_production_check_fresh.json`](../experiments/sprint-6-noms/results/compile_production_check_fresh.json)).
The evaluation itself reads the exports.

On the exports, Ω takes the form

> Ω = 1.0 · Σ_f C(n_f, 2) + 0.6 · C(n, 2) + 0.3 · P₂₄

where n_f counts the origins presenting fingerprint f, n the window's origins as the gate counts
them, and P₂₄ the exported pairs of distinct origins that share a /24 (a /48 in IPv6). The weights
are read from the ontology.

Only windows that fire produce an evidence chain: the rule, the cluster, the scope and the split of
Ω(S) by sub-relation. It is exported as JSON-LD (Listing 1) and STIX 2.1 (III-E).

## 3. Two layers in a deployment

The production run is offline, over exported counts per endpoint (App. C). A live deployment would
run two layers at two rates, and Appendix D times them apart.

| | Layer 1: admission | Layer 2: aggregation |
|---|---|---|
| Runs | per request or new session | once per window |
| Updates | one class counter per equality sub-relation | class membership, then Ω(S) per endpoint |
| Feeds | the class sizes of the open window | the trigger, the scope and, when they fire, the evidence chain |
| Cost with class counts | 0.33–0.42 µs per admission | linear in sessions |
| Cost with pair edges | 15–21 ns per candidate pair | about 200 µs per RDF edge |

The rule reads one endpoint per S, so partitioning by endpoint evaluates it exactly, with no traffic
between shards. A campaign that spreads one JA4 across many endpoints then has too few pairs in any
shard. Catching it would need a global sketch, which is not implemented (App. D). The partitioning
itself is not implemented either (App. C).

## 4. Class counting and pair edges

For an equality sub-relation, the pairs it links follow from the class sizes alone. Their number,
the size of Eᵢ(S), is Σₖ C(nₖ, 2) over the classes, with each nₖ counted in distinct origins
(App. A). Admitting a session then means incrementing one counter per sub-relation. The cost does
not depend on the window size |S_W|, and no pair is enumerated.

A relation that is not transitive still compares the new session with candidates. Inverted indexes
and locality-sensitive hashing narrow that set before any per-pair work. The cost per pair then
stays constant, and the candidate count is what grows.

Appendix A specifies six sub-relations. The paper exercises three, with weights 1.0, 0.6 and 0.3.
The other procedures below are design specifications: no script runs them, and their weights are
untested (App. C).

| Sub-relation | Exercised in the paper | Specified only (App. A) | Cost per pair in the design |
|---|---|---|---|
| `relatedByTLSFingerprint` | exact JA4 equality, as class counts | a near variant, `ja4_distance = 1`, which is not transitive | O(1) |
| `relatedByEndpointConvergence` | same endpoint: a host, or an address and port | path-pattern normalization (`/api/users/12345` → `/api/users/{id}`) | O(1), prefix-tree index |
| `relatedByNetworkProximity` | shared IPv4 /24 or IPv6 /48 | a shared ASN, resolved from current BGP tables | O(1), inverted prefix index |
| `relatedByReusedIdentity` | none | overlapping identity sets (cookies, tokens, usernames; JWTs compared by their `sub` claim), which is not transitive | O(1) amortized, inverted index |
| `relatedByTemporalPattern` | none | normalized DTW over inter-arrival sequences, d ≤ τ_DTW; sessions with fewer than three requests skipped | O(n), see below |
| `relatedByPayloadSignature` | none | cosine similarity above τ_payload over the mean and standard deviation of body size and hashes of the dominant User-Agent and Content-Type | O(1), precomputed vectors |

The temporal relation is the only one whose cost per pair is not constant. FastDTW under a
constant-width Sakoe–Chiba band cuts that cost from O(n²) to O(n). Locality-sensitive hashing over
summary vectors (mean, standard deviation, minimum and maximum of the inter-arrival times, and
their entropy) avoids comparing all pairs.

The near variant would absorb version drift within one TLS library. Exact matching splits one
botnet stack across minor version changes, and unbounded fuzzy matching would merge unrelated
stacks. The near variant is not an equivalence, so it would need pair edges.

## 5. Measured cost

Appendix D times both layers on a synthetic window: 30% of sessions in one campaign that shares a
botnet JA4, benign JA4 from a pool of 2,000, nine endpoints and dispersed /24s. Admission fills a
window of |S_W| sessions, then times 200 further sessions. Each value is a median of three repeats
on one core. Layer 2 runs on `rdflib`, the in-memory reference implementation. The benchmark counts
sessions, one node each. The pair-edge path is skipped above an estimated 3,000,000 pairs.
`make latency` reruns it without data, and the
[lab notebook §1](../experiments/sprint-6-noms/README.md#1-latency) records the run conditions.

**Admission, per request.** "Pair path" enumerates the peers already in the window, as the rules
are written. "Class counters" is the path of section 4.

| \|S_W\| | pair path, p50 | candidate pairs per admission | ns per pair | class counters, p50 |
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
| 100,000 | 1,364.6 µs | 65,020 | 21.0 | 0.38 µs |

**Aggregation, per window.** "Pair edges" materializes every pair in RDF, then sums Ω(S). "Class
aggregation" stores one membership triple per session and sub-relation, and one SPARQL query sums
the weighted class counts.

| \|S_W\| | pair edges, total | RDF edges | µs per edge | class aggregation, total |
|---|---|---|---|---|
| 100 | 0.84 s | 2,703 | 309 | 0.07 s |
| 250 | 3.67 s | 17,221 | 213 | 0.09 s |
| 500 | 12.89 s | 65,115 | 198 | 0.16 s |
| 1,000 | 52.78 s | 265,328 | 199 | 0.33 s |
| 2,500 | 357.76 s | 1,641,169 | 218 | 0.81 s |
| 5,000 | skipped | | | 1.38 s |
| 10,000 | skipped | | | 2.86 s |
| 25,000 | skipped | | | 6.77 s |
| 50,000 | skipped | | | 13.22 s |
| 100,000 | skipped | | | 26.37 s |

What the tables show:

- Class admission stays at 0.33–0.42 µs from 100 to 100,000 sessions.
- The pair path costs 15–21 ns per candidate pair. Its growth comes from the candidate count.
- Pair edges cost about 200 µs each (309 µs at 100 sessions), and their number grows with the
  square of |S_W|: 52.8 s at 1,000 sessions and 358 s at 2,500.
- Class aggregation is linear: 0.33 s at 1,000 sessions, 161 times faster, and 26.4 s at 100,000.
- Both paths give the same Ω(S) for every endpoint, to within 7.3 × 10⁻¹² (the paper rounds this to
  10⁻¹¹).

The quadratic term therefore lies in the value of Ω(S), which counts pairs, and in the pair edges of
the relations that are not transitive. Earlier versions of this page and of the paper put it in the
rule itself, and the [lab notebook §1](../experiments/sprint-6-noms/README.md#1-latency) records
the correction.

## 6. Backends and reasoning profile (design intent)

**Store.** The design targets Apache Jena (Fuseki with TDB2), where the sprint-1 laboratory
pipeline loads its graphs. The cost numbers come from `rdflib`, the in-memory reference
implementation, so the Layer-2 figures are likely an upper bound (App. D).

**Languages.** SWRL is Horn and cannot aggregate. In the design, SWRL defines the sub-relations one
pair at a time, and SPARQL sums Ω(S) and compares it with τ_cluster, reading the weights from the
ontology. For the equality sub-relations, the SPARQL query counts pairs from class membership
(`kg:inClass`, `kg:ofRelation`), so no pair edge is materialized. The paper prints no query: its
Listing 1 is the evidence chain (App. D). `bench_latency.py` times this aggregation, and
[`pillar2-symbolic-reasoning/`](../experiments/pillar2-symbolic-reasoning/) runs the pairwise form
on a toy graph.

**Profile.** OWL 2 RL is the target for a deployment that materializes inferences, because its
materialization takes polynomial time, unlike reasoning in OWL 2 DL. This is design intent. No
reasoner runs in the evaluation (III-E), and no script in the repository calls one.

## 7. Where to look in the code

| Concern | Location |
|---|---|
| Sub-relations, weights, class keys and count unit | [`ontology/ddos_ontology.owl`](../ontology/ddos_ontology.owl) |
| The ontology values every script reads | [`experiments/common/kg_ontology.py`](../experiments/common/kg_ontology.py) |
| Count query compiled from the ontology; `make compile-check` | [`compile_counts.py`](../experiments/sprint-6-noms/scripts/compile_counts.py) |
| Binding template, with placeholder table and column names | [`experiments/sprint-6-noms/bindings/`](../experiments/sprint-6-noms/bindings/) |
| Ω, calibration and scopes per production window: the test (`adjusted_p`, `log_tail`), known fleets (`known_fleets`), the beta-binomial's φ (`intra_window_correlation`), the z threshold (`calibrate_baselines`), cross-fitting (`--split crossfit`) | [`rule_detection_production.py`](../experiments/sprint-6-noms/scripts/rule_detection_production.py) |
| Gates (τ_cluster, distinct origins, seasonal), the metrics (`clopper_pearson`, `cluster_ci`, `joint_expected`), the floor (`floor`) and its ramp (`model_new`) | [`production_tables.py`](../experiments/sprint-6-noms/scripts/production_tables.py) |
| Floors by popularity band, and the enrichment limit | [`floor_bands.py`](../experiments/sprint-6-noms/scripts/floor_bands.py) |
| Matched, drifted, flat and pooled profiles on generated traffic (V-A) | [`profile_drift.py`](../experiments/sprint-6-noms/scripts/profile_drift.py) |
| Ω per fixed window on generated traffic (App. E) | [`rule_detection.py`](../experiments/sprint-6-noms/scripts/rule_detection.py) |
| Ω per chained cluster, laboratory and generated traffic | [`experiments/sprint-1/scripts/compute_coordination.py`](../experiments/sprint-1/scripts/compute_coordination.py) |
| Ω split by sub-relation (`decompose_omega`); the modal scope (`derive_scope`), the binomial test (`derive_scope_enriched`) and its level (`calibrate_level`) on generated traffic; the evidence chain as JSON-LD and STIX 2.1 | [`evidence_mitigation.py`](../experiments/pillar4-evidence-mitigation/scripts/evidence_mitigation.py) |
| Listing 1, the evidence chain of the default campaign | [`example_chain.py`](../experiments/sprint-6-noms/scripts/example_chain.py) |
| Cost model, both layers; `make latency` | [`bench_latency.py`](../experiments/sprint-6-noms/scripts/bench_latency.py) |
| Pairwise SWRL rules and their SPARQL form, on a toy graph | [`relatedBy.swrl`](../experiments/pillar2-symbolic-reasoning/rules/relatedBy.swrl), [`reason.py`](../experiments/pillar2-symbolic-reasoning/scripts/reason.py) |
| Legacy gate G4 of the sprint-1 laboratory pipeline | [`coordinatedHTTPFlood.rq`](../experiments/sprint-1/queries/coordinatedHTTPFlood.rq) |
| Window sweep (not in the paper) | [`window_sweep.py`](../experiments/sprint-6-noms/scripts/window_sweep.py) |
