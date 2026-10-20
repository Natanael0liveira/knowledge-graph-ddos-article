# Sprint 1: extraction pipeline (PCAP → JA4 + flows → sessions → KG)
#
# Usage, from this directory (experiments/sprint-1/):
#   make help

# ----- Configuration -----
SHELL := /bin/bash

# Load DATA_ROOT (and FUSEKI_DB) from experiments/.env
ENV_FILE := $(abspath ../.env)
ifneq ("$(wildcard $(ENV_FILE))","")
    include $(ENV_FILE)
    export
endif

# `make help` works without .env, showing a placeholder for DATA_ROOT.
# Every other target stops here while DATA_ROOT is not set.
ifeq ($(filter-out help,$(MAKECMDGOALS)),)
DATA_ROOT ?= <DATA_ROOT>
endif
DATA_ROOT ?= $(error DATA_ROOT is not set. Run first: ../scripts/setup-data-storage.sh /Volumes/YourDrive/kg-ddos-data)

# Target dataset (default: CICIDS2017 for Sprint 1)
DATASET ?= cicids2017

# Derived paths
RAW_DIR        := $(DATA_ROOT)/raw/$(DATASET)
PROCESSED_DIR  := $(DATA_ROOT)/processed
JA4_DIR        := $(PROCESSED_DIR)/ja4/$(DATASET)
FLOWS_DIR      := $(PROCESSED_DIR)/flows/$(DATASET)
SESSIONS_FILE  := $(PROCESSED_DIR)/sessions/$(DATASET).parquet
CLUSTERS_FILE  := $(PROCESSED_DIR)/clusters/$(DATASET).csv
KG_DIR         := $(DATA_ROOT)/kg
LOG_DIR        := $(DATA_ROOT)/logs

# Venv
VENV := ../.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Java: prefer Homebrew's openjdk@17 over the macOS stub in /usr/bin/java
JAVA_BREW := $(shell brew --prefix openjdk@17 2>/dev/null)/bin/java
JAVA := $(shell [ -x "$(JAVA_BREW)" ] && echo "$(JAVA_BREW)" || command -v java 2>/dev/null)

# Fuseki
FUSEKI_URL := http://localhost:3030

# Native (ARM) bulk load with the Apache Jena tools. It avoids the transactional
# POST per chunk into an emulated amd64 JVM, which could hang for hours.
# The version MUST match the Fuseki image (docker-compose.yml), so that the TDB2
# format is identical.
JENA_VERSION ?= 5.1.0
JENA_HOME    ?= $(HOME)/apache-jena-$(JENA_VERSION)
JENA_JAVA_HOME := $(shell brew --prefix openjdk@17 2>/dev/null)
# N-Triples export (streaming, constant memory). Building the whole rdflib graph
# in RAM exhausts swap on large datasets.
NT_FILE      := $(KG_DIR)/exports/$(DATASET).nt
# The TDB2 store lives on the internal SSD (FUSEKI_DB in .env); exFAT breaks the
# memory mapping TDB2 relies on.
FUSEKI_DB    ?= $(error FUSEKI_DB is not set in .env: point it to a path on the internal SSD (see ../.env.example))

# ----- Default -----
.DEFAULT_GOAL := help

.PHONY: help check python-venv install-deps install-cicflowmeter \
        fuseki-up fuseki-down fuseki-logs \
        test download extract-ja4 extract-flows sessions clusters load-kg \
        install-jena-tools export-nt load-kg-bulk coordination \
        validate stats clean clean-all

# ----- Help -----
help:  ## Show this help
	@echo "Sprint 1: extraction pipeline (PCAP → JA4 + flows → sessions → KG)"
	@echo ""
	@echo "Configuration:"
	@echo "  DATA_ROOT = $(DATA_ROOT)"
	@echo "  DATASET   = $(DATASET)"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Typical sequence (CICIDS2017; README.md has the details):"
	@echo "  make install-deps install-cicflowmeter   # Python environment in ../.venv"
	@echo "  make check                               # tools on PATH, .env and DATA_ROOT"
	@echo "  make download                            # how to get the CICIDS2017 capture"
	@echo "  make extract-ja4 && make extract-flows   # run in the background"
	@echo "  make sessions"
	@echo "  $(PYTHON) scripts/label_cicids2017.py --sessions $(SESSIONS_FILE)"
	@echo "  make clusters"
	@echo "  make install-jena-tools load-kg-bulk coordination   # optional: Fuseki graph, gates G3/G4"
	@echo "  make validate                            # validation notebook"

# ----- Dependency check -----
check:  ## Check dependencies (Python, Docker, tshark, Java)
	@echo "==> Checking dependencies..."
	@command -v python3 >/dev/null || { echo "❌ python3 not found"; exit 1; }
	@command -v tshark  >/dev/null || { echo "❌ tshark not found (brew install wireshark)"; exit 1; }
	@[ -x "$(JAVA)" ] || command -v java >/dev/null || { echo "❌ java not found (brew install openjdk@17)"; exit 1; }
	@command -v docker  >/dev/null && docker info >/dev/null 2>&1 || { echo "⚠️  docker not found or its daemon is stopped. Apache Jena Fuseki will not run. Install Docker Desktop for the Fuseki targets (fuseki-up, load-kg, load-kg-bulk, coordination)."; }
	@[ -f $(ENV_FILE) ] || { echo "❌ $(ENV_FILE) not found (run ../scripts/setup-data-storage.sh)"; exit 1; }
	@[ -d $(DATA_ROOT) ] || { echo "❌ DATA_ROOT $(DATA_ROOT) is not accessible"; exit 1; }
	@echo "✅ Required dependencies OK"
	@echo "    DATA_ROOT=$(DATA_ROOT)"
	@echo "    tshark version: $$(tshark --version | head -1)"
	@echo "    java path: $(JAVA)"
	@echo "    Free space: $$(df -g $(DATA_ROOT) | awk 'NR==2 {print $$4}') GB"

# ----- Python environment -----
python-venv:  ## Create the Python virtualenv in ../.venv
	@[ -d $(VENV) ] || python3 -m venv $(VENV)
	@echo "✅ venv in $(VENV)"

install-deps: python-venv  ## Install the Python dependencies (after creating the venv)
	$(PIP) install --upgrade pip
	$(PIP) install -r ../requirements.txt
	@echo "✅ Dependencies installed. Activate with: source $(VENV)/bin/activate"

install-cicflowmeter:  ## Install cicflowmeter with pip and patch it (scapy 2.5 and bug fixes)
	@if ! $(PYTHON) -c "import cicflowmeter" 2>/dev/null; then \
	  echo "==> Installing cicflowmeter with pip..."; \
	  $(PIP) install cicflowmeter; \
	fi
	@# cicflowmeter 0.2.0 uses scapy's old sessions API (toPacketList).
	@# scapy >= 2.6 changed that API, and cicflowmeter then stops working (empty CSV).
	@if ! $(PYTHON) -c "import scapy; v=tuple(int(x) for x in scapy.VERSION.split('.')[:2]); exit(0 if v <= (2,5) else 1)" 2>/dev/null; then \
	  echo "==> Downgrading scapy to 2.5.0 (for cicflowmeter)..."; \
	  $(PIP) install "scapy==2.5.0"; \
	fi
	@# Patch the venv's copy in place (min() on an empty sequence)
	@$(PYTHON) scripts/patch_cicflowmeter.py
	@echo "✅ cicflowmeter ready"

# ----- Fuseki (Apache Jena triple store) -----
fuseki-up:  ## Start Apache Jena Fuseki with Docker
	docker compose up -d
	@echo "✅ Fuseki running at $(FUSEKI_URL)"
	@echo "    Admin: $(FUSEKI_URL)/dataset.html"

fuseki-down:  ## Stop Fuseki
	docker compose down
	@echo "✅ Fuseki stopped"

fuseki-logs:  ## Follow Fuseki's logs
	docker compose logs -f fuseki

# ----- Test with a small PCAP -----
test:  ## Run the pipeline on a small test PCAP (needs ../sample-data/slowloris-test.pcap, which is not shipped)
	@mkdir -p $(LOG_DIR) ../sample-data
	@if [ ! -f ../sample-data/slowloris-test.pcap ]; then \
	  echo "==> Test PCAP not found: ../sample-data/slowloris-test.pcap"; \
	  echo "    (TODO: no public link defined yet; a Wireshark sample capture would serve)"; \
	  exit 1; \
	fi
	$(PYTHON) scripts/extract_ja4.py --pcap ../sample-data/slowloris-test.pcap --out ../sample-data/ja4/slowloris-test.csv
	$(PYTHON) scripts/extract_flows.py --pcap ../sample-data/slowloris-test.pcap --out ../sample-data/flows/slowloris-test.csv
	$(PYTHON) scripts/build_sessions.py --ja4-dir ../sample-data/ja4 --flows-dir ../sample-data/flows --out ../sample-data/sessions.parquet
	@echo "✅ Test pipeline OK. See ../sample-data/"

# ----- Main pipeline: CICIDS2017 (or DATASET=cic-iot-2023) -----
download:  ## How to download CICIDS2017 (needs a UNB registration)
	@echo "==> CICIDS2017 needs a manual registration at UNB:"
	@echo "    https://www.unb.ca/cic/datasets/ids-2017.html"
	@echo ""
	@echo "    After registering and logging in, download ONLY:"
	@echo "      📄 Wednesday-WorkingHours.pcap"
	@echo "        → holds DoS slowloris, DoS Slowhttptest, DoS Hulk, DoS GoldenEye"
	@echo "      📄 Wednesday-WorkingHours.pcap_ISCX.csv (optional)"
	@echo "        → per-flow labels; the pipeline does not read it and labels sessions"
	@echo "          with scripts/label_cicids2017.py instead"
	@echo ""
	@echo "    Save them in:"
	@echo "    $(RAW_DIR)/"
	@echo ""
	@echo "    When done:"
	@echo "      make extract-ja4 && make extract-flows"

extract-ja4: check  ## Extract JA4 from every PCAP under raw/ (recursive) with tshark
	@mkdir -p $(JA4_DIR) $(LOG_DIR)
	@pcaps=$$(find $(RAW_DIR) -type f -name "*.pcap" -not -name "._*"); \
	[ -n "$$pcaps" ] || { echo "❌ No PCAP in $(RAW_DIR). Run 'make download' first."; exit 1; }; \
	for pcap in $$pcaps; do \
	  relpath=$$(echo "$$pcap" | sed "s|$(RAW_DIR)/||"); \
	  name=$$(echo "$$relpath" | sed "s|/|_|g" | sed "s|.pcap$$||"); \
	  echo "==> Extracting JA4 from $$relpath..."; \
	  $(PYTHON) scripts/extract_ja4.py \
	    --pcap "$$pcap" \
	    --out "$(JA4_DIR)/$$name.csv" \
	    2>&1 | tee "$(LOG_DIR)/extract_ja4_$$name.log"; \
	done
	@echo "✅ JA4 written to $(JA4_DIR)/"

extract-flows: check install-cicflowmeter  ## Extract flows (recursive) with the Python cicflowmeter
	@mkdir -p $(FLOWS_DIR) $(LOG_DIR)
	@pcaps=$$(find $(RAW_DIR) -type f -name "*.pcap" -not -name "._*"); \
	[ -n "$$pcaps" ] || { echo "❌ No PCAP in $(RAW_DIR)"; exit 1; }; \
	for pcap in $$pcaps; do \
	  relpath=$$(echo "$$pcap" | sed "s|$(RAW_DIR)/||"); \
	  name=$$(echo "$$relpath" | sed "s|/|_|g" | sed "s|.pcap$$||"); \
	  echo "==> Extracting flows from $$relpath..."; \
	  $(PYTHON) scripts/extract_flows.py \
	    --pcap "$$pcap" \
	    --out "$(FLOWS_DIR)/$$name.csv" \
	    2>&1 | tee "$(LOG_DIR)/extract_flows_$$name.log"; \
	done
	@echo "✅ Flows written to $(FLOWS_DIR)/"

sessions:  ## Rebuild sessions from flows and JA4
	@mkdir -p $(dir $(SESSIONS_FILE)) $(LOG_DIR)
	$(PYTHON) scripts/build_sessions.py \
	  --ja4-dir $(JA4_DIR) \
	  --flows-dir $(FLOWS_DIR) \
	  --out $(SESSIONS_FILE) \
	  --window 300 \
	  2>&1 | tee $(LOG_DIR)/build_sessions.log
	@echo "✅ Sessions in $(SESSIONS_FILE)"

clusters:  ## Derive the cluster ground truth
	@mkdir -p $(dir $(CLUSTERS_FILE)) $(LOG_DIR)
	$(PYTHON) scripts/derive_clusters.py \
	  --sessions $(SESSIONS_FILE) \
	  --out $(CLUSTERS_FILE) \
	  --sample 10 \
	  2>&1 | tee $(LOG_DIR)/derive_clusters.log
	@echo "✅ Clusters in $(CLUSTERS_FILE) (sample for manual review: $(basename $(CLUSTERS_FILE)).sample.csv)"

load-kg:  ## Load sessions and clusters into Fuseki over HTTP. REUSE_TTL=1 reuses an exported TTL.
	@mkdir -p $(KG_DIR)/exports $(LOG_DIR)
	$(PYTHON) scripts/load_to_fuseki.py \
	  --sessions $(SESSIONS_FILE) \
	  --clusters $(CLUSTERS_FILE) \
	  --ontology ../../ontology/ddos_ontology.owl \
	  --fuseki-url $(FUSEKI_URL) \
	  --dataset $(DATASET) \
	  --export-ttl $(KG_DIR)/exports/$(DATASET).ttl \
	  --chunk $(or $(CHUNK),200000) \
	  $(if $(REUSE_TTL),--reuse-ttl,) \
	  2>&1 | tee $(LOG_DIR)/load_to_fuseki_$(DATASET).log
	@echo "✅ KG loaded at $(FUSEKI_URL)/$(DATASET)/sparql"

export-nt:  ## Write N-Triples (.nt) by streaming, in constant memory, with no HTTP upload
	@mkdir -p $(KG_DIR)/exports $(LOG_DIR)
	$(PYTHON) scripts/load_to_fuseki.py \
	  --sessions $(SESSIONS_FILE) \
	  --clusters $(CLUSTERS_FILE) \
	  --ontology ../../ontology/ddos_ontology.owl \
	  --fuseki-url $(FUSEKI_URL) \
	  --dataset $(DATASET) \
	  --export-ttl $(NT_FILE) \
	  --stream \
	  2>&1 | tee $(LOG_DIR)/export_nt_$(DATASET).log
	@echo "✅ N-Triples in $(NT_FILE)"

install-jena-tools:  ## Download Apache Jena ($(JENA_VERSION)) for the native bulk load (tdb2.tdbloader)
	@if [ -x "$(JENA_HOME)/bin/tdb2.tdbloader" ]; then \
	  echo "✅ Jena already in $(JENA_HOME)"; \
	else \
	  echo "▶ downloading apache-jena-$(JENA_VERSION) (the Fuseki image's version)..."; \
	  curl -fsSL -o /tmp/apache-jena-$(JENA_VERSION).tar.gz \
	    https://archive.apache.org/dist/jena/binaries/apache-jena-$(JENA_VERSION).tar.gz; \
	  tar xzf /tmp/apache-jena-$(JENA_VERSION).tar.gz -C $(HOME); \
	  echo "✅ Jena extracted to $(JENA_HOME)"; \
	fi

load-kg-bulk:  ## FAST native ARM load with tdb2.tdbloader. Writes the .nt if missing.
	@[ -x "$(JENA_HOME)/bin/tdb2.tdbloader" ] || { echo "❌ tdb2.tdbloader not found in $(JENA_HOME). Run: make install-jena-tools"; exit 1; }
	@[ -f "$(NT_FILE)" ] || $(MAKE) DATASET=$(DATASET) export-nt
	@echo "▶ stopping Fuseki (releases the TDB2 lock)..."
	-docker compose down
	@echo "▶ recreating the $(DATASET) store (clean load)..."
	rm -rf "$(FUSEKI_DB)/databases/$(DATASET)"
	@echo "▶ native bulk load (the host's ARM JVM)..."
	JAVA_HOME="$(JENA_JAVA_HOME)" JVM_ARGS="-Xmx6g" \
	  "$(JENA_HOME)/bin/tdb2.tdbloader" --loc "$(FUSEKI_DB)/databases/$(DATASET)" "$(NT_FILE)" \
	  2>&1 | tee $(LOG_DIR)/tdbloader_$(DATASET).log
	@echo "▶ starting Fuseki..."
	docker compose up -d
	@echo "✅ $(DATASET) loaded at $(FUSEKI_URL)/$(DATASET)/sparql (check the COUNT)"

COORD_FILE := $(PROCESSED_DIR)/coordination/$(DATASET).csv
COORD_NT   := $(KG_DIR)/exports/$(DATASET)-coordination.nt

coordination:  ## Compute Ω(S) and gates G3 (ROC AUC) and G4 (coordinatedHTTPFlood)
	@mkdir -p $(dir $(COORD_FILE)) $(LOG_DIR)
	$(PYTHON) scripts/compute_coordination.py \
	  --sessions $(SESSIONS_FILE) \
	  --out $(COORD_FILE) \
	  --emit-nt $(COORD_NT) \
	  2>&1 | tee $(LOG_DIR)/coordination_$(DATASET).log
	@echo "▶ loading Ω(S) into Fuseki (append) for the G4 SPARQL query..."
	-docker compose down
	JAVA_HOME="$(JENA_JAVA_HOME)" JVM_ARGS="-Xmx4g" \
	  "$(JENA_HOME)/bin/tdb2.tdbloader" --loc "$(FUSEKI_DB)/databases/$(DATASET)" "$(COORD_NT)"
	docker compose up -d
	@echo "✅ Coordination in $(COORD_FILE). G4 query: queries/coordinatedHTTPFlood.rq (kg:DetectionCluster / kg:coordinationScore)"

# ----- Validation -----
validate:  ## Open the validation notebook in Jupyter
	$(PYTHON) -m jupyter notebook notebooks/validate.ipynb

stats:  ## Print basic statistics
	$(PYTHON) scripts/stats.py --sessions $(SESSIONS_FILE) --clusters $(CLUSTERS_FILE)

# ----- Cleanup -----
clean:  ## Remove intermediate files (keeps raw/ and kg/)
	rm -rf $(JA4_DIR) $(FLOWS_DIR) $(SESSIONS_FILE) $(CLUSTERS_FILE) $(LOG_DIR)
	@echo "✅ Cleanup done (raw/ and kg/ kept)"

clean-all:  ## ⚠️  Remove the dataset's PCAPs, processed/, kg/ and logs/. Use with care.
	@echo "⚠️  This deletes $(RAW_DIR), $(PROCESSED_DIR), $(KG_DIR) and $(LOG_DIR)."
	@read -p "Are you sure? Type 'yes delete': " confirm; \
	if [ "$$confirm" = "yes delete" ]; then \
	  rm -rf $(RAW_DIR) $(PROCESSED_DIR) $(KG_DIR) $(LOG_DIR); \
	  echo "✅ All removed."; \
	else \
	  echo "Canceled."; \
	fi
