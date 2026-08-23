#!/usr/bin/env python3
"""Sprint 6 (NOMS) — sensitivity of the derived scope to the background profile.

The enrichment test of Section III-G compares fingerprint prevalence inside the
fired cluster against a background profile the operator maintains outside attack
episodes. That profile is a deployment dependency, so its quality has to be
measured, not assumed. This script holds the attack episode fixed (the canonical
alpha=1.5, M=25 scenario) and varies ONLY the profile:

    matched   profile alpha=1.5  -- the operator profiled the right population
    drifted   profile alpha=2.0  -- profile more concentrated than reality
    flat      profile alpha=0.0  -- uniform pool, i.e. a useless/absent profile

Reports attack coverage and collateral for each. Coverage is expected to be
insensitive (profile quality governs precision, not recall); collateral is not.

Usage:
    python profile_drift.py --work $DATA_ROOT/synth/sprint6_realistic \
        --alpha 1.5 --stacks 25 --K 1000 --seeds 15 --out-dir ../results
"""
import argparse, json, logging, sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve(); EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "sprint-1" / "scripts"),
                str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from compute_coordination import (_is_attack, assign_detection_clusters,  # noqa: E402
                                  compute_omega)
from evidence_mitigation import derive_scope_enriched, matches_scope_multi  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def profile_for(work, alpha):
    bg = pd.read_parquet(work / f"baseline_a{alpha}.parquet")
    return bg["ja4"].value_counts(normalize=True)


def evaluate(raw, profile):
    d = raw.copy()
    d["start_ts"] = pd.to_datetime(d["start_ts"]); d["end_ts"] = pd.to_datetime(d["end_ts"])
    d = assign_detection_clusters(d, 300)
    cl = compute_omega(d)
    atk = cl[cl["attack_frac"] >= 0.5]
    if not len(atk):
        return None
    cid = atk.sort_values("omega", ascending=False).iloc[0]["det_cluster"]
    scope = derive_scope_enriched(d[d["det_cluster"] == cid], profile,
                                  min_support=0.002, max_values=256)
    y = _is_attack(raw["label_first"]).astype(int).values
    flagged = matches_scope_multi(raw, scope).values
    tp = int((flagged & (y == 1)).sum()); fp = int((flagged & (y == 0)).sum())
    return {"coverage": tp / max(int((y == 1).sum()), 1),
            "collateral": fp / max(int((y == 0).sum()), 1),
            "n_ja4": len(scope.get("tlsJa4", []) or [])}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--alpha", type=float, default=1.5)
    ap.add_argument("--stacks", type=int, default=25)
    ap.add_argument("--K", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--out-dir", required=True, type=Path)
    a = ap.parse_args(); a.out_dir.mkdir(parents=True, exist_ok=True)

    PROFILES = [("matched", a.alpha), ("drifted", 2.0), ("flat", 0.0)]
    profs = {name: profile_for(a.work, al) for name, al in PROFILES}
    rows = []
    for seed in range(1, a.seeds + 1):
        f = a.work / f"a{a.alpha}_m{a.stacks}_adv0_K{a.K}_seed{seed}.parquet"
        if not f.exists():
            continue
        raw = pd.read_parquet(f)
        for name, al in PROFILES:
            r = evaluate(raw, profs[name])
            if r:
                r.update({"profile": name, "profile_alpha": al, "seed": seed})
                rows.append(r)
        log.info("seed %d done", seed)

    df = pd.DataFrame(rows)
    df.to_csv(a.out_dir / "profile_drift_runs.csv", index=False)
    agg = {}
    print("\n" + "=" * 74)
    print(f"BACKGROUND-PROFILE SENSITIVITY — episode alpha={a.alpha}, M={a.stacks}, "
          f"K={a.K}, n={a.seeds}")
    print("=" * 74)
    print(f"{'profile':<10}{'alpha':>7}{'coverage':>12}{'collateral':>13}{'|scope|':>9}{'n':>5}")
    print("-" * 74)
    for name, al in PROFILES:
        s = df[df.profile == name]
        if not len(s):
            continue
        e = {"profile_alpha": al, "n": int(len(s)),
             "coverage": float(s.coverage.mean()),
             "collateral": float(s.collateral.mean()),
             "n_ja4": float(s.n_ja4.mean())}
        agg[name] = e
        print(f"{name:<10}{al:>7}{e['coverage']*100:>11.1f}%{e['collateral']*100:>12.2f}%"
              f"{e['n_ja4']:>9.1f}{e['n']:>5}")
    (a.out_dir / "profile_drift.json").write_text(json.dumps(
        {"episode_alpha": a.alpha, "stacks": a.stacks, "K": a.K, "seeds": a.seeds,
         "min_support": 0.002, "min_enrichment": 3.0, "aggregate": agg}, indent=2))
    print(f"\nOK: {a.out_dir}/profile_drift.json")


if __name__ == "__main__":
    main()
