#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the rule Omega(S) >= tau evaluated as a window-level detector.

The paper's central formal object had never been measured on its own. The
canonical scenario forms detection clusters by chaining sessions whose gaps stay
under W, which on a single endpoint yields one cluster holding nearly every
session, and tau was taken in-sample, as the 99th percentile of Omega over the
benign-dominant clusters of the same scenario. This script evaluates the rule the
way it would run:

- windows are fixed W = 300 s slots per endpoint, as the paper declares;
- tau is calibrated on attack-free scenarios with their own seeds, so no label
  and no test window enters the threshold;
- false alarms are measured on a second, held-out set of attack-free scenarios;
- detection is measured on the canonical scenarios (alpha = 1.5, 25 stacks), over
  windows holding at least k_min attacker sessions;
- a flash crowd is a held-out attack-free scenario with N extra legitimate
  sessions, drawn from another attack-free scenario, retimed into one window.

Three rules are compared:

  omega      |S| >= k_min, rate >= tau_rate and Omega(S) >= tau (Section III-F)
  pipeline   omega, then the enrichment scope of Section III-H must name a
             fingerprint; otherwise the verdict is evidence only, no filter
  enrichment |S| >= k_min and a non-empty enrichment scope, without Omega

Usage:
    python rule_detection.py --work $DATA_ROOT/synth/sprint6_realistic \\
        --clean-work $DATA_ROOT/synth/sprint6_rule \\
        --dist-dir $DATA_ROOT/synth/distributions --out-dir ../results
"""
import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
S2 = EXP / "sprint-2" / "scripts"
sys.path[:0] = [str(EXP / "sprint-1" / "scripts"),
                str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from compute_coordination import _is_attack  # noqa: E402
from evidence_mitigation import derive_scope_enriched, matches_scope_multi  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)
STEALTH_CFG = S2.parent / "configs" / "scenario_stealth.yaml"
W_TLS, W_EP, W_NET = 1.0, 0.6, 0.3          # coordinationWeight, as in the ontology


def pairs(counts):
    counts = np.asarray(counts, dtype=float)
    return float((counts * (counts - 1) / 2).sum())


def ensure_clean(py, dist_dir, work, alpha, seed):
    """Attack-free scenario with the canonical benign mix (cached)."""
    pq = work / f"clean_a{alpha}_seed{seed}.parquet"
    if pq.exists():
        return pq
    jl = work / f"clean_a{alpha}_seed{seed}.jsonl"
    subprocess.run([py, str(S2 / "generator.py"), "--config", str(STEALTH_CFG),
                    "--param", "K=0", "--param", f"benign_ja4_zipf_alpha={alpha}",
                    "--seed", str(seed), "--distributions", str(dist_dir),
                    "--out", str(jl)], check=True, capture_output=True)
    subprocess.run([py, str(S2 / "synth_to_sessions.py"), "--jsonl", str(jl),
                    "--out", str(pq)], check=True, capture_output=True)
    jl.unlink(missing_ok=True)
    return pq


def windows(df, w_s):
    """Assign fixed W-second slots per endpoint."""
    df = df.copy()
    df["endpoint"] = df["dst_ip_first"].astype(str) + ":" + df["dst_port_first"].astype(str)
    df["net24"] = df["src_ip_first"].astype(str).str.rsplit(".", n=1).str[0]
    t0 = df["start_ts"].min()
    df["win"] = ((df["start_ts"] - t0).dt.total_seconds() // w_s).astype(int)
    return df


def window_stats(g):
    """Omega(S) and the aggregate rate of one window, from class sizes."""
    span = max(1.0, (g["end_ts"].max() - g["start_ts"].min()).total_seconds())
    return {
        "size": len(g),
        "omega": (W_TLS * pairs(g["ja4"].dropna().value_counts().values)
                  + W_EP * pairs([len(g)])
                  + W_NET * pairs(g["net24"].value_counts().values)),
        "rate": float(g["n_requests"].sum()) / span,
    }


def scope_of(g, profile, min_count=0):
    """Enrichment scope and the fraction of the window it would block.

    ``min_count`` adds an absolute floor to the relative one: a fingerprint must
    cover sigma of the window AND at least ``min_count`` sessions. Coordination
    needs several sessions sharing a value, and a fingerprint seen once is never
    evidence of it, however rare it is in the background.
    """
    sigma = max(0.002, min_count / len(g)) if min_count else 0.002
    scope = derive_scope_enriched(g, profile, min_support=sigma, max_values=256)
    if not scope.get("tlsJa4"):
        return False, 0.0, 0.0
    hit = matches_scope_multi(g, scope).values
    att = _is_attack(g["label_first"]).values
    legit = (~att).sum()
    return True, float(hit[att].mean()) if att.any() else 0.0, \
        float(hit[~att].sum() / legit) if legit else 0.0


def steady(df, minutes, rng):
    """Spread the benign sessions uniformly over ``minutes``, keeping durations.

    The generator places ~88% of benign sessions in the first five minutes, so a
    five-minute window never sees steady traffic. Attack sessions keep their
    times, which are already concentrated at the start of the episode.
    """
    if not minutes:
        return df
    df = df.copy()
    ben = ~_is_attack(df["label_first"])
    t0 = df["start_ts"].min()
    dur = df.loc[ben, "end_ts"] - df.loc[ben, "start_ts"]
    df.loc[ben, "start_ts"] = t0 + pd.to_timedelta(rng.uniform(0, minutes * 60, ben.sum()), unit="s")
    df.loc[ben, "end_ts"] = df.loc[ben, "start_ts"] + dur.values
    return df


def evaluate(df, kind, scen, w_s, profile, k_min, min_count=0):
    rows = []
    for (ep, win), g in windows(df, w_s).groupby(["endpoint", "win"]):
        st = window_stats(g)
        n_att = int(_is_attack(g["label_first"]).sum())
        named, recall, coll = (scope_of(g, profile, min_count) if st["size"] >= k_min
                               else (False, 0.0, 0.0))
        rows.append({"kind": kind, "scenario": scen, "endpoint": ep, "win": win,
                     "n_attack": n_att, **st, "scope_named": named,
                     "scope_recall": recall, "scope_collateral": coll})
    return rows


def flash_crowd(base, donor, n, w_s, rng):
    """Retime n legitimate sessions from ``donor`` into one window of ``base``."""
    b = base.copy()
    t0 = b["start_ts"].min()
    win = int(rng.integers(0, max(1, int((b["start_ts"].max() - t0).total_seconds() // w_s))))
    lo = t0 + pd.Timedelta(seconds=win * w_s)
    extra = donor.sample(n=min(n, len(donor)), random_state=int(rng.integers(1 << 31))).copy()
    dur = extra["end_ts"] - extra["start_ts"]
    extra["start_ts"] = lo + pd.to_timedelta(rng.uniform(0, w_s, len(extra)), unit="s")
    extra["end_ts"] = extra["start_ts"] + dur
    extra["dst_ip_first"] = b["dst_ip_first"].iloc[0]   # same attacked service
    extra["dst_port_first"] = b["dst_port_first"].iloc[0]
    return pd.concat([b, extra], ignore_index=True), win


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path, help="canonical attack scenarios")
    ap.add_argument("--clean-work", required=True, type=Path, help="cache of attack-free runs")
    ap.add_argument("--dist-dir", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--alpha", type=float, default=1.5)
    ap.add_argument("--stacks", type=int, default=25)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--K", type=int, nargs="+", default=[50, 1000])
    ap.add_argument("--window-s", type=int, default=300)
    ap.add_argument("--k-min", type=int, default=5)
    ap.add_argument("--tau-rate", type=float, default=1.0)
    ap.add_argument("--percentiles", type=float, nargs="+", default=[95, 99, 99.9])
    ap.add_argument("--flash", type=int, nargs="+", default=[25, 50, 100])
    ap.add_argument("--min-count", type=int, default=0,
                    help="absolute support floor for the enrichment scope (0 = sigma only)")
    ap.add_argument("--steady-minutes", type=float, default=0,
                    help="spread benign sessions uniformly over this span (0 = as generated)")
    ap.add_argument("--profile", choices=["baseline", "calib"], default="baseline",
                    help="background profile: the single attack-free baseline run "
                         "(1,000 sessions) or all calibration runs pooled")
    ap.add_argument("--tag", default="", help="suffix for the output files")
    args = ap.parse_args()
    args.clean_work.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    py, rng = sys.executable, np.random.default_rng(20260924)

    calib_seeds = range(5001, 5001 + args.seeds)
    if args.profile == "calib":        # attack-free, disjoint from the test seeds
        bg = pd.concat([pd.read_parquet(ensure_clean(py, args.dist_dir, args.clean_work,
                                                     args.alpha, s)) for s in calib_seeds])
    else:
        bg = pd.read_parquet(args.work / f"baseline_a{args.alpha}.parquet")
    profile = bg["ja4"].value_counts(normalize=True)
    profile.attrs["n"] = len(bg)
    log.info("background profile: %s, %d sessions, %d fingerprints",
             args.profile, len(bg), profile.size)

    test_seeds = range(6001, 6001 + args.seeds)
    donor_seeds = range(7001, 7001 + args.seeds)
    rows = []
    for s in calib_seeds:
        rows += evaluate(steady(pd.read_parquet(ensure_clean(py, args.dist_dir, args.clean_work, args.alpha, s)),
                                args.steady_minutes, rng),
                         "calib", s, args.window_s, profile, args.k_min, args.min_count)
    for s in test_seeds:
        rows += evaluate(steady(pd.read_parquet(ensure_clean(py, args.dist_dir, args.clean_work, args.alpha, s)),
                                args.steady_minutes, rng),
                         "clean", s, args.window_s, profile, args.k_min, args.min_count)
    log.info("attack-free windows evaluated")
    for K in args.K:
        for s in range(1, args.seeds + 1):
            pq = args.work / f"a{args.alpha}_m{args.stacks}_adv0_K{K}_seed{s}.parquet"
            rows += evaluate(steady(pd.read_parquet(pq), args.steady_minutes, rng),
                             f"attack_K{K}", s, args.window_s, profile, args.k_min, args.min_count)
        log.info("attack K=%d evaluated", K)
    for n in args.flash:
        for s, dn in zip(test_seeds, donor_seeds):
            base = steady(pd.read_parquet(ensure_clean(py, args.dist_dir, args.clean_work, args.alpha, s)),
                          args.steady_minutes, rng)
            donor = pd.read_parquet(ensure_clean(py, args.dist_dir, args.clean_work, args.alpha, dn))
            fc, win = flash_crowd(base, donor, n, args.window_s, rng)
            for r in evaluate(fc, f"flash_{n}", s, args.window_s, profile, args.k_min,
                              args.min_count):
                if r["win"] == win:            # only the surge window
                    rows.append(r)
        log.info("flash crowd N=%d evaluated", n)

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / f"rule_detection_windows{args.tag}.csv", index=False)

    eligible = lambda d: d[(d["size"] >= args.k_min) & (d["rate"] >= args.tau_rate)]
    calib = eligible(df[df["kind"] == "calib"])
    out = {"config": {k: (str(v) if isinstance(v, Path) else v) for k, v in vars(args).items()},
           "calibration_windows": int(len(calib)), "by_percentile": {}}
    for p in args.percentiles:
        tau = float(np.percentile(calib["omega"], p)) if len(calib) else float("inf")
        res = {"tau": tau}
        for kind in sorted(df["kind"].unique()):
            if kind == "calib":
                continue
            d = df[df["kind"] == kind]
            if kind.startswith("attack"):
                d = d[d["n_attack"] >= args.k_min]
            base = d[(d["size"] >= args.k_min) & (d["rate"] >= args.tau_rate)]
            n_all = len(d)
            fire_omega = (base["omega"] >= tau)
            fire_pipe = fire_omega & base["scope_named"]
            fire_enr = d[d["size"] >= args.k_min]["scope_named"]
            res[kind] = {
                "windows": int(n_all),
                "omega": float(fire_omega.sum() / n_all) if n_all else None,
                "pipeline": float(fire_pipe.sum() / n_all) if n_all else None,
                "enrichment": float(fire_enr.sum() / n_all) if n_all else None,
                "median_omega": float(d["omega"].median()) if n_all else None,
                "median_size": float(d["size"].median()) if n_all else None,
                "collateral_when_filtered": float(base.loc[fire_pipe, "scope_collateral"].mean())
                if fire_pipe.any() else 0.0,
            }
        out["by_percentile"][str(p)] = res
    (args.out_dir / f"rule_detection{args.tag}.json").write_text(json.dumps(out, indent=2))

    print("\n" + "=" * 92)
    print("RULE AS DETECTOR, per 5-min window. Fraction of windows where each rule fires.")
    print("=" * 92)
    for p, res in out["by_percentile"].items():
        print(f"\ntau = p{p} of attack-free Omega = {res['tau']:.1f}")
        print(f"{'windows':<16}{'n':>6}{'omega':>9}{'pipeline':>10}{'enrich.':>9}"
              f"{'med. |S|':>10}{'med. Omega':>12}")
        for kind, r in res.items():
            if kind == "tau":
                continue
            print(f"{kind:<16}{r['windows']:>6}{r['omega']:>9.3f}{r['pipeline']:>10.3f}"
                  f"{r['enrichment']:>9.3f}{r['median_size']:>10.0f}{r['median_omega']:>12.1f}")
    print(f"\nOK: {args.out_dir}/rule_detection{args.tag}.json")


if __name__ == "__main__":
    main()
