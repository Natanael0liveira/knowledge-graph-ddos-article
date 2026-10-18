#!/usr/bin/env python3
"""Sprint 6 (NOMS): audit the paper's numbers against the result files.

Every number of Sections V-A to V-D, Appendices C to E, the conclusion and the
abstract that comes from this sprint is recomputed from the JSON/CSV that produced
it and compared with the literal text of papers/http-session-noms/article.tex.
Tables are named by their LaTeX labels (tab:symbolic, tab:production, tab:floor,
tab:perwindow), since their numbers shift, and their rows are parsed as printed.
Exit status 1 on any mismatch.

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
    """paper: literal as printed; value: recomputed (a tuple for several); fmt: how the paper rounds it."""
    global ok, bad
    got = fmt.format(*value) if isinstance(value, tuple) else fmt.format(value)
    intex = paper in TEXN
    good = (got == paper.replace("\\%", "").replace("$", "").strip()) and intex
    ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} {label:58s} paper={paper!r:16s} data={got:9s} {'' if intex else '<< not in tex'}")
pct = "{:.1f}"; pct2 = "{:.2f}"; f3 = "{:.3f}"

print("== Section V-A: ablation (canonical_realistic.json, canonical_baselines.json)")
CR = json.load(open(R + "canonical_realistic.json")); CA = CR["aggregate"]; CT = CR["tests"]
CFG = {"a": "a_ml_sem_ontologia", "b": "b_ontologia_sem_related", "c": "c_so_network_proximity", "d": "d_completo"}
au = lambda K, fam, cf: CA[f"K={K}"][f"{fam}|{CFG[cf]}"]["mean"]
good = CR["alpha"] == 1.5 and CR["stacks"] == 25 and CR["seeds"] == 30 and "($\\alpha = 1.5$, $M = 25$, 30 seeds)" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-A: alpha {CR['alpha']}, M = {CR['stacks']}, n = {CR['seeds']} seeds")
chk("V-A: (a), K = 50 and 1000", "ROC AUC of $0.498$ and $0.503$", (au(50, "rf", "a"), au(1000, "rf", "a")), "ROC AUC of {:.3f} and {:.3f}")
chk("V-A: (b)", "(b) $0.500$ and $0.502$", (au(50, "rf", "b"), au(1000, "rf", "b")), "(b) {:.3f} and {:.3f}")
CB = json.load(open(R + "canonical_baselines.json"))["aggregate"]
ac = [CB[f"K={K}"][b]["mean"] for K in (50, 1000) for b in ("fernandes2015", "bharathi2012_pca", "kemp2023")]
chk("V-A: the three academic baselines", "baselines $0.495$--$0.518$", (min(ac), max(ac)), "baselines {:.3f}--{:.3f}")
fa = [au(K, f, "a") for K in (50, 1000) for f in CR["families"]]
chk("V-A: (a) under every classifier family", "(a) stays at $0.488$--$0.503$ under every classifier family", (min(fa), max(fa)),
    "(a) stays at {:.3f}--{:.3f} under every classifier family")
chk("V-A: (d)", "(d) reaches $0.927$ and $0.982$", (au(50, "rf", "d"), au(1000, "rf", "d")), "(d) reaches {:.3f} and {:.3f}")
chk("V-A: (c)", "(c) reaches $0.499$ and $0.659$", (au(50, "rf", "c"), au(1000, "rf", "c")),
    "(c) reaches {:.3f} and {:.3f}")
t = CT["K=1000"]; pb = {round(t[k]["p_bonferroni"] / 1e-9, 1) for k in ("d_vs_c", "d_vs_a")}
good = pb == {7.5} and all(t[k]["p_bonferroni"] < 0.05 for k in t) and "$p_{\\mathrm{Bonf}} = 7.5\\times 10^{-9}$" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-A: p_Bonf {pb} x 1e-9 for (d)-(c) and (d)-(a)")
print("== Section V-A and Appendix C: cross-M (cross_m_generalization.json)")
XM = json.load(open(R + "cross_m_generalization.json")); XA = XM["aggregate"]
xm = lambda p, cf="d", k="cross_m": XA[p][cf][k]["mean"]
cv = XM["canonical_validation"]
good = max(cv["max_abs_diff_vs_canonical_runs_csv"].values()) < 1e-12 and abs(cv["recomputed_in_distribution"]["d"]["mean"] - au(1000, "rf", "d")) < 1e-12
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-M: the in-distribution protocol reproduces the canonical runs ({cv['max_abs_diff_vs_canonical_runs_csv']})")
good = XM["K"] == 1000 and XM["alpha"] == 1.5 and not set(XM["seed_halves"][0]) & set(XM["seed_halves"][1])
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-M: K = {XM['K']}, alpha = {XM['alpha']}, disjoint seed halves")
chk("V-A: trained on 5, tested on 25 and 100", "(d) falls to $0.61$ and $0.63$", (xm("5->25"), xm("5->100")), "(d) falls to {:.2f} and {:.2f}")
chk("App. C: trained on 25, tested on 5", "and trained on 25 it falls to $0.48$ on five", xm("25->5"), "and trained on 25 it falls to {:.2f} on five")
chk("App. C: trained on 25, tested on 100", "and $0.75$ on 100", xm("25->100"), "and {:.2f} on 100")
cs = [xm(p, "d", "cross_seed_same_m") for p in XA]
chk("App. C: same M, other seeds", "versus $0.95$--$0.995$ on the same $M$ with other seeds", (min(cs), max(cs)),
    "versus {:.2f}--{:.3f} on the same M with other seeds")
lk = [XA[p]["a"]["all_sessions"]["same_seed_reference_leaky"]["mean"] for p in XA]
chk("App. C: a same-seed split would score (a)", "(a) at $0.88$--$0.94$ by memorization", (min(lk), max(lk)), "(a) at {:.2f}--{:.2f} by memorization")
xs = [xm(p) for p in XA]
sym = json.load(open(R + "symbolic_detector.json"))["aggregate"]
print("== tab:symbolic (symbolic_detector.json)")
# the rows as printed in the table
rows = {"1.5:1:0": "$M{=}1$ ", "1.5:5:0": "$M{=}5$ ", "1.5:25:0": "$M{=}25$ ",
        "1.5:100:0": "$M{=}100$", "1.5:25:1": "$M{=}25$, adversarial"}
U = pd.read_csv(R + "unseen_synth_summary.csv")
def us(mode, stacks, adv, method, col, alpha=1.5):
    x = U[(U["mode"] == mode) & (U["alpha"] == alpha) & (U["stacks"] == stacks) & (U["adv"] == adv) & (U["method"] == method)]
    return float(x.iloc[0][col])
for k, lab in rows.items():
    a = sym[k]; line = [l for l in TEX.splitlines() if l.startswith(lab) and "&" in l]
    nums = re.findall(r"\d+\.\d+", line[0].split("&", 1)[1]) if line else []
    st, adv = int(k.split(":")[1]), int(k.split(":")[2])
    exp = [f"{a['sym_recall']*100:.1f}", f"{a['sym_fpr']*100:.2f}", f"{a['sym_f1']:.3f}",
           f"{us('original', st, adv, 'modal', 'recall')*100:.1f}",
           f"{us('original', st, adv, 'zscore', 'recall')*100:.1f}",
           f"{us('original', st, adv, 'unseen', 'recall')*100:.1f}",
           f"{a['rf_recall_fpr0']*100:.1f}", f"{a['rfp_recall_fpr0']*100:.1f}"]
    good = nums == exp; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} tab:symbolic row {k:48s} printed={nums} data={exp}")
# the enrichment rows of unseen_synth.py reproduce tab:symbolic (two scripts, one number)
for k in rows:
    st, adv = int(k.split(":")[1]), int(k.split(":")[2])
    good = abs(us("original", st, adv, "enrichment", "recall") - sym[k]["sym_recall"]) < 5e-4; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} unseen_synth reproduces tab:symbolic enrichment recall at {k}")
line = [l for l in TEX.splitlines() if l.startswith("$M{=}25$, shared") and "&" in l]
nums = re.findall(r"\d+\.\d+", line[0].split("&", 1)[1]) if line else []
exp = [f"{us('shared_profile_tail', 25, 0, 'enrichment', 'recall')*100:.1f}",
       f"{us('shared_profile_tail', 25, 0, 'enrichment', 'fpr')*100:.2f}",
       f"{us('shared_profile_tail', 25, 0, 'enrichment', 'f1'):.3f}",
       f"{us('shared_profile_tail', 25, 0, 'modal', 'recall')*100:.1f}",
       f"{us('shared_profile_tail', 25, 0, 'zscore', 'recall')*100:.1f}",
       f"{us('shared_profile_tail', 25, 0, 'unseen', 'recall')*100:.1f}"]
good = nums == exp; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:symbolic row shared stacks {'':34s} printed={nums} data={exp}")
SC = [(1, 0), (5, 0), (25, 0), (100, 0), (25, 1)]
v = max(us("original", s, a_, "unseen", "fpr") for s, a_ in SC); vm = max(us("original", s, a_, "unseen", "fpr_max") for s, a_ in SC)
good = f"{v*100:.2f}" == "0.03" and f"{vm*100:.1f}" == "0.5" and "with mean collateral $0.03\\%$ (at most $0.5\\%$ in one seed)" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:symbolic note: unseen FPR mean {v*100:.3f}%, largest seed {vm*100:.2f}%")
zf0 = [us("original", s, 0, "zscore", "fpr") for s in (1, 5, 25, 100)]
good = (max(zf0) == 0 and f"{us('shared_profile_tail', 25, 0, 'zscore', 'fpr')*100:.2f}" == "3.37"
        and f"{us('original', 25, 1, 'zscore', 'fpr')*100:.1f}" == "11.3"
        and "and the $z$-score $89.9\\%$ at $3.37\\%$" in TEXN and "the $z$-score $57.3\\%$ at $11.3\\%$" in TEXN
        and f"{us('shared_profile_tail', 25, 0, 'zscore', 'recall')*100:.1f}" == "89.9" and f"{us('original', 25, 1, 'zscore', 'recall')*100:.1f}" == "57.3"
        and f"{us('shared_profile_tail', 25, 0, 'enrichment', 'recall')*100:.1f}" == "85.4" and f"{us('shared_profile_tail', 25, 0, 'enrichment', 'fpr')*100:.2f}" == "2.23"
        and "On those the test blocks $85.4\\%$ at $2.23\\%$ collateral, and the $z$-score $89.9\\%$ at $3.37\\%$" in TEXN
        and "the test reaches wherever the learned model runs except the adversarial case." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:symbolic note: z-score FPR 0 except shared and adversarial")
mf = [us("original", s, a_, "modal", "fpr") for s, a_ in ((5, 0), (25, 0), (100, 0), (25, 1))] + [us("shared_profile_tail", 25, 0, "modal", "fpr")]
good = (us("original", 1, 0, "modal", "fpr") == 0 and all(f"{x*100:.1f}" == "39.0" for x in mf)
        and f"{us('original', 25, 0, 'modal', 'fpr', alpha=2.0)*100:.1f}" == "61.1"
        and "With a single botnet stack, the modal fingerprint and the test agree, blocking $89.8\\%$ of the attack with no observed collateral." in TEXN
        and "it blocks $0.0\\%$ of the attack and $39.0\\%$ of legitimate traffic, rising to $61.1\\%$ under a more concentrated legitimate population ($\\alpha = 2.0$)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:symbolic note: modal FPR 0 at M=1, 39.0% elsewhere, 61.1% at alpha 2.0")
print("== Section V-B text")
good = all(abs(us("original", s, 0, "zscore", "recall") - us("original", s, 0, "enrichment", "recall")) < 5e-4
           and us("original", s, 0, "zscore", "fpr") == 0 for s in (5, 25)) and "The binomial test and the $z$-score block $90.0\\%$ of the attack at five stacks and $90.3\\%$ at 25" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the z-score blocks as the test at 5 and 25 stacks, zero FPR")
m100 = {m: us("original", 100, 0, m, "recall") for m in ("enrichment", "zscore", "unseen")}
good = (f"{m100['enrichment']*100:.1f}" == "38.6" and f"{m100['zscore']*100:.1f}" == "80.4" and f"{m100['unseen']*100:.1f}" == "88.1"
        and "the test falls well below the $z$-score and the unseen filter (Table~\\ref{tab:symbolic})" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-A: at 100 stacks the z-score and the unseen filter beat the test {m100}")
SDA = json.load(open(R + "symbolic_detector.json"))["aggregate"]["1.5:25:0"]
good = (f"{SDA['rf_recall_fpr1']*100:.1f}" == "66.8" and f"{SDA['rfp_recall_fpr1']*100:.1f}" == "94.6"
        and "At $1\\%$ false positives, which the test does not need, (d) reaches $66.8\\%$ at 25 stacks and $94.6\\%$ with the profile" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-A: the learned model at 1% FPR, {SDA['rf_recall_fpr1']*100:.1f}% and {SDA['rfp_recall_fpr1']*100:.1f}% with the profile")
chk("RF + profile recall @FPR=0, M=25", "87.4", sym["1.5:25:0"]["rfp_recall_fpr0"]*100, pct)
chk("RF + profile recall @FPR=0, M=100", "86.9", sym["1.5:100:0"]["rfp_recall_fpr0"]*100, pct)
# "the rule matches it up to 25 stacks": within two points of the profile-aware model
gap = max(sym[k]["rfp_recall_fpr0"] - sym[k]["sym_recall"] for k in ("1.5:1:0", "1.5:5:0", "1.5:25:0"))
good = gap < 0.02 and sym["1.5:25:0"]["sym_recall"] >= sym["1.5:25:0"]["rfp_recall_fpr0"]
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} rule matches the profile-aware model up to M=25 (largest shortfall {gap*100:.1f} pts)")

print("== fig:collateral and Section V-C (realistic_final_consolidated.csv)")
c = pd.read_csv(R + "realistic_final_consolidated.csv").set_index(["alpha", "stacks", "adv"])
g = lambda a, m, v, col, _c=c: float(_c.loc[(a, m, v), col]) * 100
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
print("== cross-check: tab:symbolic and fig:collateral come from two scripts; enrichment must agree")
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
chk("M=100 1k profile (same as tab:symbolic)", "38.6", dm["matched"]["coverage"]*100, pct)

print("== per window (rule_detection_steady60_rate0_bigprof_binom)")
J = json.load(open(R + "rule_detection_steady60_rate0_bigprof_binom.json")); r = J["by_percentile"]["99.0"]
W = pd.read_csv(R + "rule_detection_windows_steady60_rate0_bigprof_binom.csv")
def fired(kind):
    x = W[(W.kind == kind) & (W["size"] >= 5)]
    if kind.startswith("attack"): x = x[x.n_attack >= 5]
    return x, x[(x.omega >= r["tau"]) & x.scope_named]
pw = {}
for kind, n in (("attack_K1000", 90), ("attack_K50", 35), ("clean", 360), ("flash_25", 30), ("flash_50", 30), ("flash_100", 30)):
    x, f = fired(kind); rr = r[kind]
    pw[kind] = (rr["windows"] == n and len(x) == n, rr["omega"], rr["pipeline"],
                f.scope_recall.median() if kind.startswith("attack") else None, f.scope_collateral.max() if kind.startswith("attack") else None)
good = (all(v[0] for v in pw.values())
        and [f"{pw[k][1]*100:.1f}" for k in ("attack_K1000", "attack_K50", "clean")] == ["77.8", "85.7", "0.6"]
        and [round(pw[k][1] * 100) for k in ("flash_25", "flash_50", "flash_100")] == [80, 100, 100]
        and all(pw[k][2] == 0 for k in ("clean", "flash_25", "flash_50", "flash_100"))
        and [round(pw[k][3] * 100) for k in ("attack_K1000", "attack_K50")] == [80, 75] and all(pw[k][4] == 0 for k in ("attack_K1000", "attack_K50"))
        and "Over 30 runs each, $\\Omega$ passes $\\tau_{\\mathrm{cluster}}$ in $77.8\\%$ and $85.7\\%$ of the 90 and 35 attack windows at $K = 1000$ and $50$, in $0.6\\%$ of 360 clean windows and in $80$--$100\\%$ of the flash crowds of 25 to 100 users" in TEXN
        and all(len(fired(k)[0][fired(k)[0].omega >= r["tau"]]) == len(fired(k)[1]) for k in ("attack_K1000", "attack_K50"))
        and "names a filter in every attack window flagged by $\\Omega$ and blocks a median $75$--$80\\%$ of attackers, with no legitimate session hit." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: the rule per window on generated traffic (former Table VIII) {[(k, round(v[1]*100, 1)) for k, v in pw.items()]}")
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

print("== Section V-D intro and Appendix E (production_summary.json)")
P = json.load(open(R + "production_summary.json")); E = P["endpoints"]; V = P["variants"]
m, a = V["origin_calibrated"], V["origin_calibrated_all"]
c = a["clean"]
chk("scope per connection, nominal level (V-D)", "60.1", V["session_nominal"]["clean"]["enrichment"]*100, pct)
chk("scope per origin, nominal level (V-D)", "26.9", V["origin_nominal"]["clean"]["enrichment"]*100, pct)
chk("rule per origin, calibrated (V-C)", "brings the base rule to $0.2\\%$", m["clean"]["pipeline"]*100, "brings the base rule to {:.1f}")
v = c["collateral_pipeline_median"]; good = 0.4 <= v <= 0.6 and "often a fleet blocking about half of a window's clients" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: false alarms block 'about half' of clients: {v:.3f}")
cells = [x for sec in ("attack_fresh_M25", "attack_tail_M25", "attack_relative_M25") for x in a[sec].values()]
good = (c["origins_enrichment_pipeline"] <= 0.55 * c["pipeline"]
        and all(x["origins_enrichment_blocked"] >= x["blocked_pipeline"] for x in cells)
        and "halves the base rule's false alarms with no loss of detection" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: origin gate halves false alarms ({c['origins_enrichment_pipeline']*100:.2f} vs "
      f"{c['pipeline']*100:.2f}%), no loss in any of {len(cells)} attack cells")
n_org, n_om = round(c["origins_enrichment_pipeline"] * c["windows"]), round(c["pipeline"] * c["windows"])
good = n_org < n_om / 2 + 1 and "halves the base rule's false alarms with no loss of detection" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: origin gate {n_org} against {n_om} clean false alarms")
vb = P["volume_baseline"]
nb_, no1, no2 = vb["clean_both"]["windows"], vb["clean_omega_only"]["windows"], vb["clean_origins_only"]["windows"]
good = (nb_, nb_ + no1 + no2) == (136, 181) and "which fires with $\\Omega$ in 136 of the 181 clean windows where either fires" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: gate and Omega fire together in {nb_} of {nb_ + no1 + no2} clean windows where either fires")
more = all(x["origins"] >= x["omega"] for x in list(vb["attack_fresh_M25"].values()) + list(vb["attack_relative_M25"].values()))
ok += more; bad += not more; print(f"{'OK ' if more else 'XX '} V-D: the origin threshold catches at least as many attacks")
sc = sorted(E[e]["clean"]["enrichment"] * 100 for e in E)
good = f"${sc[0]:.1f}$--${sc[-1]:.1f}\\%$" in TEX; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: scope alone out of sample {sc[0]:.1f}--{sc[-1]:.1f}%")
# rho sensitivity: every pooled entry of the earlier production table that depends on rho
dep = [("pipeline", "collateral_pipeline_median", "blocked_pipeline"),
       ("union_pipeline", "union_collateral_median", "union_blocked"),
       ("origins_enrichment_pipeline", "origins_enrichment_collateral_median", "origins_enrichment_blocked"),
       ("origins_union_pipeline", "origins_union_collateral_median", "origins_union_blocked")]
def kinds(v):
    fire, coll, blk = [], [], []
    for cf, cc, b in dep:
        fire += [v["clean"][cf], v["flash"]["100"][cf]]; coll.append(v["clean"][cc])
        for src in ("fresh", "tail"):
            blk += [v[f"attack_{src}_M25"]["100"][b], v[f"attack_{src}_M25"]["1000"][b],
                    v["attack_relative_M25"][f"{src}:M25:x1"][b]]
    return fire, coll, blk
moves = [max(abs(x - y) for r in ("rho2", "rho5") for x, y in zip(kinds(V[r])[i], kinds(a)[i])) for i in range(3)]
chk("App. E: rho moves no firing rate by over", "by more than $0.3$ points", moves[0]*100, "by more than {:.1f} points")
chk("App. E: rho moves no blocked share by over", "by more than $4.5$", moves[2]*100, "by more than {:.1f}")
chk("App. E: rho moves a collateral median by up to", "no collateral median by more than $7.2$", moves[1]*100, "no collateral median by more than {:.1f}")
chk("App. E: flash crowds of 1,000, z-score", "86.8", a["flash"]["1000"]["zscore_pipeline"]*100, pct)
# App. B's profile range now covers the held-out day too; the test-day profiles must sit inside it
fps = [x for e in E for x in E[e]["profile_fingerprints"]]
good = min(fps) == 76 and max(fps) <= 1163 and "exceeds the $76$--$1\\,163$ observed per production endpoint" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. B: test-day profiles hold {min(fps)}--{max(fps)} fingerprints, inside the printed 76--1163")
good = P["self_check"]["mismatches"] == 0; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} production scope self-check: {P['self_check']}")

print("== tab:production (production_tables.json)")
import math
import statistics as st_
PT = json.load(open(R + "production_tables.json"))
TD, FD, FL, FPD = PT["test_days"], PT["fresh_day"], PT["floor"], PT["floor_deployed"]
tf = ["2026-09-20", "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24"]
fmt = lambda v: "--" if v is None else f"{v*100:.1f}"
# the configurations as the tables name them (Table II): run and scope, and the gate
SCOPE = {"binomial": ("fleets", "union"), "beta-bin.": ("od", "union"), "$z$-score": ("base", "zcal"),
         "base rule": ("base", "enrichment")}
XFIT = {"binomial": ("xfit_fleets", "union"), "beta-bin.": ("xfit_od", "union"), "$z$-score": ("xfit", "zcal")}
GATE = {"binomial": "origins", "beta-bin.": "origins", "$z$-score": "origins", "base rule": "omega"}
COLS = ["new:x0.1", "new:x1", "shared:x0.1", "shared:x1"]
def table_rows(label):
    s = TEX[TEX.index("\\label{%s}" % label):]
    s = s[:s.index("\\end{tabular}")]
    group, rows = None, []
    for l in s.splitlines():
        if "Test days, calibrated in sample" in l: group = "in"; continue
        if "Test days, cross-fitted" in l: group = "xfit"; continue
        if "Held-out day" in l: group = "fresh"; continue
        cells = [x.strip() for x in l.strip().rstrip("\\").split("&")]
        vals = cells[2:]
        if len(vals) != 8 or not all(re.fullmatch(r"\d+\.\d|--", x) for x in vals):
            continue
        group = cells[0] or group
        rows.append((group, cells[1].replace("$^{*}$", ""), vals))
    return rows
def expected(g, name):
    run, sc = (XFIT if g == "xfit" else SCOPE)[name]
    B = FD if g == "fresh" else TD
    blk = B[run]["all"] if g in ("in", "xfit", "fresh") else B[run]["per_endpoint"][g]
    r = blk[f"{sc}|{GATE[name]}"]
    return [fmt(r["clean_rate"]), fmt(blk[f"{sc}|none"]["clean_rate"]), fmt(r["clean_collateral_median"]),
            fmt(r["flash1000"])] + [fmt(r[x]["blocked"]) for x in COLS]
# the held-out day's rows left Table IV when the block got its own table (Table VII)
for label, want in (("tab:production", [("in", n) for n in ("binomial", "beta-bin.", "$z$-score")]
                     + [("xfit", n) for n in ("binomial", "beta-bin.", "$z$-score")]),):
    rows = table_rows(label)
    for g, name, printed in rows:
        exp = expected(g, name)
        good = printed == exp; ok += good; bad += not good
        print(f"{'OK ' if good else 'XX '} {label} {g:5s} {name:10s} printed={printed} data={exp}")
    good = [(g, n) for g, n, _ in rows] == want; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} {label} holds the {len(want)} rows in order ({len(rows)} parsed)")
fz, ob, zc = TD["fleets"]["all"]["union|origins"], TD["od"]["all"]["union|origins"], TD["base"]["all"]["zcal|origins"]
ff_, fo, zf = FD["fleets"]["all"]["union|origins"], FD["od"]["all"]["union|origins"], FD["base"]["all"]["zcal|origins"]
good = fz["clean_windows"] == 5643 and ff_["clean_windows"] == 1152 and "(5\\,643 on the test days and 1\\,152 on the held-out day, windows under $k_{\\min}$ origins left out)" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:production note: {fz['clean_windows']} clean windows on the test days, {ff_['clean_windows']} on the held-out day")
tp_ = TEX[TEX.index("\\label{tab:production}"):]; tp_ = tp_[:tp_.index("\\end{table}")]
good = ("$^{*}$Post hoc. $0.1\\times$, $1\\times$: botnet size, in median windows.}" in tp_ and "Held-out day" not in tp_
        and "\\caption{The configurations on the test days, all endpoints.}" in TEX and "so at most about $90\\%$ can be blocked" in TEXN); ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:production: test days only, the beta-binomial marked post hoc")
nfa = {e: TD["fleets"]["per_endpoint"][e]["union|origins"]["clean_fires"] for e in ("E1", "E2", "E3", "E4")}
good = nfa["E2"] == 4 and max(nfa[e] for e in ("E1", "E3", "E4")) == 1 \
    and "4 of them on the web console" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: false alarms per endpoint {nfa}, 4 of 5 on the console")
kf = {r: [FL[r][e][f]["known_fleets"] for e in FL[r] for f in FL[r][e]] for r in FL}
same = all(TD["od"][k] == TD["od_fleets"][k] and FD["od"][k] == FD["od_fleets"][k] for k in ("all", "per_endpoint"))
good = (max(kf["od_fleets"]) == 0 and same
        and "& beta-bin. & --             & post hoc" in TEX)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: beta-binomial names no known fleet in any fold in sample ({max(kf['od_fleets'])}), identical with the fleet profile: {same}")
good = ("Five choices were made on the test days: counting origins, calibrating $\\lambda_e$, the gate, the union with the unseen filter and the $5\\%$ fleet share" in TEXN
        and "$^{*}$Post hoc: built after the held-out day was read" in TEXN
        and "The second, built after the held-out day was read (Section~\\ref{sec:posthoc}), is a \\textbf{beta-binomial background}" in TEXN
        and "\\textit{Cross-fitting}, built post hoc, judges each calibration day, like a test day, against a profile of the other days" in TEXN
        and "$^{*}$Post hoc, as is cross-fitting" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:configs note: the choices made on the test days and the post hoc ones")

print("== tab:floor (production_tables.json, floor_bands.json)")
FB = json.load(open(R + "floor_bands.json"))
good = FB["check"]["mismatches"] == 0 and FB["check"]["folds"] == 60
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} floor_bands: profiles rebuilt from the exports match the runs in {FB['check']['folds']} folds")
bB = lambda run, e, band, key: [FB["per_endpoint"][e][f][run]["bands"][band] for f in tf]
good = all([x["binomial"] for x in bB("fleets", e, "ranks_11_plus", "")] == [FPD["fleets"][e][f]["25"]["shared"]["min_attackers"] for f in tf]
           for e in ("E1", "E2", "E3", "E4"))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} floor_bands reproduces the binomial configuration's shared floors fold by fold")
exact = lambda run, e: st_.median(x["beta_binomial"] for x in bB(run, e, "ranks_11_plus", ""))
exactW = lambda run, e: st_.median(x["beta_binomial_windows"] for x in bB(run, e, "ranks_11_plus", ""))
med = lambda run, e: st_.median(FL[run][e][f]["new"]["min_fraction_of_window"] for f in tf)
ma = lambda run, e: st_.median(FL[run][e][f]["new"]["min_attackers"] for f in tf)
lvl = lambda run, e: st_.median(FL[run][e][f]["level"] for f in tf)
dA = lambda run, e, kind, M=25: st_.median(FPD[run][e][f][str(M)][kind]["min_attackers"] for f in tf)
dF = lambda run, e, kind, M=25: st_.median(FPD[run][e][f][str(M)][kind]["min_fraction_of_window"] for f in tf)
for e, lab in [("E1", "E1, RUM beacons"), ("E2", "E2, web console"), ("E3", "E3, API"), ("E4", "E4, SSO")]:
    line = [l for l in TEX.splitlines() if l.strip().startswith(lab) and "&" in l]
    cl = [x.strip() for x in line[0].strip().rstrip("\\").split("&")] if line else []
    printed = ([cl[1]] + [re.search(r"10\^\{(-?\d+)\}", x).group(1) for x in cl[2:4]] + cl[4:8]) if len(cl) == 8 else cl
    no = st_.median(FL["base"][e][f]["median_origins"] for f in tf)
    exp = [f"{no:,.0f}".replace(",", "\\,"), str(round(math.log10(lvl("fleets", e)))), str(round(math.log10(lvl("od", e))))]
    exp += [f"{dA(a, e, k):.0f}/{dA(b, e, k):.0f}" for a, b in (("fleets", "xfit_fleets"),) for k in ("new", "shared")]
    exp += [f"{dA('od', e, 'new'):.0f}/{dA('xfit_od', e, 'new'):.0f}", f"{exact('od', e):.0f}/{exact('xfit_od', e):.0f}"]
    good = printed == exp; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} tab:floor {lab:16s} printed={printed} data={exp}")
no_ = [st_.median(FL["base"][e][f]["median_origins"] for f in tf) for e in ("E1", "E2", "E3", "E4")]
good = round(no_[0], -3) == 3000 and "whose median windows hold about $3\\,000$, " + ", ".join(f"{x:.0f}" for x in no_[1:3]) + f" and {no_[3]:.0f} origins" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} IV: median windows {no_}")
good = PT["endpoints_exported"] == 12 and "Of the 12 endpoints exported, they are the four that carry TLS and have at least 50 calibration windows and a median window of at least $k_{\\min}$ origins" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} IV: the four evaluated endpoints of the {PT['endpoints_exported']} exported")
good = (all(FPD["fleets"][e][f]["25"]["new"]["min_attackers"] == math.ceil(5 * 25 / 0.9) and FPD["fleets"][e][f]["25"]["new"]["set_by"] == "unseen"
            for e in ("E1", "E2", "E3") for f in tf) and "the unseen filter sets the floor on E1 to E3: 139 attackers per window, so that the average stack reaches $k_{\\min}$ origins. On E4 the test names the stacks first, from 84" in TEXN
        and all(FPD["fleets"]["E4"][f]["25"]["new"]["set_by"] == "test" and FPD["fleets"]["E4"][f]["25"]["new"]["min_attackers"] == 84 for f in tf)
        and "requiring $\\lceil k_{\\min} M/0.9 \\rceil$ attackers regardless of level, 139 for $M = 25$" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D, tab:floor: the unseen filter sets the new-stack floor at 139 attackers on E1-E3")
good = ("the level sets the floor, computed at their median share." in TEXN
        and FB["bands"]["ranks_11_plus"] == [11, None])
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared stacks at the tail's median prevalence")
lim = 0.9 / (3.0 * 25)
above = [FB["per_endpoint"][e][f]["fingerprints_above_limit"] for e in ("E1", "E2", "E3", "E4") for f in tf]
share = [FB["per_endpoint"][e][f]["origin_share_above_limit"] for e in ("E1", "E2", "E3", "E4") for f in tf]
good = (f"{lim*100:.1f}" == "1.2" and all(abs(FB["per_endpoint"][e][f]["enrichment_limit"] - lim) < 1e-12 for e in ("E1", "E2", "E3", "E4") for f in tf)
        and "a botnet on $M$ stacks is not expected to enrich a fingerprint whose share exceeds $0.9/(\\rho M)$, $1.2\\%$ for $M = 25$" in TEXN
        and (min(above), max(above)) == (4, 28) and round(min(share) * 100) == 86 and round(max(share) * 100) == 94
        and "\\textbf{Past the ratio limit the scope is expected to name nothing.} The 4 to 28 most common fingerprints of each endpoint, which carry $86$--$94\\%$ of its origins, lie past that limit for a 25-stack botnet" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D, V-B: the ratio limit 0.9/(rho M) = {lim:.3f}; {min(above)}--{max(above)} fingerprints above it carry {min(share)*100:.1f}--{max(share)*100:.1f}% of origins")
b36 = st_.median(x["binomial"] for x in bB("fleets", "E1", "ranks_36_100", ""))
o36 = st_.median(x["beta_binomial"] for x in bB("od", "E1", "ranks_36_100", ""))
good = (b36 == 743 and o36 == 480
        and "and those of rank 36 to 100 need 743, 1\\,898, 227 and 84" in TEXN
        and "Post hoc, on ranks 36 to 100 the busiest endpoint's floor falls from 743 attackers under the binomial to 480 under the beta-binomial" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B, App. E: E1 floors on profile ranks 36-100, binomial {b36}, beta-binomial {o36}")
n1135 = {e: [x["binomial"] for x in bB("fleets", e, "ranks_11_35", "")] for e in ("E1", "E2", "E3", "E4")}
good = (all(v is None for e in ("E1", "E2") for v in n1135[e]) and all(v is not None for e in ("E3", "E4") for v in n1135[e])
        and [st_.median(n1135[e]) for e in ("E3", "E4")] == [808, 114]
        and "and with the fingerprints' popularity: those of rank 11 to 35 are never named on the two largest endpoints (Appendix~\\ref{app:window})" in TEXN
        and "For 25 stacks, fingerprints of rank 11 to 35 need 808 on E3 and 114 on E4" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: ranks 11-35 never named on E1 and E2, named on E3 and E4 {n1135}")
tailb = [FB["per_endpoint"][e][f]["tail_prevalence_median"] for e in ("E1",) for f in tf]
good = max(tailb) < 1e-5 and "On stacks that real clients also present, mostly rare ones past the profile's ten most common fingerprints, the level sets the floor" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared stacks are mostly rare (E1 tail median prevalence {max(tailb):.1e})")

print("== Section V-B prose (production_tables.json)")
f1 = FL["base"]["E1"]
so = sorted(f1[f]["new"]["min_stack_origins"] for f in tf)
good = f"past {so[0]} to {so[-1]} origins" in TEXN and round(math.log10(lvl("base", "E1"))) == -60 and "fleets push $\\lambda_e$ down to $10^{-60}$" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: E1 level 10^-60 names a stack only past {so[0]} to {so[-1]} origins")
kn = sorted(set(FL["fleets"]["E1"][f]["known_fleets"] for f in tf))
good = kn == [5, 6] and "five or six known fleets" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: E1 exempts {kn} known fleets per test day")
nw = [dA("fleets", e, "new") for e in ("E1", "E2", "E3", "E4")]
good = nw == [139, 139, 139, 84] and "For a 25-stack botnet on new stacks, the unseen filter sets the floor on E1 to E3: 139 attackers per window" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: binomial configuration's new-stack floors {nw}")
shA, shF = dA("fleets", "E1", "shared"), dF("fleets", "E1", "shared")
shS = [dF("fleets", e, "shared") for e in ("E2", "E3", "E4")]
good = (shA == 254 and round(shF * 100) == 8 and round(min(shS)) == 4 and round(max(shS)) == 19
        and "A typical stack is then named only past 254 attackers on the busiest endpoint, $8\\%$ of its window, and past 4 to 19 median windows on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared-stack floors E1 {shA} ({shF*100:.1f}%), small endpoints {[round(x, 1) for x in shS]} windows")
l1 = lvl("od", "E1")
good = (round(math.log10(l1)) == -4 and "& $10^{-21}$ & $10^{-4}$ &" in TEX and "& $10^{-73}$ & $10^{-2}$ &" in TEX
        and all(FL["od"]["E1"][f]["new"]["min_stack_origins"] == 3 for f in tf)
        and all(FL["od"][e][f]["new"]["min_stack_origins"] == 2 for e in ("E2", "E3", "E4") for f in tf)
        and all(abs(lvl("od", e) - 0.01) < 1e-12 for e in ("E2", "E3", "E4")))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: beta-binomial level {l1:.2e} on E1 (three origins), the 0.01 cap elsewhere (two)")
bsA, bsF = exact("od", "E1"), exactW("od", "E1")
bsS = [exactW("od", e) for e in ("E2", "E3", "E4")]
good = (bsA == 86 and all(exact("od", e) < dA("fleets", e, "shared") for e in ("E1", "E2", "E3"))
        and exact("od", "E4") == dA("fleets", "E4", "shared")
        and "In sample the beta-binomial lowers the shared-stack floor on the three largest endpoints (Table~\\ref{tab:floor})" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: beta-binomial shared floors E1 {bsA} ({bsF*100:.1f}%), elsewhere {[round(x, 2) for x in bsS]}")
SW = PT["sweep"]
m = SW["fleets"]["E1"]["new:M25:A100"]
good = (round(m["blocked_alone"] * 100) == round(m["model_blocked_alone"] * 100) == 43
        and f"{m['model_blocked_alone']*100:.1f}" == "43.1" and f"{m['blocked_alone']*100:.1f}" == "43.2"
        and "It is no cliff: below it the scope names the stacks that chance makes larger, as a binomial model of stack sizes predicts ($43.1\\%$ predicted versus $43.2\\%$ measured for 100 new-stack attackers on E1, Fig.~\\ref{fig:stops})" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: below the floor, E1 scope alone stops {m['blocked_alone']*100:.1f}% of 100 new-stack attackers, model {m['model_blocked_alone']*100:.1f}%")
dev = [abs(SW[r][e][k]["blocked_alone"] - SW[r][e][k]["model_blocked_alone"]) for r in ("fleets", "od") for e in ("E1", "E2", "E3")
       for k in SW[r][e] if k.startswith("new:M25:A")]
good = max(dev) < 0.1
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} the stack-size model matches the injected new stacks on E1-E3 within {max(dev)*100:.1f} points")
alone = {"bin": TD["fleets"]["all"]["union|none"]["clean_rate"], "bin_E2": TD["fleets"]["per_endpoint"]["E2"]["union|none"]["clean_rate"],
         "beta": TD["od"]["all"]["union|none"]["clean_rate"], "z": TD["base"]["all"]["zcal|none"]["clean_rate"],
         "gate": TD["base"]["all"]["gates_clean"]["origins"]}
chk("V-B: components out of sample", "scope alone names a filter in $2.2\\%$ of clean test-day windows, and the distinct-origin gate alone fires in $3.0\\%$",
    tuple(alone[k] * 100 for k in ("bin", "gate")),
    "scope alone names a filter in {:.1f} of clean test-day windows, and the distinct-origin gate alone fires in {:.1f}")
jb, jz = TD["fleets"]["all"]["union|origins"], TD["base"]["all"]["zcal|origins"]
from scipy.stats import poisson as _pois
pj = lambda r, k: (TD[r]["all"][k]["clean_fires"], TD[r]["all"][k]["clean_joint_expected"],
                   float(_pois.sf(TD[r]["all"][k]["clean_fires"] - 1, TD[r]["all"][k]["clean_joint_expected"])))
chk("V-B: joint misfires of the binomial configuration", "yet the 5 joint misfires, versus 3.5 under independence, are within chance ($P = 0.27$,",
    pj("fleets", "union|origins"), "yet the {} joint misfires, versus {:.1f} under independence, are within chance (P = {:.2f},")
jo = TD["od"]["all"]["union|origins"]
chk("App. E: the same for the beta-binomial and the z-score", "for the post hoc beta-binomial and the calibrated $z$-score, in 22 and 20 windows versus 7.5 and 11.9",
    (jo["clean_fires"], jz["clean_fires"], jo["clean_joint_expected"], jz["clean_joint_expected"]),
    "for the post hoc beta-binomial and the calibrated z-score, in {} and {} windows versus {:.1f} and {:.1f}")
PJ = {n: pj(*rk)[2] for n, rk in (("bin", ("fleets", "union|origins")), ("bin_x", ("xfit_fleets", "union|origins")),
                                   ("beta", ("od", "union|origins")), ("beta_x", ("xfit_od", "union|origins")),
                                   ("z", ("base", "zcal|origins")), ("z_x", ("xfit", "zcal|origins")))}
xb_, xo_, xz_ = pj("xfit_fleets", "union|origins"), pj("xfit_od", "union|origins"), pj("xfit", "zcal|origins")
good = (PJ["bin"] > 0.05 and PJ["bin_x"] > 0.05 and max(PJ["beta"], PJ["beta_x"], PJ["z"], PJ["z_x"]) < 0.05
        and PJ["beta"] < 1e-4 and f"{PJ['z']:.2f}" == "0.02"
        and "($P < 10^{-4}$ and $P = 0.02$ for a Poisson count)" in TEXN
        and f"and in {xo_[0]} and {xz_[0]} versus {xo_[1]:.1f} and {xz_[1]:.1f} cross-fitted" in TEXN
        and f"5 versus 3.5 and {xb_[0]} versus {xb_[1]:.1f} cross-fitted ($P = {PJ['bin']:.2f}$ and ${PJ['bin_x']:.2f}$)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B, App. E: joint misfires against independence, Poisson P { {k: round(v, 4) for k, v in PJ.items()} }")
good = all(v > 0.01 for v in alone.values()) and "Pooled across endpoints, the calibrated scope and gate each exceed their $1\\%$ budget alone on the test days, and only together stay within it (Table~\\ref{tab:production})" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: every calibrated component exceeds 1% out of sample ({ {k: round(v*100, 2) for k, v in alone.items()} })")
ci = fz["clean_ci95"]
good = (fz["clean_fires"] == 5 and fmt(fz["clean_rate"]) == "0.1"
        and f"Together they fire on only $0.1\\%$ of clean windows (5 of 5\\,643, 95\\% interval ${ci[0]*100:.2f}$--${ci[1]*100:.2f}\\%$)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the binomial configuration, {fz['clean_fires']} false alarms on the test days")
e2day = lambda r, k: TD[r]["per_endpoint"]["E2"][k]["clean_fires_by_fold"]["2026-09-23"]
good = (fmt(zc["clean_rate"]) == fmt(ob["clean_rate"]) == "0.4" and (zc["clean_fires"], ob["clean_fires"]) == (20, 22)
        and e2day("base", "zcal|origins") == e2day("od", "union|origins") == 13
        and zc["clean_collateral_mean"] < fz["clean_collateral_mean"]
        and "The misfires of the other two also cluster by day, 13 of each on one day of the console, so exact intervals, which assume independent windows, understate their uncertainty" in TEXN
        and TD["od"]["per_endpoint"]["E2"]["union|origins"]["clean_fires"] == 19 and ob["clean_fires"] == 22
        and "but 19 of its 22 false alarms fall on the web console, where $74.4\\%$ of 1\\,000-user crowds trigger it" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: z-score and beta-binomial fire on {zc['clean_fires']} and {ob['clean_fires']} clean windows")
chk("V-B: median collateral per alarm", "These misfires block a median $32.9\\%$ of the window's clients", fz["clean_collateral_median"]*100,
    "These misfires block a median {:.1f} of the window's clients")
chk("V-B: expected collateral per clean window", "an expected $0.03\\%$ of clients per clean window", fz["clean_rate"] * fz["clean_collateral_mean"] * 100,
    "an expected {:.2f} of clients per clean window")
per_day = {k: s["clean_fires"] / 20 for k, s in (("bin", fz), ("z", zc), ("beta", ob))}
e2m = TD["fleets"]["per_endpoint"]["E2"]["union|origins"]["clean_fires"]
good = (fz["clean_fires"] == 5 and e2m == 4 and PT["endpoints"]["E2"] == "web console" and fz["clean_windows"] == 5643
        and "(5 of 5\\,643, 95\\% interval $0.03$--$0.21\\%$), 4 of them on the web console" in TEXN and round(288 * 0.01, 1) == 2.9
        and "about 2.9 of a day's 288 windows." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: {e2m} of the {fz['clean_fires']} misfires on the web console, budget 2.9 a day")
chk("V-B: flash crowds of 1,000 and their filters", "trigger the configuration in $22.2\\%$ of windows, with lighter filters blocking a median $4.3\\%$ of the window's clients",
    (fz["flash1000"]*100, fz["flash1000_collateral_median"]*100),
    "trigger the configuration in {:.1f} of windows, with lighter filters blocking a median {:.1f} of the window's clients")
good = fz["flash1000_collateral_median"] < fz["clean_collateral_median"]; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: flash-crowd filters are lighter than clean-window misfires ({fz['flash1000_collateral_median']*100:.1f}% vs {fz['clean_collateral_median']*100:.1f}%)")
S3 = [("fleets", "union|origins"), ("od", "union|origins"), ("base", "zcal|origins")]
sw1 = SW["fleets"]["E1"]
g_small = [sw1[f"new:M25:A{A}"]["gate"] for A in (25, 50, 100, 250)] + [sw1["new:M25:x0.1"]["gate"]]
good = (round(min(g_small) * 100) == 6 and round(max(g_small) * 100) == 13 and round(sw1["new:M25:A1000"]["gate"] * 100) == 45
        and round(sw1["new:M25:x1"]["gate"] * 100) == 79 and 0.3 < 1000 / no_[0] < 0.35
        and "the gate opens in only $6$--$13\\%$ of windows for botnets from 25 attackers up to a tenth of the median window" in TEXN
        and "in $45\\%$ at a third and in $79\\%$ at a whole window" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: E1 gate in attack windows {min(g_small)*100:.1f}--{max(g_small)*100:.1f}% up to a tenth, {sw1['new:M25:A1000']['gate']*100:.1f}% at 1,000, {sw1['new:M25:x1']['gate']*100:.1f}% at 1x")
chk("V-C: E1, the binomial configuration stops", "therefore stops $3.4\\%$ of a 100-attacker botnet and $11.8\\%$ of a tenth-size botnet",
    (sw1["new:M25:A100"]["blocked"]*100, sw1["new:M25:x0.1"]["blocked"]*100),
    "therefore stops {:.1f} of a 100-attacker botnet and {:.1f} of a tenth-size botnet")
chk("V-C: E1, the scope alone would block", "Its scope alone would block $43.2\\%$ and $89.6\\%$",
    (sw1["new:M25:A100"]["blocked_alone"]*100, sw1["new:M25:x0.1"]["blocked_alone"]*100), "Its scope alone would block {:.1f} and {:.1f}")
SE1 = PT["stealth_E1"]["fleets"]["fresh:x0.1"]
bd = [SE1[f]["blocked"] * 100 for f in tf]; bn = [SE1[f]["blocked_no_gate"] * 100 for f in tf]; bs = [SE1[f]["blocked_seasonal"] * 100 for f in tf]
chk("V-C: E1 0.1x blocked by day, origin gate", "$0.6$--$37.2\\%$ depending on the day", (min(bd), max(bd)), "{:.1f}--{:.1f} depending on the day")
bnf = PT["stealth_E1"]["fleets"]["fresh:x0.1"]["2026-09-25"]["blocked_no_gate"] * 100
good = all(89 <= x <= 91 for x in bn + [bnf]) and "The \\textit{scope as its own trigger} (No gate, dashed in Fig.~\\ref{fig:stops}) stops about $90\\%$ of that botnet on new stacks every day" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-C: E1 0.1x, the scope alone stops {min(bn):.1f}--{max(bn):.1f}% by test day and {bnf:.1f}% held out")
e1s, e1o_ = TD["fleets"]["per_endpoint"]["E1"]["union|seasonal"], TD["fleets"]["per_endpoint"]["E1"]["union|origins"]
e2o, e2s = TD["fleets"]["per_endpoint"]["E2"]["union|origins"], TD["fleets"]["per_endpoint"]["E2"]["union|seasonal"]
xs_ = {e: (TD["xfit_od"]["per_endpoint"][e]["union|seasonal"]["clean_rate"], FD["xfit_od"]["per_endpoint"][e]["union|seasonal"]["clean_rate"])
       for e in ("E1", "E2", "E3", "E4")}
good = (e1s["new:x0.1"]["blocked"] > e1o_["new:x0.1"]["blocked"] and f"{e2s['clean_rate']*100:.2f}" == "2.64"
        and all(max(v) <= 0.01 for v in xs_.values())
        and all(TD[r]["per_endpoint"]["E2"]["union|seasonal"]["clean_rate"] > 0.01 for r in ("fleets", "xfit_fleets", "od"))
        # ... and the unseen filter behind the seasonal gate also stays within it on the console
        and TD["fleets"]["per_endpoint"]["E2"]["unseen|seasonal"]["clean_rate"] <= 0.01
        # V-C quotes the range of those three: 2.0--2.6%
        and f"{min(TD[r]['per_endpoint']['E2']['union|seasonal']['clean_rate'] for r in ('fleets', 'xfit_fleets', 'od'))*100:.1f}" == "2.0"
        and f"{max(TD[r]['per_endpoint']['E2']['union|seasonal']['clean_rate'] for r in ('fleets', 'xfit_fleets', 'od'))*100:.1f}" == "2.6"
        and TD["xfit_od"]["per_endpoint"]["E2"]["union|seasonal"]["clean_rate"] <= 0.01
        and "It stops more of the tenth-size botnet on the busiest endpoint. Behind it, however, only the cross-fitted beta-binomial and the unseen filter stay within the budget on the console, where the binomial and the in-sample beta-binomial misfire in $2.0$--$2.6\\%$ of windows" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: seasonal gate E1 0.1x {e1s['new:x0.1']['blocked']*100:.1f}% vs {e1o_['new:x0.1']['blocked']*100:.1f}%, console {e2s['clean_rate']*100:.2f}%, cross-fitted beta-binomial at most {max(max(v) for v in xs_.values())*100:.2f}%")
good = e1s["clean_fires"] == 0; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: the seasonal gate raises no false alarm on E1 ({e1s['clean_fires']})")
a1, a1x, a1f = TD["fleets"]["per_endpoint"]["E1"]["union|none"], TD["xfit_fleets"]["per_endpoint"]["E1"]["union|none"], FD["fleets"]["per_endpoint"]["E1"]["union|none"]
b1 = TD["base"]["per_endpoint"]["E1"]["union|none"]; bf1 = a1["clean_fires_by_fold"]
good = (a1["clean_fires"] == 14 and a1["clean_windows"] == 1440 and f"{a1['clean_rate']*100:.2f}" == "0.97"
        and [round(x * 100, 2) for x in a1["clean_ci95"]] == [0.53, 1.63]
        and [bf1[f] for f in tf] == [0, 0, 1, 5, 8] and f"{a1['clean_collateral_median']*100:.1f}" == "1.0"
        and "With the binomial and known fleets, its rate on the busiest endpoint sits at the budget, rising from no false alarm on the first two test days to 8 of 288 on the last" in TEXN
        and "and its misfires there block a median $1.0\\%$ of the clients" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: binomial scope alone on E1 {a1['clean_fires']}/{a1['clean_windows']} = {a1['clean_rate']*100:.2f}% (CI {[round(x*100, 2) for x in a1['clean_ci95']]}), by day {[bf1[f] for f in tf]}, {b1['clean_fires']} without fleets")
good = (a1f["clean_fires"] == 0 and a1f["clean_windows"] == 288
        and f"{a1['clean_rate']*100:.2f}" == "0.97")
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} Table VI: the binomial scope alone on E1: {a1['clean_rate']*100:.2f}% test, 0 of 288 held out")
sa = [TD["fleets"]["per_endpoint"][e]["union|none"]["clean_rate"] * 100 for e in ("E2", "E3", "E4")]
def _e1(run, key, cell, blk=TD):
    return blk[run]["per_endpoint"]["E1"][key][cell]["blocked"]
GT = ("origins", "seasonal", "none")
same = all(abs(_e1(r, f"unseen|{g}", "new:x0.1", B) - _e1(r, f"union|{g}", "new:x0.1", B)) <= 0.005
           for g in GT for r in ("fleets", "xfit_od") for B in (TD, FD))
fewer = all(TD[r]["all"][f"unseen|{g}"]["clean_fires"] < TD[r]["all"][f"union|{g}"]["clean_fires"]
            and TD[r]["all"][f"unseen|{g}"]["flash1000"] < TD[r]["all"][f"union|{g}"]["flash1000"] for g in GT for r in ("fleets", "xfit_od"))
shared_ = all(_e1("fleets", f"unseen|{g}", "shared:x0.1") == 0 < _e1("xfit_od", f"union|{g}", "shared:x0.1") for g in GT)
good = (min(sa) > 1.0 and same and fewer and shared_
        and all(round(TD["fleets"]["per_endpoint"][e]["unseen|none"]["new:A100"]["blocked"] * 100) == 43 for e in ("E1", "E2", "E3", "E4"))
        and [round(min(TD["xfit_od"]["per_endpoint"][e]["union|seasonal"]["new:A100"]["blocked"] for e in ("E2", "E3", "E4")) * 100),
             round(max(TD["xfit_od"]["per_endpoint"][e]["union|seasonal"]["new:A100"]["blocked"] for e in ("E2", "E3", "E4")) * 100)] == [53, 84]
        and f"{TD['xfit_od']['per_endpoint']['E1']['union|seasonal']['new:A100']['blocked']*100:.1f}" == "3.9"
        and "The unseen filter covers new stacks of at least $k_{\\min}$ origins, and the test adds shared stacks and, in some configurations, smaller new ones. On the larger new stacks, as in E1's tenth-size botnet, the unseen filter without the test does as well under every trigger, with fewer false alarms and flash-crowd firings, since it names each such stack. Its false alarms as its own trigger cluster by day" in TEXN
        # only E1's tenth-size botnet puts k_min origins on each of its 25 stacks (90% of it on stacks)
        and 0.9 * 0.1 * no_[0] / 25 >= 5 and all(0.9 * 0.1 * x / 25 < 5 for x in no_[1:])
        and all(TD[r]["per_endpoint"][e][f"union|{g}"]["new:A100"]["blocked"] == TD[r]["per_endpoint"][e][f"unseen|{g}"]["new:A100"]["blocked"]
                for r in ("fleets",) for e in ("E1", "E2", "E3") for g in ("origins", "seasonal", "none"))
        and all(TD["fleets"]["per_endpoint"]["E4"][f"union|{g}"]["new:A100"]["blocked"] > TD["fleets"]["per_endpoint"]["E4"][f"unseen|{g}"]["new:A100"]["blocked"] + 0.3
                for g in ("origins", "seasonal", "none"))
        and all(TD["xfit_od"]["per_endpoint"][e][f"union|{g}"]["new:A100"]["blocked"] > TD["xfit_od"]["per_endpoint"][e][f"unseen|{g}"]["new:A100"]["blocked"] + 0.1
                for e in ("E2", "E3", "E4") for g in ("origins", "seasonal", "none"))
        and round(TD["xfit_od"]["per_endpoint"]["E1"]["union|none"]["new:A100"]["blocked"] * 100) == 58
        and round(TD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["new:A100"]["blocked"] * 100) == 43
        and "For new stacks too small for the filter, the cross-fitted beta-binomial adds on the small endpoints and, as its own trigger, on the busiest one too ($58\\%$ versus the filter's $43\\%$ of 100 attackers), while the binomial adds only on the single sign-on. Behind the seasonal gate, the cross-fitted beta-binomial stops $53$--$84\\%$ of 100 new-stack attackers on the small endpoints but only $3.9\\%$ on the busiest one" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: on new stacks the unseen filter matches every scope under every trigger with fewer misfires; only the test names shared stacks (binomial alone on E2-E4 {min(sa):.2f}--{max(sa):.2f}%)")
chk("App. E: the scope alone on shared stacks, E1", "With known fleets it stops $61.1\\%$ of the busiest endpoint's tenth-size botnet on shared stacks",
    TD["fleets"]["per_endpoint"]["E1"]["union|none"]["shared:x0.1"]["blocked"]*100, "With known fleets it stops {:.1f} of the busiest endpoint's tenth-size botnet on shared stacks")
gs = TD["base"]["all"]["gates_clean"]
chk("App. E: the seasonal gate alone", "The post hoc seasonal gate alone fires on $3.0\\%$ of clean test-day windows", gs["seasonal"]*100,
    "The post hoc seasonal gate alone fires on {:.1f} of clean test-day windows")
fs1, fo1 = FD["fleets"]["per_endpoint"]["E1"]["union|seasonal"]["new:x0.1"]["blocked"], FD["fleets"]["per_endpoint"]["E1"]["union|origins"]["new:x0.1"]["blocked"]
chk("App. E: the seasonal gate on E1 by day", "the binomial behind it stops $10.0$--$44.7\\%$ of E1's tenth-size botnet depending on the day.",
    (min(bs), max(bs)), "the binomial behind it stops {:.1f}--{:.1f} of E1's tenth-size botnet depending on the day.")
good = fo1 == 0 and f"{fs1*100:.1f}" == "15.3" and f"{gs['origins']*100:.1f}" == "3.0"
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: on the held-out day the origin gate stopped none of it ({fo1})")
S1 = PT["stealth_E1"]["fleets"]["fresh:x0.1"]; S2 = PT["stealth_E1"]["fleets"]["tail:x0.1"]
gt = [S1[f]["gate"] for f in tf]; rw = [S1[f]["recall_where_named"] for f in tf]
nm = [S[f]["named"] for S in (S1, S2) for f in tf + ["2026-09-25"]]
good = min(nm) == 1.0 and all(0.85 <= x <= 0.95 for x in rw) and f"depending on the day, the gate opens in ${min(gt)*100:.1f}$--${max(gt)*100:.0f}\\%$ of the windows of a botnet a tenth the size of the window" in TEX
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: E1 at 0.1x named in every window (new and shared stacks), gate {min(gt)*100:.1f}--{max(gt)*100:.1f}%")
e1f, e1o = TD["fleets"]["per_endpoint"]["E1"], TD["od"]["per_endpoint"]["E1"]
good = abs(e1f["union|origins"]["new:x0.1"]["blocked"] - sw1["new:M25:x0.1"]["blocked"]) < 1e-12
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} the sweep reproduces the E1 0.1x cell of the per-endpoint results (Table VI)")
sm = lambda r, k: [TD[r]["per_endpoint"][e][k]["new:x1"] for e in ("E2", "E3", "E4")]
b3 = [c["blocked"] for c in sm(*S3[0])]
o3 = [c for c in sm(*S3[1]) + sm(*S3[2])]
gx1 = [SW["fleets"][e]["new:M25:x1"]["gate"] for e in ("E2", "E3", "E4")]
good = (all(dA("fleets", e, "new") > no_[i + 1] for i, e in enumerate(("E2", "E3", "E4")))
        and f"{min(b3)*100:.0f}" == "2" and f"{max(b3)*100:.0f}" == "5")
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: small endpoints at 1x: gate {min(gx1)*100:.1f}--{max(gx1)*100:.1f}%, below the floors, {min(b3)*100:.1f}--{max(b3)*100:.1f}% stopped")
s100 = [SW["fleets"][e]["new:M25:A100"] for e in ("E2", "E3", "E4")]; h100 = [SW["fleets"][e]["shared:M25:A100"] for e in ("E2", "E3", "E4")]
good = (min(x["gate"] for x in s100) > 0.5 and f"{100 / no_[1]:.1f}" == "1.6" and f"{100 / no_[3]:.0f}" == "5"
        and f"On the small endpoints, 100 attackers equal 1.6 to 5 median windows and open the gate in ${min(x['gate'] for x in s100)*100:.0f}$--${max(x['gate'] for x in s100)*100:.0f}\\%$ of windows, leaving the floor as the main limit" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: small endpoints at 100 attackers: gate {min(x['gate'] for x in s100)*100:.0f}%+, new {[round(x['blocked']*100, 1) for x in s100]}, shared {[round(x['blocked']*100, 1) for x in h100]}")
chk("V-B: the binomial configuration, pooled", "stops $38.4\\%$ and $77.7\\%$ of 100 and 1\\,000 attackers on new stacks and $21.7\\%$ and $63.3\\%$ on shared ones",
    tuple(fz[x]["blocked"]*100 for x in ("new:A100", "new:A1000", "shared:A100", "shared:A1000")),
    "stops {:.1f} and {:.1f} of 100 and 1\\,000 attackers on new stacks and {:.1f} and {:.1f} on shared ones")
un = TD["base"]["all"]["unseen|origins"]
good = un["shared:A100"]["blocked"] == un["shared:A1000"]["blocked"] == 0
ok += good; bad += not good
chk("App. E: the unseen filter alone, the z-score and the beta-binomial at 100", "Of 100 attackers on new stacks, the unseen filter by itself behind the origin gate stops $29.4\\%$, the calibrated $z$-score $54.7\\%$ ($23.7\\%$ on shared ones) and the post hoc beta-binomial $59.8\\%$ ($40.5\\%$)",
    (un["new:A100"]["blocked"]*100, zc["new:A100"]["blocked"]*100, zc["shared:A100"]["blocked"]*100, ob["new:A100"]["blocked"]*100, ob["shared:A100"]["blocked"]*100),
    "Of 100 attackers on new stacks, the unseen filter by itself behind the origin gate stops {:.1f}, the calibrated z-score {:.1f} ({:.1f} on shared ones) and the post hoc beta-binomial {:.1f} ({:.1f})")
good = "figures the small endpoints dominate" in TEXN and fz["new:A100"]["blocked"] > 10 * sw1["new:M25:A100"]["blocked"]
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the pooled 100-attacker cell is carried by the small endpoints")
calib = [TD[r]["all"][k] for r, k in S3 + [("base", "enrichment|omega"), ("base", "union|origins")]]
good = all(x["attack_collateral_median"] == 0 for x in calib) and "the calibrated scopes block a median $0\\%$ of legitimate clients" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: calibrated scopes block a median 0% of legitimate clients in attack windows")
pe = [TD[r]["per_endpoint"][e][k] for r, k in S3 for e in ("E1", "E2", "E3", "E4")]
p90, amax = max(x["attack_collateral_p90"] for x in pe), max(x["attack_collateral_max"] for x in pe)
smax = max(TD[r]["per_endpoint"][e][k]["attack_collateral_max"] for r, k in S3 for e in ("E2", "E3", "E4"))
good = (round(p90 * 100) == 3 and f"{amax*100:.0f}" == "71" and smax == amax
        and "block a median $0\\%$ of legitimate clients and up to $71\\%$ in the worst window of a small endpoint" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: attack-window collateral p90 {p90*100:.1f}%, max {amax*100:.1f}% (on a small endpoint)")
adv = [fz[x]["blocked"] for x in ("adv:A100", "adv:A1000")]
e12 = [TD["fleets"]["per_endpoint"][e]["union|origins"][x]["blocked"] for e in ("E1", "E2") for x in ("adv:A100", "adv:A1000")]
chk("V-B: adversarial botnet, binomial configuration", "stops $7.0\\%$ and $23.8\\%$ of 100 and 1\\,000 attackers.",
    (adv[0]*100, adv[1]*100), "stops {:.1f} and {:.1f} of 100 and 1\\,000 attackers.")
ab2 = [FB["per_endpoint"][e][f]["fingerprints_above_limit"] for e in ("E1", "E2") for f in tf]
good = (max(e12) == 0 and [e for e in ("E1", "E2", "E3", "E4")] == sorted(PT["endpoints"]) and min(ab2) >= 23
        and f"{TD['fleets']['per_endpoint']['E4']['union|origins']['adv:A1000']['blocked']*100:.1f}" == "73.5"
        and "A botnet using the endpoint's 25 most common fingerprints, the boundary of the threat model, is therefore mostly missed: the configuration stops $7.0\\%$ and $23.8\\%$ of 100 and 1\\,000 attackers. It stops none on the two largest endpoints, where nearly all 25 exceed the limit, but $73.5\\%$ of 1\\,000 on the single sign-on" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the adversarial botnet is blocked 0% on E1 and E2 ({e12})")
CH = json.load(open(R + "ja4_churn.json"))
newd = [r["new_fingerprints"] for e in CH["per_endpoint"] for f, r in CH["per_endpoint"][e].items() if f in tf]
e1n = [CH["per_endpoint"]["E1"][f]["new_fingerprints"] for f in tf]
good = (min(newd) > 0 and max(e1n) == 345 and "Fingerprints absent from the profile appear daily but rarely concentrate" in TEXN
        and f"{CH['test_days']['windows_with_candidate_share']*100:.2f}" == "0.21" and "$0.21\\%$ of test-day windows" in TEXN
        and CH["test_days"]["windows"] == 5643)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: JA4 churn, new fingerprints every day (E1 up to {max(e1n)}), candidates in {CH['test_days']['windows_with_candidate_share']*100:.2f}% of windows")
chk("App. E: scope alone with fleets, all endpoints", "on $2.2\\%$ of pooled", TD["fleets"]["all"]["union|none"]["clean_rate"]*100, "on {:.1f} of pooled")
chk("App. E: scope alone without fleets", "versus $3.5\\%$ for the union without them", TD["base"]["all"]["union|none"]["clean_rate"]*100, "versus {:.1f} for the union without them")
chk("App. E: uncalibrated z-score, clean", "fires on $2.6\\%$ of clean", TD["base"]["all"]["zscore|omega"]["clean_rate"]*100, "fires on {:.1f} of clean")
chk("App. E: uncalibrated z-score, flash", "and $64.5\\%$ of 100-user flash crowds", TD["base"]["all"]["zscore|omega"]["flash100"]*100, "and {:.1f} of 100-user flash crowds")

print("== the held-out day (production_tables.json, compile_production_check_fresh.json)")
from scipy.stats import binom as _binom
pv = _binom.sf(ff_["clean_fires"] - 1, ff_["clean_windows"], fz["clean_fires"] / fz["clean_windows"])
gw = ff_["clean_gate_windows"]; pc2 = _binom.sf(1, gw, fz["clean_fires"] / fz["clean_gate_windows"])
good = (ff_["clean_fires"] == 2 and ff_["clean_windows"] == 1152 and pv >= 0.05 and gw == 3 and fz["clean_gate_windows"] == 168
        and f"{pc2:.3f}" == "0.003"
        and f"The held-out day gave the binomial configuration 2 false alarms in 1\\,152 clean windows, consistent with the test days' rate ($P = {pv:.2f}$). Its gate opened in only 3 of them, and the scope misfired in two, both on the web console, more often than the test days' 5 of 168 openings predict (post hoc, $P = 0.003$)." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: {ff_['clean_fires']} of {ff_['clean_windows']}, P = {pv:.3f}; gate opened in {gw}, scope misfired in 2 (P = {pc2:.4f} against 5 of 168)")
good = "Flash crowds of 100 users: share of windows where the configuration fires" in (HERE / "results" / "fresh_day_protocol.md").read_text()
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: the protocol fixes flash crowds of 100 users as a metric")
good = FD["fleets"]["per_endpoint"]["E2"]["union|origins"]["clean_fires"] == 2 and PT["endpoints"]["E2"] == "web console" \
    and "both on the web console" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: both false alarms on the web console")
ot = TD["overlap_frozen_zcal"]
good = ot["frozen"] == 5 and ot["both"] == 4
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} test days: the calibrated z-score shared {ot['both']} of the configuration's {ot['frozen']} false alarms")
o2 = TD["od"]["per_endpoint"]["E2"]["union|origins"]
good = (f"{o2['clean_rate']*100:.1f}" == "1.3" and f"{o2['flash1000']*100:.1f}" == "74.4"
        and "where $74.4\\%$ of 1\\,000-user crowds trigger it" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: the in-sample beta-binomial on the console, {o2['flash1000']*100:.1f}% of 1,000-user crowds")
cpf = json.load(open(R + "compile_production_check_fresh.json"))
good = cpf["origins_equal"] == cpf["net24_pairs_equal"] == cpf["windows"] == 1152 and "in every window of two production days, 1\\,152 windows each" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: compiled query equals the export in {cpf['origins_equal']}/{cpf['windows']} windows")
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
good = cc["ok"] and cc["omega_max_abs_diff"] == 0 and "verifies the compiled count query on generated sessions" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} compiled query reproduces Omega exactly on {cc['windows_x_endpoints']} "
      f"window-endpoints ({cc['sessions']} sessions): max diff {cc['omega_max_abs_diff']}")
x = cc["extension"]
good = (x["triples_added"] == 4 and x["code_lines_changed"] == 0 and x["omega_max_abs_diff"] == 0
        and x["relation"] in x["compiled_classes"] and "through four triples" in TEXN
        and "with no code change." in TEXN
        # the partition relation plus the class relations: three equality signals, a fourth added
        and len(cc["plan"]["classes"]) + 1 == 3 and len(x["compiled_classes"]) + 1 == 4
        and "also after a fourth equality signal is added as four triples" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} a new signal costs {x['triples_added']} triples and {x['code_lines_changed']} lines of code")
cp = json.load(open(R + "compile_production_check.json"))
good = (cp["origins_equal"] == cp["net24_pairs_equal"] == cp["windows"]
        and "in every window of two production days" in TEXN
        and cp["ja4_pairs_equal_without_waf_blocks"] == cp["windows_without_waf_blocks"]
        and cpf["ja4_pairs_equal_without_waf_blocks"] == cpf["windows_without_waf_blocks"] == cp["windows_without_waf_blocks"]
        and f"and JA4 pair counts in the {cp['windows_without_waf_blocks']} windows of each day on the endpoint where the WAF blocked no client" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} compiled query in the operator's store: origins and /24 pairs equal the export "
      f"in {cp['origins_equal']}/{cp['windows']} windows")
sv = json.load(open(R + "stix_validation.json"))
good = (sv["ok"] and sv["errors"] == 0 and sv["warnings"] == 0 and sv["strict_errors"] == 0
        and all(c["valid_strict"] for c in sv["chains"]) and "validator in strict mode" in TEXN
        and sv["bundles"] == 4 and "Exported bundles pass through the OASIS STIX~2.1 validator in strict mode, the reference TAXII~2.1 server" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} {sv['bundles']} STIX bundles valid, strict included "
      f"({sv['errors']} errors, {sv['warnings']} warnings, {sv['strict_errors']} strict errors)")
si = json.load(open(R + "stix_ingest.json")); tx, mi = si["taxii"], si["misp"]
good = (tx["accepted_all"] and all(tx["identical_by_type"][t] for t in ("indicator", "course-of-action",
                                                                     "relationship", "identity"))
        and not tx["identical_by_type"]["extension-definition"]
        and "the reference TAXII~2.1 server (medallion 3.0.0) and MISP's importer (misp-stix 2026.9.16). The server returns them unchanged except for the extension definition it fails to serve" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} TAXII 2.1: accepted, identical by type {tx['identical_by_type']}")
good = (mi["fingerprints_kept"] == 0 and mi["fingerprints_in_scope"] > 0 and mi["endpoint_kept_where_scoped"]
        and mi["course_of_action_kept"] and "MISP's importer drops the fingerprints" in TEXN
        and "an extension the importer does not map to MISP's own JA4 object." in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} MISP import: CoA and endpoint kept, fingerprints kept {mi['fingerprints_kept']}/{mi['fingerprints_in_scope']}")
print("== known-fleet profile (fleet_profile.json)")
fp = json.load(open(R + "fleet_profile.json"))
sh = float(fp["chosen_share"])
good = (fp["protocol"]["design_days"] == 3 and fp["protocol"]["held_out_days"] == 2
        and f"at least ${sh*100:.0f}\\%$ of calibration windows" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} share chosen on 3 design days: {sh}, eligible {fp['eligible']}")
d0 = fp["design"]; good = all(d0[s]["false_alarms"] > d0["base"]["false_alarms"] for s in d0 if s not in ("base", fp["chosen_share"]))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} every other share adds false alarms on design days")
d05, d5 = d0["0.005"], d0["0.05"]
ec = lambda r: r["false_alarms"] / r["clean_windows"] * r["collateral_median"]
good = (round(ec(d05) * 100, 4) == 0.0028 and round(ec(d5) * 100, 3) == 0.070 and round(ec(d5) / ec(d05)) == 25
        and round(d05["fresh:A100"] * 100, 1) == 44.6 and round(d5["fresh:A100"] * 100, 1) == 30.9
        and "Using the rate times the median collateral, a rougher measure than the mean, the $0.5\\%$ share blocked about 25 times fewer legitimate clients per clean window on those days ($0.0028\\%$ versus $0.070\\%$). It also stopped more of a 100-attacker botnet on new stacks ($44.6\\%$ versus $30.9\\%$)" in TEXN
        and fp["eligible"] == ["0.05"] and len(d0) - 1 == 4
        and "Of four shares, each added to the base rule, only $5\\%$ had no more false alarms than the rule alone on the first three test days, although $0.5\\%$ blocked about 25 times fewer legitimate clients and more of a 100-attacker botnet" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E, Table II: by rate x median collateral the 0.5% share is {ec(d5)/ec(d05):.1f}x lighter ({ec(d05)*100:.4f}% against {ec(d5)*100:.3f}%)")
fe = fp["fleets_per_endpoint"]["E1"]
good = sorted(set(fe["fleets"])) == [5, 6] and "five or six known fleets" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} E1 known fleets per fold: {fe['fleets']}")
lv = round(math.log10(float(np.median(fe["level"]))))
good = f"to about $10^{{{lv}}}$" in TEXN and round(math.log10(E["E1"]["scope_level_median"])) == -60
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} E1 level rises from 10^-60 to 10^{lv}")
good = (fp["eligible"] == [fp["chosen_share"]] and len(fp["design"]) == 5
        and f"only one whose false alarms did not exceed those of the rule alone ({d0[fp['chosen_share']]['false_alarms']} versus {d0['base']['false_alarms']}, the others {min(v['false_alarms'] for s, v in d0.items() if s not in ('base', fp['chosen_share']))} to {max(v['false_alarms'] for s, v in d0.items() if s not in ('base', fp['chosen_share']))})" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} only one of four shares kept false alarms at or below the base rule's")
print("== generator: window sweep and the vocabulary-tail variant")
print("== cross-fitted calibration (production_tables.json: xfit, xfit_fleets, xfit_od)")
xb, xo, xz = TD["xfit_fleets"]["all"]["union|origins"], TD["xfit_od"]["all"]["union|origins"], TD["xfit"]["all"]["zcal|origins"]
xa = {"bin": TD["xfit_fleets"]["all"]["union|none"]["clean_rate"], "z": TD["xfit"]["all"]["zcal|none"]["clean_rate"],
      "z_E2": TD["xfit"]["per_endpoint"]["E2"]["zcal|none"]["clean_rate"], "beta": TD["xfit_od"]["all"]["union|none"]["clean_rate"],
      "beta_E2": TD["xfit_od"]["per_endpoint"]["E2"]["union|none"]["clean_rate"], "beta_fresh": FD["xfit_od"]["all"]["union|none"]["clean_rate"]}
good = (xb["clean_fires"] == 6 and fz["clean_fires"] == 5 and f"{xa['bin']*100:.1f}" == "1.9"
        and "the binomial configuration barely changes, with 6 false alarms versus 5" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: binomial scope alone {xa['bin']*100:.2f}%, {xb['clean_fires']} false alarms versus {fz['clean_fires']}")
good = abs(xb["new:A100"]["blocked"] - fz["new:A100"]["blocked"]) < 0.03
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: the binomial stops {xb['new:A100']['blocked']*100:.1f}% against {fz['new:A100']['blocked']*100:.1f}% of 100 attackers")
good = f"{xa['z']*100:.1f}" == "2.5" and "the calibrated $z$-score loses its lead over the binomial" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: the z-score alone fires in {xa['z']*100:.2f}% (Table IV), its lead was in-sample")
chk("cross-fit: beta-binomial alone", "only the cross-fitted beta-binomial nearly meets its budget ($1.1\\%$", xa["beta"]*100, "only the cross-fitted beta-binomial nearly meets its budget ({:.1f}")
chk("App. E: cross-fitted beta-binomial on the held-out day", "its scope alone fires in $1.2\\%$ of the held-out day's windows", xa["beta_fresh"]*100,
    "its scope alone fires in {:.1f} of the held-out day's windows")
good = min(xa["beta"], xa["bin"], xa["z"]) == xa["beta"] and "Of the calibrated scopes used alone, only the cross-fitted beta-binomial nearly meets its budget ($1.1\\%$, Fig.~\\ref{fig:operating})" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: only the beta-binomial comes near its 1% target")
xl = [FL["xfit_od"][e][f]["log10_level"] for e in ("E1", "E2", "E3", "E4") for f in tf]
good = (max(xl) < -2 + 1e-9 and round(min(xl)) == -17 and round(max(xl)) == -2
        and "The beta-binomial's levels then fall to $10^{-17}$--$10^{-2}$" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: beta-binomial levels 10^{min(xl):.1f}..10^{max(xl):.1f}, {xo['clean_fires']} false alarms")
xk = [FL["xfit_od_fleets"]["E1"][f]["known_fleets"] for f in tf]
good = xk.count(1) == 3 and xk.count(0) == 2 and max(kf["od_fleets"]) == 0 and "and one fingerprint would be a known fleet on E1 on three of five days, though none qualifies in sample." in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: E1 known fleets under the beta-binomial {xk}")

xsS = [exactW("xfit_od", e) for e in ("E2", "E3", "E4")]
xnS = [dF("xfit_od", e, "new") for e in ("E2", "E3", "E4")]
good = ([round(x) for x in xsS] == [3, 3, 4] and [round(x) for x in xnS] == [2, 3, 3]
        and "On the three small endpoints the cross-fitted beta-binomial names shared stacks only past 3 to 4 median windows and new stacks from 2 to 3, so for smaller botnets the fallback is a rate limit or a challenge to every client" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: the recommended scope's floors on E2-E4, shared {[round(x, 2) for x in xsS]} and new {[round(x, 2) for x in xnS]} median windows")
shB = [dA("xfit_fleets", e, "shared") for e in ("E1", "E2", "E3", "E4")]; shO = [exact("xfit_od", e) for e in ("E1", "E2", "E3", "E4")]
good = (xo["clean_fires"] == xb["clean_fires"] and xo["clean_collateral_median"] < xb["clean_collateral_median"] and xo["flash1000"] < xb["flash1000"]
        and all(o < b for o, b in zip(shO, shB)) and xz["new:A100"]["blocked"] < xb["new:A100"]["blocked"] + 0.05)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: cross-fitted, the beta-binomial matches the binomial's false alarms with lower shared floors {shO} vs {shB}")
good = ("A first cross-fitting design, calibrated only on the last calibration day, was dropped" in TEXN
        and "The second, built after the held-out day was read (Section~\\ref{sec:posthoc}), is a \\textbf{beta-binomial background}" in TEXN
        and "\\textit{Cross-fitting}, built post hoc, judges each calibration day, like a test day, against a profile of the other days" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the dropped cross-fit design and the post hoc status are disclosed")
print("== the WAF's verdicts (waf_labels.json)")
WL = json.load(open(R + "waf_labels.json")); WC, WA = WL["clean_profile"]["test_days"], WL["all_profile"]["test_days"]
good = (WL["clean_profile"]["check"]["zscore_mismatches"] == 0 == WL["all_profile"]["check"]["zscore_mismatches"]
        and not WC["E1"]["waf_clients"] and all(WC[e]["windows_with_waf"] == WC[e]["windows"] for e in ("E2", "E3", "E4")))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF: z-score recomputed with 0 mismatches under both profiles; blocks in every window of E2-E4, none on E1")
chk("WAF: blocked share of the window", "a median $9$--$63\\%$ of each window's clients on E2 to E4, and none on E1",
    (min(WC[e]["waf_share_median"] for e in ("E2", "E3", "E4"))*100, max(WC[e]["waf_share_median"] for e in ("E2", "E3", "E4"))*100),
    "a median {:.0f}--{:.0f} of each window's clients on E2 to E4, and none on E1")
CF = ("binomial", "beta-binomial", "z-score")
pc = [WC[e]["scores"][c]["precision"] for e in ("E3", "E4") for c in CF]
chk("WAF, profile without blocked clients: precision", "$84$--$99\\%$ of the clients the scopes would block on the full traffic of the API and single sign-on were also blocked by the WAF",
    (min(pc)*100, max(pc)*100), "{:.0f}--{:.0f} of the clients the scopes would block on the full traffic of the API and single sign-on were also blocked by the WAF")
fl_ = WL["clean_profile"]["implied_precision_floor"]
chk("WAF: the implied precision floor", "only if $70$--$88\\%$ of its clients were blocked", (min(fl_.values())*100, max(fl_.values())*100),
    "only if {:.0f}--{:.0f} of its clients were blocked")
pa = [WA[e]["scores"][c]["precision"] for e in ("E2", "E3", "E4") for c in CF]
br = [WA[e]["base_rate"] for e in ("E2", "E3", "E4")]
good = (f"{min(pa)*100:.1f}" == "0.4" and f"{max(pa)*100:.0f}" == "33"
        and max(WA[e]["scores"][c]["lift"] for e in ("E2", "E3", "E4") for c in CF) < 1
        and f"{min(br)*100:.0f}" == "10" and f"{max(br)*100:.0f}" == "63"
        and "With a profile of all clients, only $0.4$--$33\\%$ of the clients the three calibrated scopes would block were also blocked by the WAF, below a random pick ($10$--$63\\%$) on every endpoint" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF, all-client profile, E2-E4: precision {min(pa)*100:.1f}--{max(pa)*100:.1f}% vs random {min(br)*100:.1f}--{max(br)*100:.1f}%, lift below 1 everywhere")
dets = [WA[e]["surges"]["detected"][c] for e in ("E3", "E4") for c in CF]
chance = [WA[e]["surges"]["expected_by_chance"][c] for e in ("E3", "E4") for c in CF]
eps_ = WA["E3"]["surges"]["episodes"] + WA["E4"]["surges"]["episodes"]
good = (min(dets) == 0 and max(dets) == 2 and eps_ == 38 and f"{max(chance):.1f}" == "0.5"
        and "On the API and single sign-on, the scopes catch at most 2 of the WAF's 38 surges (Appendix~\\ref{app:window})" in TEXN
        and all(json.load(open(R + "waf_labels.json"))["all_profile"]["test_days"]["E2"]["surges"]["scores"][s]["recall"] < 0.01 for s in ("binomial", "beta-binomial", "z-score"))
        and "With a profile of all clients, the scopes catch the WAF's surges clearly above chance only on the console, and there with under $1\\%$ of blocked clients" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF surges on E3+E4: {eps_} episodes, detected {min(dets)}--{max(dets)}, chance at most {max(chance):.2f}")
S2 = WA["E2"]["surges"]
e2d = [S2["detected"][c] for c in ("beta-binomial", "z-score")]
e2c = [S2["expected_by_chance"][c] for c in ("beta-binomial", "z-score")]
e2r = [S2["scores"][c]["recall"] for c in ("beta-binomial", "z-score")]
good = (e2d == [5, 5] and S2["detected"]["binomial"] == 0 and S2["episodes"] == 33 and max(e2c) < 1 and max(e2r) < 0.01
        and "clearly above chance only on the console, and there with under $1\\%$ of blocked clients" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF surges on E2: detected {e2d} of {S2['episodes']}, chance {[round(x, 2) for x in e2c]}, recall {[round(x*100, 2) for x in e2r]}%")
mr = [WC[e]["scores"]["modal"]["recall"] for e in ("E2", "E3", "E4")]; nc = [WC[e]["ceiling"]["no_clean"] for e in ("E2", "E3", "E4")]
good = (round(min(mr) * 100) == 13 and round(max(mr) * 100) == 55 and max(nc) < 0.5
        and "Most clients blocked by the WAF shared fingerprints with unblocked clients." in TEXN
        and "This WAF's verdicts cannot serve as labels." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF: blocked clients on common fingerprints (modal {[round(x*100) for x in mr]}%, no unblocked peer {[round(x*100) for x in nc]}%), negative result both ways")
good = "\\textbf{This WAF's verdicts cannot serve as labels.}" in TEX   # left the abstract in round 31
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: the WAF's verdicts cannot label floods")
print("== methodology and calibration text")
dd = json.load(open(HERE.parent / "sprint-2" / "distributions" / "session_duration.json"))["count"]
rr = json.load(open(HERE.parent / "sprint-2" / "distributions" / "session_requests.json"))["count"]
ks = json.load(open(HERE.parent / "sprint-2" / "results" / "ks_validation.json"))["features"]
good = (dd == 40351 and rr == 322658 and f"{ks['n_requests']['ks_D']:.3f}" == "0.002" and f"{ks['duration_s']['ks_D']:.3f}" == "0.003"
        and "Request counts come from all $322\\,658$ benign CICIDS2017 sessions and durations from the $40\\,351$ with two or more requests" in TEXN
        and "distances of $D = 0.002$ and $0.003$ between generated and real sessions only check the sampler" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} IV: request counts from {rr}, durations from {dd} sessions, KS D {ks['n_requests']['ks_D']} and {ks['duration_s']['ks_D']}")
good = f"{0.9 / 0.384:.1f}" == "2.3" and "With the measured $p_1 = 38.4\\%$" in TEXN and "only while $M < 2.3$" in TEXN and "the most common carrying $38.4\\%$ of requests" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-C: the modal fingerprint is an attack stack only while M < 0.9/0.384 = {0.9/0.384:.2f}")
import subprocess
proto = (HERE / "results" / "fresh_day_protocol.md").read_text()
t0 = pd.Timestamp(re.search(r"Written (\S+Z)", proto).group(1))
t1 = pd.Timestamp(subprocess.run(["git", "log", "--diff-filter=A", "--format=%aI", "--", "results/fresh_day_protocol.md"],
                                 cwd=HERE, capture_output=True, text=True).stdout.split()[-1]).tz_convert("UTC")
hrs = (t1 - t0).total_seconds() / 3600
good = round(hrs) == 17 and "committed 17 hours after the stated time," in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. F: protocol written {t0}, committed {t1} ({hrs:.1f} h later)")
good = (HERE.parents[1] / "LICENSE").read_text().startswith("MIT License") and "under the MIT license" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. F: MIT license in the repository")
print("== abstract, discussion and conclusion")
ab = re.sub(r"\s+", " ", TEX[TEX.index("\\begin{abstract}"):TEX.index("\\end{abstract}")])
def abs_chk(label, phrase, value, fmt_):
    global ok, bad
    got = fmt_.format(*value) if isinstance(value, tuple) else fmt_.format(value)
    good = phrase in ab and got == phrase.replace("\\%", "").replace("$", "")
    ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} abstract: {label:44s} phrase={phrase!r} data={got}")
abs_chk("modal blocks none, hits legitimate traffic", "blocks $39\\%$ of legitimate traffic and no attacker once the botnet spans five TLS stacks",
        us("original", 5, 0, "modal", "fpr")*100, "blocks {:.0f} of legitimate traffic and no attacker once the botnet spans five TLS stacks")
good = us("original", 5, 0, "modal", "recall") == 0; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: the modal scope blocks no attacker at five stacks")
pr = [us("original", s, 0, "enrichment", "recall") for s in (1, 5, 25)]
pf = [us("original", s, 0, "enrichment", "fpr") for s in (1, 5, 25)]
good = all(round(x * 100) == 90 for x in pr) and max(pf) == 0 and "The test blocks $90\\%$ of a botnet on up to 25 new stacks with no observed collateral" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the binomial test blocks 90% up to 25 stacks at zero FPR")
good = (fmt(fz["clean_rate"]) == "0.1" and 0.30 <= fz["clean_collateral_median"] <= 0.36 and alone["bin"] > 0.01 and alone["gate"] > 0.01
        and "the test and its volume trigger misfire together in $0.1\\%$ of attack-free windows on the days used to choose them, though each alone exceeds its $1\\%$ budget. These misfires block a median third of the window's clients" in ab)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: the binomial configuration misfires on {fz['clean_rate']*100:.2f}%, each misfire blocking a median {fz['clean_collateral_median']*100:.1f}%")
grows = all(dA("fleets", e, k, 5) < dA("fleets", e, k, 25) < dA("fleets", e, k, 100) for e in ("E1", "E2", "E3", "E4") for k in ("new", "shared"))
good = grows and "Calibration has a price: legitimate client fleets raise a floor" in ab and "legitimate fleets raise a calibration floor" in TEXN and "The floor grows with the number of stacks" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract, V-B: every floor grows from 5 to 25 to 100 stacks")
# the floor's values left the abstract in round 33; V-B states them
good = (f"{shF*100:.0f}" == "8" and f"{min(shS):.0f}" == "4" and f"{max(shS):.0f}" == "19"
        and "is singled out only when large" in ab
        and "A typical stack is then named only past 254 attackers on the busiest endpoint, $8\\%$ of its window, and past 4 to 19 median windows on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract, V-B: the floor on shared stacks, {shF*100:.0f}% of E1's window and {min(shS):.0f} to {max(shS):.0f} windows elsewhere")
good = min(share) > 0.5 and "The 4 to 28 most common fingerprints of each endpoint, which carry" in TEXN   # left the abstract in round 31
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: never named on the fingerprints carrying most origins ({min(share)*100:.0f}%+)")
good = (round(sw1["new:M25:x0.1"]["blocked"] * 100) == 12 and sw1["new:M25:x0.1"]["gate"] < 0.2
        and round(TD["fleets"]["per_endpoint"]["E1"]["union|none"]["new:x0.1"]["blocked"] * 100) == 90
        and "On the busiest endpoint the trigger lets most of a small injected botnet through" in ab)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the trigger lets most of a small botnet through ({sw1['new:M25:x0.1']['gate']*100:.1f}%), {sw1['new:M25:x0.1']['blocked']*100:.1f}% stopped")
# the held-out block (production_tables_block.json): 14 days after the held-out day
PB = json.load(open(R + "production_tables_block.json")); BD = PB["test_days"]
BR = json.load(open(R + "block_report.json"))
bz = BD["fleets"]["all"]["union|origins"]
un1 = BD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["new:x0.1"]["blocked"]
unB = max(BD["fleets"]["per_endpoint"][e]["unseen|none"]["clean_rate"] for e in ("E1", "E2", "E3", "E4"))
x4 = {e: BD["xfit_od"]["per_endpoint"][e]["union|seasonal"] for e in ("E1", "E2", "E3", "E4")}
nblk = len(bz["clean_fires_by_fold"])
good = (nblk == 14 and PB["folds"]["test"] == 14 and 8 + 1 + nblk == 23 and 1 + nblk == 15
        and 1.8 <= bz["clean_rate"] / fz["clean_rate"] <= 2.4 and bz["clean_ci95"][1] <= 0.01
        and "on generated campaigns and 23 days of a CDN operator's traffic" in ab
        and "On 14 later pre-specified days their rate doubles, still within budget." in ab)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: 8 + 1 + {nblk} = 23 days; on the block the rate is {bz['clean_rate']/fz['clean_rate']:.2f}x the test days', upper bound {bz['clean_ci95'][1]*100:.2f}%")
good = (round(un1 * 100) == 90 and unB == 0 and all(v["clean_rate"] <= 0.01 for v in x4.values())
        and x4["E1"]["shared:x0.1"]["blocked"] > 0.1 and bz["clean_fires"] > 0
        and BD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["shared:x0.1"]["blocked"] == 0
        and "Post hoc triggers recover part of that loss on those days." in ab)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: on the block the unseen filter as its own trigger stops {un1*100:.1f}% of E1's tenth-size botnet with no misfire; the seasonal arm stops {x4['E1']['shared:x0.1']['blocked']*100:.1f}% on shared stacks")
good = (cp["origins_equal"] == cp["windows"] and cpf["origins_equal"] == cpf["windows"] and cp["net24_pairs_equal"] == cp["windows"]
        and "The compiled query reproduced exported address and /24-pair counts in every window of two production days" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: the compiled query reproduces origins and /24 pairs")
good = (mi["fingerprints_kept"] == 0 and mi["fingerprints_in_scope"] > 0
        and "We specify the filter and its counts in an OWL ontology, since no exchange standard we examined expresses it in its core vocabulary" in ab
        and "An OWL ontology specifies the counts the decision reads and the scope it exports, and the log store's query is compiled from it" in TEXN
        and "No exchange standard we examined expresses this JA4 filter in its core vocabulary" in TEXN
        and "Among the standards we examined, STIX~2.1, DOTS and Flowspec lack a JA4 property in their core vocabularies, while OCSF records JA4 fingerprints in network events and in the evidence of findings~\\cite{ocsf2025schema} but defines no filter or remediation over them" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract, contribution (iii), VI: JA4 only in a STIX extension, dropped by MISP's importer; OCSF records it with no filter (external, checked on its schema)")
e1r_ = [dF(r, "E1", k) for r in ("fleets", "od", "xfit_fleets", "xfit_od") for k in ("new", "shared")]
good = (max(e1r_) < 0.1
        and "A typical stack is then named only past 254 attackers on the busiest endpoint, $8\\%$ of its window" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: every E1 floor under a tenth of the window ({[round(x*100, 1) for x in e1r_]}%)")
x4a, b3a = BD["xfit_od"]["all"]["union|seasonal"], BD["fleets"]["all"]["unseen|none"]
fbd = BD["fleets"]["all"]["union|origins"]["clean_fires_by_fold"]
from datetime import date as _date
wk = sum(v for d, v in fbd.items() if _date.fromisoformat(d).weekday() < 5)
x4e1 = sorted(x4["E1"]["clean_fires_by_fold"].values(), reverse=True)
good = (x4a["clean_fires"] == 20 and bz["clean_fires"] == 31
        and x4a["new:A100"]["blocked"] > bz["new:A100"]["blocked"] and x4a["shared:A100"]["blocked"] > bz["shared:A100"]["blocked"]
        and 0.30 <= x4a["flash1000"] <= 0.36 and x4a["flash1000_collateral_median"] < 0.05 and 0.63 <= x4a["clean_collateral_median"] <= 0.70
        and x4["E1"]["new:x0.1"]["blocked"] < 0.25 * un1 and BD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["clean_fires"] == 0
        and wk == 30 and sum(x4e1[:2]) == 12 and sum(x4e1) == 14
        and x4["E1"]["clean_fires"] == 14 and BD["fleets"]["per_endpoint"]["E1"]["union|origins"]["clean_fires"] == 0
        and f"{(x4a['clean_gate_windows'] - x4a['clean_fires']) / x4a['clean_windows'] * 100:.1f}" == "1.5"
        and BD["base"]["all"]["zcal|origins"]["clean_fires"] == x4a["clean_fires"] and BD["base"]["all"]["zcal|origins"]["flash1000"] < x4a["flash1000"]
        and BD["base"]["all"]["zcal|origins"]["new:A100"]["blocked"] < x4a["new:A100"]["blocked"] and BD["base"]["all"]["zcal|origins"]["shared:A100"]["blocked"] < x4a["shared:A100"]["blocked"]
        and "\\1~\\textit{Now} our candidate is the cross-fitted beta-binomial behind the seasonal gate, with the fallback below its floor. It was built post hoc, but the comparison fixed in advance preferred it on every endpoint. On the same days it misfired in fewer windows than the binomial configuration (20 versus 31, though 14 versus none on the busiest endpoint) and stopped more of 100 attackers. Crowds of 1\\,000 users trigger it in a third of windows, with light filters, and its misfires block a median two thirds of the window's clients. The fallback then acts on its gate's other clean openings, $1.5\\%$ of windows. The calibrated $z$-score misfired as often and fired on fewer crowds, but stopped less. On the busiest endpoint the beta-binomial gives up most new-stack detection, which the unseen filter as its own trigger keeps with no false alarm. Running both there is untested. \\2~\\textit{Next}, a longer evaluation, since no later day has tested this choice: the binomial configuration misfires on weekdays, which a gate calibrated by day of the week may absorb, and the beta-binomial's misfires cluster on two days of the busiest endpoint." in TEXN
        and all(round(PT[blk][run]["per_endpoint"][e][sc]["new:A1000"]["blocked"] * 100, 1) == 90.0
                for blk in ("test_days", "fresh_day") for run in ("fleets", "xfit_od") for e in ("E2", "E3", "E4")
                for sc in ("union|origins", "union|seasonal", "union|none", "unseen|origins", "unseen|seasonal", "unseen|none"))
        and "On each small endpoint, every scope in Table~\\ref{tab:triggers} stops $90.0\\%$ of 1\\,000 attackers on new stacks under every trigger, on both test and held-out days" in TEXN
        and all(0.13 <= PT["sweep"]["fleets"][e]["new:M25:x1"]["gate"] <= 0.33 for e in ("E2", "E3", "E4"))
        and "A botnet of one median window opens it in only $14$--$33\\%$." in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} VI: the seasonal arm on the block, {x4a['clean_fires']} misfires vs {bz['clean_fires']}, crowds {x4a['flash1000']*100:.1f}%, misfires {x4a['clean_collateral_median']*100:.1f}%; binomial misfires on weekdays {wk} of {bz['clean_fires']}; arm's E1 misfires by day {x4e1[:3]}")
bq = bz["clean_fires"] / bz["clean_gate_windows"]
# "because": the joint rate is the gate's rate times the scope's misfires once open; the gate
# opened about half as often, so the doubling comes from the scope
gq = (bz["clean_gate_windows"] / bz["clean_windows"]) / (fz["clean_gate_windows"] / fz["clean_windows"])
cq = (bz["clean_fires"] / bz["clean_gate_windows"]) / (fz["clean_fires"] / fz["clean_gate_windows"])
good = (f"{alone['bin']*100:.1f}" == "2.2" and f"{bq*100:.0f}" == "13" and bz["clean_ci95"][1] <= 0.01
        and 0.4 <= gq <= 0.6 and cq > 4 and abs(gq * cq - bz["clean_rate"] / fz["clean_rate"]) < 1e-9
        and "The binomial configuration's false alarms stay at $0.1\\%$ of clean windows on the days used to choose it, though its scope alone exceeds its budget there ($2.2\\%$). On 14 later pre-specified days they double, still within budget, because the scope misfires in $13\\%$ of gate openings. On those days two of three post hoc configurations held their budget. On the busiest endpoint, the gate lets most of a small botnet through" in TEXN
        and "is named by the binomial test only past $8\\%$ of the busiest endpoint's window and 4 to 19 median windows on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: the binomial configuration's rate doubles on the block, scope misfires in {bq*100:.1f}% of gate openings")
good = (round(un1 * 100) == 90 and unB == 0 and all(v["clean_rate"] <= 0.01 for v in x4.values())
        and x4["E1"]["shared:x0.1"]["blocked"] > 0 == BD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["shared:x0.1"]["blocked"]
        and x4["E1"]["new:x0.1"]["blocked"] < 0.5 * un1
        and not BR["m2"]["5"]["E1"]["within"]
        and "On the busiest endpoint, the gate lets most of a small botnet through. The unseen filter as its own trigger stops $90\\%$ of it on new stacks with no false alarm, and there a cross-fitted beta-binomial behind a seasonal gate, preferred on every endpoint, adds shared stacks but loses most new ones. Next come weekday calibration, HTTP/2 attacks and a captured stealthy campaign" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: on the block, the unseen filter alone {un1*100:.1f}% with no misfire; the seasonal arm {x4['E1']['shared:x0.1']['blocked']*100:.1f}% on shared, {x4['E1']['new:x0.1']['blocked']*100:.1f}% on new")
good = ("so no attack label is required." in TEXN and "The scope is evaluated offline, behind the operator's WAF, so the profiles and floors describe the clients the WAF lets through" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-C, IV-A: no attack label; the profile excludes WAF-blocked clients, the scope runs behind the WAF")
SDV = json.load(open(R + "symbolic_detector.json"))["aggregate"]["1.5:25:1"]
good = f"{SDV['rf_recall_fpr1']*100:.1f}" == "23.4" and "The modal fingerprint blocks $3.6\\%$ at $39.0\\%$, and the learned model $23.4\\%$ at $1\\%$ false positives" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-A: the learned model on the adversarial botnet at 1% FPR, {SDV['rf_recall_fpr1']*100:.1f}%")
print("== round 18: the trigger table, flash crowds, floors by stack count")
def trow(run, scope, gate):
    k = f"{scope}|{gate}"
    t1, f1 = TD[run]["per_endpoint"]["E1"][k], FD[run]["per_endpoint"]["E1"][k]
    to = max(TD[run]["per_endpoint"][e][k]["clean_rate"] for e in ("E2", "E3", "E4"))
    fo = max(FD[run]["per_endpoint"][e][k]["clean_rate"] for e in ("E2", "E3", "E4"))
    cm = TD[run]["all"][k]["clean_collateral_median"]
    return [f"{t1['clean_rate']*100:.2f}", f"{f1['clean_rate']*100:.2f}", f"{to*100:.2f}", f"{fo*100:.2f}",
            f"{t1['new:x0.1']['blocked']*100:.1f}", f"{f1['new:x0.1']['blocked']*100:.1f}", f"{t1['shared:x0.1']['blocked']*100:.1f}",
            f"{TD[run]['all'][k]['flash1000']*100:.1f}", "--" if cm is None else f"{cm*100:.1f}"]
i0 = TEX.index("\\label{tab:triggers}"); tabT = TEX[i0:TEX.index("\\end{table}", i0)]
rowsT = [ln for ln in tabT.splitlines() if ln.strip().endswith("\\\\") and ("binomial" in ln or "beta-bin" in ln or "unseen" in ln)]
gotT = [[c.strip().rstrip("\\").strip() for c in ln.split("&")[2:]] for ln in rowsT]
expT = [trow(r, s, g) for g in ("origins", "seasonal", "none") for r, s in (("fleets", "union"), ("xfit_od", "union"), ("fleets", "unseen"))]
good = (gotT == expT and [ln.split("&")[0].strip() for ln in rowsT[::3]] == ["Origin gate", "Seasonal gate$^{*}$", "No gate$^{*}$"]
        and all(trow("fleets", "unseen", g) == trow("xfit_od", "unseen", g) for g in ("origins", "seasonal", "none")))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} Table VI: 9 rows x 9 cells from production_tables.json" + ("" if good else f" got={gotT} exp={expT}"))
g1 = TD["fleets"]["per_endpoint"]["E1"]["gates_clean"]["origins"]
chk("V-B: the distinct-origin gate alone, pooled and on E1", "and the distinct-origin gate alone fires in $3.0\\%$, reaching $5.4\\%$ on the busiest endpoint",
    (TD["fleets"]["all"]["gates_clean"]["origins"]*100, g1*100), "and the distinct-origin gate alone fires in {:.1f}, reaching {:.1f} on the busiest endpoint")
f5, f100 = dA("fleets", "E1", "shared", 5), dA("fleets", "E1", "shared", 100)
r5, r100 = dF("fleets", "E1", "shared", 5), dF("fleets", "E1", "shared", 100)
w5 = [dF("fleets", e, "shared", 5) for e in ("E2", "E3", "E4")]; w100 = [dF("fleets", e, "shared", 100) for e in ("E2", "E3", "E4")]
fM = {M: [dA("fleets", e, "shared", M) for e in ("E1", "E2", "E3", "E4")] for M in (5, 100)}
good = ((f5, f100) == (50, 1026) and round(r5 * 100) == 2 and round(r100 * 100) == 34
        and fM[5] == [50, 164, 28, 17] and fM[100] == [1026, 6158, 1017, 454]
        and "The floor grows with the number of stacks, from $2\\%$ of the busiest window at 5 stacks to $34\\%$ at 100" in TEXN
        and "the shared-stack floor for 5 and 100 stacks is 50 and 1\\,026 attackers on E1, 164 and 6\\,158 on E2, 28 and 1\\,017 on E3 and 17 and 454 on E4" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared floors at 5 and 100 stacks: E1 {f5} and {f100} ({r5*100:.1f}% and {r100*100:.1f}%), small {min(w5):.1f}--{max(w5):.1f} and {min(w100):.1f}--{max(w100):.1f} windows")
FPa = json.load(open(R + "fleet_profile.json"))["fleets_per_endpoint"]
FPj, FP3 = FPa["E1"], FPa["E3"]
# known fleets on the busiest endpoint (5-6, about 7% of its profile) and the API (1-2 on four
# of the five test days, at most 7%); the console and single sign-on exempt none
good = (all(0.065 <= s <= 0.075 for s in FPj["profile_share"]) and set(FPj["fleets"]) <= {5, 6}
        and max(FP3["profile_share"]) <= 0.075 and sum(1 for k in FP3["fleets"] if k) == 4
        and all(k == 0 for e in ("E2", "E4") for k in FPa[e]["fleets"])
        and "allow-list for the busiest endpoint and the API, covering fingerprints that together carry up to about $7\\%$ of their profiles" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D: known fleets carry {min(FPj['profile_share'])*100:.1f}--{max(FPj['profile_share'])*100:.1f}% of E1's profile and at most {max(FP3['profile_share'])*100:.1f}% of the API's")
good = "$1.2\\%$ for $M = 25$ and $\\rho = 3$" in TEXN and "and there the ratio sets a harder limit" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D: the ratio limit is stated for rho = 3")
x36 = st_.median(x["beta_binomial"] for x in bB("xfit_od", "E1", "ranks_36_100", ""))
good = (x36 == 949 and b36 == 743 and o36 == 480
        and [st_.median(x["beta_binomial"] for x in bB("xfit_od", e, "ranks_36_100", "")) for e in ("E2", "E3", "E4")] == [509, 255, 84]
        and [st_.median(x["binomial"] for x in bB("fleets", e, "ranks_36_100", "")) for e in ("E2", "E3", "E4")] == [1898, 227, 84]
        and "the cross-fitted beta-binomial's floor on those ranks is also higher on the API (255 versus 227), equal on the single sign-on and lower on the console (509 versus 1\\,898)" in TEXN
        and "falls from 743 attackers under the binomial to 480 under the beta-binomial in sample, and rises to 949 cross-fitted" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D, App. E: E1 ranks 36-100 floor {b36} binomial, {o36} beta-binomial in sample, {x36} cross-fitted")
ufd = {e: TD["fleets"]["per_endpoint"][e]["unseen|none"]["clean_fires_by_fold"] for e in ("E1", "E2", "E3")}
good = (max(ufd["E1"].values()) == sum(ufd["E1"].values()) == 4 and max(ufd["E2"].values()) == sum(ufd["E2"].values()) == 2
        and max(ufd["E3"].values()) == 5 and sum(ufd["E3"].values()) == 6
        and "The unseen filter's misfires as its own trigger cluster by day: all 4 on the busiest endpoint and both on the console fall on one day, and 5 of the API's 6 on another" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: the unseen filter's own-trigger misfires by day {ufd}")
SI = json.load(open(R + "stix_ingest.json"))["versions"]
CPN = json.load(open(R + "compile_production_check.json"))
good = (SI["medallion"] == "3.0.0" and SI["misp-stix"] == "2026.9.16" and "the export drops such clients" in CPN["note"]
        and "(medallion 3.0.0)" in TEXN and "(misp-stix 2026.9.16)" in TEXN
        and "which reproduced exported address and /24-pair counts, and JA4 pair counts where the WAF blocked no client (Appendix~\\ref{app:repro})" in TEXN
        and "The query ran in the operator's log store, the artifact keeps only its counts, and the evaluation reads the exports" in TEXN
        and "Elsewhere the export drops clients partly blocked by the WAF, which the compiled query keeps." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI, App. F: what the compiled query reproduced, tool versions {SI}")
good = ("and past 4 to 19 median windows on the small ones, as medians of daily ratios" in TEXN
        and round(dF("fleets", "E1", "shared") * 100) == 8 and round(max(shS)) == 19)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the floor ratios are medians of the daily ratios")
# App. B: the weight grid (sprint 4) does not contain the ontology's 0.6, which reaches the grid's best AUC on its own
WS = json.load(open(HERE.parent / "sprint-4" / "results" / "weights_session_realistic.json"))
good = (0.6 not in WS["grid"] and WS["paper_weights"] == [1.0, 0.6, 0.3] and round(WS["paper_auc"], 3) == round(WS["best_auc"], 3) == 0.943
        and "reaches the same optimal AUC of $0.943$, as does the ontology's $(1.0,\\ 0.6,\\ 0.3)$" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. B: grid {WS['grid']} excludes 0.6; the ontology's weights reach AUC {WS['paper_auc']} as the best {WS['best_weights']} does")
# App. C: the strong per-session baseline is FLOW (3 attributes) plus 6 sums, and (b)-(d) all add to it
import ast as _ast
def _list_assign(path, name):
    for n in _ast.walk(_ast.parse(open(path).read())):
        if isinstance(n, _ast.Assign) and any(getattr(t, 'id', None) == name for t in n.targets):
            return n.value
_flow = _list_assign(HERE.parent / 'sprint-3' / 'scripts' / 'run_ablation.py', 'FLOW')
_strong = _list_assign(HERE.parent / 'sprint-5' / 'scripts' / 'run_klage_comparison.py', 'STRONG_FLOW')
_sets = _list_assign(HERE.parent / 'sprint-4' / 'scripts' / 'run_sprint4.py', 'STRONG_SETS')
n_flow = len(_flow.elts) + len(_strong.right.elts)
adds = all(isinstance(v, _ast.BinOp) and getattr(v.left, 'id', None) == 'STRONG_FLOW' for v in _sets.values[1:])
good = (n_flow == 9 and adds and 'a strong per-session baseline using nine flow attributes' in TEXN
        and '(c) adds only network proximity, and (d) adds cross-session evidence' in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. C: the strong baseline has {n_flow} flow attributes, and (b)-(d) add to it: {adds}")
# III-E and contribution (iii): the ontology declares every term the exported evidence chain uses,
# and each property's domain admits the node it is used on (the scope node is a Mitigation).
import rdflib as _rdf
from rdflib.namespace import RDF as _RDF, RDFS as _RDFS, OWL as _OWL
_o = _rdf.Graph(); _o.parse(str(HERE.parent.parent / 'ontology' / 'ddos_ontology.owl'), format='xml')
_c = _rdf.Graph(); _c.parse(R + 'example_chain.jsonld', format='json-ld')
def _supers(x, seen=None):
    seen = set() if seen is None else seen
    if x in seen: return seen
    seen.add(x)
    for y in _o.objects(x, _RDFS.subClassOf): _supers(y, seen)
    return seen
def _allowed(p):
    out = set()
    for d in _o.objects(p, _RDFS.domain):
        u = _o.value(d, _OWL.unionOf)
        out |= set(_o.items(u)) if u is not None else {d}
    return out
_declared = set(_o.subjects(_RDF.type, _OWL.ObjectProperty)) | set(_o.subjects(_RDF.type, _OWL.DatatypeProperty)) | set(_o.subjects(_RDF.type, _OWL.AnnotationProperty))
_types = {s: set(_c.objects(s, _RDF.type)) for s in set(_c.subjects())}
for _s, _p, _v in _c:
    for _r in _o.objects(_p, _RDFS.range):
        if (_r, _RDF.type, _OWL.Class) in _o: _types.setdefault(_v, set()).add(_r)
_undeclared = sorted({str(p).split('#')[-1] for s, p, v in _c if p != _RDF.type and p not in _declared})
_conflicts = sorted({str(p).split('#')[-1] for s, p, v in _c if p != _RDF.type and _allowed(p)
                     and not any(_allowed(p) & _supers(t) for t in _types.get(s, set()))})
_XS = 'http://www.w3.org/2001/XMLSchema#'
_badrange = sorted({f"{str(p).split('#')[-1]}:{str(v.datatype or _XS + 'string').split('#')[-1]}" for s, p, v in _c
                    if isinstance(v, _rdf.Literal) and _o.value(p, _RDFS.range) is not None
                    and str(_o.value(p, _RDFS.range)).startswith(_XS)
                    and str(v.datatype or _XS + 'string') != str(_o.value(p, _RDFS.range))})
# JSON-LD 1.1 turns an integral number into xsd:integer, so every xsd:double term the chain
# uses must be coerced by its context
_ctx = json.load(open(R + 'example_chain.jsonld'))['@context']
_used = {str(p).split('#')[-1] for s, p, v in _c}
_untyped = sorted(t for t in _used if (_rdf.URIRef('http://security.example.org/ontology/ddos#' + t), _RDFS.range, _rdf.URIRef(_XS + 'double')) in _o
                  and not (isinstance(_ctx.get('kg:' + t), dict) and _ctx['kg:' + t].get('@type') == 'xsd:double'))
good = (not _undeclared and not _conflicts and not _badrange and not _untyped and len(_c) > 40
        and 'links a session to its \\texttt{Identity}, source \\texttt{IPAddress} and \\texttt{Endpoint}. An \\texttt{Attack} links to its \\texttt{Mitigation}, whose scope the evidence chain carries' in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-E: the OWL declares every term of the exported chain ({len(_c)} triples); undeclared {_undeclared}, domain conflicts {_conflicts}, literals outside their range {_badrange}, double terms not typed in the context {_untyped}")
# App. B: the generator's 2 000 benign fingerprints exceed every production profile, held-out day included
CH = json.load(open(R + 'ja4_churn.json'))['per_endpoint']
_pf = [d['profile_fingerprints'] for e in CH.values() for d in e.values()]
good = (min(_pf) == 76 and max(_pf) == 1163 and max(_pf) < 2000
        and 'exceeds the $76$--$1\\,163$ observed per production endpoint' in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. B: production profiles hold {min(_pf)}-{max(_pf)} fingerprints, below the generator's 2000")

print("== the held-out block (production_tables_block.json, block_report.json, ja4_churn_block.json)")
BR = json.load(open(R + "block_report.json")); CB_ = json.load(open(R + "ja4_churn_block.json"))
from scipy.stats import binom as _bn
r_test, rc_test = fz["clean_fires"] / fz["clean_windows"], fz["clean_fires"] / fz["clean_gate_windows"]
pA = _bn.sf(bz["clean_fires"] - 1, bz["clean_windows"], r_test)
pC = _bn.sf(bz["clean_fires"] - 1, bz["clean_gate_windows"], rc_test)
# the block's report reproduces from the reduction, and states the protocol's verdicts
sys.path.insert(0, str(HERE / "scripts")); import block_report as _brm
good = (json.loads(json.dumps(_brm.report(PB, "test_days", CB_))) == BR
        and BR["m1"]["fires"] == 31 and not BR["m1"]["consistent"] and not BR["m8"]["all"]["consistent"] and BR["enough_days"])
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} block: block_report.json recomputes from the reduction; metric 1 and 8 not consistent")
# Table VII, cell by cell
CFB = [("Origin gate", "binomial", "fleets", "union|origins"), ("$\\Omega$ gate", "base rule", "base", "enrichment|omega"),
       ("Origin gate", "$z$-score", "base", "zcal|origins"), ("No gate", "unseen", "fleets", "unseen|none"),
       ("Seasonal gate", "beta-bin.$^{\\dagger}$", "xfit_od", "union|seasonal"), ("No gate", "binomial$^{a}$", "fleets", "union|none")]
def brow(run, key, e1_only=False):
    a = BD[run]["per_endpoint"]["E1"][key] if e1_only else BD[run]["all"][key]
    e1 = BD[run]["per_endpoint"]["E1"][key]
    p2 = lambda v: f"{v*100:.2f}"; p1 = lambda v: "--" if v is None else f"{v*100:.1f}"
    m = max(BD[run]["per_endpoint"][e][key]["clean_rate"] for e in ("E2", "E3", "E4"))
    return (["--" if e1_only else p2(a["clean_rate"]), p2(e1["clean_rate"]), "--" if e1_only else p2(m),
             p1(e1["new:x0.1"]["blocked"]), p1(e1["shared:x0.1"]["blocked"]),
             p1(a["new:A100"]["blocked"]), p1(a["shared:A100"]["blocked"]), p1(a["flash1000"]), p1(a["clean_collateral_median"])])
i0 = TEX.index("\\label{tab:block}"); tabB = TEX[i0:TEX.index("\\end{table}", i0)]
rowsB = [[c.strip().rstrip("\\").strip() for c in ln.split("&")] for ln in tabB.splitlines()
         if ln.strip().endswith("\\\\") and ln.count("&") == 10 and not ln.lstrip().startswith("\\textbf")]
gotB = [r[2:] for r in rowsB]; expB = [brow(run, key, i == 5) for i, (_, _, run, key) in enumerate(CFB)]
good = gotB == expB and [(r[0], r[1]) for r in rowsB] == [(t, sc) for t, sc, _, _ in CFB]
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} Table VII: 6 rows x 9 cells from production_tables_block.json" + ("" if good else f" got={gotB} exp={expB}"))
good = (bz["clean_windows"] == 16103 and PB["folds"]["test"] == 14
        and "16\\,103 clean windows, each day calibrated on all earlier days. E2--E4: max. 100 attackers, Fl.\\,1k, Coll.: pooled." in TEXN
        and "$^{a}$E1 alone.}" in TEX and "--min-calib-days 9" in (HERE / "results" / "heldout_block_protocol.md").read_text()
        and "\\caption{The six configurations fixed in advance, on the 14-day block.}" in TEX)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} Table VII: caption and note, {bz['clean_windows']} clean windows")
# V-D: the block's paragraph
ci = bz["clean_ci95"]; gr = bz["clean_gate_windows"] / bz["clean_windows"]; gt_ = fz["clean_gate_windows"] / fz["clean_windows"]
pe1 = {e: BD["fleets"]["per_endpoint"][e]["union|origins"] for e in ("E1", "E2", "E3", "E4")}
good = (bz["clean_fires"] == 31 and f"{bz['clean_rate']*100:.2f}" == "0.19" and [f"{x*100:.2f}" for x in ci] == ["0.13", "0.27"]
        and pA < 1e-4 and 1.8 <= bz["clean_rate"] / r_test <= 2.4 and ci[1] <= 0.01
        and 0.4 <= gr / gt_ <= 0.6 and bz["clean_gate_windows"] == 233 and f"{bz['clean_fires']/bz['clean_gate_windows']*100:.0f}" == "13"
        and f"{rc_test*100:.1f}" == "3.0" and pC < 1e-11
        and wk == 30 and pe1["E1"]["clean_fires"] == 0 and pe1["E2"]["clean_fires"] == 17 and pe1["E2"]["clean_gate_windows"] == 29
        and f"{bz['clean_collateral_median']*100:.0f}" == "39"
        and not BR["m1"]["consistent"]
        and "The 14-day block was exported after its protocol was public and analyzed after its export hashes were published (Appendix~\\ref{app:repro}). There the configuration misfired in 31 of 16\\,103 clean windows ($0.19\\%$, 95\\% interval $0.13$--$0.27\\%$, Table~\\ref{tab:block}). That is twice the test days' rate and, by the protocol's test, inconsistent with it ($P < 10^{-4}$), though within the budget. The gate opened half as often, but the scope misfired in 31 of its 233 openings ($13\\%$), versus 5 of 168 ($P < 10^{-11}$). The misfires fell on weekdays (30 of 31) and on the small endpoints, 17 of them in the console's 29 gate openings, and blocked a median $39\\%$ of the window's clients." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: block {bz['clean_fires']}/{bz['clean_windows']}, P = {pA:.1e}; gate {gr*100:.2f}% vs {gt_*100:.2f}%; scope {bz['clean_fires']}/{bz['clean_gate_windows']}, P = {pC:.1e}")
# V-D: the comparison fixed in advance (metric 7)
m7a, m7w = BR["m7"]["amended"], BR["m7"]["as_written"]
x4r = [x4[e]["clean_rate"] for e in ("E1", "E2", "E3", "E4")]
small = ("E2", "E3", "E4")
n4 = [x4[e]["new:A100"]["blocked"] for e in small]; s4 = [x4[e]["shared:A100"]["blocked"] for e in small]
n3 = [BD["fleets"]["per_endpoint"][e]["unseen|none"]["new:A100"]["blocked"] for e in small]
s3 = [BD["fleets"]["per_endpoint"][e]["unseen|none"]["shared:A100"]["blocked"] for e in small]
c5 = BD["fleets"]["per_endpoint"]["E1"]["union|none"]
good = (all(m7a[e]["arms"]["4"]["preferred"] for e in m7a) and all(m7w[e]["arms"]["4"]["preferred"] for e in m7w)
        and not m7a["E1"]["arms"]["5"]["preferred"] and not m7w["E1"]["arms"]["5"]["preferred"]
        and all(BR["m2"]["4"][e]["within"] for e in BR["m2"]["4"]) and not BR["m2"]["5"]["E1"]["within"]
        and (f"{min(x4r)*100:.2f}", f"{max(x4r)*100:.2f}") == ("0.05", "0.35")
        and (round(min(n4) * 100), round(max(n4) * 100)) == (68, 88) and all(round(x * 100) == 43 for x in n3)
        and (round(min(s4) * 100), round(max(s4) * 100)) == (34, 66) and max(s3) == 0
        and f"{x4['E1']['shared:x0.1']['blocked']*100:.1f}" == "11.4" and f"{x4['E1']['new:x0.1']['blocked']*100:.1f}" == "11.8"
        and f"{un1*100:.1f}" == "89.6" and unB == 0 and f"{c5['clean_rate']*100:.2f}" == "1.56"
        and "Behind it, the cross-fitted beta-binomial stays within the budget everywhere ($0.05$--$0.35\\%$) and is preferred to the unseen filter as its own trigger on every endpoint. On the small endpoints it stops $68$--$88\\%$ of 100 attackers on new stacks, versus $43\\%$, and $34$--$66\\%$ on shared ones, which the filter misses. On the busiest endpoint it is preferred only for shared stacks, which the filter cannot name: it adds $11.4\\%$ of the tenth-size botnet there but stops only $11.8\\%$ on new ones, versus $89.6\\%$. The unseen filter raised no false alarm, and the binomial scope with known fleets as its own trigger exceeded the budget there ($1.56\\%$)." in TEXN
        and BD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["shared:x0.1"]["blocked"] == 0 and m7a["E1"]["baseline"]["shared"] == 0
        and m7a["E1"]["arms"]["4"]["new"] < m7a["E1"]["baseline"]["new"] and m7a["E1"]["arms"]["4"]["shared"] >= m7a["E1"]["baseline"]["shared"] + 1)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: metric 7 prefers the seasonal arm everywhere, as written and amended; its rates {[round(x*100, 2) for x in x4r]}")
good = (all(m7a[e]["arms"][c]["preferred"] == m7w[e]["arms"][c]["preferred"] for e in m7a for c in m7a[e]["arms"])
        and "Its one amended rule, adopted after the export and before any result was computed, compares the small endpoints on 100 attackers and leaves the verdict unchanged." in TEXN
        and "The block's protocol was pushed publicly before any of its days was exported, and the export hashes, with an addendum that adds three metrics, before any result was computed" in TEXN
        and "The repository holds every metric both protocols name, whatever its value (\\texttt{production\\_tables.json}, \\texttt{block\\_report.json})." in TEXN
        and all(k in BR for k in ("m1", "m2", "m3", "m3_e1_by_day", "m4", "m5", "m6", "m7", "m8", "m9", "m10"))
        and all(k in FD["fleets"]["all"]["union|origins"] for k in ("clean_collateral_median", "flash100", "new:A100", "new:A1000", "new:x1", "new:x0.1", "shared:A100"))
        and "enrichment|omega" in FD["base"]["all"] and cpf["windows"] == 1152
        and "adds three metrics" in re.sub(r"\s+", " ", (HERE / "results" / "heldout_block_protocol_addendum_metrics.md").read_text())
        and "A few rows of raw counts were seen on screen at export." in TEXN
        and "amends one decision rule, metric 7's" in re.sub(r"\s+", " ", (HERE / "results" / "heldout_block_protocol_addendum_metrics.md").read_text())
        and "glanced at a few of those" in re.sub(r"\s+", " ", (HERE / "results" / "heldout_block_addendum_hashes.md").read_text())
        and all(f"## Part {k}" in (HERE / "results" / "heldout_block_addendum_hashes.md").read_text() for k in (1, 2, 3)))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. F: the amendment leaves every verdict unchanged; the addenda record the hashes of all three parts and what was seen")
# App. E: details of V-D
bdays = list(bz["clean_fires_by_fold"].values()); ovr = BD["overlap_frozen_rule"]
gS = [PB["stealth_E1"]["fleets"]["fresh:x0.1"][d]["gate"] for d in PB["stealth_E1"]["fleets"]["fresh:x0.1"]]
bS = [PB["stealth_E1"]["fleets"]["fresh:x0.1"][d]["blocked"] for d in PB["stealth_E1"]["fleets"]["fresh:x0.1"]]
# the block days only: ja4_churn.py also scores 2026-09-25 by default, a history day here
kmin_new = [d["new_fingerprints_kmin"] for e in BR["m10"]["per_endpoint"].values() for d in e.values()]
assert len(kmin_new) == 4 * 14 and not BR["m10"]["missing_endpoints"]
from scipy.stats import fisher_exact as _fx
fR = _fx([[bz["clean_fires"], bz["clean_windows"] - bz["clean_fires"]], [fz["clean_fires"], fz["clean_windows"] - fz["clean_fires"]]], alternative="greater")[1]
fC = _fx([[bz["clean_fires"], bz["clean_gate_windows"] - bz["clean_fires"]], [fz["clean_fires"], fz["clean_gate_windows"] - fz["clean_fires"]]], alternative="greater")[1]
zB = BD["base"]["all"]["zcal|origins"]
good = ((min(bdays), max(bdays)) == (0, 6) and ovr["frozen"] == 31 and ovr["both"] == 30
        and zB["clean_fires"] == 20 < bz["clean_fires"] and zB["flash1000"] < bz["flash1000"] and zB["flash100"] < bz["flash100"]
        and zB["new:A100"]["blocked"] > bz["new:A100"]["blocked"] and zB["shared:A100"]["blocked"] > bz["shared:A100"]["blocked"] and f"{fR:.2f}" == "0.07" and f"{fC:.4f}" == "0.0002"
        and f"{bz['clean_joint_expected']:.1f}" == "2.9"
        and (pe1["E3"]["clean_fires"], pe1["E3"]["clean_gate_windows"], pe1["E4"]["clean_fires"], pe1["E4"]["clean_gate_windows"]) == (10, 98, 4, 95)
        and f"{bz['flash100']*100:.1f}" == "3.4" and f"{bz['clean_rate']*bz['clean_collateral_mean']*100:.2f}" == "0.08"
        and (f"{min(gS)*100:.1f}", f"{max(gS)*100:.1f}") == ("0.0", "13.9") and (f"{min(bS)*100:.1f}", f"{max(bS)*100:.1f}") == ("0.0", "12.5")
        and max(kmin_new) == 0
        and "On the block, the configuration misfired in 0 to 6 windows a day, never on the busiest endpoint, and the base rule fired on 30 of those 31 windows. Gate and scope misfired together in 31 windows versus 2.9 if independent, and the scope misfired in 10 of the API's 98 gate openings and 4 of the single sign-on's 95. Counting the test days' own uncertainty, a one-sided Fisher test gives $P = 0.07$ for the rate's rise and $P = 0.0002$ for the misfires once the gate opens. The $z$-score reference misfired less (20 versus 31), fired on fewer crowds and stopped more of 100 attackers. Crowds of 100 users trigger the configuration in $3.4\\%$ of windows, and its misfires block an expected $0.08\\%$ of clients per clean window. On the busiest endpoint the origin gate opens in $0.0$--$13.9\\%$ of a tenth-size botnet's windows, depending on the day, and the configuration stops $0.0$--$12.5\\%$ of it. Behind the seasonal gate, 12 of the beta-binomial's 14 misfires on the busiest endpoint fall on two days. No fingerprint absent from the profile reached $k_{\\min}$ origins in a block window." in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: block by day {min(bdays)}-{max(bdays)}, base rule shares {ovr['both']} of {ovr['frozen']}, joint expected {bz['clean_joint_expected']:.1f}, E1 gate {min(gS)*100:.1f}-{max(gS)*100:.1f}%")
# the prospective days in the text: 1 held-out day and 14 block days
good = ("We evaluate budget and floor on eight days across four CDN endpoints, and the budget on 15 later days." in TEXN
        and "The CDN's traffic, over 23 days, measures the scopes' false alarms and, with injected botnets, their detection." in TEXN
        and "A ninth day, the \\textit{held-out day}, and 14 more, the \\textit{block}, were analyzed as fixed in advance." in TEXN
        and "and on 14 pre-specified days the rate doubles yet stays within the budget." in TEXN
        and "over 23 days of one operator's own endpoints" in TEXN and "a case not observed in 23 days" in TEXN
        and "so only the held-out day and the block test them prospectively" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} I, IV-A, V, VI: 1 held-out day and 14 block days, 23 production days in all")
# App. F's count, taken over every check above (each table check covers a whole table)
good = 240 <= ok + bad + 1 <= 260 and "recomputes about 250 printed numbers" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. F: the audit recomputes about 250 numbers ({ok + bad} checks)")
print(f"\nTOTAL: {ok} OK, {bad} mismatches")
sys.exit(1 if bad else 0)
