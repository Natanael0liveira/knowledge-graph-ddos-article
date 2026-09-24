#!/usr/bin/env python3
"""Sprint 6 (NOMS) — audit the paper's numbers against the result files.

Every number of Table III, Fig. 3, Section V-B/V-D and Appendix E that comes from
this sprint is recomputed from the JSON/CSV that produced it and compared with the
literal text of papers/http-session-noms/article.tex. Table rows are parsed as
printed. Exit status 1 on any mismatch.

Usage:  python audit_paper.py          (from experiments/sprint-6-noms)
"""
import json, re, sys
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parents[1]
R = str(HERE / "results") + "/"
TEX = (HERE.parents[1] / "papers" / "http-session-noms" / "article.tex").read_text()
ok = bad = 0
def chk(label, paper, value, fmt):
    """paper: literal as printed; value: recomputed; fmt: how the paper rounds it."""
    global ok, bad
    got = fmt.format(value)
    intex = paper in TEX
    good = (got == paper.replace("\\%", "").replace("$", "").strip()) and intex
    ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} {label:58s} paper={paper!r:16s} data={got:9s} {'' if intex else '<< not in tex'}")
pct = "{:.1f}"; pct2 = "{:.2f}"; f3 = "{:.3f}"

sym = json.load(open(R + "symbolic_detector.json"))["aggregate"]
print("== Table III (symbolic_detector.json)")
# the rows as printed in the table
rows = {"1.5:1:0": r"Monolithic ($M{=}1$)  & 84.0\% & 0.00\% & 0.885 & 0.997 & 91.7\% \\",
        "1.5:5:0": r"$M{=}5$               & 90.0\% & 0.00\% & 0.948 & 0.996 & 88.6\% \\",
        "1.5:25:0": r"$M{=}25$              & 90.3\% & 0.00\% & \textbf{0.949} & 0.979 & \textbf{36.4\%} \\",
        "1.5:100:0": r"$M{=}100$             & 38.6\% & 0.00\% & 0.556 & 0.961 & \textbf{17.6\%} \\",
        "1.5:25:1": r"$M{=}25$, adversarial & 30.4\% & 3.78\% & 0.452 & 0.862 & 7.8\% \\"}
for k, row in rows.items():
    a = sym[k]; nums = re.findall(r"\d+\.\d+", row.split("&", 1)[1])
    exp = [f"{a['sym_recall']*100:.1f}", f"{a['sym_fpr']*100:.2f}", f"{a['sym_f1']:.3f}", f"{a['rf_auc']:.3f}", f"{a['rf_recall_fpr0']*100:.1f}"]
    good = nums == exp and row in TEX; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} Table III row {k:48s} printed={nums} data={exp}")
print("== Section V-B text")
chk("RF recall @1% FPR, M=25", "66.8", sym["1.5:25:0"]["rf_recall_fpr1"]*100, pct)
chk("RF recall @1% FPR, M=100", "44.5", sym["1.5:100:0"]["rf_recall_fpr1"]*100, pct)
chk("RF recall @1% FPR, M=25 adversarial", "23.4", sym["1.5:25:1"]["rf_recall_fpr1"]*100, pct)
r25 = sym["1.5:25:0"]["sym_recall"]/sym["1.5:25:0"]["rf_recall_fpr0"]; r100 = sym["1.5:100:0"]["sym_recall"]/sym["1.5:100:0"]["rf_recall_fpr0"]
print(f"{'OK ' if min(r25,r100)>2 else 'XX '} 'more than twice' / 'doubles': ratios M=25 {r25:.2f}, M=100 {r100:.2f}"); ok += min(r25,r100)>2

print("== Fig. 3 and Section V-D (realistic_final_consolidated.csv)")
c = pd.read_csv(R + "realistic_final_consolidated.csv").set_index(["alpha", "stacks", "adv"])
g = lambda a, m, v, col: float(c.loc[(a, m, v), col]) * 100
chk("monolithic blocked (both rules)", "84.0", g(1.5, 1, 0, "enr_cov"), pct)
chk("modal inverts: attack blocked M=5", "0.0", g(1.5, 5, 0, "modal_cov"), pct)
chk("modal inverts: legitimate hit M=5", "39.0", g(1.5, 5, 0, "modal_coll"), pct)
chk("modal collateral at alpha=2.0", "61.1", g(2.0, 25, 0, "modal_coll"), pct)
chk("enrichment M=5", "90.0", g(1.5, 5, 0, "enr_cov"), pct)
chk("enrichment M=25", "90.3", g(1.5, 25, 0, "enr_cov"), pct)
chk("enrichment M=100", "38.6", g(1.5, 100, 0, "enr_cov"), pct)
for m in (5, 25, 100):
    v = g(1.5, m, 0, "enr_coll"); good = v == 0; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} enrichment collateral M={m} is zero: {v}")
chk("adversarial enrichment blocked", "30.4", g(1.5, 25, 1, "enr_cov"), pct)
chk("adversarial enrichment collateral", "3.78", g(1.5, 25, 1, "enr_coll"), pct2)
chk("adversarial frequency rule blocked", "3.6", g(1.5, 25, 1, "modal_cov"), pct)
print("== cross-check: Table III and Fig. 3 come from two scripts; enrichment must agree")
for key, (a, m, v) in {"1.5:1:0": (1.5, 1, 0), "1.5:5:0": (1.5, 5, 0), "1.5:25:0": (1.5, 25, 0), "1.5:100:0": (1.5, 100, 0), "1.5:25:1": (1.5, 25, 1)}.items():
    d1, d2 = sym[key]["sym_recall"]*100, g(a, m, v, "enr_cov"); good = abs(d1-d2) < 0.05; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} {key}: symbolic_detector {d1:.2f} vs realistic_probe {d2:.2f}")

print("== drift (profile_drift.json, profile_drift_m100.json)")
dr = json.load(open(R + "profile_drift.json"))["aggregate"]; dm = json.load(open(R + "profile_drift_m100.json"))["aggregate"]
chk("drifted profile coverage", "90.3", dr["drifted"]["coverage"]*100, pct)
v = dr["drifted"]["collateral"]; good = v == 0; ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} drifted profile collateral is zero: {v}")
chk("flat profile collateral", "77.6", dr["flat"]["collateral"]*100, pct)
chk("M=100 pooled profile coverage", "89.6", dm["pooled"]["coverage"]*100, pct)
v = dm["pooled"]["collateral"]; good = v == 0; ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} M=100 pooled collateral is zero: {v}")
chk("M=100 1k profile (same as Table III)", "38.6", dm["matched"]["coverage"]*100, pct)

print("== per window (rule_detection_steady60_rate0_bigprof_binom)")
J = json.load(open(R + "rule_detection_steady60_rate0_bigprof_binom.json")); r = J["by_percentile"]["99.0"]
W = pd.read_csv(R + "rule_detection_windows_steady60_rate0_bigprof_binom.csv")
def fired(kind):
    x = W[(W.kind == kind) & (W["size"] >= 5)]
    if kind.startswith("attack"): x = x[x.n_attack >= 5]
    return x, x[(x.omega >= r["tau"]) & x.scope_named]
for kind, lab, n in [("attack_K1000", "Attack, $K = 1000$", 90), ("attack_K50", "Attack, $K = 50$", 35), ("clean", "Clean", 360),
                     ("flash_25", "Flash crowd, 25", 30), ("flash_50", "Flash crowd, 50", 30), ("flash_100", "Flash crowd, 100", 30)]:
    x, f = fired(kind); rr = r[kind]
    cells = [str(rr["windows"]), f"{rr['omega']*100:.1f}", f"{rr['pipeline']*100:.1f}"]
    if kind.startswith("attack"):
        cells += [f"{f.scope_recall.median()*100:.1f}", f"{f.scope_collateral.max()*100:.1f}"]
    line = [l for l in TEX.splitlines() if l.startswith(lab)]
    printed = re.findall(r"\d+(?:\.\d+)?", line[0].split("&", 1)[1]) if line else []
    exp = [c.replace("100.0", "100") for c in cells]
    good = printed == exp and rr["windows"] == n and len(x) == n; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} Table VI {kind:13s} printed={printed} data={exp} (windows in csv {len(x)})")
chk("Omega-only clean false alarms", "0.6", r["clean"]["omega"]*100, pct)
print(f"    tau = {r['tau']:.1f}, calibration windows = {J['calibration_windows']}, profile = {J['config']['profile']}, significance = {J['config']['significance']}")
print("== fixed floor in the same setting (rule_detection_windows_steady60_rate0_bigprof.csv)")
V = pd.read_csv(R + "rule_detection_windows_steady60_rate0_bigprof.csv")
for kind in ["clean", "flash_25", "flash_50", "flash_100"]:
    x = V[(V.kind == kind) & (V["size"] >= 5)]
    print(f"    {kind:10s} scope named {x.scope_named.mean()*100:5.1f}%  median collateral {x[x.scope_named].scope_collateral.median()*100:4.1f}%")

print("== per window with the 1,000-session profile (rule_detection_steady60_rate0_binom)")
J1 = json.load(open(R + "rule_detection_steady60_rate0_binom.json")); r1 = J1["by_percentile"]["99.0"]
W1 = pd.read_csv(R + "rule_detection_windows_steady60_rate0_binom.csv")
def fired1(kind):
    x = W1[(W1.kind == kind) & (W1["size"] >= 5)]
    if kind.startswith("attack"): x = x[x.n_attack >= 5]
    return x, x[(x.omega >= r1["tau"]) & x.scope_named]
chk("1k: rule acts on attack windows, low end (K=1000)", "69", r1["attack_K1000"]["pipeline"]*100, "{:.0f}")
chk("1k: rule acts on attack windows, high end (K=50)", "80", r1["attack_K50"]["pipeline"]*100, "{:.0f}")
v = r1["clean"]["pipeline"]; good = v == 0; ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} 1k: rule on clean windows is zero: {v}")
_, fa = fired1("attack_K1000"); _, fb = fired1("attack_K50")
chk("1k: median attackers blocked, low end (K=50)", "20", fb.scope_recall.median()*100, "{:.0f}")
chk("1k: median attackers blocked, high end (K=1000)", "55", fa.scope_recall.median()*100, "{:.0f}")
v = max(fa.scope_collateral.max(), fb.scope_collateral.max()); good = v == 0; ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} 1k: no collateral in attack windows: {v}")
fl = sum(len(fired1(k)[1]) for k in ("flash_25", "flash_50", "flash_100")); good = fl == 1; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} 1k: flash crowds with a filter = {fl} of 90")
chk("1k: users hit in that flash crowd", "11.7", max(fired1(k)[1].scope_collateral.max() if len(fired1(k)[1]) else 0 for k in ("flash_25","flash_50","flash_100"))*100, pct)
print(f"\nTOTAL: {ok} OK, {bad} mismatches")
sys.exit(1 if bad else 0)
