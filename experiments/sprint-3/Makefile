# Sprint 3 — Baselines + Ablação

SHELL := /bin/bash

ENV_FILE := $(abspath ../.env)
ifneq ("$(wildcard $(ENV_FILE))","")
    include $(ENV_FILE)
    export
endif

DATA_ROOT ?= $(error DATA_ROOT não definido)
DIST_DIR  := $(DATA_ROOT)/synth/distributions
SYNTH_DIR := $(DATA_ROOT)/synth/sprint3
LOG_DIR   := $(DATA_ROOT)/logs

VENV   := ../.venv
PYTHON := $(VENV)/bin/python
GEN    := ../sprint-2/scripts
SEED   ?= 7

.DEFAULT_GOAL := help
.PHONY: help scenarios ablation multiattack clean

help:  ## Lista targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

scenarios:  ## Gera cenários furtivos K=1/50/1000 + converte p/ sessions
	@[ -f $(DIST_DIR)/session_requests.json ] || { echo "❌ Calibre o Sprint 2: make -C ../sprint-2 calibrate"; exit 1; }
	@mkdir -p $(SYNTH_DIR) $(LOG_DIR)
	@for k in 1 50 1000; do \
	  echo "==> stealth K=$$k"; \
	  $(PYTHON) $(GEN)/generator.py --config ../sprint-2/configs/scenario_stealth.yaml \
	    --param K=$$k --seed $(SEED) --distributions $(DIST_DIR) \
	    --out $(SYNTH_DIR)/stealth_K$$k.jsonl 2>&1 | tail -1; \
	  $(PYTHON) $(GEN)/synth_to_sessions.py --jsonl $(SYNTH_DIR)/stealth_K$$k.jsonl \
	    --out $(SYNTH_DIR)/stealth_K$$k.parquet 2>&1 | grep sessions; \
	done
	@echo "✅ Cenários em $(SYNTH_DIR)/"

ablation:  ## Roda baselines + ablação a/b/c/d e imprime a tabela
	$(PYTHON) scripts/run_ablation.py \
	  --scenario K1=$(SYNTH_DIR)/stealth_K1.parquet \
	             K50=$(SYNTH_DIR)/stealth_K50.parquet \
	             K1000=$(SYNTH_DIR)/stealth_K1000.parquet \
	  2>&1 | tee $(LOG_DIR)/sprint3_ablation.log

REAL_S1 := $(DATA_ROOT)/processed/sessions/cicids2017.parquet
REAL_S2 := $(DATA_ROOT)/processed/sessions/cic-iot-2023.parquet

multiattack:  ## Passo A do HARDENING: generalização multi-ataque em dados reais (a vs d)
	@[ -f $(REAL_S1) ] || { echo "❌ $(REAL_S1) não existe (HD externo montado?)"; exit 1; }
	@mkdir -p results
	$(PYTHON) scripts/run_real_multiattack.py \
	  --dataset cicids2017=$(REAL_S1) \
	  --dataset cic-iot-2023=$(REAL_S2) \
	  --out results/real_multiattack.csv \
	  2>&1 | tee $(LOG_DIR)/sprint3_multiattack.log

clean:  ## Remove cenários do Sprint 3
	rm -rf $(SYNTH_DIR)
	@echo "✅ removido $(SYNTH_DIR)"
