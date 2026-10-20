# Pillar 4: evidence chain and scope derivation

[`scripts/evidence_mitigation.py`](scripts/evidence_mitigation.py) is the library
behind the scope and the evidence chain. It splits Ω(S) by sub-relation, derives
the mitigation scope, measures a scope's collateral and exports the chain as
JSON-LD and STIX 2.1. Sprint 6 imports it for Table III, the calibration of the
test level, Listing 1 and the STIX checks. `make demo` runs it on a toy cluster. No
number of the paper is computed here.

## In the paper

- **Section III-C.** The binomial enrichment test is
  `derive_scope_enriched(cluster, profile, min_enrichment=3.0, significance=λ)`. It
  selects a fingerprint f when c(f)/n ≥ ρ·b(f) and P[X ≥ c(f)] < λ/|F| for
  X ~ Bin(n, b(f)). b(f) includes the 1/N prior, and |F| counts the fingerprints of
  profile and alarm. `calibrate_level` sets λ_e, the largest level up to 0.01 at
  which the scope selects a filter in at most 1% of attack-free clusters.
- **Table III.** The "Modal" column is `derive_scope` (sprint-6 `unseen_synth.py`,
  `coverage=0.5`). The binomial test is `derive_scope_enriched` with
  `matches_scope_multi` (sprint-6 `symbolic_detector.py`).
- **Section III-E, Appendices D and F.** The chain's JSON-LD (Listing 1, written by
  sprint-6 [`example_chain.py`](../sprint-6-noms/scripts/example_chain.py)) and its
  STIX 2.1 bundle (an indicator and a course-of-action linked by *mitigates*).
  Sprint-6 `make stix-check` runs the OASIS validator in strict mode, and
  `make stix-ingest` sends the bundles through a TAXII 2.1 server and MISP's
  importer, which drops the JA4 extension (Section VI).
- **Sections V-B to V-D.** The production evaluation reimplements the test over
  counts in sprint-6
  [`rule_detection_production.py`](../sprint-6-noms/scripts/rule_detection_production.py),
  with the unseen filter, the union, the z-score and the beta-binomial, and checks
  it against `derive_scope_enriched`.

## Functions

| Function | What it does | Used in sprint 6 by |
|---|---|---|
| `decompose_omega` | Ω(S) split into TLS, endpoint and /24 pairs; `unit="origin"` counts distinct sources | `example_chain.py`, `compile_counts.py` |
| `derive_scope` | Modal scope: the cluster's most common JA4, plus the endpoint and a /24 that hold at least `coverage` of the sessions sharing that JA4 | `unseen_synth.py`, `realistic_probe.py`, `collateral_purity_sweep.py` |
| `derive_scope_enriched` | The binomial enrichment test; returns a set of fingerprints, plus the endpoint and a /24 that hold at least half the cluster | `symbolic_detector.py`, `unseen_synth.py`, `realistic_probe.py`, `profile_drift.py`, `rule_detection.py`, `example_chain.py`, and the self-check of `rule_detection_production.py` |
| `matches_scope`, `matches_scope_multi` | The sessions a scope blocks, for one JA4 or for a set | `symbolic_detector.py`, `unseen_synth.py`, `realistic_probe.py`, `profile_drift.py`, `rule_detection.py`, `collateral_purity_sweep.py` |
| `min_adjusted_p`, `calibrate_level` | The smallest Bonferroni-adjusted p among enriched fingerprints, and the level calibrated from it on attack-free clusters | `level_calibration.py`, `rule_detection.py` (through `calibrate_level`) |
| `evidence_chain_jsonld`, `stix_bundle` | The chain as JSON-LD, and as a STIX 2.1 bundle | `example_chain.py`, `stix_check.py` |
| `collateral` | Benign sessions a scope hits, next to a global rate limit on its endpoint | none (this directory's demo and `qualitative_evidence.py`) |

Each STIX bundle holds an identity, a property-extension definition, an indicator
whose pattern is the scope, a course-of-action and the relationship
course-of-action *mitigates* indicator. STIX has no JA4 property, so the
fingerprints travel in the extension
(`network-traffic:extensions.'extension-definition--…'.ja4 IN (…)`), together with
Ω(S), the cluster size and the split by sub-relation. The identifiers are UUIDv4
derived from the cluster and the scope, so a re-exported chain does not duplicate
downstream.

## Inputs

None for the demo, which builds its toy cluster in the script. The weights come
from the ontology through [`../common/kg_ontology.py`](../common/kg_ontology.py).
The command line and the scripts below read sessions in Sprint 1's schema
(`src_ip_first`, `dst_ip_first`, `dst_port_first`, `ja4`, `label_first`).

## Run

| Target | What it does | Writes |
|---|---|---|
| `help` | Lists the targets | |
| `demo` | `decompose_omega`, the modal `derive_scope` and `collateral` on a toy cluster: 12 attackers that share one JA4 and one endpoint, and 400 benign sessions as the collateral reference | overwrites the committed `results/evidence.jsonld` and `results/mitigation.stix.json` |

Without a target (`../data` is the symlink to `DATA_ROOT`):

```bash
# One detected cluster and a benign set (modal scope)
../.venv/bin/python scripts/evidence_mitigation.py --cluster CLUSTER.parquet \
  --benign BENIGN.parquet --out-dir OUT

# Chains of the largest attack-dominated cluster of each attack on the captures;
# overwrites results/chains/
../.venv/bin/python scripts/qualitative_evidence.py --out-dir results/chains \
  --sessions cicids2017=../data/processed/sessions/cicids2017.parquet \
             cic-iot-2023=../data/processed/sessions/cic-iot-2023.parquet

# Collateral of the modal scope against a global rate limit, over scenario files;
# prints only
../.venv/bin/python scripts/collateral_eval.py --scenarios DIR --coverage 0.5 --max-files 30
```

## Outputs

| File | Producer | In the paper |
|---|---|---|
| `results/evidence.jsonld`, `results/mitigation.stix.json` | `make demo`; sprint-6 `make stix-check` rewrites the bundle from the chain | App. F's STIX checks include it |
| `results/chains/chain_cicids2017_DoS-Other.*`, `results/chains/chain_cicids2017_GoldenEye.*` | `qualitative_evidence.py`; `make stix-check` rewrites the bundles | App. F's STIX checks include them |
| `results/chains/completeness_table.csv` | `qualitative_evidence.py` | No |

## Results

`make demo`, translated and abridged (the script prints in Portuguese):

```
Ω(S) = 105.6  (12 sessions)
Split by sub-relation:
  relatedByTLSFingerprint          pairs=66  ×1.0 = 66.0
  relatedByEndpointConvergence     pairs=66  ×0.6 = 39.6
DERIVED MITIGATION SCOPE: {"tlsJa4": "t13d_botnetX", "endpoint": "10.0.0.1:443"}
COLLATERAL (400 BENIGN sessions):
  scoped mitigation (derived scope):  0 (0.00%)
  global rate limit on the endpoint:  198 (49.50%)
```

No two attackers share a /24, so network proximity adds nothing. The global limit
hits about half the benign sessions because the toy draws their ports from 443,
443, 80 and 8080. The toy has no time window. The chain is in
[`results/evidence.jsonld`](results/evidence.jsonld).

On the laboratory captures the attack clusters share no JA4, so no fingerprint
enters a scope. Each chain's scope is the attacked endpoint plus the attackers'
/24, from endpoint convergence and network proximity
([`results/chains/completeness_table.csv`](results/chains/completeness_table.csv)).

On generated traffic (Table III), from five stacks on the modal fingerprint belongs
to legitimate clients: it covers 0.0% of attackers and blocks 39.0% of legitimate
traffic. The binomial test covers 90.0–90.3% of attackers on 5 and 25 stacks, with
no observed collateral. [`../FINDINGS.md`](../FINDINGS.md) has the rest.

## Caveats

- `make demo` runs the modal `derive_scope` on a single-stack toy. It shows the
  chain's format, and the enrichment test does not run in it.
- When attackers adopt common legitimate fingerprints, little is enriched. On
  generated traffic the test then covers 30.4% at 3.78% collateral (Table III), so
  an alarm mainly invokes the fallback (Section VI).
- The profile must exclude attack episodes and stay current. A flat or missing
  profile raises collateral to 77.6% (Section V-A). Profiles should be rebuilt from
  windows where the scope selects nothing, and persistent new fingerprints admitted
  only after operator review (Section VI).
- Without `significance`, `derive_scope_enriched` applies a fixed support floor
  (`min_support`) in place of the binomial test, as earlier revisions did. Only
  three sub-relations enter `decompose_omega`: TLS, endpoint and /24.
- `collateral_eval.py` and `qualitative_evidence.py` pick the attack cluster with
  labels; sprint 6 picks the cluster of largest Ω without labels
  (`--label-free-cluster`). The scope's /24 condition is `kg:srcNet24`, a
  `Mitigation` property; the session's prefix is `kg:srcPrefix`.
