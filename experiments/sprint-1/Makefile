# Sprint 1 — Pipeline de Extração (PCAP → KG)
#
# Uso: a partir desta pasta (experiments/sprint-1/):
#   make help

# ----- Configuração -----
SHELL := /bin/bash

# Carregar DATA_ROOT do .env da pasta experiments/
ENV_FILE := $(abspath ../.env)
ifneq ("$(wildcard $(ENV_FILE))","")
    include $(ENV_FILE)
    export
endif

DATA_ROOT ?= $(error DATA_ROOT não definido. Rode primeiro: ../scripts/setup-data-storage.sh /Volumes/SeuHD/kg-ddos-data)

# Dataset alvo (default: CICIDS2017 para Sprint 1)
DATASET ?= cicids2017

# Caminhos derivados
RAW_DIR        := $(DATA_ROOT)/raw/$(DATASET)
PROCESSED_DIR  := $(DATA_ROOT)/processed
JA4_DIR        := $(PROCESSED_DIR)/ja4/$(DATASET)
FLOWS_DIR      := $(PROCESSED_DIR)/flows/$(DATASET)
SESSIONS_FILE  := $(PROCESSED_DIR)/sessions/$(DATASET).parquet
CLUSTERS_FILE  := $(PROCESSED_DIR)/clusters/$(DATASET).csv
KG_DIR         := $(DATA_ROOT)/kg
LOG_DIR        := $(DATA_ROOT)/logs

# Venv
VENV := ../.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Java — prefere openjdk@17 do brew sobre o stub do macOS em /usr/bin/java
JAVA_BREW := $(shell brew --prefix openjdk@17 2>/dev/null)/bin/java
JAVA := $(shell [ -x "$(JAVA_BREW)" ] && echo "$(JAVA_BREW)" || command -v java 2>/dev/null)

# Fuseki
FUSEKI_URL := http://localhost:3030

# ----- Default -----
.DEFAULT_GOAL := help

.PHONY: help check python-venv install-deps install-cicflowmeter \
        fuseki-up fuseki-down fuseki-logs \
        test download extract-ja4 extract-flows sessions clusters load-kg \
        validate stats clean clean-all

# ----- Help -----
help:  ## Mostra esta ajuda
	@echo "Sprint 1 — Pipeline de Extração (PCAP → KG)"
	@echo ""
	@echo "Configuração:"
	@echo "  DATA_ROOT = $(DATA_ROOT)"
	@echo ""
	@echo "Targets disponíveis:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "Sequência típica:"
	@echo "  make check       # valida dependências"
	@echo "  make fuseki-up   # sobe o triple store"
	@echo "  make test        # roda pipeline em PCAP pequeno (validação)"
	@echo "  make download    # baixa CIC-DDoS2019 Slowloris"
	@echo "  make extract-ja4 && make extract-flows  # background"
	@echo "  make sessions && make clusters"
	@echo "  make load-kg"
	@echo "  make validate    # notebook Jupyter com relatório"

# ----- Validação de dependências -----
check:  ## Verifica dependências (Python, Docker, tshark, Java)
	@echo "==> Verificando dependências..."
	@command -v python3 >/dev/null || { echo "❌ python3 não encontrado"; exit 1; }
	@command -v tshark  >/dev/null || { echo "❌ tshark não encontrado (brew install wireshark)"; exit 1; }
	@[ -x "$(JAVA)" ] || command -v java >/dev/null || { echo "❌ java não encontrado (brew install openjdk@17)"; exit 1; }
	@command -v docker  >/dev/null && docker info >/dev/null 2>&1 || { echo "⚠️  docker não encontrado ou daemon parado. Apache Jena Fuseki não rodará. Instale Docker Desktop para o passo make load-kg."; }
	@[ -f $(ENV_FILE) ] || { echo "❌ $(ENV_FILE) não encontrado (rode setup-data-storage.sh)"; exit 1; }
	@[ -d $(DATA_ROOT) ] || { echo "❌ DATA_ROOT $(DATA_ROOT) não acessível"; exit 1; }
	@echo "✅ Dependências críticas OK"
	@echo "    DATA_ROOT=$(DATA_ROOT)"
	@echo "    tshark version: $$(tshark --version | head -1)"
	@echo "    java path: $(JAVA)"
	@echo "    Free space: $$(df -g $(DATA_ROOT) | awk 'NR==2 {print $$4}') GB"

# ----- Setup do ambiente Python -----
python-venv:  ## Cria virtualenv Python em ../.venv
	@[ -d $(VENV) ] || python3 -m venv $(VENV)
	@echo "✅ venv em $(VENV)"

install-deps: python-venv  ## Instala dependências Python (após criar venv)
	$(PIP) install --upgrade pip
	$(PIP) install -r ../requirements.txt
	@echo "✅ Dependências instaladas. Ative com: source $(VENV)/bin/activate"

install-cicflowmeter:  ## Instala cicflowmeter via pip + aplica patches (scapy 2.5 + bugfixes)
	@if ! $(PYTHON) -c "import cicflowmeter" 2>/dev/null; then \
	  echo "==> Instalando cicflowmeter via pip..."; \
	  $(PIP) install cicflowmeter; \
	fi
	@# cicflowmeter 0.2.0 usa API antiga de sessions do scapy (toPacketList).
	@# Em scapy >= 2.6 essa API mudou e cicflowmeter para de funcionar (CSV vazio).
	@if ! $(PYTHON) -c "import scapy; v=tuple(int(x) for x in scapy.VERSION.split('.')[:2]); exit(0 if v <= (2,5) else 1)" 2>/dev/null; then \
	  echo "==> Downgrade scapy para 2.5.0 (compat com cicflowmeter)..."; \
	  $(PIP) install "scapy==2.5.0"; \
	fi
	@# Aplica patches in-place no venv (bugs de min() em sequência vazia)
	@$(PYTHON) scripts/patch_cicflowmeter.py
	@echo "✅ cicflowmeter pronto"

# ----- Fuseki (Apache Jena triple store) -----
fuseki-up:  ## Sobe Apache Jena Fuseki via Docker
	docker compose up -d
	@echo "✅ Fuseki rodando em $(FUSEKI_URL)"
	@echo "    Admin: $(FUSEKI_URL)/dataset.html"

fuseki-down:  ## Para o Fuseki
	docker compose down
	@echo "✅ Fuseki parado"

fuseki-logs:  ## Logs do Fuseki
	docker compose logs -f fuseki

# ----- Teste com PCAP público pequeno -----
test:  ## Roda pipeline completa em PCAP de teste pequeno (~100 MB)
	@mkdir -p $(LOG_DIR) ../sample-data
	@if [ ! -f ../sample-data/slowloris-test.pcap ]; then \
	  echo "==> Baixando PCAP de teste..."; \
	  echo "    (TODO: link público a definir; usa sample do Wireshark)"; \
	  exit 1; \
	fi
	$(PYTHON) scripts/extract_ja4.py --pcap ../sample-data/slowloris-test.pcap --out ../sample-data/ja4.csv
	$(PYTHON) scripts/extract_flows.py --pcap ../sample-data/slowloris-test.pcap --out ../sample-data/flows.csv
	$(PYTHON) scripts/build_sessions.py --ja4 ../sample-data/ja4.csv --flows ../sample-data/flows.csv --out ../sample-data/sessions.parquet
	@echo "✅ Test pipeline OK. Verifique ../sample-data/"

# ----- Pipeline principal: CIC-DDoS2019 -----
download:  ## Instruções para baixar CICIDS2017 (requer registro UNB)
	@echo "==> CICIDS2017 requer registro manual na UNB:"
	@echo "    https://www.unb.ca/cic/datasets/ids-2017.html"
	@echo ""
	@echo "    Após registro/login, baixe APENAS:"
	@echo "      📄 Wednesday-WorkingHours.pcap          (~12 GB)"
	@echo "        → contém DoS slowloris, DoS Slowhttptest, DoS Hulk, DoS GoldenEye"
	@echo "      📄 Wednesday-WorkingHours.pcap_ISCX.csv (~10 MB)"
	@echo "        → rótulos por flow (BENIGN / DoS slowloris / DoS Slowhttptest / ...)"
	@echo ""
	@echo "    Salve em:"
	@echo "    $(RAW_DIR)/"
	@echo ""
	@echo "    Quando terminar:"
	@echo "      make extract-ja4 && make extract-flows"

extract-ja4: check  ## Extrai JA4 de cada PCAP em raw/ (recursivo) via tshark
	@mkdir -p $(JA4_DIR) $(LOG_DIR)
	@pcaps=$$(find $(RAW_DIR) -type f -name "*.pcap" -not -name "._*"); \
	[ -n "$$pcaps" ] || { echo "❌ Nenhum PCAP em $(RAW_DIR). Rode 'make download' primeiro."; exit 1; }; \
	for pcap in $$pcaps; do \
	  relpath=$$(echo "$$pcap" | sed "s|$(RAW_DIR)/||"); \
	  name=$$(echo "$$relpath" | sed "s|/|_|g" | sed "s|.pcap$$||"); \
	  echo "==> Extraindo JA4 de $$relpath..."; \
	  $(PYTHON) scripts/extract_ja4.py \
	    --pcap "$$pcap" \
	    --out "$(JA4_DIR)/$$name.csv" \
	    2>&1 | tee "$(LOG_DIR)/extract_ja4_$$name.log"; \
	done
	@echo "✅ JA4 extraído em $(JA4_DIR)/"

extract-flows: check install-cicflowmeter  ## Extrai flows (recursivo) via cicflowmeter Python
	@mkdir -p $(FLOWS_DIR) $(LOG_DIR)
	@pcaps=$$(find $(RAW_DIR) -type f -name "*.pcap" -not -name "._*"); \
	[ -n "$$pcaps" ] || { echo "❌ Nenhum PCAP em $(RAW_DIR)"; exit 1; }; \
	for pcap in $$pcaps; do \
	  relpath=$$(echo "$$pcap" | sed "s|$(RAW_DIR)/||"); \
	  name=$$(echo "$$relpath" | sed "s|/|_|g" | sed "s|.pcap$$||"); \
	  echo "==> Extraindo flows de $$relpath..."; \
	  $(PYTHON) scripts/extract_flows.py \
	    --pcap "$$pcap" \
	    --out "$(FLOWS_DIR)/$$name.csv" \
	    2>&1 | tee "$(LOG_DIR)/extract_flows_$$name.log"; \
	done
	@echo "✅ Flows extraídos em $(FLOWS_DIR)/"

sessions:  ## Reconstrói sessões a partir de flows + JA4
	@mkdir -p $(dir $(SESSIONS_FILE)) $(LOG_DIR)
	$(PYTHON) scripts/build_sessions.py \
	  --ja4-dir $(JA4_DIR) \
	  --flows-dir $(FLOWS_DIR) \
	  --out $(SESSIONS_FILE) \
	  --window 300 \
	  2>&1 | tee $(LOG_DIR)/build_sessions.log
	@echo "✅ Sessões em $(SESSIONS_FILE)"

clusters:  ## Deriva ground truth de cluster
	@mkdir -p $(dir $(CLUSTERS_FILE)) $(LOG_DIR)
	$(PYTHON) scripts/derive_clusters.py \
	  --sessions $(SESSIONS_FILE) \
	  --out $(CLUSTERS_FILE) \
	  --sample 10 \
	  2>&1 | tee $(LOG_DIR)/derive_clusters.log
	@echo "✅ Clusters em $(CLUSTERS_FILE) (amostra para revisão manual: $(CLUSTERS_FILE).sample)"

load-kg:  ## Carrega sessões e clusters no Apache Jena Fuseki
	$(PYTHON) scripts/load_to_fuseki.py \
	  --sessions $(SESSIONS_FILE) \
	  --clusters $(CLUSTERS_FILE) \
	  --ontology ../../ontology/ddos_ontology.owl \
	  --fuseki-url $(FUSEKI_URL) \
	  --dataset cic-ddos-2019 \
	  --export-ttl $(KG_DIR)/exports/cic-ddos-2019.ttl \
	  2>&1 | tee $(LOG_DIR)/load_to_fuseki.log
	@echo "✅ KG carregado em $(FUSEKI_URL)/cic-ddos-2019/sparql"

# ----- Validação -----
validate:  ## Abre notebook Jupyter com relatório de validação
	$(PYTHON) -m jupyter notebook notebooks/validate.ipynb

stats:  ## Imprime estatísticas básicas
	$(PYTHON) scripts/stats.py --sessions $(SESSIONS_FILE) --clusters $(CLUSTERS_FILE)

# ----- Limpeza -----
clean:  ## Remove artefatos intermediários (mantém raw e KG)
	rm -rf $(JA4_DIR) $(FLOWS_DIR) $(SESSIONS_FILE) $(CLUSTERS_FILE) $(LOG_DIR)
	@echo "✅ Limpeza concluída (raw/ e kg/ preservados)"

clean-all:  ## ⚠️  Remove TUDO incluindo PCAPs e KG. Use com cuidado.
	@echo "⚠️  Isso vai apagar TUDO em $(DATA_ROOT)."
	@read -p "Tem certeza? Digite 'sim apagar': " confirm; \
	if [ "$$confirm" = "sim apagar" ]; then \
	  rm -rf $(RAW_DIR) $(PROCESSED_DIR) $(KG_DIR) $(LOG_DIR); \
	  echo "✅ Tudo limpo."; \
	else \
	  echo "Cancelado."; \
	fi
