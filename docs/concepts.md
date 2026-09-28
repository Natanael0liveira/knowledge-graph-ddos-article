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
with `rdfs:subPropertyOf` under a symmetric `relatedTo` and annotated with a
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

**The trigger decides what is stopped, and it can be chosen per endpoint.** A
scope blocks only in the windows where the trigger fires. On the busiest endpoint
the p99 gate opens in 6–13% of the windows of a botnet a tenth of the window, so the
binomial configuration stops 11.8% of it (0.6–37.2% by day), while its scope alone
would block 89.6%. Two other triggers were measured after the held-out day:

- a **seasonal gate** compares the distinct origins with their median at the same
  hour of day on the calibration days, and fires past the 99th percentile of that
  ratio on the calibration windows (the same 1% budget). On the busiest endpoint it
  stops 20.4% of the tenth-size botnet and 90.0% of one the size of the window
  (against 70.8%), with no false alarm, but it lifts the binomial configuration's
  false alarms on the web console from 0.28% to 2.64%: the seasonal baseline makes
  off-hours fleets look like surges;
- the **scope as its own trigger** (no gate) stops 89.4–89.8% of the tenth-size
  botnet on every test day. On the busiest endpoint it fires on 0.97% of clean
  windows (0.83% cross-fitted, 0 of 288 on the held-out day), at the budget, and
  its misfires block a median 1.0% of the clients. On the small endpoints it fires on
  1.5–4.4%, above the budget.

So the trigger decides, and the choice needs care. The binomial scope alone on the
busiest endpoint sits *at* the budget rather than below it (14 of 1,440, 95% interval
0.53–1.63%, rising 0, 0, 1, 5, 8 by day) and depends on the fleet exemption (92 of 1,440
without it), and under the cross-fitted beta-binomial it fired on 1.74% of the held-out
day's windows. The cross-fitted beta-binomial behind the seasonal gate stays within
the budget on every endpoint on both day sets (4 of 5,643 and 0 of 1,152) while
stopping more than the origin gate (20.4% of a tenth-size botnet on E1 against 11.9%).
But on new stacks of at least k_min origins, as in that tenth-size botnet, the unseen
filter alone does as well under every trigger, with fewer false alarms and flash-crowd
firings (below that size the test names stacks the filter cannot, but only where its trigger
opens: of 100 attackers, the cross-fitted beta-binomial behind the seasonal gate stops
53-84% on the small endpoints and 3.9% on the busiest one, against the filter's 43%): as its own trigger it misfires on 0.28% of
E1's clean windows and at most 0.42% elsewhere, and stops the same 90%. The enrichment
test's gain is on shared stacks, which the unseen filter never names. So the paper
(Table VI) takes the unseen filter as its own trigger as the baseline of the next,
pre-specified test, against the cross-fitted beta-binomial behind the seasonal gate and
the binomial scope with known fleets as its own trigger; all of it was examined after
the held-out day was read.

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

All are subclasses of `ApplicationLayerAttack` defined by cross-session
structure (the ontology states it in each class comment; it is not a declared
property), and all map to MITRE ATT&CK **T1498.001**.

- **`CoordinatedHTTPFlood`** — sessions linked by `relatedTo` converging on one
  endpoint with high aggregate rate. Instantiated experimentally by distributed
  Slow HTTP DoS (Slowloris, slowhttptest, HULK, GoldenEye). This is the class the
  paper evaluates.
- **`CredentialStuffing`** — linked sessions targeting a `LoginEndpoint` with
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
results change. On the four production endpoints its median falls to between 10⁻⁴
and 10⁻⁷³, and the smallest botnet the test can name grows with it (the
calibration floor, below). At such levels the p-value is a score, not a probability
the model gets right, and λ_e is an empirical quantile of that score.

The 1% does not hold on the days after the calibration. On the clean test-day
windows the binomial configuration's scope alone names a filter in 2.2% (4.4% on
the web console), the beta-binomial's in 4.4% and the calibrated z-score in 6.1%,
and the distinct-origin gate alone fires in 3.0% against its own 1%. The
configurations' false-alarm rates (0.1–0.4% of clean windows) come from the
conjunction: gate and scope seldom misfire together (paper, Section V-B).

**The calibration floor.** A calibrated level has a price, and it can be
computed before any attack. Among n origins, the test names a stack only past the
smallest count c with P[Bin(n, b) ≥ c] · |F| < λ_e (and c/n ≥ ρ·b). A botnet of A
attackers spread over 25 stacks, 90% of it on the stacks, puts about 0.9·A/25
origins on each stack in a window of n₀ + A origins. The floor is the smallest A
whose stacks reach that count, divided by the endpoint's median window n₀. A
hypothetical endpoint with 2,000 origins per window, a profile of 200,000
origin-fingerprint pairs and |F| = 300 shows the mechanism:

| λ_e | Smallest nameable count per stack | Smallest botnet A | Floor (share of the window) |
|---|---|---|---|
| 10⁻² | 3 | 84 | 4% |
| 10⁻²¹ | 10 | 278 | 14% |
| 10⁻⁶⁰ | 22 | 612 | 31% |

On production traffic the fleets push the busiest endpoint's level to about 10⁻⁶⁰,
where the binomial test names a new stack only past 15 to 18 origins, 16% of the
typical window. Exempting the endpoint's known fleets from the scope and from the
level's calibration (below) raises the level to about 10⁻²¹ and lowers that to 7%.
The exemption is an allow-list: a fingerprint on it is never scoped.

The deployed configuration joins the test with the unseen filter (below), which
names a stack absent from the profile once it holds k_min = 5 origins, so from
⌈k_min·M/0.9⌉ attackers whatever the level: 139 for M = 25, 28 for M = 5, 556 for
M = 100. Its floor for M = 25 (paper, Table V) is therefore 139 attackers on new
stacks on three endpoints (5% of the busiest window, 2.2 and 3.4 whole windows on
two small ones) and 84 on the fourth, where the test names them first. On stacks
real clients also present the unseen filter names nothing and the level binds: 254
attackers on the busiest endpoint (8% of its window) and 4 to 19 whole windows on
the small ones, where no botnet that fits in a window can be named. For an operator
the floor is a planning quantity: above it the scope can be a fingerprint filter;
below it the fallback is a rate limit or a challenge.

**The floor is not a cliff.** It is where the *mean* stack, 0.9·A/M, reaches c_min, and
stack sizes vary. An attacker sits on a stack with probability 0.9, and its stack then
holds it and Bin(A − 1, 0.9/M) others, so the share of a botnet on new stacks that the
scope alone names is

    0.9 · P[Bin(A − 1, 0.9/M) ≥ c_min − 1]

On the busiest endpoint that is 9%, 43% and 88% at 50, 100 and 250 attackers, the
injected botnets give the same, and at the floor itself (139) about two thirds: the
floor is the size at which a typical stack is named, and below it the scope still names
the stacks chance makes larger.

**The ratio sets a harder limit.** However large the botnet, one of its stacks holds at
most 0.9/M of the window, so the effect condition c/n ≥ ρ·b fails for every fingerprint
with b > 0.9/(ρ·M): 1.2% for M = 25, 6% for M = 5. On the four production endpoints the
fingerprints past that limit are the 4 to 28 most common, and they carry 86–94% of the
origins. A bot hiding behind one of them is never scoped by the test, which is the
arithmetic behind the adversarial boundary (sprint-6 README, section 18).

**Naming is not stopping.** The configuration acts only where the distinct-origin gate
fires. On the busiest endpoint the gate opens in 6–13% of the windows of botnets of 25
attackers to a tenth of the window, so a botnet the scope names in every window is
11.8% stopped; on the small endpoints a botnet of 100 attackers opens the gate in most
windows, and there the floor decides.

**A background that models the fleets lowers the floor.** Fleets break the
binomial's independence because their clients switch on together, which makes a
fingerprint's count overdispersed: its variance across windows exceeds n·b·(1 − b).
The beta-binomial variant (`--overdispersion` in `rule_detection_production.py`)
estimates, for each fingerprint of the profile, an intra-window correlation φ from
the calibration windows by the method of moments, Var[c] = n·b·(1 − b)·(1 + (n − 1)·φ),
clipped to [0, 0.99], and tests the count against a beta-binomial with the same
mean. A fingerprint absent from the profile keeps the binomial, since there is
nothing to estimate φ from, and λ_e is calibrated as before. A fleet's surge now
falls within what the background expects, so the calibrated level rises: to 7 × 10⁻⁵ on the busiest endpoint,
where three origins name a stack, and to the 0.01 cap on the three small ones, where
two do. The floor on shared stacks falls to 86 attackers on the busiest endpoint (3%
of its window) and to 1.4–4.2 windows elsewhere, and no fingerprint qualifies as a
known fleet in sample, so the allow-list is not needed there (paper, Sections V-B and
V-C, Table V). The floor is computed at the shared stack's own correlation. The tail's
median correlation is 0 on three endpoints, where the floor equals the binomial tail's,
and about 3 × 10⁻⁴ on the fourth, where even so small a correlation raises it from 56 to
84 attackers: it adds b·(1 − b)·φ to the variance of the stack's per-window
probability, which rivals b² when b is small. The price, in sample, is a higher false-alarm rate: 22 of
5,643 clean windows (0.4%) against 5 for the binomial configuration, and 1.3% on
the web console, above the 1% budget (the calibrated z-score is at 1.1% there
too). The beta-binomial was built after the fresh day was read, so its result on
that day (no false alarm) is post hoc; the binomial configuration is the one the
protocol fixed (sprint-6 README, section 13).

**Calibrating out of sample.** In the rolling split the calibration windows also
build the profile they are judged against, so a level can be fitted to its own days.
Cross-fitting judges each calibration day against a profile (and φ) of the *other*
calibration days when λ_e, the z-score's threshold and the known fleets are fitted,
as the test day is judged against days it is not part of; the test day's profile and
the trigger stay as they were. Two things follow. The binomial configuration barely
moves (6 false alarms against 5 on the test days), so its calibration was not
flattered by the in-sample fit. The beta-binomial's levels fall from the 0.01 cap to
between 10⁻¹⁷ and 10⁻², and it then matches the binomial's 6 false alarms with
filters that block a median 2% of a window's clients against 31%, fewer flash-crowd
triggers and a lower floor on shared stacks everywhere (84–168 attackers against
114–1,041 for M = 25).
Levels that low need p-values in logs: a fleet absent from the other days' profile
has p-values below the smallest double, and a level computed from p-values that
underflow to 0 is 0, which names nothing (`log_tail` in
`rule_detection_production.py`; sprint-6 README, section 15). Both the beta-binomial
and the cross-fitting were built after the fresh day was read, so the deployable
choice remains the binomial configuration until a pre-specified test on new days.

**Fingerprints the profile never saw need no such level.** The fleets that set
λ_e present fingerprints of the profile; no fleet presents one absent from it.
Joining the enrichment test with a filter of fingerprints absent from the profile
and seen in at least k_min origins therefore recovers the new botnet stacks the
strict level refuses, at almost no cost in false alarms. Behind a distinct-origin
gate (section 4) the union fires on 0.1% of clean production windows and blocks
38.4% and 77.7% of 100 and 1,000 attackers on new stacks (paper, Section V-B); the
unseen filter alone stops 29.4% of the 100. On stacks real clients also present the
union is the enrichment test, since the unseen filter names none. On generated traffic the unseen filter alone matches the
test up to 25 stacks, because the generator's stacks never occur in the benign
vocabulary; with stacks drawn from the profile's tail it blocks none, where the
test blocks 85.4% (paper, Table III).

**Baselines at the same budget.** A per-fingerprint z-score, z = (c − n·b) /
√(n·b·(1 − b)) with z > 3, fires on 2.9% of clean production windows behind the
distinct-origin gate (2.6% behind Ω), so its
detection is not comparable with a test held to 1%. Calibrated as λ_e is, with its
threshold at the 99th percentile of each calibration window's largest z (never
below 3), it blocks as much as the binomial configuration or more above the floor, at
0.4% of clean windows against 0.1% and with lighter alarms, and the beta-binomial
lands on the same operating point. On the fresh day, analyzed as fixed in advance,
the binomial configuration and the z-score fire on the same two windows. The
binomial buys its lower false-alarm rate on the test days with a higher floor. A
z-score of each fingerprint against its own calibration history, calibrated the same
way, fires on half of the flash crowds (sprint-6 README, section 12). Cross-fitted,
the calibrated z-score's threshold rises by a median factor of 1.8 and its lead in
detection disappears (33.6% of 100 attackers against the binomial's 36.9%). Above the
floor every calibrated scope stops 67–71% of a botnet the size of the busiest
endpoint's typical window.

**The WAF's verdicts are not labels for this problem.** The only malicious population
the production exports carry is the clients the operator's WAF blocked. Scored against
those verdicts, the scopes look precise only when the profile excludes the blocked
clients, and that agreement is built in. If the WAF blocks a share S of a window, a
fingerprint whose unblocked clients keep their profile share b is enriched on the full
traffic, c/n ≥ ρ·b, only when a share s ≥ 1 − (1 − S)/ρ of its own clients was
blocked: 0.88 at S = 63% and 0.80 at S = 39%, the two endpoints where the WAF blocks
most. With a profile of all clients, as a scope in front of the WAF would build it,
the scopes name a filter in 2–3% of those windows, fewer of the clients they would
block were blocked than a random pick gives, and they catch the WAF's surges at
chance. The WAF's populations are part of every day's traffic, so a scope that reads
deviations from that traffic ignores them (paper, Section V-B; sprint-6 README,
section 16).

**ρ is an effect-size floor, and it barely matters.** Rerun at ρ = 2 and ρ = 5,
no pooled production firing rate moves by more than 0.3 points and no blocked
share by more than 4.5, while a collateral median shifts by up to 7.2 (paper,
Appendix E). The level does the work.

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

**The profile has to be large enough for the stacks it must name.** With the
1,000-session profile of the cluster-level experiments, b(f) of an unseen
fingerprint is 0.001, and a stack of about ten sessions in a 2,000-session cluster
(M = 100) is indistinguishable from the profile's own tail: coverage falls to
38.6%, with no collateral. A profile pooled over 30 attack-free periods (30,000
sessions) restores 89.6% (`experiments/sprint-6-noms/results/profile_drift_m100.json`).
Profile quality governs precision, and profile size governs the smallest stack
the test can name.

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
- in the operator's log store, the compiled query returned the exported distinct
  origins and same-/24 pairs in every window of two production days, and the JA4
  class sizes in the 288 windows a day where the WAF blocked no client
  (`results/compile_production_check.json`, `compile_production_check_fresh.json`);
- the exported STIX 2.1 bundle passes the OASIS validator in strict mode
  (`results/stix_validation.json`) and crosses the reference TAXII 2.1 server
  unchanged, save the extension definition. MISP's STIX importer drops the
  fingerprints, which STIX 2.1 carries only in an extension the importer does not
  map to MISP's own JA4 object (`ja4-plus`), and DOTS scopes a request by the
  attacked resource and filters only on network and transport header fields (RFC 8783),
  so both would widen a fingerprint scope to the endpoint or to address prefixes.

Of the standards examined, STIX 2.1, DOTS and Flowspec have no JA4 property in their
core vocabulary. OCSF records JA4 fingerprints in network events (since v1.3.0, August
2024) and in the evidence of findings (v1.4.0, January 2025), but defines no filter or
remediation over them. The paper states this as its third contribution:
fingerprint-scoped mitigation needs a JA4 match in the DOTS filters and a JA4 property in
STIX, for instance in a TLS extension of its network-traffic object. The ontology
is the specification the operator deploys and the vocabulary of the exported chain.

What the graph does not add is also measured: the AUC gain comes from the
cross-session structure, which features express as well, and at window scale the
trigger is a count of origins (section 4). A learned model over those features does
not generalize across botnet structures, though: trained on campaigns of 5 stacks
and tested on 25 or 100, configuration (d) falls from 0.95–0.995 on the same stack
count to 0.61 and 0.63,
and trained on 25, to 0.48 on 5 and 0.75 on 100, because the forest learns the
band of fingerprint sharing one stack count produces. The label-free rule keeps
about 90% up to 25 stacks. These tests use disjoint seeds: the generator draws the
benign sessions before anything that depends on M, so a same-seed split would let
even per-session features score 0.88–0.94 by memorizing identical benign rows
(sprint-6 README, section 14).

This work differs on four axes, which are the columns of Table I in the paper:
the reasoning unit is the application session; relations between sessions are
explicit, typed and weighted rather than implicit in learned embeddings; the
verdict is a derivation rather than a post-hoc explanation; and a mitigation
scope, plus the legitimate traffic it blocks, follows from the same graph.
