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
# Calibrated generator distributions (aggregates of public CICIDS2017), versioned
# in sprint-2/distributions so scenario generation does not need the data drive.
DIST     ?= ../sprint-2/distributions
# Scenario cache of the sprint-4 reproduction (same-service, near-uniform benign
# pool, monolithic botnet), read by `ml`, `window` and `purity`. The paper's
# canonical scenarios (alpha = 1.5, 25 TLS stacks) are REALWORK below. NOT
# synth/sprint4 (pre-flow-feature cache, missing columns) and NOT
# synth/sprint4_strong_work (still carries the target-port artefact, where
# config (b) reaches 0.888 instead of collapsing to chance).
WORK     ?= $(DATA)/synth/sprint4_realistic_work
RESULTS  ?= results
SEEDS    ?= 30
K        ?= 50 1000
# Family-wise level of the binomial over-representation test that selects the
# fingerprints of the enrichment scope (Section III-G). Empty = the fixed floor
# sigma = 0.002 of earlier revisions.
SIG      ?= 0.01
SIGFLAG   = $(if $(SIG),--significance $(SIG))
# The paper's method (Section III-G): Omega and the scope count distinct origins
# (source addresses), and the scope's test level is calibrated per endpoint on
# attack-free traffic, as tau is, never above SIG. `make METHOD= <target>` reruns
# with the session count and nominal level of earlier revisions.
METHOD   ?= origin
METHODFLAG = $(if $(METHOD),--unit $(METHOD) --calibrate-level)
# The per-cluster experiments evaluate the cluster of largest Omega, chosen with no
# label; `make CLUSTER= <target>` restores the attack-share choice of earlier revisions.
CLUSTER  ?= label-free
CLUSTERFLAG = $(if $(CLUSTER),--label-free-cluster)
# Attack-free runs of rule_detection.py (calibration, test and flash-crowd donors).
RULEWORK ?= $(DATA)/synth/sprint6_rule

.PHONY: rule-production-od help latency ml window realistic canonical purity symbolic drift all-hd check-data clean baselines rule rule-production production-summary audit compile-check stix-check stix-ingest rule-production-fleets fleet-selection rule-production-fresh production-tables unseen-synth cross-m

help:
	@echo "No external data required:"
	@echo "  make audit              # every sprint-6 number of the paper against results/"
	@echo "  make compile-check      # the count query compiled from the ontology, on generated sessions"
	@echo "  make stix-check         # the exported STIX 2.1 bundles, OASIS validator in strict mode"
	@echo "  make stix-ingest        # the same bundles through TAXII 2.1 and MISP's importer"
	@echo "  make latency            # cost of both layers (Fig. 3; the full sweep takes long)"
	@echo "Needs the data drive (synthetic scenario caches):"
	@echo "  make canonical          # the ablation of Section V-A"
	@echo "  make realistic symbolic unseen-synth   # Section V-C, Table II and Fig. 2"
	@echo "  make drift rule baselines cross-m"
	@echo "  make ml window purity   # sprint-4 reproduction cache"
	@echo "Needs the operator's exports on the drive (PRODDATA):"
	@echo "  make rule-production rule-production-fresh rule-production-od"
	@echo "  make production-tables  # Tables III and IV, anonymized to results/"
	@echo ""
	@echo "Vars: SEEDS=$(SEEDS)  K='$(K)'  DATA=$(DATA)"

check-data:
	@test -d "$(REALWORK)" || { \
	  echo "ERROR: $(REALWORK) not found (cached scenarios live on the data drive)."; \
	  echo "Mount the external drive (experiments/data -> /Volumes/Untitled/kg-ddos-data)."; \
	  exit 1; }
	@echo "data OK: $(REALWORK)"

latency:
	$(PY) scripts/bench_latency.py \
	  --sizes 100 250 500 1000 2500 5000 10000 25000 50000 100000 \
	  --repeats 3 --probes 200 --pair-cap 3000000 \
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
	  --seeds 15 --dist-dir $(DIST) --work $(REALWORK) --out-dir $(RESULTS) --tag final $(SIGFLAG) \
	  $(METHODFLAG) --clean-work $(RULEWORK) $(CLUSTERFLAG)

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
	  --K 1000 --seeds 15 --out-dir $(RESULTS) $(SIGFLAG) \
	  $(METHODFLAG) $(CLUSTERFLAG) --clean-work $(RULEWORK) --dist-dir $(DIST)

drift: check-data
	nice -n 10 $(PY) scripts/profile_drift.py --work $(REALWORK) \
	  --alpha 1.5 --stacks 25 --K 1000 --seeds 15 --out-dir $(RESULTS) $(SIGFLAG) \
	  $(METHODFLAG) $(CLUSTERFLAG) --clean-work $(RULEWORK) --dist-dir $(DIST)
	nice -n 10 $(PY) scripts/profile_drift.py --work $(REALWORK) --pooled-work $(RULEWORK) \
	  --alpha 1.5 --stacks 100 --K 1000 --seeds 15 --out-dir $(RESULTS) $(SIGFLAG) --tag _m100 \
	  $(METHODFLAG) $(CLUSTERFLAG) --clean-work $(RULEWORK) --dist-dir $(DIST)

all-hd: ml window realistic canonical purity symbolic drift

clean:
	rm -rf $(RESULTS)/*.csv $(RESULTS)/*.json

# Academic baselines on the canonical scenarios: the source of Section V-A's baseline numbers.
baselines: check-data
	nice -n 10 $(PY) scripts/run_canonical_baselines.py --work $(REALWORK) --out-dir $(RESULTS)

# The rule Omega >= tau as a window-level detector, with flash crowds. Benign
# traffic is spread over 60 min, since the generator packs it into one window;
# the stealth campaign does not raise the aggregate rate, so condition (iv) is off;
# the background profile pools the 30 attack-free calibration runs. The second
# run repeats it with the 1,000-session profile of the cluster-level experiments.
rule: check-data
	nice -n 10 $(PY) scripts/rule_detection.py --work $(REALWORK) --clean-work $(RULEWORK) \
	  --dist-dir $(DIST) --out-dir $(RESULTS) --percentiles 99 --steady-minutes 60 \
	  --tau-rate 0 --profile calib $(SIGFLAG) $(METHODFLAG) --tag _steady60_rate0_bigprof_binom
	nice -n 10 $(PY) scripts/rule_detection.py --work $(REALWORK) --clean-work $(RULEWORK) \
	  --dist-dir $(DIST) --out-dir $(RESULTS) --percentiles 99 --steady-minutes 60 \
	  --tau-rate 0 --profile baseline $(SIGFLAG) $(METHODFLAG) --tag _steady60_rate0_binom

# The rule per window on production traffic, with the canonical botnet injected
# into the counts. The exports are aggregates of a CDN's access log, kept on the
# data drive (one YYYY-MM-DD directory per day) and never in the repository; the
# results go next to them for the same reason. The origin count needs the E3/E4
# exports; SPLIT=rolling tests each day on a profile, tau and level calibrated on
# the days before it, as the rule would run.
PRODDATA ?= $(DATA)/azion
SPLIT    ?= rolling
# The eight days behind Tables III and IV and Appendix E (five test folds); the fresh day
# 2026-09-25 is evaluated apart (rule-production-fresh, fresh_day_protocol.md).
TESTDAYS ?= 2026-09-17_2026-09-24 2026-09-23

rule-production:
	@test -d "$(PRODDATA)" || { \
	  echo "ERROR: $(PRODDATA) not found (production exports live on the data drive)."; \
	  exit 1; }
	nice -n 10 $(PY) scripts/rule_detection_production.py --data-dir $(PRODDATA) \
	  --days $(TESTDAYS) --out-dir $(PRODDATA)/results --split $(SPLIT) $(SIGFLAG) \
	  $(if $(METHOD),$(METHODFLAG),--unit session) --tag _$(SPLIT)_$(or $(METHOD),session)

# The known-fleet profile (README section 11): the grid of shares, then the choice
# on the first three test days and the held-out test on the last two.
FLEETS ?= 0.005 0.01 0.02 0.05
rule-production-fleets:
	for s in $(FLEETS); do nice -n 10 $(PY) scripts/rule_detection_production.py \
	  --data-dir $(PRODDATA) --days $(TESTDAYS) --out-dir $(PRODDATA)/results --split $(SPLIT) $(SIGFLAG) \
	  $(METHODFLAG) --fleets $$s --tag _$(SPLIT)_$(METHOD)_fleets$$s & done; wait
fleet-selection:
	$(PY) scripts/fleet_selection.py --results $(PRODDATA)/results --roles $(PRODDATA)/roles.json \
	  --shares $(FLEETS) --out $(RESULTS)/fleet_profile.json

# Every day, the fresh one included, with the base rule and with the chosen known-fleet
# share (5%): the fresh day is a sixth test fold calibrated on all earlier days. The
# first five folds reproduce rule-production and rule-production-fleets exactly.
rule-production-fresh:
	nice -n 10 $(PY) scripts/rule_detection_production.py --data-dir $(PRODDATA) \
	  --out-dir $(PRODDATA)/results --split $(SPLIT) $(SIGFLAG) $(METHODFLAG) \
	  --tag _$(SPLIT)_$(METHOD)_v2 & \
	nice -n 10 $(PY) scripts/rule_detection_production.py --data-dir $(PRODDATA) \
	  --out-dir $(PRODDATA)/results --split $(SPLIT) $(SIGFLAG) $(METHODFLAG) \
	  --fleets 0.05 --tag _$(SPLIT)_$(METHOD)_fleets0.05_v2 & wait

# The same two runs with the overdispersed background (--overdispersion): each profile
# fingerprint is tested against a beta-binomial whose intra-window correlation is
# estimated on the calibration windows, so that fleets of clients that switch on
# together no longer force the level down (README section 13).
rule-production-od:
	nice -n 10 $(PY) scripts/rule_detection_production.py --data-dir $(PRODDATA) \
	  --out-dir $(PRODDATA)/results --split $(SPLIT) $(SIGFLAG) $(METHODFLAG) --overdispersion \
	  --tag _$(SPLIT)_$(METHOD)_od_v2 & \
	nice -n 10 $(PY) scripts/rule_detection_production.py --data-dir $(PRODDATA) \
	  --out-dir $(PRODDATA)/results --split $(SPLIT) $(SIGFLAG) $(METHODFLAG) --overdispersion \
	  --fleets 0.05 --tag _$(SPLIT)_$(METHOD)_od_fleets0.05_v2 & wait

# The production numbers of Tables III and IV (test days and fresh day apart), with
# the baselines calibrated to the scope's budget, attack-window collateral, the WAF
# cross-check and the calibration floor; anonymized, read by the paper's audit.
production-tables:
	$(PY) scripts/production_tables.py --results $(PRODDATA)/results --roles $(PRODDATA)/roles.json \
	  --base rule_production_windows_$(SPLIT)_$(METHOD)_v2.csv \
	  --fleets rule_production_windows_$(SPLIT)_$(METHOD)_fleets0.05_v2.csv \
	  --od rule_production_windows_$(SPLIT)_$(METHOD)_od_v2.csv \
	  --od-fleets rule_production_windows_$(SPLIT)_$(METHOD)_od_fleets0.05_v2.csv \
	  --test-folds 2026-09-20 2026-09-21 2026-09-22 2026-09-23 2026-09-24 \
	  --fresh-folds 2026-09-25 --out $(RESULTS)/production_tables.json

# The unseen-fingerprint filter on the synthetic scenarios of Table II and Fig. 2,
# and botnet stacks drawn from the profile's tail, shared with real clients.
unseen-synth: check-data
	$(PY) scripts/unseen_synth.py --out-dir $(RESULTS)

# Does configuration (d) learn coordination or the generator's stack-size band? Train
# on campaigns with M botnet TLS stacks and test on campaigns with another M (5 -> 25,
# 100; 25 -> 5, 100), at alpha 1.5 and K 1,000, on disjoint seeds, since scenarios that
# share a seed share their benign sessions. Reads the cached scenarios, generates none.
cross-m: check-data
	nice -n 10 $(PY) scripts/cross_m_generalization.py --work $(REALWORK) --out-dir $(RESULTS)

# The anonymized summary of rule-production that the paper and `make audit` read:
# E1..E4 with generic roles (from roles.json on the drive), rates only.
production-summary:
	$(PY) scripts/production_summary.py --results $(PRODDATA)/results \
	  --roles $(PRODDATA)/roles.json --out $(RESULTS)/production_summary.json

# The count query compiled from the ontology, checked against decompose_omega on
# generated sessions, plus a sub-relation added to a copy of the ontology (no data).
compile-check:
	$(PY) scripts/compile_counts.py --check --out $(RESULTS)/compile_check.json

# Every committed evidence chain exported as STIX 2.1 and checked by the OASIS
# validator, strict mode included (no data).
stix-check:
	$(PY) scripts/stix_check.py --out $(RESULTS)/stix_validation.json

# The same bundles through two consumers: the OASIS reference TAXII 2.1 server on
# localhost, and MISP's STIX 2.1 importer (no data, no network beyond localhost).
stix-ingest: stix-check
	$(PY) scripts/stix_ingest.py --out $(RESULTS)/stix_ingest.json

# Recompute every sprint-6 number of the paper from results/ and compare with the
# text of article.tex. Needs no drive: it reads only the committed result files.
audit:
	$(PY) scripts/audit_paper.py

