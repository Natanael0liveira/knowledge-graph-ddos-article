# Findings

What the evaluation found on generated, laboratory and production traffic, negative results
included. Each result gives its paper pointer (a section, table, figure or appendix of
[`papers/http-session-noms/article.tex`](../papers/http-session-noms/article.tex)) and the
committed file it comes from. Result files without a directory are in `sprint-6-noms/results/`;
other paths are relative to `experiments/`.

Definitions live elsewhere: the method in [`../docs/concepts.md`](../docs/concepts.md) (sections 4–8),
the metrics in [`../docs/metrics.md`](../docs/metrics.md), the design in
[`../docs/evaluation.md`](../docs/evaluation.md). How each number was produced, and what was fixed
before which data, is in [`METHODOLOGY.md`](METHODOLOGY.md).

**Scenario labels.** Every generated-traffic result names its cache
([`METHODOLOGY.md`, "Scenario caches"](METHODOLOGY.md#scenario-caches)):
- *canonical*: `synth/sprint6_realistic`, stealth mode on the attacked service, Zipf α = 1.5 and
  25 stacks unless a row varies them, with attack-free runs in `synth/sprint6_rule`;
- *sprint-4 cache*: `synth/sprint4_realistic_work`, stealth mode on the attacked service with a
  near-uniform pool of 2,000 benign fingerprints and a monolithic botnet. It backs App. B's weights
  and the KS check of IV-A. Its other results are not in the paper.

## Generated traffic

### Per-session detection is at chance (canonical; App. C)

- The per-session configuration (a), nine flow features in a Random Forest, reaches ROC AUC 0.498
  at K = 50 and 0.503 at K = 1,000. Configuration (b) reaches 0.500 and 0.502, and the three
  academic baselines 0.495–0.518 (`canonical_realistic.json`, `canonical_baselines.json`; 30
  seeds).
- Under four classifier families, (a) stays at 0.488–0.503. This is the chance level that stealth
  mode imposes by design.
- The cross-session configuration (d) reaches 0.927 and 0.982, and (c) 0.499 and 0.659. At
  K = 1,000, paired Wilcoxon tests give p_Bonf = 7.5 × 10⁻⁹ for (d)−(c) and (d)−(a), with Cohen's
  d of 13.5 and 22.3 (`canonical_realistic.json`; the paper prints only p).
- That separability does not transfer across botnet structures. Trained on five stacks, (d) falls
  to 0.61 on 25 stacks and 0.63 on 100. Trained on 25, it falls to 0.48 on five and 0.75 on 100,
  versus 0.95–0.995 on the same M with other seeds (`cross_m_generalization.json`; why the seeds
  are disjoint: [`METHODOLOGY.md`](METHODOLOGY.md#validity-hardening-and-corrections)).

### The scope selects attackers without labels (canonical; V-A, Table III)

Each scope runs alone on the alarm's cluster, with K = 1,000 and 15 seeds
(`symbolic_detector.json`, `unseen_synth_summary.csv`).

- **The modal fingerprint fails once the botnet spans several stacks.** With one botnet stack, the
  modal fingerprint and the binomial test both cover 89.8% of attackers, with no observed
  collateral. From five stacks on, the modal fingerprint belongs to legitimate clients. It covers
  0.0% of attackers and blocks 39.0% of legitimate traffic, or 61.1% under a more concentrated
  legitimate population (α = 2.0). Section III-C predicts this. With the measured head share
  p₁ = 38.4% of requests as a proxy for origins, and a campaign as large as legitimate traffic, the
  modal fingerprint belongs to the attack only while M < 2.3.
- **Profile-relative scopes cover about 90% on new stacks.** The binomial test and the z-score
  cover 90.0% of attackers at five stacks and 90.3% at 25, with no observed collateral in these
  campaigns. The other tenth of the attackers use one-off fingerprints, so scoping trades coverage
  for precision.
- **At 100 stacks the test needs a larger profile.** Each stack then holds about ten attackers, too
  few to stand out against a 1,000-session profile. The test falls to 38.6%, below the z-score
  (80.4%) and the unseen filter (88.1%). A profile pooled over 30 attack-free periods restores
  89.6% (`profile_drift_m100.json`).
- **The unseen filter matches or exceeds the test on new stacks.** Its mean collateral is 0.03%,
  at most 0.5% in one seed, because generated new stacks never occur in legitimate traffic. It
  cannot select shared stacks, which legitimate clients also present. On shared stacks the test
  covers 85.4% of attackers at 2.23% collateral, versus 89.9% at 3.37% for the z-score.
- **A learned model needs labels that an operator lacks during an attack.** A Random Forest on the
  cross-session features (d), trained on campaign labels and held to zero false positives, covers
  36.4% of attackers at 25 stacks and 17.6% at 100. With log b(f) and log enrichment per session it
  covers 87.4% and 86.9%, although it trains on labels from the campaign it scores. At 1% false
  positives, which the test does not need, (d) reaches 66.8% at 25 stacks, or 94.6% with the
  profile. The learned models were not run on shared stacks.

### Two conditions limit the scope (canonical; V-A)

- **Common legitimate fingerprints.** When attackers adopt them, outside the threat model, little
  is enriched. The test covers 30.4% of attackers at 3.78% collateral, the z-score 57.3% at 11.3%,
  the modal scope 3.6% at 39.0%, and the learned model 23.4% at 1% false positives. An alarm then
  mainly invokes the fallback (VI).
- **A poor profile.** A flat or missing profile makes every fingerprint appear rare and raises
  collateral to 77.6%. A profile drifted to α = 2.0 has little effect: coverage stays at 90.3%,
  with no observed collateral (`profile_drift.json`). Section VI asks that profiles be rebuilt from
  windows where the scope selects nothing, and that persistent new fingerprints enter the profile
  only after operator review.

### The rule per window (canonical and attack-free runs; III-B, App. E)

The setup (τ_cluster, the attack-free runs, the spread of benign starts) is in
[`../docs/evaluation.md`](../docs/evaluation.md#timing-and-windows). Results:
`rule_detection_steady60_rate0_bigprof_binom.json` and its window CSV.

- **Ω mostly measures volume.** Its endpoint term, 0.6·C(n, 2), gives 91% of the score in the
  default campaign (Listing 1).
- Over 30 runs each, Ω reaches τ_cluster in 77.8% and 85.7% of the 90 and 35 attack windows at
  K = 1,000 and 50, and in 0.6% of 360 clean windows.
- **Ω alone fires on flash crowds**, in 80–100% of crowds of 25 to 100 users. With the test, the
  rule fires on no clean window (one-sided 95% upper bound 0.8%) and on no flash crowd. It selects
  a filter in every attack window flagged by Ω and blocks a median 75–80% of attackers, with no
  legitimate session hit.
- The test separates these crowds from campaigns because generated crowds draw their users from
  the benign mix the profile describes. A surge on one client type is enriched, and the test does
  not remove every crowd of production clients (V-A, V-B).
- **The weights matter little per window.** With uniform weights, Ω catches 78.9% and 85.7% of the
  attack windows. Without its endpoint term it catches 33.3% and none, while still flagging 53–100%
  of flash crowds (`…_binom_wuniform.json`, `…_binom_wnoep.json`).
- A distinct-origin gate catches 82.2% and 85.7% of the attack windows. With the test, it fires on
  no clean window or flash crowd.
- Generated campaigns, a third to half of the origins in the windows they overlap, are easier than
  the tenth-size production injections, where the gate mostly fails (VI).

### Weights and robustness (sprint-4 cache; App. B, otherwise not in the paper)

- **Weight calibration identifies only the TLS weight (App. B).** The per-session grid search gives
  (w_tls, w_ep, w_net) = (1.0, 0.3, 0.3) (`sprint-4/results/weights_session_realistic.json`).
- Only the TLS fingerprint discriminates alone: AUC 0.93, versus 0.50 for endpoint convergence and
  0.58 for network proximity.
- Every endpoint weight in the grid reaches the same optimal AUC of 0.943, as do the ontology's
  weights (1.0, 0.6, 0.3). Only the top of the weight order is therefore identified.
- **Detection by (d) depends on the shared fingerprint (not in the paper).** As the share of
  attackers on the botnet's fingerprint falls from 1.0 to 0, the AUC of (d) falls from 1.00 through
  0.94, 0.88 and 0.81 to 0.74, over 10 seeds (`sprint-4/results/robustness_sweep.csv`).
- Endpoint convergence does not replace the fingerprint, since legitimate users of the attacked
  service converge on the same endpoint. Alone, it scores AUC 0.50 (App. B).
- The sweep uses Sprint 3's three-feature (a)–(d) sets. Its jitter columns are identical, because
  stealth mode ignores `coordination_temporal_jitter`.

## Laboratory captures (App. C)

- The captures hold five attack types in six dataset–attack pairs: Slowloris, Slowhttptest, HULK
  and GoldenEye in CICIDS2017, and DDoS Slowloris and HTTP Flood in CIC-IoT2023
  (`sprint-3/results/real_multiattack_strong.csv`). A fifth CICIDS2017 attack label, DoS-Other,
  holds 4 sessions (`sprint-2/distributions/_metadata.json`), below the 50 attack sessions the run
  requires (`run_real_multiattack.py --min-attack`), so it is not scored.
- **A strong per-session classifier suffices there.** The nine-feature model reaches AUC 0.98–1.00
  on all six pairs, so cross-session evidence adds little. Real Slowloris, unlike the stealthy
  campaigns, leaves a per-session flow signature.
- On CIC-IoT2023 DDoS Slowloris, whose attack clusters contain seven origins in one of 143 /24
  prefixes, the nine-feature baseline reaches F₁ = 0.900 (AUC 0.987). Three flow features plus
  cross-session evidence reach 0.911 (AUC 0.982). They flag 2.88% and 2.73% of benign sessions
  (`sprint-5/results/klage_comparison.json`).
- **The comparison with KLAGE is uncontrolled.** KLAGE reports F₁ = 0.841 on this attack, and our
  strong per-session baseline also exceeds it. The released code starts from a graph of
  unpublished construction and provides no weights, which prevents a controlled rerun.
- **Scoped mitigation by fingerprint is not demonstrable on these captures.** Their evidence chains
  activate only the endpoint and /24 sub-relations, and the derived scope is an endpoint plus a /24
  prefix (`pillar4-evidence-mitigation/results/chains/completeness_table.csv`).

## Production traffic: the test days (IV-A, V-B to V-D)

Four endpoints of a CDN operator's own services: E1, real-user monitoring beacons; E2, a web
console; E3, an API; E4, single sign-on. Their median windows hold about 3,000, 62, 41 and 20
origins. The split, the injected botnets and what was fixed when are in
[`../docs/evaluation.md`](../docs/evaluation.md#4-production-traffic). Unless a bullet says
otherwise, the configuration is the binomial one: the distinct-origin gate, the binomial test
united with the unseen filter, and known fleets exempt (Table II). Results:
`production_tables.json`, `floor_bands.json`, `fleet_profile.json`, `production_summary.json`,
`waf_labels.json`.

### Calibration

- **Fleets break the binomial model.** At level 0.01, the scope selects a filter in 26.9% of clean
  windows counted in origins, because legitimate fleets switch on together. Counted in
  connections, the share is 60.1%, since one client opens many (App. E).
- The level λ_e is therefore calibrated per endpoint to the 1% false-alarm budget (III-C). At
  levels such as 10⁻⁶⁰, the binomial tail is no longer a reliable probability. It serves as a score
  calibrated on observed traffic.
- On E1, fleets push λ_e to 10⁻⁶⁰. Exempting its five or six known fleets raises it to about
  10⁻²¹ (V-B, Table V).
- Known fleets are fingerprints selected at level 0.01 in at least 5% of calibration windows. They
  act as an allow-list on E1 and the API and carry up to about 7% of their profiles. The scope
  never blocks attackers who use them (III-D).
- **The 5% fleet share was chosen on the test days.** Of four shares, each added to the base rule
  on the first three test days, only 5% gave no more false alarms than the rule alone (5 versus 6;
  the others 12 to 16). By rate times median collateral, the 0.5% share blocked about 25 times
  fewer legitimate clients per clean window (0.0028% versus 0.070%). It also stopped more of a
  100-attacker botnet on new stacks (44.6% versus 30.9%) (IV-B, App. E).

### False alarms

- **Gate and scope each exceed the 1% budget alone.** Pooled over the endpoints, the binomial
  scope alone selects a filter in 2.2% of clean windows, and the gate opens in 3.0%, or 5.4% on E1
  (V-B, Table IV).
- **Together they misfire in 0.1% of clean windows** (5 of 5,643; 95% interval 0.03–0.21%), four
  of them on the web console.
- The five joint misfires, versus 3.5 expected under independence, are compatible with chance
  (P = 0.27). For the post hoc beta-binomial and the calibrated z-score, joint misfires exceed
  independence: 22 and 20 versus 7.5 and 11.9 (P < 10⁻⁴ and P = 0.02; App. E).
- The five misfires block a median 32.9% of the clients in their windows, or an expected 0.03% per
  clean window.
- The gate's other 163 openings (2.9% of clean windows) go to the fallback, a rate limit or a
  challenge to every client.
- Flash crowds of 1,000 production clients trigger the configuration in 22.2% of windows. Its
  filters there are lighter and block a median 4.3% of the window's clients (90th percentile 20.6%,
  not in the paper).
- Misfires cluster by day: 13 of the z-score's 20 and 13 of the beta-binomial's 22 fall on one day
  of the console. Exact intervals assume independent windows, so they understate this uncertainty
  (App. E).
- Cross-fitted (post hoc), the binomial configuration barely changes, with six false alarms versus
  five (V-D).

### The calibration floor and the enrichment limit

- **New stacks.** For a 25-stack botnet on new fingerprints, the unseen filter sets the floor on
  E1–E3 at 139 attackers per window, where the average stack reaches k_min origins. On E4 the test
  selects stacks first, from 84 attackers (Table V).
- **Shared stacks.** All lie beyond the profile's ten most common fingerprints, and most are rare.
  The calibrated level sets their floor, computed at their median share. A typical stack needs 254
  attackers on E1, 8% of its median window, and 4 to 19 median windows on E2–E4, as medians of
  daily ratios.
- The shared-stack floor grows with the number of stacks, from 2% of E1's median window at five
  stacks to 34% at 100. It also grows with fingerprint popularity: ranks 11–35 are never selected
  on E1 and E2 (App. E; `floor_bands.json`).
- **The floor is a ramp.** Below it, chance leaves some stacks large enough to be selected. A
  binomial model of stack sizes predicts 43.1% coverage without the gate for 100 new-stack
  attackers on E1, close to the measured 43.2% (Fig. 2).
- **Beyond the enrichment limit, selection is unlikely.** A stack's expected share stays below
  0.9/M, so a fingerprint whose background share exceeds 0.9/(ρM), 1.2% for M = 25 and ρ = 3, is
  not expected to be selected (III-D).
- The 4–28 most common fingerprints of each endpoint, carrying 86–94% of its origins, exceed the
  limit (V-B).
- A botnet on the endpoint's 25 most common fingerprints, outside the threat model, is therefore
  largely missed. Pooled, the configuration blocks 7.0% of 100 attackers and 23.8% of 1,000. It
  blocks none on E1 and E2, where nearly all 25 fingerprints exceed the limit, and 73.5% of 1,000
  on E4, where only four or five do.

### The trigger decides what is stopped (V-C, Fig. 2)

- A selected fingerprint blocks attackers only in windows where the gate also fires.
- **On E1 the gate rarely opens for a small botnet.** It opens in 6–13% of windows for botnets from
  25 attackers to a tenth of the median window. The configuration therefore blocks 3.4% of a
  100-attacker botnet and 11.8% of a tenth-size botnet, 0.6–37.2% depending on the day. Its scope
  alone would cover 43.2% and 89.6%.
- **On E2–E4 the floor is the main limit.** There 100 attackers are 1.6 to 5 median windows and
  open the gate in 66–100% of windows. A botnet of one median window opens it in only 14–33%.
- Pooled, the configuration stops 38.4% and 77.7% of 100 and 1,000 attackers on new stacks, and
  21.7% and 63.3% on shared ones. The small endpoints dominate these figures (App. E).

### Other triggers and what each scope adds (V-C, V-D, Table VI, Fig. 3)

Both other triggers are exploratory. They were evaluated after the held-out day was read, with the
binomial in sample, as the protocol fixed it.
- **The seasonal gate** divides the distinct origins by their median at the same hour of the
  calibration days, and fires at that ratio's 99th percentile. It raises coverage of E1's
  tenth-size botnet on new stacks from 11.8% to 20.4%.
- Behind it, only the cross-fitted beta-binomial and the unseen filter stay within the budget on
  the web console. The binomial and the in-sample beta-binomial misfire there in 2.0–2.6% of
  windows.
- **Without a gate,** the scope covers about 90% of E1's tenth-size botnet on new stacks each day.
  With known fleets, the binomial scope alone sits at the budget on E1: 0.97% of clean windows
  (95% interval 0.53–1.63%), rising from none on the first two test days to eight of 288 on the
  last.
- **The unseen filter and the test.** The unseen filter selects new stacks of at least k_min
  origins. The test adds shared stacks and, in some configurations, smaller new ones.
- For larger new stacks, including E1's tenth-size botnet, the unseen filter matches the test under
  every trigger, with fewer false alarms and flash-crowd firings. Its false alarms without a gate
  cluster by day (App. E).
- For smaller new stacks, the post hoc cross-fitted beta-binomial adds coverage on E2–E4 and,
  without a gate, on E1: 58% of 100 attackers there, versus the filter's 43%. The binomial adds
  coverage only on single sign-on.
- With the seasonal gate, the cross-fitted beta-binomial covers 53–84% of 100 new-stack attackers
  on E2–E4, but 3.9% on E1.
- Fingerprints absent from the profile appear daily but rarely concentrate: only 0.21% of test-day
  windows contain one with at least k_min origins (App. E; `ja4_churn.json`).
- **Post hoc scopes.** Used without a gate, only the cross-fitted beta-binomial among the
  calibrated scopes approaches the 1% budget (1.1%, Fig. 3).
- In sample, the beta-binomial lowers the shared-stack floor on the three largest endpoints
  (Table V). But 19 of its 22 false alarms occur on the console, where it fires on 74.4% of
  1,000-user crowds.
- Under cross-fitting, the calibrated z-score loses its coverage lead (Fig. 3).

### The WAF's verdicts cannot serve as labels (V-D, App. E)

- The operator's WAF, the only source of labels at hand, blocks a median 9–63% of clients per
  window on E2–E4 and none on E1 (`waf_labels.json`).
- With a profile built without the blocked clients, the scopes reproduce WAF decisions by
  construction: a stable fingerprint is enriched only if 70–88% of its clients were blocked.
- With a profile of all clients, only 0.4–33% of the clients the three calibrated scopes would
  block were also blocked by the WAF, below the 10–63% of a random pick on every endpoint.
- On the API and single sign-on, the scopes catch at most two of the WAF's 38 surges. Most clients
  the WAF blocked shared fingerprints with unblocked clients.

## The held-out day (V-D)

The ninth production day, 2026-09-25, was analyzed with the configuration fixed in advance
(`fresh_day_protocol.md`; results in the `fresh_day` section of `production_tables.json`).
- The binomial configuration produces two false alarms in 1,152 clean windows, consistent with the
  test-day rate by the protocol's rule (P = 0.27).
- The gate opens in only three clean windows, and the scope misfires in two, both on the web
  console. That is more than the test days' five misfires in 168 openings predict (post hoc,
  P = 0.003).
- With three openings, the day cannot measure the scope's reliability once the gate opens
  (`heldout_block_protocol_addendum_metrics.md`). The block measures it (metric 8, below).
- Behind the seasonal gate, the cross-fitted beta-binomial raised no false alarm that day. Without a
  gate it misfired in 1.74% of E1's windows (Table VI).
- On E4 that day, crowds of 1,000 users fired the configuration in 97.2% of windows. In 98% of
  these firings the scope held the same fingerprint, and the filters blocked a median 1.1% of the
  window's clients (`flash_concentration` in `production_tables.json`; not in the paper).
- Every metric of the protocol, including those the paper does not print, is listed with its value
  in `fresh_day_metrics_location.md`.

## The 14-day block (V-D, Table VII, App. E)

Fourteen later days, 2026-09-26 to 10-09, exported after their protocol became public and analyzed
after their export hashes were published (`heldout_block_protocol.md` and its addenda). Each block
day is a test day, calibrated on all earlier days: 16,103 clean windows in all
(`production_tables_block.json`, `block_report.json`).

| Trigger, scope | FA: all, E1, E2–E4 max | E1 tenth-size: new, shared | 100 attackers: new, shared | Coll. |
|---|---|---|---|---|
| Origin gate, binomial (primary) | 0.19, 0.00, 0.42 | 2.9, 2.4 | 36.8, 22.1 | 39.0 |
| Ω gate, binomial test (base rule) | 0.26, 0.00, 0.69 | 0.0, 0.0 | 29.4, 22.0 | 46.6 |
| Origin gate, z-score | 0.12, 0.00, 0.30 | 3.0, 2.6 | 56.2, 26.9 | 40.1 |
| No gate\*, unseen filter | 0.00, 0.00, 0.00 | 89.6, 0.0 | 43.2, 0.0 | – |
| Seasonal gate\*, beta-binomial (cross-fitted) | 0.12, 0.35, 0.05 | 11.8, 11.4 | 61.0, 39.7 | 65.7 |
| No gate\*, binomial, E1 alone | –, 1.56, – | 89.6, 67.7 | 43.4, 4.5 | 4.3 |

In %. FA: false-alarm rate over clean windows. 100 attackers and Coll. (median collateral of a
misfire) are pooled, except in the last row. \*Post hoc configurations, fixed before the block.

- **False alarms double, within the budget (metric 1).** The binomial configuration misfires in 31
  of 16,103 clean windows (0.19%; 95% interval 0.13–0.27%). That is about twice the test-day rate
  and, by the protocol's test, inconsistent with it (P < 10⁻⁴), though below the 1% budget.
- **The scope misfires more often once the gate opens (metric 8).** The gate opens about half as
  often as on the test days, but the scope misfires in 31 of 233 openings (13%), versus five of 168
  on the test days (P < 10⁻¹¹).
- Of these misfires, 30 occur on weekdays (metric 9) and all on E2–E4: 17 in the console's 29 gate
  openings, 10 in the API's 98 and 4 in single sign-on's 95. The configuration misfired in 0 to 6
  windows a day, never on E1.
- The selected filters block a median 39% of those windows' clients, or an expected 0.08% per clean
  window.
- The base rule fired on 30 of those 31 windows. Gate and scope misfired together in 31 windows,
  versus 2.9 if independent.
- Post hoc, counting the test days' own uncertainty, a one-sided Fisher test gives P = 0.07 for the
  rate's rise and P = 0.0002 for the misfires once the gate opens.
- Crowds of 100 users trigger the configuration in 3.4% of windows, and crowds of 1,000 in 18.8%.
- On E1 the origin gate opens in 0.0–13.9% of a tenth-size botnet's windows, depending on the day,
  and the configuration stops 0.0–12.5% of it.
- The z-score reference misfired less than the binomial configuration (20 versus 31), fired on
  fewer crowds and stopped more of 100 attackers.
- No fingerprint absent from the profile reached k_min origins in a block window (metric 10).
- **The pre-specified comparison favors the seasonal gate (metric 7).** Behind it, the cross-fitted
  beta-binomial stays within the budget everywhere (0.05–0.35%) and is preferred on every endpoint
  to the unseen filter without a gate. The rule as written and the amended rule give the same
  verdicts (App. F).
- On E2–E4, it covers 68–88% of 100 new-stack attackers, versus 43% for the unseen filter, and
  34–66% on shared stacks, which the unseen filter cannot select.
- On E1, its advantage comes only from shared stacks. It adds 11.4% coverage of the tenth-size
  botnet, but covers just 11.8% of it on new stacks, versus 89.6% for the unseen filter.
- On E1 the unseen filter produces no false alarms, while the binomial scope with known fleets
  exceeds the budget there without a gate (1.56%).

## The current candidate (VI)

The cross-fitted beta-binomial behind the seasonal gate, with the fallback, a rate limit or a
challenge to every client, below its floor. It was developed post hoc and fixed before the 14-day
block, where the pre-specified comparison preferred it to the unseen filter on every endpoint. The
binomial configuration is the pre-specified one.
- Two factors guide the choice per endpoint: the calibration floor and the trigger's sensitivity.
- On the three smaller endpoints, the candidate selects shared stacks only above 3 to 4 median
  windows, and new stacks from 2 to 3.
- On the block it produced fewer false alarms than the binomial configuration (20 versus 31,
  though 14 versus none on E1). It also stopped more of 100 attackers.
- Crowds of 1,000 users triggered it in one third of windows, generally with lighter filters. Its
  misfires blocked a median two thirds of the clients in their windows.
- On its gate's other clean openings (1.5% of windows), the fallback would act. This cost is not
  included in the false-alarm budget.
- The calibrated z-score misfired as often, with fewer crowd activations but lower attack coverage.
- On E1 the candidate misses most new-stack attackers, whereas the unseen filter without a gate
  retains high coverage with no false alarm on the block. Running both there is untested.
- Behind the seasonal gate, 12 of the beta-binomial's 14 misfires on E1 fall on two days (App. E).
- **Open.** No later day has tested this choice, so the next step is a longer evaluation. The
  binomial configuration misfires mainly on weekdays, which suggests that a gate calibrated by day
  of the week may help. Whether an attack near the floor exhausts a service depends on its spare
  capacity, which was not measured.

## Summary

| Claim | Result | Paper | Source |
|---|---|---|---|
| Per-session detection of stealthy campaigns (canonical) | At chance: AUC 0.488–0.503 under four classifier families, 0.495–0.518 for three baselines | App. C | `canonical_realistic.json`, `canonical_baselines.json` |
| Cross-session features with labels (canonical) | Separate (AUC 0.927 and 0.982) but do not transfer across stack counts (0.48–0.75) | App. C | `canonical_realistic.json`, `cross_m_generalization.json` |
| The modal fingerprint (canonical) | From five stacks, 39.0% of legitimate traffic and no attackers | V-A, Table III | `unseen_synth_summary.csv` |
| Profile-relative scoping (canonical) | 90.0–90.3% of attackers on 5 to 25 new stacks, no observed collateral; 85.4% of shared stacks at 2.23% | V-A, Table III | `symbolic_detector.json`, `unseen_synth_summary.csv` |
| Limits on generated traffic (canonical) | Common fingerprints: 30.4% at 3.78% collateral; a flat profile: 77.6% collateral | V-A | `unseen_synth_summary.csv`, `profile_drift.json` |
| False alarms, test days | 0.1% (5 of 5,643) for gate and scope together; 2.2% for the scope alone, 3.0% for the gate alone | V-B, Table IV | `production_tables.json` |
| False alarms, held-out day | 2 of 1,152, consistent (P = 0.27); the gate opened in 3 clean windows | V-D | `production_tables.json` |
| False alarms, 14-day block | 0.19% (31 of 16,103): about twice the test-day rate, inconsistent with it, within the budget | V-D, Table VII | `production_tables_block.json`, `block_report.json` |
| Cost of a misfire | A median 33–39% of the window's clients | V-B, V-D | `production_tables.json`, `production_tables_block.json` |
| What limits coverage | The calibration floor (fleets), the enrichment limit (common fingerprints) and the trigger (E1's gate misses most of a small botnet) | V-B, V-C | `production_tables.json`, `floor_bands.json` |
| Current candidate | Cross-fitted beta-binomial behind the seasonal gate, fallback below its floor; on E1 the unseen filter without a gate keeps 89.6% of the tenth-size botnet on new stacks | VI, Table VII | `production_tables_block.json`, `block_report.json` |
| WAF verdicts | Cannot serve as labels | V-D | `waf_labels.json` |
| Laboratory captures | A strong per-session model suffices (AUC 0.98–1.00); scoping by fingerprint is not demonstrable; the KLAGE comparison is uncontrolled | App. C | `sprint-3/results/real_multiattack_strong.csv`, `sprint-5/results/klage_comparison.json` |
| Weights (sprint-4 cache) | Only the TLS weight is identified; per window, Ω mostly measures volume and uniform weights detect as well | App. B, III-B, App. E | `sprint-4/results/weights_session_realistic.json`, `rule_detection_steady60_rate0_bigprof_binom_w*.json` |
| Robustness to JA4 sharing (sprint-4 configuration) | AUC of (d) from 1.00 to 0.74 as JA4 sharing goes to zero | not in the paper | `sprint-4/results/robustness_sweep.csv` |
