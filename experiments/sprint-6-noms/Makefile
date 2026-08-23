# Sprint 6 (NOMS) — experiments added for the IEEE/IFIP NOMS submission.
#
#   latency    : per-request admission + per-window symbolic evaluation vs |S_W|
#                (NO external data needed — runs anywhere)
#   ml         : is the per-session collapse specific to Random Forest?
#   window     : sensitivity to the operational window W
#   realistic  : production-realistic scenario sweep (Zipf benign JA4, heterogeneous
#                botnet, adversarial fingerprint adoption) — modal vs enrichment scope
#   canonical  : the ablation that the paper reports, on the realistic scenario
#   purity     : collateral vs benign prevalence of the discriminator
#   drift      : sensitivity of the derived scope to the background profile the
#                enrichment test reads (matched / drifted / flat)
#   symbolic   : the SPARQL/enrichment rule evaluated AS a detector, against the
#                learned model forced onto the same operating point
#   all-hd     : everything that needs the external drive
#
# The external drive must be mounted for `ml` and `window`:
#   experiments/data -> /Volumes/Untitled/kg-ddos-data

PY       ?= ../.venv/bin/python
DATA     ?= ../data
DIST     ?= $(DATA)/synth/distributions
# Canonical scenario cache: the REALISTIC same-service run that produced the
# paper's Table III. NOT synth/sprint4 (pre-flow-feature cache, missing columns)
# and NOT synth/sprint4_strong_work (still carries the target-port artefact,
# where config (b) reaches 0.888 instead of collapsing to chance).
WORK     ?= $(DATA)/synth/sprint4_realistic_work
RESULTS  ?= results
SEEDS    ?= 30
K        ?= 50 1000

.PHONY: help latency ml window realistic canonical purity symbolic drift all-hd check-data clean

help:
	@echo "make latency            # no external data required"
	@echo "make ml                 # needs the HD (reuses the sprint-4 scenario cache)"
	@echo "make window             # needs the HD"
	@echo "make realistic          # needs the HD"
	@echo "make canonical          # needs the HD — gera a tabela do paper"
	@echo "make purity             # needs the HD"
	@echo "make all-hd             # tudo que precisa do HD"
	@echo ""
	@echo "Vars: SEEDS=$(SEEDS)  K='$(K)'  DATA=$(DATA)"

check-data:
	@test -d "$(DIST)" || { \
	  echo "ERROR: $(DIST) not found."; \
	  echo "Mount the external drive (experiments/data -> /Volumes/Untitled/kg-ddos-data)."; \
	  exit 1; }
	@echo "data OK: $(DIST)"

latency:
	$(PY) scripts/bench_latency.py \
	  --sizes 100 250 500 1000 2500 5000 10000 \
	  --repeats 3 --probes 200 --pair-cap 400000 \
	  --out $(RESULTS)

ml: check-data
	$(PY) scripts/run_ml_families.py --seeds $(SEEDS) --K $(K) \
	  --dist-dir $(DIST) --work $(WORK) --out-dir $(RESULTS)

window: check-data
	$(PY) scripts/window_sweep.py --seeds 10 --K 1000 \
	  --W 60 120 300 600 1800 \
	  --dist-dir $(DIST) --work $(WORK) --out-dir $(RESULTS)

REALWORK ?= $(DATA)/synth/sprint6_realistic

realistic: check-data
	nice -n 10 $(PY) scripts/realistic_probe.py \
	  --grid 0:1:0 1.5:1:0 1.5:5:0 1.5:25:0 1.5:100:0 2.0:25:0 1.5:5:1 1.5:25:1 2.0:25:1 \
	  --seeds 15 --dist-dir $(DIST) --work $(REALWORK) --out-dir $(RESULTS) --tag final

canonical: check-data
	nice -n 10 $(PY) scripts/run_canonical_realistic.py --seeds $(SEEDS) --K $(K) \
	  --alpha 1.5 --stacks 25 \
	  --dist-dir $(DIST) --work $(REALWORK) --out-dir $(RESULTS)

purity: check-data
	nice -n 10 $(PY) scripts/collateral_purity_sweep.py --scenarios $(WORK) \
	  --p 0 0.001 0.005 0.01 0.05 0.1 0.25 0.5 0.75 0.9 \
	  --max-files 30 --out-dir $(RESULTS)

symbolic: check-data
	nice -n 10 $(PY) scripts/symbolic_detector.py --work $(REALWORK) \
	  --grid 0.0:1:0 1.5:1:0 1.5:5:0 1.5:25:0 1.5:100:0 2.0:25:0 \
	         1.5:5:1 1.5:25:1 2.0:25:1 \
	  --K 1000 --seeds 15 --out-dir $(RESULTS)

drift: check-data
	nice -n 10 $(PY) scripts/profile_drift.py --work $(REALWORK) \
	  --alpha 1.5 --stacks 25 --K 1000 --seeds 15 --out-dir $(RESULTS)

all-hd: ml window realistic canonical purity symbolic drift

clean:
	rm -rf $(RESULTS)/*.csv $(RESULTS)/*.json
