#!/usr/bin/env python3
"""#4 — Isola a contribuição do JA4.

O Passo B não isolou o JA4 porque a convergência de endpoint (cluster_size) carregava
sozinha e o JA4 benigno do lab é pouco diverso (#3). Aqui isolamos o JA4 de duas formas:
(i) benigno com diversidade de JA4 REALISTA (`benign_ja4_pool` grande), como na internet;
(ii) detector que usa SOMENTE a feature `share_ja4` (peers no mesmo cluster com o mesmo
JA4), sem `cluster_size`/endpoint — então a convergência de endpoint não confunde.

Varremos `coordination_ja4_share` ∈ {1,0 … 0,0}. Previsão: o AUC do detector JA4-only
acompanha o ja4_share (alto→detecta, 0→acaso), provando que o JA4 é o sinal que carrega
quando isolado e quando o benigno tem diversidade realista. Reporta também o detector
completo (d) como referência.

Uso: python ja4_isolation.py --dist-dir ... --work ... --K 500 --seeds 5 --benign-pool 2000
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HERE = Path(__file__).resolve()
S2 = HERE.parents[2] / "sprint-2" / "scripts"
sys.path.insert(0, str(HERE.parents[2] / "sprint-1" / "scripts"))
from compute_coordination import assign_detection_clusters, session_features, _is_attack  # noqa: E402

CFG = S2.parent / "configs" / "scenario_stealth.yaml"
SHARES = [1.0, 0.75, 0.5, 0.25, 0.0]


def scenario(py, dist, work, K, seed, share, pool):
    tag = f"K{K}_sh{share}_s{seed}_pool{pool}"
    pq = work / f"{tag}.parquet"
    if pq.exists():
        return pq
    js = work / f"{tag}.jsonl"
    subprocess.run([py, str(S2/"generator.py"), "--config", str(CFG),
                    "--param", f"K={K}", "--param", f"coordination_ja4_share={share}",
                    "--param", f"benign_ja4_pool={pool}", "--seed", str(seed),
                    "--distributions", str(dist), "--out", str(js)], check=True, capture_output=True)
    subprocess.run([py, str(S2/"synth_to_sessions.py"), "--jsonl", str(js), "--out", str(pq)],
                   check=True, capture_output=True)
    js.unlink(missing_ok=True)
    return pq


def aucs(pq):
    df = pd.read_parquet(pq)
    df["start_ts"] = pd.to_datetime(df["start_ts"]); df["end_ts"] = pd.to_datetime(df["end_ts"])
    d = session_features(assign_detection_clusters(df, 300))
    y = _is_attack(d["label_first"]).astype(int).values
    if len(np.unique(y)) < 2:
        return None
    ja4_only = roc_auc_score(y, d["share_ja4"].astype(float).values)
    full = roc_auc_score(y, (d[["share_ja4", "cluster_size", "share_net"]].astype(float)
                             .pipe(lambda x: (x - x.mean()) / (x.std() + 1e-9)).sum(1)).values)
    return ja4_only, full


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dist-dir", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--K", type=int, default=500)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--benign-pool", type=int, default=2000)
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    rows = []
    for share in SHARES:
        for seed in range(1, args.seeds + 1):
            pq = scenario(py, args.dist_dir, args.work, args.K, seed, share, args.benign_pool)
            r = aucs(pq)
            if r:
                rows.append({"ja4_share": share, "ja4_only": r[0], "full_d": r[1]})
    df = pd.DataFrame(rows)

    print("\n" + "=" * 56)
    print(f"#4 — ISOLAMENTO DO JA4 (benigno diverso, pool={args.benign_pool}, K={args.K}, n={args.seeds})")
    print("=" * 56)
    print(f"{'ja4_share':>10}{'AUC(JA4-only)':>16}{'AUC(d completo)':>18}")
    means = {}
    for s in SHARES:
        sub = df[df["ja4_share"] == s]
        if not len(sub):
            continue
        means[s] = sub["ja4_only"].mean()
        print(f"{s:>10.2f}{sub['ja4_only'].mean():>16.3f}{sub['full_d'].mean():>18.3f}")
    seq = [means[s] for s in SHARES if s in means]
    mono = all(seq[i] >= seq[i+1] - 0.03 for i in range(len(seq)-1))
    print(f"\nJA4-only acompanha ja4_share (cai de {seq[0]:.3f} → {seq[-1]:.3f}): "
          f"{'✅ SIM (JA4 isolado como sinal)' if mono and seq[0]-seq[-1] > 0.2 else '⚠️ não'}")


if __name__ == "__main__":
    main()
