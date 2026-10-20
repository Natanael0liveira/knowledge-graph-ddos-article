# Sprint 5: comparison with KLAGE on CIC-IoT2023

This stage scores DDoS Slowloris against every other session of CIC-IoT2023, to set
our numbers beside the F₁ = 0.841 that KLAGE (Belcastro et al., Future Generation
Computer Systems, 2026) reports for that attack. The comparison is uncontrolled
(Appendix C). Appendix C's F₁ and AUC on this capture come from here.

## In the paper

- **Appendix C.** "A strong per-session baseline using nine flow attributes reaches
  F₁ = 0.900 (AUC 0.987), while three of them plus cross-session evidence reach
  0.911 (AUC 0.982)." The paper reports the comparison in its text and has no KLAGE
  table.

## Inputs

- `$DATA_ROOT/processed/sessions/cic-iot-2023.parquet`, built by
  [sprint 1](../sprint-1/). `run` reads only this file, so `clusters` and the graph
  targets are optional here:

  ```bash
  cd ../sprint-1
  make DATASET=cic-iot-2023 extract-ja4 extract-flows sessions
  ```

- The PCAPs, saved under `$DATA_ROOT/raw/cic-iot-2023/`. They come from UNB
  (https://www.unb.ca/cic/datasets/iotdataset-2023.html, the account used for
  CICIDS2017) or from the IEEE DataPort mirror
  (https://ieee-dataport.org/documents/ciciot2023-dataset). Sprint 1's
  `build_sessions.py` labels sessions by file name: `slowloris` gives Slowloris,
  `http_flood` or `http-flood` gives HTTP-Flood, `benign` gives BENIGN, and any other
  name stays UNLABELED.

## Run

| Target | What it does | Writes |
|---|---|---|
| `help` | Lists the targets; works without `.env` | |
| `run` | A random forest per feature set (300 trees, 70/30 split, threshold 0.5), Slowloris against every other session | `results/klage_comparison.json` |

## Outputs

| File | Producer | In the paper |
|---|---|---|
| `results/klage_comparison.json` | `make run` | App. C |

Its keys name the configurations. `a_ml_sem_ontologia` is (a), the three `FLOW`
features. `a_ml_forte` is (a′), the nine `STRONG_FLOW` features. `d_completo` is
(d), `FLOW` plus `share_ja4`, `share_net` and `cluster_size` (feature sets in the
[sprint-3 README](../sprint-3/README.md#inputs)). `collateral_fpr_benign` is the
share of benign test sessions flagged.

## Results

| Method | F₁ | Precision | Recall | ROC AUC | Benign flagged |
|---|---|---|---|---|---|
| KLAGE, published, on network nodes | 0.841 | | | | not reported |
| (a) three flow features | 0.179 | 0.691 | 0.103 | 0.551 | 1.06% |
| (a′) nine flow features | 0.900 | 0.901 | 0.899 | 0.987 | 2.88% |
| (d) three flow features + cross-session | 0.911 | 0.908 | 0.915 | 0.982 | 2.73% |

With nine features the per-session model does not collapse, and (d) leads it by
0.011 in F₁. The lean (a) flags the fewest benign sessions because it catches only
10% of the attack. Real Slowloris in this capture leaves a per-session flow
signature (Appendix C).

## Caveats

- The comparison is uncontrolled. Granularity (sessions versus network nodes),
  protocol (one attack against the rest versus KLAGE's multiclass setup) and
  coverage differ.
- Our own nine-feature per-session model also exceeds 0.841, so the margin over
  KLAGE cannot be credited to cross-session evidence.
- KLAGE's released code starts from a graph whose construction is unpublished and
  ships no weights, so a controlled rerun is not possible (Appendix C).
- The negative class holds the HTTP Flood sessions as well as the benign ones. The
  benign-flagged rate counts only the benign test sessions.
- RT-IoT2022, listed in the earlier plan, was not run, and the paper does not use it.
