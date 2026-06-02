# Pilar 2 — Raciocínio Simbólico (veredicto-como-derivação)

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

help:  ## Lista targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-8s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

demo:  ## Avalia coordinatedHTTPFlood por SWRL+SPARQL num grafo-brinquedo (offline)
	$(PYTHON) scripts/reason.py --demo
