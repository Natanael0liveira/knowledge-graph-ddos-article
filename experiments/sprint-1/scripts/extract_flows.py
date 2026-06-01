#!/usr/bin/env python3
"""Extract flow features from a PCAP using cicflowmeter (Python implementation).

Wraps the cicflowmeter Python CLI, which produces flow-level features per
bidirectional flow (defined by 5-tuple). This is a Python reimplementation
of the original CICFlowMeter Java tool, with comparable feature output.

Usage:
    python extract_flows.py --pcap input.pcap --out flows.csv
"""
import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def run_cicflowmeter(pcap: Path, out_csv: Path, cicflowmeter_bin: str = "cicflowmeter") -> None:
    """Run cicflowmeter Python CLI on pcap.

    Command:
        cicflowmeter -f input.pcap -c output.csv
    """
    cmd = [
        cicflowmeter_bin,
        "-f", str(pcap),
        "-c", str(out_csv),
    ]
    log.info("Running cicflowmeter on %s ...", pcap.name)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=14400  # 4h
        )
    except FileNotFoundError:
        log.error("cicflowmeter not found in PATH. Install: pip install cicflowmeter")
        sys.exit(2)
    except subprocess.CalledProcessError as e:
        log.error("cicflowmeter exited with code %d", e.returncode)
        log.error("stderr: %s", e.stderr[:500])
        sys.exit(3)
    except subprocess.TimeoutExpired:
        log.error("cicflowmeter timed out after 4 hours")
        sys.exit(4)

    if result.stderr:
        log.debug("stderr: %s", result.stderr[-300:])
    log.debug("stdout: %s", result.stdout[-300:])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pcap", required=True, type=Path, help="Input PCAP")
    ap.add_argument("--out", required=True, type=Path, help="Output CSV (flows)")
    # Mantém --cicflowmeter para compatibilidade com Makefile antigo (JAR), mas ignora
    ap.add_argument(
        "--cicflowmeter", type=Path, default=None,
        help="(Compat) Path to old CICFlowMeter JAR — ignorado, usamos pip cicflowmeter",
    )
    ap.add_argument(
        "--java", default=None,
        help="(Compat) Path to java binary — ignorado, não usamos Java",
    )
    args = ap.parse_args()

    if not args.pcap.exists():
        log.error("PCAP not found: %s", args.pcap); sys.exit(1)

    # Encontrar cicflowmeter CLI (prefere venv local, fallback global)
    venv_bin = Path(__file__).resolve().parents[2] / ".venv" / "bin" / "cicflowmeter"
    if venv_bin.exists():
        cli = str(venv_bin)
    elif shutil.which("cicflowmeter"):
        cli = "cicflowmeter"
    else:
        log.error("cicflowmeter não encontrado. Execute: pip install cicflowmeter")
        sys.exit(2)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    run_cicflowmeter(args.pcap, args.out, cicflowmeter_bin=cli)
    log.info("Wrote %s", args.out)


if __name__ == "__main__":
    main()
