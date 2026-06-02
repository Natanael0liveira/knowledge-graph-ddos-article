#!/usr/bin/env python3
"""Label CICIDS2017 (Wednesday) sessions by attacker-pair + time window.

`build_sessions.py` leaves CICIDS2017 sessions as UNLABELED (the Wednesday PCAP
carries no per-flow labels). We recover ground truth the same way the official
CICIDS2017 labels were produced: the DoS attacks all originate from the attacker
host 172.16.0.1 against victim 192.168.10.50:80, in well-separated time bursts.

So: a session is an attack iff it is on the attacker→victim:80 pair; its attack
TYPE is assigned by which time window its start_ts falls in. Window boundaries are
placed in the near-empty gaps observed between the real bursts (verified at 5-min
resolution), which align with the canonical Sharafaldin et al. (2018) schedule:
  Slowloris ~09:47–10:10 · Slowhttptest ~10:14–10:35 · Hulk ~10:43–11:00 ·
  GoldenEye ~11:10–11:23. Everything else is BENIGN.

(Heartbleed targets a different host/port (192.168.10.51:444) and is not an HTTP
flood, so it is out of scope for the coordination hypothesis and not labeled here.)
"""
import argparse
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ATTACKER = "172.16.0.1"
VICTIM = "192.168.10.50"
VICTIM_PORT = 80
DAY = "2017-07-05"

# (label, lower_inclusive, upper_exclusive) — boundaries sit in the inter-burst gaps
WINDOWS = [
    ("Slowloris",    f"{DAY} 09:40", f"{DAY} 10:12"),
    ("Slowhttptest", f"{DAY} 10:12", f"{DAY} 10:38"),
    ("Hulk",         f"{DAY} 10:38", f"{DAY} 11:05"),
    ("GoldenEye",    f"{DAY} 11:05", f"{DAY} 11:30"),
]


def label(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ts = pd.to_datetime(df["start_ts"])
    attacker_pair = (
        (df["src_ip_first"] == ATTACKER)
        & (df["dst_ip_first"] == VICTIM)
        & (df["dst_port_first"] == VICTIM_PORT)
    )
    lbl = pd.Series("BENIGN", index=df.index)
    # attacker-pair outside any window → DoS-Other (still attack, just stragglers)
    lbl[attacker_pair] = "DoS-Other"
    for name, lo, hi in WINDOWS:
        win = attacker_pair & (ts >= pd.Timestamp(lo)) & (ts < pd.Timestamp(hi))
        lbl[win] = name
    df["label_first"] = lbl.values
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None,
                    help="output parquet (default: overwrite --sessions)")
    args = ap.parse_args()

    df = pd.read_parquet(args.sessions)
    log.info("Loaded %d sessions", len(df))
    before = df.get("label_first", pd.Series(dtype=str)).value_counts(dropna=False)
    log.info("label_first antes: %s", before.to_dict())

    df = label(df)
    after = df["label_first"].value_counts()
    log.info("label_first depois:\n%s", after.to_string())
    n_attack = int((df["label_first"] != "BENIGN").sum())
    log.info("Ataque: %d (%.1f%%) | Benigno: %d",
             n_attack, 100 * n_attack / len(df), len(df) - n_attack)

    out = args.out or args.sessions
    df.to_parquet(out, index=False)
    log.info("✅ Escrito %s", out)


if __name__ == "__main__":
    main()
