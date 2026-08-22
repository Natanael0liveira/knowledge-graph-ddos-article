#!/usr/bin/env python3
"""Sprint 6 (NOMS) — probe of the production-realistic scenario axes.

A cheap scan over the three realism defects found in the generator, run before
committing to a full sweep. Each grid point generates one scenario per seed and
reports both halves of the claim:

  detection : per-session ROC AUC for ablation configs (a)-(d)
  mitigation: what the derived scope actually blocks (attacker coverage) AND
              what it costs (benign collateral) --- the pair, not just the half
              the paper currently reports

Axes:
  alpha      Zipf exponent of the benign JA4 popularity curve. 0 = the historical
             uniform draw (unrealistically flat); the calibrated real distribution
             over ~322k benign sessions has a 52.7% head, matched around 1.8-2.0.
  stacks     number of distinct TLS stacks in the botnet. 1 = the historical
             monolithic botnet; real botnets span device types.
  adversarial  when set, the botnet adopts the MOST COMMON benign fingerprints
             instead of a disjoint namespace --- what a competent attacker does.

Resource note: single process, nice'd, RandomForest capped at n_jobs=2, one
scenario held in memory at a time. This box has 8 cores / 8 GB.

Usage:
    python realistic_probe.py --grid 1.5:5:1 1.5:25:0 2.0:25:1 --seeds 5 \\
        --dist-dir $DATA_ROOT/synth/distributions \\
        --work $DATA_ROOT/synth/sprint6_realistic --out-dir ../results
"""
import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
S2 = EXP / "sprint-2" / "scripts"
sys.path[:0] = [str(EXP / "sprint-1" / "scripts"), str(EXP / "sprint-3" / "scripts"),
                str(EXP / "sprint-4" / "scripts"),
                str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from run_ablation import build_features  # noqa: E402
from run_sprint4 import STRONG_SETS  # noqa: E402
from compute_coordination import (_is_attack, assign_detection_clusters,  # noqa: E402
                                  compute_omega)
from evidence_mitigation import (derive_scope, matches_scope,  # noqa: E402
                                 derive_scope_enriched, matches_scope_multi)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

STEALTH_CFG = S2.parent / "configs" / "scenario_stealth.yaml"
N_JOBS = 2  # keep headroom on an 8-core / 8 GB box


def ensure_baseline(py, dist_dir, work, alpha):
    """Perfil histórico: janela SEM ataque, mesma distribuição benigna.

    É o que um operador tem antes da campanha; não usa rótulos.
    """
    pq = work / f"baseline_a{alpha}.parquet"
    if not pq.exists():
        jl = work / f"baseline_a{alpha}.jsonl"
        subprocess.run([py, str(S2 / "generator.py"), "--config", str(STEALTH_CFG),
                        "--param", "K=0",
                        "--param", f"benign_ja4_zipf_alpha={alpha}",
                        "--seed", "777", "--distributions", str(dist_dir),
                        "--out", str(jl)], check=True, capture_output=True)
        subprocess.run([py, str(S2 / "synth_to_sessions.py"), "--jsonl", str(jl),
                        "--out", str(pq)], check=True, capture_output=True)
        jl.unlink(missing_ok=True)
    bg = pd.read_parquet(pq)
    prof = bg["ja4"].value_counts(normalize=True)
    prof.attrs["n"] = len(bg)
    return prof


def ensure(py, dist_dir, work, alpha, stacks, adv, K, seed):
    tag = f"a{alpha}_m{stacks}_adv{int(adv)}_K{K}_seed{seed}"
    pq = work / f"{tag}.parquet"
    if pq.exists():
        return pq
    jl = work / f"{tag}.jsonl"
    subprocess.run([py, str(S2 / "generator.py"), "--config", str(STEALTH_CFG),
                    "--param", f"K={K}",
                    "--param", f"benign_ja4_zipf_alpha={alpha}",
                    "--param", f"botnet_ja4_stacks={stacks}",
                    "--param", f"botnet_ja4_adversarial={'true' if adv else 'false'}",
                    "--seed", str(seed), "--distributions", str(dist_dir),
                    "--out", str(jl)], check=True, capture_output=True)
    subprocess.run([py, str(S2 / "synth_to_sessions.py"), "--jsonl", str(jl),
                    "--out", str(pq)], check=True, capture_output=True)
    jl.unlink(missing_ok=True)
    return pq


def evaluate(pq, profile):
    raw = pd.read_parquet(pq)
    df = build_features(raw)
    y = _is_attack(df["label_first"]).astype(int).values
    if y.sum() < 2 or y.sum() == len(y):
        return None
    itr, ite = train_test_split(np.arange(len(y)), test_size=0.3,
                                random_state=42, stratify=y)
    out = {}
    for cfg, feats in STRONG_SETS.items():
        X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values
        clf = RandomForestClassifier(n_estimators=200, random_state=42,
                                     class_weight="balanced", n_jobs=N_JOBS)
        clf.fit(X[itr], y[itr])
        out[cfg] = roc_auc_score(y[ite], clf.predict_proba(X[ite])[:, 1])

    # ---- mitigation: both halves ----
    d = raw.copy()
    d["start_ts"] = pd.to_datetime(d["start_ts"]); d["end_ts"] = pd.to_datetime(d["end_ts"])
    d = assign_detection_clusters(d, 300)
    cl = compute_omega(d)
    atk_cl = cl[cl["attack_frac"] >= 0.5]
    if len(atk_cl):
        cid = atk_cl.sort_values("omega", ascending=False).iloc[0]["det_cluster"]
        cluster = d[d["det_cluster"] == cid]
        A = raw[raw["label_first"] == "ATTACK"]
        B = raw[raw["label_first"] == "BENIGN"]
        # (i) heurística atual do paper: JA4 modal do subconjunto coordenado
        scope = derive_scope(cluster, coverage=0.5)
        out["mit_attack_cov"] = float(matches_scope(A, scope).mean())
        out["mit_collateral"] = float(matches_scope(B, scope).mean())
        out["mit_ja4_in_scope"] = "tlsJa4" in scope
        # (ii) proposta: discriminador escolhido por enriquecimento sobre o fundo
        scope_e = derive_scope_enriched(cluster, profile)
        out["enr_attack_cov"] = float(matches_scope_multi(A, scope_e).mean())
        out["enr_collateral"] = float(matches_scope_multi(B, scope_e).mean())
        out["enr_ja4_in_scope"] = "tlsJa4" in scope_e
        out["enr_n_ja4"] = len(scope_e.get("tlsJa4", []) or [])
        ep = scope.get("endpoint")
        bep = B["dst_ip_first"].astype(str) + ":" + B["dst_port_first"].astype(str)
        out["mit_global_collateral"] = float((bep == ep).mean()) if ep else 0.0
    else:
        out.update({"mit_attack_cov": float("nan"), "mit_collateral": float("nan"),
                    "mit_ja4_in_scope": False, "mit_global_collateral": float("nan"),
                    "enr_attack_cov": float("nan"), "enr_collateral": float("nan"),
                    "enr_ja4_in_scope": False, "enr_n_ja4": 0})

    # ---- descriptive: is the botnet even the most 'coordinated' group? ----
    b = raw[raw["label_first"] == "BENIGN"]
    a = raw[raw["label_first"] == "ATTACK"]
    out["benign_head_share"] = float(b["ja4"].value_counts().iloc[0] / len(b))
    out["benign_ja4_distinct"] = int(b["ja4"].nunique())
    out["share_ja4_attack"] = float(df.loc[y == 1, "share_ja4"].mean())
    out["share_ja4_benign"] = float(df.loc[y == 0, "share_ja4"].mean())
    out["ja4_overlap"] = int(len(set(a["ja4"].dropna()) & set(b["ja4"].dropna())))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--grid", nargs="+", required=True,
                    help="pontos alpha:stacks:adv, ex 1.5:5:1")
    ap.add_argument("--K", type=int, default=1000)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--dist-dir", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--tag", default="probe")
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    rows = []
    for point in args.grid:
        alpha, stacks, adv = point.split(":")
        alpha, stacks, adv = float(alpha), int(stacks), bool(int(adv))
        profile = ensure_baseline(py, args.dist_dir, args.work, alpha)
        for seed in range(1, args.seeds + 1):
            pq = ensure(py, args.dist_dir, args.work, alpha, stacks, adv, args.K, seed)
            r = evaluate(pq, profile)
            if r:
                r.update({"alpha": alpha, "stacks": stacks, "adversarial": adv,
                          "K": args.K, "seed": seed})
                rows.append(r)
        log.info("done %s (%d seeds)", point, args.seeds)

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / f"realistic_{args.tag}_runs.csv", index=False)

    keys = ["a_ml_sem_ontologia", "b_ontologia_sem_related",
            "c_so_network_proximity", "d_completo"]
    print("\n" + "=" * 108)
    print(f"PRODUCTION-REALISTIC PROBE  (K={args.K}, n={args.seeds} seeds, mean)")
    print("=" * 108)
    print(f"{'alpha':>6} {'stk':>4} {'adv':>4} {'head%':>6} {'#ja4':>5} "
          f"{'shJA4 atk/ben':>14} {'ovl':>4} | "
          + "".join(f"{k.split('_')[0]:>7}" for k in keys)
          + f" | {'modal cov/coll':>14} {'ENRICH cov/coll':>14} {'#ja4':>4} {'glob':>6}")
    print("-" * 108)
    for point in args.grid:
        alpha, stacks, adv = point.split(":")
        sub = df[(df.alpha == float(alpha)) & (df.stacks == int(stacks))
                 & (df.adversarial == bool(int(adv)))]
        if not len(sub):
            continue
        print(f"{alpha:>6} {stacks:>4} {adv:>4} "
              f"{sub.benign_head_share.mean()*100:>5.1f}% {sub.benign_ja4_distinct.mean():>5.0f} "
              f"{sub.share_ja4_attack.mean():>6.0f}/{sub.share_ja4_benign.mean():<7.0f} "
              f"{sub.ja4_overlap.mean():>4.0f} | "
              + "".join(f"{sub[k].mean():>7.3f}" for k in keys)
              + f" | {sub.mit_attack_cov.mean()*100:>6.1f}%/{sub.mit_collateral.mean()*100:<6.1f}%"
                f" {sub.enr_attack_cov.mean()*100:>6.1f}%/{sub.enr_collateral.mean()*100:<6.1f}%"
                f" {sub.enr_n_ja4.mean():>4.1f} {sub.mit_global_collateral.mean()*100:>6.1f}%")
    (args.out_dir / f"realistic_{args.tag}.json").write_text(
        json.dumps({"grid": args.grid, "K": args.K, "seeds": args.seeds,
                    "rows": rows}, indent=2, default=str))
    print(f"\nOK: {args.out_dir}/realistic_{args.tag}_runs.csv")


if __name__ == "__main__":
    main()
