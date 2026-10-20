# Sprint 4: earlier 30-seed run and weight calibration

This stage ran the (a) to (d) ablation and the baselines over 30 seeds, with
bootstrap intervals and paired tests, and calibrated the weights of Ω(S). Both ran
on the scenario cache `$DATA_ROOT/synth/sprint4_realistic_work`: legitimate users
on the attacked service, "a near-uniform benign vocabulary against a monolithic
botnet" (Appendix B), with 2,000 benign fingerprints at α = 0 and one botnet stack.
The weight calibration is the paper's Appendix B. The paper's ablation numbers come
from the sprint-6 rerun on the canonical scenario (α = 1.5, M = 25), and this
stage's run stays for provenance. Sprint 6 imports its feature sets
(`STRONG_SETS`, `STRONG_FLOW`), its statistics helpers (`boot_ci`, `cohens_d`) and
`ensure_scenario`.

## In the paper

- **Appendix B.** The weight calibration
  ([`results/weights_session_realistic.json`](results/weights_session_realistic.json)):
  the grid {0.3, 0.5, 0.7, 0.9, 1.0}³ (125 combinations) on 60 scenarios gives
  (1.0, 0.3, 0.3). The TLS signal alone reaches AUC 0.93, versus 0.50 for endpoint
  convergence and 0.58 for network proximity. Every endpoint weight in the grid
  reaches the same AUC of 0.943, as does the ontology's (1.0, 0.6, 0.3).
- **Appendix C.** Sprint 6 reruns this stage's design: 30 seeds, a 70/30 split,
  bootstrap intervals and paired Wilcoxon tests with Bonferroni. The printed
  numbers come from sprint-6
  [`canonical_realistic.json`](../sprint-6-noms/results/canonical_realistic.json).
- **Not in the paper:** this run's AUCs, the robustness sweep, the bar chart and the
  cluster-level grids.

## Inputs

- `$DATA_ROOT/synth/distributions/` from [sprint 2](../sprint-2/), flow files
  included (`run` checks only for `session_requests.json`).
- `WORK = $DATA_ROOT/synth/sprint4_realistic_work`. `run` generates any missing
  scenario there (`K<K>_seed<s>.parquet`); `weights` and `weights-cluster` read it.
- `SEEDS ?= 30` and `K ?= 50 1000`. Results go to `$DATA_ROOT/results/`; the
  committed copies sit in `results/`.

## Run

| Target | What it does | Writes, under `$DATA_ROOT/results/` |
|---|---|---|
| `help` | Lists the targets; works without `.env` | |
| `run` | 30 seeds × K ∈ {50, 1000}: (a) to (d) with the nine-feature sets (`--strong`) and the baselines, bootstrap 95% intervals, and Wilcoxon tests of (d)−(c) and (d)−(a) with Bonferroni over four tests | `sprint4_aggregated.json`, `sprint4_runs.csv` |
| `weights` | Per-session weight calibration on the 60 scenarios of `WORK` | `weights_session_realistic.json` |
| `weights-cluster` | The earlier cluster-level grid, on the first 20 scenarios of `WORK` | `sprint4_weights.json` |
| `figures` | AUC versus K with 95% intervals, from `sprint4_runs.csv` | `figures/money_figure_auc_vs_k.png` |
| `all` | `run`, `weights` and `figures` | |
| `clean` | Removes `WORK`, which sprint-6 `ml`, `window` and `purity` also read, and this stage's JSON and CSV | |

Without a target (`../data` is the symlink to `DATA_ROOT`):

```bash
# Robustness sweep: AUC of (a), (c) and (d) as coordination_ja4_share and the jitter vary
../.venv/bin/python scripts/robustness_sweep.py --dist-dir ../data/synth/distributions \
  --work ../data/synth/sprint4_robust --out-dir ../data/results --seeds 10

# The bar chart of this run, as committed
../.venv/bin/python scripts/make_money_figure.py --in results/sprint4_aggregated.json \
  --out results/money_figure_auc_vs_k.png

# AUC of share_ja4 alone as coordination_ja4_share varies; prints only, no committed output
../.venv/bin/python scripts/ja4_isolation.py --dist-dir ../data/synth/distributions \
  --work ../data/synth/sprint4_ja4 --K 500 --seeds 5 --benign-pool 2000
```

## Outputs

| File | Producer | In the paper |
|---|---|---|
| `results/weights_session_realistic.json` | `make weights` | App. B |
| `results/sprint4_aggregated.json`, `results/sprint4_runs.csv` | `make run` | No |
| `results/robustness_sweep.csv` | `robustness_sweep.py` | No |
| `results/money_figure_auc_vs_k.png` | `make_money_figure.py`; `make figures` draws a line chart of the same name under `$DATA_ROOT/results/figures/` | No; it served the earlier manuscript |
| `results/sprint4_weights.json` | `weight_search.py` (`weights-cluster`), on the earlier `synth/sprint4` cache | No |
| `results/weights_hard.json` | `weight_search.py` on scenarios of `../sprint-2/configs/scenario_hard.yaml` | No |
| `results/stealth_flow_strong.csv`, `results/stealth_flow_thin.csv` | sprint-3 `run_real_multiattack.py` on one K = 1,000 stealth scenario, with and without `--strong-baseline` (commit 87026cd) | No; no script reads them |

## Results

The earlier run, ROC AUC over 30 seeds
([`results/sprint4_aggregated.json`](results/sprint4_aggregated.json)):

| Configuration | K = 50 | K = 1,000 |
|---|---|---|
| (a) nine flow features | 0.519 | 0.502 |
| (b) (a) plus `has_identity`, `dst_port_first` | 0.527 | 0.503 |
| (c) (a) plus `share_net` | 0.523 | 0.664 |
| (d) (a) plus `share_ja4`, `share_net`, `cluster_size` | 0.968 | 0.976 |
| Baselines: Fernandes, Bharathi (k-means), Kemp | 0.517–0.520 | 0.501–0.502 |

For (d)−(c) and (d)−(a), p_Bonf = 7.5 × 10⁻⁹ at both K. This is the smallest p
that the exact Wilcoxon test gives for 30 pairs (2⁻²⁹), times four: (d) wins on
every seed. Cohen's d is 8.8 and 7.8 at K = 50, and 12.2 and 19.6 at K = 1,000. The
sprint-6 rerun gives (d) 0.927 and 0.982, and d = 13.5 and 22.3 at K = 1,000.

The weights ([`results/weights_session_realistic.json`](results/weights_session_realistic.json),
60 scenarios, 91,500 sessions): (w_tls, w_ep, w_net) = (1.0, 0.3, 0.3) reaches AUC
0.943. So do the ontology's (1.0, 0.6, 0.3) and every endpoint weight in the grid
with w_tls = 1.0 and w_net = 0.3. Alone, the TLS feature reaches 0.930, the cluster
size (the endpoint proxy) 0.503 and the /24 feature 0.577. No ±20% change of a
best weight lowers the AUC, and the best and worst vectors of the grid differ by
0.0415. Only the TLS weight is identified (Appendix B).

The robustness sweep ([`results/robustness_sweep.csv`](results/robustness_sweep.csv),
10 seeds, `FLOW` sets, K = 500 by the script's default, which the CSV does not
record): AUC(d) falls from 1.000 to 0.939, 0.883, 0.808 and 0.738 as
`coordination_ja4_share` goes from 1.0 to 0.75, 0.5, 0.25 and 0. (a) stays at
0.497–0.505. The three jitter levels give identical AUCs, because stealth mode
ignores `coordination_temporal_jitter`.

The cluster-level grids saturate. In `sprint4_weights.json` the best vector, the
ontology's and every ±20% change score AUC 1.0. `weights_hard.json` picks
(0.3, 0.3, 1.0), the first of several vectors at 1.0, versus 0.972 for the
ontology's weights.

## Caveats

- The cache is near-uniform and monolithic, unlike the canonical scenario. Cite
  every number from it with its cache.
- Bharathi here is the k-means-only adaptation (`bharathi2012`). The paper's
  PCA → k-means version came later (sprint-6 `canonical_baselines.json`).
- The committed `results/sprint4_weights.json` dates from when `WORK` pointed to
  the earlier `synth/sprint4` cache (commit 8b5f7fd), so `make weights-cluster` on
  today's `WORK` does not reproduce it. No target generates the `scenario_hard.yaml`
  scenarios behind `weights_hard.json`, and neither file records its scenario count.
- No weight was calibrated on production traffic. Per window, uniform weights detect
  as well (Appendix E).
- Only two values of K were run, 50 and 1,000.
