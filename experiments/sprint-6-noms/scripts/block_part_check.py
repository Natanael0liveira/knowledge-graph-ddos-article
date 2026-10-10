#!/usr/bin/env python3
"""Sprint 6 (NOMS) — a blind check of one exported part of the held-out block.

Loads the part with the frozen loader (rule_detection_production.load_day and
build_windows at 05ccc0e, from a worktree passed as --code), as the block run will, and
prints only:
- whether E3 and E4 load, and their first and last window;
- how many host-windows the part shares with the other day directories of the block;
- per endpoint E1..E4, the windows present in each export, out of 288 per day.

It prints no count of clients, fingerprints or alarms and writes nothing, so it can run
before the block is read, while a bad file can still be exported again. The endpoints
are the paper's, picked as production_tables.py --endpoints-from picks them.

Usage (from experiments/sprint-6-noms, with a worktree at 05ccc0e in $WT):
    python scripts/block_part_check.py --code $WT/experiments/sprint-6-noms/scripts \\
        --data-dir ../data/azion/block2 --part 2026-10-01_2026-10-05
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

DAY = re.compile(r"\d{4}-\d{2}-\d{2}(_\d{4}-\d{2}-\d{2})?")
PAPER_FOLDS = ("2026-09-20", "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24")


def days_in(name):
    a, _, b = name.partition("_")
    return (date.fromisoformat(b or a) - date.fromisoformat(a)).days + 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--code", required=True, type=Path, help="scripts/ of a checkout at 05ccc0e")
    ap.add_argument("--data-dir", required=True, type=Path, help="the block's directory (block2)")
    ap.add_argument("--part", required=True, help="the part's directory, e.g. 2026-10-01_2026-10-05")
    args = ap.parse_args()
    sys.path.insert(0, str(args.code.resolve()))
    import rule_detection_production as rdp  # noqa: E402  (the frozen loader)

    full = 288 * days_in(args.part)
    fp, pr = rdp.load_day(args.data_dir / args.part, "origin")
    print("load_day: ok, E3 and E4 found with the columns the run reads")
    for name, df in (("E3", fp), ("E4", pr)):
        print(f"{name}: windows {df['window'].min()} to {df['window'].max()} ({df['window'].dt.tz})")

    keys = set(zip(fp["host"], fp["window"])) | set(zip(pr["host"], pr["window"]))
    others = sorted(d.name for d in args.data_dir.iterdir()
                    if d.is_dir() and d.name != args.part and DAY.fullmatch(d.name) and any(d.glob("*.json")))
    shared = 0
    for o in others:
        f, p = rdp.load_day(args.data_dir / o, "origin")
        shared += len(keys & (set(zip(f["host"], f["window"])) | set(zip(p["host"], p["window"]))))
    print(f"host-windows shared with {', '.join(others)}: {shared}")

    prod = args.data_dir.parent
    ref = json.loads((prod / "results" / "rule_production_rolling_origin_v2.json").read_text())
    roles = json.loads((prod / "roles.json").read_text())
    ev = set.intersection(*(set(ref["folds"][f]) for f in PAPER_FOLDS))
    hosts = sorted((h for h in ev if h in roles), key=lambda h: -ref["hosts"][h]["median_test_size"])
    for i, h in enumerate(hosts):
        n3 = fp.loc[fp["host"] == h, "window"].nunique()
        n4 = pr.loc[pr["host"] == h, "window"].nunique()
        print(f"E{i + 1}: windows in E3 {n3}/{full}, in E4 {n4}/{full}")
    recs = rdp.build_windows(fp, pr)
    n = sum(r["host"] in hosts for r in recs)
    print(f"build_windows: ok, {n} endpoint-windows for E1-E4 (of {full * len(hosts)})")


if __name__ == "__main__":
    main()
