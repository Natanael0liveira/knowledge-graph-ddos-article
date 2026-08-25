# Sprint 3 — Baselines and ablation

Measure three academic baselines and four ablation configurations over **the same
input**, isolating the contribution of the `relatedBy_*` family. The decisive
result appears in the **stealthy** scenarios from Sprint 2.

## The four configurations

They differ **only** in the feature set handed to a common classifier
(RandomForest):

| Config | Features | What it tests |
|---|---|---|
| (a) ML without ontology | **Strong** per-session flow set (8–9 attributes) | Per-session state of the art |
| (b) Ontology without `relatedBy_*` | (a) plus per-session ontological attributes (identity, target) | Ontology with no cross-session correlation |
| (c) `relatedByNetworkProximity` only | (a) plus `share_net` (/24) | The network signal alone (weight 0.3) |
| (d) Full framework | (a) plus `share_ja4`, `share_net`, `cluster_size` | The complete `relatedBy_*` family |

The three baselines (Fernandes 2015 PCA + threshold; Bharathi 2012 k-means;
Kemp 2023 RF/SVM) run on the features of (a), being per-session by construction.

## Result

The attack is mimetic: each session is individually indistinguishable from a
legitimate user, and only the correlation structure between sessions betrays the
campaign.

**These are preliminary single-seed numbers.** The canonical values, with n = 30
seeds, bootstrap confidence intervals and paired tests, come from Sprint 4 and are
what the paper reports (0.927 at K = 50 and 0.982 at K = 1000 for (d), against
0.498–0.503 for (a), (b) and the baselines).

| Config | K = 50 | K = 1000 |
|---|---|---|
| (a) per-session ML (strong) | 0.519 | 0.502 |
| (b) ontology without `relatedBy` | 0.527 | 0.503 |
| (c) network proximity only | 0.523 | 0.664 |
| **(d) full** | **0.968** | **0.976** |
| Baselines (Fernandes / Bharathi / Kemp) | ~0.52 | ~0.50 |

**Reading.** The strong per-session ML, the baselines **and** the ontology without
`relatedBy` (b) all sit near chance against stealthy distributed campaigns, even
with 8–9 flow features. Per-session ontological attributes are not enough; it is
the relation **between** sessions that carries detection. At K = 50 network
proximity is weak because the botnet is dispersed, but the shared JA4 at weight
1.0 carries (d), which empirically supports the paper's evasion-cost weighting.

> **Artifact removed.** In an earlier version (b) scored around 0.88 through a
> **port artifact**: synthetic benign traffic had varied `dst_port` while the
> attack went to `:443`. Forcing legitimate users onto the same service
> (`benign_same_service=true`) removes it and (b) falls to chance. That realistic
> scenario is what the paper reports.

**Caveat.** Non-stealthy attacks (slowloris or HULK with a distinct flow
signature) are already separable by (a); the cross-session gain is large only in
the stealthy regime. In the concentrated scenario (K = 1) there is no campaign, a
single session, so ROC is undefined.

## Running

```bash
# Requires Sprint 2 calibrated: make -C ../sprint-2 calibrate
make scenarios   # stealthy scenarios K = 1/50/1000 (seed 7), converted to sessions
make ablation    # baselines plus configs a/b/c/d, prints the table
```

## Gates

- [x] Baselines and configuration (a) consume the same input
- [x] (a)–(d) over the same input
- [x] The gain of (d) over (a) grows with K and with stealth. Inverted sanity
      check: in a non-stealthy attack all configurations converge
- [ ] n ≥ 30 with bootstrap CIs and paired tests → **Sprint 4**

## Limitations, addressed in Sprint 4

- Single seed here; statistical rigour (n ≥ 30, bootstrap, Wilcoxon, Bonferroni,
  Cohen's *d*) is Sprint 4.
- Weights fixed at 1.0/0.6/0.3; the grid search is Sprint 4.
- The baselines are faithful operationalizations, not exact replications of the
  original papers.
