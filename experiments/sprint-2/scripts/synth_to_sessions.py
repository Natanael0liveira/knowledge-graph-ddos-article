#!/usr/bin/env python3
"""Aggregate synthetic JSONL events into a Sprint-1 sessions parquet.

The generator emits one line per HTTP request. The Sprint-1 coordination
analysis (`compute_coordination.py`) consumes per-session rows, so we group the
events by `session_id` and reduce them to the same schema produced by
`build_sessions.py` (src/dst, start/end, n_requests, duration_s, ja4, label).

Ground truth (`is_attack`, `campaign_id`) is preserved in extra columns so the
evaluation can score detection — the KG pipeline itself ignores them. The
`label_first` column is set to BENIGN / the attack variant so the existing
gate code (attack = label != BENIGN) works unchanged.

Usage:
    python synth_to_sessions.py --jsonl scenario.jsonl --out sessions.parquet
"""
import argparse
import json
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def to_sessions(events: pd.DataFrame) -> pd.DataFrame:
    events["timestamp"] = pd.to_datetime(events["timestamp"], format="ISO8601")
    g = events.groupby("session_id", sort=False)
    rows = g.agg(
        src_ip_first=("src_ip", "first"),
        src_port_first=("src_port", "first"),
        dst_ip_first=("dst_ip", "first"),
        dst_port_first=("dst_port", "first"),
        start_ts=("timestamp", "min"),
        end_ts=("timestamp", "max"),
        n_requests=("timestamp", "size"),
        ja4=("tls_ja4", "first"),
        identity_token=("identity_token", "first"),
        asn=("asn", "first"),
        is_attack=("is_attack", "max"),
        campaign_id=("campaign_id", "first"),
    ).reset_index()
    rows["duration_s"] = (rows["end_ts"] - rows["start_ts"]).dt.total_seconds()
    # label_first: attack variant (from UA) or BENIGN — keeps gate code unchanged.
    # The synthetic attack always carries is_attack=True; map to a single ATTACK
    # class (the variant is per-scenario, not per-session here).
    rows["label_first"] = rows["is_attack"].map({True: "ATTACK", False: "BENIGN"})
    # sni/ja3 absent in synth; add empty columns so TLS-coverage code is happy
    rows["ja3"] = pd.NA
    rows["sni"] = pd.NA
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jsonl", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    events = pd.read_json(args.jsonl, lines=True)
    log.info("Loaded %d events from %s", len(events), args.jsonl)
    sessions = to_sessions(events)
    n_atk = int(sessions["is_attack"].sum())
    log.info("→ %d sessions (%d attack, %d benign)",
             len(sessions), n_atk, len(sessions) - n_atk)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sessions.to_parquet(args.out, index=False)
    log.info("✅ %s", args.out)


if __name__ == "__main__":
    main()
