#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the evidence chain of Listing 2, from a canonical campaign.

Listing 2 used to show a CICIDS2017 DoS-Other cluster. Counted in origins, as the
rule now counts, that cluster holds two sources and does not fire: the laboratory
attacks come from one to seven origins, single-source floods that per-source
controls address. The listing therefore shows the fired cluster of a canonical
stealthy campaign (alpha = 1.5, M = 25, K = 1000, seed 1), with the scope derived
by the enrichment test at the calibrated level.

Usage:
    python example_chain.py --work $DATA_ROOT/synth/sprint6_realistic \\
        --clean-work $DATA_ROOT/synth/sprint6_rule --dist-dir ../../sprint-2/distributions \\
        --out ../results/example_chain.jsonld
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(HERE.parent), str(EXP / "sprint-1" / "scripts"),
                str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from compute_coordination import assign_detection_clusters, compute_omega  # noqa: E402
from evidence_mitigation import (decompose_omega, derive_scope_enriched,  # noqa: E402
                                 evidence_chain_jsonld)
from level_calibration import add_arguments, level_for  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", required=True, type=Path)
    ap.add_argument("--scenario", default="a1.5_m25_adv0_K1000_seed1")
    ap.add_argument("--alpha", type=float, default=1.5)
    ap.add_argument("--significance", type=float, default=0.01)
    ap.add_argument("--out", required=True, type=Path)
    add_arguments(ap)
    args = ap.parse_args()

    bg = pd.read_parquet(args.work / f"baseline_a{args.alpha}.parquet")
    profile = bg["ja4"].value_counts(normalize=True)
    profile.attrs["n"] = len(bg)
    level = level_for(profile, args.alpha, args)

    d = pd.read_parquet(args.work / f"{args.scenario}.parquet")
    d["start_ts"] = pd.to_datetime(d["start_ts"]); d["end_ts"] = pd.to_datetime(d["end_ts"])
    d = assign_detection_clusters(d, 300)
    cl = compute_omega(d, unit=args.unit)
    cid = cl.sort_values("omega", ascending=False).iloc[0]["det_cluster"]   # no label used
    cluster = d[d["det_cluster"] == cid]
    scope = derive_scope_enriched(cluster, profile, min_support=0.0, max_values=256,
                                  significance=level, unit=args.unit)
    scope.pop("_ja4_detail", None)
    if "tlsJa4" in scope:
        scope["tlsJa4"] = sorted(scope["tlsJa4"])
    chain = evidence_chain_jsonld(decompose_omega(cluster, unit=args.unit), scope, args.scenario)
    chain["kg:scopeLevel"] = level
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(chain, indent=2))
    print(json.dumps({k: v for k, v in chain.items() if k != "kg:derivedMitigationScope"}, indent=2))
    s = chain["kg:derivedMitigationScope"]
    print("scope:", {k: (len(v) if isinstance(v, list) else v) for k, v in s.items()})


if __name__ == "__main__":
    main()
