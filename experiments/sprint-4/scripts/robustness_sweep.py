#!/usr/bin/env python3
"""Passo B do HARDENING — sweep de robustez sobre a força de coordenação.

Ataca a ameaça de circularidade do sintético: se a config (d) acerta porque
medimos exatamente o sinal injetado, então remover o sinal deve degradar a
detecção SUAVEMENTE. Variamos a força dos sinais de coordenação e medimos AUC(d):
- `coordination_ja4_share` ∈ {1.0, 0.75, 0.5, 0.25, 0.0}  (JA4 compartilhado)
- `coordination_temporal_jitter` ∈ {0.0, 0.5, 1.0}        (ruído no padrão temporal)

Esperado: AUC(d) cai monotonicamente quando ja4_share→0 (sem o sinal de peso alto,
e com rede dispersa, sobra pouca coordenação detectável). Se AUC(d) ficar ~1.0
SEMPRE, há vazamento — investigar. Reporta também (a) e (c) como referência.

Usage:
    python robustness_sweep.py --dist-dir $DATA_ROOT/synth/distributions \
        --work $DATA_ROOT/synth/sprint4_robust --out-dir $DATA_ROOT/results --seeds 10
"""
import argparse
import logging
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
S2 = HERE.parents[2] / "sprint-2" / "scripts"
S3 = HERE.parents[2] / "sprint-3" / "scripts"
sys.path.insert(0, str(S3))
from run_ablation import build_features, FEATURE_SETS, auc_for  # noqa: E402
sys.path.insert(0, str(HERE.parents[2] / "sprint-1" / "scripts"))
from compute_coordination import _is_attack  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

STEALTH_CFG = S2.parent / "configs" / "scenario_stealth.yaml"
JA4_SHARES = [1.0, 0.75, 0.5, 0.25, 0.0]
JITTERS = [0.0, 0.5, 1.0]


def gen_scenario(py, dist_dir, work, K, seed, ja4, jitter):
    tag = f"K{K}_ja4{ja4}_jit{jitter}_s{seed}"
    parquet = work / f"{tag}.parquet"
    if parquet.exists():
        return parquet
    jsonl = work / f"{tag}.jsonl"
    subprocess.run([py, str(S2 / "generator.py"), "--config", str(STEALTH_CFG),
                    "--param", f"K={K}", "--param", f"coordination_ja4_share={ja4}",
                    "--param", f"coordination_temporal_jitter={jitter}",
                    "--seed", str(seed), "--distributions", str(dist_dir),
                    "--out", str(jsonl)], check=True, capture_output=True)
    subprocess.run([py, str(S2 / "synth_to_sessions.py"), "--jsonl", str(jsonl),
                    "--out", str(parquet)], check=True, capture_output=True)
    jsonl.unlink(missing_ok=True)
    return parquet


def auc_d(parquet):
    df = build_features(pd.read_parquet(parquet))
    y = _is_attack(df["label_first"]).astype(int).values
    if y.sum() < 2 or y.sum() == len(y):
        return {}
    out = {}
    for cfg in ("a_ml_sem_ontologia", "c_so_network_proximity", "d_completo"):
        out[cfg], _ = auc_for(FEATURE_SETS[cfg], df, y)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dist-dir", required=True, type=Path)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--K", type=int, default=500)
    ap.add_argument("--seeds", type=int, default=10)
    args = ap.parse_args()
    args.work.mkdir(parents=True, exist_ok=True)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    rows = []
    for ja4 in JA4_SHARES:
        for jitter in JITTERS:
            for seed in range(1, args.seeds + 1):
                p = gen_scenario(py, args.dist_dir, args.work, args.K, seed, ja4, jitter)
                r = auc_d(p)
                if r:
                    r.update({"ja4_share": ja4, "jitter": jitter, "seed": seed})
                    rows.append(r)
        log.info("ja4_share=%.2f concluído", ja4)

    df = pd.DataFrame(rows)
    df.to_csv(args.out_dir / "robustness_sweep.csv", index=False)

    print("\n" + "=" * 64)
    print(f"PASSO B — ROBUSTEZ vs FORÇA DE COORDENAÇÃO (K={args.K}, n={args.seeds})")
    print("=" * 64)
    print("AUC média (jitter agregado) por ja4_share:")
    print(f"{'ja4_share':>10}{'AUC(a)':>10}{'AUC(c)':>10}{'AUC(d)':>10}")
    for ja4 in JA4_SHARES:
        sub = df[df["ja4_share"] == ja4]
        if not len(sub):
            continue
        print(f"{ja4:>10.2f}{sub['a_ml_sem_ontologia'].mean():>10.3f}"
              f"{sub['c_so_network_proximity'].mean():>10.3f}{sub['d_completo'].mean():>10.3f}")
    # checagem de monotonicidade de (d) vs ja4_share
    means = [df[df["ja4_share"] == j]["d_completo"].mean() for j in JA4_SHARES if len(df[df["ja4_share"] == j])]
    mono = all(means[i] >= means[i+1] - 0.02 for i in range(len(means)-1))
    print(f"\nAUC(d) degrada monotonicamente com ja4_share↓: {'✅ sim' if mono else '⚠️ NÃO (investigar vazamento)'}")
    print(f"  ja4=1.0 → {means[0]:.3f}   ja4=0.0 → {means[-1]:.3f}   queda = {means[0]-means[-1]:+.3f}")
    print(f"\n✅ {args.out_dir}/robustness_sweep.csv")


if __name__ == "__main__":
    main()
