# Pillar 4: evidence chain and scoped mitigation

SHELL := /bin/bash
ENV_FILE := $(abspath ../.env)
ifneq ("$(wildcard $(ENV_FILE))","")
    include $(ENV_FILE)
    export
endif

VENV   := ../.venv
PYTHON := $(VENV)/bin/python

.DEFAULT_GOAL := help
.PHONY: help demo

help:  ## List the targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-8s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

demo:  ## Demonstrate the evidence and mitigation chain on a toy cluster (offline; overwrites results/)
	$(PYTHON) scripts/evidence_mitigation.py --demo --out-dir results
