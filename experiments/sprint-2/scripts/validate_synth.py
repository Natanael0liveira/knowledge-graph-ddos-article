#!/usr/bin/env python3
"""Calibration gate: synthetic legit traffic must match the real BENIGN traffic.

Compares the distributions of the *legitimate* synthetic sessions (is_attack ==
False) against the real BENIGN sessions from Sprint 1, via the two-sample
Kolmogorov–Smirnov test on the calibrated features (duration, requests/session).

Gate: KS statistic D ≤ 0.10 (distributions within ~10%, per the Sprint-2 README).

Usage:
    python validate_synth.py --real sessions.parquet --synth scenarios/A [--out report.json]
"""
import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import ks_2samp

sys.path.insert(0, str(Path(__file__).parent))
from synth_to_sessions import to_sessions  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

D_MAX = 0.10
FEATURES = ["duration_s", "n_requests"]


def load_synth_legit(synth: Path) -> pd.DataFrame:
    files = sorted(synth.glob("*.jsonl")) if synth.is_dir() else [synth]
    if not files:
        log.error("Nenhum .jsonl em %s", synth)
        sys.exit(1)
    ev = pd.concat([pd.read_json(f, lines=True) for f in files], ignore_index=True)
    sess = to_sessions(ev)
    return sess[~sess["is_attack"].astype(bool)]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--real", required=True, type=Path)
    ap.add_argument("--synth", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    real = pd.read_parquet(args.real)
    lbl = "label_first" if "label_first" in real.columns else "label"
    real_benign = real[real[lbl].str.upper() == "BENIGN"]
    synth = load_synth_legit(args.synth)
    log.info("Real BENIGN: %d | Synth legit: %d", len(real_benign), len(synth))

    results, all_pass = {}, True
    for feat in FEATURES:
        if feat not in real_benign or feat not in synth:
            continue
        D, p = ks_2samp(real_benign[feat].dropna(), synth[feat].dropna())
        ok = D <= D_MAX
        all_pass &= ok
        results[feat] = {"ks_D": float(D), "p_value": float(p), "pass": bool(ok)}
        log.info("  %-14s KS D=%.4f (p=%.3g) %s",
                 feat, D, p, "✅" if ok else "❌ (D>%.2f)" % D_MAX)

    print("\n========== GATE DE CALIBRAÇÃO (KS) ==========")
    for feat, r in results.items():
        print(f"{'✅' if r['pass'] else '❌'} {feat:14s} D={r['ks_D']:.4f} (limite ≤{D_MAX})")
    print("RESULTADO:", "PASS ✅" if all_pass else "FAIL ❌")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(
            {"d_max": D_MAX, "all_pass": all_pass, "features": results}, indent=2))
        log.info("Relatório → %s", args.out)


if __name__ == "__main__":
    main()
