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
| M = 100 | **0.0% / 39.0%** | **85.0% / 0.00%** |
| M = 25, adversarial | 3.6% / 39.0% | 30.4% / 3.78% |

This is not graceful degradation: the mechanism selects the **wrong target** and
produces a filter that only hurts users.

**The correction** (`derive_scope_enriched` plus `matches_scope_multi`) ranks
candidates by enrichment over a background profile of normal traffic, taken from
an attack-free window with no labels, and returns a **set** of fingerprints, which
is what covers a fragmented botnet. Operating point: `min_enrichment=3.0`,
`min_support=0.01`, dropping to 0.002 when M is high, since the floor must sit
below 1/M.

Two boundary conditions, both measured:

- **An adversary adopting the benign head.** Nothing is enriched and the rule
  refuses to block the popular fingerprints. The scoped advantage is lost, but it
  is lost **safely**: the harmful filter is never emitted.
- **Background profile quality.** Moderate drift is tolerable (0.45% collateral
  with a profile from another distribution), but a flat or missing profile is not
  (81–84%). Profile quality governs precision, never coverage. Keeping it fresh is
  a deployment requirement.

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
- The **STIX 2.1 output is representative**, with the correct structure
  (bundle / indicator / course-of-action / relationship, `pattern_type: stix`),
  but is not checked against a formal STIX validator. JA4 uses a custom
  `x-tls:ja4` extension.
- Only the three sub-relations with session-level data enter the decomposition,
  the same scope as the ablation: TLS/JA4, endpoint, /24.
