# Evaluation design

How the claims in [`papers/http-session-noms`](../papers/http-session-noms/) are
tested, and what each traffic source can and cannot establish. For the concepts
see [`concepts.md`](concepts.md).

---

## Why the Slow HTTP DoS family

The family is the experimental instantiation of `CoordinatedHTTPFlood`, chosen
for four reasons:

1. **Best covered L7 class in public datasets.** Slowloris, slowhttptest, HULK
   and GoldenEye appear in CICIDS2017, CIC-DDoS2019 and CIC-IoT2023.
2. **Works natively over HTTPS.** The attacks sustain traffic over established
   TLS connections, so a JA4 fingerprint is observable at every handshake.
3. **Contemporary at record scale.** HTTP/2 Rapid Reset sustained peaks of
   398M rps (Google), 201M rps (Cloudflare) and 155M rps (AWS) in September 2023
   with a botnet of roughly 20,000 machines. That botnet size falls directly in
   Scenario C below.
4. **Maps cleanly onto the ontology.** K = 1 is the classic single-source attack;
   high K is the distributed version. Connection-holding variants (Slowloris,
   slow body, slow read) and rate-based ones (HULK, GoldenEye, Rapid Reset) are
   subclasses of the same family.

## Parameterizing by distribution, not by attack name

The central hypothesis has two parts: cross-session representation gains over
per-session detection as the **degree of distribution K** grows, and the symbolic
path turns that structure into an auditable, low-collateral decision. The
evaluation is therefore parameterized by K.

| Scenario | K | What it models | Expectation |
|---|---|---|---|
| A | 1 | Classic single-source high-volume attack | No cross-session edge needed; conventional detectors suffice |
| B | 10–100 | Small botnets, proxy-limited operations | Network proximity only partial; high-weight signals must carry detection |
| C | ≥ 1000 | Hundreds of ASNs and prefixes | Per-session signal negligible, `relatedByNetworkProximity` nearly empty |

Scenario C is the regime in which the contribution has to hold to be
operationally meaningful. The paper reports B (K = 50) and C (K = 1000).

## Traffic sources

### Source 1 — calibrated synthetic generator (primary)

Produces distributed Slow HTTP DoS campaigns with perfectly known coordination
ground truth, parameterized by K, by the fraction of origins sharing TLS
signature and identity, by IP/ASN dispersion and by the time window. It is the
only source that covers Scenario C.

Two parameters decide whether the scenario resembles production, and both are
calibrated rather than assumed:

- **Benign fingerprint popularity**, shaped as a Zipf curve of exponent α. Real
  populations are concentrated: an up-to-date browser on a given platform emits
  essentially one JA4. Calibrated against 6.33M TLS requests logged at a
  production edge point of presence (495 distinct fingerprints, top one 38.4% of
  requests, top ten 93.8%). The measured curve is bracketed by α = 1.5 and
  α = 2.0; α = 1.5 is canonical and the range is swept.
- **Botnet composition.** Real botnets span device classes and therefore TLS
  stacks, so the campaign is distributed uniformly over M stacks, with M = 25
  canonical and swept because no published measurement fixes it. An adversarial
  mode lets the botnet adopt the most common benign fingerprints instead of its
  own.

**What the M sweep is for.** M is not a realism knob among others: it is the axis
that *breaks the assumption prior work rests on*. A detector that scopes
mitigation by the single most frequent fingerprint only works while the botnet
emits one — at M = 1. Spreading the campaign over M stacks gives each attacker
stack a share of about 1/M, and once that falls below the head of the benign
Zipf curve (38.4% of requests at the measured edge), the most frequent
fingerprint inside a fired cluster stops being an attacker's and becomes a
*legitimate* one. Distributing uniformly is the conservative choice for a given
M, since it denies the detector any dominant stack to latch onto.

Two consequences follow, and both are measured rather than assumed. First, the
sweep is the stress test of the enrichment rule: it has to keep working from
M = 1 to M = 100 while the frequency rule inverts at M = 5 (see
[`../experiments/pillar4-evidence-mitigation/`](../experiments/pillar4-evidence-mitigation/)).
Second, M fixes a design constraint — the support floor σ must sit below 1/M, or
the scope silently drops the smaller stacks — which is why σ = 0.002 rather than
a rounder number. See [`concepts.md`](concepts.md) for the derivation.

Legitimate distributions are calibrated against the ~322k benign sessions of
CICIDS2017 and verified by Kolmogorov–Smirnov tests (D = 0.003 for duration,
D = 0.002 for request count, both p > 0.8), so the observed gain cannot come from
artificially easy benign traffic. A **stealth mode** draws attacker sessions from
the same per-session distributions as benign traffic, so the campaign reveals
itself only through cross-session structure.

**What it establishes:** the mechanism, under an assumption of perfect
per-session indistinguishability. **What it does not:** field performance. The
mimicry is imposed by construction.

### Source 2 — public datasets

CICIDS2017 (Wednesday capture: Slowloris, slowhttptest, HULK, GoldenEye) and
CIC-IoT2023, the latter being the dataset on which KLAGE reports F₁ = 84.1% for
DDoS Slowloris. Both run through the same extraction pipeline
(PCAP → JA4 + flows → sessions → graph).

**What they establish:** that the pipeline works on real captures, and a
comparison point against published state of the art. **What they do not:** the
stealthy distributed regime. Their attacks carry an obvious flow signature, so a
strong per-session classifier already reaches F₁ ≈ 0.90 on them and the
cross-session gain is marginal. Both are laboratory testbed captures, not
production traffic.

### The benchmark gap

No public benchmark provides captured stealthy distributed Layer-7 traffic.
This is not for lack of looking, and it is not improving: the 2024
BCCC-cPacket-Cloud-DDoS dataset names "inadequate representation of
application-layer DDoS attacks" as a deficiency of the 16 datasets it surveyed,
and then ships 17 DDoS scenarios that are all TCP-based. Validating the approach
on a captured stealthy distributed campaign remains the single most important
experimental direction, and it is stated as such in the paper's limitations.

## Baselines and configurations

Every combination is run n = 30 times with distinct seeds, giving bootstrap
confidence intervals and paired tests. All configurations consume the same
underlying traffic attributes, so the ablation separates *representation*, not
data availability.

The per-session baseline is deliberately **strong**: a Random Forest over all
eight to nine available flow attributes, repeated with histogram gradient
boosting, a multilayer perceptron and logistic regression so the negative result
does not depend on one hypothesis class. Three academic baselines are
reimplemented (PCA profiling, k-means over a behavioural matrix, supervised
RF/SVM over session features).

| | Configuration |
|---|---|
| (a) | ML baseline without ontology |
| (b) | Ontology with no `relatedBy` sub-relation, sessions as isolated nodes |
| (c) | Ontology with only `relatedByNetworkProximity`, a naive ASN/prefix detector |
| (d) | Full cross-session feature representation over the three observable sub-relations |

So (d)−(a) is the total contribution, (d)−(b) the gain of representing
cross-session structure at all, and (d)−(c) the gain of high-weight signals over
network proximity.

Configuration (d) reaches the cross-session evidence through **features**, not by
querying the RDF graph. It is a feature-level proxy chosen so that every
configuration differs only in representation. The ablation therefore measures the
representation; what the symbolic formalism adds is evaluated separately, by
running the rule itself as a detector.

## Metrics

Beyond standard classification metrics the evaluation reports **collateral
damage**: the fraction of legitimate traffic falling inside the scope derived
from the verdict. Evidence chains are assessed for *completeness* (do they
enumerate every correlated session and activated sub-relation?) and
*actionability* (is the derived scope coherent with the cluster discriminator?).
Both checks are automated. No user study was run, so whether the chains shorten
an analyst's time to decision is untested.

## Where each result lives

| Claim | Stage |
|---|---|
| Extraction pipeline | `experiments/sprint-1/` |
| Calibrated generator | `experiments/sprint-2/` |
| Baselines and ablation | `experiments/sprint-3/` |
| Full run, weight calibration | `experiments/sprint-4/` |
| Comparison against KLAGE | `experiments/sprint-5/` |
| Cost model, window sweep, profile drift | `experiments/sprint-6-noms/` |
| Verdict as derivation | `experiments/pillar2-symbolic-reasoning/` |
| Evidence chain, scoped mitigation | `experiments/pillar4-evidence-mitigation/` |
