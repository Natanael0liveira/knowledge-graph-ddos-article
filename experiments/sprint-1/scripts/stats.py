#!/usr/bin/env python3
"""Print summary statistics for sessions and clusters."""
import argparse
from pathlib import Path
import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--clusters", type=Path, default=None)
    args = ap.parse_args()

    sessions = pd.read_parquet(args.sessions)
    print("="*60)
    print(f"SESSIONS: {len(sessions)}")
    print("="*60)

    label_col = "label_first" if "label_first" in sessions.columns else "label"
    if label_col in sessions.columns:
        print("\nLabel distribution:")
        print(sessions[label_col].value_counts().to_string())

    if "duration_s" in sessions.columns:
        print("\nDuration (s) statistics:")
        print(sessions["duration_s"].describe().to_string())

    if "ja4" in sessions.columns:
        unique_ja4 = sessions["ja4"].dropna().nunique()
        print(f"\nUnique JA4 fingerprints: {unique_ja4}")
        print("\nTop 10 most common JA4:")
        print(sessions["ja4"].value_counts().head(10).to_string())

    if args.clusters and args.clusters.exists():
        clusters = pd.read_csv(args.clusters)
        print("\n" + "="*60)
        print(f"CLUSTERS: {len(clusters)}")
        print("="*60)
        if "n_sessions" in clusters.columns:
            print("\nSessions per cluster:")
            print(clusters["n_sessions"].describe().to_string())
        if "label" in clusters.columns:
            print("\nLabel distribution:")
            print(clusters["label"].value_counts().to_string())


if __name__ == "__main__":
    main()
