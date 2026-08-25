# Findings on real captures

What the framework does on CICIDS2017 and CIC-IoT2023, including the parts that
did not work. Entries superseded by later runs have been dropped; the canonical
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

The result is therefore demonstrated on calibrated synthetic traffic, where the
frequency rule and the enrichment rule can be compared side by side under a known
ground truth. Both ship in the repository.

## The negative result on scope derivation

On a monolithic botnet the frequency rule and the enrichment rule agree: 84.0% of
attacker sessions blocked with no collateral observed, against 100% for a global
endpoint rate limit, which by definition disconnects every legitimate user of the
attacked service.

From five stacks on, the frequency rule **inverts**. The modal fingerprint of the
cluster becomes a legitimate one, and the rule blocks 0.0% of the attack and
39.0% of legitimate traffic. A more concentrated benign population (α = 2.0)
raises that collateral to 61.1%.

Enrichment removes the failure, blocking 90.0%, 90.3% and 85.0% of the attack at
M = 5, 25 and 100 stacks, in every case with no collateral observed across
n = 15 campaigns, and reproducing the frequency rule where the latter worked. The
surviving 10–15% is the tail of attackers with one-off fingerprints: scoped
mitigation trades completeness for precision.

## Two conditions bound the mitigation result

**Adversarial.** When the botnet adopts common benign fingerprints, little is
enriched and the rule blocks 30.4% of the attack at 3.78% collateral. The
selectivity advantage is largely lost, but it is lost *safely*: with a stricter ρ
the scope declines to name a fingerprint and degenerates to the global control,
which is the correct report when no discriminator exists.

**Background profile quality.** Moderate drift is tolerable (an α = 2.0 profile
against an α = 1.5 episode gives 90.3% coverage at 0.45% collateral); a flat or
missing profile is not, since every fingerprint then looks rare, the benign head
scores as enriched, and collateral jumps to 81.2%. Coverage is unaffected
throughout, because profile quality governs precision rather than recall. Keeping
the profile fresh is a deployment requirement, not an optimization, and it
implies a fail-safe: where the profile fails a freshness check, scoped mitigation
should be suppressed and the verdict emitted as evidence only.

## Summary

| Claim | Verdict |
|---|---|
| Cross-session beats per-session | Yes, in the stealthy distributed regime; on conventional real captures a strong per-session model already suffices |
| Scoped mitigation | Yes in principle and on calibrated synthetic traffic; not demonstrable on the current real datasets |
| Weight calibration | Ordering corroborated; absolute values still require production data |
| Robustness | No redundancy: detection depends on an observable high-weight discriminator |
