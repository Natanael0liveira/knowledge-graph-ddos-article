#!/usr/bin/env python3
"""Derive cluster ground truth from sessions.

Heuristic: sessions are clustered together if they share label (attack/benign)
AND fall within a temporal proximity window. For attack sessions, additional
constraints by shared JA4 or shared destination endpoint can refine clusters.

Output: clusters.csv + clusters.csv.sample (10 random clusters for manual review)

Usage:
    python derive_clusters.py --sessions sessions.parquet --out clusters.csv
"""
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def derive_clusters(
    sessions: pd.DataFrame, time_window_s: int = 300
) -> pd.DataFrame:
    """Cluster sessions by (label, dst_ip, dst_port, ja4) within time window."""
    log.info("Deriving clusters with time_window=%d s ...", time_window_s)

    # Sort by start time
    sessions = sessions.sort_values("start_ts").copy()

    # Cluster key: same attack label + same target + similar JA4 within window
    sessions["cluster_id"] = None
    cluster_idx = 0

    # Group by (label, dst_ip, dst_port) and then sweep by time
    label_col = "label_first" if "label_first" in sessions.columns else "label"
    if label_col not in sessions.columns:
        log.error("No label column. Cannot derive ground truth.")
        sys.exit(1)

    group_cols = [label_col]
    if "dst_ip_first" in sessions.columns:
        group_cols.extend(["dst_ip_first", "dst_port_first"])
    elif "dst_ip" in sessions.columns:
        group_cols.extend(["dst_ip", "dst_port"])

    for group_keys, grp in sessions.groupby(group_cols):
        grp = grp.sort_values("start_ts")
        cluster_idx += 1
        current_cluster = f"c{cluster_idx:04d}"
        last_end = None
        for idx, row in grp.iterrows():
            if last_end is not None:
                gap = (row["start_ts"] - last_end).total_seconds()
                if gap > time_window_s:
                    cluster_idx += 1
                    current_cluster = f"c{cluster_idx:04d}"
            sessions.at[idx, "cluster_id"] = current_cluster
            last_end = row["end_ts"]

    # Aggregate cluster info
    cluster_info = sessions.groupby("cluster_id").agg({
        "session_id": "count",
        "start_ts": "min",
        "end_ts": "max",
        label_col: "first",
    }).rename(columns={
        "session_id": "n_sessions",
        "start_ts": "cluster_start",
        "end_ts": "cluster_end",
        label_col: "label",
    })
    cluster_info["duration_s"] = (
        (cluster_info["cluster_end"] - cluster_info["cluster_start"]).dt.total_seconds()
    )

    log.info("Derived %d clusters (%d attack, %d benign)",
             len(cluster_info),
             (cluster_info["label"] != "BENIGN").sum() if (cluster_info["label"] == "BENIGN").any() else len(cluster_info),
             (cluster_info["label"] == "BENIGN").sum())

    return sessions, cluster_info


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--time-window", type=int, default=300)
    ap.add_argument("--sample", type=int, default=10, help="Random sample for review")
    args = ap.parse_args()

    sessions = pd.read_parquet(args.sessions)
    log.info("Loaded %d sessions", len(sessions))

    sessions_clustered, clusters = derive_clusters(sessions, args.time_window)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    clusters.to_csv(args.out, index=True)
    log.info("Wrote %s", args.out)

    # Sample for manual review
    sample = clusters.sample(min(args.sample, len(clusters)), random_state=42)
    sample_path = args.out.with_suffix(".sample.csv")
    sample.to_csv(sample_path, index=True)
    log.info("Wrote sample for manual review: %s", sample_path)

    # Also save sessions with cluster_id attached
    sessions_clustered.to_parquet(args.sessions, index=False)
    log.info("Updated %s with cluster_id column", args.sessions)


if __name__ == "__main__":
    main()
