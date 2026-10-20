# Metrics

This page defines every metric and statistical test behind the paper's tables. The
method itself (the trigger, the test, calibration and the floor) is defined in
[`concepts.md`](concepts.md). The experimental design is in
[`evaluation.md`](evaluation.md). Results in prose are in
[`FINDINGS.md`](../experiments/FINDINGS.md).

Pointers such as (V-B), (App. E) or (Table VII) refer to the paper,
[`article.tex`](../papers/http-session-noms/article.tex). File names without a path are in
[`experiments/sprint-6-noms/results/`](../experiments/sprint-6-noms/results/). A number marked
*computed here* is not printed in the paper. It follows from the named file by the formula
shown, computed with scipy.

The production metrics are computed by
[`production_tables.py`](../experiments/sprint-6-noms/scripts/production_tables.py): into
`production_tables.json` for the test days and the held-out day, and into
`production_tables_block.json` for the block (`make production-tables-block`).
[`block_report.py`](../experiments/sprint-6-noms/scripts/block_report.py) computes the block's
ten protocol metrics into `block_report.json` (`make block-report`).

1. [Units of decision](#1-units-of-decision)
2. [Classification metrics](#2-classification-metrics)
3. [Collateral damage](#3-collateral-damage)
4. [Reading the production tables](#4-reading-the-production-tables)
5. [False alarms](#5-false-alarms)
6. [What misfires cost](#6-what-misfires-cost)
7. [Coverage of an injected botnet](#7-coverage-of-an-injected-botnet)
8. [Prospective tests](#8-prospective-tests)
9. [Scores against the WAF](#9-scores-against-the-waf)
10. [Other tests](#10-other-tests)

## 1. Units of decision

On generated traffic, each metric counts the **sessions** of one campaign, averaged over
seeds. Each origin carries one session there (III-C), so sessions and origins give the same
counts. A session belongs to the campaign (**positive**) or is legitimate (**negative**). A
scope either matches it or lets it through:

| | matched | let through |
|---|---|---|
| **attacker session** | TP (true positive) | FN (false negative) |
| **legitimate session** | FP (false positive) | TN (true negative) |

On production traffic no client carries an attack label. Two units replace the session:

- A **window** is one endpoint's five-minute interval, 288 a day. False alarms are counted
  in windows.
- A **client** is an origin: a source address, counted once per fingerprint it presents
  (III-B). Collateral and coverage are shares of clients. The gate's count also includes
  plain-HTTP clients (App. A).

A test window is **clean** before any botnet is injected into it (IV-A).

## 2. Classification metrics

### Recall and FPR

> **recall = TP / (TP + FN)**
>
> **FPR = FP / (FP + TN)**

Recall is the share of the campaign's sessions that the scope matches. It is also called
sensitivity, true-positive rate or detection rate. Its denominator holds only attacker
sessions.

FPR is the share of legitimate sessions that the scope matches by mistake. It is also called
the false-positive rate. Its denominator holds only legitimate sessions.

In the default campaign (M = 25, K = 1000), the binomial test's scope has recall 90.3% and
FPR 0.00% over 15 seeds (Table III). The scope is selected from the alarm's cluster, and
recall counts all of the campaign's attacker sessions (`symbolic_detector.py`). The scope
lists all 25 stacks in every seed (`sym_n_ja4` in `symbolic_detector.json`). The missing
9.7% are therefore the attackers on one-off fingerprints, which no scope selects.

**Class balance moves neither number.** Recall reads the attacker row of the table, and FPR
the legitimate row. A window may hold a thousand attackers and a hundred legitimate clients,
or the reverse, and the pair reads the same way. Accuracy, (TP + TN) / all, depends on which
class is larger, so it is never reported.

**Report the pair together.** Either number alone is easy to game. Matching nothing gives
recall 0% at FPR 0%. Matching everything gives recall 100% at FPR 100%. The second case is
the paper's fallback for windows the scope cannot serve: a rate limit or a challenge to every
client (V-B). It reaches the whole attack and every legitimate client.

### Precision and F1

> **precision = TP / (TP + FP)**
>
> **F1 = 2 · precision · recall / (precision + recall)**

Precision is the share of matched sessions that belong to the attack. F1 is the harmonic
mean of precision and recall, so a large gap between the two pulls it down. At precision 1.0
and recall 0.1, F1 is 0.18, where the arithmetic mean would give 0.55. Table III gives F1 next
to recall and FPR. On the laboratory captures, F1 is the score that compares with KLAGE's
published F₁ (App. C).

Precision depends on class balance, because its denominator mixes both classes. Two scopes
with the same recall and FPR show different precision on windows with different attack sizes.

### ROC and AUC

A learned model gives each session a **score**. It becomes a detector only once a cut-off is
chosen. Each cut-off gives one (FPR, recall) pair. Plotting recall against FPR, as the cut-off
moves from strictest to loosest, traces the **ROC curve**. **AUC** is the area under it, in
[0, 1]:

> AUC is the probability that a randomly chosen attacker session scores higher than a
> randomly chosen legitimate one.

AUC = 0.5 is chance, and AUC = 1.0 means the two score distributions do not overlap. AUC
summarizes the whole curve and commits to no operating point.

That is why the ablation is compared in AUC (App. C). It asks how well each representation
separates the two populations, whatever the threshold. In stealth mode, the per-session flow
attributes (a) stay at AUC 0.488–0.503 under four classifier families, and the three academic
baselines sit at 0.495–0.518. The cross-session representation (d) reaches 0.927 at K = 50 and 0.982 at
K = 1000 (`canonical_realistic.json`, `canonical_baselines.json`). These numbers measure
separability. A deployed detector also needs an operating point, which the next metric adds.

### Recall at FPR = 0

A system that blocks automatically works at one point of the ROC curve. For blocking, that
point is usually the strictest one, where no legitimate session is hit. Table III therefore
gives the learned models' recall at FPR = 0: the share of attacker sessions that score above
every legitimate session (`recall_fpr0` in `symbolic_detector.py`).

The two numbers can diverge sharply. For the learned model (d) at M = 25:

| | (d) |
|---|---|
| AUC | 0.979 |
| recall at FPR = 0 | **36.4%** |

An AUC of 0.979 looks close to perfect. Yet at a cut-off that spares every legitimate
session, the model recovers about a third of the attack. A few legitimate sessions score as
high as the attackers, and the cut-off must clear them all. AUC averages that tail away, and
recall at FPR = 0 depends on it entirely.

The gap widens with M. Recall at FPR = 0 is 88.6%, 36.4% and 17.6% at M = 5, 25 and 100,
while AUC moves only from 0.996 to 0.979 and 0.961 (`rf_recall_fpr0` and `rf_auc` in
`symbolic_detector.json`). At 1% false positives, (d) reaches 66.8% at M = 25 (V-A;
`rf_recall_fpr1`). See [`evaluation.md`](evaluation.md#1-the-question-and-its-two-axes) for
the M axis.

### The scope has no score, so it has no AUC

A scope does not rank sessions. A session matches the selected fingerprints or it does not,
so the scope has one operating point and no threshold to sweep. Table III therefore gives
recall, FPR and F1 for the binomial test, recall for the other scopes, and recall at FPR = 0
for the learned models.

The test's profile and level come from attack-free runs, so its operating point uses no
labels. Its FPR is 0.00% on new stacks, and 2.23% and 3.78% on shared and adversarial stacks
(Table III).

## 3. Collateral damage

**Collateral damage** is the share of legitimate traffic inside the selected scope: the FPR of
the filter if it were deployed (IV-B). The paper uses the operational word because a false
positive of a deployed filter is a blocked user.

| Wording on generated traffic | Metric |
|---|---|
| covers or blocks x% of attackers | recall |
| blocks x% of legitimate traffic (collateral) | FPR |

For example, from five stacks onward the modal fingerprint covers 0.0% of attackers and
blocks 39.0% of legitimate traffic (V-A; `fpr` of `modal` in `unseen_synth_summary.csv`). In
classifier terms that is recall 0.0% at FPR 39.0%, worse than matching nothing. "No observed
collateral" over 15 seeds means FPR = 0 for the scope.

On production traffic, collateral is a share of one window's clients, in three settings:

- **Clean window.** Coll. is the share of all the window's clients the filter blocks. The
  tables give its median over a configuration's false alarms (IV-B).
- **Flash-crowd window.** The same share, with the crowd counted among the clients
  (`flash1000_collateral_median`).
- **Attack window.** The share of the window's legitimate clients the filter blocks
  (`attack_collateral_median`). On the test days the calibrated scopes block a median 0%, and
  up to 71% in the worst window of a small endpoint (App. E).

## 4. Reading the production tables

Tables IV to VII use the column names and marks below. Values are percentages.

| Column or mark | Tables | Meaning |
|---|---|---|
| FA | IV, VI, VII | False-alarm rate: the share of clean windows in which the configuration's trigger and scope together select a filter ([§5](#5-false-alarms)) |
| No gate (a column) | IV | The scope's own rate on clean windows, with no trigger ([§5](#each-component-alone-and-the-joint-misfire-test)) |
| No gate (a trigger) | VI, VII | The scope runs as its own trigger ([`concepts.md`](concepts.md#5-the-triggers)) |
| Coll. | IV, VI, VII | Median, over the configuration's false alarms, of the share of the window's clients the filter blocks ([§3](#3-collateral-damage)) |
| Fl. 1k | IV, VI, VII | Share of windows in which the configuration fires once 1,000 of the day's clients join a clean window ([§6](#flash-crowds)) |
| New, Shared | IV, VI, VII | Coverage of an injected 25-stack botnet on new stacks (absent from the traffic) or shared stacks (the profile's tail beyond its ten most common fingerprints) ([§7](#7-coverage-of-an-injected-botnet)) |
| 0.1×, 1× | IV, VII | Botnet size in median windows of the endpoint. 0.1× is the *tenth-size* botnet. |
| 100 attackers | VII | A botnet of 100 attackers per window |
| test, held | VI | The five test days, and the held-out day |
| all, E1 | VII | Pooled over the four endpoints, and the busiest endpoint alone |
| E2–E4: max | VI, VII | The largest value among the three smaller endpoints |
| pooled | VI, VII | Computed over the windows of all four endpoints together |
| in sample, cross-fitted | IV, V | Calibration days judged against a profile that includes them, or against a profile of the other days ([`concepts.md`](concepts.md#cross-fitting)) |
| n₀ | V | The median calibration window, in origins |
| λₑ bin., beta | V | The calibrated level of the binomial and of the beta-binomial test, in sample |
| new, shared (floors) | V | Attackers per window from which the scope selects a typical stack, as "in sample / cross-fitted", test-day medians ([`concepts.md`](concepts.md#8-the-calibration-floor-and-the-enrichment-limit)) |
| \* | IV–VII | Post hoc: built after the held-out day was read. The starred rows of Table VII were still fixed before the block. |
| † | VI, VII | Cross-fitted |
| ᵃ | VII | Run on E1 alone |

## 5. False alarms

### The rate and its exact interval

A **false alarm** is a clean window in which the configuration's trigger fires and its scope
selects a filter. The **false-alarm rate** is x/n over the clean windows. Windows under
k_min = 5 origins, where no gate can open, are left out:

| Day set | Clean windows | Left out |
|---|---|---|
| Five test days | 5,643 | 117 of E4's 1,440 (App. E) |
| Held-out day | 1,152 | none (App. E) |
| 14-day block | 16,103 | 25 of E4's 4,032 (`m2` in `block_report.json`) |

The rate comes with its exact (Clopper–Pearson) 95% interval. The bounds are quantiles of
beta distributions:

    lower = Beta⁻¹(0.025; x, n − x + 1)        upper = Beta⁻¹(0.975; x + 1, n − x)

For example, the binomial configuration misfires in 5 of 5,643 clean test-day windows: 0.089%,
with interval 0.029–0.207% (V-B; `clean_ci95`). On the block it misfires in 31 of 16,103:
0.19%, with interval 0.13–0.27% (V-D). With x = 0 the lower bound is 0, and the upper bound is
1 − 0.025^(1/n).

The **false-alarm budget** is 1%. Each scope is calibrated to select a filter in at most 1% of
an endpoint's attack-free calibration windows (III-C), and later rates are judged against the
same 1%. On a day of 288 windows, that is 2.9 misfires per endpoint.

### Windows are not independent

The exact interval treats windows as independent draws. False alarms cluster by day, so the
interval understates the uncertainty of clustered rates (IV-B). For example, 13 of the
in-sample beta-binomial's 22 test-day misfires, and 13 of the calibrated z-score's 20, fall on
one day of the web console (App. E; `clean_fires_by_fold`).

### Why the endpoint-day bootstrap is not used

The artifact also gives a percentile interval from a bootstrap over endpoint-days
(`clean_ci95_cluster`, from `cluster_ci` in `production_tables.py`). It resamples each
endpoint's days with replacement, keeps the endpoints fixed, recomputes misfires over windows,
and takes the 2.5th and 97.5th percentiles of 10,000 draws.

With five test days per endpoint, the bootstrap cannot see day-to-day variation it has not
sampled. For the binomial configuration it gives 0.02–0.16%, narrower than the exact
0.03–0.21%. For the cross-fitted beta-binomial its lower bound is 0%, although six misfires
were observed. The paper therefore reports the exact interval and states the clustering. On
the block, with 14 days per endpoint, the bootstrap gives 0.12–0.27%, close to the exact
0.13–0.27% (`m1.ci95_cluster` in `block_report.json`). An overdispersed count model per
endpoint-day, or more days, would be the proper fix.

### Each component alone, and the joint-misfire test

The result files also give each component's rate alone: the scope without a gate (the `|none`
keys, the No gate column) and the gate without the scope (`gates_clean`). Both are calibrated
to the 1% budget. On the test days both exceed it: the binomial scope alone selects a filter
in 2.2% of clean windows, and the distinct-origin gate opens in 3.0% (V-B). The configuration's
rate is low because it needs both.

If gate and scope misfired independently, the expected number of joint misfires would be

    expected = Σₑ (gate rateₑ × scope rateₑ × clean windowsₑ)

summed over the endpoints e (`clean_joint_expected`). A fleet can create dependence: it raises
the origin count and enriches its own fingerprint in the same window. Under independence, the
joint misfires are a sum of many rare window events, so their count is close to Poisson with
that mean. The tail P[X ≥ observed] says how surprising the observation is:

| Configuration, test days | In sample | P | Cross-fitted | P |
|---|---|---|---|---|
| Binomial | 5 against 3.5 | 0.27 | 6 against 3.2 | 0.10 |
| Beta-binomial | 22 against 7.5 | 1.4 × 10⁻⁵ | 6 against 1.8 | 0.011 |
| Calibrated z-score | 20 against 11.9 | 0.020 | 13 against 4.6 | 0.001 |

The paper prints four of these P values: 0.27, 0.10, P < 10⁻⁴ and 0.02 (App. E). The others
are computed here from the same counts.

The dependence is clear for the beta-binomial and the z-score. On the test days, the binomial
configuration's excess is within chance. On the block the excess is much larger: 31 joint
misfires against 2.9 expected (App. E). The same Poisson tail gives P ≈ 10⁻²¹ (computed here,
from `clean_joint_expected` in `production_tables_block.json`). The expectation pools days per
endpoint, so day-to-day variation alone can inflate the excess (App. E).

## 6. What misfires cost

### Expected collateral per clean window

A rare misfire can block many clients, and a frequent one can block few. The **expected
collateral per clean window** combines the two:

    expected collateral = false-alarm rate × mean collateral per false alarm

| Configuration | Days | FA | Mean Coll. | Expected |
|---|---|---|---|---|
| Binomial | test | 0.089% | 30.6% | 0.027% |
| Calibrated z-score | test | 0.354% | 11.4% | 0.041% |
| Beta-binomial, in sample | test | 0.390% | 7.7% | 0.030% |
| Binomial | block | 0.19% | 42.5% | 0.082% |
| Cross-fitted beta-binomial, seasonal gate | block | 0.12% | 52.7% | 0.065% |

Sources: `clean_collateral_mean` in `production_tables.json`, and `m5` in `block_report.json`.
The paper prints 0.03% for the binomial configuration on the test days (V-B) and 0.08% on the
block (App. E). The first three rows show that a configuration that misfires rarely but
broadly, and one that misfires often but narrowly, can cost legitimate users about the same.

The tables give the median collateral, while this product uses the mean. App. E's comparison
of known-fleet shares uses the rate times the median, a rougher measure (0.0028% versus
0.070% per clean window).

### Flash crowds

The **flash-crowd rate** is the share of windows in which the configuration fires once N of
the day's clients (N = 100 or 1,000) are added to a clean window (IV-A). It measures how often a
surge of real users would meet a filter. The collateral of those firings is the median share
of the window's clients the filter blocks, with the crowd counted among them. For example,
crowds of 1,000 production clients trigger the binomial configuration in 22.2% of test-day
windows, with filters blocking a median 4.3% of the window's clients (V-B).

On generated traffic, a flash crowd retimes 25, 50 or 100 legitimate sessions from another
run into one window (App. E).

### The fallback's cost

When the gate opens and the scope selects nothing, the **fallback** acts: a rate limit or a
challenge to every client (V-B). Its count on clean windows is

    fallback windows = clean gate openings − false alarms

| Configuration | Days | Fallback windows | Share of clean windows |
|---|---|---|---|
| Binomial | test | 168 − 5 = 163 | 2.9% (V-B) |
| Binomial | block | 233 − 31 = 202 | 1.3% (computed here, from `m8`) |
| Cross-fitted beta-binomial, seasonal gate | block | 255 − 20 = 235 | 1.5% (VI) |

The gate openings are `clean_gate_windows`. The fallback reaches every client of the window,
so it is the "match everything" case of [§2](#recall-and-fpr). The false-alarm budget does not
count this cost (VI).

## 7. Coverage of an injected botnet

On production, attackers are added to the counts of real windows (IV-A). Their stacks are new
(absent from the traffic), shared (the profile's tail beyond its ten most common fingerprints)
or adversarial (the endpoint's 25 most common). For one attack window w,

    blocked_w = 1{gate fires} × 1{scope selects a filter} × matched_w

where matched_w is the share of the window's attackers that the selected filter matches. The
paper's **coverage** is the mean of blocked_w over all attack windows, including those the
gate misses (IV-B). It is at most about 90%, because a tenth of the attackers use one-off
fingerprints that no scope selects.

The result files give the factors apart (`gate`, `named` and `blocked`), which shows which
part fails. For 100 attackers on new stacks on the test days, the binomial configuration's
scope selects a filter in every window, the gate fires in 68.4% of them, and 38.4% of the
attackers are blocked (`new:A100` in `production_tables.json`; App. E). `blocked_alone` and
`blocked_no_gate` drop the gate factor. They give what the scope alone would block, the dashed
line of Fig. 2.

On generated traffic, "covers" means the scope's recall ([§2](#recall-and-fpr)), with no gate.

## 8. Prospective tests

### The held-out day

The binomial configuration was fixed before the held-out day was read
([`evaluation.md`](evaluation.md#6-the-held-out-day-protocol)). Its false alarms then test the
test-day rate r = 5/5,643. Under that rate, the count X in the day's 1,152 clean windows is
Bin(1152, r), with mean 1.02. The protocol calls the day consistent if P[X ≥ x] ≥ 0.05:

| False alarms x | P[X ≥ x] |
|---|---|
| 2 (observed) | 0.27 |
| 3 | 0.084 |
| 4 | 0.020 |

Up to three false alarms would pass, and four would fail. The test is weak. Against a rate
three times higher it fails with probability P[Bin(1152, 3r) ≥ 4] = 0.37 (computed here). One
day can expose a gross error. Confirming the rate needs many more windows.

The count also depends on how often the gate opens. On the held-out day the gate opened in 3
clean windows (`clean_gate_windows`), and the scope misfired in 2 of them, both on the web
console. On the test days the scope misfired in 5 of 168 openings. Conditional on the gate,

    P[Bin(3, 5/168) ≥ 2] = 0.003

This test is post hoc (V-D). Read this way, the day passed because its gate rarely opened.
Once the gate opened, the scope misfired more often than the test days predict. The block's
protocol then made this conditional test a pre-specified metric (metric 8, below).

### The 14-day block

[`evaluation.md`](evaluation.md#7-the-14-day-block-protocol) gives the protocol and its ten
metrics. The counts and P values below are in `block_report.json`.

**Primary A: the binomial configuration's false-alarm rate.** Under the test-day rate r, the
count in 16,103 clean windows is Bin(16103, r), with mean 14.3. The block is consistent if
P[X ≥ x] ≥ 0.05, that is, with up to 21 misfires (`m1.largest_consistent`). Against a doubled
rate, the test fails with probability 0.91 (computed here; the protocol planned 0.93 for about
15,800 windows).

- Observed: 31 misfires, 0.19% (exact 95% interval 0.13–0.27%).
- P[X ≥ 31] = 8.3 × 10⁻⁵ (V-D: P < 10⁻⁴). The block is therefore **not consistent** with the
  test days, though its rate stays below the 1% budget.

**Metric 8: the scope's reliability once the gate opens.** The gate opened in 233 clean
windows, and the scope misfired in 31 of them: 13% (exact 95% interval 9.2–18.4%). On the test
days it was 5 of 168. P[Bin(233, 5/168) ≥ 31] = 4.9 × 10⁻¹² (V-D: P < 10⁻¹¹), so this is not
consistent either. Per endpoint: 0 of 11 openings on E1, 17 of 29 on E2, 10 of 98 on E3 and 4
of 95 on E4 (`m8`).

**Primary B: the budget per endpoint**, for configurations 3 to 5. A configuration is
**within the budget** on an endpoint if its rate is at most 1%. It is **shown within the
budget** if the upper end of its exact two-sided 95% interval is at most 1%. In 4,032 windows
that allows up to 27 false alarms, 0.67% (`heldout_block_protocol.md`). The binomial scope with
known fleets as E1's own trigger (configuration 5) misfired in 63 of 4,032 windows: 1.56%,
upper bound 2.0%, over the budget (`m2`; Table VII). Configurations 3 and 4 are shown within
the budget on every endpoint.

**Metric 9: the weekly cycle** is descriptive. 30 of the 31 misfires fall on the ten weekdays,
and 1 on the four weekend days (`m9`).

### Post hoc: Fisher's exact test

The binomial tests above treat the test-day rate as exact. With only five test-day misfires,
that rate is itself uncertain. A one-sided Fisher exact test compares the two samples and
counts the uncertainty of both:

| | misfires | other clean windows |
|---|---|---|
| block | 31 | 16,072 |
| test days | 5 | 5,638 |

It gives P = 0.066 for the rise of the rate. The same test on gate openings, 31 of 233 against
5 of 168, gives P = 0.00017. The paper rounds them to P = 0.07 and 0.0002 (App. E). The first
is above the protocol's 5% level, and the second is far below it. These tests are post hoc and
do not change the protocol's verdict.

## 9. Scores against the WAF

The only malicious population the production exports carry is the clients the operator's WAF
blocked. [`waf_labels.py`](../experiments/sprint-6-noms/scripts/waf_labels.py) scores each
calibrated scope against those verdicts, under two profiles: one without the blocked clients,
and one with all clients (V-D). The WAF blocks none of E1's clients, so E1 has no labels. Per
endpoint, the scores are:

- **named**: the share of windows in which the scope selects a filter;
- **recall**: the share of blocked clients the filter matches;
- **precision**: the share of matched clients that the WAF blocked;
- **base rate**: the blocked share of all clients, which is the precision of a random pick;
- **lift**: precision divided by the base rate, so a random pick has lift 1;
- **collateral**: the share of unblocked clients the filter matches.

A **surge** is a run of consecutive windows, each with at least k_min blocked clients and at
least the 99th percentile of the endpoint's blocked count on the days before. A surge is
*detected* when the filter matches a blocked client in one of its windows. Chance alone gives

    expected detections = Σ over surges of 1 − (1 − p₀)^L

with L the surge's length in windows and p₀ the rate at which the filter matches a blocked
client outside surges.

**Why a profile without blocked clients agrees with the WAF by construction.** Let the WAF
block a share S of a window's clients. Take a stable fingerprint: its unblocked clients make up
the same share b of the window's unblocked clients as in the profile. Let a share s of the
fingerprint's own clients be blocked. Its share of the whole window is then b(1 − S)/(1 − s),
and the effect condition c/n ≥ ρ·b holds only when

    (1 − S)/(1 − s) ≥ ρ,   that is,   s ≥ 1 − (1 − S)/ρ

With ρ = 3 and the endpoints' median blocked shares S = 9–63% (E2–E4), a stable fingerprint is
enriched only if 70–88% of its clients were blocked (V-D; `implied_precision_floor` in
`waf_labels.json`). Under that profile the scopes reproduce the WAF's decisions: 84–99% of the
clients they would block on the API and single sign-on were blocked by the WAF (App. E).

**With a profile of all clients**, as a scope deployed in front of the WAF would build it, only
0.4–33% of the clients the three calibrated scopes would block were blocked by the WAF. That is
below a random pick's 10–63% on every endpoint, a lift below 1. On the API and single sign-on,
the scopes catch at most two of the WAF's 38 surges (V-D). These scores therefore cannot
validate the scope.

## 10. Other tests

- **Upper bound at zero events.** With no event in n windows, the one-sided 95% upper bound is
  1 − 0.05^(1/n). For example, the per-window rule with the test fires on none of 360
  generated clean windows, a bound of 0.8% (App. E). The held-out-day protocol uses the rule of
  three, 3/n, which bounds a zero count near 0.26% for 1,152 windows (`fresh_day_protocol.md`).
- **Kolmogorov–Smirnov distance D.** The largest gap between two empirical cumulative
  distributions. Between generated and source sessions, D = 0.002 for request counts and 0.003
  for durations (IV-A; [`ks_validation.json`](../experiments/sprint-2/results/ks_validation.json)).
  The generator samples from those very distributions, so D checks only the sampler.
- **Paired Wilcoxon signed-rank test, Bonferroni-corrected.** The ablation pairs configurations
  on the same 30 seeds (App. C). Here (d) wins in all 30 pairs, so the exact two-sided P is
  2/2³⁰ = 1.86 × 10⁻⁹, the smallest this test can give with 30 pairs. Multiplied by the four
  comparisons made, that is the paper's p_Bonf = 7.5 × 10⁻⁹ for (d) − (c) and (d) − (a)
  (`tests` in `canonical_realistic.json`).
- **Bootstrap intervals over seeds.** Means over seeds on generated traffic come with a 95%
  percentile interval from 2,000 resamples (`ci95`, from `boot_ci` in
  [`run_sprint4.py`](../experiments/sprint-4/scripts/run_sprint4.py)).
- **The binomial model of stack sizes**, which predicts coverage near the floor, is part of
  the method and is defined in [`concepts.md`](concepts.md#8-the-calibration-floor-and-the-enrichment-limit).
