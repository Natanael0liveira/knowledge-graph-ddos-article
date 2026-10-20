# Sprint 3: baselines and ablation

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
SYNTH_DIR := $(DATA_ROOT)/synth/sprint3
LOG_DIR   := $(DATA_ROOT)/logs

VENV   := ../.venv
PYTHON := $(VENV)/bin/python
GEN    := ../sprint-2/scripts
SEED   ?= 7

.DEFAULT_GOAL := help
.PHONY: help scenarios ablation multiattack clean

help:  ## List the targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

scenarios:  ## Generate stealth scenarios K=1/50/1000 and convert them to sessions
	@[ -f $(DIST_DIR)/session_requests.json ] || { echo "❌ Calibrate Sprint 2 first: make -C ../sprint-2 calibrate"; exit 1; }
	@mkdir -p $(SYNTH_DIR) $(LOG_DIR)
	@for k in 1 50 1000; do \
	  echo "==> stealth K=$$k"; \
	  $(PYTHON) $(GEN)/generator.py --config ../sprint-2/configs/scenario_stealth.yaml \
	    --param K=$$k --seed $(SEED) --distributions $(DIST_DIR) \
	    --out $(SYNTH_DIR)/stealth_K$$k.jsonl 2>&1 | tail -1; \
	  $(PYTHON) $(GEN)/synth_to_sessions.py --jsonl $(SYNTH_DIR)/stealth_K$$k.jsonl \
	    --out $(SYNTH_DIR)/stealth_K$$k.parquet 2>&1 | grep sessions; \
	done
	@echo "✅ Scenarios in $(SYNTH_DIR)/"

ablation:  ## Run the baselines and the a/b/c/d ablation, and print the table
	$(PYTHON) scripts/run_ablation.py \
	  --scenario K1=$(SYNTH_DIR)/stealth_K1.parquet \
	             K50=$(SYNTH_DIR)/stealth_K50.parquet \
	             K1000=$(SYNTH_DIR)/stealth_K1000.parquet \
	  2>&1 | tee $(LOG_DIR)/sprint3_ablation.log

REAL_S1 := $(DATA_ROOT)/processed/sessions/cicids2017.parquet
REAL_S2 := $(DATA_ROOT)/processed/sessions/cic-iot-2023.parquet

multiattack:  ## Multi-attack run on real captures (a vs d)
	@[ -f $(REAL_S1) ] || { echo "❌ $(REAL_S1) does not exist (is the external drive mounted?)"; exit 1; }
	@mkdir -p results
	$(PYTHON) scripts/run_real_multiattack.py \
	  --dataset cicids2017=$(REAL_S1) cic-iot-2023=$(REAL_S2) \
	  --out results/real_multiattack.csv \
	  2>&1 | tee $(LOG_DIR)/sprint3_multiattack.log

clean:  ## Remove the Sprint 3 scenarios
	rm -rf $(SYNTH_DIR)
	@echo "✅ removed $(SYNTH_DIR)"
