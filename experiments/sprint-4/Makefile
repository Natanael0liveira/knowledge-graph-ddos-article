# Sprint 4 — Execução completa + calibração de pesos

SHELL := /bin/bash
ENV_FILE := $(abspath ../.env)
ifneq ("$(wildcard $(ENV_FILE))","")
    include $(ENV_FILE)
    export
endif

DATA_ROOT ?= $(error DATA_ROOT não definido)
DIST_DIR  := $(DATA_ROOT)/synth/distributions
# Canonical scenario cache for the published numbers: the REALISTIC same-service
# run. NOT synth/sprint4 (predates the flow features; run_sprint4 fails there with
# KeyError on fwd_bytes_sum) and NOT synth/sprint4_strong_work (still carries the
# target-port artefact: config (b) reaches 0.888 instead of collapsing to chance).
WORK      := $(DATA_ROOT)/synth/sprint4_realistic_work
RESULTS   := $(DATA_ROOT)/results
VENV      := ../.venv
PYTHON    := $(VENV)/bin/python
SEEDS     ?= 30
K         ?= 50 1000

.DEFAULT_GOAL := help
.PHONY: help run weights weights-cluster figures all clean

help:  ## Lista targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run:  ## Execução estatística: $(SEEDS) seeds × K, ablação + baselines + testes
	@[ -f $(DIST_DIR)/session_requests.json ] || { echo "❌ Calibre Sprint 2 antes."; exit 1; }
	$(PYTHON) scripts/run_sprint4.py --seeds $(SEEDS) --K $(K) --strong \
	  --dist-dir $(DIST_DIR) --work $(WORK) --out-dir $(RESULTS)

weights:  ## Calibração por sessão dos pesos w_i (a que o README reporta)
	$(PYTHON) scripts/weight_calibration_session.py --scenarios $(WORK) --max-files 20 \
	  --out $(RESULTS)/weights_session_realistic.json

weights-cluster:  ## Grid search antigo, objetivo por cluster (saturava; ver nota histórica)
	$(PYTHON) scripts/weight_search.py --scenarios $(WORK) --max-files 20 \
	  --out $(RESULTS)/sprint4_weights.json

figures:  ## Money figure (AUC vs K, IC95% por config)
	$(PYTHON) scripts/make_figures.py --runs $(RESULTS)/sprint4_runs.csv \
	  --out $(RESULTS)/figures

all: run weights figures  ## Pipeline completo do Sprint 4

clean:  ## Remove cenários e resultados do Sprint 4
	rm -rf $(WORK) $(RESULTS)/sprint4_*.json $(RESULTS)/sprint4_runs.csv
