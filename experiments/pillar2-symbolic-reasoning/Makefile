# Pillar 2: the sub-relations as SWRL rules and the Ω(S) aggregation in SPARQL

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

demo:  ## Evaluate coordinatedHTTPFlood with SWRL rules (as SPARQL CONSTRUCT) and SPARQL on a toy graph (offline)
	$(PYTHON) scripts/reason.py --demo
