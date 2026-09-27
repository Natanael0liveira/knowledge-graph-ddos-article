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
/24-pair match. Its JA4 class sizes lie between the export's clean and total counts
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
  and the JA4 class sizes in the 288 windows where the WAF blocked no client
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
  origin and /24-pair counts and the JA4 class sizes where the WAF blocked no client
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
