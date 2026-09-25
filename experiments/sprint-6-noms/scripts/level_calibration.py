"""Sprint 6 (NOMS) — the test level of the enrichment scope, calibrated without labels.

Section III-H calibrates the level of the binomial test per endpoint, as
tau_cluster is calibrated: on attack-free traffic, so that the scope names a
filter in at most 1% of it, and never above the nominal 0.01. On production
traffic this is what keeps legitimate fleets from being filtered; on the
generator, whose sessions are independent draws, it leaves the nominal level in
place.

The per-cluster experiments (symbolic_detector, realistic_probe, profile_drift)
take their calibration clusters from the attack-free runs of rule_detection.py
(seeds 5001-5030, generated on first use), clustered as the rule clusters them.
A profile is always calibrated on runs of its own benign mix: the operator builds
the profile and calibrates the level on the same normal period.
"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(HERE.parent), str(EXP / "sprint-1" / "scripts"),
                str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from compute_coordination import assign_detection_clusters  # noqa: E402
from evidence_mitigation import calibrate_level  # noqa: E402
from rule_detection import ensure_clean  # noqa: E402

CALIB_SEEDS = range(5001, 5031)


def add_arguments(ap):
    """The options every per-cluster experiment shares."""
    ap.add_argument("--unit", choices=["session", "origin"], default="session",
                    help="what Omega and the scope count: sessions, or distinct source "
                         "addresses (the paper's method)")
    ap.add_argument("--calibrate-level", action="store_true",
                    help="calibrate the test level on attack-free runs (needs "
                         "--significance, --clean-work and --dist-dir)")
    ap.add_argument("--label-free-cluster", action="store_true",
                    help="evaluate the cluster of largest Omega, chosen with no label (the "
                         "paper's method); default: the largest-Omega cluster whose attack "
                         "share is at least 0.5, as earlier revisions did")
    ap.add_argument("--clean-work", type=Path, default=None,
                    help="cache of attack-free runs (rule_detection.py --clean-work)")
    if not any("--dist-dir" in a.option_strings for a in ap._actions):
        ap.add_argument("--dist-dir", type=Path, default=None,
                        help="generator distributions, to create missing attack-free runs")


def clean_clusters(clean_work, dist_dir, alpha, unit, k_min=5, window_s=300):
    """Clusters of the attack-free calibration runs with at least k_min units."""
    out = []
    for seed in CALIB_SEEDS:
        d = pd.read_parquet(ensure_clean(sys.executable, dist_dir, clean_work, alpha, seed))
        d["start_ts"] = pd.to_datetime(d["start_ts"]); d["end_ts"] = pd.to_datetime(d["end_ts"])
        for _, c in assign_detection_clusters(d, window_s).groupby("det_cluster"):
            n = c["src_ip_first"].nunique() if unit == "origin" else len(c)
            if n >= k_min:
                out.append(c)
    return out


def fired_cluster(cl, label_free):
    """The cluster the scope is derived from: the largest Omega, with or without labels."""
    pool = cl if label_free else cl[cl["attack_frac"] >= 0.5]
    if not len(pool):
        return None
    return pool.sort_values("omega", ascending=False).iloc[0]["det_cluster"]


def level_for(profile, alpha, args, cache={}):
    """The scope's level for ``profile``, whose benign mix has Zipf exponent ``alpha``."""
    if not args.calibrate_level:
        return args.significance
    if args.significance is None or args.clean_work is None or args.dist_dir is None:
        raise SystemExit("--calibrate-level needs --significance, --clean-work and --dist-dir")
    key = (id(profile), alpha, args.unit)
    if key not in cache:
        clusters = clean_clusters(args.clean_work, args.dist_dir, alpha, args.unit)
        cache[key] = calibrate_level(clusters, profile, cap=args.significance, unit=args.unit)
    return cache[key]
