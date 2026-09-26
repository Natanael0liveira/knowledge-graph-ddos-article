#!/usr/bin/env python3
"""Sprint 6 (NOMS) — does configuration (d) learn coordination or the stack-size band?

Question
--------
Table II trains and tests configuration (d), the cross-session representation
(the strong flow features plus share_ja4, share_net and cluster_size), on a 70/30
split of the sessions of ONE generated campaign (run_canonical_realistic.one_run).
A reviewer asked whether (d) then learns coordination, or merely the band of
share_ja4 values produced by the generator's number of botnet TLS stacks M. With
K = 1,000 bots, 90% of them on a shared stack drawn uniformly from M stacks, each
stack groups about 900/M sessions. So an attack session's share_ja4 sits near 180
at M = 5, 35 at M = 25 and 8 at M = 100, while a benign session's share_ja4 is set
by the Zipf rank of its fingerprint. A model that learned one band has no reason
to score another band as attack. This script trains on campaigns with one M and
tests on campaigns with another.

Protocol
--------
Every scenario is a cached generator output a{alpha}_m{M}_adv0_K{K}_seed{seed}.parquet
at alpha = 1.5 and K = 1,000. Features, labels, preprocessing, split and estimator
are those of the canonical ablation: build_features from sprint-3 run_ablation.py,
_is_attack on label_first, STRONG_SETS from run_sprint4.py for configurations (a)
and (d), inf -> NaN -> 0, train_test_split(test_size=0.3, random_state=42,
stratify=y), and models(42)["rf"] from run_ml_families.py, capped at n_jobs = 2
(which does not change the trees). Only the train/test assignment changes:

  in_distribution    Table II's procedure: one model per test scenario, trained on
                     its 70% rows and scored on its 30% rows.
  cross_seed_same_m  one model trained on the 70% rows of the scenarios with the
                     SAME M whose seeds are in the other half, scored on the 30%
                     rows of the test scenario. It controls for the pooled,
                     cross-scenario protocol while holding M fixed.
  cross_m            the same pooled protocol, with training scenarios drawn from
                     a DIFFERENT M.

Seeds 1-15 are split into halves 1-7 and 8-15. A model trained on one half scores
the test scenarios of the other half; then the halves swap. So each of the 15 test
scenarios of a direction gets exactly one AUC per protocol, and the three numbers
are paired on the same held-out sessions. Each number is reported as the mean over
test scenarios with a bootstrap 95% CI over test scenarios (boot_ci from
run_sprint4.py). The same is done for the paired differences. As a check that the
pipeline is the canonical one, the M = 25 in-distribution AUCs are recomputed on
seeds 1-30 and compared, seed by seed, with results/canonical_realistic_runs.csv.

Leakage check
-------------
The generator draws the ASN pool and all 1,000 benign sessions from
random.Random(seed) before anything that depends on M. So two scenarios with the
same seed and different M carry the same benign sessions. The attack sessions of
M = 25 and M = 100 also coincide in everything except the stack label. The reason
is that random.choice over 25 and over 100 stacks rejects the same 32-bit draws, so
both consume the random stream identically (the stack for 25 is the stack for 100
divided by 4). With 5 stacks the rejection threshold differs, so the stream
desynchronizes at the first draw that only one of the two rejects.

The script measures all of this with 64-bit row hashes keyed by session_id, for
every seed and pair of M. The hashes cover full rows, per-session behaviour (every
column except identifiers, fingerprints and labels) and the (a) and (d) feature
rows. It then checks that no session, (a) row or (d) row of a test scenario in the
disjoint-seed protocol appears in the scenarios its model was trained on. A test
session counts as a copy only if its behaviour hash (source address and port,
timestamps, volumes) is found. An equal (a) row with a different behaviour hash is
a coincidence of values: single-request sessions whose byte counts fall on a flat
segment of the calibrated quantiles recur across seeds, in both classes. For
reference only, it also reports what a same-seed design would have scored: each
model scored on all sessions of the test-M scenarios from its own seed half, next
to the disjoint-seed score on all sessions.

Resource discipline: run under nice (make cross-m), n_jobs = 2, and one scenario
DataFrame in memory at a time. Only the feature matrices and hashes (a few MB) are
kept.

Usage:
    python cross_m_generalization.py --work $DATA_ROOT/synth/sprint6_realistic \\
        --out-dir ../results
"""
import argparse
import itertools
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "sprint-1" / "scripts"), str(EXP / "sprint-3" / "scripts"),
                str(EXP / "sprint-4" / "scripts"), str(HERE.parent)]
from run_ablation import build_features  # noqa: E402
from run_sprint4 import STRONG_SETS, boot_ci  # noqa: E402
from compute_coordination import _is_attack  # noqa: E402
from run_ml_families import models  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CONFIGS = {"a": "a_ml_sem_ontologia", "d": "d_completo"}
SEED = 42    # one_run's default: the seed of the 70/30 split and of the estimator
N_JOBS = 2
# Columns that name a session, its fingerprint or its label. Every other column
# describes the session's behaviour. The stack names and the shared token embed the
# seed, so a session copied under another seed would differ only in these columns.
NAMES_AND_LABELS = ["session_id", "ja4", "identity_token", "is_attack", "campaign_id",
                    "label_first", "ja3", "sni"]
RESULTS = HERE.parents[1] / "results"


def row_hashes(frame):
    """64-bit hash of every row (pandas.util.hash_pandas_object), index ignored."""
    return pd.util.hash_pandas_object(frame, index=False).to_numpy()


def prepare(pq):
    """One scenario, prepared exactly as run_canonical_realistic.one_run prepares it.

    Returns the (a) and (d) matrices, the labels, the canonical 70/30 split and the
    row hashes of the leakage check. The DataFrames are released on return.
    """
    raw = pd.read_parquet(pq)
    df = build_features(raw)
    y = _is_attack(df["label_first"]).astype(int).values
    if y.sum() < 2 or y.sum() == len(y):
        return None
    itr, ite = train_test_split(np.arange(len(y)), test_size=0.3,
                                random_state=SEED, stratify=y)
    X = {c: df[STRONG_SETS[name]].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
         for c, name in CONFIGS.items()}
    hashes = pd.DataFrame({
        "full": row_hashes(raw.drop(columns=["session_id"]).astype(str)),
        "behaviour": row_hashes(raw.drop(columns=NAMES_AND_LABELS).astype(str)),
    }, index=raw["session_id"].to_numpy())
    feat = pd.DataFrame({c: row_hashes(pd.DataFrame(X[c])) for c in CONFIGS},
                        index=df["session_id"].to_numpy())
    feat["attack"] = y
    return {"X": X, "y": y, "itr": itr, "ite": ite, "hashes": hashes.join(feat)}


def rf():
    """The canonical estimator, models(42)["rf"], capped at N_JOBS threads."""
    return models(SEED)["rf"].set_params(n_jobs=N_JOBS)


def in_distribution_auc(s, c):
    """Table II's number for one scenario: train on its 70% rows, score its 30%."""
    X, y = s["X"][c], s["y"]
    est = rf().fit(X[s["itr"]], y[s["itr"]])
    return roc_auc_score(y[s["ite"]], est.predict_proba(X[s["ite"]])[:, 1])


def fit_pooled(scens, c):
    """One model on the 70% training rows of several scenarios."""
    X = np.vstack([s["X"][c][s["itr"]] for s in scens])
    y = np.concatenate([s["y"][s["itr"]] for s in scens])
    return rf().fit(X, y), len(y)


def score(est, s, c):
    """AUC on the canonical 30% held-out rows and on all sessions of a test scenario."""
    X, y = s["X"][c], s["y"]
    p = est.predict_proba(X)[:, 1]
    return roc_auc_score(y[s["ite"]], p[s["ite"]]), roc_auc_score(y, p)


def summary(vals):
    """Mean and bootstrap 95% CI over test scenarios."""
    mean, lo, hi = boot_ci(np.asarray(vals, dtype=float))
    return {"mean": mean, "ci95": [lo, hi], "n": int(len(vals))}


def seed_range(seeds):
    return f"{seeds[0]}-{seeds[-1]}"


def same_seed_overlap(S, ms, seeds):
    """Identical rows between scenarios that share a seed but differ in M."""
    out = {}
    for m1, m2 in itertools.combinations(ms, 2):
        per = {cls: {col: [] for col in ("full", "behaviour", "a", "d")}
               for cls in ("benign", "attack")}
        benign_tables_identical = 0
        for seed in seeds:
            h1, h2 = S[m1, seed]["hashes"], S[m2, seed]["hashes"]
            assert set(h1.index) == set(h2.index), "session ids differ across M"
            h2 = h2.reindex(h1.index)
            assert (h1["attack"] == h2["attack"]).all(), "labels differ across M"
            for cls, flag in (("benign", 0), ("attack", 1)):
                sel = h1["attack"] == flag
                for col in per[cls]:
                    per[cls][col].append(int((h1.loc[sel, col] == h2.loc[sel, col]).sum()))
            ben = h1["attack"] == 0
            benign_tables_identical += int((h1.loc[ben, "full"] == h2.loc[ben, "full"]).all())
        n_cls = {cls: int((S[m1, seeds[0]]["hashes"]["attack"] == flag).sum())
                 for cls, flag in (("benign", 0), ("attack", 1))}
        out[f"m{m1} vs m{m2}"] = {
            "seeds": len(seeds),
            "seeds_with_identical_benign_session_table": benign_tables_identical,
            "identical_rows_per_scenario": {
                cls: {col: {"min": min(v), "max": max(v), "mean": float(np.mean(v)),
                            "of": n_cls[cls]} for col, v in cols.items()}
                for cls, cols in per.items()}}
    return out


def disjoint_overlap(S, m_train, m_test, halves):
    """Test rows of the disjoint-seed protocol that appear in its training scenarios."""
    seen = {"sessions": 0, "a_rows": 0, "d_rows": 0}
    checked = 0
    for f in (0, 1):
        tr = pd.concat([S[m_train, s]["hashes"] for s in halves[f]])
        for s in halves[1 - f]:
            te = S[m_test, s]["hashes"]
            seen["sessions"] += int(np.isin(te["behaviour"], tr["behaviour"]).sum())
            seen["a_rows"] += int(np.isin(te["a"], tr["a"]).sum())
            seen["d_rows"] += int(np.isin(te["d"], tr["d"]).sum())
            checked += len(te)
    return {"test_rows_checked": checked, **{f"test_{k}_found_in_training": v
                                             for k, v in seen.items()}}


def diagnostics(S, ms, seeds):
    """Where each class sits on the cross-session features, per M (seeds pooled)."""
    d = list(STRONG_SETS[CONFIGS["d"]])
    ij, inet = d.index("share_ja4"), d.index("share_net")
    out = {}
    for m in ms:
        X = np.vstack([S[m, s]["X"]["d"] for s in seeds])
        y = np.concatenate([S[m, s]["y"] for s in seeds])
        out[f"m{m}"] = {}
        for cls, flag in (("attack", 1), ("benign", 0)):
            ja4, net = X[y == flag, ij], X[y == flag, inet]
            out[f"m{m}"][cls] = {
                "share_ja4_percentiles_5_25_50_75_95":
                    [float(v) for v in np.percentile(ja4, [5, 25, 50, 75, 95])],
                "share_ja4_zero_fraction": float((ja4 == 0).mean()),
                "share_net_positive_fraction": float((net > 0).mean())}
    return out


def main():
    started = time.perf_counter()
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", required=True, type=Path,
                    help="cached scenarios (read only; nothing is generated)")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--alpha", type=float, default=1.5)
    ap.add_argument("--K", type=int, default=1000)
    ap.add_argument("--pairs", nargs="+", default=["5:25", "5:100", "25:5", "25:100"],
                    help="train_M:test_M directions")
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--split-at", type=int, default=7,
                    help="the seed halves are 1..split_at and split_at+1..seeds")
    ap.add_argument("--canonical-seeds", type=int, default=30,
                    help="M=25 seeds whose in-distribution AUC is compared with "
                         "canonical_realistic_runs.csv (0 = skip)")
    ap.add_argument("--canonical-runs", type=Path,
                    default=RESULTS / "canonical_realistic_runs.csv")
    ap.add_argument("--canonical-json", type=Path,
                    default=RESULTS / "canonical_realistic.json")
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    pairs = [tuple(int(x) for x in p.split(":")) for p in args.pairs]
    ms = sorted({m for p in pairs for m in p})
    seeds = list(range(1, args.seeds + 1))
    halves = (seeds[:args.split_at], seeds[args.split_at:])

    def path(m, seed):
        return args.work / f"a{args.alpha}_m{m}_adv0_K{args.K}_seed{seed}.parquet"

    missing = [str(path(m, s)) for m in ms for s in seeds if not path(m, s).exists()]
    if missing:
        sys.exit("missing cached scenarios (this script never generates them):\n"
                 + "\n".join(missing))

    # ---- 1. every scenario once: canonical features + in-distribution AUC ----
    S, rows, ind_auc = {}, [], {}

    def add_in_distribution(m, seed, s):
        for c in CONFIGS:
            ind_auc[m, seed, c] = in_distribution_auc(s, c)
            rows.append({"protocol": "in_distribution", "config": c, "m_train": m,
                         "m_test": m, "fold": "", "train_seeds": str(seed),
                         "test_seed": seed, "auc_heldout": ind_auc[m, seed, c],
                         "auc_all": float("nan"), "n_train": len(s["itr"]),
                         "n_heldout": len(s["ite"]), "n_all": len(s["y"])})

    for m in ms:
        for seed in seeds:
            s = prepare(path(m, seed))
            if s is None:
                sys.exit(f"degenerate labels in {path(m, seed)}")
            S[m, seed] = s
            add_in_distribution(m, seed, s)
        log.info("M=%d: %d scenarios prepared", m, len(seeds))

    # ---- 2. the in-distribution pipeline against the canonical run (M=25) ----
    # Seeds outside the cross-M design are prepared one at a time and not kept.
    validation = None
    if args.canonical_seeds and args.canonical_runs.exists():
        canon = json.loads(args.canonical_json.read_text())
        runs = pd.read_csv(args.canonical_runs)
        runs = runs[runs["K"] == args.K].set_index("seed")
        mc = int(canon["stacks"])
        if float(canon["alpha"]) != args.alpha:
            log.warning("canonical run is at alpha=%s; skipping validation", canon["alpha"])
        else:
            diffs = {c: [] for c in CONFIGS}
            ind25 = {c: [] for c in CONFIGS}
            for seed in range(1, args.canonical_seeds + 1):
                if seed not in runs.index or not path(mc, seed).exists():
                    continue
                if (mc, seed) not in S:
                    add_in_distribution(mc, seed, prepare(path(mc, seed)))
                for c, name in CONFIGS.items():
                    ind25[c].append(ind_auc[mc, seed, c])
                    diffs[c].append(abs(ind_auc[mc, seed, c]
                                        - float(runs.loc[seed, f"rf|{name}"])))
            agg = canon["aggregate"][f"K={args.K}"]
            validation = {
                "m": mc, "seeds_compared": len(diffs["a"]),
                "max_abs_diff_vs_canonical_runs_csv": {c: float(max(v))
                                                       for c, v in diffs.items()},
                "recomputed_in_distribution": {c: summary(v) for c, v in ind25.items()},
                "canonical_realistic_json": {
                    c: {**agg[f"rf|{name}"], "n": int(agg["n"])}
                    for c, name in CONFIGS.items()}}
            log.info("canonical check (M=%d, %d seeds): max |diff| a=%.2e d=%.2e", mc,
                     len(diffs["a"]), max(diffs["a"]), max(diffs["d"]))

    # ---- 3. leakage check ----
    leakage = {
        "method": "64-bit row hashes keyed by session_id: full rows (all columns but "
                  "session_id), per-session behaviour (all columns but "
                  + ", ".join(NAMES_AND_LABELS) + ") and the (a) and (d) feature rows "
                  "after the canonical preprocessing",
        "reading": "a test session is a copy only if its behaviour hash is found in the "
                   "training scenarios; an equal (a) or (d) row with a different behaviour "
                   "hash is a coincidence of values (e.g. single-request sessions whose "
                   "byte counts fall on a flat segment of the calibrated quantiles)",
        "same_seed_different_m": same_seed_overlap(S, ms, seeds),
        "disjoint_seed_protocol": {
            f"{mtr}->{mte}": disjoint_overlap(S, mtr, mte, halves)
            for mtr, mte in pairs + [(m, m) for m in sorted({p[1] for p in pairs})]}}

    # ---- 4. pooled models: one per (training M, config, seed half) ----
    importances = {}
    d_feats = list(STRONG_SETS[CONFIGS["d"]])
    for mtr in ms:
        targets = [mte for p_tr, mte in pairs if p_tr == mtr]
        if mtr in {p[1] for p in pairs}:
            targets = [mtr] + targets           # the same-M control
        if not targets:
            continue
        for c in CONFIGS:
            for f in (0, 1):
                train, test = halves[f], halves[1 - f]
                est, n_train = fit_pooled([S[mtr, s] for s in train], c)
                if c == "d":
                    importances.setdefault(f"m{mtr}", []).append(est.feature_importances_)
                for mte in targets:
                    plan = [("cross_seed_same_m" if mte == mtr else "cross_m", test)]
                    if mte != mtr:
                        plan.append(("same_seed_reference", train))
                    for protocol, test_seeds in plan:
                        for seed in test_seeds:
                            s = S[mte, seed]
                            auc_ho, auc_all = score(est, s, c)
                            rows.append({"protocol": protocol, "config": c,
                                         "m_train": mtr, "m_test": mte, "fold": f,
                                         "train_seeds": seed_range(train),
                                         "test_seed": seed, "auc_heldout": auc_ho,
                                         "auc_all": auc_all, "n_train": n_train,
                                         "n_heldout": len(s["ite"]), "n_all": len(s["y"])})
            log.info("training M=%d, config %s: done", mtr, c)

    runs = pd.DataFrame(rows)
    runs.to_csv(args.out_dir / "cross_m_generalization_runs.csv", index=False)

    # ---- 5. aggregate over test scenarios, paired by test seed ----
    def vec(protocol, c, mtr, mte, col="auc_heldout"):
        sub = runs[(runs["protocol"] == protocol) & (runs["config"] == c)
                   & (runs["m_train"] == mtr) & (runs["m_test"] == mte)]
        return sub.set_index("test_seed").loc[seeds, col].to_numpy(dtype=float)

    aggregate = {}
    for mtr, mte in pairs:
        key = f"{mtr}->{mte}"
        aggregate[key] = {}
        for c in CONFIGS:
            ind = vec("in_distribution", c, mte, mte)
            same = vec("cross_seed_same_m", c, mte, mte)
            cross = vec("cross_m", c, mtr, mte)
            by_fold = {}
            for f in (0, 1):
                sel = np.isin(seeds, halves[1 - f])
                by_fold[f"train {seed_range(halves[f])} -> test {seed_range(halves[1 - f])}"] = {
                    "in_distribution": float(ind[sel].mean()),
                    "cross_seed_same_m": float(same[sel].mean()),
                    "cross_m": float(cross[sel].mean())}
            aggregate[key][c] = {
                "in_distribution": summary(ind),
                "cross_seed_same_m": summary(same),
                "cross_m": summary(cross),
                "cross_m_minus_in_distribution": summary(cross - ind),
                "cross_m_minus_cross_seed_same_m": summary(cross - same),
                "by_fold": by_fold,
                "all_sessions": {
                    "cross_seed_same_m": summary(vec("cross_seed_same_m", c, mte, mte, "auc_all")),
                    "cross_m": summary(vec("cross_m", c, mtr, mte, "auc_all")),
                    "same_seed_reference_leaky":
                        summary(vec("same_seed_reference", c, mtr, mte, "auc_all"))}}

    result = {
        "question": "does configuration (d) learn coordination or the generator's "
                    "stack-size band? train on campaigns with M botnet TLS stacks, "
                    "test on campaigns with another M",
        "alpha": args.alpha, "K": args.K, "pairs": [f"{a}->{b}" for a, b in pairs],
        "seed_halves": [list(h) for h in halves],
        "configs": {c: STRONG_SETS[name] for c, name in CONFIGS.items()},
        "estimator": f"run_ml_families.models({SEED})['rf'] with n_jobs={N_JOBS}",
        "split": "train_test_split(np.arange(n), test_size=0.3, random_state=42, "
                 "stratify=y), as run_canonical_realistic.one_run",
        "protocols": {
            "in_distribution": "one model per test scenario on its 70% rows, scored on "
                               "its 30% rows (Table II's procedure)",
            "cross_seed_same_m": "one model on the 70% rows of the same-M scenarios of "
                                 "the other seed half, scored on the test scenario's 30% rows",
            "cross_m": "one model on the 70% rows of the training-M scenarios of the "
                       "other seed half, scored on the test scenario's 30% rows",
            "same_seed_reference_leaky": "reference only: the cross_m model scored on "
                                         "the test-M scenarios of its OWN seed half, "
                                         "all sessions"},
        "ci": "bootstrap 95% over test scenarios (run_sprint4.boot_ci, 2000 resamples)",
        "canonical_validation": validation,
        "leakage_check": leakage,
        "aggregate": aggregate,
        "diagnostics": {
            "cross_session_features_by_m": diagnostics(S, ms, seeds),
            "rf_d_feature_importance_by_training_m": {
                k: dict(zip(d_feats, np.mean(v, axis=0).round(4).tolist()))
                for k, v in importances.items()}}}
    (args.out_dir / "cross_m_generalization.json").write_text(json.dumps(result, indent=2))

    # ---- report ----
    def cell(x, sign=""):
        return f"{x['mean']:{sign}.3f} [{x['ci95'][0]:{sign}.3f},{x['ci95'][1]:{sign}.3f}]"

    print("\n" + "=" * 106)
    print(f"CROSS-M GENERALIZATION — alpha={args.alpha}, K={args.K}, RF. Per-session ROC "
          f"AUC, mean [95% CI] over {len(seeds)} test scenarios (30% held-out rows)")
    print("=" * 106)
    print(f"{'direction':<11}{'cfg':<5}{'in-distribution':>22}{'cross-seed same M':>22}"
          f"{'cross-M':>22}{'cross-M - in-dist':>24}")
    for key, block in aggregate.items():
        for c in CONFIGS:
            b = block[c]
            print(f"{key:<11}{'(' + c + ')':<5}"
                  + "".join(cell(b[k]).rjust(22) for k in
                            ("in_distribution", "cross_seed_same_m", "cross_m"))
                  + cell(b["cross_m_minus_in_distribution"], "+").rjust(24))
    print("\nreference only, AUC on all sessions: same-seed design (leaky) vs disjoint seeds")
    for key, block in aggregate.items():
        print(f"  {key}: " + "; ".join(
            f"({c}) {block[c]['all_sessions']['same_seed_reference_leaky']['mean']:.3f} vs "
            f"{block[c]['all_sessions']['cross_m']['mean']:.3f}" for c in CONFIGS))
    if validation:
        print(f"\ncanonical check, M={validation['m']} ({validation['seeds_compared']} "
              f"seeds): max |AUC - canonical_realistic_runs.csv| = "
              f"{validation['max_abs_diff_vs_canonical_runs_csv']}")
    print("\nleakage, same seed across M (identical rows per scenario, min-max):")
    for k, v in leakage["same_seed_different_m"].items():
        r = v["identical_rows_per_scenario"]
        print(f"  {k}: benign tables identical in {v['seeds_with_identical_benign_session_table']}"
              f"/{v['seeds']} seeds; " + "; ".join(
                  f"{cls} {col} {r[cls][col]['min']}-{r[cls][col]['max']}/{r[cls][col]['of']}"
                  for cls in ("benign", "attack") for col in ("behaviour", "a", "d")))
    print("leakage, disjoint-seed protocol (test rows found in training scenarios):")
    for k, v in leakage["disjoint_seed_protocol"].items():
        print(f"  {k}: " + ", ".join(f"{kk}={vv}" for kk, vv in v.items()))
    print(f"\nOK: {args.out_dir}/cross_m_generalization.json + cross_m_generalization_runs.csv"
          f"  ({time.perf_counter() - started:.0f} s)")


if __name__ == "__main__":
    main()
