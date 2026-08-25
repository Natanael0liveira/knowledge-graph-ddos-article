# Sprint 4 — Full statistical run and weight calibration

Turn the preliminary result of Sprint 3 into statistically solid numbers
(n ≥ 30 seeds, bootstrap CIs, paired tests with Bonferroni and Cohen's *d*) and
calibrate the weights of Ω(S).

> **Which numbers are canonical.** This sprint established the statistical
> machinery on the scenario as it stood at the time. Sprint 6 then added the two
> realism parameters, benign fingerprint popularity (α) and botnet composition
> (M), and re-ran the same design on the resulting canonical scenario
> (α = 1.5, M = 25). **The paper reports the Sprint 6 run**, whose artifact is
> `../sprint-6-noms/results/canonical_realistic.json`. The values below are the
> earlier run and are kept for provenance.

## Running

```bash
make run       # 30 seeds x K in {50, 1000}: ablation a/b/c/d, 3 baselines, tests
make weights   # grid search over w_i in {0.3, 0.5, 0.7, 0.9, 1.0}^3, plus sensitivity
make figures   # AUC vs K with 95% CIs
```

## Results, earlier run (n = 30 seeds, stealthy distributed, same-service)

Legitimate users reach the attacked service on `:443`, so **no per-session
attribute**, target port included, separates benign from attacker. The per-session
baseline is **strong**: 8–9 flow features, not a lean 3-feature strawman.

| Config | K = 50 | K = 1000 |
|---|---|---|
| (a) per-session ML (strong) | 0.519 | 0.502 |
| (b) ontology without `relatedBy` | 0.527 | 0.503 |
| (c) network proximity only | 0.523 | 0.664 |
| **(d) full framework** | **0.968** | **0.976** |
| Baselines (Fernandes / Bharathi / Kemp) | ~0.50 | ~0.50 |

| Contrast | p (Bonferroni) | Cohen's *d* |
|---|---|---|
| K = 1000, (d)−(c) | 7.4 × 10⁻⁹ | +12.2 |
| K = 1000, (d)−(a) | 7.4 × 10⁻⁹ | +19.6 |

In the canonical Sprint 6 run the same contrasts give *d* = 13.5 and *d* = 22.4
at p_bonf = 7.5 × 10⁻⁹, with (d) at 0.927 and 0.982.

**Reading.** With a strong per-session baseline, (a) sits at chance even with 8–9
features, so the separation in the stealthy regime is not in per-session flow
features but in the correlation structure between sessions. Configuration (b),
which adds per-session ontological attributes but no `relatedBy_*` relation, also
sits at chance: since benign and attacker share the endpoint, no per-session
attribute distinguishes them. Only the explicit relations in (d) separate. This
is the **strongest** version of the result, and it can no longer be dismissed as a
target-port artifact.

## Gates

- [x] n ≥ 30 runs per configuration
- [x] (d)−(c) significant in Scenario C after Bonferroni
- [x] Weights documented with ±20% sensitivity

## Weight calibration

In the realistic same-service scenario, per-session calibration corroborates the
proposed ordering. The best vector is **(w_tls = 1.0, w_endpoint = 0.3,
w_net = 0.3)**, TLS dominant, and the TLS fingerprint is the **only individually
discriminative signal** (isolated AUC 0.93, against 0.50 for endpoint convergence
and 0.58 for network proximity). The paper's weights (1.0 / 0.6 / 0.3) reach the
**same optimal AUC 0.943** and are robust to ±20% perturbation.

The honest nuance to keep: this validates the **ordering** (TLS ≫ endpoint ≈
network), **not** the absolute values. In the pure same-service regime the medium
and low weights are not separately identifiable. Full calibration still requires
production data. Documented in
[`results/weights_session_realistic.json`](results/weights_session_realistic.json).

> **Superseded note.** In an earlier, too-easy synthetic scenario the grid search
> appeared to saturate, every combination scoring high, and calibration was
> declared inconclusive. In the realistic same-service scenario the grid
> desaturates and corroborates the ordering above.

## Limitations

- Two K points (50, 1000). A denser curve (10, 50, 200, 1000, 10000) would make a
  better figure.
- Absolute weight values still require production traffic with partial and
  conflicting signals.
