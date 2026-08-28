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
fingerprints that never cleared the enrichment floor.

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
features sit at AUC 0.471–0.502 while cross-session features reach ≥ 0.98 — is a
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

The mitigation results (Fig. 3, and
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
