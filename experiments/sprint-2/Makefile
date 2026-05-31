# Sprint 2 — Gerador Sintético Calibrado

SHELL := /bin/bash

# Carregar DATA_ROOT do .env da pasta experiments/
ENV_FILE := $(abspath ../.env)
ifneq ("$(wildcard $(ENV_FILE))","")
    include $(ENV_FILE)
    export
endif

DATA_ROOT ?= $(error DATA_ROOT não definido)

# Paths
SPRINT1_SESSIONS  := $(DATA_ROOT)/processed/sessions/cicids2017.parquet
SYNTH_DIR         := $(DATA_ROOT)/synth
DIST_DIR          := $(SYNTH_DIR)/distributions
SCENARIOS_DIR     := $(SYNTH_DIR)/scenarios
LOG_DIR           := $(DATA_ROOT)/logs

# Venv
VENV   := ../.venv
PYTHON := $(VENV)/bin/python

# Seeds para cada cenário (30 por padrão)
SEEDS := $(shell seq 1 30)

.DEFAULT_GOAL := help

.PHONY: help calibrate scenario-A scenario-B scenario-C validate clean

help:
	@echo "Sprint 2 — Gerador Sintético"
	@echo ""
	@echo "Pré-requisito: Sprint 1 validado ($(SPRINT1_SESSIONS) deve existir)"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

calibrate:  ## Extrai distribuições das sessões legítimas do Sprint 1
	@[ -f $(SPRINT1_SESSIONS) ] || { echo "❌ $(SPRINT1_SESSIONS) não existe. Conclua Sprint 1 primeiro."; exit 1; }
	@mkdir -p $(DIST_DIR) $(LOG_DIR)
	$(PYTHON) scripts/calibrate.py \
	  --sessions $(SPRINT1_SESSIONS) \
	  --out-dir $(DIST_DIR) \
	  2>&1 | tee $(LOG_DIR)/sprint2_calibrate.log
	@echo "✅ Distribuições em $(DIST_DIR)/"

scenario-A:  ## Gera Cenário A (concentrado, K=1) — 30 seeds
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
	@echo "✅ Cenário A gerado em $(SCENARIOS_DIR)/A/"

scenario-B:  ## Gera Cenário B (moderado, K=10..100) — 30 seeds × 3 valores de K
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
	@echo "✅ Cenário B gerado em $(SCENARIOS_DIR)/B/"

scenario-C:  ## Gera Cenário C (distribuído, K=1000..10000) — 30 seeds × 2 valores de K
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
	@echo "✅ Cenário C gerado em $(SCENARIOS_DIR)/C/"

validate:  ## Compara distribuições sintético × real (teste Kolmogorov-Smirnov)
	$(PYTHON) scripts/validate_synth.py \
	  --real $(SPRINT1_SESSIONS) \
	  --synth $(SCENARIOS_DIR)/A \
	  --distributions $(DIST_DIR)

clean:  ## Remove dados sintéticos (mantém calibração)
	rm -rf $(SCENARIOS_DIR)/{A,B,C}
	@echo "✅ Cenários removidos. Calibração preservada em $(DIST_DIR)/"
