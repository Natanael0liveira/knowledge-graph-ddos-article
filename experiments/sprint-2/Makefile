# Sprint 2: calibrated synthetic generator

SHELL := /bin/bash

# Load DATA_ROOT from experiments/.env
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

# Paths
SPRINT1_SESSIONS  := $(DATA_ROOT)/processed/sessions/cicids2017.parquet
SYNTH_DIR         := $(DATA_ROOT)/synth
DIST_DIR          := $(SYNTH_DIR)/distributions
SCENARIOS_DIR     := $(SYNTH_DIR)/scenarios
LOG_DIR           := $(DATA_ROOT)/logs

# Venv
VENV   := ../.venv
PYTHON := $(VENV)/bin/python

# Seeds for each scenario (30 by default)
SEEDS := $(shell seq 1 30)

# Directory of generator .jsonl files whose legitimate sessions `make validate`
# compares with Sprint 1's BENIGN sessions
SYNTH ?= $(SCENARIOS_DIR)/A

.DEFAULT_GOAL := help

.PHONY: help calibrate scenario-A scenario-B scenario-C validate clean

help:
	@echo "Sprint 2: synthetic generator"
	@echo ""
	@echo "Prerequisite: Sprint 1 validated ($(SPRINT1_SESSIONS) must exist)"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

calibrate:  ## Extract distributions from Sprint 1's legitimate sessions
	@[ -f $(SPRINT1_SESSIONS) ] || { echo "❌ $(SPRINT1_SESSIONS) does not exist. Finish Sprint 1 first."; exit 1; }
	@mkdir -p $(DIST_DIR) $(LOG_DIR)
	$(PYTHON) scripts/calibrate.py \
	  --sessions $(SPRINT1_SESSIONS) \
	  --out-dir $(DIST_DIR) \
	  2>&1 | tee $(LOG_DIR)/sprint2_calibrate.log
	@echo "✅ Distributions in $(DIST_DIR)/"

scenario-A:  ## Generate Scenario A (concentrated, K=1), 30 seeds
	@mkdir -p $(SCENARIOS_DIR)/A $(LOG_DIR)
	@for s in $(SEEDS); do \
	  echo "==> A: seed $$s"; \
	  $(PYTHON) scripts/generator.py \
	    --config configs/scenario_A.yaml \
	    --seed $$s \
	    --out $(SCENARIOS_DIR)/A/seed_$$s.jsonl \
	    --distributions $(DIST_DIR) \
	    2>&1 | tee -a $(LOG_DIR)/sprint2_scenarioA.log; \
	done
	@echo "✅ Scenario A generated in $(SCENARIOS_DIR)/A/"

scenario-B:  ## Generate Scenario B (moderate, K=10..100), 30 seeds × 3 values of K
	@mkdir -p $(SCENARIOS_DIR)/B $(LOG_DIR)
	@for k in 10 50 100; do \
	  for s in $(SEEDS); do \
	    echo "==> B: K=$$k seed=$$s"; \
	    $(PYTHON) scripts/generator.py \
	      --config configs/scenario_B.yaml \
	      --param K=$$k \
	      --seed $$s \
	      --out $(SCENARIOS_DIR)/B/K$$k\_seed$$s.jsonl \
	      --distributions $(DIST_DIR); \
	  done; \
	done
	@echo "✅ Scenario B generated in $(SCENARIOS_DIR)/B/"

scenario-C:  ## Generate Scenario C (distributed, K=1000..10000), 30 seeds × 2 values of K
	@mkdir -p $(SCENARIOS_DIR)/C $(LOG_DIR)
	@for k in 1000 10000; do \
	  for s in $(SEEDS); do \
	    echo "==> C: K=$$k seed=$$s"; \
	    $(PYTHON) scripts/generator.py \
	      --config configs/scenario_C.yaml \
	      --param K=$$k \
	      --seed $$s \
	      --out $(SCENARIOS_DIR)/C/K$$k\_seed$$s.jsonl \
	      --distributions $(DIST_DIR); \
	  done; \
	done
	@echo "✅ Scenario C generated in $(SCENARIOS_DIR)/C/"

validate:  ## Compare synthetic and real distributions (Kolmogorov-Smirnov test); SYNTH=<dir of .jsonl>
	$(PYTHON) scripts/validate_synth.py \
	  --real $(SPRINT1_SESSIONS) \
	  --synth $(SYNTH)

clean:  ## Remove the synthetic scenarios (keeps the calibration)
	rm -rf $(SCENARIOS_DIR)/{A,B,C}
	@echo "✅ Scenarios removed. Calibration kept in $(DIST_DIR)/"
