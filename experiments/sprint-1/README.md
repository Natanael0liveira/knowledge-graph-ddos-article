# Sprint 1: extraction pipeline (PCAP → sessions)

This stage turns laboratory captures into sessions that carry a JA4 fingerprint and
flow features. It reads the CICIDS2017 Wednesday capture (Slowloris, Slowhttptest,
HULK, GoldenEye) and CIC-IoT2023 (DDoS Slowloris, HTTP Flood). Sprints 2, 3 and 5
read its session files. It can also load the sessions into an Apache Jena Fuseki
graph and query a SPARQL gate there. That graph path is legacy: the paper's
evaluation runs no reasoner (Section III-E). No table or figure of the paper is
computed here. The benign session counts of Appendix B come from this stage's
output.

## In the paper

- **Appendix C, laboratory captures.** Both datasets "run through the same
  extraction pipeline (PCAP → JA4 + flows → sessions)". The paper's scores on them
  come from [sprint 5](../sprint-5/), and the per-attack runs of
  [sprint 3](../sprint-3/) back its conclusion.
- **Appendix B and Section IV-A.** The generator samples request counts from all
  322,658 benign CICIDS2017 sessions of this stage, and durations from the 40,351
  with two or more requests ([`../sprint-2/distributions/`](../sprint-2/distributions/)).
- **Not in the paper:** the Fuseki graph, the notebook's gates and the legacy query
  [`queries/coordinatedHTTPFlood.rq`](queries/coordinatedHTTPFlood.rq), which is
  not Listing 1.

## Inputs

- **`experiments/.env`** with `DATA_ROOT`, written by
  [`../scripts/setup-data-storage.sh`](../scripts/setup-data-storage.sh). Every
  target except `help` needs it. The script also creates `../data`, a symlink to
  `DATA_ROOT`, which the commands below use.
- **`FUSEKI_DB`** in the same file, for `fuseki-up`, `load-kg-bulk` and
  `coordination`. It holds the TDB2 store and must sit on an internal APFS disk.
  The setup script does not write it; copy the line from
  [`../.env.example`](../.env.example).
- **PCAPs** under `$DATA_ROOT/raw/<dataset>/`. `DATASET` is `cicids2017` by
  default; pass `DATASET=cic-iot-2023` for the other capture. `make download`
  prints how to get CICIDS2017, which needs a UNB registration. The CIC-IoT2023
  sources are in the [sprint-5 README](../sprint-5/README.md#inputs).
- **Labels.** `sessions` leaves the CICIDS2017 Wednesday sessions `UNLABELED`.
  [`scripts/label_cicids2017.py`](scripts/label_cicids2017.py) labels them by
  attacker-victim pair and time window (command below). CIC-IoT2023 labels come
  from the PCAP file names: `slowloris`, `http_flood` or `http-flood`, and
  `benign`.
- **Tools.** `python3`; `tshark` with the `tls.handshake.ja4` field (check with
  `tshark -G fields | grep tls.handshake.ja4`); Docker for Fuseki; a JDK 17 for
  `tdb2.tdbloader`. The Makefile looks for Homebrew's `openjdk@17` first.
  `make check` also accepts the macOS `java` stub, so run `java -version` before
  the Jena targets. The Python environment is `../.venv` (`make install-deps`);
  flow extraction also needs `make install-cicflowmeter`.

## Run

Paths are under `$DATA_ROOT`, and `<ds>` is the value of `DATASET`. "Drive" marks
the targets that read or write there.

| Target | What it does | Drive | Writes |
|---|---|---|---|
| `help` | Lists the targets and the typical sequence; works without `.env` | No | |
| `check` | Checks that `python3`, `tshark` and `java` are on `PATH` and that `.env` and `DATA_ROOT` exist; warns if Docker is down; checks no version | Yes | |
| `python-venv` | Creates the venv | No | `../.venv` |
| `install-deps` | Installs [`../requirements.txt`](../requirements.txt) into the venv | No | `../.venv` |
| `install-cicflowmeter` | Installs `cicflowmeter`, pins scapy 2.5.0 and patches the package ([`scripts/patch_cicflowmeter.py`](scripts/patch_cicflowmeter.py)) | No | `../.venv` |
| `fuseki-up`, `fuseki-down`, `fuseki-logs` | Starts, stops or follows Fuseki ([`docker-compose.yml`](docker-compose.yml), port 3030) | No | |
| `test` | JA4, flows and sessions of `../sample-data/slowloris-test.pcap` | Yes (logs) | `../sample-data/` |
| `download` | Prints how to download CICIDS2017 | No | |
| `extract-ja4` | JA4 of every PCAP under `raw/<ds>/`, with `tshark` | Yes | `processed/ja4/<ds>/` |
| `extract-flows` | Flows of every PCAP, with the Python `cicflowmeter` | Yes | `processed/flows/<ds>/` |
| `sessions` | Joins flows and JA4 by 5-tuple into sessions; more than 300 s of inactivity starts a new one | Yes | `processed/sessions/<ds>.parquet` |
| `clusters` | Ground-truth clusters by label, target and time, a review sample of ten, and a `cluster_id` column added to the sessions file | Yes | `processed/clusters/<ds>.csv`, `<ds>.sample.csv` |
| `load-kg` | Loads the sessions into Fuseki over HTTP; `REUSE_TTL=1` reuses the Turtle export, `CHUNK` sets the triples per POST | Yes | `kg/exports/<ds>.ttl` |
| `export-nt` | Streams the sessions to N-Triples in constant memory | Yes | `kg/exports/<ds>.nt` |
| `install-jena-tools` | Downloads Apache Jena 5.1.0, the version of the Fuseki image | No | `~/apache-jena-5.1.0` |
| `load-kg-bulk` | Stops Fuseki, rebuilds the dataset with `tdb2.tdbloader` (after `export-nt` if the `.nt` is missing) and restarts Fuseki | Yes | `$FUSEKI_DB/databases/<ds>` |
| `coordination` | Ω(S) per detection cluster and gates G3 and G4, then appends the clusters' triples to the store | Yes | `processed/coordination/<ds>.csv`, `kg/exports/<ds>-coordination.nt` |
| `validate` | Opens [`notebooks/validate.ipynb`](notebooks/validate.ipynb) in Jupyter | Yes | |
| `stats` | Prints label, duration and JA4 counts | Yes | |
| `clean` | Removes the JA4, flow, session and cluster files of `<ds>`, and `logs/`, which every stage shares | Yes | |
| `clean-all` | Removes `raw/<ds>/`, `processed/`, `kg/` and `logs/` once you type `yes delete` | Yes | |

The typical order for CICIDS2017:

```bash
make install-deps install-cicflowmeter
make check
make download                   # then save the PCAP under $DATA_ROOT/raw/cicids2017/
make extract-ja4 && make extract-flows
make sessions
../.venv/bin/python scripts/label_cicids2017.py \
  --sessions ../data/processed/sessions/cicids2017.parquet
make clusters
make install-jena-tools load-kg-bulk coordination   # optional: the graph and gates G3/G4
make validate
```

The labeling script has no target. It rewrites the sessions file in place unless
`--out` names another file. It must run before `clusters`, which groups sessions
by label.

## Outputs

No result of this stage is committed. Its files stay under `$DATA_ROOT` (table
above), with logs in `$DATA_ROOT/logs/`. Later stages read the session files:

| File | Read by |
|---|---|
| `processed/sessions/cicids2017.parquet` | sprint-2 `make calibrate`, `make validate` and `calibrate_flow.py`; sprint-3 `make multiattack`; pillar-4 `qualitative_evidence.py` |
| `processed/sessions/cic-iot-2023.parquet` | sprint-3 `make multiattack`; sprint-5 `make run`; pillar-4 `qualitative_evidence.py` |

## Results

The labeled CICIDS2017 capture gives 368,777 sessions: 322,658 benign, 30,391
HULK, 7,472 GoldenEye, 4,217 Slowhttptest, 4,035 Slowloris, and 4 DoS-Other
sessions that the attacker sent outside the four attack windows
([`../sprint-2/distributions/_metadata.json`](../sprint-2/distributions/_metadata.json)).
CIC-IoT2023 gives 289,170 benign, 380,004 HTTP Flood and 118,063 Slowloris
sessions ([`../sprint-3/results/real_multiattack.csv`](../sprint-3/results/real_multiattack.csv)).

`make validate` checks seven gates. The notebook stores no output, so no
committed file records whether they pass.

- At least 1,000 sessions.
- G1: at least five distinct JA4.
- JA4 on at least 50% of the TLS sessions (port 443, or with SNI or JA3).
- At least ten derived clusters.
- The review sample exists.
- G3: ROC AUC of at least 0.85 for the better of a logistic regression and a
  random forest on behavioral and coordination features. The notebook itself
  calls this the trivial part, since these captures are separable by flow.
- G4: the `coordinatedHTTPFlood` rule returns at least one cluster with Ω ≥ τ,
  |S| ≥ 5 and at least one request per second on an HTTP port. τ is the 99th
  percentile of Ω over benign-dominated clusters.

## Caveats

- `make test` needs `../sample-data/slowloris-test.pcap`, which the repository
  does not ship and no public link provides. Without it the target stops with a
  note. Its outputs go to `experiments/sample-data/`, which git does not ignore.
- Without the labeling step the CICIDS2017 sessions stay `UNLABELED`. `clusters`
  then groups them under one label, the sprint-2 calibration finds no benign
  session, and gates G3 and G4 have no labels to score against.
- `load-kg` posts chunks over HTTP and can hang on large datasets on Apple
  Silicon, where the `stain/jena-fuseki` image runs under amd64 emulation.
  `load-kg-bulk` loads natively with `tdb2.tdbloader`. TDB2 needs the memory
  mapping that exFAT lacks, hence `FUSEKI_DB` on an internal disk. Building the
  whole rdflib graph in memory exhausts swap on large datasets, hence the streamed
  `export-nt`.
- The legacy query hard-codes the CIC-IoT2023 thresholds. It reads
  `kg:DetectionCluster` triples that `coordination` writes and that the ontology
  does not declare.
- [`docker-compose.yml`](docker-compose.yml) commits the Fuseki admin password and
  publishes port 3030 on every interface, and the `curl` example in the query file
  repeats the password. Run Fuseki on a trusted machine, or bind the port to
  `127.0.0.1` and set your own password first.
