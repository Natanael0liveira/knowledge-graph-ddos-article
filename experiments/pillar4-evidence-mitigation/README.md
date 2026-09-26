# Pillar 4 — Evidence chain and scoped mitigation

When `coordinatedHTTPFlood` fires on a cluster S, this module couples
**detection → symbolic evidence → mitigation with a derived scope**.

## What `scripts/evidence_mitigation.py` does

1. **Decomposes Ω(S)** per `relatedBy_*` sub-relation: which signals fired, at
   which weight.
2. **Derives the mitigation scope.** Two implementations coexist, deliberately:
   - `derive_scope` — the original heuristic, by the **modal** JA4 of the
     coordinated subset. **Fails against a heterogeneous botnet** (below). Kept so
     the negative result stays reproducible.
   - `derive_scope_enriched` — the correction, by **enrichment** over a benign
     background profile. This is what the paper uses.
3. **Exports the evidence chain** as **JSON-LD** over the ontology vocabulary
   (`kg:CoordinatedHTTPFlood`, `kg:activatedSubRelations`,
   `kg:coordinationWeight`, `kg:derivedMitigationScope`) and as **STIX 2.1**
   (`indicator` + `course-of-action` + a *mitigates* `relationship`). The verdict
   *is* the derivation that satisfied the rule.
4. **Estimates collateral damage** of the scoped filter against a global rate
   limit on the endpoint.

## Demo

```bash
make demo      # toy cluster: 12 stealthy attackers, 400 benign, same endpoint
```

```
Omega(S) = 105.6  (12 sessions)
  relatedByTLSFingerprint        pairs=66  x1.0 = 66.0
  relatedByEndpointConvergence   pairs=66  x0.6 = 39.6   (NetworkProximity inactive: /24s dispersed)
DERIVED SCOPE: {tlsJa4: t13d_botnetX, endpoint: 10.0.0.1:443}
COLLATERAL (400 BENIGN):
  scoped (derived):           0   (0.00%)
  global endpoint rate limit: 198 (49.50%)
```

Outputs land in `--out-dir` as `evidence.jsonld` and `mitigation.stix.json`.

**The STIX bundle is valid STIX 2.1** (`make stix-check` in `sprint-6-noms`, OASIS
`stix2-validator`, strict mode included). It holds an `indicator` whose pattern is
the derived scope, a `course-of-action`, the relationship `course-of-action
mitigates indicator`, the producing `identity`, and one `extension-definition` of
type property-extension. STIX has no JA4 property, so the fingerprint travels in
that extension (`network-traffic:extensions.'extension-definition--…'.ja4 IN (…)`),
and so do Ω(S), the cluster size and the decomposition per sub-relation.
Identifiers are UUIDv4-formatted and deterministic in the cluster and the scope,
so re-exporting a verdict does not duplicate it downstream. The earlier exporter
failed the validator with 13 errors per bundle: identifiers not of the form
`type--UUID`, no `created`, `modified` or `valid_from`, and a fingerprint set
rendered as a Python list inside the pattern.

> **The 0.00% in this demo is the monolithic scenario.** It does not hold against
> a heterogeneous botnet under the modal heuristic. See below.

## The error Sprint 6 found, and the correction

**Choosing by modal frequency is wrong by construction.** Frequency rewards what
is common, and on a service under attack **what is common is legitimate traffic**.
With the botnet fragmented across five or more TLS stacks, each attacker stack is
smaller than the head of the benign distribution, the cluster's modal value
becomes a **legitimate** fingerprint, and the derived scope becomes a filter that
blocks users:

| Scenario (α = 1.5, realistic benign) | Modal: attack / collateral | Enrichment |
|---|---|---|
| Monolithic (M = 1) | 84.0% / 0.00% | 84.0% / 0.00% |
| M = 5 | **0.0% / 39.0%** | **90.0% / 0.00%** |
| M = 25 | **0.0% / 39.0%** | **90.3% / 0.00%** |
| M = 100 | **0.0% / 39.0%** | **38.6% / 0.00%** (89.6% with a 30k-session profile) |
| M = 25, adversarial | 3.6% / 39.0% | 30.4% / 3.78% |

This is not graceful degradation: the mechanism selects the **wrong target** and
produces a filter that only hurts users.

**The correction** (`derive_scope_enriched` plus `matches_scope_multi`) ranks
candidates by enrichment over a background profile of normal traffic, taken from
an attack-free window with no labels, and returns a **set** of fingerprints, which
is what covers a fragmented botnet. Operating point: `min_enrichment=3.0` and
`significance=0.01`, a binomial over-representation test that replaces the fixed
`min_support` floor of earlier revisions (see [`docs/concepts.md`](../../docs/concepts.md)).
Without `significance` the function keeps the old floor, so earlier results stay
reproducible.

Two boundary conditions, both measured:

- **An adversary adopting the benign head.** Nothing is enriched and the rule
  refuses to block the popular fingerprints. The scoped advantage is lost, but it
  is lost **safely**: the harmful filter is never emitted.
- **Background profile quality and size.** Moderate drift is tolerable (no
  collateral with a profile from another distribution), but a flat or missing
  profile is not (77.6%). Profile quality governs precision; profile size governs
  the smallest stack the test can certify (38.6% at M = 100 with 1,000 profile
  sessions, 89.6% with 30,000). Keeping the profile fresh and ample is a
  deployment requirement.

Experiments and data in [`../sprint-6-noms/`](../sprint-6-noms/).

> **Toy demo versus the paper's canonical number.** This demo gives 49.5% for the
> global control, because only about half the 400 benign sessions fall inside the
> cluster window. The **canonical** number comes from `collateral_eval.py` in the
> realistic same-service scenario (n = 30, K = 1000), where legitimate users do
> access the attacked service: there a global rate limit takes down **100%** of
> them and the scoped filter **0%**, with the JA4 in scope in 30 of 30 runs. That
> 0% against 100% is what the paper reports.

## Wiring to real data

The input cluster is a slice of the sessions that `coordinatedHTTPFlood` (G4)
detected. `compute_coordination.py` marks the winning `det_cluster`; pass those
sessions plus a BENIGN set as `--cluster` and `--benign`.

## Caveats

- Demonstrated on a toy cluster; running over a real detected cluster needs the
  drive. The logic is validated, the real numbers come after.
- The scope's /24 key is written `srcNet24` in the JSON-LD chains, while the
  ontology's property is `srcPrefix`. The key is kept so the committed chains and
  the identifiers of their STIX bundles stay unchanged.
- Only the three sub-relations with session-level data enter the decomposition,
  the same scope as the ablation: TLS/JA4, endpoint, /24.
