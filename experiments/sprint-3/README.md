# Sprint 3: baselines, first ablation and laboratory captures

This stage holds the code of configurations (a) to (d) and of the three academic
baselines, which sprints 4 and 6 import. `make ablation` ran the first,
single-seed version of the ablation. The paper's ablation and baseline numbers
(Appendix C) come from sprint-6 `make canonical baselines`. This stage's committed
results are the per-attack runs on the two laboratory captures.

## In the paper

- **Appendix C, configurations and baselines.** Configurations (a) to (d) and the
  reimplemented PCA profiling, PCA with k-means, and RF/SVM baselines are this
  stage's code ([`scripts/run_ablation.py`](scripts/run_ablation.py),
  [`scripts/baselines.py`](scripts/baselines.py)). The printed numbers come from
  sprint 6: at K = 50 and 1,000, (a) reaches 0.498 and 0.503, (b) 0.500 and 0.502,
  (d) 0.927 and 0.982, and the three baselines 0.495–0.518
  ([`canonical_realistic.json`](../sprint-6-noms/results/canonical_realistic.json),
  [`canonical_baselines.json`](../sprint-6-noms/results/canonical_baselines.json)).
- **Appendix C, laboratory captures.** "Real Slowloris, unlike our stealthy
  campaigns, leaves a per-session flow signature." `results/real_multiattack_strong.csv`
  shows this for every attack of both captures. The paper prints only the
  CIC-IoT2023 numbers of [sprint 5](../sprint-5/).

## Inputs

- `$DATA_ROOT/synth/distributions/` from sprint 2 (`make -C ../sprint-2 calibrate`;
  `scenarios` checks for it).
- `$DATA_ROOT/processed/sessions/cicids2017.parquet` and `cic-iot-2023.parquet`
  from [sprint 1](../sprint-1/), labeled, for `multiattack`.
- `SEED` (default 7) for `scenarios`.

The feature sets, in code ([`../../docs/evaluation.md`](../../docs/evaluation.md)
says what each configuration tests):

| Set | Features | Used by |
|---|---|---|
| `FLOW` | `n_requests`, `duration_s`, `req_per_s` | `make ablation`, `make multiattack`, the sprint-4 robustness sweep |
| `STRONG_FLOW` | `FLOW` plus `fwd_bytes_sum`, `bwd_bytes_sum`, `fwd_pkts_sum`, `bwd_pkts_sum`, `iat_mean_mean` and `iat_std_mean`: nine | `run_real_multiattack.py --strong-baseline`, sprint-4 `--strong`, sprint 6 |
| (b) adds | `has_identity` (the session has a JA4) and `dst_port_first` | |
| (c) adds | `share_net` | |
| (d) adds | `share_ja4`, `share_net`, `cluster_size` | |

`share_ja4` and `share_net` count the session's peers in its detection cluster
with the same JA4 or /24, and `cluster_size` is that cluster's size. The cluster
chains an endpoint's sessions while consecutive starts stay within 300 s
(sprint-1 `compute_coordination.py`). No feature reads the weights of Ω(S).

The baselines run on the flow features of (a). `fernandes2015` scores the PCA
reconstruction error. `bharathi2012_pca` follows the published PCA → k-means →
per-cluster threshold, and is the paper's. `bharathi2012`, the earlier
k-means-only adaptation, is still printed. `kemp2023` averages a random forest and
an SVM.

## Run

| Target | What it does | Writes |
|---|---|---|
| `help` | Lists the targets; works without `.env` | |
| `scenarios` | Stealth scenarios at K = 1, 50 and 1,000 from `scenario_stealth.yaml`, seed `SEED`, converted to sessions | `$DATA_ROOT/synth/sprint3/stealth_K*.{jsonl,parquet}` |
| `ablation` | ROC AUC of (a) to (d) and of the four baselines on those scenarios, with the `FLOW` sets; prints a table | `$DATA_ROOT/logs/sprint3_ablation.log` |
| `multiattack` | Each labeled attack against BENIGN on both captures, (a) and (d) with `FLOW` | `results/real_multiattack.csv` |
| `clean` | Removes `$DATA_ROOT/synth/sprint3` | |

Without a target, the nine-feature run:

```bash
../.venv/bin/python scripts/run_real_multiattack.py --strong-baseline \
  --dataset cicids2017=../data/processed/sessions/cicids2017.parquet \
            cic-iot-2023=../data/processed/sessions/cic-iot-2023.parquet \
  --out results/real_multiattack_strong.csv
```

`../data` is the symlink to `DATA_ROOT` that `setup-data-storage.sh` creates.

## Outputs

| File | Producer | In the paper |
|---|---|---|
| `results/real_multiattack.csv` | `make multiattack` | No |
| `results/real_multiattack_strong.csv` | the command above | App. C states its conclusion |

Each row holds one attack and one configuration: F₁, precision, recall and ROC AUC
on a 70/30 split, and `collateral_fpr_benign`, the share of benign test sessions
flagged at threshold 0.5.

## Results

ROC AUC of each attack against BENIGN. The cross-session columns add `share_ja4`,
`share_net` and `cluster_size`.

| Capture | Attack | Attack sessions | (a) `FLOW` | (d) `FLOW` + cross-session | (a) `STRONG_FLOW` | (d) `STRONG_FLOW` + cross-session |
|---|---|---|---|---|---|---|
| CICIDS2017 | GoldenEye | 7,472 | 0.563 | 1.000 | 1.000 | 1.000 |
| CICIDS2017 | HULK | 30,391 | 0.722 | 1.000 | 1.000 | 1.000 |
| CICIDS2017 | Slowhttptest | 4,217 | 0.634 | 1.000 | 1.000 | 1.000 |
| CICIDS2017 | Slowloris | 4,035 | 0.582 | 1.000 | 1.000 | 1.000 |
| CIC-IoT2023 | HTTP Flood | 380,004 | 0.517 | 0.964 | 0.999 | 1.000 |
| CIC-IoT2023 | Slowloris | 118,063 | 0.554 | 0.991 | 0.980 | 0.998 |

The benign side holds 322,658 sessions on CICIDS2017 and 289,170 on CIC-IoT2023.
With three flow features, (a) reaches 0.517–0.722. With all nine it reaches
0.980–1.000, so a per-session model suffices on these captures (Appendix C). The
earlier 30-seed ablation is in
[`../sprint-4/results/sprint4_aggregated.json`](../sprint-4/results/sprint4_aggregated.json).

## Caveats

- `make ablation` differs from the paper's ablation. It uses the three-feature
  `FLOW` sets, one seed and `scenario_stealth.yaml` without the sprint-6 overrides,
  which means a uniform 2,000-fingerprint benign pool and a monolithic botnet. The
  paper's run has nine features, 30 seeds, α = 1.5 and M = 25 (sprint-6
  `make canonical baselines`).
- At K = 1 the scenario holds a single attack session, and `run_ablation.py` skips
  any scenario with fewer than two.
- On CICIDS2017 every attack comes from one attacker host to one victim endpoint
  (`../sprint-1/scripts/label_cicids2017.py`), so the /24 and cluster features of
  (d) separate it trivially.
- `run_real_multiattack.py` skips attacks with fewer than 50 sessions
  (`--min-attack`), which drops the 4 DoS-Other sessions.
- The baselines are operationalizations, since the original papers' hyperparameters
  are not all recoverable (`baselines.py`). Bharathi's threshold is under-specified,
  so `bharathi2012_pca` divides the distance to the nearest centroid by that
  cluster's 95th-percentile training distance.
