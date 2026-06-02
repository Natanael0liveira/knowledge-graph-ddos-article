# Sprint 5 — Comparação com KLAGE (CIC-IoT2023)

SHELL := /bin/bash
ENV_FILE := $(abspath ../.env)
ifneq ("$(wildcard $(ENV_FILE))","")
    include $(ENV_FILE)
    export
endif

DATA_ROOT ?= $(error DATA_ROOT não definido)
SESSIONS  := $(DATA_ROOT)/processed/sessions/cic-iot-2023.parquet
VENV      := ../.venv
PYTHON    := $(VENV)/bin/python

.DEFAULT_GOAL := help
.PHONY: help run

help:  ## Lista targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-8s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run:  ## Compara nosso arcabouço × KLAGE em DDoS Slowloris (CIC-IoT2023)
	@[ -f $(SESSIONS) ] || { echo "❌ $(SESSIONS) não existe (rode Sprint 1 p/ cic-iot-2023)."; exit 1; }
	$(PYTHON) scripts/run_klage_comparison.py \
	  --sessions $(SESSIONS) \
	  --out results/klage_comparison.json
