# Sprint 5: comparison with KLAGE (CIC-IoT2023)

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
SESSIONS  := $(DATA_ROOT)/processed/sessions/cic-iot-2023.parquet
VENV      := ../.venv
PYTHON    := $(VENV)/bin/python

.DEFAULT_GOAL := help
.PHONY: help run

help:  ## List the targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-8s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run:  ## Compare with KLAGE on DDoS Slowloris (CIC-IoT2023)
	@[ -f $(SESSIONS) ] || { echo "❌ $(SESSIONS) does not exist (run Sprint 1 with DATASET=cic-iot-2023)."; exit 1; }
	$(PYTHON) scripts/run_klage_comparison.py \
	  --sessions $(SESSIONS) \
	  --out results/klage_comparison.json
