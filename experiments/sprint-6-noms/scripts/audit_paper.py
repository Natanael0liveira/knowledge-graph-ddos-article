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
import numpy as np
import pandas as pd
HERE = Path(__file__).resolve().parents[1]
R = str(HERE / "results") + "/"
TEX = (HERE.parents[1] / "papers" / "http-session-noms" / "article.tex").read_text()
TEXN = re.sub(r"\s+", " ", TEX)          # prose, whitespace-insensitive
ok = bad = 0
def chk(label, paper, value, fmt):
    """paper: literal as printed; value: recomputed; fmt: how the paper rounds it."""
    global ok, bad
    got = fmt.format(value)
    intex = paper in TEXN
    good = (got == paper.replace("\\%", "").replace("$", "").strip()) and intex
    ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} {label:58s} paper={paper!r:16s} data={got:9s} {'' if intex else '<< not in tex'}")
pct = "{:.1f}"; pct2 = "{:.2f}"; f3 = "{:.3f}"

sym = json.load(open(R + "symbolic_detector.json"))["aggregate"]
print("== Table III (symbolic_detector.json)")
# the rows as printed in the table
rows = {"1.5:1:0": "Monolithic ($M{=}1$)", "1.5:5:0": "$M{=}5$ ", "1.5:25:0": "$M{=}25$ ",
        "1.5:100:0": "$M{=}100$", "1.5:25:1": "$M{=}25$, adversarial"}
for k, lab in rows.items():
    a = sym[k]; line = [l for l in TEX.splitlines() if l.startswith(lab) and "&" in l]
    nums = re.findall(r"\d+\.\d+", line[0].split("&", 1)[1]) if line else []
    exp = [f"{a['sym_recall']*100:.1f}", f"{a['sym_fpr']*100:.2f}", f"{a['sym_f1']:.3f}",
           f"{a['rf_recall_fpr0']*100:.1f}", f"{a['rfp_recall_fpr0']*100:.1f}"]
    good = nums == exp; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} Table III row {k:48s} printed={nums} data={exp}")
print("== Section V-B text")
chk("RF recall @1% FPR, M=25", "66.8", sym["1.5:25:0"]["rf_recall_fpr1"]*100, pct)
chk("RF AUC, M=25", "0.979", sym["1.5:25:0"]["rf_auc"], f3)
chk("RF + profile recall @FPR=0, M=25", "87.4", sym["1.5:25:0"]["rfp_recall_fpr0"]*100, pct)
chk("RF + profile recall @FPR=0, M=100", "86.9", sym["1.5:100:0"]["rfp_recall_fpr0"]*100, pct)
chk("RF recall @1% FPR, M=25 adversarial", "23.4", sym["1.5:25:1"]["rf_recall_fpr1"]*100, pct)
# "the rule matches it up to 25 stacks": within two points of the profile-aware model
gap = max(sym[k]["rfp_recall_fpr0"] - sym[k]["sym_recall"] for k in ("1.5:1:0", "1.5:5:0", "1.5:25:0"))
good = gap < 0.02 and sym["1.5:25:0"]["sym_recall"] >= sym["1.5:25:0"]["rfp_recall_fpr0"]
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} rule matches the profile-aware model up to M=25 (largest shortfall {gap*100:.1f} pts)")

print("== Fig. 3 and Section V-D (realistic_final_consolidated.csv)")
c = pd.read_csv(R + "realistic_final_consolidated.csv").set_index(["alpha", "stacks", "adv"])
g = lambda a, m, v, col: float(c.loc[(a, m, v), col]) * 100
chk("monolithic blocked (both rules)", "89.8", g(1.5, 1, 0, "enr_cov"), pct)
chk("monolithic blocked, frequency rule", "89.8", g(1.5, 1, 0, "modal_cov"), pct)
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
    print(f"{'OK ' if good else 'XX '} Table V {kind:14s} printed={printed} data={exp} (windows in csv {len(x)})")
chk("Omega-only clean false alarms", "0.6", r["clean"]["omega"]*100, pct)
cal = W[(W.kind == "calib") & (W["size"] >= 5)]; to = cal["size"].quantile(0.99)
gate = {}
for kind in ("attack_K1000", "attack_K50", "clean", "flash_25", "flash_50", "flash_100"):
    x, _ = fired(kind); gate[kind] = ((x["size"] >= to).mean(), ((x["size"] >= to) & x.scope_named).mean())
chk("origin gate, K=1000 (App. E)", "82.2", gate["attack_K1000"][0]*100, pct)
chk("origin gate, K=50 (App. E)", "85.7", gate["attack_K50"][0]*100, pct)
good = all(gate[k][1] == 0 for k in ("clean", "flash_25", "flash_50", "flash_100")) and \
    all(gate[k][1] == gate[k][0] for k in ("attack_K1000", "attack_K50"))
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} origin gate with the test: no clean window or flash crowd, detection kept")
print(f"    tau = {r['tau']:.1f}, calibration windows = {J['calibration_windows']}, profile = {J['config']['profile']}, significance = {J['config']['significance']}")
print("== fixed floor in the same setting (rule_detection_windows_steady60_rate0_bigprof.csv)")
V = pd.read_csv(R + "rule_detection_windows_steady60_rate0_bigprof.csv")
for kind in ["clean", "flash_25", "flash_50", "flash_100"]:
    x = V[(V.kind == kind) & (V["size"] >= 5)]
    print(f"    {kind:10s} scope named {x.scope_named.mean()*100:5.1f}%  median collateral {x[x.scope_named].scope_collateral.median()*100:4.1f}%")

print("== production traffic (production_summary.json)")
P = json.load(open(R + "production_summary.json")); E = P["endpoints"]; V = P["variants"]
m, a = V["origin_calibrated"], V["origin_calibrated_all"]
fmt = lambda v: "--" if v is None else f"{v*100:.1f}"
def row(label, cells, nth=0):
    """A Table VI row as printed against the summary (-- where the rule never fired);
    ``nth`` picks among rows that share a label (one per gate)."""
    global ok, bad
    line = [l for l in TEX.splitlines() if l.strip().startswith(label) and "&" in l]
    printed = re.findall(r"\d+\.\d|--", line[nth].split("&", 2)[2]) if len(line) > nth else []
    exp = [fmt(c) for c in cells]
    good = printed == exp; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} Table VI {label:22s}#{nth} printed={printed} data={exp}")
rel = lambda d, src, f: d["attack_relative_M25"][f"{src}:M25:x{f}"]
for e, lab in [("E1", "E1, RUM beacons"), ("E2", "E2, web console"), ("E3", "E3, API"), ("E4", "E4, SSO")]:
    c, at = E[e]["clean"], E[e]["attack_fresh_M25"]
    row(lab, [c["pipeline"], c.get("collateral_pipeline_median"), E[e]["flash"]["100"]["pipeline"],
              at["100"]["blocked_pipeline"], at["1000"]["blocked_pipeline"],
              rel(E[e], "fresh", 1)["blocked_pipeline"]])
c, fr, sh, fl = a["clean"], a["attack_fresh_M25"], a["attack_tail_M25"], a["flash"]["100"]
for lab, nth, cf, cc, b in (
        ("Enrichment", 0, "pipeline", "collateral_pipeline_median", "blocked_pipeline"),
        ("$z$-score", 0, "zscore_pipeline", "zscore_collateral_median", "zscore_blocked"),
        ("Unseen JA4", 0, "unseen_pipeline", "unseen_collateral_median", "unseen_blocked"),
        ("Enrich.\\ $\\cup$ unseen", 0, "union_pipeline", "union_collateral_median", "union_blocked"),
        ("Enrichment", 1, "origins_enrichment_pipeline", "origins_enrichment_collateral_median",
         "origins_enrichment_blocked"),
        ("Enrich.\\ $\\cup$ unseen", 1, "origins_union_pipeline", "origins_union_collateral_median",
         "origins_union_blocked")):
    row(lab, [c[cf], c[cc], fl[cf], fr["100"][b], sh["100"][b], fr["1000"][b], sh["1000"][b],
              rel(a, "fresh", 1)[b], rel(a, "tail", 1)[b]], nth)
n_clean = f"{a['clean']['windows']:,}".replace(",", "\\,")
good = n_clean == "5\\,643" and (n_clean + " attack-free") in TEX; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} clean windows in Table VI: {n_clean}")
chk("scope per connection, nominal level (V-B)", "60.1", V["session_nominal"]["clean"]["enrichment"]*100, pct)
chk("scope per origin, nominal level (V-B)", "26.9", V["origin_nominal"]["clean"]["enrichment"]*100, pct)
chk("rule per origin, calibrated (abstract, V-B)", "0.2", m["clean"]["pipeline"]*100, pct)
v = c["collateral_pipeline_median"]; good = 0.4 <= v <= 0.6 and "blocking about half of that window's clients" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: false alarms block 'about half' of clients: {v:.3f}")
chk("abstract: test fires on flash crowds of 100", "$4\\%$ of flash crowds", fl["pipeline"]*100, "{:.0f} of flash crowds")
chk("abstract: z-score fires on flash crowds of 100", "against $65\\%$", fl["zscore_pipeline"]*100, "against {:.0f}")
chk("abstract: origin gate + union, clean", "fires on $0.1\\%$ of clean", c["origins_union_pipeline"]*100, "fires on {:.1f} of clean")
chk("abstract: origin gate + union, collateral", "median $30\\%$ of their clients", c["origins_union_collateral_median"]*100, "median {:.0f} of their clients")
chk("V-B: flash crowds of 100, enrichment", "3.9", fl["pipeline"]*100, pct)
chk("V-B: flash crowds of 100, z-score", "64.5", fl["zscore_pipeline"]*100, pct)
chk("V-B: origin gate + union, 100 new", "38.4", fr["100"]["origins_union_blocked"]*100, pct)
chk("V-B: origin gate + union, 1,000 new", "77.7", fr["1000"]["origins_union_blocked"]*100, pct)
chk("V-B: origin gate + union, collateral", "29.9", c["origins_union_collateral_median"]*100, pct)
cells = [x for sec in ("attack_fresh_M25", "attack_tail_M25", "attack_relative_M25") for x in a[sec].values()]
good = (c["origins_enrichment_pipeline"] <= 0.55 * c["pipeline"]
        and all(x["origins_enrichment_blocked"] >= x["blocked_pipeline"] for x in cells)
        and "halves the false alarms with no loss of detection" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: origin gate halves false alarms ({c['origins_enrichment_pipeline']*100:.2f} vs "
      f"{c['pipeline']*100:.2f}%), no loss in any of {len(cells)} attack cells")
vb = P["volume_baseline"]; lo, hi = vb["agreement_range"]
good = f"${lo*100:.0f}$--${hi*100:.1f}\\%$" in TEX; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: Omega vs origin threshold agree {lo*100:.1f}--{hi*100:.1f}%")
more = all(x["origins"] >= x["omega"] for x in list(vb["attack_fresh_M25"].values()) + list(vb["attack_relative_M25"].values()))
ok += more; bad += not more; print(f"{'OK ' if more else 'XX '} V-B: the origin threshold catches at least as many attacks")
chk("V-B: shared stacks blocked at 100", "20.2", sh["100"]["blocked_pipeline"]*100, pct)
chk("V-B: shared stacks blocked at 1,000", "61.6", sh["1000"]["blocked_pipeline"]*100, pct)
v = sh["100"]["unseen_blocked"] + sh["1000"]["unseen_blocked"]; good = v == 0; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: unseen filter blocks no shared stack: {v}")
v = sh["100"]["zscore_blocked"] > sh["100"]["blocked_pipeline"] and sh["1000"]["zscore_blocked"] > sh["1000"]["blocked_pipeline"]
ok += v; bad += not v; print(f"{'OK ' if v else 'XX '} V-B: z-score blocks more with shared stacks")
vb = P["volume_baseline"]
good = vb["clean_omega_only"]["windows"] == 13 and vb["clean_omega_only"]["scope_named"] == 8 and \
    "the eight clean windows that only $\\Omega$ admits" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: eight clean windows only Omega admits, scope firing: {vb['clean_omega_only']}")
chk("App. E: their share of Omega outside the endpoint term", "$33\\%$ of their", vb["clean_omega_only"]["non_endpoint_share_median"]*100, "{:.0f} of their")
elsew = [vb["clean_origins_only"]["non_endpoint_share_median"], vb["clean_both"]["non_endpoint_share_median"]]
good = all(round(x*100) in (11, 12) for x in elsew) and "against $12\\%$ elsewhere" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: 12% elsewhere: {[round(x*100,1) for x in elsew]}")
sc = sorted(E[e]["clean"]["enrichment"] * 100 for e in E)
good = f"${sc[0]:.1f}$--${sc[-1]:.1f}\\%$" in TEX; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: scope alone out of sample {sc[0]:.1f}--{sc[-1]:.1f}%")
mx = max(fr[A]["collateral_pipeline_max"] for A in fr); chk("App. E: attack-window collateral up to", "70", mx*100, "{:.0f}")
e1 = E["E1"]["attack_fresh_M25"]["1000"]; e4 = rel(E["E4"], "fresh", 1)
good = e1["enrichment"] >= 0.5 > e1["omega"] and e4["enrichment"] >= 0.5 > e4["omega"]; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: on E1 at 1,000 and E4 at 1x the scope names stacks but Omega < tau "
      f"(E1 {e1['enrichment']:.2f}/{e1['omega']:.2f}, E4 {e4['enrichment']:.2f}/{e4['omega']:.2f})")
good = all(rel(E[e], "fresh", 1)["blocked_enrichment" if "blocked_enrichment" in rel(E[e], "fresh", 1) else "blocked_pipeline"] < 0.05 for e in ("E2", "E3"))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: on E2 and E3 the stacks of a 1x botnet are not certified")
chk("App. E: E1 at 1,000, Omega below tau", "$57\\%$", (1 - e1["omega"])*100, "{:.0f}")
chk("App. E: E4 at 1x, Omega below tau", "$94\\%$ of them", (1 - e4["omega"])*100, "{:.0f} of them")
big = [e for e in E if E[e]["origins_per_window"] == "> 1,000"]
good = big == ["E1"] and all(E[e]["origins_per_window"] in ("< 10", "10-100") for e in E if e != "E1")
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: at 0.1x only E1 holds more than 100 attackers")
t1 = rel(E["E1"], "fresh", 0.1); t1s = rel(E["E1"], "tail", 0.1)
chk("App. E: E1 at 0.1x, enrichment", "0.6", t1["blocked_pipeline"]*100, pct)
chk("App. E: E1 at 0.1x, unseen", "11.2", t1["unseen_blocked"]*100, pct)
chk("App. E: E1 at 0.1x, z-score", "12.5", t1["zscore_blocked"]*100, pct)
chk("App. E: E1 z-score false alarms", "5.1", E["E1"]["clean"]["zscore_pipeline"]*100, pct)
good = abs(t1["union_blocked"] - t1["unseen_blocked"]) < 5e-4; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: E1 at 0.1x the union recovers the unseen share ({t1['union_blocked']*100:.1f})")
good = max(t1s["blocked_pipeline"], t1s["unseen_blocked"], t1s["union_blocked"]) < 0.005; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: E1 at 0.1x shared stacks: only the z-score stops any")
chk("App. E: E1 at 0.1x shared stacks, z-score", "12.2", t1s["zscore_blocked"]*100, pct)
# rho sensitivity: every pooled entry of Table VI that depends on rho
dep = [("pipeline", "collateral_pipeline_median", "blocked_pipeline"),
       ("union_pipeline", "union_collateral_median", "union_blocked"),
       ("origins_enrichment_pipeline", "origins_enrichment_collateral_median", "origins_enrichment_blocked"),
       ("origins_union_pipeline", "origins_union_collateral_median", "origins_union_blocked")]
def entries(v):
    out = []
    for cf, cc, b in dep:
        out += [v["clean"][cf], v["clean"][cc], v["flash"]["100"][cf]]
        for src in ("fresh", "tail"):
            out += [v[f"attack_{src}_M25"]["100"][b], v[f"attack_{src}_M25"]["1000"][b],
                    v["attack_relative_M25"][f"{src}:M25:x1"][b]]
    return out
def kinds(v):
    fire, coll, blk = [], [], []
    for cf, cc, b in dep:
        fire += [v["clean"][cf], v["flash"]["100"][cf]]; coll.append(v["clean"][cc])
        for src in ("fresh", "tail"):
            blk += [v[f"attack_{src}_M25"]["100"][b], v[f"attack_{src}_M25"]["1000"][b],
                    v["attack_relative_M25"][f"{src}:M25:x1"][b]]
    return fire, coll, blk
moves = [max(abs(x - y) for r in ("rho2", "rho5") for x, y in zip(kinds(V[r])[i], kinds(a)[i])) for i in range(3)]
chk("App. E: rho moves no firing rate by more than", "$0.3$ points", moves[0]*100, "{:.1f} points")
chk("App. E: rho moves no blocked share by more than", "more than $4.5$", moves[2]*100, "more than {:.1f}")
chk("App. E: rho moves a collateral median by up to", "up to $7.2$", moves[1]*100, "up to {:.1f}")
chk("abstract: origin gate + union, new stacks, low end", "$38$--$78\\%$", fr["100"]["origins_union_blocked"]*100, "{:.0f}--78")
chk("abstract: origin gate + union, new stacks, high end", "$38$--$78\\%$", fr["1000"]["origins_union_blocked"]*100, "38--{:.0f}")
chk("abstract: origin gate + union, shared stacks, low end", "$20$--$62\\%$", sh["100"]["origins_union_blocked"]*100, "{:.0f}--62")
chk("abstract: origin gate + union, shared stacks, high end", "$20$--$62\\%$", sh["1000"]["origins_union_blocked"]*100, "20--{:.0f}")
n_org, n_om = round(c["origins_enrichment_pipeline"] * c["windows"]), round(c["pipeline"] * c["windows"])
good = f"({n_org} against {n_om} clean windows)" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: origin gate {n_org} against {n_om} clean false alarms")
chk("VI: E1 at 0.1x, enrichment", "enrichment to $0.6\\%$", t1["blocked_pipeline"]*100, "enrichment to {:.1f}")
chk("App. E: flash crowds of 1,000, z-score", "86.8", a["flash"]["1000"]["zscore_pipeline"]*100, pct)
fps = [x for e in E for x in E[e]["profile_fingerprints"]]
good = f"${min(fps)}$--${max(fps)}$" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. B: production endpoints show {min(fps)}--{max(fps)} fingerprints")
chk("flash crowd of 100, rule", "3.9", a["flash"]["100"]["pipeline"]*100, pct)
chk("flash crowd of 1,000, rule", "21.8", a["flash"]["1000"]["pipeline"]*100, pct)
chk("WAF agreement on E3", "84", E["E3"]["waf_matched_share"]*100, "{:.0f}")
chk("WAF agreement on E4", "96", E["E4"]["waf_matched_share"]*100, "{:.0f}")
chk("WAF agreement on E2", "1.5", E["E2"]["waf_matched_share"]*100, pct)
good = not E["E1"]["waf_matched_share"] and "E1 has no WAF activity" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} E1 has no WAF activity")
import math
for e, exp in (("E4", "-4"), ("E3", "-14"), ("E1", "-60"), ("E2", "-73")):
    got = str(round(math.log10(E[e]["scope_level_median"]))); good = got == exp and f"10^{{{exp}}}$ ({e})" in TEXN
    ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} level of {e} about 10^{exp}: data 10^{got}")
good = P["self_check"]["mismatches"] == 0; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} production scope self-check: {P['self_check']}")
print("== weight ablation (rule_detection_*_w*.json)")
wa = lambda t: json.load(open(R + f"rule_detection_steady60_rate0_bigprof_binom{t}.json"))["by_percentile"]["99.0"]
chk("uniform weights, K=1000", "78.9", wa("_wuniform")["attack_K1000"]["omega"]*100, pct)
chk("uniform weights, K=50 (as default)", "85.7", wa("_wuniform")["attack_K50"]["omega"]*100, pct)
chk("no endpoint term, K=1000", "33.3", wa("_wnoep")["attack_K1000"]["omega"]*100, pct)
v = wa("_wnoep")["attack_K50"]["omega"]; good = v == 0; ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} no endpoint term, K=50 catches none: {v}")
fl = [wa("_wnoep")[f"flash_{n}"]["omega"]*100 for n in (25, 50, 100)]
good = f"{min(fl):.0f}" == "53" and f"{max(fl):.0f}" == "100" and "$53$--$100\\%$ of flash crowds" in TEX
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} no endpoint term, flash crowds {min(fl):.1f}--{max(fl):.1f}%")
print("== what the graph adds (compile_check.json, stix_validation.json)")
cc = json.load(open(R + "compile_check.json"))
good = cc["ok"] and cc["omega_max_abs_diff"] == 0 and "the compiled SQL reproduces $\\Omega$ exactly" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} compiled query reproduces Omega exactly on {cc['windows_x_endpoints']} "
      f"window-endpoints ({cc['sessions']} sessions): max diff {cc['omega_max_abs_diff']}")
x = cc["extension"]
good = (x["triples_added"] == 4 and x["code_lines_changed"] == 0 and x["omega_max_abs_diff"] == 0
        and x["relation"] in x["compiled_classes"] and "as four triples" in TEXN
        and "with no change to any code" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} a new signal costs {x['triples_added']} triples and {x['code_lines_changed']} lines of code")
cp = json.load(open(R + "compile_production_check.json"))
good = (cp["origins_equal"] == cp["net24_pairs_equal"] == cp["windows"]
        and f"in all {cp['windows']:,} windows of a day".replace(",", "\\,") in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} compiled query in the operator's store: origins and /24 pairs equal the export "
      f"in {cp['origins_equal']}/{cp['windows']} windows")
sv = json.load(open(R + "stix_validation.json"))
good = (sv["ok"] and sv["errors"] == 0 and sv["warnings"] == 0 and sv["strict_errors"] == 0
        and all(c["valid_strict"] for c in sv["chains"]) and "validator accepts in strict mode" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} {sv['bundles']} STIX bundles valid, strict included "
      f"({sv['errors']} errors, {sv['warnings']} warnings, {sv['strict_errors']} strict errors)")
print("== known-fleet profile (fleet_profile.json)")
fp = json.load(open(R + "fleet_profile.json"))
sh = float(fp["chosen_share"])
good = (fp["protocol"]["design_days"] == 3 and fp["protocol"]["held_out_days"] == 2
        and f"${sh*100:.0f}\\%$ of an endpoint's calibration" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} share chosen on 3 design days: {sh}, eligible {fp['eligible']}")
d0 = fp["design"]; good = all(d0[s]["false_alarms"] > d0["base"]["false_alarms"] for s in d0 if s not in ("base", fp["chosen_share"]))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} every other share adds false alarms on design days")
fe = fp["fleets_per_endpoint"]["E1"]
good = sorted(set(fe["fleets"])) == [5, 6] and "five or six of them" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} E1 known fleets per fold: {fe['fleets']}")
chk("E1 fleets' share of the profile", "$7\\%$ of the profile", float(np.median(fe["profile_share"]))*100, "{:.0f} of the profile")
lv = round(math.log10(float(np.median(fe["level"]))))
good = f"$10^{{-60}}$ to $10^{{{lv}}}$" in TEXN and round(math.log10(E["E1"]["scope_level_median"])) == -60
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} E1 level rises from 10^-60 to 10^{lv}")
hb, hf = fp["held_out_per_endpoint"]["E1"]["base"], fp["held_out_per_endpoint"]["E1"]["fleets"]
chk("held out: E1 0.1x new stacks, base", "from $0.7\\%$ to $6.3\\%$", hb["fresh:x0.1"]*100, "from {:.1f} to 6.3")
chk("held out: E1 0.1x new stacks, fleets", "from $0.7\\%$ to $6.3\\%$", hf["fresh:x0.1"]*100, "from 0.7 to {:.1f}")
chk("held out: E1 0.1x shared stacks, base", "($0.2\\%$ to $4.4\\%$", hb["tail:x0.1"]*100, "({:.1f} to 4.4")
chk("held out: E1 0.1x shared stacks, fleets", "($0.2\\%$ to $4.4\\%$", hf["tail:x0.1"]*100, "(0.2 to {:.1f}")
ho = fp["held_out"]
good = f"at {ho['fleets']['false_alarms']} false alarms against {ho['base']['false_alarms']}" in TEXN \
    and ho["fleets"]["false_alarms"] <= ho["base"]["false_alarms"]
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held out: {ho['fleets']['false_alarms']} false alarms against {ho['base']['false_alarms']}")
sec = {k: v for k, v in fp["held_out_secondary_all_shares"].items() if k != fp["chosen_share"]}
c0 = fp["held_out_secondary_all_shares"][fp["chosen_share"]]
good = all(v["false_alarms"] >= 1.8 * c0["false_alarms"] and v["collateral_median"] < c0["collateral_median"]
           and v["flash100"] > c0["flash100"] and v["mean_blocked"] > c0["mean_blocked"] for v in sec.values()) \
    and "fire twice as often, on lighter filters and on more flash crowds" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} held out, smaller shares: more blocked, ~2x false alarms, lighter, more flash crowds")
print(f"\nTOTAL: {ok} OK, {bad} mismatches")
sys.exit(1 if bad else 0)
