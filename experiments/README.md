# Experiments

Code and configuration for every experimental stage of the paper. **Data**
(PCAPs, processed datasets, KG output) lives outside the repository on an
external drive pointed at by an environment variable; only code, configs and
light logs are versioned.

For why each stage exists and what it can establish, see
[`../docs/evaluation.md`](../docs/evaluation.md). For the decisions behind each
one, see [`METHODOLOGY.md`](METHODOLOGY.md). For results on real captures, see
[`FINDINGS.md`](FINDINGS.md).

## Setup

### Prerequisites

| Tool | Minimum | Install (macOS) |
|---|---|---|
| Python | 3.11 | `brew install python@3.11` |
| Docker Desktop | 4.x | https://www.docker.com/products/docker-desktop |
| tshark | 4.0+ (has JA4) | `brew install wireshark` |
| GNU Make | any | ships with macOS |
| Java | 17+ (for CICFlowMeter) | `brew install openjdk@17` |

```bash
python3 --version && docker --version && tshark --version && make --version && java --version
```

### External drive

```bash
df -h | grep -i volumes                          # find the mount point
export DATA_ROOT=/Volumes/YourDrive/kg-ddos-data
mkdir -p "$DATA_ROOT"
./scripts/setup-data-storage.sh "$DATA_ROOT"     # creates the tree and experiments/.env
```

Confirm that `experiments/.env` holds `DATA_ROOT=...` and that `experiments/data`
is a symlink exposing `raw/`, `processed/`, `synth/`, `kg/` and `results/`.

## Stages

```
experiments/
├── sprint-1/                     extraction pipeline: PCAP -> JA4 + flows -> sessions -> graph
├── sprint-2/                     calibrated synthetic generator
├── sprint-3/                     baselines and ablation (a/b/c/d)
├── sprint-4/                     statistical run, n = 30
├── sprint-5/                     comparison against KLAGE on CIC-IoT2023
├── sprint-6-noms/                realistic scenario, cost model, corrections for submission
├── pillar2-symbolic-reasoning/   SWRL + SPARQL, verdict as derivation
├── pillar4-evidence-mitigation/  JSON-LD / STIX chain and scoped mitigation
├── requirements.txt
├── METHODOLOGY.md                why each decision was made, per stage
└── FINDINGS.md                   results on real captures
```

Each stage is driven by a Makefile with named targets and fixed seeds. Start with
`make help` inside any of them.

## Status

All stages are coded and executed. Headline results, matching the paper:

| Stage | Data | Result |
|---|---|---|
| 1 — pipeline and KG | CICIDS2017 + CIC-IoT2023 | Both loaded; gates G1–G4 pass in `validate.ipynb` |
| 2 — synthetic generator | calibrated from stage 1 | KS pass (D = 0.003 duration, 0.002 request count); reproducible; stealth mode |
| 3 — baselines and ablation | stealthy synthetic, same service on :443 | (d) 0.927 at K = 50 and 0.982 at K = 1000, against 0.498–0.503 for (a), (b) and the three academic baselines |
| 4 — statistical run | synthetic, n = 30 | (d)−(a) Cohen's *d* = 22.4 and (d)−(c) *d* = 13.5, both p_bonf = 7.5 × 10⁻⁹; rank-biserial +1.00 |
| 5 — comparison with KLAGE | CIC-IoT2023 (real) | (d) F₁ = 0.911 and a strong per-session baseline at 0.900, both above KLAGE's published 0.841; the cross-session margin is marginal on this conventional dataset |
| 6 — NOMS additions | synthetic + real | Cost model, window sweep, profile drift |
| Pillar 2 | synthetic | Rule as detector: 90.3% recall at zero false positives where the learned model reaches 36.4% |
| Pillar 4 | synthetic + real | Frequency scoping fails (0% attack, 39% legitimate hit); enrichment blocks 85–90% with no collateral observed |

**What this supports.** The cross-session advantage is real and statistically
strong in the **stealthy distributed** regime. On conventional real datasets a
strong per-session classifier already suffices, and the paper says so explicitly;
what remains unconditional there is the framework: the session as an ontological
entity, the symbolic verdict, the evidence chain and the derived mitigation
scope.

**Open.** RT-IoT2022 (manual download from IEEE DataPort) and calibration of the
*absolute* w values against production traffic with partial and conflicting
signals. In the realistic same-service scenario the calibration corroborates the
TLS-dominant *ordering*, with the paper's weights reaching the optimal AUC 0.943.
