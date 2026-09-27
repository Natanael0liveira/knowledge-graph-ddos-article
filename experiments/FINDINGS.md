# Findings

What the framework does on CICIDS2017 and CIC-IoT2023, on calibrated synthetic
traffic and on production traffic, including the parts that did not work. Entries superseded by later runs have been dropped; the canonical
scenario is the realistic same-service one, where legitimate users access the
attacked service on the same port.

---

## Detection generalizes across attacks; the cross-session gain does not

The pipeline detects across six attacks (Slowloris, slowhttptest, HULK,
GoldenEye, HTTP-Flood, DoS-Other) on two datasets. But on these captures the
**cross-session gain is roughly zero**: a strong per-session classifier already
separates the traffic, because the attacks were never calibrated to mimic benign
flow. This is not a failure of the framework, it is the boundary of when the
framework is needed, and the paper reports it as such.

## Endpoint redundancy was an artifact

An early run suggested that endpoint convergence could compensate for the loss of
the TLS fingerprint. It cannot. In the realistic same-service scenario, where
legitimate users hit the attacked endpoint too, they converge on it as well.

The robustness sweep makes the dependency explicit: as the fraction of origins
sharing the TLS fingerprint falls, AUC for configuration (d) decreases
monotonically from 1.00 to ≈ 0.74 under full randomization
(`robustness_sweep.csv`). That residual above chance is an artifact of a finite
benign JA4 pool and should tend to chance at internet-scale diversity.

**Detection depends on an observable high-weight discriminator**, JA4 or reused
identity. There is no redundancy to fall back on.

## Weight calibration corroborates the ordering, not the values

In the realistic same-service scenario, per-session calibration over the weight
grid returns a best vector of (w_tls = 1.0, w_ep = 0.3, w_net = 0.3), and the
TLS fingerprint is the only individually discriminative signal (isolated
AUC = 0.93, against 0.50 for endpoint convergence and 0.58 for network
proximity). The paper's weights (1.0, 0.6, 0.3) reach the **same optimal
AUC = 0.943** and are insensitive to ±20% perturbation.

So calibration validates the **ordering**. In the pure same-service regime the
medium and low weights are not separately identifiable, since in isolation both
sit near chance, and their absolute values remain open pending production traffic
with partial and conflicting signals.

## Scoped mitigation is not demonstrable on CIC captures

Pillar 4 runs on real clusters, but scoped mitigation does not manifest there.
The reason is structural, not a bug: the CIC captures are LAN traffic and largely
non-TLS, so the JA4 discriminator the scope derivation depends on is either
absent or degenerate.

Counted in origins, the five CICIDS2017 clusters hold one to three sources, below
k_min, and the two of CIC-IoT2023 hold seven. The result is therefore demonstrated on
calibrated synthetic traffic, where the frequency rule and the enrichment rule can be
compared side by side under a known ground truth (both ship in the repository), and
measured on production traffic (below).

## The negative result on scope derivation

On a monolithic botnet the frequency rule and the enrichment rule agree: 89.8% of
attacker sessions blocked with no collateral observed, where a challenge to every
client, the fallback without a scope, would burden every legitimate user of the
attacked service.

From five stacks on, the frequency rule **inverts**. The modal fingerprint of the
cluster becomes a legitimate one, and the rule blocks 0.0% of the attack and
39.0% of legitimate traffic. A more concentrated benign population (α = 2.0)
raises that collateral to 61.1%.

Enrichment removes the failure, blocking 90.0% and 90.3% of the attack at M = 5 and
25 stacks with no collateral observed across n = 15 campaigns, and reproducing the
frequency rule where the latter worked; a per-fingerprint z-score does the same. The
surviving 10% is the tail of attackers with one-off fingerprints: scoped mitigation
trades completeness for precision. At 100 stacks a stack of about ten sessions among
two thousand cannot be told from the tail of a 1,000-session profile, and the test
falls to 38.6%; a profile pooled over 30 attack-free periods restores 89.6%, and the
z-score keeps 80.4%.

## Two conditions bound the mitigation result

**Adversarial.** When the botnet adopts common benign fingerprints, little is
enriched and the rule blocks 30.4% of the attack at 3.78% collateral. The
selectivity advantage is largely lost, but it is lost *safely*: with a stricter ρ
the scope declines to name a fingerprint and degenerates to the global control,
which is the correct report when no discriminator exists.

**Background profile quality.** Moderate drift is tolerable (an α = 2.0 profile
against an α = 1.5 episode gives 90.3% coverage with no collateral); a flat or
missing profile is not, since every fingerprint then looks rare, the benign head
scores as enriched, and collateral jumps to 77.6%. Keeping the profile fresh is a
deployment requirement, not an optimization, and it implies a fail-safe: where the
profile fails a freshness check, scoped mitigation should be suppressed and the
verdict emitted as evidence only.

## On production traffic

Eight days of four endpoints of a CDN operator's own services, with a botnet injected
into the counts and a ninth day analyzed with every choice fixed in advance
(`sprint-6-noms/README.md`, sections 9, 11 to 13 and 15 to 17).

- **The binomial model is wrong there, so the level is an empirical quantile.** Fleets
  of legitimate clients switch on together; at the nominal level the scope names a
  filter in 26.9% of clean windows counted in origins. The level is set so that the
  scope alone names one in at most 1% of the calibration windows, which pushes it to
  10⁻⁶⁰ on the busiest endpoint.
- **The 1% does not hold out of sample; the configuration's rate does.** The scope
  alone fires on 2.2% of clean test-day windows and the distinct-origin gate on 3.0%.
  The recommended configuration needs both and raises false alarms on 0.1% (5 of
  5,643), 6 when calibrated out of sample, and 2 of 1,152 on the held-out day, a test
  with a power of only 37% against a tripled rate, whose gate opened in only 3 windows.
  Joint misfires of gate and scope exceed independence clearly for the beta-binomial
  and the z-score (Poisson P < 10⁻⁴ and 0.02) and within chance for the binomial
  configuration (5 against 3.5, P = 0.27). Misfires cluster by endpoint-day, which the
  exact interval ignores; a bootstrap over five days per endpoint is too coarse to
  fix that (it gave a narrower interval than the exact one).
- **The fleet share was chosen by misfire count.** On
  the design days the 5% share had the fewest false alarms (5 against 6 for the base
  rule, 12 to 16 for smaller shares), which the protocol set as the criterion. By rate
  times median collateral, the paper's own metric, the 0.5% share blocked about 25
  times fewer legitimate clients per clean window (0.0028% against 0.070%) and stopped
  more of 100 attackers on new stacks (44.6% against 30.9%). Re-choosing now would be
  post hoc; the paper discloses it in Table II's note and Appendix E.
- **Fleets set a calibration floor.** A 25-stack botnet on fingerprints real clients
  also present is named only past 8% of the busiest endpoint's window and 4 to 19
  whole windows on the small ones; new stacks are named from ⌈5M/0.9⌉ = 139 attackers
  by the unseen filter. The floor is a ramp, not a cliff: below it the scope names the
  stacks chance makes larger, as a binomial model of stack sizes predicts. A harder
  limit sits past it: no 25-stack botnet can be enriched on a fingerprint more common
  than 0.9/(ρM) = 1.2%, and those fingerprints carry 86–94% of each endpoint's origins.
  A beta-binomial background, built after the held-out day was read, lowers the
  shared-stack floor to 6% and at most 4.4 windows out of sample.
- **Naming is not stopping: the trigger lets most of a small botnet through.** At a
  tenth of the busiest endpoint's window the scope names the botnet in every window, but
  the gate fires in 0.7–42% of them by day, so 11.8% of the attackers are stopped.
  A seasonal gate (the ratio to the same hour's median) stops 20.4%, and the scope as
  its own trigger 89.4–89.8% on every day, within the 1% budget on that endpoint
  (0.97%, 0 of 288 on the held-out day) but not on the small ones (1.5–4.4%). Post
  hoc. Round 18: that 0.97% sits at the budget (95% interval 0.53–1.63%, rising 0, 0,
  1, 5, 8 by day) and needs the fleet exemption (92 of 1,440 without it); under the
  cross-fitted beta-binomial the scope alone reached 1.74% on the held-out day. The
  cross-fitted beta-binomial behind the seasonal gate stays within the budget on every
  endpoint on both day sets (4 of 5,643, 0 of 1,152) and stops 20.4% (15.3% held out),
  so the paper proposes it as the next test's primary, the scope alone on E1 as secondary.
- **On new stacks the unseen filter alone matches every scope (round 19).** Under the
  origin gate, the seasonal gate and as its own trigger, the unseen filter stops as much
  of E1's tenth-size botnet on new stacks as the calibrated scopes, with fewer false
  alarms (0 behind the seasonal gate; 0.28% on E1 and at most 0.42% elsewhere as its own
  trigger) and fewer flash-crowd firings (3.4% of 1,000-user crowds). The enrichment
  test's gain is on shared stacks: 14.4-15.1% behind the seasonal gate and 61.1-65.7% as
  its own trigger, where the unseen filter names none.
- **Flash-crowd firings are light.** The filters the binomial configuration installs
  on 1,000-user crowds block a median 4.3% of the window's clients (90th percentile
  20.6%), against 32.9% for clean-window misfires. On the held-out day E4's crowds fire
  it in 97.2% of windows, 98% of them on one fingerprint far more common that day than
  in the profile, at a median 1.1%.
- **The boundary holds.** A botnet on the endpoint's 25 most common fingerprints is
  mostly missed (7.0% and 23.8% of 100 and 1,000 attackers).
- **The WAF's verdicts are not labels.** Scored against the clients the operator's WAF
  blocked, the scopes agree only under a profile that excludes those clients, where
  agreement is built in; under a profile of all clients they do worse than a random
  pick.

## Summary

| Claim | Verdict |
|---|---|
| Cross-session beats per-session | Yes, in the stealthy distributed regime; on conventional real captures a strong per-session model already suffices |
| Scoped mitigation | Yes on calibrated synthetic traffic; on production traffic 0.1% false alarms and a calibration floor set by fleets, with detection measured only for an injected botnet; not demonstrable on the CIC captures |
| Calibration out of sample | The configuration keeps its rate; each calibrated component alone exceeds its 1% target |
| Weight calibration | Only the top of the ordering is supported; at window scale Ω is volume, and uniform weights detect as well |
| Robustness | No redundancy: detection depends on an observable high-weight discriminator |
