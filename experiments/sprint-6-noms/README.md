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
| `scripts/run_canonical_baselines.py` | Table II's baseline rows had **no result file** behind them | Yes |
| `scripts/rule_detection.py` | The rule Ω(S) ≥ τ had **never been evaluated on its own**, nor against flash crowds | Yes |

```bash
make latency      # runs anywhere
make all-hd       # ml + window, needs the drive mounted
make drift        # profile drift, plus the M = 100 run with a pooled profile
make baselines    # Table II baseline rows
make rule         # the rule as a window-level detector (Appendix E)
```

`realistic`, `symbolic`, `drift` and `rule` pass `--significance $(SIG)` to the
scope derivation (`SIG ?= 0.01`, section 7). `make SIG= <target>` reruns a target
with the fixed floor σ = 0.002 of earlier revisions.

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

## 5. Table II baselines

`run_canonical_baselines.py` runs the academic baselines of
`sprint-3/scripts/baselines.py` on the cached canonical scenarios (α = 1.5,
M = 25, 30 seeds, K ∈ {50, 1000}) with the same features and split as
configuration (b): `test_size = 0.3`, `random_state = 42`, stratified. Output:
`results/canonical_baselines.json` and `canonical_baselines_runs.csv`.

| Baseline | K = 50 | K = 1000 |
|---|---|---|
| `fernandes2019` | 0.518 | 0.509 |
| `bharathi2012` (k-means only, earlier adaptation) | 0.520 | 0.509 |
| `bharathi2012_pca` (published structure, in the paper) | 0.499 | 0.495 |
| `kemp2018` | 0.499 | 0.503 |

The earlier rows of Table II are reproduced to three decimals, so they were
right and only lacked a committed source. Bharathi et al. describe PCA over a
behavior matrix, k-means on the retained components and a per-cluster threshold.
Their threshold (eq. 8) is under-specified; `bharathi2012_pca` scores a session
by its distance to the nearest centroid over that cluster's 95th-percentile
training distance.

## 6. The rule as a detector

`rule_detection.py` evaluates Ω(S) ≥ τ per fixed window of W = 300 s, per
endpoint, instead of per gap-chained cluster:

- τ is a percentile of Ω over attack-free scenarios with their own seeds
  (calibration 5001–5030), so no label enters the threshold;
- false alarms are measured on held-out attack-free scenarios (6001–6030);
- detection is measured on the canonical scenarios, over windows holding at
  least `k_min` = 5 attacker sessions;
- a flash crowd retimes N ∈ {25, 50, 100} legitimate sessions from a donor
  scenario (7001–7030) into one window of the attacked service.

Three rules are compared: `omega` (conditions i, iv and v), `pipeline` (Ω
followed by a non-empty enrichment scope) and `enrichment` (the scope alone).
Attack-free scenarios are generated on first use into `$RULEWORK`.

Options, each variant written under its own `--tag`:
`--steady-minutes` spreads benign sessions uniformly over that many minutes,
`--min-count` adds an absolute floor to σ, `--tau-rate` sets condition (iv), and
`--profile calib` builds the background profile from the 30 calibration runs
instead of one.

### Findings

**The generator packs benign traffic into one burst.** A median 87.6% of the
benign sessions of a scenario fall in one 5-minute window. The paper's
gap-chained clusters therefore hold nearly every session, and W never operates.
This is also why the window sweep (section 3) is flat.

**Ω alone reacts to volume.** With benign traffic spread over 60 min, τ at p99
of 360 calibration windows (τ = 4,323) and condition (iv) off
(`_steady60_floor4_rate0_bigprof`):

| Windows | n | Ω ≥ τ | pipeline | enrichment |
|---|---|---|---|---|
| attack, K = 1000 | 90 | 77.8% | 68.9% | 72.2% |
| attack, K = 50 | 35 | 85.7% | 80.0% | 82.9% |
| clean | 360 | 0.6% | 0.3% | 13.9% |
| flash crowd, N = 25 | 30 | 80.0% | 13.3% | 20.0% |
| flash crowd, N = 50 | 30 | 100% | 16.7% | 16.7% |
| flash crowd, N = 100 | 30 | 100% | 13.3% | 13.3% |

**Condition (iv) never holds in steady traffic.** With τ_rate = 1 req/s no
window of low-rate sessions is eligible (`_steady60`), so τ is undefined and
the rule never fires outside a burst.

**The enrichment scope is unsafe at window scale.** With the paper's operating
point (ρ = 3, σ = 0.002 as a fraction, default run), a scope is named in 93% of
clean windows with at least 5 sessions, blocking a median 19.9% of their
legitimate sessions (max 80%), and in every flash crowd (median 14–24%). The
reason is that σ = 0.002 of a 5-minute window is less than one session. An
absolute floor of 4 sessions (`--min-count 4`) cuts this to 7.8% of clean
windows and 7–20% of flash crowds, but the scope then covers a median 20–53% of
the attackers, since 25 stacks leave few sessions per stack in one window. A
background profile from 30 runs instead of one does not help, so the cause is
the fixed ratio, which ignores window size.

The paper's report of no collateral holds at the cluster sizes of Table III
(about 1,000–2,000 sessions), where σ = 0.002 already means several sessions.
Section 7 replaces the fixed floor by a significance test.

## 7. The binomial enrichment test

The fixed floor σ ignores the number of sessions it is applied to. The scope now
admits a fingerprint f seen c times among n sessions when it is enriched,
c/n ≥ ρ·b(f), and improbable under the background, P[X ≥ c] < α/|F| for
X ~ Bin(n, b(f)), with ρ = 3 and α = 0.01 (`derive_scope_enriched(...,
significance=0.01)`). [`docs/concepts.md`](../../docs/concepts.md) has the
derivation and a worked example.

**The Bonferroni family is every fingerprint of the profile or the window.** The
first prototype divided α by the fingerprints present in the window, about 27.
Which fingerprints appear is itself random, so that undercounts the family: the
scope then named a filter in 1.9–2.2% of the *calibration* windows, above the 1%
level, with p-values of 10⁻⁴ to 10⁻⁵ on benign tail fingerprints. With the family
at about 900, those picks fall below the cut.

**Per window** (`make rule`, 60-min benign spread, rate condition off, pooled
30,000-session profile, τ = 4,323):

| Windows | n | Ω ≥ τ | Ω and scope: σ = 0.002 | Ω and scope: binomial | Coverage (binomial) |
|---|---|---|---|---|---|
| attack, K = 1000 | 90 | 77.8% | 77.8% | 77.8% | median 79.8%, no collateral |
| attack, K = 50 | 35 | 85.7% | 85.7% | 85.7% | median 75.3%, no collateral |
| clean | 360 | 0.6% | 0.6% | 0.0% | |
| flash crowd, N = 25 | 30 | 80.0% | 80.0% | 0.0% | |
| flash crowd, N = 50 | 30 | 100% | 100% | 0.0% | |
| flash crowd, N = 100 | 30 | 100% | 100% | 0.0% | |

With the fixed floor the scope alone names a filter in every clean window and
every flash crowd (median collateral 17.8% and 12–16%), and in attack windows it
blocks every attacker at a median 12% collateral. With the binomial test it names
one clean window in 360 and no flash crowd. Source:
`results/rule_detection_steady60_rate0_bigprof{,_binom}.json`.

**Per cluster** (Table III, Fig. 3, the drift paragraph), with the paper's
1,000-session profile, the test reproduces every row except two:

| Configuration | σ = 0.002 | binomial |
|---|---|---|
| M = 1, 5, 25, and the three adversarial rows | as published | identical |
| α = 2.0, M = 25 | 90.3%, collateral 0.05% | 90.3%, no collateral |
| **M = 100** | **85.0%** | **38.6%**, no collateral |
| drift: α = 2.0 profile | 0.45% collateral | no collateral |
| drift: flat profile | 81.2% collateral | 77.6% collateral |

At M = 100 a stack holds about ten of some 2,000 cluster sessions, and a
1,000-session profile cannot tell it from its own tail. A profile pooled over the
30 attack-free calibration runs restores 89.6% with no collateral
(`results/profile_drift_m100.json`). The Random Forest columns of Table III do not
change.

**Fig. 3 now has a source.** It used to read `results/realistic_consolidated.csv`,
which no script wrote: its enrichment bars came from a σ = 0.002 run, while
`realistic_probe.py` called the scope with its default σ = 0.01, which at
M = 100 names no fingerprint and falls back to the whole endpoint (93% collateral).
`realistic_probe.py` now passes σ = 0.002 or the test explicitly and writes
`results/realistic_{tag}_consolidated.csv`, which `make_figures_en.py` reads. The
orphan file was removed.

