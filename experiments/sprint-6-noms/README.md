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
| `scripts/rule_detection_production.py` | The rule had **never met production traffic**: every window so far came from the generator | Yes, and the production exports |

```bash
make latency      # runs anywhere
make all-hd       # ml + window, needs the drive mounted
make drift        # profile drift, plus the M = 100 run with a pooled profile
make baselines    # Table II baseline rows
make rule         # the rule as a window-level detector (Appendix E)
make rule-production  # the same rule on production traffic, botnet injected (section 9)
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

## 8. Audit of the paper's numbers

`make audit` runs `scripts/audit_paper.py`, which recomputes every number this
sprint contributes to the paper (Table III rows as printed, Section V-B and V-D
text, Fig. 3 bars, the drift figures, Table VI and Appendix E) from the committed
files in `results/`, and compares them with the literal text of
`papers/http-session-noms/article.tex`. It also checks that Table III
(`symbolic_detector.py`) and Fig. 3 (`realistic_probe.py`), two independent
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
one or two origins, which no calibrated level certifies, and Ω stays within the
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
calibrated level certifies (0.0% / 3.9% blocked by the scope alone).

**At a tenth of the typical window only E1 is in the stealth regime** (over 100
attackers; the others get fewer than ten). There the calibrated level (10⁻⁶⁰)
holds enrichment to 0.6%, against 11.2% for the unseen filter and 12.5% for the
z-score, which fires on 5.1% of E1's clean windows; the union recovers 11.2%, and
with shared stacks only the z-score stops any (12.2%). Pooled, no scope passes 5%,
which is why the paper reports E1 separately.

**ρ barely matters** (`--rho 2`, `--rho 5`, tags `_rolling_origin_rho2/5`, in
`variants.rho2/rho5`). No pooled entry of Table VI that depends on ρ moves by more
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
attack-share choice had picked a one-session cluster. Table III and Fig. 3 move
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
The Random Forest of Table III reads no profile of normal traffic; given it as two
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
operator's ClickHouse (21.8) for 2026-09-23, the compiled query returned the
exported origin and /24-pair counts in all 1,152 windows** (`--compare`,
`results/compile_production_check.json`). Its JA4 class sizes lie between the
export's clean and total counts in every window and equal the clean ones in all
288 windows without a WAF-blocked client: the export drops a client the WAF
blocked part of the time, the compiled filter (requests the WAF did not block) keeps it.

**The STIX export is valid STIX 2.1** (`make stix-check`, `scripts/stix_check.py`,
`results/stix_validation.json`): four bundles, built from the committed JSON-LD
chains alone, pass the OASIS `stix2-validator` with no error or warning, in strict
mode too, and parse with the `stix2` library. See the pillar-4 README for the
format.

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
(`scripts/fleet_selection.py`):

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
5.1% of E1's clean windows. Computed after the choice and for transparency only
(`held_out_secondary_all_shares`), the smaller shares keep the same trade-off on
the held-out days: 13–16 false alarms at a median 10.6–12.2% collateral, flash
crowds of 100 fired on 6.6–11.0%, mean blocked 30.3–33.8%, E1 at 0.1× 6.5% /
5.7–5.9%. The control rerun without `--fleets` reproduces the base per-window CSV
byte for byte.
