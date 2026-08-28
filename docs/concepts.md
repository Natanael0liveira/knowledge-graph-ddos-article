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

summed over the sub-relations, where Eᵢ(S) is the set of unordered session pairs
in S linked by sub-relation *i*. A SPARQL/SWRL rule fires when Ω(S) clears a
threshold τ_cluster and every session of S targets the same endpoint. The
derivation that satisfied the rule *is* the verdict; nothing is explained after
the fact.

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

The scope is therefore selected by **enrichment**. With c(f) the prevalence of
fingerprint f inside the fired cluster and b(f) its prevalence in a background
profile of normal traffic maintained outside attack episodes, the scope admits
every f with c(f)/b(f) ≥ ρ and c(f) ≥ σ, with **ρ = 3** and **σ = 0.002** at
the operating point used throughout. This yields a *set* of fingerprints, which
is what covers a fragmented botnet.

The support floor σ must sit **below the share of the smallest stack worth acting
on**, that is, below 1/M for a botnet spread over M TLS stacks; σ = 0.002 leaves
room down to M = 100 and beyond. Lowering it costs nothing, because it is the
enrichment test — not the floor — that keeps legitimate traffic out.

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

This work differs on four axes, which are the columns of Table I in the paper:
the reasoning unit is the application session; relations between sessions are
explicit, typed and weighted rather than implicit in learned embeddings; the
verdict is a derivation rather than a post-hoc explanation; and a mitigation
scope, plus the legitimate traffic it blocks, follows from the same graph.
