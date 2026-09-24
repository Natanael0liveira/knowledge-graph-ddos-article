# Sprint 6 — Additions for the NOMS submission

Experiments closing gaps a NOMS reviewer would find unaided. None replaces an
existing result; all are additive and Sprints 1–5 stay intact.

| Script | Gap it closes | Needs the drive? |
|---|---|---|
| `scripts/bench_latency.py` | The paper claimed O(\|S_W\|·c) cost and near-linear OWL 2 RL behaviour, but **measured nothing** | No |
| `scripts/run_ml_families.py` | "No per-session detector works" rested on **a single** Random Forest | Yes |
| `scripts/window_sweep.py` | Sensitivity to *W* was declared uncharacterized | Yes |
| `scripts/run_canonical_realistic.py` | The generator had three realism defects, all favourable to us | Yes |
| `scripts/profile_drift.py` | How much background-profile staleness the enrichment test tolerates | No |

```bash
make latency      # runs anywhere
make all-hd       # ml + window, needs the drive mounted
make drift        # profile drift
```

## Which scenario cache is canonical

**`$DATA_ROOT/synth/sprint4_realistic_work`** is the work dir; the other two
mislead:

- `synth/sprint4` predates the flow features; `run_sprint4.py` fails on it with
  `KeyError: ['fwd_bytes_sum', ...]`.
- `synth/sprint4_strong_work` still carries the **port artifact**: configuration
  (b) reaches 0.888 instead of collapsing to chance.

> **The paper's numbers come from `run_canonical_realistic.py` →
> `results/canonical_realistic.json`** (α = 1.5, 25 TLS stacks), not from the
> earlier reproduction on `sprint4_realistic_work`. The earlier run gives (d) at
> 0.968 / 0.976 with Cohen's *d* of +12.2 and +19.6; the canonical run gives
> 0.927 / 0.982 with *d* of +13.5 and +22.4 at p_bonf = 7.5 × 10⁻⁹. Use the
> canonical artifact when checking the paper.

## 1. Latency

Measures the **two layers separately**, because they run at different rates and
have different complexity, and each layer **in two ways**:

- **Layer 1, admission (per request, hot path).** Admitting a new session into a
  window of |S_W| sessions. *Peers enumerated*: instantiate `relatedBy_*` edges
  through the inverted indexes (JA4, endpoint, /24 buckets), O(1) per candidate
  pair. *Class counters*: for the equality-based sub-relations, increment one
  counter per sub-relation, O(1) per session.
- **Layer 2, symbolic evaluation (per window, auditable path).** *Pair edges*:
  materialize every pair in RDF via SPARQL CONSTRUCT, then aggregate Ω(S).
  *Class aggregation*: materialize class membership and compute Ω(S) from class
  sizes, `Σ C(n, 2)`, with one SPARQL query. Every run checks that both give the
  same Ω(S) for every endpoint.

No dataset needed: latency depends on |S_W| and on the window's coordination
structure, not on the traffic being real. The session mix is parameterized
(`--coord-frac`, `--ja4-pool`, `--endpoints`) and recorded with the timings.

The sweep has a `--pair-cap`: above it the pair-edge path is skipped rather than
exhausting memory.

### Results (3 repeats, one core, AC power, Low Power Mode off)

| \|S_W\| | admission, peers | edges/adm | ns/pair | admission, classes | pair edges | RDF edges | µs/edge | class aggregation |
|---|---|---|---|---|---|---|---|---|
| 100 | 2.3 µs | 148 | 15.3 | 0.42 µs | 0.84 s | 2,703 | 309 | 0.07 s |
| 250 | 3.8 µs | 239 | 15.9 | 0.38 µs | 3.67 s | 17,221 | 213 | 0.09 s |
| 500 | 6.7 µs | 396 | 17.0 | 0.38 µs | 12.89 s | 65,115 | 198 | 0.16 s |
| 1,000 | 12.0 µs | 741 | 16.2 | 0.37 µs | 52.78 s | 265,328 | 199 | 0.33 s |
| 2,500 | 31.0 µs | 1,660 | 18.7 | 0.38 µs | 357.76 s | 1,641,169 | 218 | 0.81 s |
| 5,000 | 64.2 µs | 3,373 | 19.0 | 0.33 µs | not run | |  | 1.38 s |
| 10,000 | 126.9 µs | 6,495 | 19.5 | 0.37 µs | not run | |  | 2.86 s |
| 25,000 | 293.9 µs | 16,321 | 18.0 | 0.33 µs | not run | |  | 6.77 s |
| 50,000 | 608.8 µs | 32,156 | 18.9 | 0.33 µs | not run | |  | 13.22 s |
| 100,000 | 1364.6 µs | 65,020 | 21.0 | 0.38 µs | not run | |  | 26.37 s |

Both paths give the same Ω(S), to within 7e-12.

**Class counting removes the quadratic cost.** Admission is flat at 0.33–0.42 µs
per session from 100 to 100,000 sessions, and class aggregation is linear, 26.4 s
at 100,000. The pair path stays linear in its own unit of work (15–21 ns per
candidate pair, about 200 µs per RDF edge), but its edge count grows with the
square of |S_W|: 52.8 s at 1,000 and 358 s at 2,500.

An earlier version of this README said the quadratic term belonged to neither the
implementation nor the backend. For the equality-based sub-relations that was
wrong: they are equivalence relations, so pair counts follow from class sizes.
The quadratic growth stays in the value of Ω(S), which counts pairs, and in the
pair edges of the non-transitive relations (near-variant JA4, temporal, payload),
which the indexes restrict.

> **Measure on AC power.** A run on battery with macOS Low Power Mode on came out
> about 1.8× slower across every size. The published numbers above are from a
> plugged-in run; the pre-change results are kept in git history.

**Backend caveat.** The symbolic layer is measured on `rdflib`, the in-memory
reference implementation. The production backend declared in the paper is Apache
Jena Fuseki with TDB2. Layer-2 numbers are therefore an upper bound of the
reference implementation, and are reported as such.

## 2. ML families

Runs the same ablation over the same strong feature set and the **same split**
across four families: `rf`, `hgb` (HistGradientBoosting), `mlp` and `logreg`. If
all sit at chance in configuration (a), the claim stops being "the Random Forest
failed" and becomes "no hypothesis class separates these sessions".

`xgboost` is installed but its native library does not load here (missing
`libomp`); sklearn's `HistGradientBoostingClassifier` covers the same algorithm
family without a new dependency.

> **`ml_families.json` is on the superseded scenario and is not the source of the
> paper's table.** It ran before the realism correction, on the Sprint 4 cache
> (flat benign pool, α = 0, monolithic botnet). Configuration (d) at K = 1000:
>
> | Family | Superseded | Canonical |
> |---|---|---|
> | `rf` | 0.976 | 0.982 |
> | `hgb` | 0.979 | 0.990 |
> | `mlp` | 0.956 | **0.803** |
> | `logreg` | 0.961 | **0.799** |
>
> The collapse of `mlp` and `logreg` in the canonical scenario **is a finding, not
> a bug**: fragmenting the botnet across 25 stacks makes cross-session evidence
> non-monotonic in the label, and monotonic-response models cannot carve out the
> middle band. It is what the paper discusses, and it argues for the symbolic
> path. With a monolithic botnet the effect simply does not exist.

Configuration (a) sits at chance for all four families in both scenarios, which
is what the central thesis needed: the collapse is a property of the
*representation*, not of the learner.

## 3. Window sweep

*W* enters only through `assign_detection_clusters`, so sweeping it means
recomputing the cross-session features over the **same** cached scenarios. Both
sides are reported: effect on detection and cost in cluster occupancy.

| W (s) | clusters | mean \|S\| | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|---|
| 60 | 16 | 132 | 0.505 | 0.508 | 0.664 | 0.976 |
| 120 | 11 | 207 | 0.505 | 0.508 | 0.663 | 0.977 |
| 300 | 6 | 364 | 0.505 | 0.508 | 0.664 | 0.977 |
| 600 | 4 | 557 | 0.505 | 0.508 | 0.664 | 0.978 |
| 1800 | 3 | 867 | 0.505 | 0.508 | 0.664 | 0.978 |

**Detection is insensitive to W over a 30× range** while mean cluster occupancy
grows 6.6×. The reason: the discriminative
feature is a *fraction* (the share of the cluster carrying one JA4), invariant to
cluster scale. Cluster size alone carries little, which is why (c) stays at 0.664
throughout.

Operational rule: **keep W as small as the traffic permits.** A larger window buys
no detection and adds state, linearly with class counting (quadratically with
pair edges, Section 1).

Two bounds: the scenarios target a single endpoint, so W is the only clustering
knob and a multi-endpoint deployment may behave differently; and W must still be
large enough for a cluster to form, which at W = 60 s already means ~132 sessions.

## 4. Realism corrections to the generator

Three defects, all favourable to us, all corrected and backward-compatible
(defaults preserve the old behaviour):

1. **Benign JA4 was UNIFORM** over a synthetic pool (792 distinct in 1,000
   sessions, modal 0.4%). The distribution calibrated over ~322k benign sessions
   is the opposite: 39 distinct, top-1 52.7%, top-10 98.4%. Fixed by
   `benign_ja4_zipf_alpha`.
2. **Monolithic botnet**, one JA4 for 88% of attackers. Fixed by
   `botnet_ja4_stacks`.
3. **Attacker namespace disjoint from benign**, making collision impossible by
   construction. Fixed by `botnet_ja4_adversarial`, where the botnet adopts the
   most common benign fingerprints, which is what browser-impersonation tooling
   does.

> Watch out: `--param x=false` arrives as the **string** `"false"`, and
> `bool("false")` is `True` in Python. Fixed for both boolean keys.
