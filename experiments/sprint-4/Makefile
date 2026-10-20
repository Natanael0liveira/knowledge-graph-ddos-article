# Sprint 4: full statistical run and weight calibration

SHELL := /bin/bash
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
DIST_DIR  := $(DATA_ROOT)/synth/distributions
# Scenario cache of this stage's numbers: the same-service run, with a near-uniform
# benign pool and a monolithic botnet (the paper's canonical scenarios are sprint 6's).
# NOT synth/sprint4 (predates the flow features; run_sprint4 fails there with a
# KeyError on fwd_bytes_sum) and NOT synth/sprint4_strong_work (still carries the
# target-port artifact: config (b) reaches 0.888 instead of collapsing to chance).
WORK      := $(DATA_ROOT)/synth/sprint4_realistic_work
RESULTS   := $(DATA_ROOT)/results
VENV      := ../.venv
PYTHON    := $(VENV)/bin/python
SEEDS     ?= 30
K         ?= 50 1000

.DEFAULT_GOAL := help
.PHONY: help run weights weights-cluster figures all clean

help:  ## List the targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run:  ## Statistical run: $(SEEDS) seeds × K, ablation, baselines and tests
	@[ -f $(DIST_DIR)/session_requests.json ] || { echo "❌ Calibrate Sprint 2 first."; exit 1; }
	$(PYTHON) scripts/run_sprint4.py --seeds $(SEEDS) --K $(K) --strong \
	  --dist-dir $(DIST_DIR) --work $(WORK) --out-dir $(RESULTS)

weights:  ## Per-session calibration of the weights w_i (the paper's Appendix B)
	$(PYTHON) scripts/weight_calibration_session.py --scenarios $(WORK) --max-files 60 \
	  --out $(RESULTS)/weights_session_realistic.json

weights-cluster:  ## Earlier grid search with a per-cluster objective (saturated; see the README)
	$(PYTHON) scripts/weight_search.py --scenarios $(WORK) --max-files 20 \
	  --out $(RESULTS)/sprint4_weights.json

figures:  ## AUC vs K figure with 95% CIs per config
	$(PYTHON) scripts/make_figures.py --runs $(RESULTS)/sprint4_runs.csv \
	  --out $(RESULTS)/figures

all: run weights figures  ## Full Sprint 4 pipeline

clean:  ## Remove the Sprint 4 scenarios and results
	rm -rf $(WORK) $(RESULTS)/sprint4_*.json $(RESULTS)/sprint4_runs.csv
