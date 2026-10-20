# Evaluation design

How the paper's claims are tested, and what each traffic source can and cannot establish.
Pointers such as (IV-A) or (Table II) refer to the paper,
[`article.tex`](../papers/http-session-noms/article.tex). The method (the trigger, the test,
calibration and the floor) is defined in [`concepts.md`](concepts.md), and every metric and
statistical test in [`metrics.md`](metrics.md). Results in prose are in
[`FINDINGS.md`](../experiments/FINDINGS.md). File names without a path are in
[`experiments/sprint-6-noms/results/`](../experiments/sprint-6-noms/results/).

1. [The question and its two axes](#1-the-question-and-its-two-axes)
2. [Generated traffic](#2-generated-traffic)
3. [Laboratory captures and the benchmark gap](#3-laboratory-captures-and-the-benchmark-gap)
4. [Production traffic](#4-production-traffic)
5. [Configurations and baselines](#5-configurations-and-baselines)
6. [The held-out day protocol](#6-the-held-out-day-protocol)
7. [The 14-day block protocol](#7-the-14-day-block-protocol)
8. [What each evaluation establishes](#8-what-each-evaluation-establishes)
9. [Where results live](#9-where-results-live)

## 1. The question and its two axes

The evaluation asks when a TLS-fingerprint filter can stop a low-rate distributed attack
without excessive collateral, and when it cannot (I). Two axes organize it:

- **K, the degree of distribution**: the number of devices the attacker controls. It sets how
  much per-session signal is left.
- **M, the number of TLS stacks** the botnet spans. It sets whether the alarm's most common
  (modal) fingerprint or a profile-relative scope selects the botnet.

### The K axis

| K | What it models | In the paper |
|---|---|---|
| 1 | A classic single-source attack | Not evaluated: the paper studies attacks spread over many sources (I) |
| 10–100 | A small botnet whose origins each stay below their own rate limit | K = 50 |
| ≥ 1000 | A botnet across hundreds of /24 prefixes, with almost no per-session signal. The generator draws each attacker's /24 from a pool of 2,000 and its ASN from 12 values, and no scope reads the ASN | K = 1000 |

In stealth mode, per-session features sit at chance at both reported sizes, so only
cross-session structure separates the campaign (App. C). On a window, Ω is then mostly
volume: its endpoint term gives 91% of the score in the default campaign, and the scope is
what sets the attack apart (III-B; [`concepts.md`](concepts.md#4-coordination-mass-and-the-weights)).

### The M axis

No published measurement shows how botnets are distributed across TLS stacks, so M is varied
(IV-A). Generated campaigns use M = 1, 5, 25 and 100, with M = 25 by default (Table III).
Spreading attackers uniformly at random is the hardest case in expectation for selecting a
stack at a given M (IV-A).

M is the axis that breaks the modal scope. The modal fingerprint belongs to the attack only
while each stack holds more attackers than the most common legitimate fingerprint holds
legitimate origins. At the measured head (38.4% of requests) and with a campaign as large as
legitimate traffic, that holds only for M < 2.3 (III-C; the derivation is in
[`concepts.md`](concepts.md#why-the-modal-fingerprint-fails)). From five stacks onward the modal fingerprint is a legitimate
one (Table III).

M also sets how small a stack the scope must select. At M = 100 each stack holds about ten
attackers, too few to stand out against a 1,000-session profile. The binomial test then covers
38.6% of attackers, and a profile pooled over 30 attack-free periods restores 89.6% (V-A;
`profile_drift_m100.json`). Profile size therefore governs the smallest stack the test can
select.

## 2. Generated traffic

A generator produces controlled, distributed Slow HTTP DoS campaigns against one endpoint,
with known ground truth. It is calibrated on benign CICIDS2017 sessions and on JA4
fingerprints measured at a CDN (IV, IV-A).

### Why the Slow HTTP DoS family

- **It is low-rate.** In the threat model, each session holds a connection and a worker as
  legitimate traffic does, so no per-session rate rises (III-A).
- **It can run over HTTPS**, where a JA4 fingerprint is observable at every handshake.
- **Public captures cover it**: CICIDS2017 (Slowloris, Slowhttptest, HULK, GoldenEye) and
  CIC-IoT2023 (DDoS Slowloris, HTTP Flood) (App. C).
- **It instantiates the ontology's `CoordinatedHTTPFlood` class.** K = 1 is the classic
  single-source attack, and a large K the distributed one.

High-volume attacks are the contrast. HTTP/2 Rapid Reset (CVE-2023-44487) reached 398 million
requests per second (I). HTTP/2 needs sub-relations beyond the HTTP/1.1 family evaluated here,
and it is future work (App. C, VII).

### Inputs

| Input | Value | Source |
|---|---|---|
| Legitimate fingerprint popularity | Zipf with exponent α: 1.5 by default, 2.0 as a variant | 6.33M TLS requests at one production edge point of presence: 495 fingerprints, the most common carrying 38.4% of requests and the top ten 93.8%. The head fits α = 1.5, the top ten α = 2.0 (IV-A). |
| Benign fingerprint pool | 2,000 fingerprints | It follows the Zipf shape of the 495 measured, and exceeds the 76–1,163 seen per production endpoint (App. B). |
| Request counts | All 322,658 benign CICIDS2017 sessions | App. B |
| Durations | The 40,351 benign sessions with two or more requests | App. B |
| Botnet stacks | 90% of attackers uniformly at random over M stacks, the rest on one-off fingerprints | IV-A |

Popularity is measured per request, which if anything overstates concentration (App. B). The
Kolmogorov–Smirnov distances between generated and source sessions, D = 0.002 and 0.003, check
only the sampler ([`metrics.md`](metrics.md#10-other-tests)).

### Modes

- **Stealth.** Attacker sessions draw from the same per-session distributions as legitimate
  ones, so only cross-session structure reveals the campaign.
- **New stacks** (the default). The botnet's stacks never occur in legitimate traffic.
- **Shared stacks.** Stacks come from the profile's tail, which legitimate clients also
  present.
- **Adversarial stacks.** Attackers use the most common legitimate fingerprints, as
  browser-imitating bots might. This lies outside the threat model and tests its boundary
  (III-A).

### Timing and windows

Attackers start within the first 30 s. A campaign therefore holds a median 34–45% of the
origins in the windows it overlaps, and 50% of the alarm's cluster. The cluster chains an
endpoint's sessions while consecutive starts stay within 300 s of one another (IV-A). This
regime is easier than the tenth-size production injections, where the production gate mostly
fails (VI).

The rule also runs as deployed, per 300 s window and endpoint (App. E):

- τ_cluster is the 99th percentile of Ω over the windows of 30 attack-free runs, which also
  form the profile.
- False alarms are counted on 30 more runs.
- Detection is counted on default campaigns (α = 1.5, M = 25), over windows with at least
  k_min = 5 attackers.
- A flash crowd retimes 25, 50 or 100 legitimate sessions from a third run into one window.
- Benign starts are spread over 60 min, since the generator otherwise packs them early.

### Profiles and seeds

The profile variants are matched, drifted to α = 2.0 and flat, plus one pooled over 30
attack-free periods for M = 100 (V-A; `profile_drift.json` and `profile_drift_m100.json`, from
[`profile_drift.py`](../experiments/sprint-6-noms/scripts/profile_drift.py)). Table III uses 15
seeds. The ablation and the academic baselines use 30 (App. C).

## 3. Laboratory captures and the benchmark gap

CICIDS2017 (Slowloris, Slowhttptest, HULK, GoldenEye) and CIC-IoT2023 (DDoS Slowloris, HTTP
Flood) run through the same extraction pipeline: PCAP → JA4 + flows → sessions (App. C).
KLAGE reports F₁ = 0.841 on CIC-IoT2023 DDoS Slowloris.

On that capture, the attack clusters contain seven origins in one of 143 /24 prefixes. A
strong per-session baseline using nine flow attributes reaches F₁ = 0.900 (AUC 0.987). Three
of those attributes plus cross-session evidence reach 0.911 (AUC 0.982). Real Slowloris,
unlike the stealthy campaigns, leaves a per-session flow signature (App. C).

The comparison with KLAGE is **uncontrolled**. The strong baseline also exceeds the published
0.841. KLAGE's released code starts from a graph of unpublished construction and provides no
weights, which prevents a controlled rerun (App. C; [`sprint-5/`](../experiments/sprint-5/)).

**The benchmark gap.** The paper found no independent capture of the stealthy regime.
BCCC-cPacket-Cloud-DDoS-2024 criticizes the application-layer coverage of earlier datasets and
provides 17 TCP-based DDoS scenarios (App. C). Captured stealthy campaigns are future work
(VII).

## 4. Production traffic

### Endpoints and exports

- **Endpoints.** Four endpoints of the CDN operator's own services: real-user monitoring
  beacons (E1), a web console (E2), an API (E3) and single sign-on (E4). Their median windows
  hold about 3,000, 62, 41 and 20 origins. Of 12 exported endpoints, these are the four with
  TLS, at least 50 calibration windows and a median window of at least k_min origins (IV-A).
- **Exports.** Counts only: distinct origins and connections per fingerprint and window, and
  same-/24 pairs per window (IV-A). They hold no prefixes, so the scope is judged on JA4 alone
  (App. E). The exports stay with the operator's data, and only counts and rates enter the
  repository (App. F).
- **Behind the WAF.** The scope is evaluated offline behind the operator's WAF, so profiles and
  floors describe the clients the WAF lets through (IV-A). The WAF's verdicts are the only
  malicious labels the exports carry. They are scored with
  [`waf_labels.py`](../experiments/sprint-6-noms/scripts/waf_labels.py)
  ([`metrics.md`](metrics.md#9-scores-against-the-waf)).

### Days

| Days | Count | Role |
|---|---|---|
| Initial days | 8 | Rolling split. Each of the last five, the test days, is tested with the profile, thresholds and levels of the days before it (IV-A). |
| Held-out day | 1 | The next day, analyzed with the configuration fixed in advance ([§6](#6-the-held-out-day-protocol)) |
| The block | 14 | The 14 days after the held-out day, each calibrated on all earlier days ([§7](#7-the-14-day-block-protocol)) |

That makes 23 days. The two protocols give the dates.

### Assumptions

- Calibration days are assumed attack-free. An attack there would lower the test's level and
  raise the gate's threshold, making both more cautious (IV-A).
- Pre-injection test windows are treated as clean, so a real attack there would count as a
  false alarm (IV-A).

### Injections and flash crowds

Generated botnets are added to the counts of each test window (IV-A):

- **Sizes.** 25 to 1,000 attackers per window, or from a tenth of the endpoint's median window
  (*tenth-size*) to all of it.
- **Structure.** 90% of attackers uniformly at random on 25 stacks, and the rest on one-off
  fingerprints that no scope selects, so at most about 90% can be blocked.
- **Stacks.** New (absent from the traffic), shared (from the profile's tail beyond its ten most
  common fingerprints) or adversarial (the endpoint's 25 most common).

The artifact also injects 5- and 100-stack botnets (`sweep` in `production_tables.json`). A
flash crowd adds 100 or 1,000 of the day's own clients to one window (IV-A).

### Calibration splits

Every production configuration runs **in sample** and **cross-fitted**, both defined in
[`concepts.md`](concepts.md#cross-fitting). Cross-fitting was introduced post hoc (`--split
crossfit` in
[`rule_detection_production.py`](../experiments/sprint-6-noms/scripts/rule_detection_production.py)).
A first design, calibrated only on the last calibration day, was dropped after its results were
seen, because one day misses the rare fleet events that set the level (V-D).

### What was fixed when

| When | What was fixed | Pointer |
|---|---|---|
| On generated traffic, before any production data were examined | ρ = 3, k_min = 5, the 99th percentile for τ_cluster, and the 25-stack botnet | IV-B |
| On the test days | Counting origins, calibrating λₑ, the distinct-origin gate, the union with the unseen filter, and the 5% fleet share, chosen on the first three test days by false-alarm count | IV-B, App. E; `fleet_profile.json` |
| Before the held-out day was read | The binomial configuration as primary, the base rule as reference, seven metrics and the primary's decision rule | [§6](#6-the-held-out-day-protocol); `fresh_day_protocol.md` |
| After the held-out day was read (post hoc) | The beta-binomial background, cross-fitting, the seasonal gate, and the scope as its own trigger. The calibrated z-score was in the code before, outside the protocol | Table II note, V-C, V-D; `fresh_day_protocol_addendum.md` |
| Before any block day was exported | The block's six configurations, its parameters, the injection, metrics 1–7 and their decision rules | [§7](#7-the-14-day-block-protocol); `heldout_block_protocol.md` |
| After the block's protocol, before any block count was read | Metrics 8–10; metric 7's amended rule; the export hashes of all three parts; the run from commit `05ccc0e` | [§7](#the-addendum-on-metrics); `heldout_block_protocol_addendum_metrics.md`, `heldout_block_addendum_hashes.md` |

The counts behind the 5% fleet share are in
[`FINDINGS.md`](../experiments/FINDINGS.md#calibration).

## 5. Configurations and baselines

### On generated traffic

Four scopes, each applied to the alarm's cluster (IV-B). Their definitions are in
[`concepts.md`](concepts.md#6-the-scope).

| Scope | Selects |
|---|---|
| Modal fingerprint | The cluster's most common fingerprint |
| Unseen filter | Fingerprints absent from the profile and seen in at least k_min origins |
| z-score | Fingerprints with z > 3 against their binomial background |
| Binomial test | Fingerprints both enriched and unlikely, at level λₑ = 0.01 |

**The learned baseline** is a Random Forest trained on campaign labels, with cross-session
evidence from the three sub-relations: configuration (d) of the ablation below. It is held to
zero false positives, which the test also achieves wherever the learned model is evaluated,
except in the adversarial case (IV-B). A second model, "+ profile", adds log b(f) and log
enrichment per session (V-A). Both train on labels from the campaign they score, which an
operator does not have during an attack. They were not run on shared stacks (Table III).

**The ablation** (App. C) compares representations of the same traffic attributes. Each
configuration runs on 30 seeds, with each campaign split 70/30 into training and test
sessions. Comparisons are paired across seeds
([`metrics.md`](metrics.md#10-other-tests)).

| | Configuration |
|---|---|
| (a) | The nine per-session flow attributes in a Random Forest, repeated with gradient boosting, a multilayer perceptron and logistic regression |
| (b) | Adds per-session ontological attributes |
| (c) | Adds only network proximity |
| (d) | Adds cross-session evidence from the three sub-relations: the share of the cluster sharing one JA4 or /24, plus its size |

(d) − (a) measures what cross-session evidence adds to per-session features. (d) − (c)
measures what the fingerprint and endpoint evidence add to network proximity alone. (d)
computes its cross-session evidence as features, without querying the RDF graph, so the
configurations differ only in representation. The scopes themselves are evaluated as
detectors in Table III.

**Cross-M tests** train on campaigns with one M and test on another, on disjoint seeds. The
generator draws every benign session before any M-dependent step, so a same-seed split would
let (a) score 0.88–0.94 by memorization (App. C; `cross_m_generalization.json`).

**Academic baselines**, reimplemented on the same scenarios (App. C; `canonical_baselines.json`):

- PCA profiling, after Fernandes et al.;
- PCA with k-means over a behavioral matrix, after Bharathi et al., with a per-cluster
  threshold in the code (`bharathi2012_pca` in
  [`baselines.py`](../experiments/sprint-3/scripts/baselines.py));
- a supervised RF/SVM over session features, after Kemp et al.

### On production traffic: Table II

Thresholds, levels and known fleets are estimated from attack-free days (IV-B).

| Configuration | Gate | Scope | Background | Exempt | Chosen | Held-out day |
|---|---|---|---|---|---|---|
| Base rule | Ω ≥ τ | test | binomial | none | test days | in the protocol, as reference |
| Binomial | distinct origins | test ∪ unseen | binomial | known fleets | test days | in the protocol |
| z-score | distinct origins | z above its p99 | binomial | none | test days | in the code before the day was read, outside the protocol |
| Beta-binomial | distinct origins | test ∪ unseen | beta-binomial | none | post hoc | post hoc |

The **binomial configuration** is the pre-specified one: the held-out day's protocol fixed it,
and it is the block's primary configuration. The **base rule** is the protocols' reference.

The **current candidate** is the cross-fitted beta-binomial behind the seasonal gate. Below its
floor, the fallback acts: a rate limit or a challenge to every client. The candidate was built
post hoc and fixed before the block, where the pre-specified comparison preferred it to the
unseen filter on every endpoint (VI).

The triggers behind these configurations, the distinct-origin gate, the Ω gate, the post hoc
seasonal gate and no gate, are defined in [`concepts.md`](concepts.md#5-the-triggers).

### On the block: six configurations

| # | Trigger | Scope | Role in the protocol |
|---|---|---|---|
| 1 | Distinct-origin gate | The binomial configuration's (test ∪ unseen, known fleets) | Primary |
| 2 | Ω gate | Test | Reference: the base rule |
| 3 | No gate | Unseen filter | Baseline of the comparison |
| 4 | Seasonal gate | Cross-fitted beta-binomial (test ∪ unseen) | Arm |
| 5 | No gate | Binomial with known fleets, on E1 only | Arm |
| 6 | Distinct-origin gate | Calibrated z-score | Reference |

Sources: `configs` in `block_report.json`, and
[`heldout_block_protocol.md`](../experiments/sprint-6-noms/results/heldout_block_protocol.md).
Table VII prints the rows in another order.

## 6. The held-out day protocol

- **Written before the day was read**, with the SHA-256 of the day's exports
  ([`fresh_day_protocol.md`](../experiments/sprint-6-noms/results/fresh_day_protocol.md)). The
  exports had been opened only to check their columns and row counts. The protocol was
  committed 17 hours after its stated time, so no external timestamp attests that order
  (App. F).
- **The day.** The day after the eight initial days, for the same four endpoints.
- **Frozen configuration.** The binomial configuration, calibrated on every earlier day, with
  origins as the unit, k_min = 5, W = 300 s, ρ = 3, the 1% budget with λₑ capped at 0.01, and
  known fleets at 5%. Injections and flash crowds follow the test days.
- **Metrics,** each reported whatever its value:
  1. primary: the clean-window false alarms, pooled, with a consistency test against the
     test-day rate;
  2. the median share of a false-alarm window's clients that the filter blocks;
  3. the firing rate under 100-user flash crowds;
  4. the blocked share of the injected botnets, pooled;
  5. E1's tenth-size botnet, on new and shared stacks;
  6. the same metrics for the base rule, as reference;
  7. the agreement of the compiled count query with the exports.
- **Outside the protocol.** The calibrated z-score was in the code before the day was read, but
  the protocol does not name it. The beta-binomial was built after the day was read, so its
  row is post hoc
  ([`fresh_day_protocol_addendum.md`](../experiments/sprint-6-noms/results/fresh_day_protocol_addendum.md)).
- **Where each metric is now.** The day is reported apart and never pooled with the test days
  ([`fresh_day_metrics_location.md`](../experiments/sprint-6-noms/results/fresh_day_metrics_location.md)).

The test, its power and the post hoc test conditional on the gate are in
[`metrics.md`](metrics.md#the-held-out-day).

## 7. The 14-day block protocol

- **Fixed before export.**
  [`heldout_block_protocol.md`](../experiments/sprint-6-noms/results/heldout_block_protocol.md)
  was pushed publicly before any block day was exported, and its push time on GitHub is its
  external timestamp. The export hashes were published before any result was computed
  ([`heldout_block_addendum_hashes.md`](../experiments/sprint-6-noms/results/heldout_block_addendum_hashes.md)).
  A few rows of raw counts were seen on screen at export (App. F).
- **Days and endpoints.** The 14 days after the held-out day: two full weeks, so every weekday
  appears twice. The same four endpoints, taken from the paper's own run, with no new endpoint
  selection.
- **Calibration.** The paper's nine days are history only. Every block day is a test day,
  calibrated on all earlier days (the rolling split, `--min-calib-days 9`). Cross-fitted runs
  use `--split crossfit`.
- **Export.** The log store keeps 8 to 12 days, so the block was exported in three parts, each
  within a week of its first day. The run required at least 7 test days, and all 14 were
  available (`enough_days` in `block_report.json`).
- **Frozen code.** The block ran from a checkout of commit `05ccc0e`, the commit that added the
  protocol. The report script,
  [`block_report.py`](../experiments/sprint-6-noms/scripts/block_report.py), came later. Before
  any block count was read, `make block-report-check` ran it on the paper's own days, and it
  reproduced the paper's numbers (21 checks).
- **Parameters, as in the paper.** Origins as the unit, k_min = 5, W = 300 s, ρ = 3, the gates
  at their 99th percentile, λₑ calibrated to the 1% budget and capped at 0.01, and known fleets
  at a 5% share. Injections and flash crowds follow the test days.
- **Configurations.** The six of [§5](#on-the-block-six-configurations).
- **Nothing is tuned on the block.** Once a block day is read, the protocol does not change,
  whatever the results.

### The ten metrics

| # | Metric | Decision |
|---|---|---|
| 1 | Primary A: the binomial configuration's false alarms, pooled | Consistency test against the test-day rate |
| 2 | Primary B: the budget of configurations 3 to 5, per endpoint | Within the budget, and shown within it by the exact interval |
| 3 | Blocked share of the injected botnets, for every configuration | Descriptive |
| 4 | Flash crowds of 100 and 1,000 users: firing rate and median share blocked | Descriptive |
| 5 | Cost of a false alarm: the median share of the window's clients blocked | Descriptive |
| 6 | False alarms per day and endpoint | Descriptive |
| 7 | The comparison VI asks for: baseline 3 against arms 4 and 5, per endpoint | An arm is preferred where it is within the budget and stops more |
| 8 | The scope's reliability once the gate opens | Consistency test against the test days' 5 misfires in 168 openings |
| 9 | Weekly cycle: false alarms on weekdays and on weekend days | Descriptive |
| 10 | Fingerprint churn: fingerprints absent from the profile that reach k_min origins | Descriptive |

Every metric is reported whatever its value. The tests and their outcomes are in
[`metrics.md`](metrics.md#the-14-day-block).

### The addendum on metrics

[`heldout_block_protocol_addendum_metrics.md`](../experiments/sprint-6-noms/results/heldout_block_protocol_addendum_metrics.md)
was written before the first part was exported, and pushed after that export and before any
block count was read. It adds metrics 8 to 10 and amends one decision rule, metric 7's.

As written, metric 7 compared the arms on a tenth-size botnet that no scope can select on the
small endpoints: there it holds 2 to 7 attackers, fewer than the botnet's 25 stacks. The
amended rule compares E1's tenth-size botnet and 100 attackers on E2–E4. It prefers an arm on
an endpoint only if the arm is within the budget there and stops at least one point more than
the baseline on new or shared stacks. The amendment was fixed on the paper's test days, and
adopted after the export and before any result was computed. Both versions are reported, the
amended one decides, and the verdict is the same under both (App. F; `m7` in
`block_report.json`).

## 8. What each evaluation establishes

| Source | Establishes | Does not establish |
|---|---|---|
| Generated traffic | The selection mechanism, under mimicry imposed by design | Field performance. Its campaigns, a third to half of the origins in the windows they overlap, are easier than the tenth-size production injections. Its new stacks never occur in legitimate traffic, which is why the unseen filter matches the test there (VI). |
| Laboratory captures | That the pipeline works on real captures; an uncontrolled comparison point with KLAGE | The stealthy distributed regime. Both are laboratory testbed captures. They cannot test the scope either: the captures are largely non-TLS, and their attack clusters hold one to seven origins ([`FINDINGS.md`](../experiments/FINDINGS.md)). |
| Production traffic | False alarms on real clients, per endpoint and day; the floor that fleets impose; how a calibration holds on later days, through the held-out day and a pre-specified 14-day test of six configurations (Table VII); that this WAF's verdicts cannot serve as labels | Detection of a real flood. Coverage holds only for injected botnets with a fixed 25-stack structure: new stacks, mostly rare shared stacks, or the endpoint's most common fingerprints (VI). |

Further limits (VI, App. C):

- The 23 days cover one operator's own endpoints, too few to calibrate a weekly cycle.
- The five choices made on the test days are evaluated prospectively only by the held-out day
  and the block. Cross-fitting removes the in-sample fitting of calibration levels but does not
  undo earlier configuration choices.
- No later day has tested the current candidate. The next step is a longer evaluation.
- On E1, running the candidate together with the unseen filter without a gate is untested.
- Flash crowds concentrated on a single client type, and attackers that manipulate the profile
  or the fleet exemptions, were not injected.
- Whether an attack near the floor exhausts a service depends on its spare capacity, which was
  not measured.
- Counting origins by source address undercounts users behind carrier-grade NAT, and
  overcounts clients rotating IPv6 privacy addresses, whose natural unit is the /64.
- The production run is offline, over counts per endpoint. A live deployment still needs the
  partitioning of App. D, which is not implemented.

**Artifact only.**
[`qualitative_evidence.py`](../experiments/pillar4-evidence-mitigation/scripts/qualitative_evidence.py)
checks evidence chains for completeness and actionability on the laboratory captures, with the
modal scope. The paper does not report it, and no user study was run.

## 9. Where results live

The map from each table, figure and listing of the paper to its script and result file is in the
root [`README.md`](../README.md#figures-tables-and-listings), and the Sprint 6 README adds each
file's make target
([`experiments/sprint-6-noms/README.md`](../experiments/sprint-6-noms/README.md#results-by-paper-element)).
The stages and what each establishes are in
[`experiments/README.md`](../experiments/README.md#stages).
