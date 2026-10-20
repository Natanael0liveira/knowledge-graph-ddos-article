# Methodology

How the evaluation was built and corrected: the decisions behind each stage, the scenario cache
each generated result comes from, what was fixed before which data, and the corrections that
changed a conclusion. Other homes:
- the experimental design, and what each traffic source can establish:
  [`../docs/evaluation.md`](../docs/evaluation.md);
- the method (the trigger, the binomial test, the calibration floor, the enrichment limit, the
  beta-binomial background, cross-fitting): [`../docs/concepts.md`](../docs/concepts.md), sections 4–8;
- the metrics and their tests: [`../docs/metrics.md`](../docs/metrics.md);
- the results: [`FINDINGS.md`](FINDINGS.md).

Paper pointers refer to [`papers/http-session-noms/article.tex`](../papers/http-session-noms/article.tex).
Result files without a directory are in `sprint-6-noms/results/`.

## Principles

**Limits travel with the results.** Every result that depends on a limit of its source states
it: the stealth regime of generated traffic, the injected botnets of production traffic, the post
hoc status of configurations built after the held-out day was read, and the uncontrolled KLAGE
comparison. [`../docs/evaluation.md`](../docs/evaluation.md#8-what-each-evaluation-establishes)
lists what each source can and cannot establish.

**What regenerates from what (App. F).** Seeds are fixed, so every generated-traffic table and
figure regenerates from its make target, given the scenario caches. Production tables regenerate
from per-window results kept with the operator's data (`make production-tables waf-labels`).
`make audit` recomputes about 250 printed numbers from the anonymized summaries in the
repository. Sprint 1 also needs a manual download (CICIDS2017 requires a UNB registration) and a
manual review of a sample of ten clusters.

**Why the generated campaigns are stealthy.** Against an attack with a flow signature,
per-session detection already suffices (App. C). The cross-session question is tested only when
each attacker session is drawn from the benign per-session distributions, which is what stealth
mode does (IV-A).

## Scenario caches

Every generated-traffic number comes from one cache on the data drive, and
[`FINDINGS.md`](FINDINGS.md) labels each result with it.

| Cache (Makefile variable) | Configuration | Read by | In the paper |
|---|---|---|---|
| `synth/sprint6_realistic` (`REALWORK`) | The canonical scenario: stealth mode on the attacked service (`sprint-2/configs/scenario_stealth.yaml`) with Zipf α = 1.5 and 25 stacks, unless a run varies them | Sprint 6: `canonical`, `baselines`, `cross-m`, `symbolic`, `unseen-synth`, `realistic`, `drift`, `rule` | Table III, V-A, Apps. C and E |
| `synth/sprint6_rule` (`RULEWORK`) | Attack-free runs: calibration seeds 5001–5030, test seeds 6001–6030, flash-crowd donors 7001–7030 | Sprint 6: `rule`; the clean runs and profiles of `symbolic`, `unseen-synth`, `realistic`, `drift` | App. E; the pooled profile of V-A |
| `synth/sprint4_realistic_work` (`WORK`) | The sprint-4 cache: the same file with the generator's defaults (α = 0, one stack), so a near-uniform pool of 2,000 benign fingerprints and a monolithic botnet | Sprint 4: `run`, `weights`, `weights-cluster`; Sprint 6: `ml`, `window`, `purity` | App. B's weights; the KS check of IV-A |
| `synth/sprint3`, and the robustness sweep's own directory | The same file with the generator's defaults; Sprint 3 uses one seed, and the sweep varies the share of attackers on the botnet's fingerprint | Sprint 3: `scenarios`, `ablation`; `sprint-4/scripts/robustness_sweep.py` (no target) | not in the paper |
| `synth/sprint4`, `synth/sprint4_strong_work` | Older caches: the first predates the flow features, and the second keeps the target-port artifact (Sprint 6 Makefile comments) | nothing | not in the paper |

The KS distances of IV-A (D = 0.002 for request counts and 0.003 for durations) were computed on
60,000 benign sessions of the sprint-4 cache (`sprint-2/results/ks_validation.json`). They check
only the request-count and duration sampler (IV-A), which α and M do not change
(`sprint-2/scripts/generator.py`).

## Decisions per stage

### Sprint 1: laboratory pipeline

- PCAP → JA4 (tshark) and flows (the Python `cicflowmeter`) → sessions, optionally loaded into
  Apache Jena Fuseki. The graph and its SPARQL gate are legacy: the paper's evaluation runs no
  reasoner (III-E).
- Detection clusters are formed by endpoint and window, never from labels, so the result cannot be
  circular.
- `build_sessions.py` leaves CICIDS2017 sessions unlabeled. `scripts/label_cicids2017.py` labels
  them by attacker pair and time window, and no target runs it.
- `notebooks/validate.ipynb` defines seven checks, three of them named: G1 (at least five distinct
  JA4), G3 (best ROC AUC of a coordination classifier at least 0.85) and G4 (the
  `coordinatedHTTPFlood` query returns at least one cluster). It stores no outputs.
- Large graphs load through the bulk path (`make load-kg-bulk`), since the per-chunk HTTP load
  into Fuseki's emulated JVM hung for about five hours (Sprint 1 Makefile comment).

### Sprint 2: the generator

- Legitimate request counts and durations are sampled from CICIDS2017's benign sessions: all
  322,658 for request counts, and the 40,351 with two or more requests for durations (App. B;
  `sprint-2/distributions/`).
- Stealth mode draws attacker sessions from the same distributions, so only cross-session
  structure distinguishes the campaign (IV-A).
- Legitimate users reach the attacked service on the attackers' port (`benign_same_service`), so
  the target port does not separate sessions.
- Benign fingerprint popularity (Zipf α) is set from a production measurement, and the botnet's
  number of stacks M is swept because no published measurement fixes it; both are explained in
  [`../docs/evaluation.md`](../docs/evaluation.md). The defaults are α = 1.5 and M = 25 (IV-A).
- The A/B/C scenarios of `sprint-2/Makefile` are the original plan. The paper's scenarios are
  generated by Sprint 6 targets, as `scenario_stealth.yaml` with α, M and adversarial overrides.

### Sprints 3 and 4: ablation, baselines and statistics

- Configurations (a)–(d) differ only in their features
  ([`../docs/evaluation.md`](../docs/evaluation.md)). In Sprints 4 and 6, (a) is the nine-feature
  `STRONG_FLOW` set. Sprint 3's `make ablation` uses three flow features and one seed.
- The three academic baselines live in `sprint-3/scripts/baselines.py`; Sprints 4 and 6 reuse
  them ([`../docs/evaluation.md`](../docs/evaluation.md#5-configurations-and-baselines)).
- Paired Wilcoxon tests with a Bonferroni correction compare the configurations, and
  `canonical_realistic.json` also stores Cohen's d. Effect sizes this large reflect the controlled
  separation of generated traffic. They are no forecast of field performance.
- Weight calibration maximizes per-session ROC AUC over the grid {0.3, 0.5, 0.7, 0.9, 1.0}³ (125
  combinations) on 60 scenarios of the sprint-4 cache, 91,500 sessions (App. B;
  `sprint-4/results/weights_session_realistic.json`).

### Sprint 5: comparison with KLAGE

CIC-IoT2023 runs through the same pipeline, and the result is compared with KLAGE's published F₁
for DDoS Slowloris. The comparison is uncontrolled, and KLAGE's released code prevents a controlled
rerun (App. C; results in [`FINDINGS.md`](FINDINGS.md), details in
[`sprint-5/README.md`](sprint-5/README.md)). KLAGE's other dataset, RT-IoT2022, was not run.

### Pillars 2 and 4: rules, scopes and export

- Pillar 2 writes four of the six sub-relations as SWRL rules (shared JA4, reused identity, same
  endpoint, same /24); temporal and payload appear only as a comment. Ω is a SPARQL aggregation
  whose weights come from the ontology's `coordinationWeight`. The evaluation runs no reasoner:
  Sprint 6 compiles the count query from the ontology (`compile_counts.py`, `make compile-check`).
- Pillar 4 ships both scope derivations side by side: the modal fingerprint (`derive_scope`) and
  the binomial test (`derive_scope_enriched`), with the level calibration (`calibrate_level`) and
  the JSON-LD and STIX export. Sprint 6 imports it.
- On generated traffic the profile comes from attack-free runs, so no label enters the decision.
- On production traffic, `rule_detection_production.py` reimplements the test over counts, with
  the unseen filter, their union, the z-score and the beta-binomial. It checks itself against
  `derive_scope_enriched` (0 mismatches in 60 windows; `production_summary.json`).

### Sprint 6: the paper's evaluation

Everything the paper reports beyond the laboratory captures runs in
[`sprint-6-noms/`](sprint-6-noms/). Its README maps each paper element to its result files and make
target, and its lab notebook records every run and review round. The design of both evaluations,
the protocols of the held-out day and the 14-day block, and what was fixed before which data are in
[`../docs/evaluation.md`](../docs/evaluation.md) (sections 2 and 4–7).

The test days are 2026-09-20 to 09-24, calibrated from 2026-09-17. The held-out day is 2026-09-25,
and the block runs from 2026-09-26 to 10-09. File and target names call the held-out day the fresh
day, and the block `block2`. Every metric both protocols name is committed whatever its value:
`production_tables.json` and `fresh_day_metrics_location.md` for the held-out day,
`block_report.json` for the block.

## Validity hardening and corrections

Each row changed a number or a conclusion. The Sprint 6 README's lab notebook holds the full
history.

| Correction | What changed | Pointer |
|---|---|---|
| A strong per-session baseline | An early cross-session advantage on the captures came from a three-feature baseline (AUC 0.52–0.72), which nine flow features remove. The baseline kept its nine features, and the generator gained the same flow features, sampled from benign traffic in stealth mode; on generated traffic (a) stays at chance with them | App. C; `sprint-3/results/real_multiattack.csv`, `real_multiattack_strong.csv` |
| Legitimate users on the attacked service | Benign sessions reach the attacked port (`benign_same_service`), which removed a target-port artifact | `sprint-2/configs/scenario_stealth.yaml` |
| Realistic fingerprints | Sprint 6 added Zipf benign popularity (`benign_ja4_zipf_alpha`), botnets over M stacks (`botnet_ja4_stacks`) and adversarial stacks (`botnet_ja4_adversarial`) | IV-A; Sprint 6 README §4 |
| From the modal fingerprint to the profile | The modal scope blocks legitimate clients and no attackers from five stacks. The binomial test against a profile replaced it, and both ship in Pillar 4 | V-A; `pillar4-evidence-mitigation/scripts/evidence_mitigation.py` |
| From a fixed floor to a test | A fixed support floor σ = 0.002 became the binomial test with ρ = 3 at family-wise level 0.01; `make SIG= <target>` reruns the floor | III-C; Sprint 6 README §7 |
| The Bonferroni family | The divisor counts every fingerprint of the profile and the alarm. A first prototype counted only the window's fingerprints and exceeded the 1% level on calibration windows | III-C; Sprint 6 README §7 |
| A label-free cluster | Per-cluster experiments take the cluster of largest Ω, chosen with no label; `make CLUSTER= <target>` restores the attack-share choice | Sprint 6 Makefile |
| Counting origins | Counted in connections, the scope fires on more than twice as many clean windows, since one client opens many; the scope now counts distinct origins (numbers in FINDINGS), and `make METHOD= <target>` reruns sessions at the nominal level | App. E; `production_summary.json` |
| A calibrated level | Fleets break the binomial model, so λ_e is calibrated per endpoint to the 1% budget | III-C |
| The distinct-origin gate | It fires with Ω in 136 of the 181 clean windows where either fires, and halves the base rule's false alarms with no loss of detection | App. E; `production_summary.json` |
| Baselines with a committed source | The academic baselines were rerun on the canonical cache; the Bharathi baseline follows its published PCA → k-means → threshold structure | App. C; `canonical_baselines.json` |
| Disjoint seeds for cross-M tests | Scenarios that share a seed share their benign sessions, so a same-seed split scores (a) at 0.88–0.94 by memorization | App. C; `cross_m_generalization.json` |
| Cache labels | App. B's weights and the KS check ran on the sprint-4 cache; App. B says so for the weights | App. B; `sprint-2/results/ks_validation.json` |
| A dropped cross-fitting design | A first design, calibrated only on the last calibration day, was dropped after its results were seen, because one day misses the rare fleet events that set the level | V-D |
