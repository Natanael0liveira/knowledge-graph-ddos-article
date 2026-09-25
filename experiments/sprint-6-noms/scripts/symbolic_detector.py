#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the symbolic rule evaluated AS a detector.

Every detection number in the paper so far came from a Random Forest over
cross-session features. That measures the value of the *representation* and says
nothing about the symbolic layer, which is a fair objection to a paper about
knowledge graphs. This script closes that gap: it evaluates the SPARQL/enrichment
path end to end as a detector, where the set of sessions matching the derived
scope IS the set of flagged sessions --- no classifier, no training, no threshold.

It also fixes the comparison. ROC AUC is a ranking metric; the rule emits a hard
decision. Comparing 0.98 AUC against an F1 is meaningless, so we force the
learned model onto the rule's own operating point and ask: at the false-positive
rate the rule achieves, how much of the attack does the classifier recover?
A second learned model (``rfp_``) also reads the profile of normal traffic the
rule reads, as two per-session features (profile_features).

Usage:
    python symbolic_detector.py --work $DATA_ROOT/synth/sprint6_realistic \\
        --grid 0.0:1:0 1.5:1:0 1.5:5:0 1.5:25:0 1.5:100:0 2.0:25:0 \\
               1.5:5:1 1.5:25:1 2.0:25:1 \\
        --K 1000 --seeds 15 --out-dir ../results
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "sprint-1" / "scripts"), str(EXP / "sprint-3" / "scripts"),
                str(EXP / "sprint-4" / "scripts"),
                str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from run_ablation import build_features  # noqa: E402
from run_sprint4 import STRONG_SETS, boot_ci  # noqa: E402
from compute_coordination import (_is_attack, assign_detection_clusters,  # noqa: E402
                                  compute_omega)
from evidence_mitigation import derive_scope_enriched, matches_scope_multi  # noqa: E402
from level_calibration import add_arguments, fired_cluster, level_for  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
N_JOBS = 2


def profile_for(work, alpha):
    bg = pd.read_parquet(work / f"baseline_a{alpha}.parquet")
    p = bg["ja4"].value_counts(normalize=True)
    p.attrs["n"] = len(bg)
    return p


def symbolic(raw, profile, significance=None, unit="session", label_free=False):
    """Rule as detector: flagged = sessions matching the derived scope."""
    d = raw.copy()
    d["start_ts"] = pd.to_datetime(d["start_ts"]); d["end_ts"] = pd.to_datetime(d["end_ts"])
    d = assign_detection_clusters(d, 300)
    cl = compute_omega(d, unit=unit)
    cid = fired_cluster(cl, label_free)
    if cid is None:
        return None
    scope = derive_scope_enriched(d[d["det_cluster"] == cid], profile,
                                  min_support=0.0 if significance else 0.002,
                                  max_values=256, significance=significance, unit=unit)
    y = _is_attack(raw["label_first"]).astype(int).values
    flagged = matches_scope_multi(raw, scope).values
    tp = int((flagged & (y == 1)).sum()); fp = int((flagged & (y == 0)).sum())
    fn = int((~flagged & (y == 1)).sum())
    rec = tp / max(tp + fn, 1)
    prec = tp / max(tp + fp, 1)
    return {"recall": rec, "fpr": fp / max((y == 0).sum(), 1), "precision": prec,
            "f1": 2 * prec * rec / max(prec + rec, 1e-12),
            "n_ja4": len(scope.get("tlsJa4", []) or [])}


PROFILE_FEATS = ["prof_logb", "prof_enrich"]


def profile_features(df, profile):
    """What the rule reads from the profile, as per-session features.

    ``prof_logb`` is the log prevalence of the session's JA4 in normal traffic,
    with the rule's 1/N prior for unseen fingerprints; ``prof_enrich`` the log
    ratio of its share in the session's detection cluster to that prevalence, the
    enrichment the rule tests. Sessions without TLS get 0 in both.
    """
    eps = 1.0 / max(profile.attrs["n"], 1)
    b = df["ja4"].map(profile).astype(float).fillna(0.0) + eps
    has = df["ja4"].notna()
    share = (df.groupby(["det_cluster", "ja4"])["ja4"].transform("size")
             / df[has].groupby("det_cluster")["ja4"].transform("size").reindex(df.index))
    df["prof_logb"] = np.where(has, np.log10(b), 0.0)
    df["prof_enrich"] = np.where(has, np.log10(share / b), 0.0)
    return df


def learned(raw, seed=42, profile=None):
    """RF on config (d): AUC, plus recall forced to FPR=0 and FPR=1%.

    With ``profile``, the model also gets the profile features, so it reads the
    same normal traffic the rule reads.
    """
    df = build_features(raw)
    y = _is_attack(df["label_first"]).astype(int).values
    feats = list(STRONG_SETS["d_completo"])
    if profile is not None:
        df = profile_features(df, profile)
        feats += PROFILE_FEATS
    X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
    itr, ite = train_test_split(np.arange(len(y)), test_size=0.3,
                                random_state=seed, stratify=y)
    clf = RandomForestClassifier(n_estimators=200, random_state=seed,
                                 class_weight="balanced", n_jobs=N_JOBS).fit(X[itr], y[itr])
    p = clf.predict_proba(X[ite])[:, 1]
    yt = y[ite]
    neg = p[yt == 0]
    return {"auc": roc_auc_score(yt, p),
            "recall_fpr0": float((p[yt == 1] >= neg.max() + 1e-12).mean()),
            "recall_fpr1": float((p[yt == 1] >= np.quantile(neg, 0.99)).mean())}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--grid", nargs="+", required=True)
    ap.add_argument("--K", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--significance", type=float, default=None,
                    help="binomial over-representation test for the scope at this "
                         "family-wise level; default: the fixed floor sigma = 0.002")
    add_arguments(ap)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows, levels = [], {}
    for point in args.grid:
        alpha, stacks, adv = point.split(":")
        alpha, stacks, adv = float(alpha), int(stacks), int(adv)
        prof = profile_for(args.work, alpha)
        level = levels[point] = level_for(prof, alpha, args)
        for seed in range(1, args.seeds + 1):
            f = args.work / f"a{alpha}_m{stacks}_adv{adv}_K{args.K}_seed{seed}.parquet"
            if not f.exists():
                continue
            raw = pd.read_parquet(f)
            sym = symbolic(raw, prof, level, args.unit, args.label_free_cluster)
            if not sym:
                continue
            r = {"alpha": alpha, "stacks": stacks, "adv": adv, "seed": seed}
            r.update({f"sym_{k}": v for k, v in sym.items()})
            r.update({f"rf_{k}": v for k, v in learned(raw).items()})
            r.update({f"rfp_{k}": v for k, v in learned(raw, profile=prof).items()})
            rows.append(r)
        log.info("done %s", point)

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "symbolic_detector_runs.csv", index=False)

    agg = {}
    print("\n" + "=" * 96)
    print(f"SYMBOLIC RULE AS DETECTOR vs LEARNED MODEL AT THE SAME OPERATING POINT "
          f"(K={args.K}, n={args.seeds})")
    print("=" * 96)
    print(f"{'alpha':>5}{'M':>5}{'adv':>4} | {'rule: rec':>10}{'FPR':>8}{'prec':>7}{'F1':>7}"
          f" | {'RF AUC':>7}{'RF rec@FPR0':>12}{'RF rec@FPR1%':>13}"
          f" | {'+prof AUC':>9}{'rec@FPR0':>9}")
    print("-" * 96)
    for point in args.grid:
        alpha, stacks, adv = point.split(":")
        sub = df[(df.alpha == float(alpha)) & (df.stacks == int(stacks))
                 & (df.adv == int(adv))]
        if not len(sub):
            continue
        e = {c: float(sub[c].mean()) for c in
             ["sym_recall", "sym_fpr", "sym_precision", "sym_f1", "sym_n_ja4",
              "rf_auc", "rf_recall_fpr0", "rf_recall_fpr1",
             "rfp_auc", "rfp_recall_fpr0", "rfp_recall_fpr1"]}
        e["n"] = int(len(sub))
        m, lo, hi = boot_ci(sub["sym_f1"].values)
        e["sym_f1_ci95"] = [lo, hi]
        agg[point] = e
        print(f"{alpha:>5}{stacks:>5}{adv:>4} | {e['sym_recall']*100:>9.1f}%"
              f"{e['sym_fpr']*100:>7.2f}%{e['sym_precision']:>7.3f}{e['sym_f1']:>7.3f}"
              f" | {e['rf_auc']:>7.3f}{e['rf_recall_fpr0']*100:>11.1f}%"
              f"{e['rf_recall_fpr1']*100:>12.1f}%"
              f" | {e['rfp_auc']:>9.3f}{e['rfp_recall_fpr0']*100:>8.1f}%")

    (args.out_dir / "symbolic_detector.json").write_text(json.dumps(
        {"K": args.K, "seeds": args.seeds, "grid": args.grid,
         "significance": args.significance, "unit": args.unit,
         "calibrate_level": args.calibrate_level, "label_free_cluster": args.label_free_cluster,
         "level": levels, "aggregate": agg}, indent=2))
    print(f"\nOK: {args.out_dir}/symbolic_detector.json")


if __name__ == "__main__":
    main()
