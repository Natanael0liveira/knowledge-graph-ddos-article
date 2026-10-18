# Sprint 6 — Additions for the NOMS submission

Experiments closing gaps a NOMS reviewer would find unaided. None replaces an
existing result; all are additive and Sprints 1–5 stay intact.

> **Table numbers.** Each section below cites the paper's tables and sections as
> they were numbered when it was written. Since round 12 the paper has Table II (the
> configurations evaluated on production), Table III (the scope on generated traffic,
> with the modal fingerprint's column that replaced the old collateral figure), Table IV
> (production, pooled), Table V (the configurations' floor, in sample and cross-fitted),
> Table VI (production per endpoint, in the body) and Table VII (the rule per window,
> Appendix E). The production results are Section V-B, the post hoc analyses V-C, the
> boundary and the WAF V-D, and the ablation and cross-M results Appendix C. Fig. 2 is
> what the binomial configuration stops by botnet size and endpoint (V-B, from the
> `sweep` block), Fig. 3 the operating points (V-B) and Fig. 4 the cost (Appendix D).

| Script | Gap it closes | Needs the drive? |
|---|---|---|
| `scripts/bench_latency.py` | The paper claimed O(\|S_W\|·c) cost and near-linear OWL 2 RL behaviour, but **measured nothing** | No |
| `scripts/run_ml_families.py` | "No per-session detector works" rested on **a single** Random Forest | Yes |
| `scripts/window_sweep.py` | Sensitivity to *W* was declared uncharacterized | Yes |
| `scripts/run_canonical_realistic.py` | The generator had three realism defects, all favourable to us | Yes |
| `scripts/profile_drift.py` | How much background-profile staleness the enrichment test tolerates | No |
| `scripts/run_canonical_baselines.py` | The ablation's academic baselines (Section V-A, a table until round 8) had **no result file** behind them | Yes |
| `scripts/rule_detection.py` | The rule Ω(S) ≥ τ had **never been evaluated on its own**, nor against flash crowds | Yes |
| `scripts/rule_detection_production.py` | The rule had **never met production traffic**: every window so far came from the generator | Yes, and the production exports |
| `scripts/production_tables.py` | Tables IV, V and VII of the paper (pooled and per endpoint, test days and fresh day apart, calibrated baselines, the beta-binomial background, the deployed floor, cross-fitted runs) | Yes, the per-window results |
| `scripts/unseen_synth.py` | The unseen-fingerprint filter had been run on production only, and generated stacks never occur in the benign vocabulary | Yes |
| `scripts/cross_m_generalization.py` | Configuration (d) had only been scored on the botnet structure it was trained on | Yes |
| `scripts/ja4_churn.py` | How often the unseen filter would have a candidate: fingerprints the rolling profile never saw | Yes, the production exports |
| `scripts/waf_labels.py` | The production evaluation had no real malicious population: the WAF's verdicts as labels | Yes, the production exports |
| `scripts/floor_bands.py` | The floor on shared stacks used one prevalence and, under the beta-binomial, ignored the stack's correlation: floors by popularity band, at each band's correlation, and the ratio limit | Yes, the production exports |

```bash
make latency      # runs anywhere
make all-hd       # ml + window, needs the drive mounted
make drift        # profile drift, plus the M = 100 run with a pooled profile
make baselines    # the ablation's academic baselines (Section V-A)
make rule         # the rule as a window-level detector (Appendix E)
make rule-production  # the same rule on production traffic, botnet injected (section 9)
make rule-production-fresh  # the fresh day, 2026-09-25, analyzed as fixed in advance (section 12)
make rule-production-od     # the beta-binomial background, without and with known fleets (section 13)
make rule-production-crossfit  # the four configurations with a cross-fitted calibration (section 15)
make production-tables      # Tables IV and V from the per-window results (sections 12, 13 and 15)
make waf-labels             # the WAF's verdicts as labels for the scope (section 16)
make ja4-churn              # fingerprints the rolling profile never saw
make unseen-synth     # the unseen filter and shared stacks on generated traffic (section 12)
make cross-m      # configuration (d) trained on one stack count, tested on another (section 14)
make audit        # every sprint-6 number of the paper against results/ (no drive)
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
> 0.927 / 0.982 with *d* of +13.5 and +22.3 at p_bonf = 7.5 × 10⁻⁹. Use the
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
> | `mlp` | 0.956 | **0.952** |
> | `logreg` | 0.961 | **0.799** |
>
> The drop of `logreg` in the canonical scenario **is a finding, not a bug**:
> fragmenting the botnet across 25 stacks makes cross-session evidence
> non-monotonic in the label, and a model whose response to each attribute is
> monotone cannot carve out the middle band. With a monolithic botnet the effect
> does not exist.
>
> **The `mlp` row was a bug, fixed on 2026-09-26.** It used scikit-learn's early
> stopping, which scores a held-out 10% of the training set by *accuracy*. At 4.8%
> attack prevalence (K = 50) calling every session benign is already the best
> accuracy, so training stopped and restored the weights of epoch 7, before the
> network had learned a ranking: AUC 0.235 at K = 50 (below chance on its own
> training distribution) and 0.803 at K = 1000. With `early_stopping=False` the
> perceptron reaches 0.862 and 0.952 in configuration (d), and 0.493 and 0.494 in
> (a); `make canonical` was rerun and only the `mlp` entries of
> `results/canonical_realistic.json` changed. The paper's former sentence that
> the perceptron "inverts the ordering" was removed.

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
grows 6.6×. The reason: the campaign's own cluster barely changes (the largest
cluster holds 1,977–1,998 sessions at every W, `max_cluster_size` in
`window_sweep.json`), and the discriminative feature is a *fraction* (the share of
that cluster carrying one JA4). The insensitivity is therefore a property of the
generator's steady campaigns, not a claim about production traffic. Cluster size alone carries little, which is why (c) stays at 0.664
throughout.

Operational rule: **keep W as small as the traffic permits.** A larger window buys
no detection and adds state, linearly with class counting (quadratically with
pair edges, Section 1).

Two bounds: the scenarios target a single endpoint, so W is the only clustering
knob and a multi-endpoint deployment may behave differently; and W must still be
large enough for a cluster to form (the mean cluster holds ~132 sessions at W = 60 s).

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

## 5. The ablation's academic baselines

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

The rows of the former Table II (now in the text of Section V-A) are reproduced to three decimals, so they were
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

The paper's report of no collateral holds at the cluster sizes of Table II
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

The per-window result depends on the profile size, as the M = 100 point does.
With the 1,000-session profile of the cluster-level experiments
(`--profile baseline`, `results/rule_detection_steady60_rate0_binom.json`) the
rule still fires on no clean window and acts on 68.9% / 80.0% of attack windows
(K = 1000 / 50) with no collateral, but blocks a median 54.5% / 20.2% of their
attackers and names a filter in 1 of the 90 flash crowds, hitting 11.7% of its
users.

The flash crowds draw their users from another attack-free run of the same
generator, so their fingerprints follow the profile by construction. A surge
concentrated on one client type would be enriched and filtered; that case is not
evaluated.

**Per cluster** (Table II, Fig. 2, the drift paragraph), with the paper's
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
(`results/profile_drift_m100.json`). The Random Forest columns of Table II do not
change.

**Fig. 2 (collateral) now has a source.** It used to read `results/realistic_consolidated.csv`,
which no script wrote: its enrichment bars came from a σ = 0.002 run, while
`realistic_probe.py` called the scope with its default σ = 0.01, which at
M = 100 names no fingerprint and falls back to the whole endpoint (93% collateral).
`realistic_probe.py` now passes σ = 0.002 or the test explicitly and writes
`results/realistic_{tag}_consolidated.csv`, which `make_figures_en.py` reads. The
orphan file was removed.

## 8. Audit of the paper's numbers

`make audit` runs `scripts/audit_paper.py`, which recomputes every number this
sprint contributes to the paper (the ablation and cross-M numbers of Section V-A,
Tables II to V as printed, the abstract and conclusion, Sections V-B to V-D, the
collateral figure's bars, the drift figures and Appendices C to E) from the
committed files in `results/`, and compares them with the literal text of
`papers/http-session-noms/article.tex` (226 checks as of 2026-09-26, reframed version). Tables are
named by their LaTeX labels (`tab:symbolic`, `tab:production`, `tab:floor`,
`tab:perwindow`), since their numbers shift between revisions. It also checks that
Table II (`symbolic_detector.py`) and Fig. 2 (`realistic_probe.py`), two independent
scripts, agree on the enrichment coverage. It exits with status 1 on any
mismatch; a negative test that altered two numbers of the text was caught.

## 9. The rule on production traffic

`rule_detection_production.py` runs the rule of section 6 on real traffic of a
CDN (Azion, authorized), with the canonical botnet injected into it. The data are
aggregates exported from the access log, under `$DATA_ROOT/azion/`, one directory
per day (`YYYY-MM-DD`) or per range of days (`YYYY-MM-DD_YYYY-MM-DD`):

| Export | Rows | Columns |
|---|---|---|
| E1 | host × 5-min window × JA4 | connections, connections with a WAF-blocked request, requests |
| E2 | host × 5-min window | pairs of connections sharing a /24 (/48 for IPv6), connections |
| E3 | as E1 | E1's columns plus distinct client addresses, and those the WAF blocked |
| E4 | as E2 | the same pairs over distinct client addresses |

No address, port, prefix or URI leaves the log store. The exports and the
per-window results stay on the drive (`$DATA_ROOT/azion/results/`), since they
carry host names and volumes. What the paper reports is reduced by
`production_summary.py` to `results/production_summary.json`: endpoints become
E1–E4 with a generic role (read from `$DATA_ROOT/azion/roles.json`, which stays on
the drive) and a volume band, and only rates leave. `make audit` checks the paper
against that file.

**Why counts suffice.** The three sub-relations the rule reads (shared JA4, same
endpoint, same /24) are equivalence relations, so Ω is a function of class sizes:
Ω = 1.0·Σ_f C(n_f, 2) + 0.6·C(n, 2) + 0.3·P₂₄, where n_f counts the window's
units with fingerprint f, n all of them and P₂₄ the same-prefix pairs. The
enrichment test also reads only n_f and n. The script's count-based scope is
checked against `derive_scope_enriched` on a random sample of expanded windows
and exits with status 1 on any mismatch.

**Protocol** (`make rule-production`). A host is an endpoint, and the unit is the
origin: a client address (`--unit origin`, from E3 and E4). Clean traffic is every
client the WAF did not block. `--split rolling` tests each day from the fourth on
with a profile, τ (p99 of Ω) and test level calibrated on every earlier day, as
the rule would run; `hours` alternates UTC hours of one day, `halves` and `days`
are chronological. A host is evaluated when it carries TLS, has at least 50
calibration windows with k_min = 5 origins, and its median calibration window
holds at least k_min origins. `--calibrate-level` sets the scope's level per host
as τ is set (section 7 of `docs/concepts.md`).

- *False alarms*: the three rules of section 6 on the clean test windows.
- *Detection*: A ∈ {25, 50, 100, 250, 1000} attackers injected into each test
  window, built as `generator.py` builds them under `scenario_stealth.yaml`: with
  probability 0.9 an attacker takes one of M stack fingerprints, uniformly,
  otherwise one of its own, and it comes from one of 2,000 /24s. The stacks are
  `fresh` (absent from the traffic, the generator's default), `tail` (from the
  host's profile outside its ten most common fingerprints) or `adversarial` (the
  host's M most common). `blocked` is the share of the attackers the rule stops,
  averaged over all windows, so a firing that names only legitimate fleets
  counts zero.
- *Relative size*: the same botnet sized at 0.1, 0.5 and 1 times the host's
  median calibration window (`--attackers-rel`), on its own random stream, so a
  small endpoint is not flooded by an absolute size.
- *Baseline scopes*, under the same Ω ≥ τ: a per-fingerprint z-score against the
  profile (z > 3, no multiple-testing correction, no calibration), and a filter
  of fingerprints absent from the profile seen in at least k_min origins.
- *Flash crowd*: N legitimate origins drawn from the host's own test-day traffic
  added to one window, with the host's rate of same-/24 pairs.
- *WAF diagnostic*: the scope on the full test windows, blocked clients included,
  compared with the WAF's verdict, the only real label available.

Approximations: the scope is judged on JA4 alone, since the /24 conjunct of
`derive_scope_enriched` needs per-origin prefixes, and it can only narrow a
filter; E2/E4 drop blocked requests, not blocked clients (a median difference of
0 per window); injected origins draw their /24s from a pool disjoint from real
prefixes.

### Findings

Eight days (2026-09-17 to 2026-09-24), five test days, four endpoints; the fifth
candidate's typical window holds fewer than five origins.

**Sessions are not independent draws.** Counted in connections at the nominal
level (0.01), the scope names a filter in 60.1% of clean windows, including the
windows the profile came from. One client opens many connections: 5.8 per client
on the API endpoint, whose top fingerprints have a Pearson dispersion φ of 34.1
(about 1 under the binomial model). Counting origins brings φ back to about 1 and
the scope to 26.9%. The rest comes from fleets of legitimate clients sharing a
known fingerprint that switch on together: a probe fleet of about twenty clients
at one request per connection, active only 07–15 UTC; a job at fixed minutes of
each hour. Calibrating the level on the calibration windows, as τ is, brings the
scope to 3.5% and the full rule to 0.2% of clean windows of days it never saw.
The level falls to 10⁻⁴ (SSO) through 10⁻¹⁴ (API), 10⁻⁶⁰ (RUM) and 10⁻⁷³ (console).

**The level sets the smallest botnet the rule stops** (fresh stacks, M = 25,
share of attackers blocked):

| Endpoint | Origins/window | Clean: scope / rule | Flash 100: rule | A = 100 | A = 250 | A = 1000 |
|---|---|---|---|---|---|---|
| E1, RUM beacons | > 1,000 | 6.3% / 0.1% | 0.1% | 0.0% | 0.1% | 38.3% |
| E2, web console | 10–100 | 4.2% / 0.7% | 5.3% | 0.0% | 1.4% | 83.6% |
| E3, API | 10–100 | 1.7% / 0.1% | 8.2% | 25.7% | 83.9% | 90.0% |
| E4, SSO | 10–100 | 1.5% / 0.0% | 2.2% | 78.8% | 89.9% | 90.0% |
| All | | 3.5% / 0.2% | 3.9% | 26.1% | 43.8% | 75.5% |

At the nominal level (origins) the rule blocks 58% at A = 100 but fires on 1.7% of
clean windows; calibration trades that for 0.2%. Ω ≥ τ alone reacts to volume, as
on the generator: on E1, with thousands of origins per window, a botnet of a
thousand moves Ω past the daily variation in only 43% of windows. Where the rule
fires on an attack window the median legitimate share hit is zero (70% at worst,
on E3, where the scope also named a fleet).

**What a fair injection shows** (reviewer pass, 2026-09-24). Sized against each
endpoint, a botnet as large as the typical window is stopped on the busiest
endpoint (67.6%) and hardly on the three small ones (≤ 1%): its stacks then hold
one or two origins, which no calibrated level names, and Ω stays within the
daily variation. Pooled, 17.2% at 1×. Stacks drawn from fingerprints real clients
use (`tail`) lower the blocked share to 20.2% / 61.6% at 100 / 1,000 attackers.
When the rule fires on a clean window of E2 or E3 it names a fleet and blocks
about half of that window's clients (median 49.1% pooled), although it fires on
only 0.25% of clean windows.

| Gate / scope | Clean: fires / collateral | Flash 100 | Blocked, new stacks, A = 100 / 1,000 / 1× | Shared stacks |
|---|---|---|---|---|
| Ω ≥ τ / enrichment (the paper's rule) | 0.2% / 49.1% | 3.9% | 26.1 / 75.5 / 17.2 | 20.2 / 61.6 / 16.5 |
| Ω ≥ τ / z-score > 3 | 2.6% / 22.8% | 64.5% | 66.4 / 85.6 / 32.6 | 63.9 / 84.3 / 31.4 |
| Ω ≥ τ / unseen fingerprints | 0.0% / 3.3% | 0.2% | 28.6 / 77.1 / 18.4 | 0 / 0 / 0 |
| Ω ≥ τ / enrichment ∪ unseen | 0.3% / 48.6% | 4.0% | 37.5 / 77.1 / 18.6 | 20.2 / 61.6 / 16.5 |
| origins / enrichment | 0.1% / 31.4% | 3.9% | 26.1 / 76.1 / 18.4 | 20.2 / 62.1 / 17.4 |
| origins / enrichment ∪ unseen | 0.1% / 29.9% | 4.0% | 38.4 / 77.7 / 19.9 | 20.2 / 62.1 / 17.4 |

The z-score blocks more, but fires on ten times the clean windows and on most
flash crowds (64.5% at 100 users, 86.8% at 1,000, against 3.9% and 21.8% for the
rule); the unseen-fingerprint filter misses every stack real clients share. The
union of the enrichment test and the unseen filter (`union_*` columns) takes the
best of both: fingerprints absent from the profile carry no fleet, so the
calibrated level, which fleets set, need not apply to them.

**The trigger is volume** (`volume_baseline` in `results/production_summary.json`).
A plain threshold on the number of distinct origins per window, at the 99th
percentile of the same calibration windows as τ, fires on the same windows as
Ω ≥ τ in 86–99.6% of cases and catches at least as many attacks at every size
(A = 50: 42.8% against 28.9%), at 3.0% of clean windows against 2.6%. Used as
the gate in front of the scope (`origins_*` columns, `tau_origins` per fold), it
halves the rule's false alarms (0.25% → 0.11%) and loses detection in none of the
attack cells. The reason: the 13 clean windows that pass Ω ≥ τ but not the origin
threshold carry a median 33% of Ω outside the endpoint term (TLS and /24 pairs),
against 12% in the others, and in 8 of them the scope names a fleet. A fleet
concentrates on one fingerprint, which lifts Ω's TLS term in the very windows
where the scope misfires, so a trigger that reads the scope's evidence doubles its
errors. On the generator the origin gate catches 82.2% / 85.7% of attack windows
(Ω: 77.8% / 85.7%) and, with the test, no clean window or flash crowd. The paper
keeps Ω as the rule and reports the gate (Section V-B, Appendix E, contribution
(ii)).

**Both refinements were chosen on the test days** (fourth review round). They
hold on each of the five, taken alone:

| Test day | Clean false alarms, Ω / origin gate | Blocked, new stacks, A = 100: enrichment / origin gate + union |
|---|---|---|
| 1 | 1 / 1 | 26.0 / 31.4 |
| 2 | 3 / 1 | 26.1 / 39.8 |
| 3 | 2 / 1 | 26.3 / 40.9 |
| 4 | 2 / 1 | 26.1 / 40.1 |
| 5 | 6 / 2 | 26.1 / 39.6 |

Shared stacks tie every day. The counts are small (14 against 6 in all), so the
paper labels the gate and the union as findings of this evaluation that fresh
days must confirm: the design is now fixed, and days exported after 2026-09-24
would be a true out-of-sample test. Two limits bind detection: on E1 at 1,000
attackers and on E4 at 1× the scope names botnet stacks in most windows but
Ω < τ; on E2 and E3 a 1× botnet puts one or two origins on each stack, which no
calibrated level names (0.0% / 3.9% blocked by the scope alone).

**At a tenth of the typical window only E1 is in the stealth regime** (over 100
attackers; the others get fewer than ten). There the calibrated level (10⁻⁶⁰)
holds enrichment to 0.6%, against 11.2% for the unseen filter and 12.5% for the
z-score, which fires on 5.1% of E1's clean windows; the union recovers 11.2%, and
with shared stacks only the z-score stops any (12.2%). Pooled, no scope passes 5%,
which is why the paper reports E1 separately.

**ρ barely matters** (`--rho 2`, `--rho 5`, tags `_rolling_origin_rho2/5`, in
`variants.rho2/rho5`). No pooled entry of the production table of that revision that depends on ρ moves by more
than 7.2 points (a collateral median over six windows); fire and block rates move
by at most 4.5. The level does the work, and ρ = 3 stays as an effect-size floor.

**The WAF agrees where it is active.** On the full traffic, 84% (E3) and 96% (E4)
of the clients the scope would block were also blocked by the WAF; on E2 the
scope names legitimate fleets, and 1.5% were.

**A profile per hour of day did not help** (`--profile-by-hour 1`: one profile
per UTC hour from calibration windows within ±1 h). With seven days of history
each hourly profile is thin: the calibrated level loosens, but out-of-sample the
scope rises to 8.1% of clean windows and flash crowds of 100 to 19%, while the
blocked share stays at 25% / 44% / 72%. Modelling the fleets directly is future
work.

**Ω's weights do not drive window detection** (`rule_detection.py --weights`,
results `rule_detection_steady60_rate0_bigprof_binom_w{uniform,tls,noep}.json`).
With uniform weights (1, 1, 1) Ω ≥ τ catches 78.9% / 85.7% of attack windows
(K = 1000 / 50), against 77.8% / 85.7% with (1.0, 0.6, 0.3). Without the endpoint
term (TLS only, or TLS and network) it catches 33.3% / 0% and still flags 53–100%
of flash crowds. The endpoint term, which counts origins, carries the detection,
and the enrichment test the discrimination; the paper now frames it that way
(Section III-F).

**The per-cluster experiments choose the cluster without labels** (`CLUSTER ?=
label-free`, `--label-free-cluster`): the cluster of largest Ω. It is the
attack-dominant one in 148 of 150 scenarios; in the other two (M = 1, seed 3) the
attack-share choice had picked a one-session cluster. Table II and Fig. 2 move
at M = 1 only, from 84.0% to 89.8% blocked.

**Synthetic results are otherwise unchanged.** On the generator every session has its own
origin (distinct origin-fingerprint pairs equal sessions in every scenario
checked; Ω moves by at most 0.22%), and no calibration window or run names a
filter at 0.01, so the calibrated level stays at 0.01. The reruns of `symbolic`,
`realistic`, `drift` and `rule` with `METHOD=origin` reproduce every number the
paper takes from them (`make audit`).

**The laboratory captures are single-source floods.** Counted in origins, the
seven attack clusters of CICIDS2017 and CIC-IoT2023 come from one to seven
addresses in one /24; the DoS-Other cluster of the old Listing 2 holds two origins
and Ω = 0.6. Listing 2 now shows a canonical campaign
(`scripts/example_chain.py`, `results/example_chain.jsonld`).

**A real event in the export.** On 2026-09-19 the staging API received about
5,800 requests per window for 18 hours from about 22 clients: a surge from few
origins, which the origin count does not read as a distributed campaign. That
host is below k_min origins per window and is not evaluated.

**A learned model given the profile** (`symbolic_detector.py`, `rfp_*` columns).
The Random Forest of Table II reads no profile of normal traffic; given it as two
per-session features, the log prevalence of the session's JA4 and its enrichment
in the detection cluster (`profile_features`), it recovers at FPR = 0 85.9 / 91.7 /
87.4 / 86.9% at M = 1 / 5 / 25 / 100, against 89.8 / 90.0 / 90.3 / 38.6% for the
rule. It trains on 70% of the labels of the very campaign it scores, which no
operator holds during an attack; the rule needs none. At M = 100 the rule's
thousand-session profile is the limit (a pooled profile restores 89.6%, section 7).
The paper no longer claims the rule "doubles" the learned model.

## 10. What the graph adds, measured

The fourth review round asked for the graph's value to be measured rather than
asserted. Two checks, neither needing the data drive:

**The count query is compiled from the ontology** (`make compile-check`,
`scripts/compile_counts.py`, `results/compile_check.json`). The ontology now marks
each equality sub-relation with `kg:classKey` (what it equates: `kg:tlsJa4`,
`kg:targets`, `kg:srcPrefix`) and `relatedTo` with `kg:countUnit`
(`kg:originatesFrom`); the three sub-relations without a class key are listed as
needing pairwise evaluation. The compiler turns that, plus a binding of properties
to log columns (`bindings/clickhouse_example.json`), into the SQL for Ω and the
class sizes per window and endpoint. On 6,000 generated sessions from 3,871
origins (repeat clients, plain-HTTP sessions, a botnet on five stacks, three
windows, four endpoints) the DuckDB run of the compiled query reproduces
`decompose_omega(unit="origin")` with a largest difference of 0.0. A copy of the
ontology with one more equality sub-relation (same User-Agent, weight 0.5) costs
four triples; the recompiled query carries the new term and still matches the
reference, with no code changed. The production binding (table, filters) is the
operator's and stays on the drive (`$DATA_ROOT/azion/queries/`). **Run in the
operator's log store for 2026-09-23, the compiled query returned the
exported origin and /24-pair counts in all 1,152 windows**
(`results/compile_production_check.json`; the fresh day is in
`compile_production_check_fresh.json`). `--compare` reproduces the origin and
/24-pair match. Its JA4 pair counts lie between the export's clean and total counts
in every window and equal the clean ones in all 288 windows without a WAF-blocked
client: the export drops a client the WAF blocked part of the time, the compiled
filter (requests the WAF did not block) keeps it. That JA4 comparison was run ad hoc
against the per-JA4 export and is not yet part of `--compare`.

**The STIX export is valid STIX 2.1** (`make stix-check`, `scripts/stix_check.py`,
`results/stix_validation.json`): four bundles, built from the committed JSON-LD
chains alone, pass the OASIS `stix2-validator` with no error or warning, in strict
mode too, and parse with the `stix2` library. See the pillar-4 README for the
format.

**Two consumers ingest the bundles** (`make stix-ingest`, `scripts/stix_ingest.py`,
`results/stix_ingest.json`), locally and with no attack traffic:

- *TAXII 2.1.* The OASIS reference server (medallion 3.0.0, memory backend) runs
  on localhost; each bundle is posted to a collection and read back by id with
  the OASIS client (taxii2-client 2.3.0). All four bundles are accepted, and the
  indicator (with its JA4 pattern and extension), the course-of-action, the
  relationship and the identity come back identical, in 7–14 ms per bundle. The
  extension-definition cannot be served: medallion reads any object's `version`
  field as a timestamp (`common.find_att`), and STIX 2.1 requires a semantic
  `version` ("1.0.0") on that object, so listing a collection that holds one, or
  fetching it, returns HTTP 500. This is a bug of the reference server.
- *MISP.* MISP's own STIX 2.1 importer (misp-stix 2026.9.16,
  `ExternalSTIX2toMISPParser`) turns each bundle into an event: the
  course-of-action becomes a galaxy cluster and the endpoint a network-traffic
  object, but **all 26 fingerprints of the scopes are dropped**, with the warning
  "Unmapped pattern part". STIX 2.1 has no JA4 property, so the exporter carries
  it in an extension, and MISP has no JA4 attribute type either. A playbook fed
  by MISP would therefore scope the whole endpoint, the harmful choice the paper
  measures. A pattern holding only the JA4 clause is kept verbatim as a
  `stix2-pattern` object, but not mapped to attributes. Keeping the scope across
  consumers needs a standard JA4 property.

The ontology also had `kg:targets` declared with domain `Attack` and range `Host`,
so asserting a session's endpoint would have entailed that the session is an
attack; the domain and range are now unions, as for `kg:originatesFrom`. It
lacked `kg:tlsJa4`, which Listing 1's SWRL rule uses; it is declared now.

## 11. A profile that knows its fleets

The calibrated level is set by legitimate fleets: at a tenth of the typical window
it holds enrichment to 0.6% on E1, the one endpoint in the stealth regime.
`rule_detection_production.py --fleets SHARE` takes as **known fleets** the
fingerprints the test names, at the nominal level (0.01), in at least SHARE of the
endpoint's calibration windows. They leave the scope and the level's calibration,
so the level is set by what remains. The cost is an evasion route: an attacker
presenting a known fleet's fingerprint is not scoped. The option consumes no
random numbers, so the injected botnets are those of the base run, paired.

**Protocol, fixed on 2026-09-25 before any fleet run was looked at**
(`scripts/fleet_selection.py`). It was committed together with the results
(e2e09a7), so the order is not verifiable from git alone:

- design days: the first three test days (2026-09-20 to 09-22); held-out days:
  the last two (09-23, 09-24);
- grid: SHARE ∈ {0.5%, 1%, 2%, 5%}, from the calibration windows alone, where
  recurring fingerprints are named in up to 16% (RUM), 6% (API), 2.5% (console)
  and under 1% (SSO) of the windows;
- on design days, among the shares whose clean false alarms (Ω ≥ τ with a
  non-empty scope) do not exceed the base rule's, choose the largest mean blocked
  share over the eight cells the paper reports (stacks new and shared × 100 and
  1,000 attackers, 1× and 0.1× the typical window); ties to the smaller share;
- only then compute the held-out days, for the chosen share and the base rule.

**Result.** On the design days only the 5% share keeps the false alarms at or
below the base rule's (5 against 6 of 3,454 clean windows); it is chosen. The
smaller shares block more (mean 30.9–33.8% against 26.7%) but fire on 12–16
clean windows, although each of those blocks few clients (median 0.6–4.1% against
48.5%), since the fleets that made the heavy filters are no longer named.

On the held-out days, the chosen share against the base rule (Ω ≥ τ gate,
enrichment scope):

| | Clean false alarms | Collateral | Flash 100 | Mean blocked | E1 at 0.1×, new / shared |
|---|---|---|---|---|---|
| base | 8 / 2,189 | 50.2% | 3.5% | 27.9% | 0.7% / 0.2% |
| known fleets, 5% | 7 / 2,189 | 50.7% | 3.4% | 28.3% | 6.3% / 4.4% |

On E1 five or six fingerprints, 7% of the profile, are known fleets, and the level
rises from about 10⁻⁶⁰ to 10⁻²¹; E2 and E4 have none at 5% (their recurring
fingerprints are named in under 2.5% of the windows), and E3 has one or two, so
their numbers barely move. The z-score still stops more on E1 at 0.1× (12.5%), at
5.1% of E1's clean windows; on the two held-out days alone the same cell gives
6.5% for the unseen filter and 7.3% for the z-score (shared stacks: 0% and 7.1%),
against 6.3% (4.4%) for the known-fleet profile (`held_out_E1_x0.1_baselines`).
Only one of the four shares (5%) kept the design days' false alarms at or below the
base rule's, so the rule's "largest mean blocked share" had a single candidate.
Computed after the choice and for transparency only
(`held_out_secondary_all_shares`), the smaller shares keep the same trade-off on
the held-out days: 13–16 false alarms at a median 10.6–12.2% collateral, flash
crowds of 100 fired on 6.6–11.0%, mean blocked 30.3–33.8%, E1 at 0.1× 6.5% /
5.7–5.9%. The control rerun without `--fleets` reproduces the base per-window CSV
byte for byte.

## 12. Baselines at the test's budget, the calibration floor and a fresh day

A holistic review against strong NOMS papers (2026-09-25) asked for four things:
baselines on equal terms, the limit of calibration stated and measured, a test
on data that no choice had seen, and the unseen filter on generated traffic. Each
is now in the paper: Section V-D with Tables III and IV, and Table II.

**Calibrated baselines** (`rule_detection_production.py`, `calibrate_baselines`).
The uncalibrated z-score (z > 3) fires on 2.6% of clean windows, so comparing its
detection with the test's is unfair. Two baselines now get the test's budget, a
filter in at most 1% of attack-free calibration windows:

- `zcal`: the per-fingerprint z-score against the profile, with its threshold set
  to the 99th percentile of the window's largest z over the calibration windows,
  never below 3;
- `zhist`: the z-score of each fingerprint's count against its own calibration
  history (mean, and standard deviation floored at 1), thresholded the same way.

Both run under the distinct-origin gate. The regression check passed: the five
test folds of the earlier scopes are unchanged.

**The union and the unseen filter on generated traffic** (`unseen_synth.py`). The
unseen filter (fingerprints absent from the profile, seen in at least k_min
origins) matches enrichment up to 25 stacks on generated traffic, because the
generator's stacks never occur in the benign vocabulary, and does better at 100
(88.1% against 38.6%). The `profile_tail` shared mode relabels each cached scenario
with stacks drawn from the profile outside its ten most common fingerprints, as the
production injection's `tail` source does: there the unseen filter blocks 0%,
enrichment 85.4% at 2.23% collateral, and the uncalibrated z-score 89.9% at 3.37%
(K = 1000, n = 15). `vocab_tail` is a sensitivity variant, not in the paper.

**The calibration floor** (`production_tables.py`, `floor`). Among n origins the
test names a stack only past the smallest count c with P[Bin(n, b) ≥ c]·|F| < λ_e.
A 25-stack botnet of A attackers puts about 0.9·A/25 origins on each stack, so the
floor is the smallest A whose stacks reach that count in the endpoint's median
calibration window, reported as a multiple of that window (median over the five
test days, stacks new to the profile, b = 1/N):

| Endpoint | λ_e | Floor, base profile | Floor, known fleets |
|---|---|---|---|
| E1, RUM beacons | 10⁻⁶⁰ | 0.16 | 0.07 |
| E2, web console | 10⁻⁷³ | 11.6 | 11.6 |
| E3, API | 10⁻¹⁴ | 4.1 | 3.5 |
| E4, SSO | 10⁻⁴ | 4.2 | 4.2 |

On E1 a stack is named only past 15 to 18 origins. On the three small endpoints no
botnet that fits in a window can be named. Each floor record also carries the number
of known fleets its fold exempted (`known_fleets`): 5 or 6 on E1 and 0 to 2 on E3
with the 5% share, and 0 on every endpoint and fold under the beta-binomial.

**The fresh day** (`make rule-production-fresh`). The protocol,
`results/fresh_day_protocol.md`, was written before 2026-09-25 was read, with the
SHA-256 of the three exports: the frozen configuration (known fleets at 5%, the
enrichment test united with the unseen filter, the distinct-origin gate), the
metrics in the order they would be reported, and the decision rule: the day is
consistent with the test days (5 false alarms in 5,643 clean windows) if
P[Bin(n_day, 5/5,643) ≥ x_day] ≥ 0.05. The day is a sixth rolling fold,
calibrated on 2026-09-17 to 24.

- 2 false alarms in 1,152 clean windows, P = 0.27: consistent. Both fall on the web
  console and block a median 41.2% of their window's clients.
- Blocked: 38.9% and 73.4% of 100 and 1,000 attackers on new stacks, 21.5% and 60.9%
  on shared ones; at a tenth of E1's window the gate never fired.
- The calibrated z-score fired on the same two windows (`overlap_frozen_zcal` in
  `production_tables.json`) and stopped more at 100 attackers (58.3% and 26.7%); on
  the test days it fired on 20 clean windows, 4 of them among the frozen
  configuration's 5.
- The ontology-compiled count query, run in the operator's store for the day,
  returned distinct origins and /24 pairs equal to the export in all 1,152 windows
  and the JA4 pair counts in the 288 windows where the WAF blocked no client
  (`results/compile_production_check_fresh.json`).

**The stealthy regime, per day** (`stealth_E1` in `production_tables.json`). With
known fleets, a botnet a tenth of E1's window is named in every window, on new and
shared stacks alike, but the distinct-origin gate fires in 0.7% to 41.7% of those
windows depending on the day (0% on the fresh day), so 11.8% of the attackers on
new stacks are stopped. A trigger on the scope alone, examined after the fact,
would stop 89.6% (new) and 61.1% (shared) at 1.0% of E1's clean windows; it is
reported as exploratory.

**WAF agreement.** Of the clients the scope would block on the full traffic, the
WAF also blocked 84% on E3 and 96% on E4, where the scope names no fleet, and 1.5%
on E2, where it does; the scope matches 16.7% of all clients the WAF blocked. E1 has
no WAF activity.

`production_tables.py` recomputes every production number of the paper from the
per-window CSVs on the drive and writes only rates and counts to
`results/production_tables.json`; `make audit` checks Tables III and IV, the abstract,
Section V-D and Appendix E against it.

## 13. An overdispersed background (beta-binomial)

The binomial the enrichment test assumes treats each origin as an independent draw
from the profile. Fleets of legitimate clients that switch on together break that,
which is why the calibrated level falls to 10⁻⁶⁰ (RUM) and 10⁻⁷³ (console): at such
levels the p-value is only a score with an empirical threshold, as the review of
2026-09-26 pointed out, and the calibration floor of section 12 is partly set by
the misspecification.

`rule_detection_production.py --overdispersion` tests each fingerprint of the profile
against a beta-binomial of the same mean instead. Its intra-window correlation φ is a
moment estimate over the calibration windows of at least k_min origins,

    φ = Σ[(c − n b)² − n b (1 − b)] / Σ[n (n − 1) b (1 − b)],  clipped to [0, 0.99],

from Var[c] = n b (1 − b) (1 + (n − 1) φ). A fingerprint absent from the profile keeps
the binomial (φ = 0). The level is calibrated exactly as before, and the scope
self-check is skipped, since `derive_scope_enriched` implements the binomial only. On
simulated beta-binomial counts the estimator recovers φ = 0.102 for a true 0.1, 0.020
for 0.02 and about 0 for binomial counts (five repeats each).

`make rule-production-od` runs it without and with the 5% known-fleet share, and
`make production-tables` adds both runs (`od`, `od_fleets`) to
`results/production_tables.json`. Test days (five folds), union scope:

| Endpoint | Level, binomial → beta-binomial | Floor (× window) | Distinct-origin gate: false alarms | Blocked, 1× window (new stacks) |
|---|---|---|---|---|
| E1, RUM beacons | 10⁻⁶⁰ → 7 × 10⁻⁵ | 0.16 → 0.03 | 0.14% → 0.14% | 70.8% → 70.8% |
| E2, web console | 10⁻⁷³ → 0.01 (cap) | 11.6 → 0.90 | 0.28% → 1.32% | 5.0% → 25.9% |
| E3, API | 10⁻¹⁴ → 0.01 (cap) | 4.1 → 1.37 | 0.07% → 0.00% | 1.9% → 22.7% |
| E4, SSO | 10⁻⁴ → 0.01 (cap) | 4.2 → 2.8 | 0.00% → 0.08% | 2.1% → 6.0% |

Pooled over the four endpoints, under the distinct-origin gate, the beta-binomial
union fires on 0.39% of clean windows (22 of 5,643), a median 10.5% of their clients,
and blocks 59.8% and 77.7% of 100 and 1,000 attackers on new stacks and 40.5% and
63.2% on shared ones. The calibrated z-score of section 12 fires on 0.35% (20), 10.8%
collateral, and blocks 54.7%, 77.7%, 23.7% and 62.3%. The two operating points almost
coincide, with more blocked on shared stacks by the beta-binomial. Without a gate
(the scope alone as trigger), the beta-binomial fires on 2.1% of E1's clean windows
and stops 90.0% and 78.3% of a botnet a tenth of E1's window on new and shared
stacks, against 89.6% and 61.1% at 1.0% for the binomial with known fleets.

**Known fleets become unnecessary.** Under the beta-binomial no fingerprint is named
at the nominal level in 5% of any endpoint's calibration windows, so the known-fleet
set is empty on every endpoint and `od_fleets` equals `od` window for window: the
fleets' synchrony is in φ, and the allow-list of section 11, with its evasion route,
is not needed.

**Caveats.** The level stays at the 0.01 cap on the three small endpoints, and on E2
the test days' false alarms (1.32% under the gate, 10.8% as a scope-alone trigger)
exceed the 1% the calibration windows promised. φ is fitted on the calibration days
and the console's fleets vary from day to day, but the calibrated z-score, which
fits no φ, also exceeds the budget there (1.11%), so the paper attributes the excess
to the console's drift rather than to the fit alone. The variant was built after the fresh day of
section 12 had been read, so its fresh-day numbers (0 false alarms in 1,152 windows
under the gate; 1.6% as a scope-alone trigger) are post hoc and not covered by
`fresh_day_protocol.md`.

## 14. Does configuration (d) generalize across botnet structures?

The ablation of Section V-A trains and tests configuration (d) on a 70/30 split of the sessions of one
generated campaign. `scripts/cross_m_generalization.py` (`make cross-m`) trains the
same Random Forest, on the same features, on campaigns with one number of stacks M
and tests it on campaigns with another (K = 1000, α = 1.5, 15 seeds, halves of the
seeds swapped between training and test).

**Leakage check.** For a given seed the generator draws every benign session before
anything that depends on M, so the benign session table is identical across M = 5,
25 and 100, and the attack sessions of M = 25 and M = 100 differ only in their stack
label. A same-seed design would score the per-session control (a) at 0.88–0.94 from
memorized copies alone; the disjoint-seed protocol has no test session in any
training scenario.

| Train → test | (a) cross-M | (d) in distribution | (d) same M, other seeds | (d) cross-M |
|---|---|---|---|---|
| 5 → 25 | 0.498 | 0.979 | 0.949 | **0.614** [0.593, 0.633] |
| 5 → 100 | 0.498 | 0.961 | 0.956 | **0.626** [0.604, 0.645] |
| 25 → 5 | 0.498 | 0.996 | 0.995 | **0.481** [0.469, 0.492] |
| 25 → 100 | 0.489 | 0.961 | 0.956 | **0.748** [0.739, 0.758] |

(d) keeps 0.95–0.995 on unseen campaigns with the same M but falls to 0.48–0.75 when
M changes: `share_ja4`, which carries 64–77% of its feature importance, has a median
of 179 among attackers at M = 5, 35 at M = 25 and 8 at M = 100, against 133 among
benign sessions, so the forest learns the band the training M produces. The
ablation's 0.93–0.98 measures separability within one generator setting. The
enrichment rule trains on nothing and keeps about 90% at every M up to 25 (Table II).


## 15. Cross-fitted calibration

The rolling split fits each endpoint's profile, its level λₑ, the calibrated z-score's
threshold and its known fleets on the same windows: the days before the test day. A
calibration window is then judged against a profile that already contains its own
counts, so the level may be fitted to its own days, as the review of 2026-09-26
pointed out. `rule_detection_production.py --split crossfit` keeps the test day, its
profile, τ and the distinct-origin gate exactly as `rolling` does, but when it fits the
level, the z threshold and the known fleets it judges each calibration day against a
profile (and, under `--overdispersion`, a correlation φ) of the other calibration days:
leave one day out. A first version fitted everything on the last calibration day
alone; one day misses the rare fleet events that set the level, and it made the
console's level *more* lenient, so it was dropped. `make rule-production-crossfit` runs
the four configurations, and `make production-tables` reduces them as `xfit`,
`xfit_fleets`, `xfit_od` and `xfit_od_fleets`. The rolling runs are unchanged: every
decision column of their CSVs is identical with and without the option.

**p-values in logs.** Cross-fitting exposed a numerical fault. A fleet absent from the
other days' profile gets p-values below the smallest double, `binom.sf` returns 0,
and in three folds the beta-binomial's calibrated level on E1 came out exactly 0,
which names nothing. `adjusted_p` now works in natural logs (`log_tail`: the log of
`sf` where that is a float, the tail summed from `logpmf` where it underflows, since
`scipy`'s `logsf` is itself the log of `sf`), the level is carried as its log
(`scope_log10_level` in the fold records), and `production_tables.floor` computes the
floor in logs too. Decisions are unchanged wherever no p-value underflowed: the regression
on one fold gave identical named, recall and collateral columns, with the stored float
level differing in its 15th digit.

Test days, pooled over the four endpoints, under the distinct-origin gate:

| Configuration | False alarms (95% interval) | Collateral per alarm | Flash crowd 1,000 | 100 attackers, new / shared | Floor (attackers per window) |
|---|---|---|---|---|---|
| Binomial, in sample | 5 (0.03–0.21%) | 32.9% | 22.2% | 38.4% / 21.7% | 84–672 |
| Binomial, cross-fitted | 6 (0.04–0.23%) | 31.4% | 20.7% | 36.9% / 17.8% | 84–641 |
| Beta-binomial, in sample | 22 (0.24–0.59%) | 10.5% | 28.4% | 59.8% / 40.5% | 56–85 |
| Beta-binomial, cross-fitted | 6 (0.04–0.23%) | 2.0% | 10.9% | 48.0% / 27.2% | 56–141 |
| z-score, in sample | 20 (0.22–0.55%) | 10.8% | 13.1% | 54.7% / 23.7% | — |
| z-score, cross-fitted | 13 (0.12–0.39%) | 11.0% | 5.5% | 33.6% / 9.0% | — |

(The binomial's in-sample floor column is the binomial configuration's, known fleets
exempted: 198 attackers on E1, 84–672 on the small endpoints.) The binomial
configuration barely moves, so its calibration was not flattered by fitting in sample.
The calibrated z-score's threshold rises by a median factor of 1.8 across endpoints
and folds (1.2 to 6.0): its false alarms fall to 13, the console's within budget
(0.90%), and its lead in detection disappears. The beta-binomial's levels fall from the
0.01 cap to between 10⁻¹⁷ and 10⁻²; it then matches the binomial's false alarms with far
lighter filters, fewer flash-crowd triggers, more detection at 100 attackers and a lower
floor on every endpoint, and the console falls within budget (0.28%, flash crowds of
1,000 in 16.1% of its windows against 74.4% in sample). The console's scope alone still
names a filter in 4.4% of its test-day windows under either calibration: its fleets
change from day to day. The option and the beta-binomial were both built after the
fresh day was read, so these numbers are post hoc; only the binomial configuration was
tested on a day it had not seen.

## 16. The WAF's verdicts as labels

The production evaluation injects its botnets. The only malicious populations the
exports carry are the clients the operator's WAF blocked, so `scripts/waf_labels.py`
(`make waf-labels`) takes those verdicts as labels and scores each configuration of
Table II against them on the full test windows (blocked clients included), next to
trivial filters on the same windows (the window's most common fingerprint, its three
most common, the unseen filter alone) and to a random pick of clients. The WAF's rules
are its own: a blocked client is whatever the WAF blocks, not necessarily a flood.

It does so under two profiles:

- **clean profile** (the paper's rolling runs): profile, level and thresholds come
  from the clients the WAF did not block. A fingerprint the WAF blocks is then rare in
  the profile *by construction*: with ratio ρ = 3, a stable fingerprint is enriched on
  the full traffic only if its blocked share exceeds 1 − (1 − S)/3, about 0.88 on E3
  (S = 63%) and 0.80 on E4 (S = 39%);
- **all-client profile** (`--waf-in-profile`, `make rule-production-wafprof`, the
  binomial configuration and the beta-binomial): profile, level and thresholds come from
  every client, blocked ones included, as a scope in front of the WAF would see them.

Test days, scope alone on the full traffic:

| Endpoint | Profile | Named | Recall | Precision (random pick) | Lift | Surges detected (by chance) |
|---|---|---|---|---|---|---|
| E3, API | clean | 27–90% | 2–22% | 84–96% (63%) | 1.3–1.5 | 13–28 of 28 (10–26) |
| | all clients | 2–3% | 0.01–0.2% | 4–33% (63%) | 0.06–0.53 | 1–2 of 28 (0.3–0.5) |
| E4, SSO | clean | 58–100% | 8–14% | 96–99% (41%) | 2.3–2.4 | 2–10 of 10 (6–10) |
| | all clients | 2% | 0.01–0.05% | 0.4–16% (41%) | 0.01–0.38 | 0 of 10 (under 0.1) |
| E2, console | clean | 5–14% | 0.3–1% | 1–6% (10%) | 0.12–0.57 | 0–6 of 33 (0.1–2.2) |
| | all clients | 4–11% | 0.2–0.4% | 1–2% (10%) | 0.10–0.20 | 0–5 of 33 (0.1–0.8) |

(Ranges over the binomial configuration, the beta-binomial and the calibrated z-score.
A surge is a run of windows with at least k_min blocked clients and at least the 99th
percentile of the blocked count on the days before; it is detected when a filter the
scope names matches a blocked client in one of its windows, and the chance column
applies the rate at which the scope matches one outside surges.) Under the clean
profile the high precision follows from the construction, and so do the surge
detections: a surge on a fingerprint the profile lacks is enriched by design. Under the
all-client profile the scopes name a filter in 2–3% of the API's and SSO's windows, do
worse than a random pick on every endpoint, and catch those two endpoints' surges at
chance. On the console the beta-binomial and the z-score each catch 5 of 33 surges
against under 1 by chance, yet their filters match under 1% of the surges' blocked
clients. The WAF's populations are part of every day's traffic: the scope, which reads
deviations from normal traffic, rightly ignores them, and the WAF's verdicts cannot
label floods. The paper reports this as a negative result (Section V-B) and states that
its main analysis runs the scope behind the WAF. The trivial filters show why no
fingerprint filter could do much better: only 25–37% of the blocked clients sit on
fingerprints that no unblocked client of the same window presents.

## 17. What the calibrated components do out of sample, and the deployed floor

The level λₑ and the z-score's threshold are fitted so that the scope alone names a
filter in at most 1% of the calibration windows, and the distinct-origin gate sits at
its 99th percentile. On the test days (clean windows, pooled; `gates_clean` and the
`|none` keys of `production_tables.json`):

| Component | In sample | Cross-fitted |
|---|---|---|
| Binomial configuration's scope alone | 2.18% (console 4.38%) | 1.93% |
| Beta-binomial's scope alone | 4.45% (console 10.8%) | 1.10% (console 1.46%; held-out day 1.22%) |
| Calibrated z-score alone | 6.15% (console 11.5%) | 2.48% (console 5.83%) |
| Distinct-origin gate alone | 2.98% (E1 5.4%) | — (unchanged) |

Every calibrated component exceeds its 1% target on the days after calibration, and
only the cross-fitted beta-binomial comes close. The configurations' end-to-end rates
(0.09–0.39%) come from the conjunction of gate and scope, which seldom misfire together.
The paper now says so and calls the level what it is: an empirical quantile of a
misspecified score.

**The deployed configuration's floor.** The floor of Table V used to be the test's alone
on new stacks. Joined with the unseen filter, a stack absent from the profile is named
once it holds k_min = 5 origins, from ⌈5M/0.9⌉ attackers whatever the level (28, 139
and 556 for M = 5, 25, 100). `production_tables.floor_deployed` gives the configuration's
floor on new and shared stacks for M = 5, 25, 100, per run (in sample and cross-fitted).
For M = 25, in attackers per window, in sample / cross-fitted:

| Endpoint | Binomial, new | Binomial, shared | Beta-binomial, new | Beta-binomial, shared |
|---|---|---|---|---|
| E1 | 139 / 139 | 254 / 286 | 85 / 139 | 86 / 167 |
| E2 | 139 / 139 | 1,090 / 1,041 | 56 / 114 | 84 / 168 |
| E3 | 139 / 139 | 168 / 227 | 56 / 114 | 56 / 140 |
| E4 | 84 / 84 | 84 / 114 | 56 / 56 | 84 / 84 |

The level binds on shared stacks: the binomial configuration names them only past 8% of
E1's window and 4 to 19 windows elsewhere. The beta-binomial's shared floors in this table
use each stack's own correlation (section 18, `floor_bands.json`): on E1 to E3 the tail's
median correlation is 0 and the floor equals the binomial-tail value `floor` gives, on E4
it is about 3 × 10⁻⁴ and the floor rises from 56 to 84. At the 0.01 cap two origins name
a new stack, so the beta-binomial's new-stack 56 is ⌈2·25/0.9⌉, set by M and not by the
endpoint.

## 18. What the scope names, what the trigger stops, and how sure the rates are

The review of the round-11 paper asked four things of the existing data. They are in
`production_tables.json` (keys `clean_ci95_cluster`, `clean_gate_windows`,
`clean_joint_expected`, `sweep`, `endpoints_exported`) and in `floor_bands.json`
(`make floor-bands`).

**The endpoints.** The exports hold 12 endpoints; the four evaluated are all those
that carry TLS, have at least 50 calibration windows of k_min origins and a median
window of at least k_min origins. No qualifying endpoint was dropped.

**Misfires cluster, and gate and scope are not independent.** False alarms fall on few
endpoint-days: 13 of the beta-binomial's 22 and 13 of the z-score's 20 are on the web
console on 2026-09-23. A bootstrap over endpoint-days (the days of each endpoint
resampled, 10,000 draws) gives the interval next to the exact one:

| Configuration | False alarms | Exact 95% | Bootstrap 95% | Joint, if independent |
|---|---|---|---|---|
| Binomial | 5 (0.09%) | 0.03–0.21% | 0.02–0.16% | 3.5 |
| Beta-binomial | 22 (0.39%) | 0.24–0.59% | 0.06–0.82% | 7.5 |
| Calibrated z-score | 20 (0.35%) | 0.22–0.55% | 0.05–0.81% | 11.9 |
| Binomial, cross-fitted | 6 (0.11%) | 0.04–0.23% | 0.03–0.18% | 3.2 |
| Beta-binomial, cross-fitted | 6 (0.11%) | 0.04–0.23% | 0.00–0.23% | 1.8 |
| z-score, cross-fitted | 13 (0.23%) | 0.12–0.39% | 0.00–0.70% | 4.6 |

The last column is the joint misfires the gate and the scope would give if they were
independent within each endpoint (gate rate × scope rate × windows). Every configuration
exceeds it, since a fleet raises the origin count and enriches its own fingerprint at
once, but for the binomial configuration the excess is within chance (section 19). The
bootstrap column turned out too coarse to use (section 19).

**The floor is not a cliff, and a binomial model of stack sizes predicts the ramp.** The
runs inject 25, 50, 100, 250 and 1,000 attackers on 1, 5, 25 or 100 stacks, and 0.1,
0.5 and 1 times the median window on 25. On new stacks, an attacker sits on a stack with
probability 0.9 and its stack then holds it and Bin(A − 1, 0.9/M) others, so the share
the scope alone blocks is 0.9 · P[Bin(A − 1, 0.9/M) ≥ c_min − 1], with c_min the smaller
of k_min and the test's count at the fold's level (`model_new`). The binomial
configuration, M = 25, scope alone / model / configuration behind the gate, in % (the gate
column is the share of attack windows where the distinct-origin gate fires):

| Endpoint | 25 | 50 | 100 | 250 | 1,000 | gate at 25 → 1,000 |
|---|---|---|---|---|---|---|
| E1, new | 1 / 1 / 0 | 9 / 9 / 1 | 43 / 43 / 3 | 88 / 88 / 11 | 90 / 90 / 41 | 6, 6, 8, 12, 45 |
| E2, new | 1 / 1 / 0 | 9 / 9 / 3 | 43 / 43 / 28 | 88 / 88 / 88 | 90 / 90 / 90 | 15, 28, 66, 100, 100 |
| E3, new | 2 / 1 / 0 | 9 / 9 / 4 | 43 / 43 / 43 | 88 / 88 / 88 | 90 / 90 / 90 | 12, 49, 100, 100, 100 |
| E4, new | 34 / 39 / 5 | 51 / 48 / 42 | 79 / 79 / 79 | 90 / 90 / 90 | 90 / 90 / 90 | 23, 88, 100, 100, 100 |

The model matches the injections within 10 points everywhere on E1 to E3 (E4's windows
of about 20 origins vary most). The floor of Table V, where the mean stack reaches c_min,
is the size at which a typical stack is named, near two thirds of the attackers covered;
below it the scope names the stacks chance makes larger. On E1 the gate, not the scope,
decides what is stopped: it opens in 6–13% of the windows of 25 attackers to a tenth of
the window, 45% at 1,000 (a third) and 79% at the whole window, so the configuration
stops 3.4% of 100 attackers, 11.8% of a tenth of the window and 70.8% of a whole one. On
E2 to E4 the gate opens on 100 attackers (1.6 to 5 windows), and the floor decides.

**Shared stacks by popularity, and the ratio limit.** The shared cells draw 25 stacks
uniformly past the profile's ten most common fingerprints, mostly rare ones (a median
prevalence of 2 × 10⁻⁶ on E1). `floor_bands.py` rebuilds each fold's rolling profile
from the exports (checked against the runs' own records in all 60 fold-runs: profile
size, origin count and tail prevalence equal) and gives the floor, M = 25, at each band's
median prevalence and, under the beta-binomial, its median correlation:

| Endpoint | Ranks 11–35 | Ranks 36–100 | Past 100 | Past 10 (Table V) |
|---|---|---|---|---|
| E1, binomial / beta-binomial | none / none | 743 / 480 | 252 / 85 | 254 / 86 |
| E2 | none / none | 1,898 / 140 | 846 / 56 | 1,090 / 84 |
| E3 | 808 / 612 | 227 / 84 | 168 / 56 | 168 / 56 |
| E4 | 114 / 84 | 84 / 84 | (too few) | 84 / 84 |

"None": no 25-stack botnet of any size. Each stack holds at most 0.9/M of the window, so
the ratio c/n ≥ ρ·b fails for every prevalence above 0.9/(ρM), 1.2% for M = 25. On the
four endpoints the fingerprints past that limit are the 4 to 28 most common (E1 23, E2
26–28, E3 13–15, E4 4–5), and they carry 86–94% of the origins: a bot hiding behind any
of them cannot be scoped by a 25-stack test, which is why the adversarial botnet (the 25
most common fingerprints) is missed on E1 and E2. The shared floor of Table V under the
beta-binomial is now computed at the tail's correlation; it was the binomial-tail value
before, a lower bound, and changes only on E4 (56 → 84, and 2.8 → 4.2 windows in sample,
2.95 → 4.4 cross-fitted).

**The held-out day, conditional on the gate.** The gate opened in 3 of the day's 1,152
clean windows (0.26%, against 3.0% on the test days), and the binomial scope misfired in
2 of them, against 5 of 168 on the test days (P[Bin(3, 5/168) ≥ 2] = 0.003). The
unconditional count (2, P = 0.27) is consistent because the gate was quiet. The protocol's
metric 3, flash crowds of 100 users, is 1.1% on the held-out day; the paper now reports it.

## 19. What the round-13 review verified, and what changed

The review of the round-13 paper checked 30 claims against these files. We
re-verified each defect it reported before changing anything.

**The dependence of gate and scope, tested.** Under independence the joint misfires
are a sum of many rare window events, so their count is close to Poisson with the mean
of section 18. The tail P[X ≥ observed]:

| Configuration | In sample | P | Cross-fitted | P |
|---|---|---|---|---|
| Binomial | 5 against 3.5 | 0.27 | 6 against 3.2 | 0.10 |
| Beta-binomial | 22 against 7.5 | 1.4 × 10⁻⁵ | 6 against 1.8 | 0.011 |
| Calibrated z-score | 20 against 11.9 | 0.020 | 13 against 4.6 | 0.001 |

The paper now claims the dependence only where it is significant.

**The endpoint-day bootstrap is too coarse.** With five days per endpoint it gives the
binomial configuration 0.02–0.16%, narrower than the exact 0.03–0.21%, and the
cross-fitted beta-binomial a lower bound of 0% with six misfires observed. The paper
now reports the exact interval, says it assumes independent windows, and states the
clustering (13 of each on one day of the console). `cluster_ci` stays in the artifact.

**The fleet share against the paper's own collateral metric.** On the design days
(`fleet_profile.json`, block `design`), rate × median collateral per clean window is
0.0028% for the 0.5% share and 0.070% for the chosen 5%, about 25 times heavier, and
the 0.5% share stopped more of 100 attackers on new stacks (44.6% against 30.9%). The
protocol chose by misfire count (5 against 6 for the base rule, 12 to 16 for smaller
shares). The choice stands, since changing it now would be post hoc, and Table II's
note and Appendix E disclose it.

**Other verified fixes.**
- The floor bands are in the body: the headline shared floor (254 on E1) is that of the
  rare tail. Ranks 36 to 100 need 743 attackers, and ranks 11 to 35 are never named on
  E1 and E2 (`floor_bands.json`).
- Section VI said "about three misfires per endpoint and day", where the configuration
  has 0.25. "Every calibrated configuration" named a floor the z-score does not have.
- "The gate fires on the same windows as Ω in 86–99.6%" counted the windows where
  neither fires. Among clean windows where either fires they coincide in 136 of 181
  (`volume_baseline`), and the paper now says "agrees with Ω on 86–99.6% of windows".
- `relatedByTLSFingerprint` counts exact-JA4 classes. The near-variant match of
  Appendix A is specified but not exercised, since it is not an equivalence. The OWL
  comment said "equal or near-equal" and now matches.
- The Layer-7 detectors sentence cited a categorization of slow DoS attacks, and now
  cites the survey.
- The measurement note removed the point-of-presence volume but the paper cites the
  extract's size. The note now carries it (6.33M TLS requests).

**Fig. 2 of the paper** (`fig6_stops.png`, `make_figures_en.py`) draws the `sweep`
block for the binomial configuration: per endpoint, the gate rate, the scope alone and
the configuration on new and shared stacks, against attackers per window. It replaces
the numeric part of the "What the configuration stops" paragraph.

**Contribution (iii)** is now the exchange gap. No exchange standard has a JA4 property
in its core vocabulary: STIX 2.1 carries one only in an extension that MISP's importer
drops, and DOTS and Flowspec filter network and transport fields. The ontology stays as
the specification the count query is compiled from.

`make audit`: 262 checks, 0 mismatches.

## 20. Round 15: a full read for coherence and fairness

No new analysis. The text now states what the tables already held, where a reader would
otherwise draw a more favorable conclusion than the data supports:

- **Generated traffic, 100 stacks**: the z-score (80.4%) and the unseen filter (88.1%)
  beat the test (38.6%). The text said only that a pooled profile restores the test.
- **The learned baseline at 1% FPR** (`symbolic_detector.json`, `rf_recall_fpr1`,
  `rfp_recall_fpr1`): 66.8% at 25 stacks, 94.6% with the profile, against the test's
  90.3% at zero FPR. The table forces it onto the test's operating point (FPR 0).
- **Cross-M**: the AUC it falls from is the cross-M protocol's own same-M value
  (0.95–0.995, other seeds), no longer the ablation's 0.93–0.98.
- **Flash crowds**: requiring the test removes false alarms only for generated crowds,
  drawn from the profile's own mix. On production the configuration fires on 22.2% of
  1,000-user crowds, and what those misfires block was not measured.
- **Beta-binomial on the console, in sample**: 1.3% of clean windows and 74.4% of
  1,000-user crowds (16.1% cross-fitted). Its cross-fitted shared floor is below the
  binomial's cross-fitted floor on every endpoint (167/168/140/84 against
  286/1,041/227/114).
- **WAF surges**: "near chance". On the API the binomial configuration catches 2 of 28
  against 0.35 expected (Poisson P = 0.049).
- **Disclosures**: the first cross-fit design was dropped after its results were seen,
  and the uncalibrated z-score of Appendix E runs behind the Ω gate.
- **Recommendation**: the binomial configuration is recommended as tested, although its
  gate is the bottleneck on E1, and the post hoc evidence favors the cross-fitted
  beta-binomial.

The table notes are cut to two lines each. Their definitions moved to Section IV (false
alarms, collateral, window counts, the 90% cap of one-off fingerprints, the shared
mode) and to the text of V-A and V-B. `make audit`: 265 checks, 0 mismatches.

## 21. Round 17: the trigger, Section V in three findings

The round-16 review (the acceptance bar of NOMS rather than its best papers) ranked
first a re-evaluation of the trigger on the existing data. `production_tables.py`
now computes a **seasonal gate** beside the distinct-origin gate, from the
calibration windows the per-window CSVs already hold (no detection rerun): the ratio
of a window's distinct origins to the median of the same hour of day (UTC) over the
fold's calibration windows, firing past the 99th percentile of that ratio on the
calibration windows, never below 1. Every existing key of `production_tables.json`
is unchanged (checked value by value); the new keys are `union|seasonal` (and the
other scopes under it), `gates_clean.seasonal`, and `gate_seasonal` /
`blocked_seasonal` in `sweep` and `stealth_E1`.

| Busiest endpoint (E1), binomial configuration | Origin gate | Seasonal gate | Scope alone |
|---|---|---|---|
| False alarms, test days | 0 | 0 | 0.97% (0.83% cross-fitted) |
| Tenth-size botnet stopped, test days | 11.8% (0.6–37.2% by day) | 20.4% (10.0–44.7%) | 89.6% (89.4–89.8%) |
| Whole-window botnet stopped | 70.8% | 90.0% | 90.0% |
| Tenth-size botnet, held-out day | 0.0% | 15.3% | 89.7% (0 of 288 false alarms) |

The seasonal gate alone fires on 3.0% of clean test-day windows, as the origin gate
does, and it lifts the binomial configuration's false alarms on the web console from
0.28% to 2.64% (under the cross-fitted beta-binomial it does not: 0.21%). The scope
alone meets the 1% budget on E1 only; on E2 to E4 it fires on 1.5–4.4% of clean
windows. The paper (V-C, VI) proposes a trigger chosen per endpoint for the
pre-specified test, and says the analysis is post hoc.

**Section V in three findings.** V-B: false alarms and the calibration floor. V-C,
new: what is stopped, the trigger decides (Figs. 2 and 3, the other triggers). V-D:
what the evidence supports (the held-out day, the post hoc analyses, the boundary,
this WAF's verdicts).

**Text fixes the review verified**: the "88% of a named botnet" wording (it counted
the one-off tenth no scope names), the learned model's operating point on the
adversarial row (23.4% at 1% FPR), the gate/Ω agreement (136 of 181), median
collateral throughout, p1 as a share of requests, the ratio limit as an expectation,
Table II's held-out column, Table V's note, the conclusion's rate, the profile-size
sensitivity of Table VII (68.9% and 80.0% with a one-run profile), and the parameters
fixed before production data (ρ, k_min, τ's percentile, the 25-stack botnet).

**References** (36): RFC 9761 (the IETF ACL model matches TLS client parameters since
2025, but names no fingerprint, and DOTS defines its own filters), DDoS-Shield,
Xie and Yu, and Lakhina et al. DDoS-Shield decides which sessions to penalize and at
what cost, so the introduction's "none says which clients to block" became "none
scopes the block by application-client fingerprint". To keep 8 + 4 pages, the
window-sensitivity paragraph of App. D and the fleet share's secondary held-out
results left the paper (both remain in sections 11 and 12 of this README).

`make audit`: 258 checks, 0 mismatches.

## 22. Round 18: the trigger table, flash-crowd collateral, floors by stack count

The round-17 review (the acceptance bar) found one claim false: Section VI said the
scope alone stays within the budget on the busiest endpoint for the binomial *and* the
beta-binomial, but the beta-binomial's scope alone fires on 2.08% of E1's clean
test-day windows in sample and, cross-fitted, on 5 of the held-out day's 288 (1.74%).
It also found an option the paper did not report: the cross-fitted beta-binomial
behind the seasonal gate misfires on 4 of 5,643 test-day windows and none of the
held-out day's 1,152, and stops 20.4% of E1's tenth-size botnet (15.3% held out),
against 11.9% behind the origin gate. Round 18 rebuilds the recommendation on a table
of the scope behind each trigger (Table VII), from values already in
`production_tables.json`:

| Trigger | Background | FA E1 test / held | FA E2–E4 highest, test / held | E1 0.1× stopped, test / held | Coll. |
|---|---|---|---|---|---|
| Origin gate | binomial | 0.00 / 0.00 | 0.28 / 0.69 | 11.8 / 0.0 | 32.9 |
| | beta-binomial, cross-fitted* | 0.14 / 0.00 | 0.28 / 0.00 | 11.9 / 0.0 | 2.0 |
| Seasonal gate* | binomial | 0.00 / 0.00 | 2.64 / 0.69 | 20.4 / 15.3 | 35.2 |
| | beta-binomial, cross-fitted | 0.07 / 0.00 | 0.21 / 0.00 | 20.4 / 15.3 | 16.9 |
| Scope alone* | binomial | 0.97 / 0.00 | 4.38 / 1.04 | 89.6 / 89.7 | 32.6 |
| | beta-binomial, cross-fitted | 0.90 / 1.74 | 1.46 / 1.39 | 89.7 / 90.1 | 6.6 |

In %; Coll. is the median over test-day misfires, all endpoints; * post hoc. The
binomial scope alone on E1 sits at the budget: 14 of 1,440 (95% interval
0.53–1.63%), rising by day 0, 0, 1, 5, 8, and it needs the fleet exemption (92 of 1,440
without it). Section VI now proposes, for the pre-specified test, the cross-fitted
beta-binomial behind the seasonal gate as primary and the scope alone on E1 as
secondary, over a weekly cycle with an external timestamp.

**Flash-crowd collateral** (`production_tables.py` now reduces it): the filters the
binomial configuration installs on 1,000-user crowds block a median 4.3% of the
window's clients, crowd included (90th percentile 20.6%; 7.1%, 18.6% and 2.7% on E2
to E4), against 32.9% for clean-window misfires. On the held-out day E4's 1,000-user
crowds trigger the configuration in 97.2% of windows (34.1% on the test days), 98.2% of
the 280 firings on one fingerprint far more common among that day's clients than in
the profile, at a median 1.1%. The new key `flash_concentration` holds that share per
endpoint and block (a count; no fingerprint leaves the drive). Every earlier key of
`production_tables.json` is unchanged, checked value by value.

**Floors by stack count** (already in `floor_deployed`): on shared stacks E1's floor is
50, 254 and 1,026 attackers for 5, 25 and 100 stacks (2%, 8% and 34% of its window),
and 0.7–2.8, 4–19 and 24–106 windows on the small endpoints. The floor grows faster
than linearly on E2 and E3, so the paper says only that it grows with the stacks.

**Text fixes the review verified**: Listing 2 was cited as a STIX bundle (it is the
JSON-LD chain); the WAF ranges now include E2 (implied floor 70–88%, random pick
10–63%); the unsupported "one JA4 per browser" clause left (the FoxIO post does not
say it); the introduction's "none scopes by fingerprint" became "no published method"
(Table I lists a commercial JA4 product); "recommended" became "pre-specified"; 4 of the
5 misfires are on the console; the distinct-origin gate alone fires on 5.4% of E1's
clean windows; the held-out day passed mostly because its gate was quiet (3 of 1,152,
0.26% against 3.0%); the ratio limit is stated for ρ = 3; the known fleets carry about
7% of E1's profile; the exchange gap is "in its core vocabulary" throughout.

**Space.** Ω is defined in words in Section III-B, with Eq. 1 and the weights moved to
Appendix A; Section III-E is shorter; Listing 1 (the SWRL rule and SPARQL aggregation)
left, and Appendix D describes the aggregation in words; Appendix B is shorter. Fig. 4's
legend no longer overlaps its axis label. Body ends on page 8 (right column), 12 pages,
abstract 250 words.

Not done: m7 (the fleet-share comparison uses the median collateral, Section IV-B's
expected share the mean; the mean would need `fleet_selection.py` rerun on the protocol
record) and m16 (when the rolling split was fixed is not recorded in the repository).

`make audit`: 266 checks, 0 mismatches.

## 23. Round 19: a scope-bound review, the unseen filter in the trigger table

From round 19 the reviewer judges what the paper delivers against what it proposes
(its abstract and three contributions): class A for blocking issues within that scope,
B for text, table or figure fixes that need no new analysis, and C for new work, which
does not count in the verdict. Round 19's review: borderline, 3/3/2/4, one class A item.

**A1, verified.** Table VII credited the post hoc gains on new stacks to the calibrated
test, but the unseen filter alone, which reads no level and no fleet list, gives the same
stops on new stacks under every trigger, with fewer false alarms and fewer flash-crowd
firings (`unseen|seasonal`, `unseen|none` in `production_tables.json`):

| E1, tenth-size botnet | Misfires, test / held out | New stacks, test / held | Shared, test | Fl. 1k |
|---|---|---|---|---|
| Seasonal gate, cross-fitted beta-binomial | 4 of 5,643 / 0 of 1,152 | 20.4 / 15.3 | 15.1 | 10.9 |
| Seasonal gate, unseen filter alone | 0 / 0 | 20.4 / 15.3 | 0.0 | 3.4 |
| Scope itself, binomial with known fleets | E1 0.97%, E2-E4 up to 4.38% | 89.6 / 89.7 | 61.1 | 22.4 |
| Scope itself, unseen filter alone | E1 0.28%, others up to 0.42% / up to 0.35% | 89.6 / 89.7 | 0.0 | 3.4 |

What the test adds is the shared stacks. Table VII now has the unseen-filter rows and
the shared and flash-crowd columns; V-C, VI, the abstract and the conclusion say where
each gain comes from; the next test takes the unseen filter as its own trigger as the
baseline, against the cross-fitted beta-binomial behind the seasonal gate (its gain on
shared stacks) and the binomial scope with known fleets as its own trigger.

**B items applied**: "pre-specified" no longer qualifies test-day rates (the Fig. 3
legend reads "in protocol"); the seasonal gate keeps the console within the budget
under one of the four calibrations only (2.64%, 2.57% and 2.01% under the others); 95 of
the held-out day's 288 E1 windows misfire without the fleet exemption; the cross-fitted
beta-binomial's lower floor holds for the rare tail only (E1 ranks 36-100: 949
attackers against the binomial's 743); the introduction's novelty sentence is one
claim; cross-fitting is defined in IV-B; Fig. 3's caption says the small endpoints
dominate the pooled cell and marks the cross-fitted points post hoc; the held-out
diagnostics beyond the protocol are labelled; the ρ sensitivity is stated for the base
rule; the boundary paragraph folded into V-B.

Body ends at the bottom of page 8 (the Acknowledgment opens page 9), 12 pages, abstract
250 words. `make audit`: 266 checks, 0 mismatches. The rounds of review stop here, at
the user's choice.

## 24. Round 21: the round-20 review's B items

The round-20 review (scope-bound, as in round 19) found **no class A item**: all 81 cells
of Table VII and the claims of the abstract, the contributions, Tables III-VII, Section VI
and the conclusion match the artifact. Borderline leaning weak accept, 3/4/2/4. Round 21
applied its B items and cheap polish, each checked against the result files:

- **B1, the unseen filter's parity is scoped.** It holds for stacks of at least k_min
  origins, as in E1's tenth-size botnet (about 11 attackers per stack). Below that the
  test names new stacks the filter cannot: of 100 attackers, the cross-fitted
  beta-binomial as its own trigger stops 57-84% per endpoint against the filter's 43%
  (`xfit_od` and `fleets`, `union|none` and `unseen|none`, `new:A100`). V-C, VI, the
  abstract and the conclusion now say the test adds shared stacks and smaller new ones,
  and the next test covers 100 attackers as well as a tenth of the window.
- **B2** Table VII's note states its bases (FA per endpoint, Fl. 1k and Coll. pooled,
  E1's tenth-size botnet); "Scope itself" is now "No gate". **B3** the abstract's 0.1%
  is "on the days it was chosen on"; the conclusion adds that the scope misfired in 2 of
  the 3 held-out windows where the gate opened and marks its seasonal-gate sentence post
  hoc. **B4** the "Alone" column of Tables IV and VI is "No gate"; the ratio limit has its
  own paragraph; the floors by stack count and by profile rank moved to Appendix E, with
  two numbers left in the body. **B5** Section VI says the compiled query reproduced the
  origin and /24-pair counts and the JA4 pair counts where the WAF blocked no client
  (`compile_production_check.json` note); App. F gives medallion 3.0.0 and misp-stix
  2026.9.16. **B6** Fig. 3 adds the unseen filter as its own trigger and the cross-fitted
  point of the beta-binomial scope alone. **B7** the binomial scope as its own trigger is
  an option on E1 only, rising by day. **B8** the unseen filter's misfires cluster by day
  (E1 all 4 on one day, the console's 2 on one day, 5 of the API's 6 on another). **B9**
  the WAF comparison names the three profile-relative scopes (the unseen filter's lift on
  E2 is 2.8). **B10** the cross-fitted beta-binomial's floor on ranks 36-100 against the
  binomial in sample: higher on E1 (949 vs 743) and E3 (255 vs 227), equal on E4, lower on
  E2 (509 vs 1,898).
- Polish: "Ω is mostly volume"; the endpoint rule includes 50 calibration windows; the
  ablation's 30 seeds; Table V's n0 header; the OWL comment no longer cites a
  contribution number. To stay at 8 + 4 pages: App. C's explanation-validation and
  vocabulary-tail paragraphs, App. B's first sentence, three lines of Listing 1 and some
  App. A implementation details left; Figs. 2-4 are 0.1-0.15 in shorter; the unverified
  "an hourly profile did not help" left App. E.

Not applied: OpenC2 in the exchange survey (not verified, would add a reference); the
Acknowledgment still opens page 9's left column (the body ends on page 8), which the
reviewer asks to confirm against the CFP. `make audit`: 266 checks, 0 mismatches.

## 25. Round 23: the round-22 review

The round-22 review (scope-bound) found one class A item, introduced by round 21's own
fix: the text said the test's gain lies on "shared stacks and smaller new ones" for the
cross-fitted beta-binomial behind the seasonal gate, but on E1 that configuration stops
3.9% of 100 new-stack attackers (2.8% held out) against 43.2% for the unseen filter as its
own trigger, and 20.4% against 89.6% of the tenth-size botnet, because the seasonal gate
opens in 7.4% of those windows. Its gain on smaller new stacks is on E2-E4 only (53.4,
64.6, 84.2% against about 43%). V-C, VI, the abstract and the conclusion now say so; the
abstract names the cross-fitted beta-binomial as the source of the 15% on shared stacks.

B items applied: the conclusion's 0.1% is on the days the configuration was chosen on;
the floor ratios are medians of the daily ratios; the rank-band caveat names the
in-sample binomial; the compiled-query check is "JA4 pair counts", run in the
operator's log store with only its counts in the artifact (`compile_counts.py`'s
`compare_export` covers origins and /24 pairs); the configuration deployed now "stops
few small botnets there, none on the held-out day"; the unseen filter's parity holds by
construction, being part of the union; App. E gives Table VII's held-out shared and
flash-crowd cells; the WAF surges are counted (at most 2 of 38 on the API and SSO).
Polish: "None retains", Omega's 91% is of a campaign's cluster, App. F's "one command"
is for generated traffic, Fig. 4 has y ticks every two decades, App. E marks its post hoc
numbers. Space: Table VI keeps its binomial rows (the beta-binomial rows were post hoc;
the text keeps the 19 of 22 console misfires and the 74.4%), the uncited Table VIII is
one sentence in App. E, App. C's lean baseline left. Body ends on page 8, 12 pages,
abstract 250 words. `make audit`: 259 checks, 0 mismatches.

## 26. Round 25: the round-24 review and the NOMS 2027 rules

The round-24 review (scope-bound) found one class A item, an external fact: "no exchange
standard has a JA4 property in its core vocabulary" is false for OCSF. Checked at the
source, the OCSF CHANGELOG and the schema's main branch (1.10.0-dev):
- v1.3.0 (1 August 2024) added the `ja4_fingerprint` object and put
  `ja4_fingerprint_list` in the base network event class (#834);
- v1.4.0 (31 January 2025) added it to the `evidences` object of findings (#1244; the
  review's "v1.6.0" is wrong);
- in the schema JA4 appears only in `events/network/network.json`,
  `objects/evidences.json` and `objects/ja4_fingerprint.json`. The remediation classes
  carry D3FEND countermeasures and nothing over JA4, and `firewall_rule` has only
  free-text match fields.

The claim is now scoped to the standards examined in the abstract, contribution (iii),
Section VI and the conclusion. STIX 2.1, DOTS and Flowspec have no JA4 property; OCSF
records JA4 but defines no filter or remediation over it. The new reference is
`ocsf2024schema`, so 37 are cited. Section VI's remedy is now a JA4 match in the DOTS
filters and a JA4 property in STIX.

NOMS 2027 (CFP and submission guidelines read 27 September 2026): 8 pages of main text,
self-contained, plus references and an optional appendix, 12 pages in total. The PDF's
author list must match EDAS (no blind review is stated), and submission closes on 9
November 2026. The Acknowledgment is neither references nor appendix, so it now ends on
page 8 (B8).

B items applied:
- B1: the abstract's post hoc sentence puts the 90% on the busiest endpoint and names the
  beta-binomial as the alternative, 15% on shared stacks and 20% on new ones there;
- B2: IV-B says that of four fleet shares only 5% had no more false alarms than the base
  rule on the design days, and gives both sides of the trade-off (0.5% blocked about 25
  times fewer legitimate clients and more of a 100-attacker botnet);
- B3: Table IV marks its held-out cells beyond the protocol (No gate, Fl. 1k, the
  z-score), IV-B calls "No gate" a diagnostic, and App. E marks the scope as a trigger
  post hoc;
- B4, in part: V-C names the four calibrations of the seasonal gate and the 43% (the
  unseen filter as its own trigger), and says the unseen filter matches the union on new
  stacks because it names each such stack;
- B5: the unseen trigger's misfires cluster by day, and VI's "within the budget
  everywhere" is pooled over the days;
- B6 and B7, in part: the small endpoints' fallback applies below the floor, the
  configuration is deployed on the busiest endpoint, and VI's "under a tenth of its
  window" is for new or rare shared stacks;
- B10: the KLAGE comparison is uncontrolled, against its published result;
- polish: "never on the 4 to 28 most common", "matches or beats the test".

Not applied: B9 (a legend table), a Fig. 3 mark for the z-score, splitting App. E's
paragraph and a new reference on JA4 bot detection.

Space came from Section II's closing paragraph (it repeated the introduction's gap),
III-C's WAF sentence (IV-A states it), "A single source is left to volumetric
detectors", V-A's flash-crowd sentences, VI's TAXII detail (App. F keeps it) and a shorter
Acknowledgment. The body and the Acknowledgment end on page 8, the references open page
9, 12 pages, abstract 249 words. `make audit`: 259 checks, 0 mismatches.

## 27. Round 26: the round-26 review

The round-26 review (scope-bound) found no class A item and answered "ready to submit:
yes", borderline leaning weak accept, 3/4/2/4, 60-75th percentile. Only its B1 (the
readability of V-C, V-D, VI and App. E) would move it to weak accept; that item is left
to the user. The cheap items were applied:
- B4: the OCSF reference is version 1.4.0 (January 2025), and its note says JA4 is in
  network events since 1.3.0 and in finding evidence since 1.4.0 (the key is now
  `ocsf2025schema`);
- B7: "The operator's WAF verdicts cannot serve as labels";
- B8: fleets "raise" the floor (on E4 most of it is structural: 56 attackers at the
  0.01 cap, 84 calibrated), and the ratio limit holds "in expectation" in the abstract,
  contribution (ii) and V-B's heading;
- B2: Table VII's note defines "No gate: scope as trigger";
- B3: V-C no longer cites Fig. 3 for the triggers, which it does not show; V-D cites it
  for the cross-fitted arrows;
- B6: the binomial configuration is deployed on every endpoint, with the fallback below
  its floor; the baseline and the seasonal-gate arm are marked post hoc; the baseline's
  parity on the small endpoints is stated (every Table VII scope stops 90.0% of 1,000
  new-stack attackers on E2-E4 under every trigger, test days and held-out day; the base
  rule and the cross-fitted z-score stop less there and are not in Table VII);
- B5: a new fingerprint that persists enters the profile only through an operator;
- B9: test-day windows without an injected botnet (clean) are taken as attack-free, so a
  real attack there would count as a false alarm;
- B10: App. F says pair counts constrain the class sizes the scope tests but do not
  identify them;
- polish: "Pooled over the endpoints", "the floor is computed at their median
  prevalence", the survey's category, "on new stacks on every day", the TAXII server
  keeps all but the extension definition, cross-fitting post hoc at its first mention,
  ECH hides the inner ClientHello.

Space came from the CICIDS2017 session counts (now in App. B), the z-score formula (now
in words), III-A's list of what the attacker randomizes, V-A's fallback clause, V-C's
0.97% (Table VII prints it) and E1 collateral (now in App. E), and VI's cost sentence
(App. D keeps it). Table VII's note stays at two lines. The body and the Acknowledgment
end on page 8, 12 pages, abstract 250 words. `make audit`: 259 checks, 0 mismatches.

## 28. Round 27: B1, readability

At the user's choice ("Commit + B1 e fim"), round 26 was committed and one readability
pass followed, the round-26 review's B1, with no new data:
- terms are marked where they are defined: the *budget* (III-C), *new*, *shared*,
  *adversarial* and *tenth-size* (IV-A), *in sample* (each calibration day judged against
  a profile that includes it) and *cross-fitting* (IV-B), the *seasonal gate* and the
  *scope as its own trigger* (No gate) in V-C;
- V-C's "Other triggers" is in two parts: the triggers, then "What the unseen filter and
  the test add";
- VI's recommendation reads as (i) *Now*, the binomial configuration on every endpoint
  with the fallback below its floor, and (ii) *Next*, the pre-specified test of the post
  hoc triggers, its baseline and its arms;
- App. E's single "Details of Section V" paragraph is three, "Details of V-B", "V-C"
  and "V-D".

Space came from numbers the tables print (Table III's learned-model recall with the
profile, Table V's cross-fitted beta-binomial floors), V-A's "15 campaigns" and its
stealth-mode clause, a shorter RFC 9761 sentence in VI, App. A's near-variant
parenthesis, and one App. E sentence merging the pooled and held-out blocked shares. The
body and the Acknowledgment end on page 8, 12 pages, abstract 250 words. `make audit`:
259 checks, 0 mismatches.

## 29. Round 28: the final review

The final review (scope-bound, round-27 text) found no class A item: weak accept, 3/4/2/4,
confidence 4, 65-75th percentile, "clears the acceptance bar, narrowly", ready to submit.
Its one-line items were applied after checking each against the result files:
- B1: "it alone was tested" (a round-27 regression) is now "behind the distinct-origin
  gate it alone was tested", since the base rule was also in protocol, behind the Omega gate;
- B2: on the busiest endpoint a botnet that leaves the gate shut meets neither filter nor
  fallback;
- B3: on new stacks too small for the filter, the cross-fitted beta-binomial adds on the
  small endpoints and the binomial only on the single sign-on (on E1-E3 its new:A100 cells
  equal the unseen filter's exactly, under every trigger, test days and held-out day);
- B4: the adversarial botnet is stopped on no fingerprint of E1 and E2, where nearly all
  25 lie past the limit, but 73.5% of 1,000 on E4;
- B6: the abstract says the unseen trigger stops none on shared stacks;
- B7: App. F says the protocol named JA4 class sizes and the check compared pair counts;
- B8: V-C drops the exact interval of the E1 rate (the day counts stay; the endpoint-day
  bootstrap gives 0.07-2.01%);
- polish: {JA4} braced in the OCSF note, "every row the learned model runs", 2.2-3.4%
  collateral, the measured curve's head and top ten, "its typical stack", "the tenth-size
  botnet", "more common that day" with 98.2% of 280 firings in App. E, App. E's post hoc
  marks, the all-client profile for the console's surges.

Space came from V-D's in-sample beta-binomial floors (Table V prints them), V-D's closing
WAF sentence, the next test's size sentence folded into (ii), a shorter conclusion, and in
the appendices the one-run-profile sentence (its audit check went with it), "Dataset
breadth" folded into "Coverage", and a shorter seeds sentence. 12 pages, the
Acknowledgment ends on page 8, abstract 250 words. `make audit`: 258 checks, 0 mismatches.

## 30. Round 29: clarity

The user asked for paragraphs and blocks that connect naturally and for the most common
words the language allows, since the content is already complex, to lift the clarity score
of 2. The reviewers had called the text dense: many numbers per sentence, many coined terms
and few transitions.
- Sections I to VII were rewritten sentence by sentence with one idea per sentence and
  plainer words ("modal" is defined once as the alarm's most common fingerprint,
  "canonical" is "default", "headroom" is "spare capacity"). Each subsection opens from
  where the last one landed. Every qualifier and number was kept, except the numbers
  Table III already prints in V-A.
- Table VI (per endpoint) left the paper: Fig. 2, Table V, the trigger table (now
  Table VI) and the text carry its content, and its values stay in the study guide. That
  paid for the transitions.
- Fig. 3 has one x label for both panels ("false alarms (% of clean windows)") just under
  the ticks, and the legend sits clear of it. Fig. 4 is drawn at the width it prints
  (3.45 in, fonts of about 7 pt), with a two-column legend below the axis label; it was
  drawn 7 in wide and scaled to half. Fig. 2 is 0.1 in shorter to pay for Fig. 3.
- The appendix paid for Fig. 4: App. A's lead-in to the list, App. C's generic sentence
  on noisy extraction, and a shorter App. D.

12 pages, the Acknowledgment ends on page 8, abstract 250 words, no sentence over 45
words. `make audit`: 253 checks, 0 mismatches (the Table VI row checks left with the
table; App. F now says "about 250").

## 31. Round 30: the round-29 review

The round-29 review (scope-bound, the text after the clarity pass) found no class A item:
weak accept, 3/4/3/4 (clarity up from 2 to 3), confidence 4, 70-80th percentile, ready to
submit. At the user's choice its B1-B4 were applied, each number checked against the
result files:
- B1: on the console, where both held-out false alarms fell (a median 41.2% of the
  window's clients), a challenge may be the safer first response;
- B2: on the small endpoints a botnet of one median window opens the gate in only
  14-33% of windows (32.2, 32.8 and 13.7% on E2-E4), and a botnet that leaves the gate
  shut meets neither filter nor fallback on any endpoint;
- B3: as its own trigger the cross-fitted beta-binomial also adds on E1 (57.6% against
  43.2% of 100 new-stack attackers), and the next test leaves it out because it fired in
  1.74% of E1's held-out windows (5 of 288);
- B4: "what an operator would deploy" and "the evaluation places the scope behind the
  operator's WAF", since the run is offline.

Space came from the conclusion (the standards sentence and a shorter generated-traffic
sentence), a shorter ECH sentence, VI's sentence on the busiest endpoint (the new (i)
covers it) and Fig. 2 at 2.5 in. 12 pages, the Acknowledgment ends on page 8, abstract
250 words. `make audit`: 253 checks, 0 mismatches. Not applied: B5 (four denser
sentences), B6 (a sentence on the diagnostics computed after the held-out day) and the
polish.

## 32. The held-out block, fixed before its export

New production data enter the paper only as a pre-specified test,
`results/heldout_block_protocol.md`, committed and pushed before any day of it is
exported. The block is the 14 days after the paper's data, 2026-09-26 to 2026-10-09,
each calibrated on every earlier day, with the paper's nine days as history only. A
first draft chose the 30 days before the paper's data, but the log store keeps only 8
to 12 days and none of them was left; nothing was read.
- `make rule-production-block` runs the eight runs that `production-tables` reduces, on
  the block's own data directory (`$(PRODDATA)/block2`, with copies of the nine days),
  so no earlier target reads the block. `make production-tables-block` reduces them.
- `production_tables.py --endpoints-from` takes the endpoints and their order from the
  paper's run, so the block keeps the paper's E1-E4 even if volumes shift or a fifth
  host qualifies on every block day. Given the paper's own run, it reproduces
  `results/production_tables.json` byte for byte.

## 33. The user's held-out wording, back to 12 pages

The user reworded the held-out day in three places. The abstract says "consistent with the
test-day behavior but provides limited additional evidence", Section V's lead-in says "the
held-out evidence is evaluated separately", and V-D replaces "This test is weak" with the
few gate openings limiting the inference. The edits pushed the Acknowledgment to page 9, so
the added length came out of our own text:
- in the abstract, "25 new stacks", and "median", "TLS" and "ones" dropped;
- in Section VI, a table reference and an appendix reference that repeated within their
  paragraphs.

V-D's new sentence was fixed for case, `1\,152` and `$P$`, and split under 45 words. 12
pages, the Acknowledgment ends on page 8, abstract 250 words. `make audit`: 253 checks, 0
mismatches, with the phrases updated to the new wording over the same numbers.

## 34. Round 31: the abstract, for a first-time reader

Read as by someone who has not read the paper, the abstract used terms before defining
them: the scope was never defined, "gate" came two sentences before the gate, "test-day
behavior" pointed at days the abstract never names, and "4 to 19 windows" read as a count.
Not saying that the production botnets were injected left room to read them as real attacks.
The rewrite keeps 250 words and the same 26 lines, and every sentence stays under 41 words.
- The scope is "the TLS fingerprints to block", and the gate is "a gate on distinct
  origins", both given before they are used.
- "Once the botnet spans five TLS stacks" removes the double reading of "legitimate traffic
  from five stacks on".
- Each misfire blocks "a median third of the window's clients".
- Sizes are in typical windows, and the botnet is "injected".
- The gate sentence gives the cause: the gate seldom opens, so the configuration stops 12%.
- The post hoc arm is "triggering on unseen fingerprints alone".
- The user's held-out sentence now reads "consistent with that rate".

To make room, three items left the abstract and stay in the body, where the audit now
checks them: the WAF sentence (V-D's heading), the ratio limit (V-B) and the beta-binomial's
20% on new stacks (Table VI). 12 pages, the Acknowledgment ends on page 8. `make audit`: 253
checks, 0 mismatches.

## 35. Round 32: paragraphs of even length

The main text had paragraphs from 21 to 318 words (median 132), with twelve over 190. In
the appendices they ran to 300. Long paragraphs were split where the topic changes, with
no word changed at the split:
- the introduction's contributions;
- the threat model's TLS-stack assumption;
- the botnet's spread over stacks;
- the five choices made on the test days;
- the table columns beyond FA and collateral;
- the floor's growth with stacks and rank;
- "(ii) Next";
- the conclusion's evidence;
- in the appendices, V-D's details (three parts), known fleets against the scope as a
  trigger, and the held-out day's protocol.

K's short paragraph joined the controlled evaluation, and V-A's one-sentence lead-in joined
the paragraph it leads into. One sentence moved inside its paragraph: the rate times the mean
collateral now follows the collateral it multiplies.

Each split costs about a line, so short last lines paid for them. The trims were "each
staying below per-source thresholds", "five-minute" (already defined), "that" and "imposed
on", the table pointer folded into "Pooled over the endpoints (Table IV)", "in the first
30 s", "legitimate" in "a more concentrated population", "has too few pairs" and "on test
and held-out days".

Now the main text runs from 21 to 196 words (median 120), with three paragraphs over 190.
The three short ones are section lead-ins. The appendices run up to 202 words. 12 pages,
the Acknowledgment ends on page 8, no sentence over 45 words. `make audit`: 253 checks, 0
mismatches, with three phrases updated to the trimmed wording.

## 36. Round 33: the abstract says what, the contributions say less

At the user's request, the abstract now states what was done and found, not how, and it
leaves the reader wanting the details. The mechanism is named once as "a calibrated
statistical test over the TLS fingerprints of an endpoint's clients". The binomial
background, the profile, the gate, the unseen filter, the beta-binomial, the seasonal
gate and cross-fitting all stay in the body. Four numbers remain: 39%, 90%, 0.1% and "a
median third". Each qualifier stays, in a shorter form: on generated traffic, with no
observed collateral, on the days it was chosen on, injected, post hoc, and "no exchange
standard we examined ... in its core vocabulary". The user's held-out sentence stays, minus
the gate clause, which the abstract no longer explains. The closing sentence says what the
results give an operator: where fingerprint scoping pays off and where to fall back to
rate limits or challenges.

The contributions went from 191 to 127 words, one short sentence or two per point. They
drop the 2.2-3.4% shared-stack collateral, the ratio limit, the post hoc triggers and each
standard's gap, all still in V-A, III-D, V-C and VI.

The audit checks each number where it now lives: the floor's 8% and 4 to 19 windows in
V-B, the ratio limit in III-D, the shared-stack collateral in V-A, and the standards in VI.
The abstract's checks read the new phrases over the same data. The main text now ends
with about 8 lines to spare on page 8, and the references start there. 12 pages, abstract
248 words. `make audit`: 253 checks, 0 mismatches.

## 37. Round 34: even vertical spacing

IEEEtran sets `\flushbottom` in two columns. When a column cannot be filled exactly, for
instance because the next heading does not fit at its foot with two lines of text, LaTeX
spreads the remainder over the paragraph gaps. After rounds 31-33 two columns showed it:
page 1 at the maximum badness (10000), where the shorter abstract and contributions left
the right column about a line short of "II. Related Work", and page 5 (badness 3417).
- Page 1: the introduction's first paragraph gets its original wording back, "each sending
  too little to cross any per-source threshold", and the column fills.
- Page 5: V-A's lead-in is again its own paragraph, like the other section lead-ins, and
  "a more concentrated legitimate population" gets "legitimate" back.

The log now reports no underfull column, against one in commit 52eb7b6. `\raggedbottom`
was tried and rejected: it removes the stretching but leaves page 5's right column about
two lines short and page 4's left one a line and a half short. 12 pages, the
Acknowledgment ends on page 8. `make audit`: 253 checks, 0 mismatches.

## 38. Round 35: contributions and the method paragraph, more direct

At the user's request, each contribution now opens with a label that names it, and one or
two sentences back it up:
- (i) *Profile-relative scoping*;
- (ii) *What calibration costs on real traffic*, where the floor's definition moves into
  parentheses so that it no longer reads as a list item;
- (iii) *A gap in exchange standards*.

The method paragraph now follows the method's two steps: a volume trigger first raises the
alarm, and the test then chooses the scope. It says what the calibration buys (a filter in
at most 1% of attack-free windows) and that the attacker, not "their operator", cannot
cheaply replace the stacks. The contributions check in `make audit` reads the new (iii).
12 pages, the Acknowledgment ends on page 8 with little room to spare, and no column is
stretched. `make audit`: 253 checks, 0 mismatches.

The study guide's section 0.7 now takes each table and figure in turn: the question it
answers, how to read it, a worked reading with the paper's numbers, what to conclude and
what not to.

## 39. Round 36: contributions (ii) and (iii) name what the work delivers

At the user's request, contribution (ii) is now the calibration method and (iii) is the
ontology. (ii), *A calibration method for the scope*, sets the test's level per endpoint so
that it names a filter in at most 1% of attack-free windows, and derives the calibration
floor. The CDN measurements and the held-out day follow as its evaluation. (iii), *A session
ontology as the specification*, says that the ontology specifies the counts and the scope,
that the log store's query is compiled from it, and that a new equality signal needs no
change to the code. The standards gap becomes its supporting finding. (iii) claims
specification only, since Section VI states that the ontology adds nothing to detection.
The method paragraph keeps "Its threshold is calibrated on attack-free windows" and leaves
the 1% budget to (ii), so the two do not repeat each other. The layout is unchanged: 12
pages, the Acknowledgment ends on page 8, and no column is stretched. `make audit`: 253
checks, 0 mismatches, with the contributions check reading the new (iii). The study guide's
three passages on the contributions follow.

## 40. Round 37: contribution (ii) shorter, and no stretched column

Contribution (ii) keeps its label, *A calibration method for the scope*, and now reads:
"We calibrate the test per endpoint to a false-alarm budget of 1% of attack-free windows,
which sets a calibration floor: the botnet size from which it names a typical stack. We
evaluate both on eight days of four CDN endpoints and a held-out day." It is 43 words,
down from 72.

A correction to rounds 35-36. The stretched-column counter added to the build check in
round 34 matched two backslashes and so always printed 0. Rebuilding the saved states
showed that round 35's longer introduction had stretched two columns. Those two to four
extra lines no longer let "V. Results" and its lead-in fit at the foot of page 5's left
column. The heading block jumped to the right column and left the left one short
(badness 5787), which pushed the rest about five lines down. That took the references off
page 8, and the column that ends with the Acknowledgment was stretched as well. Removing
the method paragraph's "Its threshold is calibrated on attack-free windows" (which (ii) now
states), and writing "given as a median" for "which the tables give as a median", lets
the block fit again. The counter now uses `grep -F 'Underfull \vbox'` and reports 0,
confirmed by a direct grep of the log. A trim on page 3 was tried and undone: it stretched
page 4's right column, whose foot is fixed by the footnote. The references start on page 8
again, 12 pages. `make audit`: 253 checks, 0 mismatches.

## 41. Round 38: Figs. 2 and 3 show their point

A read of the figures on their own, without the text, found two problems. Fig. 2 held the
evidence but did not show the problem: nothing marked the gap between what the scope alone
would block and what the configuration stops, and the tenth-size botnet the text quotes had
no place on the axis. Fig. 3 was too dense (eight shapes in three fills). It had no budget
line, and it drew the held-out day's zero rates, which come from a gate that barely opened,
in the plot's best corner.
- Fig. 2:
  - the area between the scope alone and the configuration on new stacks is shaded, and
    labeled "lost to the gate" on E1;
  - an open triangle marks a tenth of each endpoint's median window, next to the filled one
    for the whole window;
  - the scope-alone line is now dark and the gate line light.
  The caption states the shading, including "most of a small botnet on the busiest
  endpoint".
- Fig. 3:
  - it shows the test days only, with the cross-fitted points and arrows;
  - a dashed line marks the 1% budget, so the two scope-alone configurations are seen past it;
  - the held-out day is left to Tables IV and VI, and the caption drops "Zero rates are drawn
    at 0.01%" and the open markers.
  Fig. 3 grew from 2.2 to 2.5 in. The shorter caption had let page 7's right column end
  short of "VI. Discussion" at badness 10000, and the taller figure fills it and is easier to
  read. At 2.3 in and 2.4 in the column still stretched.

No stretched column, 12 pages, the Acknowledgment ends on page 8. `make audit`: 253 checks,
0 mismatches. The study guide's readings of Figs. 2 and 3 describe the new elements. A
formatting slip from round 35 is fixed: five list items had been joined to the line above.

## 42. Round 39: Fig. 2 with two lines

Even with the shading, the user found Fig. 2 hard to read. The problem was the four series per
panel: the gate's rate (a share of windows, on an axis labelled share of the botnet) and the
shared stacks told other stories. The figure now draws only what the scope alone would block
and what the configuration stops, on new stacks, with the gap between them shaded ("lost to
the gate" on E1) and an open triangle at a tenth of each median window. The gate's rate and
the shared stacks stay in the text and Table V, and the one number the text cites from the
figure, 43.2% at 100 attackers on E1, is the dashed line. The new caption is a line shorter,
and page 7 stretched again (badness 10000). Fig. 2 grew from 2.5 to 2.6 in, which fills it
and gives the panels more room. `make_figures_en.py` draws the approved version byte for
byte. No stretched column, 12 pages, the Acknowledgment ends on page 8. `make audit`: 253
checks, 0 mismatches. The study guide's readings of Fig. 2 (0.7, 16.4 and the glossary)
follow.

## 43. Round 40: the review of the current state, and the AI-use disclosure

A scope-bound review of the current state (read-only, no data drive) gave a weak accept: 4/3/4/3/4, confidence 4,
about the 70th percentile. It recomputed a sample of numbers beyond `make audit`, and all
matched. Its only blocking item, A1, was IEEE's rule that AI-generated content be disclosed
in the Acknowledgment. The Acknowledgment now carries the authors' wording: "The authors used
an AI assistant (Claude, Anthropic) to edit text in all sections and to write the figure code.
The authors reviewed and verified all content and take full responsibility for it." The
semicolon of the authors' draft became a full stop, as the paper uses semicolons only in
enumerations. The lines were paid for in Section VI's last paragraph: "an extension the
importer does not map" and "such as a TLS extension". The audit phrase for MISP now reads the
new text. The Section III lead-in was kept, since every section opens with one.

The review's B1-B5 and C1-C6 are listed for the authors' choice:
- B1: the abstract's "calibrated test" on generated traffic, and the gate behind the 0.1%;
- B2: hedge "No published method";
- B3: the botnet spreads over stacks uniformly at random, not evenly, as the generator's
  `rng.choice` and the injector's `rng.integers` confirm;
- B4: the conclusion's "within the budget" lacks "pooled over the days";
- B5: Fig. 1 has no exit for a gate that does not open;
- C: the Listing 1 citation for 91%, "base rule" in Table IV, citing Fig. 3 in V-C and its
  "in protocol" label, a hard sentence in V-C, the note on the learned models, and the PDF
  metadata.
The figures check out technically: 307-435 ppi as placed, all fonts embedded (no Type 3),
pure grayscale. The review asks for two changes to Fig. 3: a marker for the base rule
distinct from the beta-binomial's hexagon, and a larger "1% budget" label.

12 pages, the Acknowledgment ends on page 8, no stretched column. `make audit`: 253 checks, 0
mismatches.

## 44. Round 41: the review's B and C items, and two figure fixes

At the authors' request, every B and C item of the round-40 review was applied:
- B1: in the abstract, "The test blocks 90%", since on generated traffic the level stays at
  0.01, and "behind its volume trigger, it misfires in 0.1%", since the scope alone names a
  filter in 2.2% of clean windows. "five-minute" came out, the abstract stays at 250 words,
  and "its misfires block a median third" replaces "each misfire blocks", which pinned a
  median to every misfire.
- B2: "We found no published method that blocks ...".
- B3: the botnet's stacks are drawn uniformly at random (the generator's `rng.choice`, the
  injector's `rng.integers`), not spread evenly. IV-A says "uniformly at random" and "the
  hardest case in expectation", and III-C "spread uniformly". The random stack sizes are why
  V-B's floor is no cliff.
- B4: the conclusion's unseen filter is "within the budget pooled over the days". The
  sentence, then 49 words, was split, and "gives up most new-stack detection" became Table
  VI's number, "only 20% on new ones".
- B5: Fig. 1's trigger box reads "otherwise: no action". It is exported with `drawio -x -f png
  -s 3 -b 6`, which reproduces the earlier export pixel for pixel, so the figure keeps its
  3104 x 797 size.
- C1: III-B cites Listing 1 for the 91%.
- C2: "base rule" in Table IV, and "a tenth of the median window" in V-C.
- C3: V-C cites Fig. 3, whose legend says "binomial configuration".
- C4: the console sentence in V-C leads with its claim.
- C5: "The learned models were not run on shared stacks", since `symbolic_detector.py`'s grid
  has no shared mode, and "an F1 of 0.900" in Appendix C.
- C6: Fig. 4's caption says "Dotted: reference slopes", and the PDF has title, author and
  keywords metadata.

Fig. 3's base rule is now an open circle, the one open marker, so it reads apart from the
beta-binomial's hexagon at print size. The "1% budget" label is 6.5 pt.

The added words had pushed the Acknowledgment's last line onto page 9. Section VI's "(25
stacks drawn uniformly, ...)" went back to "(25 stacks, ...)", and the conclusion's split
sentence is shorter. `make audit` learned Table IV's "base rule" row name. 12 pages, the
Acknowledgment ends on page 8, no stretched column. `make audit`: 253 checks, 0 mismatches.

## 45. Round 42: the second review, the Azion affiliation, and its B and C items

A second scope-bound review (read-only, no data drive) gave a weak accept: 4/3/4/3/4,
confidence 4, about the 70th-75th percentile. It found the 14 fixes of round 41 correct and
recomputed a sample of numbers from `production_tables.json`, and all matched. Its only
blocking item, A1, was the author block. The first author is also with Azion Technologies,
whose services the paper evaluates, so the author block now reads "Also with Azion
Technologies, Brazil". There is no funding to acknowledge. B3, the scope of the AI-use
disclosure (drafting as well as editing, analysis as well as figure code), is left to the
authors and their advisor.

- B1: IV-A defines the *cluster*: the endpoint's sessions chained while each starts within
  300 s of the previous one (`assign_detection_clusters` starts a new cluster when the gap
  between starts exceeds 300 s). III-B no longer uses the word before IV-A defines it.
- B2: Section VI says that a bot presenting a common fingerprint, or a fresh one per device,
  defeats the scope, and that an alarm then leads only to the fallback.
- C: "the hardest case in expectation for naming a stack at a given M", since above the floor
  an even spread is the easiest case, with every stack named at once. "The 99th percentile
  for tau_cluster". The conclusion reads "only 20% of it on new stacks, and 15% on shared
  ones, which the filter cannot name". V-C's console sentence leads with the set it ranges
  over. III-B's n counts each origin once per fingerprint it presents, which is how the
  exports count (n = sum of c(f)). The seasonal gate divides the distinct origins by their
  same-hour median and fires at that ratio's 99th percentile (`production_tables.py`, never
  below 1). Appendix C notes that Table III runs its learned models on its own 15 seeds.
  Table IV's header "New" matches its note ("New, Shared: blocked, all attack windows") and
  Table VI. Section V's lead-in states the held-out day's finding. The layout comment in the
  source is current.
- Figures: Fig. 1's trigger box reads "distinct origins >= p99 (base rule: Omega(S) >= tau)",
  exported at the same 3104 x 797. Fig. 3's legend says "unseen filter (origin gate)", and its
  caption "with an arrow from in sample where the two are apart". Fig. 4's caption names the
  two layers: admission, per request, and the Omega aggregation, per window.

The lines were paid for by Section VI's STIX/TAXII validation sentence (Appendix F keeps it),
IV-A's "The generator also varies ...", Section II's lead-in ("Table I compares prior scopes
and detectors."), and a few words in paragraphs whose last line held one or two words. The
affiliation line took the space that p. 4's right column left above IV-B's heading. The study
guide follows the changes. 12 pages, the Acknowledgment ends on page 8, no stretched column,
no sentence over 45 words. `make audit`: 253 checks, 0 mismatches.

## 46. Round 43: the third review's B and C items

A third scope-bound review gave a weak accept: 4/3/4/3/4, confidence 4, about the 75th
percentile, and "Ready to submit: yes", with no class A item. It found the 13 fixes of round
42 correct and recomputed Tables IV-VI, the points of Fig. 3, App. E's floors and the P values
on its own, and all matched.

- B1: Section VI now says an alarm "leads mostly to the fallback". V-B reports 73.5% of 1,000
  attackers stopped on common fingerprints on the single sign-on, and V-A 30.4% in the
  adversarial mode, so "only" contradicted the paper.
- B2: IV-B and App. E say that each fleet share was added to the base rule.
  `fleet_selection.py` counts clean false alarms with the Omega gate and the test's scope, and
  `results/fleet_profile.json` gives 6 for the rule alone, 5 with the 5% share and 12 to 16
  with the others. That 5 is not the binomial configuration's count, which is also 5 over
  the five test days.
- B3, for the authors: App. F's repository URL opens on `main`, which is still the 28 August
  state without the LICENSE. Merge or tag before submission.
- C: III-B reads "kept by the held-out day's protocol", since "the protocol" was used there
  before any introduction. App. A's class sizes are "counted as in Section III-B". V-C cites
  Fig. 3 on the No-gate sentence, since the figure has no seasonal-gate point. The conclusion
  reads "which the unseen filter misses", and Table III's caption "Scopes of the largest-Omega
  cluster as detectors.". V-A's "moderate drift" is "a profile drifted to alpha = 2.0", the
  drifted profile of `profile_drift.py`. WAF stays unexpanded, since expanding it costs a line
  on a full page and the paper does not expand common acronyms.

Every edit is line-neutral: 12 pages, the Acknowledgment ends on page 8, no stretched
column, no sentence over 45 words. Four audit strings follow the new wording. `make audit`:
253 checks, 0 mismatches.

## 47. Round 44: the fourth review's B1 and C items

A fourth scope-bound review gave a weak accept: 4/3/4/3/4, confidence 4, about the 75th
percentile, and "Ready to submit: yes", with no class A item. It found the 8 fixes of round
43 correct, and it checked numbers the audit does not cover (App. D latencies, App. B weights,
the KLAGE comparison, the JA4 measurement, the ratio-limit counts). All matched.

- B1, a regression of round 43. The compiled query (`results/compiled_counts_clickhouse_example.sql`)
  counts every class, and the per-window total, as `COUNT(DISTINCT client_ip)`. The
  production gate and Omega's endpoint term use III-B's n, the per-fingerprint sum
  (`rule_detection_production.py`). App. A now says the class sizes are in distinct
  addresses, and that on production traffic the gate and endpoint term use III-B's n. VI and
  App. F say "exported address and /24-pair counts".
- C: V-C cites "dashed in Fig. 2" for the No-gate result. That is E1's tenth-size botnet at
  89.6%, while Fig. 3 pools 100 attackers, where the scope alone blocks 52%. The introduction
  cites Cambiaso et al. for Slow HTTP DoS and CICIDS2017, which documents both, for HULK and
  GoldenEye. III-D gains a comma. App. E says that windows with fewer than k_min origins are
  left out (117 of E4's 1,440 test-day windows, none on the held-out day; `production_tables.py`
  keeps `size >= k_min`). App. D's rdflib times are "likely" an upper bound.
- Not applied: the funding line (there is none), and the old table numbers in
  `fresh_day_protocol_addendum.md`, a dated record that is not edited after the fact.

The App. A sentence first pushed App. D's heading past Fig. 4 and Listing 1, which stretched
pp. 10-11 and made 13 pages. Trims in App. A, C, E and F brought it back: "aggregated", a repeated
"restricted to network proximity", "also", "the production", "the busiest endpoint" as "E1",
and "between ... and" as a range. The audit follows the new wording. 12 pages, the
Acknowledgment ends on page 8, no stretched column. `make audit`: 253 checks, 0 mismatches.

## 48. Round 45: the fifth review's B and C items

A fifth scope-bound review gave a weak accept: 4/3/4/3/4, confidence 4, about the 70th-75th
percentile, and "Ready to submit: yes", with no class A item. It recomputed about 45 numbers
outside the audit, and all matched.

- B1: III-D names the known fleets of the busiest endpoint and the API. On the API the
  binomial configuration exempts 1 or 2 fingerprints on four of the five test days, up to
  6.9% of its profile (`results/fleet_profile.json`). The console and the single sign-on
  exempt none. The audit now checks all four endpoints.
- B2: App. A says the production gate and endpoint term add plain-HTTP clients to III-B's n.
  `rule_detection_production.py` counts them in `n_legit`, while the test's n sums the TLS
  fingerprints only. The share of plain-HTTP clients on E1-E4 was not measured, since reading
  the exports on the data drive was not permitted in this session. The text is correct
  whatever that share is.
- C:
  - App. E: "one fingerprint would be a known fleet on E1". The count comes from the fleets
    diagnostic `xfit_od_fleets`, and the cross-fitted beta-binomial exempts nothing.
  - App. C: "Each configuration, (a) to (d)".
  - App. D: "to within 10^-11", since the largest difference is 7.28e-12. Also "The pair-edge
    path takes 0.84 s ... 52.8 s", since materializing alone takes 0.79 and 50.8 s
    (`latency_summary.json`).
  - IV-B: "windows under k_min origins left out", paid for by "We also report".
  - App. A: "A near variant, ja4_distance = 1," is in an `\mbox`, without "annotated", so it
    no longer breaks across lines.
  - App. F: "per-window address and /24-pair counts".

The first App. A wording and C1 added three appendix rows and a 13th page. Shorter wording
restored the previous layout. 12 pages, the Acknowledgment ends on page 8, no stretched
column. `make audit`: 253 checks, 0 mismatches.

## 49. Round 46: the sixth review, and a three-line title

A sixth scope-bound review gave a weak accept: 4/3/4/3/4, confidence 4, about the 70th-75th
percentile, and "Ready to submit: yes", with no class A item for the sixth time. It
recomputed about 60 numbers outside the audit, and all matched. The run stalled once and was
resumed.

- B1: App. A says that III-B's n counts an address once per fingerprint, whereas the compiled
  query counts it once (`COUNT(DISTINCT client_ip)` in
  `results/compiled_counts_clickhouse_example.sql`, against the per-fingerprint sum of
  `rule_detection_production.py`).
- C1: V-B's stack-size example (43.1% against 43.2%) is "for 100 new-stack attackers on E1".
- C2: Fig. 3 draws the cross-fitted twin of "scope alone, binomial", which the caption's grey
  promised.
- C3: the title no longer forces a line break after "Mitigation:" and sets in three lines.
  That frees enough of page 1 for IV-B's heading to fit at the foot of p. 4, so the lines
  saved on pp. 1-4 over the last rounds reach page 8. The Acknowledgment now ends about five
  lines before the references, which start on page 8.
- Audit labels: Table VI (the trigger table) and "about 250 numbers".
- Left for the artifact submission: the two binding examples in `bindings/` treat WAF-blocked
  requests differently, so neither alone reproduces App. F's check on E2-E4.

12 pages, the Acknowledgment ends on page 8 with about five lines to spare, no stretched
column. `make audit`: 253 checks, 0 mismatches.

## 50. Round 47: the seventh review, and the fallback's cost

A seventh scope-bound review gave overall 4, novelty 3, technical quality 4, clarity 3,
relevance 5, confidence 4, about the 75th percentile, and "Ready to submit: yes", with no
class A item.

- B1: VI(i) states the fallback's own cost. The fallback acts on every gate opening that names
  nothing, in 2.9% of clean test-day windows (163 of 5,643: the gate opened in 168, the
  configuration fired in 5) and 5.4% on the busiest endpoint (78 of 1,440, none named). The
  audit gained a check that recomputes both from `production_tables.json`. The sentence was
  paid for by VI's "No evaluation covers a captured stealthy campaign, and", since the
  conclusion names a captured stealthy campaign as the next step.
- C: V-A names the two profile features of the learned model, "log b(f) and its log
  enrichment per session" (`symbolic_detector.py`, `profile_features`), made line-neutral with
  "trains on labels of the campaign it scores" and "At 1% false positives". IV-A reads "We
  compared that curve with". IV-B reads "Their gate is either Omega >= tau_cluster, for the
  base rule, or distinct origins ...". App. A's sentence on n is split in two. Fig. 3 draws
  the base rule's cross-fitted twin (0.21% against 0.25%).
- Not applied: a III-B pointer to App. A, which would put a line at risk on pp. 1-4, and
  larger figure fonts, for which there is no height.

Layout lesson: the lines "free" on page 8 hold the start of the references. The body can
grow by about one line before the references' heading moves to page 9. Past that, the
appendix shifts by about six rows, App. D's heading jumps past Fig. 4 and Listing 1, and the
paper grows to 13 pages. A line added on pp. 5-7 can also move a float and stretch columns,
as the first V-A wording did. In a scratch copy, the longer AI-use disclosure ("draft and
edit text ... analysis and figure code") fits without changing any line.

12 pages, the Acknowledgment and the start of the references on page 8, no stretched column.
`make audit`: 254 checks, 0 mismatches.

## 51. Round 49: a selective merge of a language revision

A language-only revision of the paper (`papers/http-session-noms/article_revised_zero_growth.tex`,
not committed) rewrote about 74% of the sentences and cut 523 words. It kept every number,
citation and reference. But it also dropped qualifiers ("drops all traffic", "the unseen filter
alone", "fires there", "any production data", "post hoc"), changed claims ("in which it is
selected" in the abstract, "may be the legitimate population", fleets that "create" the floor)
and changed key terms ("specify" to "represent", "present" to "use"). It introduced a few
subject errors ("the busiest endpoint stops", "removing the endpoint term ... flags"), 27
semicolon joins, 2 em dashes and an "X, not Y" antithesis.

Each of its 318 changed sentences was read against the original. The merge accepted 114 as
written, adapted 74 (a qualifier restored, a semicolon split, the paper's term kept) and kept
130 unchanged. The abstract and the contributions keep the authors' wording except for small
clarity edits. Number comparisons now read "versus" throughout (21), and "against" remains
only in its other senses. Relative to the text before the merge, no number, citation,
reference or label changed, and the body is 139 words shorter.

Layout: shorter Related Work left p. 2's left column a line short of Section III's heading
block, so the full Section II lead-in came back. A few adapted sentences that each added a
line in IV-A, IV-B, V-D and VI were taken back to the original. 12 pages, the Acknowledgment
and the start of the references on page 8 as before, no stretched column. The audit's pinned
phrases were mapped onto the merged wording by a word alignment. The chk templates follow
that alignment, and six f-string pins were updated by hand. `make audit`: 254 checks, 0 mismatches.

## 52. Round 50: the ninth review, after the language merge

A ninth scope-bound review, the first after the language merge, gave 4/3/4/3/4, confidence 4,
about the 70th-80th percentile, and "Ready to submit: yes", with no class A item. It judged the
English "plain, natural and consistent".

- B1: V-B's components exceed the 1% budget "on the test days", not "on the days after
  calibration". On the held-out day the scope alone fires in 0.5% and the gate in 0.26%.
- B2: V-D reads "a tenth-size botnet on the busiest endpoint never opened the gate". It no
  longer follows "flash crowds" as if it were a crowd.
- B3: VI (ii) reads "stayed within the budget everywhere, pooled over the days, and matched
  every scope ...", paid for by two words of the same paragraph.
- B4: "Gray" in Fig. 3's caption (American spelling).
- C:
  - Terms that drifted in the merge: "The obvious scope fails", the beta-binomial "nearly meets
    its budget", "class counts", KLAGE's "$F_1 = 0.841$", "the compiled query keeps them", and
    "The Trigger Decides" in the V-C heading.
  - Two dangling modifiers ("Its false alarms as its own trigger ...").
  - VII: "90% of a botnet on up to 25 new stacks ... or label".
  - III-D: fingerprints "that together carry up to about 7%" of the profiles.
  - II: "One industrial bot-management platform ... publishes no model", since the claim rests
    on one source. Paid for by "still" in the next sentence.
  - IV-A: an attack "would lower the level and raise the gate's threshold, making both more
    cautious".
- Not applied: "stops little of a small botnet" in VI (i), which cost a line on page 8.

Twelve audit pins were remapped. The one for the held-out gate was written out in full
("a tenth-size botnet on the busiest endpoint never opened the gate"), because the automatic
mapping had shortened it to "the gate.". 12 pages, the Acknowledgment and the start of the
references on page 8 as before, no stretched column. `make audit`: 254 checks, 0 mismatches.

## 53. Round 51: the four-criteria review and the independent review

A tenth review judged four things: whether the paper delivers what it promises, the results,
grammar and fluency, and how the text connects to the figures and tables. It gave
3/3/4/3/4, confidence 4, about the 70th percentile. Its one class A item was a qualifier
missing from the abstract. An independent NOMS-style review asked for two cheap fixes.

- A1 and B1, abstract: "a botnet on rare fingerprints that real clients share is singled out
  only once it is large, and one on the most common mostly escapes". Paid for by shorter
  wording elsewhere in the abstract, which stays at 250 words.
- B2: VII now says the scope alone exceeds its budget on the test days ("though its scope
  alone exceeds its budget there (2.2%)"). V's lead-in no longer credits calibration alone
  ("false alarms stay low but calibration sets a floor"). Paid for by the first sentence of
  V-D's "Post hoc analyses", which repeated III-C, the heading and the table notes.
- B4: VI (i) gives the flash-crowd cost ("Crowds of 1 000 users trigger the configuration in
  22.2% of windows"). Paid for by ", none on the held-out day", which V-D states.
- B5 to B11:
  - V-C's console sentence reordered;
  - "on the days used to choose it" in the abstract and VII;
  - "without labels and with no observed collateral";
  - "an expected 0.03%";
  - "the ACL model that DOTS filters copy";
  - Fig. 3 cited at the z-score's in-sample threshold, where its arrows show the change,
    rather than at "barely changes";
  - "(No gate, scope as trigger)" in IV-B.
- C:
  - "P = 0.27 at the test days' rate" in V-D;
  - "The fallback thus acts";
  - V-C's clause order;
  - two sentences split, in IV-A (the cluster) and VI (ii);
  - Table III's caption ("the alarm's cluster");
  - Table IV's "Config." header;
  - Table VI's "E2–E4: max." ("their maximum" and "highest endpoint" made the note three lines);
  - Fig. 1: the trigger box gains "and ≥ k_min", and the ontology box puts the unit on
    `relatedTo`, as III-E does.
- Independent review: I reads "Existing detectors flag the attack but leave that decision
  open", and III-C calls N "the profile's pooled origin–fingerprint pairs".
- Not applied:
  - B3, because the contributions carry no numbers;
  - C3, because the measured 88% is what the configuration misses, not only what the gate
    lets through;
  - C10, "(Listing 1, App. D)", because it would cost a line on pages 2 and 3, where the layout
    is fragile.

The first pass made the PDF 13 pages. The Table VI note, B4 and B2 each cost more than
the review expected. Shortening them restored the layout: 12 pages, no stretched column,
and the references starting at the same point of page 8 as before (y = 670 pt). 14 audit
pins were remapped:
- 12 automatically;
- the post hoc disclosure, which now pins III-C's "built after the held-out day was read" and
  "Cross-fitting, built post hoc";
- the held-out day's f-string.

VII's 2.2% and VI (i)'s 22.2% are now tied to the data. `make audit`: 254 checks,
0 mismatches. The study guide follows the new wording.

## 54. Round 52: the second four-criteria review

The same four-criteria review, run again, gave 3/3/4/3/4, confidence 4, about the 72nd
percentile (up from the 70th), "Ready to submit: yes", with no class A item. Its reviewer
calls 3 "weak accept", where the NOMS-style reviews of rounds 43 to 50 called 4 "weak
accept". Both use a 1 to 5 scale, so compare the verdicts and percentiles, not the numbers.

- B1 and B2, abstract:
  - it now says the test alone exceeds its budget ("though alone it exceeds its 1% budget");
  - "One on the most common mostly escapes" stands as its own sentence, because the ratio
    limit causes it at any level, not calibration;
  - paid for by "what it stops and costs", "production traffic", "adds limited evidence" and
    two split sentences. "the obvious choice", which the reviewer's version cut, stays. 250
    words.
- B3, App. F: `make compile-check` also runs "after a fourth equality signal is added as
  four triples". `compile_check.json` records this (4 triples, 0 lines of code, Ω exact), but
  the paper had never said it was tested. Page 12 is full, so App. E and F pay for it:
  "per-window", "just", "still", "separates" and "the profile describes".
- B4, contribution (i): "block most of the attack without labels", still with no number.
- B5 to B7:
  - V-C's console sentence names the four variants first;
  - V-D splits the test's power from the quiet gate;
  - Fig. 3 is cited at the beta-binomial's 1.1%, the point just past the budget line, and a
    repeated "in Table V" goes.
- C:
  - III-C's "plus 1/N" moves to the end of the definition;
  - "This share is averaged";
  - III-E's "scope and split of Ω(S) by sub-relation";
  - "DOTS, whose filters reuse that model, does not adopt it";
  - VI (i) "where the scope names nothing" and "stops little of a small botnet".
- Not applied:
  - the flash-crowd filters' 4.3% in VI (i), because it would take page 8's one line of
    slack;
  - the notes on Tables III and V and on terms, which the reviewer accepted as they are.

The reviewer's claim that page 12 had room was wrong: both columns end at y = 718 pt. The
layout is unchanged: 12 pages, no stretched column, the references at y = 670 pt on page 8,
and page 12 full. App. E lost one line and App. F gained one. Ten audit pins were
remapped, two of them trimmed by hand. The abstract's new clause and App. F's fourth signal
are tied to the data. `make audit`: 254 checks, 0 mismatches.

## 55. Round 53: the tenth NOMS-style review

The NOMS-style review, given the ninth pass's brief, scored the paper after rounds 51-52 at
4/3/4/3/4, confidence 4, 70th-80th percentile, "Ready to submit: yes", with no class A
item. That is the ninth pass's score.

- B1, Section I: "Existing detectors at most flag the attack and leave that decision
  open." Round 51's "Existing detectors flag the attack" contradicted the paragraph
  before it, which says a stealthy campaign looks legitimate on per-session signals, and
  Appendix C, where per-session detectors sit at chance.
- B2, III-C: "Let b(f) be 1/N plus the share of fingerprint f among the profile's N pooled
  origin–fingerprint pairs, c(f) …". Round 52's ", plus 1/N, c(f)" read as if c(f) were a
  second addend.
- C:
  - the abstract's "One on common fingerprints mostly escapes" (249 words);
  - IV-B's "where the gate does not fire";
  - V-D's "metrics set in advance";
  - App. F's 58-word sentence split in two;
  - App. E: "the binomial behind it stops 10.0–44.7% of E1's tenth-size botnet", since a gate
    alone stops nothing (the audit computes the range from the binomial behind the
    seasonal gate).
- Not applied: C1, which asked to restore round 51's order of V-C's console sentence.
  Round 52's reviewer had asked for the opposite, and both orders are correct.

Layout unchanged: no page changes its line count, the paper stays at 12 pages with no
stretched column, and the references start at y = 670 pt on page 8. Sentences over 45
words fell from 4 to 3. Two audit pins were updated by hand, and the App. E pin now
includes "the binomial behind it". `make audit`: 254 checks, 0 mismatches.

## 56. Round 54: the eleventh NOMS-style review

The eleventh pass scored 4/3/4/3/4 again, confidence 4, 70th-80th percentile, "Ready to
submit: yes", with no class A item. It checked about 50 numbers, and the two "P = 0.27"
come from two different tests that both recompute.

- B1, V-D: "Exported after the configuration was fixed, then analyzed with metrics set in
  advance". The old wording read as if the configuration had been analyzed.
- B2, V-C: "as in E1's tenth-size botnet". Only E1's tenth-size botnet puts at least k_min
  origins on each of its 25 stacks (about 11 per stack), while E2–E4's has 2 to 6 attackers
  in all. The audit now checks this against the median windows.
- C:
  - III-C: "the test names no fingerprint" (instead of "no scope"; "names nothing" would
    repeat "nothing" in the same sentence);
  - V-D: the console's crowd rate (16.1%) moves out of the colon that supports "nearly
    meets its budget";
  - App. F: the TAXII server's clause is its own sentence, with the list kept in pipeline
    order (validator, TAXII, MISP; the reviewer's reordering would have put MISP first);
  - IV-A: "Test-day windows before injection (clean)", since every window is scored clean
    and again with the injected botnet;
  - the abstract's "A botnet on common fingerprints mostly escapes" (250 words);
  - the footnote's "August 22, 2026".

Layout unchanged: no page changes its line count. Three audit pins were remapped, two of
them trimmed by hand. `make audit`: 254 checks, 0 mismatches. The last three NOMS-style
passes gave the same score, and their items are now precision fixes. They put clarity at 3
because of number density, which the page budget leaves no room to reduce.

## 57. Round 55: the twelfth NOMS-style review

The twelfth pass scored 4/3/4/3/4 again, confidence 4, 70th-80th percentile, "Ready to
submit: yes", with no class A item.

- B1, V-D: "Cross-fitted, only the beta-binomial nearly meets its budget: …". The paper
  defines in sample and cross-fitted, and "out of sample", used only here, read as false:
  the in-sample beta-binomial's scope alone fires in 4.4% of the test days' clean windows.
- C:
  - III-C: "the test does not name it". Round 54's "names no fingerprint" said too much,
    because a window can still name a fleet's fingerprint;
  - VI: "(25 stacks, new, shared and mostly rare, or the endpoint's most common)";
  - the footnote's "August 22, 2026, from";
  - V-D: the held-out day's 1.1% for 100-user crowds now gives the test days' 4.6%, with a
    new audit check;
  - App. E: "halves the base rule's false alarms".

Layout unchanged: no page changes its line count. Three pins were remapped, and one check
was added. `make audit`: 255 checks, 0 mismatches.

## 58. Round 56: the thirteenth NOMS-style review

The thirteenth pass scored 4/3/4/3/4 ("accept") a fourth time in a row, about the 75th
percentile, "Ready to submit: yes", with no class A item.

- B1, III-C: "Conversely, attackers hidden inside a popular legitimate fingerprint do not
  enrich it, so the test leaves it unnamed, which is correct when nothing distinguishes the
  attack from legitimate traffic." Enrichment belongs to fingerprints, and "does not name it,
  as it should" could read as "though it should".
- B2, VI: "shared but mostly rare". Because the paper uses no serial comma, "new, shared and
  mostly rare" read as three items.
- B3, III-A, which twelve passes had missed: "requires a full browser or an impersonation
  library". Headless-browser farms, the next sentence's example, run a real browser and need
  no impersonation library.
- C: V-D's "outside the protocol" (no "also"). In VI, a comma limits "where the WAF blocked no
  client" to the JA4 counts, as App. F says.
- Not applied:
  - C1, "of the three", which would have cost the z-score's Fig. 3 citation or "of windows";
  - C4, "origin gate" versus "distinct-origin gate", which the reviewer left as is.

Layout unchanged: no page changes its line count. Two pins were remapped. `make audit`:
255 checks, 0 mismatches.

## 59. Round 57: a skeptical review of the whole paper, references included

A last pass took the committee's skeptical reader as its role. It was asked for the strongest
reasons to reject, and it read the appendices and the references, which earlier briefs had
let reviewers skip. It gave 3/3/4/3/4, about the 60th-70th percentile, "Ready to submit: no"
because of one class A item. Its lower score reflects the role. Each item below was checked
against its source before it was applied.

- A, Section I: Kemp et al. [4] never measure "route entropy". Their 12 NetFlow features
  are packet, byte, flag, duration, payload and rate counts, and "entropy" appears only in
  their feature ranking. The phrase had come from `docs/concepts.md`. It is now "such as
  connection duration and packet rate".
- B:
  - App. C: Kemp et al. train RF, C4.5, 5NN, NB and JRip, with no SVM. The text now says "a
    supervised RF/SVM over session features, after [4]", and "(Table III uses 15)", since
    every Table III column uses 15 seeds.
  - App. B: the sprint-4 grid is {0.3, 0.5, 0.7, 0.9, 1.0}, so the ontology's 0.6 was never
    on it. The text now reads "as does the ontology's (1.0, 0.6, 0.3)". The ontology's
    weights, evaluated alone, reach the grid's best AUC (0.9428). A new audit check reads
    `weights_session_realistic.json`.
  - V-A and VI: "new stacks never occur in legitimate traffic". The generator also has shared
    stacks, which the next sentence of V-A names.
  - III-A: "We also assume a bot keeps the fingerprint of its TLS stack". A TLS library lets
    a bot set its cipher and extension lists, so the assumption that matters is the
    fingerprint, and VI's "a fresh one per device" is now plainly outside the threat model.
    The reviewer's matching VI edit cost a line and was not needed.
  - Abstract: "though each alone exceeds its 1% budget". The gate (3.0%) and the scope (2.2%)
    each exceed their budget, and only the two together reach 0.1%. The audit now checks
    both.
- Not applied:
  - naming the unseen filter's parity in contribution (i), which is the user's call on the
    framing;
  - further abstract changes, since the abstract is at 250 words;
  - pages for three references, since that risks the layout;
  - the OCSF version, whose note already gives the versions and the access date.
- Checked on the web: the NOMS 2027 technical-paper deadline is 9 November 2026 (ComSoc
  page). NOMS 2026 ran an Artifact Evaluation track for accepted papers. Confirm that the
  2027 CFP keeps it, since App. F names it.

Layout unchanged: no page changes its line count. The study guide follows the paper.
`make audit`: 256 checks, 0 mismatches.

## 60. Round 58: the second skeptical review

The second skeptical pass confirmed round 57's six changes. It again scored 3/3/4/3/4,
about the 60th-70th percentile, and "no" because of one class A item.

- A, App. C: "a strong per-session baseline using nine flow attributes". The code's strong
  baseline is FLOW's three attributes (requests, duration, rate) plus six byte, packet and
  inter-arrival sums. The paper's "eight" came from a wrong comment in the scripts, which now
  say 9, and the study guide follows. A new audit check reads the lists from the scripts.
- B:
  - App. C: "(c) adds only network proximity, and (d) adds cross-session evidence". In the
    code, (b) to (d) all add to (a)'s attributes.
  - V-B: "and with the fingerprints' popularity". The floor falls as the rank number rises
    (ranks 11-35 never named, 36-100 at 743, the typical tail at 254 on E1).
  - II: "None of these preserves relations across sessions", which limits the claim to the
    detectors cited. Paid for on page 2 by "One bot-management platform", dropping
    "industrial".
- C: V-A's "in generated legitimate traffic", since production shows new fingerprints daily.
  I cites "75 application-layer DDoS studies", since the survey counts studies.
- Checked, no change: "seven origins in one of 143 /24 prefixes" for CIC-IoT2023 agrees with
  `docs/concepts.md`, the evidence-chain script and the PT paper. The outdated sprint-5
  docstring ("distributed over 143 /24s") was corrected.
- Not applied: defining "admission" in App. D (page 11 is full), the HULK/GoldenEye nuance in
  I (it costs words on page 1), and the reviewer's four framing risks, which the text already
  answers.

Layout unchanged: Section II gains a line and loses one within page 2's left column.
`make audit`: 257 checks, 0 mismatches.

## 61. Round 59: the third skeptical review, and the ontology declares its export

The third skeptical pass scored 3/3/4/3/4 again, about the 60th-70th percentile, and "no"
because of one class A item, this time in the repository's ontology.

- A, III-E and contribution (iii). The text said `ApplicationSession` links a session to its
  `Mitigation`, whose scope the evidence chain carries. The OWL had no such link: its
  `mitigatedBy` starts at `Attack`. None of the terms the exported chain uses (Listing 1) was
  declared, and the scope's fingerprint condition used `tlsJa4`, whose domain was only
  sessions. Two fixes:
  - `ontology/ddos_ontology.owl` declares the chain's vocabulary: `derivedMitigationScope`
    (Attack to Mitigation), `activatedSubRelations`, `clusterSize`, `coordinationScore`,
    `verdict`, `scopeLevel`, `linkedPairs`, `weightedContribution`, and the scope conditions
    `endpoint` and `srcNet24`. The domain of `tlsJa4` now also admits a Mitigation, and the
    rule's target class `CoordinatedHTTPFlood` has a general comment. The change only adds
    declarations. The recompiled query is identical (`compile_check.json` unchanged,
    four-triple extension included).
  - III-E now reads "links a session to its Identity, source IPAddress and Endpoint. An
    Attack links to its Mitigation, whose scope the evidence chain carries."
  A new audit check parses the OWL and `example_chain.jsonld` together. It fails if the chain
  uses an undeclared term, or a property whose domain does not admit the node it is on. On the
  old ontology it fails with the nine terms; on the new one it passes.
- B:
  - App. C: in the KLAGE comparison, configuration (d) builds on FLOW's three attributes, so
    the text reads "while three of them plus cross-session evidence reach 0.911".
  - II: "Flow-based and Layer-7 HTTP DDoS detectors [5]". Fernandes et al. profile IP flows,
    not HTTP.
- C:
  - Table I: "Detectors" (KLAGE is not an L7 detector).
  - App. C: "the nine per-session flow attributes in a Random Forest (RF), repeated with
    gradient boosting, a multilayer perceptron and logistic regression". The perceptron is a
    64-32 MLP.
  - App. E: the rule "names a filter in every attack window flagged by Ω and blocks a median
    75-80% of attackers". The audit now checks that every flagged window is named.
  - Artifacts: `run_klage_comparison.py` and `sprint-5/README.md` say 9 attributes, and the
    script's docstring no longer calls real Slowloris indistinguishable per session.

Layout unchanged: no page changes its line count. The study guide follows, including the
ontology's links. `make audit`: 258 checks, 0 mismatches.

## 62. Round 60: the fourth skeptical review says "yes"

The fourth skeptical pass found no class A item. It scored 4/3/4/3/4, about the 65th-75th
percentile, "Ready to submit: yes": the first time the skeptical role approved. It loaded the
OWL with `example_chain.jsonld` and found every term declared and every domain respected, and
it recomputed about 35 numbers outside the audit.

- B, App. A: path-pattern normalization, the `exact` and `strong` flags and ASN matching were
  described as if implemented. No code runs them, and only OWL comments and `docs/` mention
  them. The text now reads "same endpoint, here a host or an address and port, with
  path-pattern normalization specified but not exercised" and "shared IPv4 /24 or IPv6 /48,
  with a shared ASN specified but not exercised". IPv6 /48 is exercised: the binding keeps
  the first 6 bytes. The appendix is one line shorter, so page 12 now has one free line.
- B, OWL: round 59 declared `coordinationScore`, `weightedContribution` and `scopeLevel` as
  xsd:decimal. JSON-LD 1.1 reads fractional numbers as xsd:double, and OWL 2 keeps the two
  value spaces disjoint, so a reasoner would find the chain inconsistent. They are now
  xsd:double. The ontology audit check also compares every literal's datatype with its
  property's declared range.
- C:
  - III-E: "annotates each equality", since only the equalities carry a class key, and "(the
    rule, cluster, scope and split …)", since the chain lists no session instances;
  - App. F: "the 288 windows of each day". Both checked days matched, and the audit now
    checks both.
- Repository:
  - OWL: the six sub-properties are also declared as classes, because the chain types its
    evidence nodes by them (OWL 2 punning). The count comments say origins, and two section
    pointers and the family comment were updated.
  - The root README's artifact map no longer lists "Table VII", "Listing 1 (SWRL + SPARQL)"
    or "Listing 2".
  - `example_chain.py` says Listing 1.
- Not applied: "detection benchmark" in II (a word on the tight page 2), and rewording the
  abstract's "each alone" (two words over 250).

`compile_check.json` is unchanged. `make audit`: 258 checks, 0 mismatches.

## 63. Round 61: the fifth skeptical review

The fifth skeptical pass found no class A item, and it again said "Ready to submit: yes"
(4/3/4/3/4, 65th-75th percentile). It checked the figures against `make_figures_en.py` and
the data, App. D against `latency_summary.json`, Section IV's setup and the standards
paragraph, and all of them matched.

- B, JSON-LD: JSON-LD 1.1 reads an integral number such as 114710.0 as xsd:integer. The
  ontology gives `coordinationScore`, `weightedContribution` and `scopeLevel` the range
  xsd:double, so a spec-conforming processor plus a reasoner would find a violation. rdflib
  keeps Python's floats as doubles, so the audit had passed.
  - The chain's context now types the three terms in `evidence_mitigation.py`, and the
    committed `example_chain.jsonld` got the same context. Only the context changed, and the
    STIX validation output is identical.
  - The ontology check now fails if an xsd:double term the chain uses is not typed in its
    context. It flags the old chain's three terms.
- B, App. D: "nine endpoints". The benchmark draws 8 benign addresses plus the attacked one,
  and `bench_latency.py`'s docstring now says so.
- B, this README: "JA4 pair counts", not class sizes, since pair counts are what
  `compile_production_check*.json` records. The comparison itself ran ad hoc and has no
  committed code. `papers/http-session-noms/README.md` lists committing it before the Artifact
  Evaluation submission, since it needs the exports on the drive.
- C:
  - III-B: "the rule for the ontology's class CoordinatedHTTPFlood". It is a class, and the
    rule is not stored in the ontology.
  - Listing 1's caption: "counted in origins, abridged".
  - III-E: "the SQL queries that return".
  - The OWL's punned-class comments, the header above `targets` and "The base rule reads a
    weighted sum".
  - Figure pointers in the root README and `make_figures_en.py` (Fig. 2 in V-C, Fig. 3 in
    V-D).

Layout unchanged: no page changes its line count. `compile_check.json` is unchanged.
`make audit`: 258 checks, 0 mismatches.

## 64. Rounds 62-63: the sixth skeptical review, and a clarity pass on Section V

Round 62 applied the sixth skeptical pass (no class A item, "Ready to submit: yes"):
- App. B's production profiles now read 76 to 1 163 fingerprints, since the held-out day's
  E1 profile holds 1 163. The audit reads `ja4_churn.json`.
- App. F says "regenerate from its make target".
- VI and VII say "a pre-specified evaluation", since "test" already names the binomial test
  and the test days.
- `coordinationWeight` is typed in the chain's context, and `--endpoints` has help text.
- The OWL says "JA4 distance = 1", as App. A does.

Round 63 is a clarity pass on Section V, where every review put clarity at 3 because of number
density. It changes no finding:
- V-A splits its two densest sentences (eight numbers in one, and the unseen filter with the
  shared stacks).
- V-B opens with its point: "Each calibrated component alone exceeds its 1% budget on the
  test days, and only the two together stay within it". It also says who sets the new-stack
  floor, and why 139.
- V-C splits the five-number sentence. "What the unseen filter and the test add" now opens
  with what each covers, and the repeated 43% goes.
- V-D:
  - its first paragraph is headed "The held-out day adds limited evidence";
  - "Post hoc analyses" opens with "Of the post hoc variants, only the cross-fitted
    beta-binomial nearly meets its budget";
  - the WAF's three shares read "9-63%".

Measured on the source:

| Subsection | words per sentence | numbers per sentence | sentences with 3+ numbers |
|---|---|---|---|
| V-A | 26.0 to 22.1 | 2.6 to 2.2 | 47% to 45% |
| V-B | 30.1 to 26.5 | 3.7 to 3.3 | 71% to 58% |
| V-C | 24.1 to 22.9 | 2.2 to 2.0 | 33% to 32% |

V-D stays about as dense (its topic sentences add words), but each paragraph now states its
point first. Nineteen audit pins were rewritten by hand, and the WAF check now compares a
range. Layout unchanged (floats in place, about one more line free on page 8). `make audit`:
259 checks, 0 mismatches.

## 65. Round 64: the clarity review of the Section V pass

A four-criteria review focused on clarity judged Section V "clearly better, a strong 3" (4
plausible after its fixes), about the 75th percentile. It said "no" because the pass had made
one claim false. It also found four qualifiers the pass had dropped, and all five are
restored:
- A1: "Of the post hoc variants, only the cross-fitted beta-binomial nearly meets its budget" was
  false. Every post hoc configuration behind a gate stays within 1%, and so does the unseen
  filter as its own trigger. It now reads "Cross-fitted and used alone, only the beta-binomial
  scope nearly meets its budget."
- B1: "Pooled across endpoints" is back in V-B's lead sentence, since E1's scope alone sits at
  0.97%.
- B2: "so that the average stack reaches k_min origins", since the floor is defined on the
  average stack. Paid for by "past 4 to 19 median windows".
- B3: "(58% versus the filter's 43% of 100 attackers)".
- B4: "The day passed mostly because its gate seldom opened: 3 clean windows, …" is back.

Clarity items:
- V-C's console sentence names the other variants' rates: "where the binomial and the
  in-sample beta-binomial misfire in 2.0-2.6% of windows". The audit checks the range.
- V-A: "too few to stand out against a 1 000-session profile".
- V-B: a comma after "the busiest endpoint", "43.1% predicted versus 43.2% measured", and
  "and an expected 0.03%".
- V-D: "ranks 36 to 100" and "the three calibrated scopes".
- IV-B: "It is held to zero false positives, which the test reaches wherever …".
- App. E: "Compared with".
- Table IV's note defines 0.1× and 1×.
- The abstract says "the test and its volume trigger misfire together … though each alone
  exceeds its 1% budget", paid for by "only when large".
- Fig. 3's legend says "unseen filter alone", as "scope alone" does.

Paid for in VI: (ii) drops "stopping 90% of 1 000 attackers on each small endpoint", which
V-C and App. E give, and the standards paragraph drops its example extension. Layout
unchanged: 12 pages, floats in place, page 12 full again. `make audit`: 259 checks, 0
mismatches.

## 66. Round 65: the second clarity review

The second clarity review rated clarity 4 once its A1 was fixed, with an overall 4 and about
the 80th percentile. It said "no" because round 64's rewrite of the console sentence had
again dropped a restriction: "only the cross-fitted beta-binomial stays within the budget on
the console" left out the unseen filter behind the seasonal gate, which misfires in 0.00% there.

- A1: "only the cross-fitted beta-binomial and the unseen filter stay within the budget on the
  console, where the binomial and the in-sample beta-binomial misfire in 2.0-2.6% of windows".
  The audit now also checks the unseen filter's console rate.
- B1-B3:
  - "The strict level ... also raises the floor", since on new stacks the unseen filter sets
    it on E1 to E3;
  - "the calibrated z-score loses its lead over the binomial", since in sample the
    beta-binomial was ahead of it;
  - V-D's lead: "Of the calibrated scopes used alone, only the cross-fitted beta-binomial nearly
    meets its budget (1.1%, Fig. 3)". The unseen filter alone sits at 0.21%, and the later
    1.1% sentence was folded in.
- B4-B8:
  - V-A: "each scope flags the sessions it matches";
  - V-B's lead names "the calibrated scope and gate";
  - "the level sets the floor, computed at their median share";
  - V-C: "On the larger new stacks, ... the unseen filter without the test", since "alone"
    elsewhere means "as its own trigger";
  - the WAF sentence: "makes the scopes agree with the WAF by construction".
- C:
  - I: "We evaluate budget and floor", paid for by "this JA4 filter";
  - Fig. 3's caption defines "Alone: as its own trigger";
  - Table IV's note: "botnet size, in median windows".
- Not applied: rewording III-B to call the base rule "the ontology's rule" (round 61 had just
  made it "the rule for the ontology's class"), and unifying every "scope alone" in the prose.

Layout unchanged (no page changes its line count, floats in place). `make audit`: 259
checks, 0 mismatches.

## 67. Round 66: an outside review on how easily the paper digests

An outside NOMS-style review (kept out of the repository, like the other review exchanges)
rated the paper about 4/5, between weak accept and accept. It gave presentation 3.5-4 and ease
for the reviewer 7.5/10. Its diagnosis matches the earlier reviews: the English is natural,
and the load comes from about twenty concepts held at once. Three of its suggestions were
applied, each tested for layout:
- V-C: "we examined two other triggers, both exploratory, after the held-out day was read",
  which says once, before Table VI, that the alternatives are exploratory;
- VI: "Two limits decide per endpoint: the calibration floor and the trigger's sensitivity";
- abstract: "Triggers examined post hoc recover part of that loss", paid for by "so what matters
  is which clients to block. We treat that choice as ..." (still 250 words).

Tested and not applied:
- a framing sentence at the start of Section V, which moves V-A's heading and gives 13 pages;
- dropping the abstract's post hoc sentence, which shortens the abstract by a line and moves
  Section III's heading block (13 pages);
- the review's "why JA4" sentence as worded, because its antithesis and semicolon break the
  house style and III-A already states the assumption.

The review's main weakness, a weak held-out day and choices made on the test days, is what the
pre-specified 14-day block being collected addresses. `make audit`: 259 checks, 0 mismatches.

## 68. The held-out block: its three parts, and the report written before the reading

Part 1 of the block (2026-09-26 to 09-30) was exported on 2026-10-01 at 12:49 UTC.
Part 2 (10-01 to 10-05) followed on 2026-10-07 at 18:55 UTC, and part 3 (10-06 to
10-09) on 2026-10-10 at 14:53 UTC, so the block holds its 14 days in full.
`results/heldout_block_addendum_hashes.md` gives each file's SHA-256, rows and first and
last window, next to the hashes of the history copies. A blind check with the loader at
`05ccc0e` (`scripts/block_part_check.py`, `make block-part-check`) prints no count: in every
part each of E1–E4 holds all its windows in both exports, and no host-window is shared
with the history or another part.

`scripts/block_report.py` computes the block's metrics 1 to 10 and applies their rules,
from the block's reduction and from `ja4_churn.py` run on the block (`make ja4-churn-block
block-report`). `make block-report-check` runs the same code on the paper's own reduction and
reproduces 21 numbers the paper prints, from 5 of 5,643 to the 0.21% churn, so the
arithmetic is fixed and checked before any block count is read.

Two things surfaced while writing it, both recorded in
`results/heldout_block_protocol_addendum_metrics.md` before the reading:
- `ja4_churn.py` takes its endpoints from the run it is given, ordered by that run's median
  window. On the block it could number them differently from the paper, so the report
  matches them to E1–E4 by role.
- Metric 7 as written compares the arms on the tenth-size botnet on every endpoint. On E2–E4
  that botnet holds 2 to 7 attackers, fewer than its 25 stacks, so no scope can name it, and
  on the test days the rule would prefer configuration 4 on E4 for 0.1% versus 0.0%. The
  amendment compares 100 attackers there, the other size Section VI names, and asks for at
  least one point more. Both versions are reported, and the amended one decides.

## 69. The block in the paper

The block ran on 2026-10-10 from a worktree at `05ccc0e`, three minutes after the hashes were
pushed (GitHub push 15:02:07 UTC, run 15:05 to 18:42 UTC). `results/production_tables_block.json`,
`results/ja4_churn_block.json` and `results/block_report.json` hold its anonymized output.

What it found, by the protocol's metrics:
- metric 1: the binomial configuration misfires in 31 of 16,103 clean windows (0.19%, exact 95%
  0.13-0.27%), twice the test days' rate, so the consistency test fails (P < 1e-4), though the
  rate stays within the 1% budget;
- metric 8: the gate opened in 233 clean windows, half the test days' rate, but the scope misfired
  in 31 of them (13% versus 5 of 168, P < 1e-11); gate and scope misfire together ten times more
  often than independence predicts (31 versus 2.9), unlike on the test days;
- metric 9: 30 of the 31 misfires fall on weekdays; 17 on the console, 10 on the API, 4 on the
  single sign-on, none on the busiest endpoint;
- metric 2: the unseen filter as its own trigger raised no false alarm on any endpoint; the
  cross-fitted beta-binomial behind the seasonal gate stays within the budget everywhere
  (0.05-0.35%); the binomial scope with known fleets as its own trigger exceeds it on E1 (1.56%);
- metric 7: the seasonal arm is preferred on every endpoint, under the rule as written and as
  amended. On E2-E4 it stops 68-88% of 100 new-stack attackers versus 43% and 34-66% on shared
  stacks versus none; on E1 it adds 11.4% of the tenth-size botnet on shared stacks but stops only
  11.8% on new ones, where the unseen filter stops 89.6%;
- metric 10: no fingerprint absent from the profile reached k_min origins in a block window.

The paper now reports the block as its own table (Table VII) and V-D's paragraphs "Prospectively,
the rate doubles" and "The comparison fixed in advance prefers the seasonal gate". The held-out
day keeps two sentences there and its Table VI columns; its rows left Table IV. Section VI
recommends the seasonal arm, as the protocol's metric 7 directs, with its costs (crowds of 1,000
users trigger it in a third of windows, its misfires block a median two thirds of a window, and
on E1 it gives up new stacks). The abstract, the conclusion and Appendices E and F follow. The
recommended scope's floors on E2-E4 (3-4 median windows on shared stacks, 2-3 on new ones) replace
the binomial's in Section VI.

Layout: 12 pages, no stretched column, Acknowledgment and the start of the references on p.8,
p.12 full; abstract 249 words, still 26 lines. Lines added on pp.1-4 move Sections II and V (one
extra line in contribution (ii) moved Section II's heading and cost five lines), so those edits
keep their line counts. `make audit`: 248 checks, 0 mismatches, with a new section that checks
Table VII cell by cell and every block number against the block's JSON; `make block-report-check`:
21 of 21.

## 70. Round 67: two reviews of the block

A NOMS-style pass (4/3/4/3/4, about the 80th percentile, "Ready to submit: yes") and a skeptical
pass focused on the block (4/3/4/3/4, about the 70th, "no" for one class A item) checked every
block number against the JSON files and found them right. The skeptical pass's A item was real:
both protocols say that every metric is reported whatever its value, and taking the held-out
day's rows out of Table IV had left its metrics 2, 3, 4 and 6 unreported. Appendix F now says that
the repository holds every metric both protocols name (`production_tables.json`'s `fresh_day`,
`block_report.json` and the block's reduction, all committed).

The other fixes, all verified against the results first:
- V-D gives metric 1's verdict in the protocol's word ("by the protocol's test, inconsistent with
  it"), says what P = 0.003 tests, and that on E1 the seasonal arm is preferred only for shared
  stacks, which the baseline cannot name;
- VI states the arm's 14 misfires on E1, where the binomial configuration had none, its fallback
  (235 other gate openings, 1.5% of clean windows), and the calibrated z-score, which misfired as
  often on fewer crowds but stopped less; it adds that no later day has tested the choice;
- VII: two of the three post hoc triggers held their budget; the floor it quotes is the
  binomial test's;
- App. E gives the two-sample view: counting the test days' own uncertainty, a one-sided Fisher
  test puts the rate's rise at P = 0.07 and the misfires once the gate opens at P = 0.0002, so the
  firm finding is the scope's lower reliability, more than the doubling;
- App. F: the addendum adds three metrics, and the amendment was adopted after the export and
  before any count was read; Table VII's note says each day is calibrated on all earlier days.

Paid for by one-word last lines (V-B, Table IV's and VII's notes, VI, App. E), App. E's sentences
on the in-sample beta-binomial's levels and the cross-fitted z-score at 100 attackers, and the
"median factor of 1.8" clause. A clearer z-score sentence that wrapped one line longer moved
Section VII's heading and cost four lines, so the shorter wording stayed. Layout: 12 pages, the
Acknowledgment and the references' heading where they were before the block (y = 579 and 670 on
p.8), about two free lines on p.12, abstract 249 words and 26 lines. `make audit`: 245 checks,
0 mismatches.

## 71. Round 68: the skeptical re-review

The skeptical pass, rerun on round 67, judged A1 resolved as long as the three block JSON files
are committed (4/3/4/3/4, about the 75th percentile, "Ready to submit: yes" on that condition),
and checked every new number against the files. It left five cheap items, all applied:
- App. F names the files that hold every metric (`production_tables.json`, `block_report.json`),
  and says the amended rule was adopted "before any result was computed", since raw rows were
  seen at export; `results/fresh_day_metrics_location.md` maps each held-out-day metric to its
  key, now that the day's rows left Table IV (the frozen addendum stays as it was);
- V-D labels the held-out day's conditional test post hoc (metric 8 was added for the block);
- VI puts the crowds and misfires before the fallback, so "it" keeps its referent;
- VII reorders its sentences so that "it" and "there" point to the busiest endpoint;
- App. E restores "though none qualifies in sample", and states that the z-score reference
  misfired less than the binomial configuration on the block (20 versus 31), fired on fewer crowds
  and stopped more of 100 attackers.

Paid for by "The block's 14 days" in V-D and App. E's sentence on the base rule's test-day crowds
(its block value is in Table VII). Marking Table VII's post hoc rows with an asterisk lengthens
its note by a line and gives 13 pages, so it stayed out. 12 pages, Acknowledgment and references
at y = 579 and 670 on p.8, p.12 full; `make audit`: 244 checks, 0 mismatches.

## 72. Round 69: an outside clarity review, and the AI disclosure

An outside clarity review of 2026-10-11 (kept out of the repository) found the English mostly
natural and no grammar errors. Its points were ellipses, referents far from their words and the
chronology of the experimental decisions. Six of its ten points were applied, each checked by
the skeptical pass and for layout:
- P1, V-D: "The 14-day block was exported after its protocol was public and analyzed after its
  export hashes were published". It removes the ellipsis "after their hashes were" and names the
  exact action: the hashes were pushed publicly (`ad7c03b`), not only recorded;
- P4, V-D: the sentence with 31 of 16,103 splits into the observation and the inference, and keeps
  the protocol's verdict word, "inconsistent", rather than the review's "differed";
- P2 and P5, VI: "Now our candidate is the cross-fitted beta-binomial behind the seasonal gate ...
  It was built post hoc, but the comparison fixed in advance preferred it on every endpoint". It
  states the recommendation's status, and the paragraph keeps its three caveats (the loss on E1,
  "Running both there is untested" and "no later day has tested this choice");
- P8, VII: "because the scope misfires in 13% of gate openings". The review worried that "as"
  links rates with different denominators. The link is an identity: the joint rate is the gate's
  rate times the scope's misfires once the gate opens, 1.45% x 13.3% = 0.19% on the block against
  2.98% x 2.98% = 0.09% on the test days. The gate opened half as often, so the doubling comes from
  the scope, and the audit checks that decomposition;
- P9, VII: "two of three post hoc configurations held their budget", since configuration 4 changes
  the scope too.

Declined, and the skeptical pass agreed:
- P3, the abstract: "their" refers to "These misfires" in the sentence before, the abstract is at
  249 words and 26 lines, and the rate once the gate opens is in V-D and VII;
- P6: the review itself calls "Two limits decide per endpoint" acceptable;
- P7: IV-B, V-C's first sentence and Table VI's note already say what "No gate" means and that
  the rates count every window;
- P10: all four V-D paragraphs already open with their evidence status.

The skeptical pass, rerun on these edits (4/3/4/3/4, about the 75th percentile, no class A item,
"Ready to submit: yes"), raised one B item: the AI disclosure named text and code, but neither the
ontology, which is contribution (iii), nor Fig. 1's drawing. The git history agrees with it:
- the ontology was created on 2026-04-14 without the assistant, and 9 of its 11 commits carry its
  co-author trailer;
- each of the other 73 code files, following renames, was created in a commit with that trailer;
- both commits of Fig. 1's draw.io source carry it.

The Acknowledgment now reads "to draft and edit text in all sections, to extend the ontology and
to write all code and figures. The authors reviewed and verified all content and take full
responsibility for it". IEEE's policy asks for this: AI-generated text, figures, images and code
are disclosed in the Acknowledgment, with the sections and the level of use. The wording keeps
every line where it was.

Tested and not applied: the pass's C1, "On the block the configuration misfired" in place of
"There", which can be read as pointing to Appendix F; with its cut it gives 13 pages. Its C2 needs
no text change: in clients, the candidate's 14 misfires on E1, the busiest endpoint, cost far more
than the binomial configuration's 31 on the small ones. A reader can infer it from "busiest
endpoint" and "two thirds", so it is kept for the rebuttal.

Layout: 12 pages, the Acknowledgment and the references' heading at y = 579 and 670 on p.8, p.12
full, abstract 249 words and 26 lines. `make audit`: 244 checks, 0 mismatches;
`make block-report-check`: 21 of 21.

## 73. Round 70: a sentence-level review

An outside review of single sentences (kept out of the repository) made seven points. Two
changed the text, and each kept every line where it was:
- IV-B: "Cross-fitting, built post hoc, judges each calibration day, like a test day, against a
  profile of the other days". It names the day that "it" stood for and removes the ellipsis "as a
  test day is". "Built post hoc" stays, the paper's term everywhere, in place of the review's
  "introduced";
- V-D: "The gate opened half as often, but the scope misfired in 31 of its 233 openings".
  Round 69's split had put a sentence between "Its gate" and "the configuration". The review's
  "compared with 5 of 168 on the test days" gives 13 pages and drops the P value, and the same
  paragraph already says "the test days' 5 of 168 openings".

Declined: in VI, "It was built post hoc" stays. "It" picks up "our candidate", the subject of the
sentence before, and the skeptical pass approved the sentence in round 69. Both explicit versions
("The candidate", "This configuration") reflow the paragraph, move Section VII's heading and give
13 pages. The review's passive would also drop "the comparison fixed in advance", the name of
V-D's paragraph. Splitting "20 versus 31, though 14 versus none" in VI also costs lines, and the
review itself says the sentence can stay.

Checked, with no change: VI gives the candidate's costs right after the recommendation, IV-B
defines Coll. as a median over alarms, and nowhere does the paper equate the budget with low risk.
VII's "two of three post hoc configurations held their budget" is prospective: the protocol fixed
those configurations before the block. What no later day has tested is the choice made on the
block, and VI says so.

12 pages, the Acknowledgment and the references' heading at y = 579 and 670 on p.8, pages 5-8
with the same number of lines. `make audit`: 244 checks, 0 mismatches, with three pins moved to
the new wording; `make block-report-check`: 21 of 21.

## 74. Round 71: Listing 1's place, the budget in windows, and a generic review

Two reader questions from the user:
- the body cited Listing 1 twice (III-B, III-E) with no pointer to Appendix D, where it sits on
  p.11, and its caption did not show where the 91% comes from. Both citations now add "Appendix D",
  and the caption says "Endpoint pairs carry 91% of Ω". Explaining in III-B what the listing is ("as
  its evidence chain shows") gives 13 pages;
- III-C's "about 2.9 of a day's 288" left "windows" implied. It is the only place the body says a day
  has 288 windows, which V-C's "8 of 288" relies on, so it stays, as "288 windows".

An outside review of 2026-10-18 (kept out of the repository) made nine general recommendations,
most of them already met by the text. Four small edits came from it:
- III-C names λ_e where the test first uses it ("unlikely under the binomial background at level
  λ_e"), instead of a paragraph later;
- III-D gives the floor's meaning before its definition ("the calibration floor: the botnet size from
  which the scope names a typical stack") and drops the later sentence that said it;
- III-C says in words why the modal fingerprint fails: "With more stacks, each one smaller, the
  filter blocks users and no attackers";
- IV-A says the production evaluation is offline ("The scope is evaluated offline, behind the
  operator's WAF"); only App. C said so.

Not applied: a decision rule at the end of the conclusion, which gives 13 pages in every wording
tried (the rule is in VI and in the abstract's last sentence), and a rewrite of VII with fewer
numbers, a structural change.

Layout: 12 pages, every page from 1 to 8 with the same number of lines, the Acknowledgment and the
references' heading at y = 579 and 670 on p.8. `make audit`: 244 checks, 0 mismatches, with two pins
moved to the new wording; `make block-report-check`: 21 of 21.

## 75. Round 72: two appendix titles, and the venue's rules rechecked

Two outside reviews of 2026-10-18 (kept out of the repository) covered the abstract and the
appendices.
- The abstract they proposed fits the layout but drops qualifiers earlier reviews required: "on the
  days used to choose them", "though each alone exceeds its 1% budget", the misfires' median third,
  "pre-specified", the floor's "rare fingerprints that real clients share", "A botnet on common
  fingerprints mostly escapes", "On the busiest endpoint", the exchange gap. The abstract stays.
- Two appendix titles now say what the appendices hold: B is "Weight Calibration and Generator
  Inputs" (the body sends the reader there for the generated sessions), and C is "Additional
  Experiments and Limitations" (it holds the laboratory captures, KLAGE and the learned models).
  New subsections and a table do not fit (p.12 is full, and the run-in headings already divide the
  appendices), renaming E "Supplementary Production Results" would be wrong (E opens with generated
  traffic), and a sentence in D on deployed latency gives 13 pages.

The NOMS 2027 rules were rechecked on the official pages: submission through JEMS3
(https://jems3.sbc.org.br/noms2027), which the CFP and the TPC's announcement link, though the
Submission Guidelines page still says EDAS; paper registration and submission on 9 November 2026;
8 + 4 = 12 pages, the 8-page main part self-contained. The paper README's checklist now lists the
open decisions this raised: IEEE's preprint notice for the public PDF, an ethics statement, and two
camera-ready items. Layout unchanged on every page; `make audit`: 244 checks, 0 mismatches.

## 76. Round 73: a non-technical clarity review

An independent reviewer read the paper as a networking researcher who is not a specialist in
statistics, application-layer DDoS or ontologies, using an outside clarity brief of 2026-10-18 (kept
out of the repository) as the framework. It scored the current text 7/10, against the brief's 6.5 on
an earlier version, and judged the brief's three top priorities met (III-C, III-D, and trigger versus
scope versus end to end). Nine of its local fixes were applied, each tested for layout:
- VII opens with the lesson: "Fingerprint scoping, a calibrated test specified in a session ontology,
  pays off where attack fingerprints differ from legitimate ones, botnets pass the floor and the
  trigger fires", in place of a restatement of the method;
- III-D: "Lower, stricter levels raise the floor", and "there ρ also limits which fingerprints can be
  named" for "the ratio sets a harder limit";
- III-E: `relatedTo` sub-properties "classify" the evidence, where "type" read as a noun;
- III-B: the base rule "fires when the coordination mass Ω(S) (...) reaches its threshold";
- IV-B: the sentence repeating the gates (III-B, Table II) is cut, and in-sample calibration says why
  it matters: "so its own fleets look less enriched";
- V-D: "On the busiest endpoint the preference rests on shared stacks alone", which no longer reads
  against "preferred (...) on every endpoint";
- VI: "On its gate's other clean openings, 1.5% of windows, the scope names nothing and the fallback
  acts";
- abstract: "on those 14 days", so the post hoc triggers' days are named (250 words).

Tested and not applied, each giving 13 pages: where 10⁻⁶⁰ comes from in III-C, a pointer from IV-A to
App. F for the held-out day's caveat, and the post hoc marks on Table VII. Moving VI's paragraph on
what the scope needs to the section's start fits but was left out. 12 pages, Acknowledgment and
references in place; `make audit`: 244 checks, 0 mismatches, four pins moved; `make
block-report-check`: 21 of 21.
