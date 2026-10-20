# Experiments

Code, configurations and committed results for every experimental stage of the paper
([`papers/http-session-noms/article.tex`](../papers/http-session-noms/article.tex)). The
repository versions code, configurations, result files and anonymized production summaries
(E1–E4, counts and rates). Logs, captures, scenario caches and the operator's exports stay on an
external data drive.

Where to go next:
- [`FINDINGS.md`](FINDINGS.md): the results in prose, negative ones included, each with its paper
  pointer and result file.
- [`METHODOLOGY.md`](METHODOLOGY.md): how the evaluation was built and corrected, and which
  scenario cache each generated result comes from.
- [`../docs/evaluation.md`](../docs/evaluation.md) for the experimental design,
  [`../docs/concepts.md`](../docs/concepts.md) for the method and
  [`../docs/metrics.md`](../docs/metrics.md) for the metrics.
- The root README's section [Figures, tables and listings](../README.md#figures-tables-and-listings):
  which result file backs each table and figure of the paper.

## Prerequisites

| Tool | Needed for | Install (macOS) |
|---|---|---|
| Python 3.11 | every stage | `brew install python@3.11` |
| GNU Make | every stage | ships with macOS |
| tshark with JA4 support | Sprint 1, JA4 extraction | `brew install wireshark`; `tshark -G fields \| grep tls.handshake.ja4` must list the field |
| Docker Desktop | Sprint 1, the Fuseki store | [docker.com](https://www.docker.com/products/docker-desktop) |
| Java 17 | Sprint 1, Apache Jena's `tdb2.tdbloader` (`make load-kg-bulk`, `make coordination`) | `brew install openjdk@17` |

Flow features come from the Python `cicflowmeter` package, so flow extraction needs no Java.

## Python environment

Every Makefile runs `../.venv/bin/python`, which is `experiments/.venv`. Sprint 1's
`make install-deps` creates it but needs `DATA_ROOT`. These commands, run from the repository
root, need neither the data drive nor `experiments/.env`:

```bash
cd experiments
python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Sprint 1's flow extraction also needs `cicflowmeter` with `scapy` 2.5.0 and three bug fixes
(`sprint-1/scripts/patch_cicflowmeter.py`), which `requirements.txt` leaves out. Run
`make install-cicflowmeter` in `sprint-1/` once `.env` exists.

## The data drive and `.env`

```bash
export DATA_ROOT=/Volumes/YourDrive/kg-ddos-data
./scripts/setup-data-storage.sh "$DATA_ROOT"
```

- The script creates the data tree on the drive, writes `experiments/.env` with `DATA_ROOT`, and
  links `experiments/data` to the drive.
- Sprint 1's TDB2 store also needs `FUSEKI_DB` in `.env`, on an internal APFS disk, since exFAT
  breaks TDB2's memory mapping. The script does not write it; see [`.env.example`](.env.example).
- `make help` works in every stage without `.env`. In Sprints 1–5 every other target stops while
  `DATA_ROOT` is unset, since make reads it when it parses the Makefile.
- Sprint 6 and the two pillars need no `.env`. Sprint 6 reaches the drive through
  `experiments/data`.

## What runs without the drive

| Where | Command | What it does | Writes |
|---|---|---|---|
| `sprint-6-noms/` | `make audit` | recomputes about 250 printed numbers of the paper from `results/` | nothing |
| `sprint-6-noms/` | `make block-report-check` | runs the block report's code on the paper's own reduction | nothing |
| `sprint-6-noms/` | `make block-report` | the 14-day block's metrics 1–10, from its committed reduction | `results/block_report.json` |
| `sprint-6-noms/` | `make compile-check` | the count query compiled from the ontology, checked on generated sessions | `results/compile_check.json` |
| `sprint-6-noms/` | `make stix-check` | rewrites each committed evidence chain's STIX 2.1 bundle and runs the OASIS validator | the bundles, `results/stix_validation.json` |
| `sprint-6-noms/` | `make stix-ingest` | the same bundles through a TAXII 2.1 server it starts on localhost, and MISP's importer | `results/stix_ingest.json` |
| `sprint-6-noms/` | `make latency` | the cost model (App. D, Fig. 4); the full sweep takes long | `results/latency_*` |
| `pillar2-symbolic-reasoning/` | `make demo` | the SWRL rules and the SPARQL Ω aggregation on a toy graph | nothing |
| `pillar4-evidence-mitigation/` | `make demo` | an evidence chain and its STIX bundle on a toy cluster, with the modal scope | overwrites `results/evidence.jsonld`, `results/mitigation.stix.json` |
| repository root | `experiments/.venv/bin/python papers/http-session-noms/figures/make_figures_en.py` | Figs. 2–4, from `production_tables.json` and `latency_summary.json` | the figure files |

Every other target reads the captures, the scenario caches or the operator's exports on the
drive. In `sprint-6-noms/`, `make clean` deletes every committed `results/*.json` and `*.csv`,
the production reductions included, which only the drive can rebuild.

## Stages

Each stage has its own README and a Makefile with fixed seeds.

| Directory | What it holds | Paper | Needs the drive |
|---|---|---|---|
| [`sprint-1/`](sprint-1/) | Laboratory pipeline: PCAP → JA4 and flows → sessions, with a legacy Fuseki graph and SPARQL gate | App. B (the benign sessions the generator samples), App. C | yes |
| [`sprint-2/`](sprint-2/) | The traffic generator, and the CICIDS2017-derived distributions it samples, committed in `distributions/` | IV-A, App. B | for its targets; Sprint 6 reads `distributions/` from the repository |
| [`sprint-3/`](sprint-3/) | First (a)–(d) ablation (three flow features, one seed), the academic baselines' code, the multi-attack run on the captures | App. C, through code that Sprints 4–6 reuse | yes |
| [`sprint-4/`](sprint-4/) | Earlier 30-seed run and weight calibration on the sprint-4 cache, and the robustness sweep | App. B (weights) | yes |
| [`sprint-5/`](sprint-5/) | The uncontrolled comparison with KLAGE on CIC-IoT2023 Slowloris | App. C | yes |
| [`sprint-6-noms/`](sprint-6-noms/) | The paper's evaluation: the scope on generated traffic, the production evaluation with the held-out day and the 14-day block, the compiled query, the STIX export, the cost model and the audit | III-E, IV, V, VI; Tables II–VII; Figs. 2–4; Apps. B–F | for scenario-cache and production targets |
| [`pillar2-symbolic-reasoning/`](pillar2-symbolic-reasoning/) | Four sub-relations as SWRL rules and the SPARQL Ω aggregation, on a toy graph; the evaluation runs no reasoner | App. A | no |
| [`pillar4-evidence-mitigation/`](pillar4-evidence-mitigation/) | Both scope derivations (modal fingerprint and binomial test), level calibration, and the JSON-LD and STIX export; Sprint 6 imports it | III-C, III-E, App. D (Listing 1) | no |
| [`common/`](common/) | `kg_ontology.py`: the weights, class keys and count unit, read from the ontology | III-E | no |
| [`scripts/`](scripts/) | `setup-data-storage.sh`: the data tree, `.env` and the data symlink | | |

The [Sprint 6 README](sprint-6-noms/README.md) maps each paper element to its result files and
make target, and keeps a lab notebook of the experiments and review rounds.
