#!/usr/bin/env python3
"""The unseen-fingerprint filter on the synthetic scenarios of Table II and Fig. 2,
and a shared-stacks mode that mirrors the production evaluation's ``tail`` source.

It reads the cached scenarios and attack-free runs read-only and writes only to --out-dir.

* Code: the functions the paper's scripts use:
    - cluster, Omega, label-free largest-Omega cluster, calibrated level:
      compute_coordination, level_calibration (as symbolic_detector.py and
      realistic_probe.py call them with --unit origin --calibrate-level
      --significance 0.01 --label-free-cluster);
    - enrichment scope: evidence_mitigation.derive_scope_enriched + matches_scope_multi
      (Table II, symbolic_detector.symbolic; Fig. 2, realistic_probe.evaluate);
    - modal (frequency) scope: evidence_mitigation.derive_scope(coverage=0.5) +
      matches_scope (realistic_probe.evaluate);
    - unseen filter: rule_detection_production.baseline_scopes()["unseen"], i.e. every
      fingerprint absent from the profile seen in at least k_min = 5 origins of the
      cluster, on the SAME profile (baseline_a{alpha}.parquet) and the SAME cluster;
    - union: enrichment JA4 set | unseen set, as rule_detection_production.judge builds it.
  The unseen and union JA4 sets are applied with the same non-JA4 conjuncts as the
  enrichment scope of that cluster (endpoint, and a /24 if one held half the origins),
  through matches_scope_multi. An empty set names no filter (blocks nothing), as in
  rule_detection_production.judge. Enrichment keeps the committed synthetic semantics
  (an empty JA4 set leaves an endpoint-only scope); the CSV records whether that case
  ever occurs.
* Data: the cached scenarios of the Makefile's REALWORK (synth/sprint6_realistic) and
  the attack-free calibration runs of RULEWORK (synth/sprint6_rule), read-only: a
  missing file is an error, never generated.
* Shared stacks (``--shared-points``): each cached scenario is relabelled, keeping every
  session and replacing only the M stack names t13d1516h2_synth_{seed:04x}_{k:02d} by
  M distinct fingerprints drawn without replacement with np.random.default_rng(seed):
    - ``profile_tail``: rule_detection_production.stacks_for("tail", M, profile, rng),
      the profile's entries outside its ten most common (the production mirror);
    - ``vocab_tail``: benign_ja4_10 .. benign_ja4_{pool-1}, the generator vocabulary
      outside its ten most common entries (a literal reading, sensitivity only).
  One-off attacker fingerprints (t13d1516h2_unique_*) are kept, as production keeps
  bot_unique_*. Relabelling is exact: the generator picks each attacker's stack with
  one draw over the list of names, so the names enter nothing else, and a generator
  that draws the names from a separate stream gives the same session tables.

Usage:
    python unseen_synth.py --out-dir ../results   (make unseen-synth)
"""
import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "sprint-6-noms" / "scripts"), str(EXP / "sprint-1" / "scripts"),
                str(EXP / "pillar4-evidence-mitigation" / "scripts"), str(EXP / "common")]
import level_calibration as LC  # noqa: E402
from compute_coordination import _is_attack, assign_detection_clusters, compute_omega  # noqa: E402
from evidence_mitigation import (_origin_units, derive_scope, derive_scope_enriched,  # noqa: E402
                                 matches_scope, matches_scope_multi)
from level_calibration import fired_cluster, level_for  # noqa: E402
import rule_detection_production as RDP  # noqa: E402  (baseline_scopes, stacks_for)


def _read_only_clean(py, dist_dir, work, alpha, seed):
    """level_calibration.ensure_clean, minus the generation: the cache is read-only."""
    pq = Path(work) / f"clean_a{alpha}_seed{seed}.parquet"
    if not pq.exists():
        raise SystemExit(f"missing cached attack-free run {pq}; refusing to generate into the drive")
    return pq


LC.ensure_clean = _read_only_clean

GRID = ["0.0:1:0", "1.5:1:0", "1.5:5:0", "1.5:25:0", "1.5:100:0", "2.0:25:0",
        "1.5:5:1", "1.5:25:1", "2.0:25:1"]                      # the Makefile's grid
IN_PAPER = {"1.5:1:0": "Table II + Fig. 2", "1.5:5:0": "Table II + Fig. 2",
            "1.5:25:0": "Table II + Fig. 2", "1.5:100:0": "Table II + Fig. 2",
            "1.5:25:1": "Table II + Fig. 2", "2.0:25:0": "Sec. V-C text (modal 61.1%)"}
METHODS = ["enrichment", "unseen", "union", "modal", "zscore"]


def profile_for(work, alpha):
    """symbolic_detector.profile_for / realistic_probe.ensure_baseline, read-only."""
    bg = pd.read_parquet(work / f"baseline_a{alpha}.parquet")
    p = bg["ja4"].value_counts(normalize=True)
    p.attrs["n"] = len(bg)
    return p


def metrics(flagged, y):
    """symbolic_detector.symbolic's metrics; FPR is the collateral of Fig. 2."""
    tp = int((flagged & (y == 1)).sum()); fp = int((flagged & (y == 0)).sum())
    fn = int((~flagged & (y == 1)).sum()); tn = int((~flagged & (y == 0)).sum())
    rec = tp / max(tp + fn, 1)
    prec = tp / max(tp + fp, 1)
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "recall": rec,
            "fpr": fp / max(int((y == 0).sum()), 1), "precision": prec,
            "f1": 2 * prec * rec / max(prec + rec, 1e-12)}


def evaluate(raw, profile, level, k_min=5, unit="origin", label_free=True):
    """Every scope of the fired cluster of one scenario, as flagged sessions."""
    d = raw.copy()
    d["start_ts"] = pd.to_datetime(d["start_ts"]); d["end_ts"] = pd.to_datetime(d["end_ts"])
    d = assign_detection_clusters(d, 300)
    cl = compute_omega(d, unit=unit)
    cid = fired_cluster(cl, label_free)
    if cid is None:
        return None
    cluster = d[d["det_cluster"] == cid]
    y = _is_attack(raw["label_first"]).astype(int).values

    scope_e = derive_scope_enriched(cluster, profile, min_support=0.0 if level else 0.002,
                                    max_values=256, significance=level, unit=unit)
    scope_m = derive_scope(cluster, coverage=0.5)
    units = _origin_units(cluster) if unit == "origin" else cluster
    counts = units["ja4"].value_counts()                  # origins per fingerprint
    base = RDP.baseline_scopes(counts, profile, SimpleNamespace(k_min=k_min))
    E = set(scope_e.get("tlsJa4", set()) or set())
    U = set(base["unseen"])
    Z = set(base["zscore"])
    conj = {k: v for k, v in scope_e.items() if k in ("endpoint", "srcNet24")}

    def by_set(S):
        if not S:
            return np.zeros(len(raw), dtype=bool)        # no filter named: nothing blocked
        return matches_scope_multi(raw, {**conj, "tlsJa4": S}).values

    flagged = {"enrichment": matches_scope_multi(raw, scope_e).values,
               "unseen": by_set(U),
               "union": by_set(E | U) if (E | U) else matches_scope_multi(raw, scope_e).values,
               "modal": matches_scope(raw, scope_m).values,
               "zscore": by_set(Z)}
    named = {"enrichment": E, "unseen": U, "union": E | U,
             "modal": {scope_m["tlsJa4"]} if "tlsJa4" in scope_m else set(), "zscore": Z}
    atk_fp = set(raw.loc[y == 1, "ja4"].dropna()); ben_fp = set(raw.loc[y == 0, "ja4"].dropna())
    crow = cl[cl["det_cluster"] == cid].iloc[0]
    info = {"cluster_sessions": int(crow["size"]), "cluster_origins": int(crow["origins"]),
            "cluster_attack_frac": float(crow["attack_frac"]), "omega": float(crow["omega"]),
            "n_clusters": int(len(cl)), "level": level,
            "enr_endpoint": conj.get("endpoint"), "enr_net24": conj.get("srcNet24"),
            "enr_empty_ja4": not E, "modal_scope": json.dumps(scope_m, sort_keys=True),
            "unseen_equals_enrichment": U == E}
    out = {}
    for m in METHODS:
        r = metrics(flagged[m], y)
        S = named[m]
        r.update({"n_named": len(S), "n_named_attack_only": len(S & (atk_fp - ben_fp)),
                  "n_named_benign_only": len(S & (ben_fp - atk_fp)),
                  "n_named_both": len(S & atk_fp & ben_fp)})
        out[m] = r
    return out, info, E, U


def stack_names(seed, M):
    """The generator's stack names (generator.py, main: shared_ja4)."""
    if M == 1:
        return [f"t13d1516h2_synth_{seed:04x}"]
    return [f"t13d1516h2_synth_{seed:04x}_{k:02d}" for k in range(M)]


def draw_shared(variant, profile, M, seed, vocab_pool=2000):
    """The M replacement names of one seed (candidate list, in order, and the draw)."""
    rng = np.random.default_rng(seed)
    if variant == "profile_tail":
        cand = list(profile.index[10:])
        drawn = RDP.stacks_for("tail", M, profile, rng)         # rng.choice(tail, M, replace=False)
    elif variant == "vocab_tail":
        cand = [f"benign_ja4_{i}" for i in range(10, vocab_pool)]
        drawn = list(rng.choice(np.array(cand, dtype=object), M, replace=False))
    else:
        raise ValueError(variant)
    return cand, [str(x) for x in drawn]


def relabel(raw, seed, drawn):
    """Replace the botnet's stack names; every session and every other field is kept."""
    M = len(drawn)
    mapping = dict(zip(stack_names(seed, M), drawn))
    atk = raw["label_first"] == "ATTACK"
    is_stack = raw["ja4"].isin(list(mapping))
    assert not (is_stack & ~atk).any(), "a benign session carries a synthetic stack name"
    rest = raw.loc[atk & ~is_stack, "ja4"]
    assert rest.str.startswith("t13d1516h2_unique_").all(), "unexpected attacker fingerprint"
    out = raw.copy()
    out.loc[is_stack, "ja4"] = raw.loc[is_stack, "ja4"].map(mapping)
    return out, int(is_stack.sum())


def boot_ci(v, n=10000, seed=0):
    v = np.asarray(v, dtype=float)
    if len(v) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = rng.choice(v, (n, len(v)), replace=True).mean(axis=1)
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", type=Path, default=EXP / "data" / "synth" / "sprint6_realistic")
    ap.add_argument("--clean-work", type=Path, default=EXP / "data" / "synth" / "sprint6_rule")
    ap.add_argument("--dist-dir", type=Path, default=EXP / "sprint-2" / "distributions")
    ap.add_argument("--grid", nargs="+", default=GRID)
    ap.add_argument("--shared-points", nargs="*", default=["1.5:25:0"])
    ap.add_argument("--shared-variants", nargs="+", default=["profile_tail", "vocab_tail"])
    ap.add_argument("--K", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--k-min", type=int, default=5)
    ap.add_argument("--significance", type=float, default=0.01)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    # level_for's options, as the Makefile passes them (METHOD=origin, SIG=0.01).
    largs = SimpleNamespace(calibrate_level=True, significance=args.significance,
                            clean_work=args.clean_work, dist_dir=args.dist_dir, unit="origin")
    t_all = time.perf_counter()
    rows, stacks_rows, levels, timing = [], [], {}, {}
    profiles = {}
    for point in args.grid:
        t0 = time.perf_counter()
        alpha, M, adv = point.split(":")
        alpha, M, adv = float(alpha), int(M), int(adv)
        prof = profiles.setdefault(alpha, profile_for(args.work, alpha))
        level = levels[point] = level_for(prof, alpha, largs)
        modes = [("original", None)]
        if point in args.shared_points:
            modes += [("shared_" + v, v) for v in args.shared_variants]
        for seed in range(1, args.seeds + 1):
            f = args.work / f"a{alpha}_m{M}_adv{adv}_K{args.K}_seed{seed}.parquet"
            if not f.exists():
                raise SystemExit(f"missing cached scenario {f}")
            raw0 = pd.read_parquet(f)
            for mode, variant in modes:
                raw, drawn, n_relab = raw0, None, 0
                if variant:
                    cand, drawn = draw_shared(variant, prof, M, seed)
                    raw, n_relab = relabel(raw0, seed, drawn)
                res = evaluate(raw, prof, level, k_min=args.k_min)
                if res is None:
                    continue
                out, info, E, U = res
                for m, r in out.items():
                    rows.append({"mode": mode, "alpha": alpha, "stacks": M, "adv": adv,
                                 "K": args.K, "seed": seed, "method": m, **r, **info,
                                 "relabelled_sessions": n_relab})
                if variant:
                    atk = raw[raw["label_first"] == "ATTACK"]["ja4"].value_counts()
                    ben = raw0[raw0["label_first"] == "BENIGN"]["ja4"].value_counts()
                    for k, name in enumerate(drawn):
                        stacks_rows.append({
                            "mode": mode, "seed": seed, "stack": k, "name": name,
                            "profile_count": int(round(prof.get(name, 0.0) * prof.attrs["n"])),
                            "in_profile": name in prof.index,
                            "attackers": int(atk.get(name, 0)), "benign_sessions": int(ben.get(name, 0)),
                            "named_enrichment": name in E, "named_unseen": name in U})
        timing[point] = time.perf_counter() - t0
        print(f"done {point}: level={level}  {timing[point]:.1f}s", flush=True)
    timing["total_s"] = time.perf_counter() - t_all

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "unseen_synth_runs.csv", index=False)
    if stacks_rows:
        pd.DataFrame(stacks_rows).to_csv(args.out_dir / "shared_stacks_draws.csv", index=False)

    # ---- aggregate: mean over seeds, bootstrap CI of recall and F1 ----
    agg = []
    for (mode, alpha, M, adv, m), g in df.groupby(["mode", "alpha", "stacks", "adv", "method"], sort=False):
        point = f"{alpha}:{M}:{adv}"
        e = {"mode": mode, "alpha": alpha, "stacks": M, "adv": adv, "method": m, "n": len(g),
             "in_paper": IN_PAPER.get(point, "") if mode == "original" else "shared stacks (new)"}
        for c in ["recall", "fpr", "precision", "f1", "n_named", "n_named_attack_only",
                  "n_named_benign_only", "n_named_both"]:
            e[c] = float(g[c].mean())
        e["recall_min"], e["recall_max"] = float(g["recall"].min()), float(g["recall"].max())
        e["fpr_max"] = float(g["fpr"].max())
        e["f1_ci_lo"], e["f1_ci_hi"] = boot_ci(g["f1"].values)
        e["recall_ci_lo"], e["recall_ci_hi"] = boot_ci(g["recall"].values)
        e["seeds_unseen_equals_enrichment"] = int(g["unseen_equals_enrichment"].sum())
        e["seeds_enr_empty_ja4"] = int(g["enr_empty_ja4"].sum())
        agg.append(e)
    agg = pd.DataFrame(agg)
    agg.to_csv(args.out_dir / "unseen_synth_summary.csv", index=False)

    # ---- paired per-seed differences against enrichment ----
    piv = df.pivot_table(index=["mode", "alpha", "stacks", "adv", "seed"], columns="method",
                         values=["recall", "fpr", "f1"])
    pair = []
    for key, g in piv.groupby(level=[0, 1, 2, 3], sort=False):
        for m in ["unseen", "union", "modal"]:
            dr = g[("recall", m)] - g[("recall", "enrichment")]
            dfp = g[("fpr", m)] - g[("fpr", "enrichment")]
            dF = g[("f1", m)] - g[("f1", "enrichment")]
            pair.append({"mode": key[0], "alpha": key[1], "stacks": key[2], "adv": key[3],
                         "method": m, "d_recall_mean": float(dr.mean()), "d_recall_min": float(dr.min()),
                         "d_recall_max": float(dr.max()), "d_fpr_mean": float(dfp.mean()),
                         "d_f1_mean": float(dF.mean()), "d_f1_min": float(dF.min()),
                         "d_f1_max": float(dF.max()),
                         "seeds_f1_equal": int((dF.abs() < 1e-12).sum()),
                         "seeds_f1_better": int((dF > 1e-12).sum()),
                         "seeds_f1_worse": int((dF < -1e-12).sum())})
    pd.DataFrame(pair).to_csv(args.out_dir / "unseen_synth_paired.csv", index=False)

    (args.out_dir / "unseen_synth.json").write_text(json.dumps(
        {"grid": args.grid, "shared_points": args.shared_points,
         "shared_variants": args.shared_variants, "K": args.K, "seeds": args.seeds,
         "k_min": args.k_min, "significance": args.significance, "unit": "origin",
         "calibrate_level": True, "label_free_cluster": True, "level": levels,
         "work": str(args.work), "clean_work": str(args.clean_work),
         "timing_s": timing}, indent=2))

    pd.set_option("display.width", 200)
    cols = ["mode", "alpha", "stacks", "adv", "method", "recall", "fpr", "f1", "n_named"]
    print(agg[cols].to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print(f"\nOK: {args.out_dir}  (total {timing['total_s']:.1f}s)")


if __name__ == "__main__":
    main()
