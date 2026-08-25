# Sprint 5 — Comparison with KLAGE (CIC-IoT2023)

Run the framework on the dataset KLAGE uses (Belcastro et al., FGCS 2026) for a
direct comparison on DDoS Slowloris. KLAGE reports F₁ = 84.1%; we report ours
alongside, plus the collateral-damage metric KLAGE does not have.

**Status:** executed on CIC-IoT2023. RT-IoT2022 is still pending a manual
download from IEEE DataPort.

## Results — DDoS Slowloris, CIC-IoT2023

One-vs-rest detection, `make run`:

| Method | F₁ | Prec | Rec | AUC | Collateral (benign FPR) |
|---|---|---|---|---|---|
| **KLAGE** (node-level, Graph-BERT) | 0.841 | — | — | — | not reported |
| Ours **(a)** per-session ML, **lean** (3 feat.) | 0.179 | 0.691 | 0.103 | 0.551 | 1.06% |
| Ours **(a′)** per-session ML, **strong** (8 feat.) | 0.900 | — | — | 0.987 | — |
| Ours **(d)** full, cross-session | **0.911** | 0.908 | 0.915 | 0.982 | 2.73% |

**The "per-session collapse to F₁ = 0.18" was an artifact of the lean baseline.**
The original (a) used only three flow features; with eight, per-session detection
does not collapse: F₁ = 0.900, AUC = 0.987. Both (a′) and (d) beat KLAGE, and the
advantage of (d) over the strong per-session model is **marginal** (ΔF₁ = +0.011).
The lead over KLAGE is therefore **not attributable to cross-session reasoning**:
real Slowloris in CIC-IoT2023 is a conventional attack with a per-session flow
signature.

**How to read the KLAGE comparison, honestly.** F₁ = 0.911 is in the **same order
of magnitude** as the published 0.841. This is **not a controlled head-to-head**
and we do not claim to beat it. The experiments differ in granularity (session
versus network node), in protocol (our binary attack-vs-rest split versus their
multiclass) and in coverage (CIC-IoT2023 only versus RT-IoT2022 plus
CIC-IoT2023). The defensible reading: *our session-level method is competitive
with the node-level state of the art on DDoS Slowloris, and adds what KLAGE does
not have, an auditable symbolic verdict and a measurable collateral-damage
figure.* The cross-session advantage does not appear here; it lives in the
stealthy distributed regime of Sprints 3 and 4.

**Caveats.**

- **Granularity.** KLAGE classifies network nodes; we classify sessions. The F₁
  values are not directly commutable.
- KLAGE evaluates on RT-IoT2022 **and** CIC-IoT2023; only the latter is used here.
- (d) has higher collateral than the lean (a) (2.73% against 1.06%): it catches
  far more attack while flagging slightly more benign traffic. Still low.
- A controlled rerun of KLAGE is not currently possible. The released code starts
  from a pre-built graph whose construction from the raw dataset is unpublished,
  and ships no weights.

Artifact: [`results/klage_comparison.json`](results/klage_comparison.json).

## Acquiring CIC-IoT2023

Run this sprint **after** Sprint 1 is validated; it reuses that infrastructure,
swapping only the input PCAPs.

- **Option A, UNB** (same account as CICIDS2017):
  https://www.unb.ca/cic/datasets/iotdataset-2023.html — take the `PCAPs/`
  (~12 GB, 33 attacks over 105 IoT devices) and `CSVs/` (~3 GB). To align with
  KLAGE, prefer the **DDoS Slowloris** subset.
- **Option B, IEEE DataPort:** https://ieee-dataport.org/documents/ciciot2023-dataset
  (free account, mirror of the same data).

Save under `$DATA_ROOT/raw/cic-iot-2023/`, already created by
`setup-data-storage.sh`.

## Reusing the Sprint 1 pipeline

```bash
cd ../sprint-1
make DATASET=cic-iot-2023 extract-ja4
make DATASET=cic-iot-2023 extract-flows
make DATASET=cic-iot-2023 sessions
make DATASET=cic-iot-2023 clusters
make DATASET=cic-iot-2023 load-kg-bulk
```

`DATASET=cic-iot-2023` points the Makefile at the right paths on the drive. The
infrastructure is unchanged.

## Acceptance gates

- [x] Sprint 1 pipeline runs with `DATASET=cic-iot-2023` without code changes
- [x] F₁ on CIC-IoT2023 DDoS Slowloris reported
- [x] Collateral damage on legitimate traffic reported
- [x] Comparison table with KLAGE in the paper
- [ ] RT-IoT2022 acquired and run
