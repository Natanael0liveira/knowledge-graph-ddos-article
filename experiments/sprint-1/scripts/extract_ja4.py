#!/usr/bin/env python3
"""Extract JA4 fingerprints from a PCAP via tshark.

Reads TLS ClientHello records and outputs CSV with one row per handshake:
    src_ip, src_port, dst_ip, dst_port, timestamp, ja4, ja4s

Requires tshark 4.0+ with built-in JA4 support.

Usage:
    python extract_ja4.py --pcap input.pcap --out ja4.csv
"""
import argparse
import csv
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# tshark fields to extract for each TLS handshake
TSHARK_FIELDS = [
    "frame.time_epoch",
    "ip.src",
    "tcp.srcport",
    "ip.dst",
    "tcp.dstport",
    "tls.handshake.ja4",
    "tls.handshake.ja4s",
    "tls.handshake.extensions_server_name",  # SNI
]


def run_tshark(pcap_path: Path, fields: list[str]) -> list[list[str]]:
    """Run tshark, return list of rows."""
    cmd = [
        "tshark", "-r", str(pcap_path),
        "-Y", "tls.handshake.type == 1 or tls.handshake.type == 2",
        "-T", "fields",
        "-E", "separator=,",
        "-E", "occurrence=f",  # first occurrence only
    ]
    for f in fields:
        cmd.extend(["-e", f])

    log.info("Running tshark on %s ...", pcap_path)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=7200
        )
    except FileNotFoundError:
        log.error("tshark not found. Install Wireshark: `brew install wireshark`")
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        log.error("tshark exited with code %d", e.returncode)
        log.error("stderr: %s", e.stderr[:500])
        sys.exit(3)
    except subprocess.TimeoutExpired:
        log.error("tshark timed out after 2 hours")
        sys.exit(4)

    rows = []
    for line in result.stdout.splitlines():
        cells = line.split(",")
        if len(cells) >= len(fields):
            rows.append(cells)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pcap", required=True, type=Path, help="Input PCAP file")
    ap.add_argument("--out", required=True, type=Path, help="Output CSV file")
    args = ap.parse_args()

    if not args.pcap.exists():
        log.error("PCAP not found: %s", args.pcap)
        sys.exit(1)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    rows = run_tshark(args.pcap, TSHARK_FIELDS)
    log.info("Extracted %d TLS handshake records", len(rows))

    if not rows:
        log.warning("No TLS handshakes found. PCAP may be HTTP-only or compressed.")

    header = [
        "timestamp", "src_ip", "src_port",
        "dst_ip", "dst_port", "ja4", "ja4s", "sni",
    ]
    with args.out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

    log.info("Wrote %s (%d rows)", args.out, len(rows))


if __name__ == "__main__":
    main()
