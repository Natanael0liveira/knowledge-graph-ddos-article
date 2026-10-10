#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the held-out block's report: metrics 1 to 10 and their decision rules.

Reads the block's reduction (production_tables.py at 05ccc0e, with the 14 block days as
test folds: production_tables_block.json) and, for metric 10, ja4_churn.py's output on
the block. It gives the metrics of heldout_block_protocol.md (1 to 7) and of
heldout_block_protocol_addendum_metrics.md (8 to 10), with the protocol's rules:
- 1, Primary A: the binomial configuration's false alarms, pooled over E1..E4,
  consistent with the test days if P[Bin(n, 5/5,643) >= x] >= 0.05;
- 2, Primary B: configurations 3 to 5 per endpoint, within the budget if the rate is at
  most 1%, and shown within it if the upper end of the exact 95% interval is;
- 3 to 6: detection, flash crowds, the cost of a false alarm, false alarms per day;
- 7: on each endpoint, the baseline (3) against the arms (4, and 5 on E1). An arm is
  preferred there only if it is within the budget and stops more on new or shared
  stacks. As the protocol writes it, the comparison is on the tenth-size botnet, at the
  precision the paper prints (0.1 point). As amended before the block was read, it is on
  the tenth-size botnet on E1 and on 100 attackers on E2-E4, where a tenth-size botnet
  holds fewer attackers than stacks, and an arm must stop at least one point more;
- 8: the scope's misfires once the gate opens, consistent with the test days if
  P[Bin(g, 5/168) >= x] >= 0.05;
- 9: the binomial configuration's false alarms on weekend days and on weekdays (UTC);
- 10: per endpoint and day, the fingerprints absent from the profile that reach k_min
  origins in some window, next to that day's false alarms. ja4_churn.py takes its
  endpoints from the run it is given, so they are matched to E1..E4 by their role.

Only rates, shares and counts leave, per endpoint E1..E4.

--check runs the same code on the paper's reduction (results/production_tables.json and
results/ja4_churn.json) and compares it with the numbers the paper prints, so the
arithmetic is checked before the block is read.

Usage:
    python block_report.py --tables ../results/production_tables_block.json \\
        --churn ../results/ja4_churn_block.json --out ../results/block_report.json
    python block_report.py --check
"""
import argparse
import json
from datetime import date
from pathlib import Path

from scipy.stats import beta, binom

RESULTS = Path(__file__).resolve().parent.parent / "results"

# The test days' rates of the binomial configuration that the block is compared with:
# joint misfires over clean windows (metric 1), and over the clean windows where its
# gate opened (metric 8).
REF_FA, REF_COND = (5, 5643), (5, 168)
BUDGET, ALPHA, MIN_DAYS = 0.01, 0.05, 7

# The protocol's configurations: (run in production_tables.py, scope|gate, name)
CONFIGS = {
    1: ("fleets", "union|origins", "binomial configuration (primary)"),
    2: ("base", "enrichment|omega", "base rule, Omega gate (reference)"),
    3: ("fleets", "unseen|none", "unseen filter as its own trigger (baseline)"),
    4: ("xfit_od", "union|seasonal", "cross-fitted beta-binomial behind the seasonal gate"),
    5: ("fleets", "union|none", "binomial scope with known fleets as its own trigger"),
    6: ("base", "zcal|origins", "calibrated z-score (reference)"),
}
ONLY_E1 = {5}                       # configuration 5 is defined on the busiest endpoint
# E1's tenth-size botnet per day (stealth_E1 of production_tables.py), where it is kept
STEALTH = {1: ("fleets", "blocked"), 4: ("xfit_od", "blocked_seasonal"), 5: ("fleets", "blocked_no_gate")}
CELLS = ("new:A100", "new:A1000", "new:x0.1", "new:x1",
         "shared:A100", "shared:A1000", "shared:x0.1", "shared:x1")


def interval(k, n, level=0.95):
    """Exact two-sided interval for k/n, as production_tables.clopper_pearson."""
    if not n:
        return None
    a = (1 - level) / 2
    return [float(beta.ppf(a, k, n - k + 1)) if k else 0.0,
            float(beta.ppf(1 - a, k + 1, n - k)) if k < n else 1.0]


def tail(x, n, p):
    """P[Bin(n, p) >= x]."""
    return float(binom.sf(x - 1, n, p))


def largest_consistent(n, p):
    """The largest count x with P[Bin(n, p) >= x] >= ALPHA."""
    x = 0
    while tail(x + 1, n, p) >= ALPHA:
        x += 1
    return x


def pct(v):
    """A share as the paper prints it, in percent to 0.1 point."""
    return round(100 * v, 1)


def report(J, section, churn=None):
    S, E = J[section], list(J["endpoints"])

    def get(c, e=None):
        run, key, _ = CONFIGS[c]
        return S[run]["all"][key] if e is None else S[run]["per_endpoint"][e][key]

    def where(c):
        """Pooled (None) and per endpoint, or E1 alone for configuration 5."""
        return ["E1"] if c in ONLY_E1 else [None] + E

    days = sorted(get(1)["clean_fires_by_fold"])
    out = {"section": section, "days": days, "enough_days": len(days) >= MIN_DAYS,
           "configs": {c: v[2] for c, v in CONFIGS.items()}}

    # 1. Primary A
    r = get(1)
    x, n, p = r["clean_fires"], r["clean_windows"], REF_FA[0] / REF_FA[1]
    out["m1"] = {"fires": x, "windows": n, "rate": x / n, "ci95": interval(x, n),
                 "ci95_cluster": r["clean_ci95_cluster"], "P": tail(x, n, p),
                 "largest_consistent": largest_consistent(n, p), "consistent": tail(x, n, p) >= ALPHA}

    # 2. Primary B
    out["m2"] = {}
    for c in (3, 4, 5):
        for e in [e for e in where(c) if e]:
            r = get(c, e)
            x, n = r["clean_fires"], r["clean_windows"]
            up = interval(x, n)[1]
            out["m2"].setdefault(c, {})[e] = {"fires": x, "windows": n, "rate": x / n, "upper95": up,
                                             "within": x / n <= BUDGET, "shown_within": up <= BUDGET}

    # 3. Detection: blocked share per botnet cell, and E1's tenth-size botnet per day
    out["m3"] = {c: {e or "all": {k: get(c, e)[k]["blocked"] for k in CELLS} for e in where(c)} for c in CONFIGS}
    SE = J["stealth_E1"]
    out["m3_e1_by_day"] = {c: {name: {d: SE[run][f"{src}:x0.1"][d][field] for d in days}
                               for name, src in (("new", "fresh"), ("shared", "tail"))}
                           for c, (run, field) in STEALTH.items()}

    # 4. Flash crowds, and 5. the cost of a false alarm
    out["m4"] = {c: {e or "all": {k: get(c, e)[k] for k in ("flash100", "flash100_collateral_median",
                                                            "flash1000", "flash1000_collateral_median")}
                     for e in where(c)} for c in CONFIGS}
    out["m5"] = {}
    for c in CONFIGS:
        for e in where(c):
            r = get(c, e)
            mean = r["clean_collateral_mean"]
            out["m5"].setdefault(c, {})[e or "all"] = {
                "collateral_median": r["clean_collateral_median"], "collateral_mean": mean,
                "expected_per_window": r["clean_rate"] * mean if mean is not None else 0.0}

    # 6. Clustering: false alarms per day and endpoint
    out["m6"] = {c: {e: get(c, e)["clean_fires_by_fold"] for e in where(c) if e} for c in CONFIGS}

    # 7. The comparison of Section VI, as the protocol writes it (the tenth-size botnet on
    # every endpoint, any larger share) and as amended before the block was read (the
    # tenth-size botnet on E1 and 100 attackers on E2-E4, where a tenth-size botnet holds
    # fewer attackers than stacks; at least one point more)
    def compare(size, margin):
        res = {}
        for e in E:
            cell = size(e)
            b = get(3, e)
            base = {"cell": cell, "within": out["m2"][3][e]["within"],
                    "new": pct(b[f"new:{cell}"]["blocked"]), "shared": pct(b[f"shared:{cell}"]["blocked"])}
            arms = {}
            for c in (4, 5):
                if e not in where(c):
                    continue
                a = get(c, e)
                new, shared = pct(a[f"new:{cell}"]["blocked"]), pct(a[f"shared:{cell}"]["blocked"])
                within = out["m2"][c][e]["within"]
                more = new > base["new"] + margin or shared > base["shared"] + margin
                arms[c] = {"within": within, "new": new, "shared": shared, "preferred": within and more}
            res[e] = {"baseline": base, "arms": arms}
        return res
    out["m7"] = {"as_written": compare(lambda e: "x0.1", 0.0),
                 "amended": compare(lambda e: "x0.1" if e == "E1" else "A100", 1.0 - 1e-9)}

    # 8. The scope once the gate opens
    p = REF_COND[0] / REF_COND[1]
    out["m8"] = {}
    for e in [None] + E:
        r = get(1, e)
        x, g = r["clean_fires"], r["clean_gate_windows"]
        m = {"misfires": x, "gate_windows": g, "share": x / g if g else None, "ci95": interval(x, g)}
        if e is None:                # the rule is pooled; per endpoint it is descriptive
            m |= {"P": tail(x, g, p), "consistent": tail(x, g, p) >= ALPHA}
        out["m8"][e or "all"] = m

    # 9. The weekly cycle
    by = get(1)["clean_fires_by_fold"]
    end = [d for d in days if date.fromisoformat(d).weekday() >= 5]
    out["m9"] = {"weekend": {"days": end, "fires": sum(by[d] for d in end)},
                 "weekdays": {"days": [d for d in days if d not in end],
                              "fires": sum(by[d] for d in days if d not in end)}}

    # 10. Fingerprint churn, matched to E1..E4 by role
    if churn is not None:
        role = {v: k for k, v in J["endpoints"].items()}
        if len(role) != len(E):
            raise SystemExit("two endpoints share a role; metric 10 cannot match them")
        match = {a: role[v] for a, v in churn["endpoints"].items() if v in role}
        rows, per = [], {}
        for a, e in sorted(match.items(), key=lambda t: t[1]):
            for d in days:
                c = churn["per_endpoint"][a].get(d)
                if c is None:
                    continue
                rows.append(c)
                per.setdefault(e, {})[d] = {
                    "new_fingerprints_kmin": c["new_fingerprints_kmin"],
                    "windows_with_candidate_share": c["windows_with_candidate_share"],
                    "fa_config1": get(1, e)["clean_fires_by_fold"].get(d),
                    "fa_config3": get(3, e)["clean_fires_by_fold"].get(d)}
        w = sum(c["windows"] for c in rows)
        out["m10"] = {"missing_endpoints": sorted(set(E) - set(match.values())), "per_endpoint": per,
                      "windows_with_candidate_share": sum(c["windows_with_candidate"] for c in rows) / w if w else None}
    return out


def show(o):
    P = lambda v, d=2: "--" if v is None else f"{100 * v:.{d}f}%"
    m1 = o["m1"]
    print(f"== {o['section']}: {len(o['days'])} days ({o['days'][0]} to {o['days'][-1]}), "
          f"{'enough' if o['enough_days'] else 'FEWER THAN 7'} to run")
    print(f"1. Primary A: {m1['fires']} false alarms in {m1['windows']} clean windows, {P(m1['rate'], 3)} "
          f"(exact 95% {P(m1['ci95'][0], 3)}-{P(m1['ci95'][1], 3)}). P = {m1['P']:.3f}, "
          f"{'consistent' if m1['consistent'] else 'NOT consistent'} (up to {m1['largest_consistent']} would be)")
    print("2. Primary B, per endpoint: false alarms/windows, rate, upper end of the exact 95% interval")
    for c, per in o["m2"].items():
        for e, m in per.items():
            verdict = "shown within" if m["shown_within"] else "within" if m["within"] else "OVER"
            print(f"   config {c} {e}: {m['fires']}/{m['windows']}, {P(m['rate'])}, {P(m['upper95'])}: {verdict}")
    print("3. Blocked share, pooled (config 5: E1), new and shared stacks, 100/1000 attackers, 0.1x/1x:")
    for c, per in o["m3"].items():
        m = per.get("all", per.get("E1"))
        print(f"   config {c}: new " + " ".join(f"{100 * m[k]:.1f}" for k in CELLS[:4])
              + " | shared " + " ".join(f"{100 * m[k]:.1f}" for k in CELLS[4:]))
    for c, v in o["m3_e1_by_day"].items():
        print(f"   E1 tenth-size by day, config {c}: new "
              + " ".join(f"{100 * x:.1f}" for x in v["new"].values()) + " | shared "
              + " ".join(f"{100 * x:.1f}" for x in v["shared"].values()))
    print("4-5. Flash crowds (rate, median share blocked) and the cost of a false alarm (median share):")
    for c in o["m4"]:
        f = o["m4"][c].get("all", o["m4"][c].get("E1"))
        k = o["m5"][c].get("all", o["m5"][c].get("E1"))
        print(f"   config {c}: 100 users {P(f['flash100'], 1)} ({P(f['flash100_collateral_median'], 1)}), "
              f"1000 users {P(f['flash1000'], 1)} ({P(f['flash1000_collateral_median'], 1)}); "
              f"false alarm {P(k['collateral_median'], 1)}, expected per clean window {P(k['expected_per_window'], 3)}")
    print("6. False alarms per day and endpoint (config 1):")
    for e, by in o["m6"][1].items():
        print(f"   {e}: " + " ".join(str(v) for v in by.values()))
    for version, label in (("as_written", "as written: tenth-size botnet, any larger share"),
                           ("amended", "amended: tenth-size on E1, 100 attackers on E2-E4, one point more")):
        print(f"7. Baseline (3) against the arms (4, and 5 on E1), blocked % ({label}):")
        for e, m in o["m7"][version].items():
            b = m["baseline"]
            arms = "; ".join(f"arm {c} {'within' if a['within'] else 'OVER'}, new {a['new']}, shared {a['shared']}: "
                             f"{'PREFERRED' if a['preferred'] else 'not preferred'}" for c, a in m["arms"].items())
            print(f"   {e} ({b['cell']}): baseline {'within' if b['within'] else 'OVER'}, "
                  f"new {b['new']}, shared {b['shared']}; {arms}")
    m8 = o["m8"]["all"]
    print(f"8. Scope once the gate opens: {m8['misfires']} of {m8['gate_windows']} gate openings"
          + (f", {P(m8['share'], 1)} (exact 95% {P(m8['ci95'][0], 1)}-{P(m8['ci95'][1], 1)}), P = {m8['P']:.3f}, "
             f"{'consistent' if m8['consistent'] else 'NOT consistent'}" if m8["gate_windows"] else ""))
    for e in [e for e in o["m8"] if e != "all"]:
        m = o["m8"][e]
        print(f"   {e}: {m['misfires']} of {m['gate_windows']}")
    w = o["m9"]
    print(f"9. Weekly cycle: {w['weekend']['fires']} false alarms on {len(w['weekend']['days'])} weekend days, "
          f"{w['weekdays']['fires']} on {len(w['weekdays']['days'])} weekdays")
    if "m10" in o:
        m = o["m10"]
        print(f"10. Churn: windows holding an unseen fingerprint of k_min origins {P(m['windows_with_candidate_share'])}"
              + (f"; endpoints missing from the churn run: {m['missing_endpoints']}" if m["missing_endpoints"] else ""))
        for e, by in m["per_endpoint"].items():
            print(f"   {e}: new at k_min by day " + " ".join(str(v["new_fingerprints_kmin"]) for v in by.values()))


def check():
    """The same code on the paper's reduction, against the numbers the paper prints."""
    J = json.loads((RESULTS / "production_tables.json").read_text())
    C = json.loads((RESULTS / "ja4_churn.json").read_text())
    T, F = report(J, "test_days", C), report(J, "fresh_day", C)
    TD, FD = J["test_days"], J["fresh_day"]
    f2 = lambda v: f"{100 * v:.2f}"
    f1 = lambda v: f"{100 * v:.1f}"
    raw = lambda B, c, e=None: (B[CONFIGS[c][0]]["all"][CONFIGS[c][1]] if e is None
                                else B[CONFIGS[c][0]]["per_endpoint"][e][CONFIGS[c][1]])
    e24 = lambda B, c: f2(max(raw(B, c, e)["clean_rate"] for e in ("E2", "E3", "E4")))
    n, r = 15_800, REF_FA[0] / REF_FA[1]
    checks = [
        ("1: test days, 5 of 5,643 (0.03-0.21%)",
         (T["m1"]["fires"], T["m1"]["windows"], [f2(v) for v in T["m1"]["ci95"]]), (5, 5643, ["0.03", "0.21"])),
        ("1: held-out day, 2 of 1,152, P = 0.27, up to 3 would pass",
         (F["m1"]["fires"], F["m1"]["windows"], f"{F['m1']['P']:.2f}", F["m1"]["largest_consistent"]), (2, 1152, "0.27", 3)),
        ("protocol size: 15,800 windows expect 14.0 and fail from 21; a doubled rate reaches it 93% of the time",
         (f"{n * r:.1f}", largest_consistent(n, r) + 1, f"{tail(largest_consistent(n, r) + 1, n, 2 * r):.2f}"),
         ("14.0", 21, "0.93")),
        ("protocol size: 4,032 windows show a budget with up to 27 false alarms (0.67%)",
         (max(x for x in range(60) if interval(x, 4032)[1] <= BUDGET), f2(27 / 4032)), (27, "0.67")),
        ("8: test days, 5 of 168 gate openings; held-out day 2 of 3, P = 0.003",
         (T["m8"]["all"]["misfires"], T["m8"]["all"]["gate_windows"], F["m8"]["all"]["misfires"],
          F["m8"]["all"]["gate_windows"], f"{F['m8']['all']['P']:.3f}"), (5, 168, 2, 3, "0.003")),
        ("Table VI FA E1, test (configs 1, 4, 5, 3)",
         [f2(raw(TD, c, "E1")["clean_rate"]) for c in (1, 4, 5, 3)], ["0.00", "0.07", "0.97", "0.28"]),
        ("Table VI FA E1, held (configs 1, 4, 5, 3)",
         [f2(raw(FD, c, "E1")["clean_rate"]) for c in (1, 4, 5, 3)], ["0.00", "0.00", "0.00", "0.00"]),
        ("Table VI FA E2-E4 max, test and held (configs 1, 4, 3)",
         [e24(B, c) for c in (1, 4, 3) for B in (TD, FD)], ["0.28", "0.69", "0.21", "0.00", "0.42", "0.35"]),
        ("Table VI New, E1 tenth-size, test and held (configs 1, 4, 5, 3)",
         [f1(R["m3"][c]["E1"]["new:x0.1"]) for c in (1, 4, 5, 3) for R in (T, F)],
         ["11.8", "0.0", "20.4", "15.3", "89.6", "89.7", "89.6", "89.7"]),
        ("Table VI Shared, E1 tenth-size, test (configs 1, 4, 5, 3)",
         [f1(T["m3"][c]["E1"]["shared:x0.1"]) for c in (1, 4, 5, 3)], ["7.7", "15.1", "61.1", "0.0"]),
        ("Table VI Fl. 1k and Coll., pooled, test (configs 1, 4, 5, 3)",
         [f1(raw(TD, c)[k]) for c in (1, 4, 5, 3) for k in ("flash1000", "clean_collateral_median")],
         ["22.2", "32.9", "10.9", "16.9", "22.4", "32.6", "3.4", "5.7"]),
        ("Table IV held-out rows: base rule, binomial, z-score (FA, Coll., Fl. 1k, New 0.1x 1x, Shared 0.1x 1x)",
         [[f1(R[k]) for k in ("clean_rate", "clean_collateral_median", "flash1000")]
          + [f1(R[k]["blocked"]) for k in ("new:x0.1", "new:x1", "shared:x0.1", "shared:x1")]
          for R in (raw(FD, 2), raw(FD, 1), raw(FD, 6))],
         [["0.2", "41.2", "24.4", "0.0", "17.3", "0.0", "16.6"], ["0.2", "41.2", "24.5", "0.0", "20.4", "0.0", "17.0"],
          ["0.2", "41.2", "0.3", "0.0", "31.4", "0.0", "19.7"]]),
        ("Table IV test-day rows, in sample: binomial and z-score",
         [[f1(R[k]) for k in ("clean_rate", "clean_collateral_median", "flash1000")]
          + [f1(R[k]["blocked"]) for k in ("new:x0.1", "new:x1", "shared:x0.1", "shared:x1")]
          for R in (raw(TD, 1), raw(TD, 6))],
         [["0.1", "32.9", "22.2", "3.0", "19.9", "1.9", "17.6"], ["0.4", "10.8", "13.1", "3.1", "28.8", "2.3", "18.9"]]),
        ("4: crowds of 100 trigger the configuration in 4.6% (test) and 1.1% (held-out)",
         (f1(T["m4"][1]["all"]["flash100"]), f1(F["m4"][1]["all"]["flash100"])), ("4.6", "1.1")),
        ("5: misfires block a median 32.9%, an expected 0.03% per clean window",
         (f1(T["m5"][1]["all"]["collateral_median"]), f2(T["m5"][1]["all"]["expected_per_window"])), ("32.9", "0.03")),
        ("6: by day 1 0 1 1 2, 4 on the console; both held-out ones on the console",
         (list(raw(TD, 1)["clean_fires_by_fold"].values()), sum(T["m6"][1]["E2"].values()), sum(F["m6"][1]["E2"].values())),
         ([1, 0, 1, 1, 2], 4, 2)),
        ("9: 2026-09-20 is a Sunday: 1 false alarm on 1 weekend day, 4 on 4 weekdays",
         (T["m9"]["weekend"]["days"], T["m9"]["weekend"]["fires"], len(T["m9"]["weekdays"]["days"]), T["m9"]["weekdays"]["fires"]),
         (["2026-09-20"], 1, 4, 4)),
        ("7: the baseline stays within the budget on every endpoint, pooled over the test days",
         all(T["m7"]["as_written"][e]["baseline"]["within"] for e in T["m7"]["as_written"]), True),
        ("7, amended: arm 4 gains on shared stacks everywhere and on new ones on E2-E4, loses new ones on E1",
         (all(A[e]["arms"][4]["shared"] > A[e]["baseline"]["shared"] for e in A)
          and all(A[e]["arms"][4]["new"] > A[e]["baseline"]["new"] for e in ("E2", "E3", "E4"))
          and A["E1"]["arms"][4]["new"] < A["E1"]["baseline"]["new"]) if (A := T["m7"]["amended"]) else None, True),
        ("7, as written: a tenth of a point on E4's 2-attacker botnet makes arm 4 preferred there",
         (T["m7"]["as_written"]["E4"]["arms"][4]["new"], T["m7"]["as_written"]["E4"]["arms"][4]["preferred"],
          T["m7"]["amended"]["E4"]["arms"][4]["preferred"]), (0.1, True, True)),
        ("10: 0.21% of test-day windows hold an unseen fingerprint of k_min origins, all endpoints matched",
         (f2(T["m10"]["windows_with_candidate_share"]), T["m10"]["missing_endpoints"]), ("0.21", [])),
    ]
    bad = 0
    for label, got, want in checks:
        ok = got == want
        bad += not ok
        print(f"{'OK ' if ok else 'XX '} {label}" + ("" if ok else f": got {got}, want {want}"))
    print(f"{len(checks) - bad} OK, {bad} mismatches")
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tables", type=Path, help="production_tables.py output")
    ap.add_argument("--section", default="test_days", help="test_days (the block) or fresh_day")
    ap.add_argument("--churn", type=Path, default=None, help="ja4_churn.py output on the same days")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--check", action="store_true", help="check the code on the paper's numbers")
    args = ap.parse_args()
    if args.check:
        raise SystemExit(check() > 0)
    if args.tables is None:
        ap.error("--tables is required without --check")
    J = json.loads(args.tables.read_text())
    churn = json.loads(args.churn.read_text()) if args.churn else None
    o = report(J, args.section, churn)
    show(o)
    if args.out:
        args.out.write_text(json.dumps(o, indent=2))
        print(f"OK: {args.out}")


if __name__ == "__main__":
    main()
