# Sprint 1 — Extraction pipeline (PCAP → KG)

Turn CICIDS2017 PCAPs (Slowloris and the Slow HTTP variants) into a knowledge
graph queryable over SPARQL, with sessions reconstructed, JA4 extracted and
cluster ground truth derived.

CICIDS2017 rather than CIC-DDoS2019: its PCAPs are named per attack, Slowloris
included, which matches the paper's focus on the Slow HTTP DoS family.

Most of the wall clock is downloads and heavy extraction running in the
background; active involvement is roughly six hours spread over two weeks.

## Flow

```
[CICIDS2017 PCAPs] ────┐
                       ├──► extract_ja4.py   ──► ja4.csv
                       └──► extract_flows.py ──► flows.csv
                                                       │
                                            build_sessions.py ──► sessions.parquet
                                                       │
                                            derive_clusters.py ──► clusters.csv
                                                       │
                                            load_to_fuseki.py ──► KG in TDB2
                                                       │
                                                 validate.ipynb
```

## Prerequisites

Checked by `make check`: Python 3.11+ with a venv, Docker running (for Fuseki),
tshark 4.0+ (with JA4), Java 17+ (for CICFlowMeter), and `experiments/.env`
written by `setup-data-storage.sh`.

## Steps

| Step | Command | Your time | Wall clock |
|---|---|---|---|
| 1. Validate setup | `make check` | 5 min | immediate |
| 2. Start Fuseki | `make fuseki-up` | 2 min | 1 min |
| 3. Small-PCAP test | `make test` | 30 min | 5 min |
| 4. Acquire CICIDS2017 | `make download` | 10 min | 6–12 h |
| 5. JA4 extraction | `make extract-ja4` | 5 min | 2–6 h |
| 6. Flow extraction | `make extract-flows` | 5 min | 2–4 h |
| 7. Session reconstruction | `make sessions` | 10 min | 30 min |
| 8. Cluster ground truth | `make clusters` | 30 min | 10 min + review |
| 9. Load into Fuseki | `make install-jena-tools && make DATASET=<ds> load-kg-bulk` | 5 min | ~2 min |
| 10. Coordination, gates G3/G4 | `make DATASET=<ds> coordination` | 5 min | ~2 min |
| 11. Final validation | `make validate` | 2 h | 1 h |

Step 8 asks you to review a sample of ten clusters by hand. Step 10 computes
Ω(S), the ROC AUC gate (G3) and materializes `coordinatedHTTPFlood` (G4).

Run `make help` for the full target list.

## Loading the KG: use `load-kg-bulk`, not `load-kg`

`make load-kg` loads over chunked HTTP POST. On datasets beyond roughly 1.2M
triples it **hangs** on Apple Silicon: the `stain/jena-fuseki` image runs under
amd64 emulation and the per-chunk commit thrashes the index. The TDB2 store also
cannot live on exFAT, which lacks POSIX memory-map semantics.

The working path:

1. Point `FUSEKI_DB` in `.env` at the **internal SSD** (see `.env.example`). Only
   the store is local; data and exports stay under `DATA_ROOT`, external drive
   included.
2. `make install-jena-tools` fetches Apache Jena at **the same version as the
   Fuseki image**, so the TDB2 format matches.
3. `make DATASET=<ds> load-kg-bulk` serializes sessions to N-Triples in
   **constant memory** (building the whole rdflib graph blows out swap past ~400k
   sessions), stops Fuseki, runs the native `tdb2.tdbloader` on the host JVM, and
   restarts. Roughly 10M triples in 2 minutes, against hours or a hang over HTTP.

The G4 gate query is in
[`queries/coordinatedHTTPFlood.rq`](queries/coordinatedHTTPFlood.rq).

## Outputs

Under `$DATA_ROOT`:

- `processed/ja4/cicids2017/*.csv` — JA4 per flow
- `processed/flows/cicids2017/*.csv` — CICFlowMeter flows
- `processed/sessions/cicids2017.parquet` — reconstructed sessions
- `processed/clusters/cicids2017.csv` — derived clusters
- `kg/fuseki-tdb2/` — Fuseki RDF store
- `kg/exports/cicids2017.ttl` — exportable Turtle snapshot

## Acceptance gates

- [ ] `make test` yields non-empty JA4 for at least one observed TLS handshake
- [ ] `sessions.parquet` covers ≥ 80% of the original flows
- [ ] At least ten clusters manually validated in `clusters.csv`
- [ ] Fuseki answers `SELECT (COUNT(*) AS ?n) WHERE { ?s a kg:ApplicationSession }` with n ≥ 1000
- [ ] `validate.ipynb` reports JA4 and session-duration distributions

## Troubleshooting

Logs are in `$DATA_ROOT/logs/`.

| Symptom | Likely cause | Fix |
|---|---|---|
| `tshark: command not found` | Wireshark missing | `brew install wireshark` |
| JA4 column empty | tshark < 4.0, no JA4 plugin | Update Wireshark |
| `Docker daemon not running` | Docker Desktop closed | Open Docker Desktop |
| `cicids2017/` empty | UNB registration pending | https://www.unb.ca/cic/datasets/ids-2017.html |
| `CICFlowMeter not found` | JAR not downloaded | `make install-cicflowmeter` |

## Where it lands in the paper

Real-capture dataset for the comparison against the literature, the Scenario A
baseline on real data, and the observed JA4 and temporal distributions used to
calibrate the sub-relation thresholds.
