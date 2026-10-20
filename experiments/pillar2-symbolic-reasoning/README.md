# Pillar 2: sub-relations as SWRL rules and the Ω aggregation in SPARQL

This directory writes the sub-relations of Appendix A as Horn rules and computes
the coordination mass Ω(S) = Σᵢ wᵢ·|Eᵢ(S)| with a SPARQL aggregation, on an
eight-session toy graph. The evaluation runs no reasoner (Section III-E): the
counts it reads come from a query compiled from the ontology (sprint-6
`compile_counts.py`, `make compile-check`). No number of the paper comes from here.

## In the paper

- **Appendix A.** [`rules/relatedBy.swrl`](rules/relatedBy.swrl) writes four of the
  six sub-relations as SWRL rules: TLS fingerprint, reused identity, endpoint
  convergence and network proximity. Temporal pattern and payload signature need
  precomputed distances and appear only as a comment.
- **Appendix D.** The cost model's pair-edge path runs the same rules as SPARQL
  CONSTRUCT, and its class-count path one SPARQL aggregation (sprint-6
  [`bench_latency.py`](../sprint-6-noms/scripts/bench_latency.py)).
- **Not in the paper:** the demo.

## Inputs

Only the venv (`../.venv`). [`scripts/reason.py`](scripts/reason.py) builds the toy
graph itself and reads every weight from `coordinationWeight` in
[`../../ontology/ddos_ontology.owl`](../../ontology/ddos_ontology.owl). `--data FILE`
reads an RDF graph instead, whose `kg:ApplicationSession` nodes must carry
`kg:tlsJa4`, `kg:targets` and `kg:srcPrefix`.

## Run

| Target | What it does | Writes |
|---|---|---|
| `help` | Lists the targets | |
| `demo` | Builds the toy graph, materializes three sub-relations as SPARQL CONSTRUCT, sums Ω(S) per endpoint and prints each cluster with Ω ≥ τ (τ = 5) | nothing |

On another graph: `../.venv/bin/python scripts/reason.py --data FILE.ttl --tau 5`.

## Outputs

None. `reason.py` prints its verdicts and writes no file, and nothing in this
directory is a result file.

## Results

`make demo`, translated and abridged (the script prints in Portuguese):

```
Ontology weights: TLSFingerprint 1.0, ReusedIdentity 1.0, TemporalPattern 0.9,
  PayloadSignature 0.6, EndpointConvergence 0.6, NetworkProximity 0.3
Materialized edges: TLSFingerprint 10, EndpointConvergence 28, NetworkProximity 0
RULE FIRED: coordinatedHTTPFlood @ 10.0.0.1_443
  Ω(S) = 26.8 ≥ τ=5.0   (|S|=8)
  DERIVATION:
    relatedByTLSFingerprint          10 pairs × w=1.0 = 10.0
    relatedByEndpointConvergence     28 pairs × w=0.6 = 16.8
```

Five attackers share one JA4 (10 pairs), all eight sessions share the endpoint
(28 pairs), and no two share a /24. The scopes evaluated as detectors on generated
traffic (Table III) are computed in sprint 6 with the functions of
[pillar 4](../pillar4-evidence-mitigation/). Their numbers are in
[`../FINDINGS.md`](../FINDINGS.md).

## Caveats

- The demo's cluster is every session on one endpoint, with no time window. In the
  paper S holds the sessions to one endpoint in one five-minute window
  (Section III-B). On generated traffic the cluster chains an endpoint's sessions
  while consecutive starts stay within 300 s (Section IV-A).
- The demo counts pairs of sessions, while the paper counts pairs of distinct
  origins (Appendix A). The evaluation computes Ω from class sizes, Σₖ C(nₖ, 2),
  and builds no pair edge.
- rdflib has no SWRL reasoner, so each rule runs as a SPARQL CONSTRUCT that emits
  each unordered pair once. With `relatedTo` symmetric, these are the pairs the
  rule derives. `reason.py` runs three of the four rules, since the toy graph holds
  no identity.
- The sprint-1 graph export does not fit `--data` as it stands: it puts the JA4 on
  the session's `Identity` node and writes no `srcPrefix`.
- τ = 5 is the script's default. The paper's thresholds are percentiles over
  attack-free windows (Section III-B).
