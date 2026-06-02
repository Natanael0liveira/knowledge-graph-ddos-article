#!/usr/bin/env python3
"""Avalia o dano colateral da mitigação cirúrgica vs global em sintético CALIBRADO.

Completa o aspecto #3 do DEEP-DIVE: a vantagem cirúrgica só aparece quando os
atacantes têm um discriminador de peso alto (JA4 de botnet compartilhado) que o
tráfego legítimo no mesmo endpoint NÃO tem. O CIC-IoT2023 (LAN + não-TLS) não tem
isso; os cenários stealth calibrados têm. Aqui medimos, sobre N seeds, a fração de
legítimos atingida pela mitigação CIRÚRGICA (escopo derivado, inclui JA4) vs GLOBAL
(rate-limit no endpoint), com intervalo de confiança por bootstrap.

Uso:
    python collateral_eval.py --scenarios <dir-com-*.parquet> --coverage 0.5
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "sprint-1" / "scripts"))
sys.path.insert(0, str(HERE.parent))
from compute_coordination import assign_detection_clusters, compute_omega  # noqa: E402
from evidence_mitigation import derive_scope, matches_scope  # noqa: E402


def eval_one(parquet: Path, coverage: float):
    df = pd.read_parquet(parquet)
    df["start_ts"] = pd.to_datetime(df["start_ts"]); df["end_ts"] = pd.to_datetime(df["end_ts"])
    d = assign_detection_clusters(df, 300)
    cl = compute_omega(d)
    atk = cl[cl["attack_frac"] >= 0.5]
    if not len(atk):
        return None
    cid = atk.sort_values("omega", ascending=False).iloc[0]["det_cluster"]
    cluster = d[d["det_cluster"] == cid]
    scope = derive_scope(cluster, coverage=coverage)
    benign = df[df["label_first"] == "BENIGN"]
    if not len(benign):
        return None
    surgical = matches_scope(benign, scope).mean()
    # global = rate-limit no endpoint do cluster
    ep = scope.get("endpoint")
    bep = benign["dst_ip_first"].astype(str) + ":" + benign["dst_port_first"].astype(str)
    glob = (bep == ep).mean() if ep else 0.0
    return {"surgical": float(surgical), "global": float(glob),
            "has_ja4_in_scope": "tlsJa4" in scope, "scope": scope}


def boot_ci(v, rng):
    v = np.asarray(v)
    if not len(v):
        return (float("nan"),) * 3
    m = [rng.choice(v, len(v), replace=True).mean() for _ in range(2000)]
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scenarios", required=True, type=Path)
    ap.add_argument("--coverage", type=float, default=0.5)
    ap.add_argument("--max-files", type=int, default=30)
    args = ap.parse_args()
    files = sorted(p for p in args.scenarios.glob("*.parquet")
                   if not p.name.startswith("._"))[: args.max_files]
    rows = [r for r in (eval_one(f, args.coverage) for f in files) if r]
    if not rows:
        print("Sem clusters de ataque nos cenários."); return
    rng = np.random.default_rng(42)
    surg = [r["surgical"] for r in rows]; glob = [r["global"] for r in rows]
    sm, slo, shi = boot_ci(surg, rng); gm, glo, ghi = boot_ci(glob, rng)
    n_ja4 = sum(r["has_ja4_in_scope"] for r in rows)

    print("\n" + "=" * 60)
    print(f"PILAR 4 — DANO COLATERAL (n={len(rows)} cenários calibrados, cobertura={args.coverage})")
    print("=" * 60)
    print(f"JA4 no escopo derivado: {n_ja4}/{len(rows)} cenários")
    print(f"  mitigação CIRÚRGICA: {100*sm:.2f}% [{100*slo:.2f}–{100*shi:.2f}]")
    print(f"  rate-limit GLOBAL:   {100*gm:.2f}% [{100*glo:.2f}–{100*ghi:.2f}]")
    red = (1 - sm/gm)*100 if gm > 0 else float("nan")
    print(f"  → redução de dano colateral: {red:.1f}%")
    print(f"\nescopo exemplo: {rows[0]['scope']}")


if __name__ == "__main__":
    main()
