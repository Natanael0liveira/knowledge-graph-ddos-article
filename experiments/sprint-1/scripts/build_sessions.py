#!/usr/bin/env python3
"""Reconstruct ApplicationSession instances from flows + JA4.

Joins flow records (CICFlowMeter output) with JA4 fingerprints (extract_ja4.py
output) on the 5-tuple, groups into sessions within a temporal window, and
computes per-session features.

Session boundary policy:
    1. Group flows by (src_ip, src_port, dst_ip, dst_port, protocol)
    2. Split into separate sessions if inactivity gap > window seconds (default 300)
    3. Attach JA4 fingerprint (first observed for the 5-tuple)

Output: sessions.parquet with columns:
    session_id, src_ip, src_port, dst_ip, dst_port, protocol,
    ja4, ja4s, sni, start_ts, end_ts, duration_s,
    n_requests, total_bytes_fwd, total_bytes_bwd,
    mean_iat, std_iat, mean_byte_rate, label

Usage:
    python build_sessions.py --ja4-dir <ja4_dir> --flows-dir <flows_dir> \\
                             --out sessions.parquet [--window 300]
"""
import argparse
import logging
import sys
from pathlib import Path
import uuid

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def load_ja4(ja4_dir: Path) -> pd.DataFrame:
    """Load and concatenate all JA4 CSVs."""
    frames = []
    for f in sorted(ja4_dir.glob("*.csv")):
        if f.name.startswith("._"):  # AppleDouble metadata on ExFAT
            continue
        log.info("Loading JA4 from %s", f.name)
        df = pd.read_csv(f, dtype=str)
        df["source_pcap"] = f.stem
        frames.append(df)
    if not frames:
        log.error("No JA4 CSVs found in %s", ja4_dir); sys.exit(1)
    out = pd.concat(frames, ignore_index=True)
    log.info("Total JA4 records: %d", len(out))
    return out


def load_flows(flows_dir: Path) -> pd.DataFrame:
    """Load and concatenate all flow CSVs from CICFlowMeter."""
    frames = []
    for f in sorted(flows_dir.glob("*.csv")):
        if f.name.startswith("._"):
            continue
        log.info("Loading flows from %s", f.name)
        df = pd.read_csv(f)
        df["source_pcap"] = f.stem.replace(".pcap_Flow", "")
        frames.append(df)
    if not frames:
        log.error("No flow CSVs found in %s", flows_dir); sys.exit(1)
    out = pd.concat(frames, ignore_index=True)
    log.info("Total flow records: %d", len(out))
    return out


def normalize_flows(flows: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names across three sources:

    1. CICFlowMeter Java (CamelCase: "Src IP", "Total Fwd Packets", ...).
    2. CICIDS2017 official CSVs (same, often with a leading space: " Source IP").
    3. cicflowmeter Python 0.2.0 (snake_case: src_ip, tot_fwd_pkts, totlen_fwd_pkts).
    """
    rename = {
        # IPs and ports
        "Src IP": "src_ip", "Source IP": "src_ip", " Source IP": "src_ip",
        "Src Port": "src_port", "Source Port": "src_port", " Source Port": "src_port",
        "Dst IP": "dst_ip", "Destination IP": "dst_ip", " Destination IP": "dst_ip",
        "Dst Port": "dst_port", "Destination Port": "dst_port", " Destination Port": "dst_port",
        "Protocol": "protocol", " Protocol": "protocol",
        # Time
        "Timestamp": "timestamp", " Timestamp": "timestamp",
        "Flow Duration": "flow_duration_us", " Flow Duration": "flow_duration_us",
        "flow_duration": "flow_duration_us",
        # Packet counts (Java vs Python cicflowmeter)
        "Total Fwd Packets": "fwd_pkts", " Total Fwd Packets": "fwd_pkts",
        "tot_fwd_pkts": "fwd_pkts",
        "Total Backward Packets": "bwd_pkts", " Total Backward Packets": "bwd_pkts",
        "tot_bwd_pkts": "bwd_pkts",
        # Byte totals
        "Total Length of Fwd Packets": "fwd_bytes", "Total Length of Fwd Packet": "fwd_bytes",
        "totlen_fwd_pkts": "fwd_bytes",
        "Total Length of Bwd Packets": "bwd_bytes", " Total Length of Bwd Packets": "bwd_bytes",
        "totlen_bwd_pkts": "bwd_bytes",
        # Inter-arrival times
        "Flow IAT Mean": "iat_mean", " Flow IAT Mean": "iat_mean",
        "flow_iat_mean": "iat_mean",
        "Flow IAT Std": "iat_std", " Flow IAT Std": "iat_std",
        "flow_iat_std": "iat_std",
        # Labels (CICIDS2017 official CSVs only; Python cicflowmeter does not emit labels)
        "Label": "label", " Label": "label",
    }
    flows.columns = [c.strip() if isinstance(c, str) else c for c in flows.columns]
    rename_clean = {k.strip(): v for k, v in rename.items()}
    flows = flows.rename(columns=rename_clean)
    known = list(set(rename_clean.values())) + ["source_pcap"]
    out = flows[[c for c in known if c in flows.columns]].copy()

    # If no Label column present (Python cicflowmeter), derive a coarse label
    # from the source PCAP name (works for CIC-IoT2023 where attacks live in
    # separate PCAPs). CICIDS2017 Wednesday mixes BENIGN + Slow HTTP and needs
    # time-window-based labelling downstream — for now mark as "UNLABELED".
    if "label" not in out.columns and "source_pcap" in out.columns:
        def _label_from_pcap(name: str) -> str:
            n = name.lower()
            if "slowloris" in n: return "Slowloris"
            if "http_flood" in n or "http-flood" in n: return "HTTP-Flood"
            if "benign" in n: return "BENIGN"
            if "wednesday" in n: return "UNLABELED"
            return "UNLABELED"
        out["label"] = out["source_pcap"].astype(str).map(_label_from_pcap)

    return out


def build_sessions(
    flows: pd.DataFrame, ja4: pd.DataFrame, window_s: int = 300
) -> pd.DataFrame:
    """Build sessions by 5-tuple + temporal window."""
    log.info("Building sessions with window=%d s ...", window_s)

    # Convert timestamps
    flows["timestamp"] = pd.to_datetime(flows["timestamp"], errors="coerce")
    flows = flows.dropna(subset=["timestamp"])
    flows = flows.sort_values("timestamp")

    # Group key — protocol is numeric (6=TCP, 17=UDP) in Python cicflowmeter
    # but a string in CICIDS2017. Normalize to TCP/UDP/OTHER for stable joins.
    def _proto(p) -> str:
        s = str(p).strip()
        if s in ("6", "TCP", "tcp"): return "TCP"
        if s in ("17", "UDP", "udp"): return "UDP"
        return s or "OTHER"
    flows["proto_str"] = flows["protocol"].map(_proto)
    flows["tuple_key"] = (
        flows["src_ip"].astype(str) + ":" + flows["src_port"].astype(str) +
        "→" + flows["dst_ip"].astype(str) + ":" + flows["dst_port"].astype(str) +
        "/" + flows["proto_str"]
    )

    # Split into sessions: within a tuple_key, split if gap > window
    flows["session_id"] = None
    for key, grp in flows.groupby("tuple_key"):
        grp = grp.sort_values("timestamp")
        last_ts = None
        sid = None
        for idx, row in grp.iterrows():
            if last_ts is None or (row["timestamp"] - last_ts).total_seconds() > window_s:
                sid = str(uuid.uuid4())[:8]
            flows.at[idx, "session_id"] = sid
            last_ts = row["timestamp"]

    # JA4 lookup: first observed JA4 per 5-tuple. JA4 records are always TCP/TLS.
    # Note: tshark 4.6.6 has no ja4s field, so we carry ja3 as a fallback column.
    ja4["tuple_key"] = (
        ja4["src_ip"].astype(str) + ":" + ja4["src_port"].astype(str) +
        "→" + ja4["dst_ip"].astype(str) + ":" + ja4["dst_port"].astype(str) +
        "/TCP"
    )
    ja4_cols = [c for c in ("ja4", "ja4s", "ja3", "sni") if c in ja4.columns]
    ja4_lookup = ja4.groupby("tuple_key").first()[ja4_cols]

    # Aggregate per session
    aggs = {
        "src_ip": "first", "src_port": "first",
        "dst_ip": "first", "dst_port": "first",
        "protocol": "first",
        "timestamp": ["min", "max", "count"],
        "fwd_bytes": "sum",
        "bwd_bytes": "sum",
        "fwd_pkts": "sum",
        "bwd_pkts": "sum",
        "iat_mean": "mean",
        "iat_std": "mean",
        "label": "first",
        "source_pcap": "first",
        "tuple_key": "first",
    }
    # Only keep columns that actually exist
    aggs = {k: v for k, v in aggs.items() if k in flows.columns}
    sessions = flows.groupby("session_id").agg(aggs)

    # Flatten column names
    sessions.columns = [
        "_".join(c) if isinstance(c, tuple) else c for c in sessions.columns
    ]
    sessions = sessions.reset_index()

    # Rename min/max
    if "timestamp_min" in sessions.columns:
        sessions = sessions.rename(columns={
            "timestamp_min": "start_ts",
            "timestamp_max": "end_ts",
            "timestamp_count": "n_requests",
        })
    sessions["duration_s"] = (
        (sessions["end_ts"] - sessions["start_ts"]).dt.total_seconds()
    )

    # Attach JA4
    if "tuple_key_first" in sessions.columns:
        sessions = sessions.merge(
            ja4_lookup, left_on="tuple_key_first", right_index=True, how="left"
        )

    log.info("Built %d sessions from %d flows", len(sessions), len(flows))
    return sessions


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ja4-dir", required=True, type=Path)
    ap.add_argument("--flows-dir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--window", type=int, default=300, help="Inactivity gap (s)")
    args = ap.parse_args()

    ja4 = load_ja4(args.ja4_dir)
    flows = load_flows(args.flows_dir)
    flows = normalize_flows(flows)
    sessions = build_sessions(flows, ja4, args.window)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    sessions.to_parquet(args.out, index=False)
    log.info("Wrote %s (%d sessions)", args.out, len(sessions))


if __name__ == "__main__":
    main()
