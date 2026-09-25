# Concepts

Conceptual background for the NOMS submission in
[`papers/http-session-noms`](../papers/http-session-noms/). For how the graph is
built and evaluated while traffic flows see [`runtime.md`](runtime.md); for the
experimental design see [`evaluation.md`](evaluation.md); for the metrics the
results are reported in see [`metrics.md`](metrics.md); for the novelty check on
scoped mitigation see [`prior-art.md`](prior-art.md).

---

## 1. The problem

Application-layer DDoS over HTTP reaches three classes of endpoint:

| Endpoint | Example | Typical attack |
|---|---|---|
| Authentication | `/api/auth/login` | login flood, credential stuffing |
| API | `/api/users/{id}` | distributed abuse across a token fleet |
| Expensive processing | `/search?q=...` | HTTP flood against costly routes |

The dangerous variants are *coordinated*: many sessions, often from hundreds or
thousands of origins, hitting one endpoint under common direction. Examined
individually, each request is indistinguishable from a legitimate one. The signal
lives in two layers: the session's own usage pattern (route entropy, fingerprint
consistency, call rhythm) and the structure *between* sessions (how many login
failures across how many identities, how many tokens converge on one endpoint,
which client signature they share).

The meta-analysis of Odusami et al. over 75 studies shows that 47% of
application-layer DDoS methods derive features from sessions, and that in all of
them the session is flattened into a numeric vector before it reaches the
classifier. The detector sees statistics, not sessions, and therefore cannot
reason about reused identities or about patterns that exist only between two
individually normal sessions.

Three deficiencies follow, and they are what this work addresses:

1. The session is a feature aggregate, not an entity.
2. There is no ontological explanation. An analyst decides dozens of times an
   hour, and "looks like an attack" is not a decision.
3. There is no cross-session reasoning, which is exactly what coordinated
   campaigns require.

## 2. Ontology, OWL and knowledge graph

An **ontology** is a formal representation of a domain: classes
(`ApplicationSession`, `Endpoint`, `Identity`), typed relations (`hasIdentity`,
`targets`, `relatedTo`), datatype properties (`requestRate`, `failureRatio`) and
axioms that every valid instance obeys.

| | Relational database | Ontology |
|---|---|---|
| Structure | Fixed tables | Flexible graph |
| Relations | Implicit foreign keys | Named edges |
| Semantics | In the schema | Explicit and formal |
| Inference | Not supported | Automatic (OWL reasoners) |
| Extension | Rigid schema | Subclasses and new relations without restructuring |

**OWL** is the W3C standard for serializing ontologies. A **knowledge graph** is
an ontology instantiated with real data. Here it is populated *at runtime* from
HTTP traffic, not offline from threat-intelligence text.

We work in the **OWL 2 RL** profile. Its forward-chaining entailment is
polynomial, which makes bounded materialization tractable for runtime reasoning
where OWL 2 DL is not. Materialization runs once per operational window, not on
the per-request path.

## 3. Why the session should be an entity

The HTTP session is the natural unit of client behaviour against an application:
it groups requests under one observed identity (cookie, JWT, username, TLS
fingerprint). It is also the object that existing detectors summarize most and
model least.

Flattening a session into `[req_rate, duration, op_count, ...]` discards the
identity that links sessions, the specific endpoint targeted, the observable
ordering of requests, and any possibility of linking sessions that share an
identity or a fingerprint.

Modelled as `ApplicationSession`, the session has identity (a stable IRI within
the window), a target (`targets`), a behaviour (`exhibitsBehavior`), ties to
other sessions (`relatedTo`) and a mitigation (`mitigatedBy`). It stops being a
statistic and becomes something to reason about.

## 4. Cross-session reasoning

Coordinated campaigns have a weak per-session signature and a clear collective
structure:

- Credential stuffing against `/api/auth/login`: each session tries a few
  credential pairs; the set represents millions.
- API abuse across a token fleet: each token respects its quota; the fleet
  degrades the service.
- Distributed HTTP flood: each origin sends few requests per second; the botnet
  sustains a hundred thousand.

### The weighted `relatedTo` family

Cross-session relatedness is not one relation but a structured family, declared
with `rdfs:subPropertyOf` under a transitive `relatedTo` and annotated with a
`coordinationWeight` in [0, 1]. Each sub-property is instantiated independently
from its own evidence, so two sessions may be linked by one, several or all six.

| Sub-property | Weight | Cost to the attacker of breaking it |
|---|---|---|
| `relatedByTLSFingerprint` | 1.0 | High: changing the TLS stack means rewriting infrastructure |
| `relatedByReusedIdentity` | 1.0 | High: pulverizing credentials attacks the campaign's economics |
| `relatedByTemporalPattern` | 0.9 | High: coherence emerges from botnet operation, and jitter only partially breaks it |
| `relatedByPayloadSignature` | 0.6 | Medium: randomizing is cheap but costs campaign coherence |
| `relatedByEndpointConvergence` | 0.6 | Medium: spreading the target dilutes the attack |
| `relatedByNetworkProximity` | 0.3 | Low: proxies and cloud fleets span prefixes and ASNs |

The ordering is an evasion-cost argument, and it is the *ordering*, not the
absolute values, that the calibration corroborates. Network proximity is the
weakest link by construction: Mirai derivatives, cloud fleets and residential
proxies spread across ASNs, and carrier-grade NAT makes a shared /24 a poor
discriminator. It therefore enters as auxiliary evidence, never as a
prerequisite.

**JA4** is the client-identity primitive: a hash of the TLS `ClientHello` that
fingerprints the client's TLS stack rather than its address, and so survives IP
rotation.

### The rule

For a candidate set S of sessions active in the window, the coordination mass is

> Ω(S) = Σᵢ wᵢ · |Eᵢ(S)|

summed over the sub-relations, where Eᵢ(S) is the set of unordered pairs of
distinct **origins** (source addresses) whose sessions in S are linked by
sub-relation *i*. A SPARQL/SWRL rule fires when S spans at least k_min origins,
Ω(S) clears a threshold τ_cluster and every session of S targets the same
endpoint. The derivation that satisfied the rule *is* the verdict; nothing is
explained after the fact.

**What the weights do, and what they do not.** At window scale most of Ω is
volume: under the one-endpoint condition the endpoint term is 0.6·C(n, 2) for n
origins, 91% of Ω in the canonical campaign of Listing 2. With uniform weights the
per-window rule detects as it does with (1.0, 0.6, 0.3), and without the endpoint
term it misses most campaigns while still flagging flash crowds
(`experiments/sprint-6-noms/README.md`, section 9). Ω ≥ τ therefore says that a
window holds more coordination than normal traffic; the enrichment test of
section 6 supplies the discriminator. The weights order the evidence chain, which
reports each sub-relation's share of Ω, and keep network proximity auxiliary.

**The trigger should not read the scope's evidence.** A plain threshold on the
number of distinct origins in the window, calibrated as τ_cluster is (its 99th
percentile over attack-free windows), gates the scope at least as well as Ω ≥ τ on
both generated and production traffic, and on production it halves the false
alarms (0.25% of clean windows to 0.11%) without losing a detection. The reason
is instructive. A legitimate fleet concentrates on one fingerprint, which lifts
Ω's TLS term (Σ_f C(n_f, 2)) exactly in the windows where the enrichment test
names that fleet; the clean windows only Ω admits carry a third of their Ω outside
the endpoint term, against an eighth elsewhere. A trigger that counts fingerprint
sharing is therefore correlated with the scope's failure mode, while a trigger
that counts origins is blind to it. A threshold on the aggregate request rate
adds nothing either: each session of a Slow HTTP campaign keeps a legitimate rate,
so a calibrated rate threshold is an origin count. This is why the rule's former
conditions on rate and on a `BotBehavior` profile were dropped from the paper:
neither was ever active in an experiment.

**Why origins and not sessions.** Sessions stay the nodes of the graph, and the
relations still link sessions; only the aggregation counts each class in
distinct origins. The threat is a botnet of many devices, so coordination is
coordination *across sources*. On production traffic a session is a connection,
and one client opens many: on the busiest API endpoint of the CDN we measured,
5.8 connections per client over eight days. Counted in sessions, one automated client posing
dozens of connections with the same fingerprint looks like a coordinated set.
Counted in origins, it is one participant. On the generator every session has its
own origin, so the two counts give the same results there
(`experiments/sprint-6-noms/README.md`, section 9). On the laboratory captures
(CICIDS2017, CIC-IoT2023) the attacks come from one to seven origins in a single
/24: floods within reach of a per-prefix limit.

**Calibrating τ_cluster.** The threshold is neither tuned on labels nor guessed.
It is fixed per scenario at the **99th percentile of Ω over legitimate
clusters**: the graph is built over attack-free traffic, Ω is computed for the
clusters that form there on their own, and the threshold is set just above where
ordinary legitimate co-occurrence lands. A cluster must therefore be more
coordinated than 99% of what benign traffic produces by itself before the rule
fires.

The weights make that floor asymmetric in a useful way. A set held together
*only* by network proximity — legitimate mobile users behind one CGN /24, the
classic false-positive mode — needs over three times as many linked pairs to
reach the same Ω as a TLS-linked set, so ordinary CGN aggregation stays below
τ_cluster. Conversely Ω can clear the threshold with `relatedByNetworkProximity`
at exactly zero, which is precisely the distributed-botnet case, provided some
combination of high-weight signals is present.

## 5. Coordinated attack classes

All are subclasses of `ApplicationLayerAttack` carrying
`exhibitsCrossSessionStructure`, and all map to MITRE ATT&CK **T1498.001**.

- **`CoordinatedHTTPFlood`** — sessions linked by `relatedTo` converging on one
  endpoint with high aggregate rate. Instantiated experimentally by distributed
  Slow HTTP DoS (Slowloris, slowhttptest, HULK, GoldenEye). This is the class the
  paper evaluates.
- **`CredentialStuffing`** — linked sessions targeting an `AuthEndpoint` with
  high aggregate authentication failure.
- **`CoordinatedAPIAbuse`** — sessions with distinct identities but linked by TLS
  fingerprint or prefix, hitting one `APIEndpoint`, whose summed rate exceeds the
  threshold even though no single session exceeds its quota.

The last two reuse the same machinery but are outside the paper's experimental
scope.

## 6. Evidence chain and derived mitigation scope

When the rule fires, the engine emits the satisfied rule, the ontology instances
involved, the decomposition of Ω(S) per sub-relation, and the derived mitigation
scope. This is exported as JSON-LD over the ontology vocabulary and as STIX 2.1,
an `indicator` plus a `course-of-action` linked by `mitigates`, for SIEM and SOAR
ingestion.

**How the scope is chosen decides whether the verdict is useful or harmful, and
the obvious choice fails.** Taking the property most of the cluster shares, its
modal fingerprint, selects whatever is common; on a service under attack what is
common is the legitimate population. Against a botnet spread over several TLS
stacks, each attacker stack is smaller than the head of the benign distribution,
so the modal value is a *legitimate* fingerprint and the filter blocks users and
no attackers.

The scope is therefore selected by **enrichment**. Let c(f) be the number of
distinct origins of the fired cluster that present fingerprint f, n = Σ_f c(f),
and b(f) the prevalence of f among the origin-fingerprint pairs of a background
profile of normal traffic maintained outside attack episodes. The scope admits
every f that passes two tests:

- **Effect size:** c(f)/n ≥ ρ · b(f), with **ρ = 3**. The fingerprint is at least
  three times more common in the cluster than in normal traffic.
- **Significance:** P[X ≥ c(f)] < λ_e / |F| for X ~ Bin(n, b(f)), with the
  level λ_e calibrated per endpoint (below) and never above **0.01**. A count this
  high is improbable if the cluster drew fingerprints the way normal traffic does. |F| is the number of fingerprints in the profile or the cluster,
  a Bonferroni correction over every fingerprint that could have been tested.
  Counting only the fingerprints present in the cluster undercounts the family,
  because which ones appear is itself random; a first prototype did that and
  exceeded the nominal false-alarm level on the calibration windows.

A fingerprint absent from the profile gets b(f) = 1/N, with N the profile's
count of origin-fingerprint pairs, so a single observation never becomes infinite
enrichment. The result is a *set* of fingerprints, which is what covers a
fragmented botnet.

**Calibrating the level λ_e.** The binomial model treats each origin as an
independent draw from the profile. Generated traffic satisfies that; production
traffic does not, because fleets of legitimate clients switch on together: a
probe fleet of about twenty clients active only during business hours, a
periodic job at fixed minutes of every hour. At the nominal level of 0.01 the
scope named a filter in 26.9% of clean production windows even counting origins
(60.1% counting connections). The level is therefore calibrated per endpoint exactly as τ_cluster is:
over the endpoint's attack-free calibration windows, take for each window the
smallest Bonferroni-adjusted p-value among its enriched fingerprints
(`min_adjusted_p`), and set λ_e to the 1st percentile of those values, capped at
0.01 (`calibrate_level` in `evidence_mitigation.py`). The scope then names a
filter in at most 1% of the windows it was calibrated on. No label is used. On
the generator the level stays at 0.01 in every scenario, so none of the synthetic
results change. On the four production endpoints it falls to between 10⁻⁴ and
10⁻⁷³, and the smallest botnet the test can certify grows with it: the endpoints
with legitimate fleets need about a thousand attackers per window
(`experiments/sprint-6-noms/results/production_summary.json`, Appendix E of the
paper).

**Fingerprints the profile never saw need no such level.** The fleets that set
λ_e present fingerprints of the profile; no fleet presents one absent from it.
Joining the enrichment test with a filter of fingerprints absent from the profile
and seen in at least k_min origins therefore recovers the botnet stacks the strict
level refuses, at almost no cost in false alarms: on production traffic the union
fires on 0.3% of clean windows against 0.2%, blocks 37.5% of 100 attackers on new
stacks against 26.1%, and on the one endpoint in the stealth regime (E1, a botnet
a tenth of its typical window) 11.2% against 0.6%. On stacks real clients also
present the union is the enrichment test, since the unseen filter names none.
Behind a distinct-origin gate (section 4) it fires on 0.1% of clean windows.

**ρ is an effect-size floor, and it barely matters.** Rerun at ρ = 2 and ρ = 5,
no pooled production rate of the paper's Table VI moves by more than 4.5 points
(7.2 for a collateral median over six windows). The level does the work.

**Why a significance test instead of a support floor.** Earlier revisions
required c(f)/n ≥ σ with σ = 0.002. A fixed fraction ignores n. On a cluster of
2,000 sessions it means at least four sessions, a reasonable bar. In a
five-minute window of 80 sessions it means less than one, so any tail fingerprint
seen once passes, since its background prevalence is tiny and its ratio huge.
Measured per window, the fixed floor named a filter in every clean window and in
every flash crowd, blocking a median 12–18% of legitimate users (sprint-6 README,
section 7). The binomial test asks the same question, whether f is
over-represented against the background, with the sample size in it: one
occurrence is never significant, while a few sessions of a fingerprint the
background almost never shows are.

Worked example, with a background of N = 30,000 sessions (|F| ≈ 900, so the cut
is 0.01 / 900 ≈ 1.1 × 10⁻⁵):

| Fingerprint in the window | b(f) | Count | P[X ≥ count] | Named? |
|---|---|---|---|---|
| Botnet stack absent from the profile, n = 150 | 1/30,000 | 2 | ≈ 1.2 × 10⁻⁵ | no, just above the cut |
| Same stack | 1/30,000 | 3 | ≈ 2 × 10⁻⁸ | yes |
| Benign tail fingerprint, n = 86 | 0.0016 | 4 | ≈ 1.5 × 10⁻⁵ | no |
| Benign fingerprint seen once, n = 86 | 1/30,000 | 1 | ≈ 2.9 × 10⁻³ | no |

**The profile has to be large enough for the stacks it must certify.** With the
1,000-session profile of the cluster-level experiments, b(f) of an unseen
fingerprint is 0.001, and a stack of about ten sessions in a 2,000-session cluster
(M = 100) is indistinguishable from the profile's own tail: coverage falls to
38.6%, with no collateral. A profile pooled over 30 attack-free periods (30,000
sessions) restores 89.6% (`experiments/sprint-6-noms/results/profile_drift_m100.json`).
Profile quality governs precision, and profile size governs the smallest stack
the test can certify.

The background must come from outside the attack episode: the campaign spans the
whole window, so using the window itself makes cluster and background prevalences
coincide. No labels are involved. A useful property follows: an adversary hiding
inside a popular benign fingerprint is by definition not enriched, so the scope
is refused and the framework reports that no discriminator exists instead of
emitting a filter that only harms users.

## 7. What is new

Security knowledge graphs have so far been *static*, built from CVEs, reports and
threat-intelligence text. Graphs built from that text do not capture runtime
traffic structure. Recent work populates graphs from traffic itself, but reasons
at the network-node level and stops at a report.

**What the graph adds, measured.** The ontology is where the numeric code reads
its parameters, and the count query is compiled from it:

- every coordinationWeight is read from `ontology/ddos_ontology.owl`
  (`experiments/common/kg_ontology.py`); no script carries its own copy;
- each equality sub-relation is annotated with its `kg:classKey`, the session
  property it equates (`kg:tlsJa4`, `kg:targets`, `kg:srcPrefix`), and
  `relatedTo` with `kg:countUnit` (`kg:originatesFrom`). From these,
  `compile_counts.py` emits the SQL a log store runs to produce the class sizes
  and Ω per window and endpoint, given only a binding of properties to columns.
  On generated sessions the compiled query reproduces `decompose_omega` exactly;
  adding a sub-relation (same User-Agent) to a copy of the ontology costs four
  triples and no code, and the recompiled query carries it
  (`results/compile_check.json`);
- the exported STIX 2.1 bundle passes the OASIS validator in strict mode
  (`results/stix_validation.json`).

What the graph does not add is also measured: the AUC gain comes from the
cross-session structure, which features express as well, and at window scale the
trigger is a count of origins (section 4).

This work differs on four axes, which are the columns of Table I in the paper:
the reasoning unit is the application session; relations between sessions are
explicit, typed and weighted rather than implicit in learned embeddings; the
verdict is a derivation rather than a post-hoc explanation; and a mitigation
scope, plus the legitimate traffic it blocks, follows from the same graph.
