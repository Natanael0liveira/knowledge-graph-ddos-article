# Metrics

The paper and the sprint READMEs report recall, FPR, precision, F1, AUC and
*recall at FPR = 0* without defining them. This page defines each one in the
terms of this project, and explains why the evaluation insists on reporting a
**pair** of numbers rather than a single score.

## The unit of decision

Every metric here is computed over **HTTP sessions** inside one operational
window. Each session carries a ground-truth label — it either belongs to the
campaign (**positive**) or is legitimate (**negative**) — and the detector either
flags it or lets it through. Four outcomes follow:

|  | detector flags | detector lets through |
|---|---|---|
| **attacker session** | TP (true positive) | FN (false negative) |
| **legitimate session** | FP (false positive) | TN (true negative) |

Everything below is a ratio built from those four counts.

## Recall — "how much of the attack did I catch?"

> **recall = TP / (TP + FN)**

The fraction of the sessions that really belonged to the campaign that the
detector flagged. Also called sensitivity, true-positive rate or detection rate.
The denominator is every attacker session that existed, so recall is blind to how
much legitimate traffic there was.

In the canonical scenario (M = 25 stacks), the symbolic rule reaches **recall =
90.3%**: of every attacker session in the window, just over nine in ten matched
the derived scope. The missing 9.7% is the tail of attackers carrying one-off
fingerprints that never passed the enrichment test.

## FPR — "how many innocent users did I hit?"

> **FPR = FP / (FP + TN)**

The fraction of the legitimate sessions that the detector flagged by mistake.
Also called false-positive rate or fall-out. The denominator is every legitimate
session, so FPR is blind to how large the attack was.

In the same scenario the rule reaches **FPR = 0.00%**: across n = 15 campaigns,
no legitimate session fell inside the derived scope.

## The two are independent, and that is the point

Recall is computed down the *attacker* row of the table; FPR down the
*legitimate* row. Neither denominator contains the other class, so **class
imbalance moves neither number**. That matters here: a window under attack may
hold a thousand attacker sessions and a hundred legitimate ones, or the reverse,
and the pair (recall, FPR) reads the same way in both.

This is also why accuracy — (TP + TN) / everything — is never reported. On
imbalanced traffic it is dominated by whichever class is larger and can look
excellent while the detector is useless.

## Why the pair must always be reported together

Either number alone is trivially gamed:

- Flag **nothing**: FPR = 0%, recall = 0%.
- Flag **everything**: recall = 100%, FPR = 100%.

The second case is not hypothetical — it is the baseline this work is measured
against. A **global rate limit on the attacked endpoint** blocks every session
reaching that endpoint, so by definition it achieves 100% recall at 100% FPR: the
attack stops and every legitimate user of the service is disconnected with it.
Reporting only recall would make that control look perfect.

## Precision and F1

> **precision = TP / (TP + FP)** — of everything I flagged, how much was really attack?
>
> **F1 = 2 · (precision · recall) / (precision + recall)**

F1 is the harmonic mean of precision and recall, which punishes a large gap
between them: a detector at precision 1.0 and recall 0.1 scores F1 = 0.18, not
0.55. It compresses two numbers into one for ranking purposes, and the evaluation
reports it for comparability with prior work — never as a substitute for the
(recall, FPR) pair.

Note that precision, unlike FPR, **does** depend on class balance: its
denominator mixes both classes. Two detectors with identical recall and FPR will
show different precision on windows with different attack volumes.

## ROC and AUC — for detectors that emit a score

A learned model does not emit a decision, it emits a **score** per session. Only
after choosing a cut-off does it become a detector. Every possible cut-off yields
one (FPR, recall) pair; plotting recall against FPR as the cut-off sweeps from
strictest to loosest traces the **ROC curve**.

**AUC** is the area under that curve, in [0, 1]. Its useful reading:

> AUC is the probability that a randomly chosen attacker session scores higher
> than a randomly chosen legitimate one.

So AUC = 0.5 is coin-flipping — the model carries no information — and AUC = 1.0
means the two score distributions do not overlap at all. AUC is a **ranking**
measure: it summarizes the whole curve and never commits to an operating point.

That property is what makes it the right metric for the ablation. Configurations
(a) through (d) are compared on how well the *representation* separates the two
populations, independent of any threshold choice. The headline result — per-session
features sit at AUC 0.471–0.503 while cross-session features reach ≥ 0.98 — is a
statement about separability, not about a deployed detector.

## Recall at FPR = 0 — the number that matters operationally

AUC summarizes the whole curve, but a production system lives at **one** point on
it, and for automatic blocking that point is normally the strictest one: no
legitimate user may be disconnected. So the evaluation also reports the recall
achievable at the cut-off where FPR is exactly zero.

The two can diverge sharply. At M = 25:

| | learned model (d) |
|---|---|
| AUC | 0.979 |
| recall @ FPR = 0 | **36.4%** |

An AUC of 0.979 looks close to perfect, yet at a cut-off strict enough to spare
every legitimate user, the model recovers barely a third of the attack. The
reason is the shape of the tail: the score distributions separate well *on
average*, but a handful of legitimate sessions score as high as the attackers,
and the cut-off must clear them all. AUC averages that tail away; recall @ FPR = 0
is decided by it entirely.

This is why the paper reports both, and why the gap widens with M — 88.6% at
M = 5, 36.4% at M = 25, 17.6% at M = 100 — while AUC barely moves (0.996 → 0.979
→ 0.961). See [`evaluation.md`](evaluation.md) for the scenario axis.

## The symbolic rule has no score, and therefore no AUC

The SPARQL/enrichment path does not rank sessions. A session either matches the
derived scope or it does not, so the rule has exactly **one** operating point and
no threshold to sweep. There is no ROC curve to integrate, which is why the
symbolic columns of the results table report recall, FPR and F1 but leave AUC
blank.

That is a property worth stating plainly rather than apologizing for: the rule
delivers a fixed (recall, FPR) pair with no tuning, and its FPR = 0 comes from
the derivation refusing to name a non-enriched fingerprint, not from a threshold
fitted on labels.

## Collateral damage is FPR under another name

The mitigation results (Fig. 2, and
[`../experiments/pillar4-evidence-mitigation/`](../experiments/pillar4-evidence-mitigation/))
use two operational labels that map exactly onto the metrics above:

| Mitigation wording | Metric |
|---|---|
| attack blocked (%) | recall |
| legitimate hit (%) — *collateral damage* | FPR |

So "the frequency rule blocks 0.0% of the attack and 39.0% of legitimate traffic"
reads, in classifier terms, as recall = 0.0% at FPR = 39.0% — worse than flagging
nothing at all. And "no collateral observed" across n = 15 campaigns is FPR = 0
measured on the mitigation scope rather than on a classifier output.

The renaming is deliberate: once a verdict drives an actual filter, a false
positive is a disconnected customer, and the operational word carries that weight
where "FPR" does not.

## Metrics on production traffic

Production traffic has no attack label for the clients it carries, so its metrics
split in two: what the clean windows measure (false alarms and what they cost) and
what an injected botnet measures (how much of it is stopped). All of them are
computed by [`production_tables.py`](../experiments/sprint-6-noms/scripts/production_tables.py)
into `results/production_tables.json`; the definitions of the floor and of the test
are in [`concepts.md`](concepts.md), section 6.

### False-alarm rate, with an exact interval

A false alarm is a clean window in which the trigger fires *and* the scope names a
filter. The rate is x/n over the clean windows, reported with the Clopper–Pearson
95% interval, whose bounds are quantiles of beta distributions:

    lower = Beta⁻¹(0.025; x, n − x + 1)        upper = Beta⁻¹(0.975; x + 1, n − x)

The binomial configuration fires on 5 of 5,643 clean test-day windows: 0.089%, with
interval 0.029–0.207%. The calibrated z-score fires on 20 (0.354%, up to 0.547%) and
the beta-binomial on 22 (0.390%, up to 0.590%). The budget the level is calibrated to,
1% of a day's 288 windows, is 2.9 misfires per endpoint and day.

**Windows are not independent.** Misfires cluster: 13 of the beta-binomial's 22 and 13
of the z-score's 20 fall on one day of the web console. The exact interval treats the
5,643 windows as independent draws, so each rate also gets a percentile interval from a
bootstrap over endpoint-days: the days of each endpoint are resampled with replacement
(the endpoints stay fixed), the rate is recomputed as misfires over windows, and the
2.5th and 97.5th percentiles of 10,000 draws bound it (`cluster_ci`). It widens the
beta-binomial's upper bound from 0.59% to 0.82% and the z-score's from 0.55% to 0.81%,
and narrows the binomial's to 0.02–0.16%, whose five misfires are spread over the days.
With five days per endpoint the bootstrap is itself rough; both intervals are reported.

The same rate is also reported for each component alone: the scope without the gate
(the `|none` keys) and the gate without the scope (`gates_clean`). Each is calibrated
to 1% and each exceeds it on the days after the calibration. The configuration's rate is
low because it needs both, and the two are not independent. If they were, per endpoint

    expected joint misfires = Σ_e (gate rate_e × scope rate_e × clean windows_e)

which gives 3.5, 7.5 and 11.9 for the binomial, the beta-binomial and the z-score against
5, 22 and 20 observed (`clean_joint_expected`): a fleet raises the origin count and
enriches its own fingerprint in the same window.

### What a false alarm costs

The collateral of an alarm is the share of the window's clients the named filter
would block. Reported as the median and the mean over the alarms, and combined with
the rate into the **expected collateral per clean window**:

    expected collateral = false-alarm rate × mean collateral per alarm

| Configuration | False-alarm rate | Mean collateral per alarm | Expected collateral |
|---|---|---|---|
| Binomial | 0.089% | 30.6% | 0.027% |
| Calibrated z-score | 0.354% | 11.44% | 0.041% |
| Beta-binomial | 0.390% | 7.7% | 0.030% |

A configuration that misfires rarely but broadly and one that misfires often but
narrowly can cost legitimate users the same, which is what the table shows.

The **flash-crowd rate** is the share of windows the configuration fires on once N
legitimate users (N = 100 or 1,000) are added to a clean window; it measures how
often a surge of real users would be challenged.

### How much of an injected botnet is stopped

Attackers are added to the counts of real windows, on stacks absent from the
traffic (*new*) or drawn from the profile past its top ten (*shared*). The blocked
share is the mean over the attack windows of

    blocked = 1{gate fires} × 1{scope names a filter} × coverage

where coverage is the share of the window's attackers the named filter matches. The
three factors are reported apart (`gate`, `named`, and their product with the
coverage), which is what shows *which* part fails. For 100 attackers on new stacks,
the binomial configuration names a filter in every window, the gate fires in 68.4%
of them, and 38.4% of the attackers are stopped. The collateral in attack windows is
reported the same way as in clean windows.

### A held-out day as a test of the rate

With the configuration fixed in advance, the held-out day's false alarms are a test of
the test-day rate r = 5/5,643. Under that rate the count X in its 1,152 windows is
Bin(1152, r), with mean 1.02:

| Alarms x | P[X ≥ x] |
|---|---|
| 2 (observed) | 0.27 |
| 3 | 0.084 |
| 4 | 0.020 |

So up to 3 alarms would pass at the 5% level and 4 would reject the rate. The test's
power against a rate three times higher, P[Bin(1152, 3r) ≥ 4], is only 0.37: a
single held-out day can refute a gross error, not confirm the rate.

The count also depends on how often the gate opened. On the held-out day it opened in
3 clean windows (`clean_gate_windows`), against 168 on the test days (3.0%), and the scope
misfired in 2 of them. Conditional on the gate, the test-day rate is 5/168, and

    P[Bin(3, 5/168) ≥ 2] = 0.003

so the unconditional count is consistent because the gate was quiet, not because the
scope misfired less.

### Scores against the WAF's verdicts

`waf_labels.py` treats the clients the operator's WAF blocked as labels. Per
configuration: **named**, the share of windows with a filter; **recall**, the share of
blocked clients the filters match; **precision**, the share of the matched clients
that were blocked; **lift**, precision divided by the window's blocked share (a random
pick of clients has lift 1); and collateral, the share of unblocked clients matched.
A **surge** is a run of consecutive windows with at least k_min blocked clients and at
least the 99th percentile of the blocked count on the days before; it is *detected*
when a filter matches a blocked client in one of its windows. Detection is compared
with chance:

    expected by chance = Σ over surges of 1 − (1 − p₀)^L

with L the surge's length in windows and p₀ the rate at which the scope matches a
blocked client outside surges. Why these scores cannot validate the scope is in
[`concepts.md`](concepts.md), section 6.
