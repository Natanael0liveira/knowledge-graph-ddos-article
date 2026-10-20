# Concepts

The definitions and formulas behind the NOMS paper in
[`papers/http-session-noms`](../papers/http-session-noms/). This file is their single home.
Other topics live elsewhere:

| Topic | File |
|---|---|
| Metrics, statistical tests and the columns of the production tables | [`metrics.md`](metrics.md) |
| Experimental design: traffic sources, injections, protocols | [`evaluation.md`](evaluation.md) |
| Windows, runtime cost, class counts and pair edges | [`runtime.md`](runtime.md) |
| Related work and the exchange standards | [`prior-art.md`](prior-art.md) |
| Results in prose | [`experiments/FINDINGS.md`](../experiments/FINDINGS.md) |
| Why each stage is built as it is | [`experiments/METHODOLOGY.md`](../experiments/METHODOLOGY.md) |
| The lab notebook: every run, correction and review | [`experiments/sprint-6-noms/README.md`](../experiments/sprint-6-noms/README.md) |

**Pointers.** "III-C" or "App. E" is a section of the paper, "Table V" or "Fig. 2" one of its
tables or figures, and "§13" a numbered section of the lab notebook. Result files (`*.json`) are in
[`experiments/sprint-6-noms/results/`](../experiments/sprint-6-noms/results/), and scripts in
[`experiments/sprint-6-noms/scripts/`](../experiments/sprint-6-noms/scripts/) unless a path is given.

**Contents.**
[1 The decision](#1-the-decision) ·
[2 Units, windows and outcome words](#2-units-windows-and-outcome-words) ·
[3 The session ontology](#3-the-session-ontology) ·
[4 Coordination mass and the weights](#4-coordination-mass-and-the-weights) ·
[5 The triggers](#5-the-triggers) ·
[6 The scope](#6-the-scope) ·
[7 Calibration](#7-calibration) ·
[8 The calibration floor and the enrichment limit](#8-the-calibration-floor-and-the-enrichment-limit) ·
[9 From the ontology to the log-store query](#9-from-the-ontology-to-the-log-store-query) ·
[10 Results in brief](#10-results-in-brief) ·
[11 Positioning](#11-positioning)

---

## 1. The decision

Low-rate distributed application-layer DDoS attacks keep every source below per-source
thresholds. A stealthy campaign also makes each session look legitimate on the per-session
signals detectors use, such as connection duration and packet rate (I). The operator then faces
one decision: which clients to block without harming legitimate traffic. Existing detectors at
most flag an attack, leaving the choice of whom to block open (I). A survey of 75
application-layer DDoS studies found that 47% use request-stream and packet-pattern features
(`odusami2020survey`).

TLS fingerprints group clients by their handshakes, so traffic from different origins can be
compared. Legitimate clients often share fingerprints, though. What matters is whether a
fingerprint appears more often than the endpoint's normal traffic predicts (I).

The method runs per endpoint and five-minute window (Fig. 1):
1. a **trigger** raises an alarm (section 5);
2. the **scope** selects the TLS fingerprints to block, by how often they appear among the
   alarm's origins relative to a **profile** of the endpoint's normal traffic (section 6);
3. when the trigger fires and the scope selects nothing, the operator falls back to a rate limit
   or a challenge to every client, the **fallback** (section 5).

The paper makes three contributions (I):
- (i) *profile-relative scoping*: select the fingerprints that occur more often than the
  endpoint's normal traffic predicts (section 6);
- (ii) *statistical calibration*: calibrate the test per endpoint to a 1% false-alarm budget on
  attack-free windows, which sets a *calibration floor*, the botnet size from which the scope
  selects a typical stack (sections 7 and 8);
- (iii) *a session ontology*: it defines the evidence the test reads and the selected filter, and
  the log-store queries are compiled from it (sections 3 and 9).

**Threat model** (III-A). The defender operates the targeted application and terminates its TLS.
For each request it records the ClientHello, from which it computes a JA4 fingerprint, the source
address with its prefix and ASN, the endpoint, the arrival time and any application identity. It
sees neither the botnet's control channel nor which sources are coordinated. It can profile normal
traffic outside attack episodes. The attacker controls K compromised devices and may make each
session statistically indistinguishable from a legitimate one. A bot keeps the fingerprint of its
TLS stack, the library shipped with its device or toolkit. Browser-imitating bots fall outside the
threat model, and the evaluation tests such attacks as its boundary (V).

## 2. Units, windows and outcome words

**Endpoint and window.** The unit of decision is one endpoint e and one five-minute window, 288
windows a day. S is the set of sessions to e in the window (III-B). On generated traffic, Table III
applies each scope to the alarm's *cluster* instead: the sessions of an endpoint chained while
consecutive starts stay within 300 s of one another (IV-A).

**Origins.** An origin is a source address. The trigger and the scope count distinct origins, n,
and count each address once per fingerprint it presents (III-B). The profile and the test
therefore work on origin–fingerprint pairs (III-C). The production gate and the endpoint term of Ω
also count plain-HTTP clients, and the compiled query counts each address once (App. A). Windows
with fewer than k_min = 5 origins are left out, since no gate can open there
([`metrics.md`](metrics.md#the-rate-and-its-exact-interval) counts them).

**Why count origins.** Sessions stay the nodes of the graph, and the relations still link
sessions. Only the aggregation counts each class in distinct origins, through
`originatesFrom`, the ontology's count unit. The threat is a botnet of many devices, so
coordination means coordination across sources. On production traffic a session is a connection,
and one client opens many: 5.8 connections per client on the API endpoint (E3) over the eight
initial days (§9). Counted in sessions, one automated client opening dozens of connections with
one fingerprint looks like a coordinated set. Counted in origins, it is one participant. At the
nominal level, the scope selects a filter in 60.1% of clean windows counted in connections and in
26.9% counted in origins (App. E). On generated traffic each origin carries one session, so the
two counts agree there (III-C). On the laboratory captures the attacks come from one to seven
origins in a single /24, floods within reach of a per-prefix limit
([`FINDINGS.md`](../experiments/FINDINGS.md), App. C).

**Clean windows.** A clean window is a test window before any botnet is injected into it, taken
as attack-free (IV-A). [`evaluation.md`](evaluation.md#assumptions) states the assumptions behind
it. The data files call the held-out day the *fresh day*.

**Median window and tenth-size botnet.** n₀ is an endpoint's median calibration window: about
3,000, 62, 41 and 20 origins on E1 (real-user monitoring beacons), E2 (web console), E3 (API) and
E4 (single sign-on) (IV-A, Table V). A *tenth-size* botnet holds a tenth of n₀ (IV-A).

**Outcome words.** The paper uses them in a fixed sense (IV-B, V):
- the test, or any scope, **selects** fingerprints;
- a scope **covers** the attackers who present a selected fingerprint;
- a configuration **blocks** attackers only in windows where its trigger fires and its scope
  selects their stacks.

[`metrics.md`](metrics.md) defines the measures built on these words: collateral (§3), false
alarms, or misfires (§5), and coverage (§7), with the columns of Tables IV–VII (§4).

## 3. The session ontology

**Ontology, OWL and knowledge graph.** An ontology is a formal description of a domain: classes
(`ApplicationSession`, `Endpoint`, `Identity`), typed relations between them (`hasIdentity`,
`targets`, `relatedTo`), datatype properties (`requestsPerSecond`, `failedLogins`) and axioms that
every valid instance obeys. OWL is the W3C language for writing ontologies, and a knowledge graph
is an ontology filled with data. The ontology is
[`ontology/ddos_ontology.owl`](../ontology/ddos_ontology.owl).

| | Relational schema | Ontology |
|---|---|---|
| Structure | Fixed tables | A graph of classes and properties |
| Relations | Implicit, through foreign keys | Named, typed properties |
| Meaning | In the application code | Declared, in annotations a program can read |
| Extension | A schema migration | New subclasses, properties or annotations |

**What the ontology does here.** It specifies the counts the trigger and the scope read, and it is
what an operator would deploy (III-E). The log-store query is compiled from its annotations
(section 9). No reasoner runs in the evaluation (III-E). OWL 2 RL, whose rule-based entailment
runs in polynomial time, is the profile a deployment that materializes the graph would target. The
paper does not measure it ([`runtime.md`](runtime.md)).

**The session as an entity.** The HTTP session groups requests under one observed identity: a
cookie, a token, a username or a TLS fingerprint. `ApplicationSession` links each session to its
`Identity` (`hasIdentity`), its source `IPAddress` (`originatesFrom`), its `Endpoint` (`targets`),
its `Behavior` (`exhibitsBehavior`) and other sessions (`relatedTo`). An `Attack` links to the
`Mitigation` derived for it (`derivedMitigationScope`), whose conditions state the selected scope,
and to one evidence node per sub-relation that links its sessions (`activatedSubRelations`).

### The weighted `relatedTo` family

Sub-properties of a symmetric `relatedTo` describe how two sessions are related (III-E, App. A).
Each carries a `coordinationWeight` in [0, 1] and is instantiated from its own evidence, so two
sessions may be linked by one, several or all six.

| Sub-property | Weight | Links two sessions that | Cost to the attacker of breaking it | In the paper (App. A) |
|---|---|---|---|---|
| `relatedByTLSFingerprint` | 1.0 | share a JA4 | High: a new TLS stack means new tooling | exercised as exact JA4 (a near variant, `ja4_distance = 1`, is specified only) |
| `relatedByReusedIdentity` | 1.0 | share a cookie, token or username | High: fresh credentials cost the campaign | specified only |
| `relatedByTemporalPattern` | 0.9 | have inter-arrival sequences within a DTW distance τ_DTW | High: the coherence comes from how the botnet runs | specified only |
| `relatedByPayloadSignature` | 0.6 | have payload summaries above a cosine similarity τ_payload | Medium: randomizing is cheap but costs coherence | specified only |
| `relatedByEndpointConvergence` | 0.6 | target the same endpoint, a host or an address and port | Medium: spreading the target dilutes the attack | exercised (path normalization is specified only) |
| `relatedByNetworkProximity` | 0.3 | share an IPv4 /24 or IPv6 /48 | Low: proxies and cloud fleets span prefixes | exercised (a shared ASN is specified only) |

The weights follow the attacker's cost of breaking each signal, and the calibration supports only
the top of that order (section 4). Network proximity is the weakest link, since carrier-grade NAT
makes a shared /24 a weak discriminator (III-B). It therefore enters as auxiliary evidence and is
never required.

**JA4.** JA4 (`althouse2023ja4`) summarizes the TLS ClientHello (III-A). Its first part spells out
the transport, the TLS version, whether the SNI names a domain, the cipher and extension counts and
an abbreviation of the first ALPN value. Its other two parts are truncated hashes of the sorted
cipher suites and of the sorted extensions with the signature algorithms. It identifies the
client's TLS stack, so it survives address rotation. Applications built on one library often share
a fingerprint (II, `anderson2019tls`). That sharing enables fingerprint filtering and also creates
collateral risk (II).

### Attack classes

The coordinated attack classes are subclasses of `ApplicationLayerAttack`. Each class comment
states its cross-session structure, and no property declares it.
- **`CoordinatedHTTPFlood`**: many distinct origins converging on one endpoint, with
  Ω(S) ≥ τ_cluster. It is the target class of the base rule (III-B) and the class the paper
  evaluates. It sits in the Slow HTTP DoS family next to the connection-exhaustion attacks, such as
  Slowloris, and HULK and GoldenEye are its subclasses. The paper runs the rule on the generator's
  distributed Slow HTTP DoS campaigns and on laboratory captures of Slowloris, Slowhttptest, HULK,
  GoldenEye and HTTP floods (IV-A, App. C).
- **`CredentialStuffing`**: distributed login attempts with reused credentials, linked by reused
  identity. It is declared, and no experiment operationalizes it.
- **`CoordinatedAPIAbuse`**: distinct tokens converging on an `APIEndpoint` through
  `relatedByTLSFingerprint`. It is declared, and no experiment operationalizes it.

The ontology carries no MITRE ATT&CK mapping. The closest techniques are T1499.002 (Endpoint
Denial of Service: Service Exhaustion Flood), whose description includes HTTP floods, T1499.003
(Application Exhaustion Flood) for floods on resource-intensive features, and T1110.004 (Brute
Force: Credential Stuffing).

## 4. Coordination mass and the weights

For a set S of sessions, the coordination mass is

    Ω(S) = Σᵢ wᵢ · |Eᵢ(S)|

where Eᵢ(S) is the set of pairs of distinct origins linked by sub-relation i, and wᵢ is its
`coordinationWeight` (App. A, Eq. 1). Each pair counts once, so one client's many connections
cannot mimic coordination. For an equality sub-relation, |Eᵢ(S)| = Σₖ C(nₖ, 2) over its class
sizes nₖ in distinct origins, so Ω depends only on class sizes. With the three exercised
sub-relations, one endpoint's window gives

    Ω = 1.0 · Σ_f C(n_f, 2) + 0.6 · C(n, 2) + 0.3 · P₂₄

where n_f counts the origins with fingerprint f, n counts all of them, and P₂₄ counts the pairs
sharing a /24 (§9). [`runtime.md`](runtime.md) shows how class counts avoid the quadratic cost of
pair edges.

**What the weights do.** In one endpoint's window the endpoint term, 0.6 · C(n, 2), carries most
of Ω: 91% in the default campaign (Listing 1, App. D). Ω therefore mostly measures volume (III-B).
The weight calibration identifies only the top of the order. The TLS fingerprint alone
discriminates (AUC 0.93, versus 0.50 for endpoint convergence and 0.58 for network proximity), and
every endpoint weight in the grid reaches the same optimal AUC of 0.943 (App. B). That calibration
ran on the older sprint-4 scenarios, with a near-uniform benign vocabulary and a monolithic botnet
(App. B). Per window, uniform weights catch at least as many attack windows (78.9% and 85.7% at
K = 1000 and 50). Without its endpoint term Ω catches 33.3% and none, while still flagging 53–100%
of flash crowds (App. E). Ω ≥ τ_cluster thus says that a window holds more coordination than normal
traffic does, and the scope supplies the discriminator. The weights order the evidence chain,
which reports each sub-relation's share of Ω, and they keep network proximity auxiliary.

**The weights make the threshold asymmetric.** A set held together only by network proximity,
such as mobile users behind one carrier-grade NAT /24, needs over three times as many linked pairs
as a TLS-linked set to reach the same Ω (1/0.3). Ordinary NAT aggregation therefore stays below
τ_cluster. A distributed botnet can still clear the threshold with no proximity pairs at all.

**Calibrating τ_cluster.** τ_cluster is the 99th percentile of Ω over attack-free windows, and no
label enters it. On generated traffic it is taken per window over the 30 attack-free runs that
also form the profile (App. E). On production it is taken per endpoint over its calibration windows
(III-B). A window must hold more coordination than 99% of attack-free windows before the base rule
fires.

## 5. The triggers

A trigger decides when the scope is consulted. The three gates are calibrated on attack-free
windows at the 99th percentile, the same 1% budget (III-B, V-C). With no gate, the scope's own
calibration sets the budget (section 7).

| Trigger | Fires when | Status |
|---|---|---|
| Distinct-origin gate | n ≥ k_min = 5 and n reaches its 99th percentile over attack-free windows | the production trigger, chosen on the test days (III-B, IV-B) |
| Ω gate | Ω(S) reaches τ_cluster, its 99th percentile | the trigger of the base rule (III-B) |
| Seasonal gate | n divided by its median at the same UTC hour of the calibration days reaches that ratio's 99th percentile | post hoc (V-C) |
| No gate | the scope selects a filter in a window of at least k_min origins | post hoc, the scope as its own trigger (V-C) |

The **base rule** is the Ω gate with the binomial test as its scope. The held-out protocol takes it
as the reference (III-B). The seasonal gate, in full (`load` in `production_tables.py`):

    r(w) = n(w) / median{ n(w′) : w′ a calibration window at the same UTC hour as w }
    fires when r(w) ≥ max(1, 99th percentile of r over the calibration windows)

**The trigger should not read the scope's evidence.** The distinct-origin gate agrees with Ω in
136 of the 181 clean windows where either fires. It halves the base rule's false alarms with no
loss of detection (App. E). The reason lies in the fleets. A legitimate fleet concentrates on one
fingerprint, which lifts Ω's TLS term, Σ_f C(n_f, 2), in the very windows where the test selects
that fleet. The clean windows that only Ω admits carry a median 33% of their Ω outside the
endpoint term, versus 12% in the others (§9, `production_summary.json`). A trigger that counts
fingerprint sharing therefore fires most where the scope misfires, and counting origins avoids
that link. A threshold on the aggregate request rate adds nothing either. Each session of a Slow
HTTP campaign keeps a legitimate rate, so a calibrated rate threshold reduces to an origin count.
Earlier versions of the rule also required an aggregate rate and a `BotBehavior` profile. Both were
dropped: in steady traffic the rate condition never held, so the rule never fired outside a burst
(§6), and no script ever evaluated the `BotBehavior` condition.

**The fallback.** When the trigger fires and the scope selects nothing, the fallback acts: a rate
limit or a challenge to every client. Below the calibration floor, or when attackers use
fingerprints the scope cannot tell from normal clients, an alarm mainly invokes the fallback (VI).
Its cost is not included in the false-alarm budget (VI), and
[`metrics.md`](metrics.md#the-fallbacks-cost) counts it.

**The trigger decides what is blocked.** A configuration blocks attackers only in windows where its
trigger fires. On the busiest endpoint a small botnet barely raises the origin count, so the gate
rarely opens, and a scope that would cover most of the botnet blocks little of it. On the smaller
endpoints the same botnet opens the gate in most windows, so the floor is the main limit there
(V-C, Fig. 2). Section 10 gives the numbers.

## 6. The scope

The scope determines which clients a mitigation would affect (III-C).

### Why the modal fingerprint fails

Selecting the alarm's most common (modal) fingerprint is the obvious choice, and it fails. On a
service under attack, the most common fingerprint usually belongs to legitimate users. Consider a
botnet of A attackers spread uniformly over M stacks, with 90% of them on the stacks and the rest on
one-off fingerprints. About 0.9·A/M attackers use each stack. If the most common legitimate
fingerprint holds a share p₁ of n_b legitimate origins, the modal fingerprint belongs to the attack
only while

    0.9 · A / M > p₁ · n_b

With the measured p₁ = 38.4% of requests, used as a proxy for origins, and a campaign as large as
legitimate traffic (A = n_b), this holds only for M < 0.9/0.384 ≈ 2.3 (III-C). With more stacks the
modal filter blocks legitimate clients and no attackers. From five stacks on it covers 0.0% of
attackers and blocks 39.0% of legitimate traffic (V-A, Table III).

### The profile

The scope compares the alarm with a **profile** of the endpoint's normal traffic, collected outside
attack episodes (III-C). Let N be the number of origin–fingerprint pairs pooled in the profile. The
background share of fingerprint f is

    b(f) = (pairs with f in the profile) / N + 1/N

The 1/N term keeps every background share above zero. A fingerprint absent from the profile gets
1/N, so one observation never becomes infinite enrichment (III-C; `adjusted_p` in
`rule_detection_production.py`).

The profile needs no attack labels, but it must exclude attack episodes. A campaign spanning the
profile would no longer appear enriched (III-C). On production, each test day is judged against a
profile of all earlier days (IV-A). Profiles should be rebuilt from windows where the scope selects
nothing, and a persistent new fingerprint should enter the profile only after operator review (VI).
Attackers who manipulate the profile or the fleet exemptions were not tested (VI).

**The profile must be large enough for the stacks it has to resolve.** With the 1,000-session
profile of the cluster-level experiments, an unseen fingerprint has b(f) = 0.001. At M = 100 a stack
holds about ten sessions of a 2,000-session cluster and cannot stand out against the profile's own
tail: the test covers 38.6%, with no collateral. A profile pooled over 30 attack-free periods
(30,000 sessions) restores 89.6% (V-A, `profile_drift_m100.json`). A flat or missing profile makes
every fingerprint look rare and raises collateral to 77.6%. A profile drifted to α = 2.0 has little
effect (V-A).

### The binomial enrichment test

Let c(f) count the alarm's origins presenting f, and n = Σ_f c(f). The **binomial enrichment test**
selects every f that passes two conditions (III-C):

- **effect size:** c(f)/n ≥ ρ · b(f), with ρ = 3, so f is at least three times more common in the
  alarm than in normal traffic;
- **significance:** P[X ≥ c(f)] < λ_e / |F| for X ~ Bin(n, b(f)), with the level λ_e calibrated
  per endpoint and never above 0.01 (section 7).

|F| counts the fingerprints in the profile or the alarm, a Bonferroni correction over every
fingerprint that could have been tested. Counting only the fingerprints present in the alarm
undercounts the family, since which ones appear is itself random. A first prototype did that and
exceeded the nominal level on its own calibration windows (§7). The test returns a *set* of
fingerprints, so it can cover a botnet spread over several stacks.

ρ sets a minimum effect size, and its value barely matters. At ρ = 2 or 5, no pooled firing rate of
the base rule moves by more than 0.3 points, no blocked share by more than 4.5, and no collateral
median by more than 7.2 (App. E). The level does the work.

**Worked example.** A background of N = 30,000 sessions with |F| ≈ 900, the per-window profile of
§7, puts the cut at 0.01/900 ≈ 1.1 × 10⁻⁵. The p-values follow from the binomial tail:

| Fingerprint in the window | b(f) | Count | P[X ≥ count] | Selected? |
|---|---|---|---|---|
| Botnet stack absent from the profile, n = 150 | 1/30,000 | 2 | ≈ 1.2 × 10⁻⁵ | no, just above the cut |
| The same stack | 1/30,000 | 3 | ≈ 2 × 10⁻⁸ | yes |
| Benign tail fingerprint, n = 86 | 0.0016 + 1/30,000 | 4 | ≈ 1.4 × 10⁻⁵ | no |
| Benign fingerprint seen once, n = 86 | 1/30,000 | 1 | ≈ 2.9 × 10⁻³ | no |

All four pass the effect-size condition. Only the three-origin botnet stack is improbable enough.

### Why a test instead of a fixed support floor

A fixed share ignores the size of the sample it is applied to. Earlier revisions required
c(f)/n ≥ σ with σ = 0.002. On a cluster of 2,000 sessions that means at least four sessions, a
reasonable bar. In a five-minute window of 80 sessions it means less than one, so any tail
fingerprint seen once passes: its background share is tiny and its ratio huge. Measured per window,
the fixed floor selected a filter in every clean window and in every flash crowd, at a median
collateral of 12–18% (§7). The binomial test asks the same question with the sample size in it. One
occurrence is never significant, while a few origins of a fingerprint the background almost never
shows are. §6 and §7 record the change.

### The z-score, the unseen filter and their union

- **z-score:** z(f) = (c(f) − n·b(f)) / √(n·b(f)·(1 − b(f))). Uncalibrated, it selects every f with
  z > 3, as Table III does on generated traffic. Calibrated, its threshold meets the same budget as
  λ_e (section 7).
- **Unseen filter:** selects every fingerprint absent from the profile and seen in at least k_min
  origins. It is uncalibrated (III-C).
- **Union:** the binomial configuration joins the test with the unseen filter, which adds new
  stacks too small for the level (III-C).

The union costs few false alarms because the fleets that set λ_e present fingerprints the profile
already holds (`judge` in `rule_detection_production.py`). Fingerprints absent from the profile
appear daily but rarely concentrate. Only 0.21% of test-day windows hold one with at least k_min
origins, and no block window does (App. E). A software release that gives many legitimate clients a
new fingerprint would trip the unseen filter at once, and none was seen over the 23 days (VI).

The unseen filter cannot select shared stacks, which legitimate clients also present (V-A). On
generated traffic it matches or exceeds the test, because the generator's stacks never occur in
legitimate traffic (V-A, VI). The code also holds `zhist`, a z-score of each fingerprint against
its own calibration history, which the paper does not report (§12).

### What the scope cannot select

Attackers who use a common legitimate fingerprint may not enrich it enough to be selected, and the
scope then cannot tell them from normal clients (III-C). On generated traffic the test covers 30.4%
of such attackers at 3.78% collateral (Table III). On production, a botnet on the endpoint's 25
most common fingerprints is largely missed: the configuration blocks 7.0% of 100 attackers (V-B).
Section 8 gives the arithmetic, the enrichment limit. A bot with a different fingerprint on every
device also evades selection, and an alarm then mainly invokes the fallback (VI).

### Why the WAF's verdicts cannot validate the scope

The WAF's verdicts are the only malicious labels the production exports carry. A profile built
without the blocked clients makes the scopes agree with the WAF by construction, and with a profile
of all clients they agree less than a random pick (V-D). The WAF's populations are part of every
day's traffic, so a scope that reads deviations from that traffic does not see them.
[`metrics.md`](metrics.md#9-scores-against-the-waf) derives the condition and gives the scores,
and §16 has the runs.

## 7. Calibration

### The level λ_e

The binomial model treats each origin as an independent draw from the profile. Generated traffic
satisfies that: each origin carries one session, and λ_e stays at 0.01 in every scenario (III-C,
`symbolic_detector.json`). Production traffic does not, because legitimate client fleets become
active together, such as a probe fleet active only in business hours (App. E). At the nominal
level 0.01, the scope selects
a filter in 26.9% of clean production windows (App. E).

λ_e is therefore calibrated per endpoint, the way τ_cluster is:
1. over the endpoint's attack-free calibration windows with at least k_min origins, take each
   window's smallest Bonferroni-adjusted p-value among its enriched fingerprints (`min_adjusted_p`);
2. set λ_e to the 1st percentile of those values, capped at 0.01.

The scope then selects a filter in at most 1% of its calibration windows, the false-alarm budget
(III-C). No label is used. The generator path is `calibrate_level` in
[`evidence_mitigation.py`](../experiments/pillar4-evidence-mitigation/scripts/evidence_mitigation.py).
The production path is `evaluate_host` in `rule_detection_production.py`, which works in log
p-values.

On production the median level falls to between 10⁻⁴ and 10⁻⁷³ (Table V, §9). On E1 the fleets
push it to 10⁻⁶⁰ before known fleets are exempted (V-B). At such levels the binomial tail is
no longer a reliable probability. It serves as a score calibrated on observed traffic (III-C).

**Levels in logs.** Fleet counts and large botnets push p-values below the smallest double. A level
computed from p-values that underflow to 0 would be 0 and select nothing. `log_tail` in
`rule_detection_production.py` therefore sums the tail in logs (§15).

### The z-score threshold

The calibrated z-score's threshold is the 99th percentile, over the calibration windows, of each
window's largest z, and never below 3, the uncalibrated threshold. It meets the same budget (III-C;
`calibrate_baselines` in `rule_detection_production.py`). The calibrated z-score is a reference. It
was in the code before the held-out day was read, but outside that day's protocol (Table II), and
the block's protocol includes it (Table VII).

### Known fleets

Known fleets are the fingerprints the test selects at the nominal level 0.01 in at least 5% of an
endpoint's calibration windows (III-D; `known_fleets` in `rule_detection_production.py`). They are
exempted from the scope and from the level's calibration, so they work as an allow-list: the scope
never blocks attackers using them (III-D). On E1, five or six fingerprints qualify, and exempting
them raises λ_e from about 10⁻⁶⁰ to about 10⁻²¹ (V-B). E3 has up to two by test day, and E2 and E4
have none (`production_tables.json`, `floor.fleets`). Together these fingerprints carry up to about
7% of their profiles (III-D). Under the beta-binomial, none qualifies in sample
(`production_tables.json`, `floor.od_fleets`; App. E).

The 5% share was chosen on the test days ([`evaluation.md`](evaluation.md#what-was-fixed-when)
gives the choice; `fleet_profile.json`, §11).

### The beta-binomial background

Fleets make a fingerprint's count overdispersed: its variance across windows exceeds n·b·(1 − b).
The **beta-binomial background**, developed after the held-out day was examined, models that
correlation within windows (III-D). For each profile fingerprint, the intra-window correlation φ(f)
is estimated by moments over the calibration windows with at least k_min origins, from

    Var[c(f)] = n · b · (1 − b) · (1 + (n − 1) · φ)

which gives, summed over those windows w,

    φ(f) = Σ_w [(c_w − n_w·b)² − n_w·b·(1 − b)] / Σ_w [n_w·(n_w − 1)·b·(1 − b)]

clipped to [0, 0.99] (`intra_window_correlation` in `rule_detection_production.py`, option
`--overdispersion`). Counts are then tested against a beta-binomial with the same mean. Fingerprints
absent from the profile stay binomial, since there is nothing to estimate φ from, and λ_e is
calibrated as before (III-D).

A fleet's surge now falls within what the background expects, so the calibrated level rises. In
sample it reaches about 10⁻⁴ on E1 and the 0.01 cap on the three smaller endpoints (Table V). Three
origins then select a new stack on E1, and two on the others (`production_tables.json`,
`floor.od`). The shared-stack floor falls on the three largest endpoints (V-D, Table V). For a rare
stack even a small φ matters. It adds b·(1 − b)·φ to the variance of the stack's per-window
probability, which rivals b² when b is small. On E4 a median φ of about 3 × 10⁻⁴ raises the shared
floor from 56 to 84 attackers (`floor_bands.json`). In sample, the price is more false alarms
(V-D, Table IV).

### Cross-fitting

In sample, each calibration day is judged against a profile that includes its own traffic, so its
fleets look less enriched (IV-B). **Cross-fitting**, introduced post hoc, judges each calibration
day against a profile, and a φ, built from the other calibration days, as a test day is judged
against days it is not part of. It applies when λ_e, the z-score threshold and the known fleets are
fitted. τ_cluster, the distinct-origin gate and the test day's own profile stay as in sample (IV-B;
option `--split crossfit` in `rule_detection_production.py`). Under cross-fitting the
beta-binomial's levels fall to between 10⁻¹⁷ and 10⁻² (App. E).
[`evaluation.md`](evaluation.md#calibration-splits) gives the design's history.

### What the budget promises

The budget holds on the calibration windows by construction (III-C). On later days it is a target,
and the rates there are measured ([`metrics.md`](metrics.md#5-false-alarms); section 10).

### How the parts combine

A configuration joins a trigger (section 5), a scope (section 6) and a background (this section),
with or without known fleets. [`evaluation.md`](evaluation.md#5-configurations-and-baselines)
lists the configurations of Table II and the block's six, says when each was fixed, and names the
current candidate.

## 8. The calibration floor and the enrichment limit

**Definition.** Calibration limits false alarms and also raises the smallest attack the scope can
select (III-D). The **calibration floor** is the botnet size from which the scope selects a typical
stack. For a stack with c attackers among n origins, the test requires

    c / n ≥ ρ · b(f)   and   P[Bin(n, b(f)) ≥ c] < λ_e / |F|

The floor is the smallest A for which a stack of 0.9·A/M attackers passes both in a window of
n₀ + A origins, with n₀ the median calibration window (III-D). Stricter levels raise it. Table V
gives the floor in attackers per window. The text also gives it as a share of n₀ (8% on E1) or in
median windows (4 to 19) (V-B). It can be computed before any attack, from the level, the profile
and n₀ (`floor` in `production_tables.py`).

**A hypothetical endpoint** shows the mechanism for a new stack (b = 1/N). It has 2,000 origins per
window, a profile of N = 200,000 origin–fingerprint pairs and |F| = 300, with M = 25. The values
follow from the definition above:

| λ_e | Smallest selectable count per stack | Smallest botnet A | Floor, share of n₀ |
|---|---|---|---|
| 10⁻² | 3 | 84 | 4% |
| 10⁻²¹ | 10 | 278 | 14% |
| 10⁻⁶⁰ | 22 | 612 | 31% |

**New stacks.** In the union, the unseen filter selects a stack absent from the profile once it
holds k_min origins, whatever the level. That takes ⌈k_min · M / 0.9⌉ attackers: 139 for M = 25, 28
for M = 5 and 556 for M = 100 (III-D). The test alone needs more on E1. At 10⁻⁶⁰ it selects a new
stack only past 15 to 18 origins, about 16% of the median window, and with known fleets past 7 or 8,
about 7% (App. E; `production_tables.json`, `floor.base` and `floor.fleets`). With the unseen filter,
the binomial configuration's new-stack floor is 139 attackers on E1–E3. On E4 it is 84, since the
test selects stacks first there (V-B, Table V).

**Shared stacks.** For stacks drawn from the profile's tail beyond its ten most common
fingerprints, the unseen filter selects nothing. The calibrated level sets the floor, computed at
the tail's median share (V-B). A typical stack then needs 254 attackers on E1, 8% of its median
window, and 4 to 19 median windows on the smaller endpoints, as medians of daily ratios (V-B,
Table V). The floor grows with the number of stacks, from 2% of E1's median window at five stacks to
34% at 100. It also grows with fingerprint popularity: ranks 11–35 are never selected on the two
largest endpoints (V-B, App. E; `floor_bands.json`).

**The floor is a ramp.** It marks where the *mean* stack, 0.9·A/M, reaches c_min, the smallest
count the scope selects: the smaller of k_min and the test's smallest selectable count at the fold's
level. Stack sizes vary around that mean. An attacker sits on a stack with probability 0.9, and its
stack then holds it and Bin(A − 1, 0.9/M) others. The share of a new-stack botnet that the scope
alone selects is therefore

    0.9 · P[Bin(A − 1, 0.9/M) ≥ c_min − 1]

(`model_new` in `production_tables.py`). On E1, with c_min = 5 and M = 25, that gives 9%, 43%, 66%
and 88% at 50, 100, 139 and 250 attackers. The injected botnets give 8.5%, 43.2% and 88.3% at 50, 100
and 250 (`production_tables.json`, `sweep`; V-B, Fig. 2). Below the floor, chance still leaves some
stacks large enough to be selected (V-B).

**The enrichment limit.** However large the botnet, one of its stacks holds at most a share 0.9/M
of the window. The effect condition c/n ≥ ρ·b is therefore not expected to hold for any fingerprint
with

    b > 0.9 / (ρ · M)

which is 1.2% for M = 25 and 6% for M = 5 (III-D). On the four production endpoints, the 4 to 28
most common fingerprints exceed it, and they carry 86–94% of the origins (V-B, `floor_bands.json`).
A bot hiding behind one of them is not expected to be selected. Selection there is unlikely, and it
still happens where few fingerprints exceed the limit. On single sign-on, where only four or five
do, the configuration blocks 73.5% of 1,000 attackers on the endpoint's 25 most common fingerprints
(V-B).

**What the floor means for an operator.** The floor is a planning quantity. Above it, the scope can
act as a fingerprint filter. Below it, the operator needs the fallback. Whether an attack near the
floor exhausts a service depends on the service's spare capacity, which the paper did not measure
(VI).

## 9. From the ontology to the log-store query

**Annotations.** Each equality sub-relation carries a `kg:classKey`, the session property it
equates: `kg:tlsJa4`, `kg:targets` or `kg:srcPrefix`. `relatedTo` carries a `kg:countUnit`,
`kg:originatesFrom`, so classes are counted in origins (III-E). The three sub-relations without a
class key are not equivalences and need pairwise evaluation ([`runtime.md`](runtime.md)).

**The compiler.** `compile_counts.py` turns those annotations and a binding of properties to
columns into the SQL a log store runs. The query returns, per endpoint and window, the class sizes
the gate, the base rule and the scope read (III-E). An example binding, with placeholders only, is in
[`experiments/sprint-6-noms/bindings/`](../experiments/sprint-6-noms/bindings/). The operator's own
binding stays with its data.

**What was checked.**
- On 6,000 generated sessions from 3,871 origins, the compiled query reproduces `decompose_omega`
  exactly (`compile_check.json`, `make compile-check`).
- Adding a sub-relation (same User-Agent) to a copy of the ontology takes four triples and no change
  to the query-generation code, and the recompiled query carries it (`compile_check.json`). A new
  session property also needs a column binding (III-E).
- In the operator's log store, the compiled query reproduced the exported address and /24-pair
  counts in every window of two production days, 1,152 windows each. It reproduced the JA4 pair
  counts in the 288 windows of each day on the endpoint where the WAF blocked no client (App. F;
  `compile_production_check.json`, `compile_production_check_fresh.json`). Elsewhere the export
  drops clients the WAF blocked in part, which the compiled query keeps.
- The protocol named JA4 class sizes, and the check compared their pair counts. Pair counts
  constrain the per-fingerprint counts the scope tests but do not identify them (App. F).

**Weights.** The scripts that compute Ω read every `coordinationWeight` from the ontology through
[`experiments/common/kg_ontology.py`](../experiments/common/kg_ontology.py). One diagnostic in
`production_summary.py`, the share of Ω outside the endpoint term, repeats the endpoint weight 0.6
as a constant.

**The evidence chain.** When the rule fires, the chain records the rule, the cluster, the scope and
the split of Ω(S) by sub-relation. It is exported as JSON-LD over the ontology's vocabulary
(Listing 1, App. D) and as STIX 2.1, an `indicator` and a `course-of-action` linked by `mitigates`
(III-E). The bundles pass the OASIS STIX 2.1 validator in strict mode (`stix_validation.json`). The
reference TAXII 2.1 server returns them unchanged except for the extension definition it fails to
serve, and MISP's importer drops the fingerprints (App. F, `stix_ingest.json`).
[`prior-art.md`](prior-art.md) says what the exchange standards can and cannot carry.

**The reference form of the rule.**
[`experiments/pillar2-symbolic-reasoning/`](../experiments/pillar2-symbolic-reasoning/) keeps the
rule as SWRL for the pairwise sub-relations and SPARQL for the weighted sum, as a demonstration. The
evaluation reads the compiled count query. [`runtime.md`](runtime.md) has the cost of both paths.

## 10. Results in brief

The results in prose, the 14-day block included, are in
[`experiments/FINDINGS.md`](../experiments/FINDINGS.md). Each row below points into the paper.

| Question | In brief | Where |
|---|---|---|
| Does the alarm's most common fingerprint make a good filter? | Only while one stack dominates. It covers 89.8% of attackers at one stack, and from five stacks on it covers 0.0% and blocks 39.0% of legitimate traffic. | V-A, Table III |
| Does profile-relative scoping work? | On generated campaigns the test covers 90.0% of attackers at five stacks and 90.3% at 25, with no observed collateral, and 85.4% of shared stacks at 2.23% collateral. | V-A, Table III |
| Would a learned model do better? | It needs campaign labels, and it does not transfer: trained on five stacks, configuration (d) falls to an AUC of 0.61 and 0.63 on 25 and 100. | V-A, App. C |
| How often does the binomial configuration misfire? | In 0.1% of the test days' clean windows (5 of 5,643), though its scope alone (2.2%) and its gate alone (3.0%) each exceed the 1% budget. Its misfires block a median 32.9% of their windows' clients. | V-B, Table IV |
| What can the scope select? | New stacks from 139 attackers per window on E1–E3 and 84 on E4. Shared stacks from 254 on E1 (8% of its median window) and from 4 to 19 median windows on the smaller endpoints. | V-B, Table V |
| What does it block? | On E1 the gate opens in 6–13% of small botnets' windows, so the configuration blocks 11.8% of a tenth-size botnet that its scope alone would cover at 89.6%. | V-C, Table VI, Fig. 2 |
| Do the rates hold on later days? | The held-out day gave 2 misfires in 1,152 clean windows. The 14-day block (2026-09-26 to 10-09) gave 31 in 16,103 (0.19%), about twice the test days' 0.1% and inconsistent with them by the protocol's test, though within the 1% budget. | V-D, Table VII |
| What is the current candidate? | The cross-fitted beta-binomial behind the seasonal gate, with the fallback below its floor. Built post hoc and fixed before the block, it misfired 20 times there (0.12%, 14 on E1). On E1 the unseen filter with no gate kept 89.6% coverage with no false alarm, while the binomial scope with known fleets and no gate exceeded the budget (1.56%). Running the candidate and the unseen filter together on E1 is untested. | V-D, VI, Table VII |
| Can the WAF's verdicts serve as labels? | No. A profile without the blocked clients makes the scopes reproduce the WAF by construction ([`metrics.md`](metrics.md#9-scores-against-the-waf)). | V-D |

## 11. Positioning

How the paper places itself against related work, and what the exchange standards examined can and
cannot carry, is in [`prior-art.md`](prior-art.md).
