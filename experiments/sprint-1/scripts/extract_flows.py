#!/usr/bin/env python3
"""Extract flow features from a PCAP using CICFlowMeter.

Wraps the CICFlowMeter Java tool, which produces 80+ flow-level features
per bidirectional flow (defined by 5-tuple).

Usage:
    python extract_flows.py --pcap input.pcap --out flows.csv \\
                            --cicflowmeter ../tools/CICFlowMeter.jar
"""
import argparse
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def run_cicflowmeter(pcap: Path, jar: Path, out_dir: Path, java_bin: str = "java") -> Path:
    """Run CICFlowMeter on pcap, output goes to out_dir/<basename>.pcap_Flow.csv."""
    cmd = [
        java_bin, "-jar", str(jar),
        str(pcap), str(out_dir),
    ]
    log.info("Running CICFlowMeter on %s ...", pcap.name)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=14400  # 4h
        )
    except FileNotFoundError:
        log.error("java not found. Install Java 17+: `brew install openjdk@17`")
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        log.error("CICFlowMeter exited with code %d", e.returncode)
        log.error("stderr: %s", e.stderr[:500])
        sys.exit(3)

    log.debug("CICFlowMeter stdout: %s", result.stdout[-500:])
    # CICFlowMeter saves <pcap_name>.pcap_Flow.csv in out_dir
    expected = out_dir / f"{pcap.stem}.pcap_Flow.csv"
    if not expected.exists():
        # Try alternate naming
        candidates = list(out_dir.glob(f"{pcap.stem}*_Flow.csv"))
        if not candidates:
            log.error("CICFlowMeter did not produce expected output in %s", out_dir)
            sys.exit(4)
        expected = candidates[0]
    return expected


def main():
    import os
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pcap", required=True, type=Path, help="Input PCAP")
    ap.add_argument("--out", required=True, type=Path, help="Output CSV (flows)")
    ap.add_argument(
        "--cicflowmeter", type=Path, default=Path("../tools/CICFlowMeter.jar"),
        help="Path to CICFlowMeter JAR",
    )
    ap.add_argument(
        "--java", default=os.environ.get("JAVA", "java"),
        help="Path to java binary (defaults to env JAVA or 'java' in PATH)",
    )
    args = ap.parse_args()

    if not args.pcap.exists():
        log.error("PCAP not found: %s", args.pcap); sys.exit(1)
    if not args.cicflowmeter.exists():
        log.error("CICFlowMeter JAR not found: %s", args.cicflowmeter)
        log.error("Run: make install-cicflowmeter")
        sys.exit(1)

    args.out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        produced = run_cicflowmeter(args.pcap, args.cicflowmeter, tmp, java_bin=args.java)
        produced.rename(args.out)

    log.info("Wrote %s", args.out)


if __name__ == "__main__":
    main()
