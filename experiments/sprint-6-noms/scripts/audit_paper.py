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
chk("V-A: (c)", "(c), restricted to network proximity, $0.499$ and $0.659$", (au(50, "rf", "c"), au(1000, "rf", "c")),
    "(c), restricted to network proximity, {:.3f} and {:.3f}")
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
chk("App. C: trained on 25, tested on 5", "and trained on 25 to $0.48$ on five", xm("25->5"), "and trained on 25 to {:.2f} on five")
chk("App. C: trained on 25, tested on 100", "and $0.75$ on 100", xm("25->100"), "and {:.2f} on 100")
cs = [xm(p, "d", "cross_seed_same_m") for p in XA]
chk("App. C: same M, other seeds", "against $0.95$--$0.995$ on the same $M$ with other seeds", (min(cs), max(cs)),
    "against {:.2f}--{:.3f} on the same M with other seeds")
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
good = f"{v*100:.2f}" == "0.03" and f"{vm*100:.1f}" == "0.5" and "at a mean collateral of $0.03\\%$ (at most $0.5\\%$ in one seed)" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:symbolic note: unseen FPR mean {v*100:.3f}%, largest seed {vm*100:.2f}%")
zf0 = [us("original", s, 0, "zscore", "fpr") for s in (1, 5, 25, 100)]
good = (max(zf0) == 0 and f"{us('shared_profile_tail', 25, 0, 'zscore', 'fpr')*100:.2f}" == "3.37"
        and f"{us('original', 25, 1, 'zscore', 'fpr')*100:.1f}" == "11.3"
        and "and the $z$-score $89.9\\%$ at $3.37\\%$" in TEXN and "the $z$-score $57.3\\%$ at $11.3\\%$" in TEXN
        and f"{us('shared_profile_tail', 25, 0, 'zscore', 'recall')*100:.1f}" == "89.9" and f"{us('original', 25, 1, 'zscore', 'recall')*100:.1f}" == "57.3"
        and f"{us('shared_profile_tail', 25, 0, 'enrichment', 'recall')*100:.1f}" == "85.4" and f"{us('shared_profile_tail', 25, 0, 'enrichment', 'fpr')*100:.2f}" == "2.23"
        and "on those the test blocks $85.4\\%$ at $2.23\\%$ collateral" in TEXN
        and "the test's operating point on every row the learned model runs but the adversarial one" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:symbolic note: z-score FPR 0 except shared and adversarial")
mf = [us("original", s, a_, "modal", "fpr") for s, a_ in ((5, 0), (25, 0), (100, 0), (25, 1))] + [us("shared_profile_tail", 25, 0, "modal", "fpr")]
good = (us("original", 1, 0, "modal", "fpr") == 0 and all(f"{x*100:.1f}" == "39.0" for x in mf)
        and f"{us('original', 25, 0, 'modal', 'fpr', alpha=2.0)*100:.1f}" == "61.1"
        and "When the botnet uses a single stack, the modal fingerprint and the test agree, blocking $89.8\\%$ of the attack with no collateral observed" in TEXN
        and "it blocks $0.0\\%$ of the attack and $39.0\\%$ of legitimate traffic, $61.1\\%$ with a more concentrated legitimate population ($\\alpha = 2.0$)" in TEXN)
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
        and "Allowed $1\\%$ false positives, which the test does not need, it reaches $66.8\\%$ at 25 stacks, and $94.6\\%$ with the profile" in TEXN)
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
        and "and blocks a median $75$--$80\\%$ of the attackers in every attack window $\\Omega$ flags, hitting no legitimate session" in TEXN)
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
        and "halves its false alarms with no loss of detection" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: origin gate halves false alarms ({c['origins_enrichment_pipeline']*100:.2f} vs "
      f"{c['pipeline']*100:.2f}%), no loss in any of {len(cells)} attack cells")
n_org, n_om = round(c["origins_enrichment_pipeline"] * c["windows"]), round(c["pipeline"] * c["windows"])
good = n_org < n_om / 2 + 1 and "halves its false alarms with no loss of detection" in TEXN; ok += good; bad += not good
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
chk("App. E: rho moves no firing rate by over", "by over $0.3$ points", moves[0]*100, "by over {:.1f} points")
chk("App. E: rho moves no blocked share by over", "by over $4.5$", moves[2]*100, "by over {:.1f}")
chk("App. E: rho moves a collateral median by up to", "no collateral median by over $7.2$", moves[1]*100, "no collateral median by over {:.1f}")
chk("App. E: flash crowds of 1,000, z-score", "86.8", a["flash"]["1000"]["zscore_pipeline"]*100, pct)
chk("App. E: flash crowds of 1,000, rule", "21.8", a["flash"]["1000"]["pipeline"]*100, pct)
fps = [x for e in E for x in E[e]["profile_fingerprints"]]
good = f"${min(fps)}$--${max(fps)}$" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. B: production endpoints show {min(fps)}--{max(fps)} fingerprints")
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
         "rule": ("base", "enrichment")}
XFIT = {"binomial": ("xfit_fleets", "union"), "beta-bin.": ("xfit_od", "union"), "$z$-score": ("xfit", "zcal")}
GATE = {"binomial": "origins", "beta-bin.": "origins", "$z$-score": "origins", "rule": "omega"}
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
for label, want in (("tab:production", [("in", n) for n in ("binomial", "beta-bin.", "$z$-score")]
                     + [("xfit", n) for n in ("binomial", "beta-bin.", "$z$-score")]
                     + [("fresh", n) for n in ("rule", "binomial", "beta-bin.", "$z$-score")]),):
    rows = table_rows(label)
    for g, name, printed in rows:
        exp = expected(g, name)
        good = printed == exp; ok += good; bad += not good
        print(f"{'OK ' if good else 'XX '} {label} {g:5s} {name:10s} printed={printed} data={exp}")
    good = [(g, n) for g, n, _ in rows] == want; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} {label} holds the {len(want)} rows in order ({len(rows)} parsed)")
fz, ob, zc = TD["fleets"]["all"]["union|origins"], TD["od"]["all"]["union|origins"], TD["base"]["all"]["zcal|origins"]
ff_, fo, zf = FD["fleets"]["all"]["union|origins"], FD["od"]["all"]["union|origins"], FD["base"]["all"]["zcal|origins"]
good = fz["clean_windows"] == 5643 and ff_["clean_windows"] == 1152 and "(5\\,643 on the test days, 1\\,152 on the held-out day)" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:production note: {fz['clean_windows']} clean windows on the test days, {ff_['clean_windows']} on the held-out day")
tp_ = TEX[TEX.index("\\label{tab:production}"):]; tp_ = tp_[:tp_.index("\\end{table}")]
good = "$^{*}$Post hoc. $^{a}$No gate, Fl.\\,1k, $z$-score: outside the protocol.}" in tp_ and "\\textit{Held-out day, calibrated on the eight days before it}$^{a}$" in tp_ and "so at most about $90\\%$ can be blocked" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:production note: the beta-binomial marked as built after the held-out day, the held-out cells outside the protocol marked")
nfa = {e: TD["fleets"]["per_endpoint"][e]["union|origins"]["clean_fires"] for e in ("E1", "E2", "E3", "E4")}
good = nfa["E2"] == 4 and max(nfa[e] for e in ("E1", "E3", "E4")) == 1 \
    and "4 of them on the web console" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: false alarms per endpoint {nfa}, 4 of 5 on the console")
kf = {r: [FL[r][e][f]["known_fleets"] for e in FL[r] for f in FL[r][e]] for r in FL}
same = all(TD["od"][k] == TD["od_fleets"][k] and FD["od"][k] == FD["od_fleets"][k] for k in ("all", "per_endpoint"))
good = (max(kf["od_fleets"]) == 0 and same and "no fingerprint qualifies as a known fleet in sample" in TEXN
        and "& beta-bin. & --             & post hoc" in TEX)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: beta-binomial names no known fleet in any fold in sample ({max(kf['od_fleets'])}), identical with the fleet profile: {same}")
good = ("Five choices were made on the test days: counting origins, calibrating $\\lambda_e$, the gate, the union with the unseen filter and the $5\\%$ fleet share" in TEXN
        and "$^{*}$Post hoc: built after the held-out day was read" in TEXN
        and "The beta-binomial and a cross-fitted calibration were built after the held-out day was read, so their results are post hoc" in TEXN
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
            for e in ("E1", "E2", "E3") for f in tf) and "from 139 attackers per window on E1 to E3, a bound set by $k_{\\min}$, and from 84 on E4, where the test names them first" in TEXN
        and all(FPD["fleets"]["E4"][f]["25"]["new"]["set_by"] == "test" and FPD["fleets"]["E4"][f]["25"]["new"]["min_attackers"] == 84 for f in tf)
        and "which takes $\\lceil k_{\\min} M/0.9 \\rceil$ attackers whatever the level, 139 for $M = 25$" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D, tab:floor: the unseen filter sets the new-stack floor at 139 attackers on E1-E3")
good = ("and the floor is computed at their median share." in TEXN
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
        and "and with the fingerprints' rank: those of rank 11 to 35 are never named on the two largest endpoints (Appendix~\\ref{app:window})" in TEXN
        and "For 25 stacks, fingerprints of rank 11 to 35 need 808 on E3 and 114 on E4" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: ranks 11-35 never named on E1 and E2, named on E3 and E4 {n1135}")
tailb = [FB["per_endpoint"][e][f]["tail_prevalence_median"] for e in ("E1",) for f in tf]
good = max(tailb) < 1e-5 and "On stacks that real clients also present, mostly rare ones past the profile's ten most common fingerprints, the level decides" in TEXN
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
good = nw == [139, 139, 139, 84] and "on new stacks from 139 attackers per window on E1 to E3, a bound set by $k_{\\min}$, and from 84 on E4" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: binomial configuration's new-stack floors {nw}")
shA, shF = dA("fleets", "E1", "shared"), dF("fleets", "E1", "shared")
shS = [dF("fleets", e, "shared") for e in ("E2", "E3", "E4")]
good = (shA == 254 and round(shF * 100) == 8 and round(min(shS)) == 4 and round(max(shS)) == 19
        and "A typical stack is then named only past 254 attackers on the busiest endpoint, $8\\%$ of its window, and past 4 to 19 times the median window on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared-stack floors E1 {shA} ({shF*100:.1f}%), small endpoints {[round(x, 1) for x in shS]} windows")
l1 = lvl("od", "E1")
good = (round(math.log10(l1)) == -4 and "the busiest endpoint's level rises to about $10^{-4}$ and the others' to the $0.01$ cap" in TEXN
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
        and "It is no cliff: below it the scope names the stacks that chance makes larger, as a binomial model of stack sizes predicts ($43.1\\%$ against $43.2\\%$ measured at 100 attackers on the busiest endpoint, Fig.~\\ref{fig:stops})" in TEXN)
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
chk("V-B: joint misfires of the binomial configuration", "yet the 5 joint misfires, against 3.5 under independence, are within chance ($P = 0.27$)",
    pj("fleets", "union|origins"), "yet the {} joint misfires, against {:.1f} under independence, are within chance (P = {:.2f})")
jo = TD["od"]["all"]["union|origins"]
chk("App. E: the same for the beta-binomial and the z-score", "for the post hoc beta-binomial and the calibrated $z$-score, in 22 and 20 windows against 7.5 and 11.9",
    (jo["clean_fires"], jz["clean_fires"], jo["clean_joint_expected"], jz["clean_joint_expected"]),
    "for the post hoc beta-binomial and the calibrated z-score, in {} and {} windows against {:.1f} and {:.1f}")
PJ = {n: pj(*rk)[2] for n, rk in (("bin", ("fleets", "union|origins")), ("bin_x", ("xfit_fleets", "union|origins")),
                                   ("beta", ("od", "union|origins")), ("beta_x", ("xfit_od", "union|origins")),
                                   ("z", ("base", "zcal|origins")), ("z_x", ("xfit", "zcal|origins")))}
xb_, xo_, xz_ = pj("xfit_fleets", "union|origins"), pj("xfit_od", "union|origins"), pj("xfit", "zcal|origins")
good = (PJ["bin"] > 0.05 and PJ["bin_x"] > 0.05 and max(PJ["beta"], PJ["beta_x"], PJ["z"], PJ["z_x"]) < 0.05
        and PJ["beta"] < 1e-4 and f"{PJ['z']:.2f}" == "0.02"
        and "($P < 10^{-4}$ and $P = 0.02$ for a Poisson count)" in TEXN
        and f"and in {xo_[0]} and {xz_[0]} against {xo_[1]:.1f} and {xz_[1]:.1f} cross-fitted" in TEXN
        and f"5 against 3.5 and {xb_[0]} against {xb_[1]:.1f} cross-fitted ($P = {PJ['bin']:.2f}$ and ${PJ['bin_x']:.2f}$)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B, App. E: joint misfires against independence, Poisson P { {k: round(v, 4) for k, v in PJ.items()} }")
good = all(v > 0.01 for v in alone.values()) and "Pooled over the endpoints (Table~\\ref{tab:production}), every calibrated component exceeds its $1\\%$ target" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: every calibrated component exceeds 1% out of sample ({ {k: round(v*100, 2) for k, v in alone.items()} })")
ci = fz["clean_ci95"]
good = (fz["clean_fires"] == 5 and fmt(fz["clean_rate"]) == "0.1"
        and f"fires on only $0.1\\%$ of clean windows (5 of 5\\,643, 95\\% interval ${ci[0]*100:.2f}$--${ci[1]*100:.2f}\\%$)" in TEXN)
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
chk("V-B: expected collateral per clean window", "about $0.03\\%$ of legitimate clients per clean window", fz["clean_rate"] * fz["clean_collateral_mean"] * 100,
    "about {:.2f} of legitimate clients per clean window")
per_day = {k: s["clean_fires"] / 20 for k, s in (("bin", fz), ("z", zc), ("beta", ob))}
e2m = TD["fleets"]["per_endpoint"]["E2"]["union|origins"]["clean_fires"]
good = (fz["clean_fires"] == 5 and e2m == 4 and PT["endpoints"]["E2"] == "web console" and fz["clean_windows"] == 5643
        and "(5 of 5\\,643, 95\\% interval $0.03$--$0.21\\%$), 4 of them on the web console" in TEXN and round(288 * 0.01, 1) == 2.9
        and "about 2.9 of a day's 288" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: {e2m} of the {fz['clean_fires']} misfires on the web console, budget 2.9 a day")
chk("V-B: flash crowds of 1,000 and their filters", "trigger the configuration in $22.2\\%$ of windows, with lighter filters that block a median $4.3\\%$ of the window's clients",
    (fz["flash1000"]*100, fz["flash1000_collateral_median"]*100),
    "trigger the configuration in {:.1f} of windows, with lighter filters that block a median {:.1f} of the window's clients")
good = fz["flash1000_collateral_median"] < fz["clean_collateral_median"]; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: flash-crowd filters are lighter than clean-window misfires ({fz['flash1000_collateral_median']*100:.1f}% vs {fz['clean_collateral_median']*100:.1f}%)")
S3 = [("fleets", "union|origins"), ("od", "union|origins"), ("base", "zcal|origins")]
sw1 = SW["fleets"]["E1"]
g_small = [sw1[f"new:M25:A{A}"]["gate"] for A in (25, 50, 100, 250)] + [sw1["new:M25:x0.1"]["gate"]]
good = (round(min(g_small) * 100) == 6 and round(max(g_small) * 100) == 13 and round(sw1["new:M25:A1000"]["gate"] * 100) == 45
        and round(sw1["new:M25:x1"]["gate"] * 100) == 79 and 0.3 < 1000 / no_[0] < 0.35
        and "the gate opens in only $6$--$13\\%$ of the windows of botnets from 25 attackers up to a tenth of the window" in TEXN
        and "in $45\\%$ at a third and in $79\\%$ at a whole window" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: E1 gate in attack windows {min(g_small)*100:.1f}--{max(g_small)*100:.1f}% up to a tenth, {sw1['new:M25:A1000']['gate']*100:.1f}% at 1,000, {sw1['new:M25:x1']['gate']*100:.1f}% at 1x")
chk("V-C: E1, the binomial configuration stops", "therefore stops $3.4\\%$ of a botnet of 100 attackers and $11.8\\%$ of a tenth-size botnet",
    (sw1["new:M25:A100"]["blocked"]*100, sw1["new:M25:x0.1"]["blocked"]*100),
    "therefore stops {:.1f} of a botnet of 100 attackers and {:.1f} of a tenth-size botnet")
chk("V-C: E1, the scope alone would block", "while its scope alone would block $43.2\\%$ and $89.6\\%$",
    (sw1["new:M25:A100"]["blocked_alone"]*100, sw1["new:M25:x0.1"]["blocked_alone"]*100), "while its scope alone would block {:.1f} and {:.1f}")
SE1 = PT["stealth_E1"]["fleets"]["fresh:x0.1"]
bd = [SE1[f]["blocked"] * 100 for f in tf]; bn = [SE1[f]["blocked_no_gate"] * 100 for f in tf]; bs = [SE1[f]["blocked_seasonal"] * 100 for f in tf]
chk("V-C: E1 0.1x blocked by day, origin gate", "$0.6$--$37.2\\%$ depending on the day", (min(bd), max(bd)), "{:.1f}--{:.1f} depending on the day")
bnf = PT["stealth_E1"]["fleets"]["fresh:x0.1"]["2026-09-25"]["blocked_no_gate"] * 100
good = all(89 <= x <= 91 for x in bn + [bnf]) and "The \\textit{scope as its own trigger} (No gate) stops about $90\\%$ of that botnet on new stacks on every day" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-C: E1 0.1x, the scope alone stops {min(bn):.1f}--{max(bn):.1f}% by test day and {bnf:.1f}% held out")
e1s, e1o_ = TD["fleets"]["per_endpoint"]["E1"]["union|seasonal"], TD["fleets"]["per_endpoint"]["E1"]["union|origins"]
e2o, e2s = TD["fleets"]["per_endpoint"]["E2"]["union|origins"], TD["fleets"]["per_endpoint"]["E2"]["union|seasonal"]
xs_ = {e: (TD["xfit_od"]["per_endpoint"][e]["union|seasonal"]["clean_rate"], FD["xfit_od"]["per_endpoint"][e]["union|seasonal"]["clean_rate"])
       for e in ("E1", "E2", "E3", "E4")}
good = (e1s["new:x0.1"]["blocked"] > e1o_["new:x0.1"]["blocked"] and f"{e2s['clean_rate']*100:.2f}" == "2.64"
        and all(max(v) <= 0.01 for v in xs_.values())
        and all(TD[r]["per_endpoint"]["E2"]["union|seasonal"]["clean_rate"] > 0.01 for r in ("fleets", "xfit_fleets", "od"))
        and TD["xfit_od"]["per_endpoint"]["E2"]["union|seasonal"]["clean_rate"] <= 0.01
        and "It stops more of the tenth-size botnet on the busiest endpoint. On the console, though, of the binomial and the beta-binomial, each in sample and cross-fitted, only the cross-fitted beta-binomial stays within the budget behind it" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: seasonal gate E1 0.1x {e1s['new:x0.1']['blocked']*100:.1f}% vs {e1o_['new:x0.1']['blocked']*100:.1f}%, console {e2s['clean_rate']*100:.2f}%, cross-fitted beta-binomial at most {max(max(v) for v in xs_.values())*100:.2f}%")
good = e1s["clean_fires"] == 0; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: the seasonal gate raises no false alarm on E1 ({e1s['clean_fires']})")
a1, a1x, a1f = TD["fleets"]["per_endpoint"]["E1"]["union|none"], TD["xfit_fleets"]["per_endpoint"]["E1"]["union|none"], FD["fleets"]["per_endpoint"]["E1"]["union|none"]
b1 = TD["base"]["per_endpoint"]["E1"]["union|none"]; bf1 = a1["clean_fires_by_fold"]
good = (a1["clean_fires"] == 14 and a1["clean_windows"] == 1440 and f"{a1['clean_rate']*100:.2f}" == "0.97"
        and [round(x * 100, 2) for x in a1["clean_ci95"]] == [0.53, 1.63]
        and [bf1[f] for f in tf] == [0, 0, 1, 5, 8] and f"{a1['clean_collateral_median']*100:.1f}" == "1.0"
        and b1["clean_fires"] == 92 and b1["clean_windows"] == 1440
        and FD["base"]["per_endpoint"]["E1"]["union|none"]["clean_fires"] == 95 and FD["base"]["per_endpoint"]["E1"]["union|none"]["clean_windows"] == 288
        and "With the binomial and known fleets, its rate on the busiest endpoint sits at the budget and rose from no false alarm on the first two test days to 8 of 288 on the last" in TEXN
        and "Without the fleet exemption it fires there in 92 of the 1\\,440 test-day windows and 95 of the held-out day's 288" in TEXN
        and "and its misfires there block a median $1.0\\%$ of the clients" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: binomial scope alone on E1 {a1['clean_fires']}/{a1['clean_windows']} = {a1['clean_rate']*100:.2f}% (CI {[round(x*100, 2) for x in a1['clean_ci95']]}), by day {[bf1[f] for f in tf]}, {b1['clean_fires']} without fleets")
good = (a1f["clean_fires"] == 0 and a1f["clean_windows"] == 288
        and f"{a1['clean_rate']*100:.2f}" == "0.97")
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} Table VII: the binomial scope alone on E1: {a1['clean_rate']*100:.2f}% test, 0 of 288 held out")
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
        and "On new stacks of at least $k_{\\min}$ origins, as in the tenth-size botnet, the unseen filter alone does as well under every trigger, since it names each such stack, with fewer false alarms and flash-crowd firings. As its own trigger its false alarms also cluster by day" in TEXN
        and all(TD[r]["per_endpoint"][e][f"union|{g}"]["new:A100"]["blocked"] == TD[r]["per_endpoint"][e][f"unseen|{g}"]["new:A100"]["blocked"]
                for r in ("fleets",) for e in ("E1", "E2", "E3") for g in ("origins", "seasonal", "none"))
        and all(TD["fleets"]["per_endpoint"]["E4"][f"union|{g}"]["new:A100"]["blocked"] > TD["fleets"]["per_endpoint"]["E4"][f"unseen|{g}"]["new:A100"]["blocked"] + 0.3
                for g in ("origins", "seasonal", "none"))
        and all(TD["xfit_od"]["per_endpoint"][e][f"union|{g}"]["new:A100"]["blocked"] > TD["xfit_od"]["per_endpoint"][e][f"unseen|{g}"]["new:A100"]["blocked"] + 0.1
                for e in ("E2", "E3", "E4") for g in ("origins", "seasonal", "none"))
        and round(TD["xfit_od"]["per_endpoint"]["E1"]["union|none"]["new:A100"]["blocked"] * 100) == 58
        and round(TD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["new:A100"]["blocked"] * 100) == 43
        and "The test adds the shared stacks. On new stacks too small for the filter, the cross-fitted beta-binomial adds on the small endpoints, and as its own trigger on the busiest one too ($58\\%$ against $43\\%$ of 100 attackers), while the binomial adds only on the single sign-on. Of 100 new-stack attackers, the cross-fitted beta-binomial behind the seasonal gate stops $53$--$84\\%$ on the small endpoints and $3.9\\%$ on the busiest one, against $43\\%$ for the unseen filter as its own trigger" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-C: on new stacks the unseen filter matches every scope under every trigger with fewer misfires; only the test names shared stacks (binomial alone on E2-E4 {min(sa):.2f}--{max(sa):.2f}%)")
chk("App. E: the scope alone on shared stacks, E1", "With known fleets it stops $61.1\\%$ of the busiest endpoint's tenth-size botnet on shared stacks",
    TD["fleets"]["per_endpoint"]["E1"]["union|none"]["shared:x0.1"]["blocked"]*100, "With known fleets it stops {:.1f} of the busiest endpoint's tenth-size botnet on shared stacks")
gs = TD["base"]["all"]["gates_clean"]
chk("App. E: the seasonal gate alone", "The post hoc seasonal gate alone fires on $3.0\\%$ of clean test-day windows", gs["seasonal"]*100,
    "The post hoc seasonal gate alone fires on {:.1f} of clean test-day windows")
fs1, fo1 = FD["fleets"]["per_endpoint"]["E1"]["union|seasonal"]["new:x0.1"]["blocked"], FD["fleets"]["per_endpoint"]["E1"]["union|origins"]["new:x0.1"]["blocked"]
chk("App. E: the seasonal gate on E1 by day", "stops $10.0$--$44.7\\%$ of a tenth-size botnet depending on the day.",
    (min(bs), max(bs)), "stops {:.1f}--{:.1f} of a tenth-size botnet depending on the day.")
good = fo1 == 0 and f"{fs1*100:.1f}" == "15.3" and f"{gs['origins']*100:.1f}" == "3.0"
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: on the held-out day the origin gate stopped none of it ({fo1})")
S1 = PT["stealth_E1"]["fleets"]["fresh:x0.1"]; S2 = PT["stealth_E1"]["fleets"]["tail:x0.1"]
gt = [S1[f]["gate"] for f in tf]; rw = [S1[f]["recall_where_named"] for f in tf]
nm = [S[f]["named"] for S in (S1, S2) for f in tf + ["2026-09-25"]]
good = min(nm) == 1.0 and all(0.85 <= x <= 0.95 for x in rw) and f"depending on the day, the gate opens in ${min(gt)*100:.1f}$--${max(gt)*100:.0f}\\%$ of the windows of a botnet a tenth the size of the window" in TEX \
    and S1["2026-09-25"]["gate"] == 0 and "the gate never opened" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: E1 at 0.1x named in every window (new and shared stacks), gate {min(gt)*100:.1f}--{max(gt)*100:.1f}%, none on the held-out day")
e1f, e1o = TD["fleets"]["per_endpoint"]["E1"], TD["od"]["per_endpoint"]["E1"]
good = abs(e1f["union|origins"]["new:x0.1"]["blocked"] - sw1["new:M25:x0.1"]["blocked"]) < 1e-12
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} the sweep reproduces the E1 0.1x cell of the per-endpoint results (Table VII)")
sm = lambda r, k: [TD[r]["per_endpoint"][e][k]["new:x1"] for e in ("E2", "E3", "E4")]
b3 = [c["blocked"] for c in sm(*S3[0])]
o3 = [c for c in sm(*S3[1]) + sm(*S3[2])]
gx1 = [SW["fleets"][e]["new:M25:x1"]["gate"] for e in ("E2", "E3", "E4")]
good = (all(dA("fleets", e, "new") > no_[i + 1] for i, e in enumerate(("E2", "E3", "E4")))
        and f"{min(b3)*100:.0f}" == "2" and f"{max(b3)*100:.0f}" == "5")
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: small endpoints at 1x: gate {min(gx1)*100:.1f}--{max(gx1)*100:.1f}%, below the floors, {min(b3)*100:.1f}--{max(b3)*100:.1f}% stopped")
s100 = [SW["fleets"][e]["new:M25:A100"] for e in ("E2", "E3", "E4")]; h100 = [SW["fleets"][e]["shared:M25:A100"] for e in ("E2", "E3", "E4")]
good = (min(x["gate"] for x in s100) > 0.5 and f"{100 / no_[1]:.1f}" == "1.6" and f"{100 / no_[3]:.0f}" == "5"
        and f"On the small endpoints a botnet of 100 attackers, 1.6 to 5 times their median window, opens the gate in ${min(x['gate'] for x in s100)*100:.0f}$--${max(x['gate'] for x in s100)*100:.0f}\\%$ of the windows, and there the floor decides" in TEXN)
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
        and "A botnet on the endpoint's 25 most common fingerprints, the boundary of the threat model, is mostly missed: the configuration stops $7.0\\%$ and $23.8\\%$ of 100 and 1\\,000 attackers. It stops none on the two largest endpoints, where nearly all 25 lie past the limit, but $73.5\\%$ of 1\\,000 on the single sign-on" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the adversarial botnet is blocked 0% on E1 and E2 ({e12})")
CH = json.load(open(R + "ja4_churn.json"))
newd = [r["new_fingerprints"] for e in CH["per_endpoint"] for f, r in CH["per_endpoint"][e].items() if f in tf]
e1n = [CH["per_endpoint"]["E1"][f]["new_fingerprints"] for f in tf]
good = (min(newd) > 0 and max(e1n) == 345 and "Fingerprints the profile has never seen appear every day but rarely concentrate" in TEXN
        and f"{CH['test_days']['windows_with_candidate_share']*100:.2f}" == "0.21" and "$0.21\\%$ of the test days' windows" in TEXN
        and CH["test_days"]["windows"] == 5643)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: JA4 churn, new fingerprints every day (E1 up to {max(e1n)}), candidates in {CH['test_days']['windows_with_candidate_share']*100:.2f}% of windows")
chk("App. E: scope alone, E1 0.1x, beta-binomial", "the scope alone stops $90.0\\%$ and $78.3\\%$ of a botnet a tenth the size of the busiest window, on new and shared stacks, at $2.1\\%$ of that endpoint's clean windows",
    (e1o["union|none"]["new:x0.1"]["blocked"]*100, e1o["union|none"]["shared:x0.1"]["blocked"]*100, e1o["union|none"]["clean_rate"]*100),
    "the scope alone stops {:.1f} and {:.1f} of a botnet a tenth the size of the busiest window, on new and shared stacks, at {:.1f} of that endpoint's clean windows")
chk("App. E: scope alone with fleets, all endpoints", "on $2.2\\%$ of pooled", TD["fleets"]["all"]["union|none"]["clean_rate"]*100, "on {:.1f} of pooled")
chk("App. E: same, held-out day", "and $0.5\\%$ on the held-out day", FD["fleets"]["all"]["union|none"]["clean_rate"]*100, "and {:.1f} on the held-out day")
chk("App. E: scope alone without fleets", "against $3.5\\%$ and", TD["base"]["all"]["union|none"]["clean_rate"]*100, "against {:.1f} and")
chk("App. E: same, held-out day, without fleets", "and $8.8\\%$ for the union without", FD["base"]["all"]["union|none"]["clean_rate"]*100, "and {:.1f} for the union without")
chk("App. E: uncalibrated z-score, clean", "fires on $2.6\\%$ of clean", TD["base"]["all"]["zscore|omega"]["clean_rate"]*100, "fires on {:.1f} of clean")
chk("App. E: uncalibrated z-score, flash", "and $64.5\\%$ of flash crowds", TD["base"]["all"]["zscore|omega"]["flash100"]*100, "and {:.1f} of flash crowds")

print("== the held-out day (production_tables.json, compile_production_check_fresh.json)")
from scipy.stats import binom as _binom
pv = _binom.sf(ff_["clean_fires"] - 1, ff_["clean_windows"], fz["clean_fires"] / fz["clean_windows"])
good = ff_["clean_fires"] == 2 and "gives the binomial configuration 2 false alarms in 1\\,152 clean windows" in TEXN \
    and f"($P = {pv:.2f}$, and up to 3 would have passed)" in TEX and pv >= 0.05
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: {ff_['clean_fires']} of {ff_['clean_windows']}, P = {pv:.3f} (protocol: consistent)")
r_ = fz["clean_fires"] / fz["clean_windows"]
p3, p4 = _binom.sf(2, ff_["clean_windows"], r_), _binom.sf(3, ff_["clean_windows"], r_)
good = p3 >= 0.05 > p4 and "and up to 3 would have passed" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: up to 3 false alarms would pass (P = {p3:.3f}), 4 would not (P = {p4:.3f})")
pw = _binom.sf(3, ff_["clean_windows"], 3 * r_)
chk("held-out day: power against a tripled rate", "a tripled rate would be flagged only $37\\%$ of the time", pw*100,
    "a tripled rate would be flagged only {:.0f} of the time")
gw = ff_["clean_gate_windows"]; pc2 = _binom.sf(1, gw, fz["clean_fires"] / fz["clean_gate_windows"])
good = (gw == 3 and fz["clean_gate_windows"] == 168 and ff_["clean_fires"] == 2 and f"{pc2:.3f}" == "0.003"
        and f"{TD['fleets']['all']['gates_clean']['origins']*100:.1f}" == "3.0"
        and f"{gw / ff_['clean_windows'] * 100:.2f}" == "0.26"
        and "the day passed mostly because the gate was quiet" in TEXN
        and "Beyond the protocol's metrics, a tripled rate would be flagged only $37\\%$ of the time, and the day passed mostly because the gate was quiet: it opened in only 3 clean windows, $0.26\\%$ against $3.0\\%$ on the test days. The scope misfired in two of them, both on the web console, more often than the test days predict once the gate is open ($P = 0.003$)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: the gate opened in {gw} clean windows, the scope misfired in 2 (P = {pc2:.4f} against 5 of 168)")
chk("held-out day: the protocol's flash crowd", "Flash crowds of 100 users trigger the configuration in $1.1\\%$ of windows",
    ff_["flash100"]*100, "Flash crowds of 100 users trigger the configuration in {:.1f} of windows")
good = "Flash crowds of 100 users: share of windows where the configuration fires" in (HERE / "results" / "fresh_day_protocol.md").read_text()
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: the protocol fixes flash crowds of 100 users as a metric")
good = FD["fleets"]["per_endpoint"]["E2"]["union|origins"]["clean_fires"] == 2 and PT["endpoints"]["E2"] == "web console" \
    and "both on the web console" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: both false alarms on the web console")
good = f"{ff_['clean_collateral_median']*100:.1f}" == "41.2"
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: the two false alarms block a median {ff_['clean_collateral_median']*100:.1f}% (Table IV)")
chk("held-out day: blocked", "and $38.9\\%$, $73.4\\%$, $21.5\\%$ and $60.9\\%$ on the held-out day",
    tuple(ff_[x]["blocked"]*100 for x in ("new:A100", "new:A1000", "shared:A100", "shared:A1000")),
    "and {:.1f}, {:.1f}, {:.1f} and {:.1f} on the held-out day")

ov, ot, orl = FD["overlap_frozen_zcal"], TD["overlap_frozen_zcal"], FD["overlap_frozen_rule"]
good = orl["frozen"] == orl["rule"] == orl["both"] == 2 and ov["frozen"] == ov["zcal"] == ov["both"] == 2 \
    and "On the held-out day the base rule, the protocol's reference, fired on the same two windows as the configuration, as did the calibrated $z$-score, outside the protocol" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: the z-score {ov} and the base rule {orl} fired on the same two windows")
good = ot["frozen"] == 5 and ot["both"] == 4
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} test days: the calibrated z-score shared {ot['both']} of the configuration's {ot['frozen']} false alarms")
o2, x2 = TD["od"]["per_endpoint"]["E2"]["union|origins"], TD["xfit_od"]["per_endpoint"]["E2"]["union|origins"]
good = (fo["clean_fires"] == 0 and "On the held-out day it raised no false alarm" in TEXN
        and f"{o2['clean_rate']*100:.1f}" == "1.3" and f"{o2['flash1000']*100:.1f}" == "74.4" and f"{x2['flash1000']*100:.1f}" == "16.1"
        and "where $74.4\\%$ of 1\\,000-user crowds trigger it" in TEXN
        and "and the console's 1\\,000-user crowds trigger it in $16.1\\%$ of windows" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: the beta-binomial raised {fo['clean_fires']} false alarms")
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
good = cc["ok"] and cc["omega_max_abs_diff"] == 0 and "checks the compiled count query on generated sessions" in TEXN
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
        and "in every window of two production days" in TEXN
        and cp["ja4_pairs_equal_without_waf_blocks"] == cp["windows_without_waf_blocks"]
        and f"and the JA4 pair counts in the {cp['windows_without_waf_blocks']} windows a day of the endpoint where the WAF blocked no client" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} compiled query in the operator's store: origins and /24 pairs equal the export "
      f"in {cp['origins_equal']}/{cp['windows']} windows")
sv = json.load(open(R + "stix_validation.json"))
good = (sv["ok"] and sv["errors"] == 0 and sv["warnings"] == 0 and sv["strict_errors"] == 0
        and all(c["valid_strict"] for c in sv["chains"]) and "validator in strict mode" in TEXN
        and sv["bundles"] == 4 and "passes the exported bundles through the OASIS STIX~2.1 validator in strict mode, the reference TAXII~2.1 server" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} {sv['bundles']} STIX bundles valid, strict included "
      f"({sv['errors']} errors, {sv['warnings']} warnings, {sv['strict_errors']} strict errors)")
si = json.load(open(R + "stix_ingest.json")); tx, mi = si["taxii"], si["misp"]
good = (tx["accepted_all"] and all(tx["identical_by_type"][t] for t in ("indicator", "course-of-action",
                                                                     "relationship", "identity"))
        and not tx["identical_by_type"]["extension-definition"]
        and "the reference TAXII~2.1 server (medallion 3.0.0), which returns them unchanged save the extension definition it fails to serve" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} TAXII 2.1: accepted, identical by type {tx['identical_by_type']}")
good = (mi["fingerprints_kept"] == 0 and mi["fingerprints_in_scope"] > 0 and mi["endpoint_kept_where_scoped"]
        and mi["course_of_action_kept"] and "MISP's importer drops the fingerprints" in TEXN
        and "an extension that the importer does not map to MISP's own JA4 object." in TEXN)
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
        and "By the rate times the median collateral, a rougher measure than the mean, the $0.5\\%$ share blocked about 25 times fewer legitimate clients per clean window on those days ($0.0028\\%$ against $0.070\\%$). It also stopped more of 100 attackers on new stacks ($44.6\\%$ against $30.9\\%$)" in TEXN
        and fp["eligible"] == ["0.05"] and len(d0) - 1 == 4
        and "Of four shares, only $5\\%$ had no more false alarms than the base rule on the first three test days, although $0.5\\%$ blocked about 25 times fewer legitimate clients and more of a 100-attacker botnet" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E, Table II: by rate x median collateral the 0.5% share is {ec(d5)/ec(d05):.1f}x lighter ({ec(d05)*100:.4f}% against {ec(d5)*100:.3f}%)")
fe = fp["fleets_per_endpoint"]["E1"]
good = sorted(set(fe["fleets"])) == [5, 6] and "five or six known fleets" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} E1 known fleets per fold: {fe['fleets']}")
lv = round(math.log10(float(np.median(fe["level"]))))
good = f"to about $10^{{{lv}}}$" in TEXN and round(math.log10(E["E1"]["scope_level_median"])) == -60
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} E1 level rises from 10^-60 to 10^{lv}")
good = (fp["eligible"] == [fp["chosen_share"]] and len(fp["design"]) == 5
        and f"only one whose false alarms did not exceed the base rule's ({d0[fp['chosen_share']]['false_alarms']} against {d0['base']['false_alarms']}, the others {min(v['false_alarms'] for s, v in d0.items() if s not in ('base', fp['chosen_share']))} to {max(v['false_alarms'] for s, v in d0.items() if s not in ('base', fp['chosen_share']))})" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} only one of four shares kept false alarms at or below the base rule's")
print("== generator: window sweep and the vocabulary-tail variant")
print("== cross-fitted calibration (production_tables.json: xfit, xfit_fleets, xfit_od)")
xb, xo, xz = TD["xfit_fleets"]["all"]["union|origins"], TD["xfit_od"]["all"]["union|origins"], TD["xfit"]["all"]["zcal|origins"]
xa = {"bin": TD["xfit_fleets"]["all"]["union|none"]["clean_rate"], "z": TD["xfit"]["all"]["zcal|none"]["clean_rate"],
      "z_E2": TD["xfit"]["per_endpoint"]["E2"]["zcal|none"]["clean_rate"], "beta": TD["xfit_od"]["all"]["union|none"]["clean_rate"],
      "beta_E2": TD["xfit_od"]["per_endpoint"]["E2"]["union|none"]["clean_rate"], "beta_fresh": FD["xfit_od"]["all"]["union|none"]["clean_rate"]}
good = (xb["clean_fires"] == 6 and fz["clean_fires"] == 5 and f"{xa['bin']*100:.1f}" == "1.9"
        and "the binomial configuration barely moves (Fig.~\\ref{fig:operating}), with 6 false alarms against 5" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: binomial scope alone {xa['bin']*100:.2f}%, {xb['clean_fires']} false alarms against {fz['clean_fires']}")
good = abs(xb["new:A100"]["blocked"] - fz["new:A100"]["blocked"]) < 0.03
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: the binomial stops {xb['new:A100']['blocked']*100:.1f}% against {fz['new:A100']['blocked']*100:.1f}% of 100 attackers")
zr = [FL["xfit"][e][f]["zcal_threshold"] / FL["base"][e][f]["zcal_threshold"] for e in ("E1", "E2", "E3", "E4") for f in tf]
good = f"which cross-fitting raises by a median factor of {st_.median(zr):.1f}" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: z threshold ratio median {st_.median(zr):.2f} (range {min(zr):.2f}--{max(zr):.2f})")
good = f"{xa['z']*100:.1f}" == "2.5" and "lead in detection came from its in-sample threshold" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: the z-score alone fires in {xa['z']*100:.2f}% (Table IV), its lead was in-sample")
chk("App. E: cross-fitted z-score at 100 attackers", "stops $33.6\\%$ of 100 attackers against $54.7\\%$", (xz["new:A100"]["blocked"]*100, zc["new:A100"]["blocked"]*100),
    "stops {:.1f} of 100 attackers against {:.1f}")
chk("cross-fit: beta-binomial alone", "its scope alone fires in $1.1\\%$ of clean windows", xa["beta"]*100, "its scope alone fires in {:.1f} of clean windows")
chk("App. E: cross-fitted beta-binomial on the held-out day", "its scope alone fires in $1.2\\%$ of the held-out day's windows", xa["beta_fresh"]*100,
    "its scope alone fires in {:.1f} of the held-out day's windows")
good = min(xa["beta"], xa["bin"], xa["z"]) == xa["beta"] and "Only the beta-binomial nearly meets its target out of sample" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: only the beta-binomial comes near its 1% target")
xl = [FL["xfit_od"][e][f]["log10_level"] for e in ("E1", "E2", "E3", "E4") for f in tf]
good = (max(xl) < -2 + 1e-9 and round(min(xl)) == -17 and round(max(xl)) == -2
        and "The beta-binomial's levels then fall to between $10^{-17}$ and $10^{-2}$" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: beta-binomial levels 10^{min(xl):.1f}..10^{max(xl):.1f}, {xo['clean_fires']} false alarms")
xk = [FL["xfit_od_fleets"]["E1"][f]["known_fleets"] for f in tf]
good = xk.count(1) == 3 and xk.count(0) == 2 and "and one known fleet appears on the busiest endpoint on three of the five days" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: E1 known fleets under the beta-binomial {xk}")

xs1, xsS = exactW("xfit_od", "E1"), [exactW("xfit_od", e) for e in ("E2", "E3", "E4")]
good = ("Its floor on the rare shared stacks of Table~\\ref{tab:floor} is below the binomial's cross-fitted floor on every endpoint" in TEXN
        and all(exact("xfit_od", e) < dA("xfit_fleets", e, "shared") for e in ("E1", "E2", "E3", "E4"))
        and "below the binomial's cross-fitted floor on every endpoint" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: beta-binomial shared floors {xs1*100:.1f}% and {[round(x, 2) for x in xsS]}")
shB = [dA("xfit_fleets", e, "shared") for e in ("E1", "E2", "E3", "E4")]; shO = [exact("xfit_od", e) for e in ("E1", "E2", "E3", "E4")]
good = (xo["clean_fires"] == xb["clean_fires"] and xo["clean_collateral_median"] < xb["clean_collateral_median"] and xo["flash1000"] < xb["flash1000"]
        and all(o < b for o, b in zip(shO, shB)) and xz["new:A100"]["blocked"] < xb["new:A100"]["blocked"] + 0.05)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: cross-fitted, the beta-binomial matches the binomial's false alarms with lower shared floors {shO} vs {shB}")
good = ("A first design of the cross-fitting, which calibrated on the last calibration day alone, was dropped" in TEXN
        and "The beta-binomial and a cross-fitted calibration were built after the held-out day was read, so their results are post hoc" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the dropped cross-fit design and the post hoc status are disclosed")
print("== the WAF's verdicts (waf_labels.json)")
WL = json.load(open(R + "waf_labels.json")); WC, WA = WL["clean_profile"]["test_days"], WL["all_profile"]["test_days"]
good = (WL["clean_profile"]["check"]["zscore_mismatches"] == 0 == WL["all_profile"]["check"]["zscore_mismatches"]
        and not WC["E1"]["waf_clients"] and all(WC[e]["windows_with_waf"] == WC[e]["windows"] for e in ("E2", "E3", "E4")))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF: z-score recomputed with 0 mismatches under both profiles; blocks in every window of E2-E4, none on E1")
chk("WAF: blocked share of the window", "a median $9\\%$, $63\\%$ and $39\\%$ of each window's clients on E2 to E4, and none on E1",
    tuple(WC[e]["waf_share_median"]*100 for e in ("E2", "E3", "E4")), "a median {:.0f}, {:.0f} and {:.0f} of each window's clients on E2 to E4, and none on E1")
CF = ("binomial", "beta-binomial", "z-score")
pc = [WC[e]["scores"][c]["precision"] for e in ("E3", "E4") for c in CF]
chk("WAF, profile without blocked clients: precision", "$84$--$99\\%$ of the clients the scopes would block on the full traffic of the API and single sign-on were blocked by the WAF",
    (min(pc)*100, max(pc)*100), "{:.0f}--{:.0f} of the clients the scopes would block on the full traffic of the API and single sign-on were blocked by the WAF")
fl_ = WL["clean_profile"]["implied_precision_floor"]
chk("WAF: the implied precision floor", "only if $70$--$88\\%$ of its clients were blocked", (min(fl_.values())*100, max(fl_.values())*100),
    "only if {:.0f}--{:.0f} of its clients were blocked")
pa = [WA[e]["scores"][c]["precision"] for e in ("E2", "E3", "E4") for c in CF]
br = [WA[e]["base_rate"] for e in ("E2", "E3", "E4")]
good = (f"{min(pa)*100:.1f}" == "0.4" and f"{max(pa)*100:.0f}" == "33"
        and max(WA[e]["scores"][c]["lift"] for e in ("E2", "E3", "E4") for c in CF) < 1
        and f"{min(br)*100:.0f}" == "10" and f"{max(br)*100:.0f}" == "63"
        and "With a profile of all clients, only $0.4$--$33\\%$ of the clients the three profile-relative scopes would block were blocked, less than a random pick ($10$--$63\\%$) on every endpoint" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF, all-client profile, E2-E4: precision {min(pa)*100:.1f}--{max(pa)*100:.1f}% vs random {min(br)*100:.1f}--{max(br)*100:.1f}%, lift below 1 everywhere")
dets = [WA[e]["surges"]["detected"][c] for e in ("E3", "E4") for c in CF]
chance = [WA[e]["surges"]["expected_by_chance"][c] for e in ("E3", "E4") for c in CF]
eps_ = WA["E3"]["surges"]["episodes"] + WA["E4"]["surges"]["episodes"]
good = (min(dets) == 0 and max(dets) == 2 and eps_ == 38 and f"{max(chance):.1f}" == "0.5"
        and "On the API and single sign-on the scopes catch at most 2 of the WAF's 38 surges (Appendix~\\ref{app:window})" in TEXN
        and all(json.load(open(R + "waf_labels.json"))["all_profile"]["test_days"]["E2"]["surges"]["scores"][s]["recall"] < 0.01 for s in ("binomial", "beta-binomial", "z-score"))
        and "With the profile of all clients, the scopes catch the WAF's surges clearly above chance only on the console, and there with under $1\\%$ of the blocked clients" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF surges on E3+E4: {eps_} episodes, detected {min(dets)}--{max(dets)}, chance at most {max(chance):.2f}")
S2 = WA["E2"]["surges"]
e2d = [S2["detected"][c] for c in ("beta-binomial", "z-score")]
e2c = [S2["expected_by_chance"][c] for c in ("beta-binomial", "z-score")]
e2r = [S2["scores"][c]["recall"] for c in ("beta-binomial", "z-score")]
good = (e2d == [5, 5] and S2["detected"]["binomial"] == 0 and S2["episodes"] == 33 and max(e2c) < 1 and max(e2r) < 0.01
        and "clearly above chance only on the console, and there with under $1\\%$ of the blocked clients" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF surges on E2: detected {e2d} of {S2['episodes']}, chance {[round(x, 2) for x in e2c]}, recall {[round(x*100, 2) for x in e2r]}%")
mr = [WC[e]["scores"]["modal"]["recall"] for e in ("E2", "E3", "E4")]; nc = [WC[e]["ceiling"]["no_clean"] for e in ("E2", "E3", "E4")]
good = (round(min(mr) * 100) == 13 and round(max(mr) * 100) == 55 and max(nc) < 0.5
        and "Most clients the WAF blocked sat on fingerprints that unblocked clients also present" in TEXN
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
good = round(hrs) == 17 and "committed 17 hours after the time it states" in TEXN
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
good = all(round(x * 100) == 90 for x in pr) and max(pf) == 0 and "The calibrated test blocks $90\\%$ of a botnet on up to 25 new stacks with no observed collateral" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the binomial test blocks 90% up to 25 stacks at zero FPR")
good = (fmt(fz["clean_rate"]) == "0.1" and 0.30 <= fz["clean_collateral_median"] <= 0.36
        and "it misfires in $0.1\\%$ of attack-free five-minute windows on the days it was chosen on, but each misfire blocks a median third of the window's clients" in ab)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: the binomial configuration misfires on {fz['clean_rate']*100:.2f}%, each misfire blocking a median {fz['clean_collateral_median']*100:.1f}%")
grows = all(dA("fleets", e, k, 5) < dA("fleets", e, k, 25) < dA("fleets", e, k, 100) for e in ("E1", "E2", "E3", "E4") for k in ("new", "shared"))
good = grows and "Calibration has a price: legitimate client fleets raise a floor" in ab and "legitimate fleets raise a calibration floor" in TEXN and "The floor grows with the stacks" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract, V-B: every floor grows from 5 to 25 to 100 stacks")
# the floor's values left the abstract in round 33; V-B states them
good = (f"{shF*100:.0f}" == "8" and f"{min(shS):.0f}" == "4" and f"{max(shS):.0f}" == "19"
        and "is singled out only once it is large" in ab
        and "A typical stack is then named only past 254 attackers on the busiest endpoint, $8\\%$ of its window, and past 4 to 19 times the median window on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract, V-B: the floor on shared stacks, {shF*100:.0f}% of E1's window and {min(shS):.0f} to {max(shS):.0f} windows elsewhere")
good = min(share) > 0.5 and "The 4 to 28 most common fingerprints of each endpoint, which carry" in TEXN   # left the abstract in round 31
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: never named on the fingerprints carrying most origins ({min(share)*100:.0f}%+)")
good = (round(sw1["new:M25:x0.1"]["blocked"] * 100) == 12 and sw1["new:M25:x0.1"]["gate"] < 0.2
        and round(TD["fleets"]["per_endpoint"]["E1"]["union|none"]["new:x0.1"]["blocked"] * 100) == 90
        and "On the busiest endpoint the alarm's trigger also lets most of a small injected botnet through" in ab)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the trigger lets most of a small botnet through ({sw1['new:M25:x0.1']['gate']*100:.1f}%), {sw1['new:M25:x0.1']['blocked']*100:.1f}% stopped")
un1 = TD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["new:x0.1"]["blocked"]
unmax = max(B["fleets"]["per_endpoint"][e]["unseen|none"]["clean_rate"] for B in (TD, FD) for e in ("E1", "E2", "E3", "E4"))
sh15 = TD["xfit_od"]["per_endpoint"]["E1"]["union|seasonal"]["shared:x0.1"]["blocked"]
good = (round(un1 * 100) == 90 and unmax <= 0.01 and round(sh15 * 100) == 15
        and TD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["clean_rate"] <= 0.01
        and TD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["shared:x0.1"]["blocked"] == 0
        and "and other triggers, examined post hoc, recover part of it" in ab)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: the unseen filter as its own trigger stops {un1*100:.1f}% (misfires at most {unmax*100:.2f}%); the alternative stops {sh15*100:.1f}% on shared stacks")
good = pv >= 0.05 and pw < 0.5 and gw == 3 and "A held-out day is consistent with that rate but provides limited additional evidence" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the held-out day is consistent")
good = (cp["origins_equal"] == cp["windows"] and cpf["origins_equal"] == cpf["windows"] and cp["net24_pairs_equal"] == cp["windows"]
        and "The compiled query returned the exported origin and /24-pair counts in every window of two production days" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: the compiled query reproduces origins and /24 pairs")
good = (mi["fingerprints_kept"] == 0 and mi["fingerprints_in_scope"] > 0
        and "we specify the filter and the counts it reads in an OWL ontology, since no exchange standard we examined expresses such a filter in its core vocabulary" in ab
        and "An OWL ontology specifies the counts the decision reads and the scope it exports, and the log store's query is compiled from it" in TEXN
        and "No exchange standard we examined expresses the resulting JA4 filter in its core vocabulary" in TEXN
        and "Of the standards we examined, STIX~2.1, DOTS and Flowspec have no JA4 property in their core vocabulary, and OCSF records JA4 fingerprints in network events and in the evidence of findings~\\cite{ocsf2025schema} but defines no filter or remediation over them" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract, contribution (iii), VI: JA4 only in a STIX extension, dropped by MISP's importer; OCSF records it with no filter (external, checked on its schema)")
e1r_ = [dF(r, "E1", k) for r in ("fleets", "od", "xfit_fleets", "xfit_od") for k in ("new", "shared")]
good = (max(e1r_) < 0.1
        and "A typical stack is then named only past 254 attackers on the busiest endpoint, $8\\%$ of its window" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: every E1 floor under a tenth of the window ({[round(x*100, 1) for x in e1r_]}%)")
xso = TD["xfit_od"]["per_endpoint"]["E1"]
good = (unmax <= 0.01 and same and xso["union|seasonal"]["shared:x0.1"]["blocked"] > 0
        and 0.005 <= a1["clean_rate"] <= 0.015 and b1["clean_fires"] == 92
        and [bf1[f] for f in tf] == [0, 0, 1, 5, 8]
        and "Its baseline, the unseen filter as its own trigger, matched every scope of Table~\\ref{tab:triggers} on new stacks of at least $k_{\\min}$ origins within the budget everywhere, pooled over the days, with $90\\%$ of 1\\,000 attackers on each small endpoint (Appendix~\\ref{app:window})" in TEXN
        and "would compare post hoc triggers on 100 attackers and on a tenth of the window" in TEXN
        and all(round(PT[blk][run]["per_endpoint"][e][sc]["new:A1000"]["blocked"] * 100, 1) == 90.0
                for blk in ("test_days", "fresh_day") for run in ("fleets", "xfit_od") for e in ("E2", "E3", "E4")
                for sc in ("union|origins", "union|seasonal", "union|none", "unseen|origins", "unseen|seasonal", "unseen|none"))
        and "On each small endpoint every scope of Table~\\ref{tab:triggers} stops $90.0\\%$ of 1\\,000 attackers on new stacks under every trigger, on test and held-out days" in TEXN
        and TD["xfit_od"]["per_endpoint"]["E1"]["union|seasonal"]["new:x0.1"]["blocked"] < 0.25 * TD["fleets"]["per_endpoint"]["E1"]["unseen|none"]["new:x0.1"]["blocked"]
        and all(TD["xfit_od"]["per_endpoint"][e]["union|seasonal"]["new:A100"]["blocked"] > TD["fleets"]["per_endpoint"][e]["unseen|none"]["new:A100"]["blocked"] for e in ("E2", "E3", "E4"))
        and "Against it would run the cross-fitted beta-binomial behind the seasonal gate, which gains on shared stacks everywhere and on smaller new stacks on the small endpoints but loses most new-stack detection on the busiest one." in TEXN
        and "\\1~\\textit{Now} we would deploy the binomial configuration on every endpoint, with the fallback below its floor, because behind the distinct-origin gate it alone was tested on a day it had not seen, as fixed in advance. A botnet that leaves the gate shut meets neither filter nor fallback on any endpoint, so on the busiest one the configuration stops few small botnets, none on the held-out day. On the console, where both held-out false alarms fell, a challenge may be the safer first response. \\2~\\textit{Next}, a test pre-specified on new days over a weekly cycle with an external timestamp would compare post hoc triggers" in TEXN
        and PT["stealth_E1"]["fleets"]["fresh:x0.1"]["2026-09-25"]["blocked"] == 0
        and FD["fleets"]["per_endpoint"]["E2"]["union|origins"]["clean_fires"] == FD["fleets"]["all"]["union|origins"]["clean_fires"] == 2
        and all(0.13 <= PT["sweep"]["fleets"][e]["new:M25:x1"]["gate"] <= 0.33 for e in ("E2", "E3", "E4"))
        and "A botnet of one median window opens it in only $14$--$33\\%$." in TEXN
        and f"{FD['xfit_od']['per_endpoint']['E1']['union|none']['clean_rate']*100:.2f}" == "1.74"
        and "The cross-fitted beta-binomial as its own trigger is left out, since it fired in $1.74\\%$ of that endpoint's held-out windows" in TEXN
        and "On the busiest endpoint the binomial scope with known fleets as its own trigger would run too: it sits at the budget there, but its false alarms rise by day and it rests on the fleet exemption" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} VI: the next test's baseline, the unseen filter as its own trigger, within the budget everywhere; the beta-binomial's gain on shared stacks {xso['union|seasonal']['shared:x0.1']['blocked']*100:.1f}%")
nwW = [dF("fleets", e, "new") for e in ("E2", "E3", "E4")]
good = ("the binomial configuration names shared stacks only past 4 to 19 windows and new stacks from 2 to 4 windows" in TEXN
        and min(nw[1:]) == 84 and max(nw[1:]) == 139 and round(min(nwW)) == 2 and round(max(nwW)) == 4)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: the small endpoints' floors and the new-stack filter range")
good = (xb["clean_fires"] <= fz["clean_fires"] + 1 and ff_["clean_fires"] == 2 and pv >= 0.05 and alone["bin"] > 0.01
        and gw == 3 and ff_["clean_fires"] == 2
        and "The binomial configuration's false alarms stay at $0.1\\%$ of clean windows on the days it was chosen on. A held-out day on which its gate barely opened is consistent with that rate, though the scope misfired in 2 of the 3 windows where the gate did open. On the busiest endpoint the gate lets most of a small botnet through" in TEXN
        and "only past $8\\%$ of the busiest endpoint's window and 4 to 19 windows on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: the binomial configuration holds its rate out of sample, its scope alone does not")
good = (all(o < b for o, b in zip(shO, shB)) and round(un1 * 100) == 90 and unmax <= 0.01 and round(sh15 * 100) == 15
        and "Post hoc, the unseen filter as its own trigger stops $90\\%$ of it on new stacks of $k_{\\min}$ origins or more within the budget, and a cross-fitted beta-binomial behind a seasonal gate stops $15\\%$ of it on shared stacks but gives up most new-stack detection" in TEXN
        and "Next come the pre-specified test of Section~\\ref{sec:discussion}, HTTP/2 attacks and a captured stealthy campaign" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: post hoc, the unseen filter as its own trigger on new stacks, the test on shared stacks behind the seasonal gate")
good = ("so no attack label is involved" in TEXN and "The evaluation places the scope behind the operator's WAF, so the profiles and floors describe the clients the WAF lets through" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-C, IV-A: no attack label; the profile excludes WAF-blocked clients, the scope runs behind the WAF")
SDV = json.load(open(R + "symbolic_detector.json"))["aggregate"]["1.5:25:1"]
good = f"{SDV['rf_recall_fpr1']*100:.1f}" == "23.4" and "the modal fingerprint $3.6\\%$ at $39.0\\%$ and the learned model $23.4\\%$ at $1\\%$" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-A: the learned model on the adversarial botnet at 1% FPR, {SDV['rf_recall_fpr1']*100:.1f}%")
good = 240 <= ok + bad + 1 <= 290 and "recomputes about 250 of the printed numbers" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. F: the audit recomputes about 260 numbers ({ok + bad})")
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
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} Table VII: 9 rows x 9 cells from production_tables.json" + ("" if good else f" got={gotT} exp={expT}"))
g1 = TD["fleets"]["per_endpoint"]["E1"]["gates_clean"]["origins"]
chk("V-B: the distinct-origin gate alone, pooled and on E1", "and the distinct-origin gate alone fires in $3.0\\%$, $5.4\\%$ on the busiest endpoint",
    (TD["fleets"]["all"]["gates_clean"]["origins"]*100, g1*100), "and the distinct-origin gate alone fires in {:.1f}, {:.1f} on the busiest endpoint")
f5, f100 = dA("fleets", "E1", "shared", 5), dA("fleets", "E1", "shared", 100)
r5, r100 = dF("fleets", "E1", "shared", 5), dF("fleets", "E1", "shared", 100)
w5 = [dF("fleets", e, "shared", 5) for e in ("E2", "E3", "E4")]; w100 = [dF("fleets", e, "shared", 100) for e in ("E2", "E3", "E4")]
fM = {M: [dA("fleets", e, "shared", M) for e in ("E1", "E2", "E3", "E4")] for M in (5, 100)}
good = ((f5, f100) == (50, 1026) and round(r5 * 100) == 2 and round(r100 * 100) == 34
        and fM[5] == [50, 164, 28, 17] and fM[100] == [1026, 6158, 1017, 454]
        and "The floor grows with the stacks, from $2\\%$ of the busiest window at 5 stacks to $34\\%$ at 100" in TEXN
        and "the shared-stack floor for 5 and 100 stacks is 50 and 1\\,026 attackers on E1, 164 and 6\\,158 on E2, 28 and 1\\,017 on E3 and 17 and 454 on E4" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared floors at 5 and 100 stacks: E1 {f5} and {f100} ({r5*100:.1f}% and {r100*100:.1f}%), small {min(w5):.1f}--{max(w5):.1f} and {min(w100):.1f}--{max(w100):.1f} windows")
e4t, e4f = TD["fleets"]["per_endpoint"]["E4"]["union|origins"], FD["fleets"]["per_endpoint"]["E4"]["union|origins"]
cc4 = PT["flash_concentration"]["fresh_day"]["E4"]
good = (f"{e4f['flash1000']*100:.1f}" == "97.2" and f"{e4t['flash1000']*100:.1f}" == "34.1" and f"{e4f['flash1000_collateral_median']*100:.1f}" == "1.1"
        and FD["fleets"]["per_endpoint"]["E4"]["unseen|origins"]["flash1000"] == 0 and cc4["top_fingerprint_share"] >= 0.9
        and PT["endpoints"]["E4"] == "SSO"
        and f"{FD['xfit_od']['per_endpoint']['E4']['union|seasonal']['flash1000']*100:.1f}" == "97.6"
        and "On the single sign-on, crowds of 1\\,000 users, also beyond the protocol, trigger it in $97.2\\%$ of windows against $34.1\\%$ on the test days, nearly all on one fingerprint more common that day (Appendix~\\ref{app:window})" in TEXN
        and PT["flash_concentration"]["fresh_day"]["E4"]["fires"] == 280 and f"{PT['flash_concentration']['fresh_day']['E4']['top_fingerprint_share']*100:.1f}" == "98.2"
        and "The configuration's 280 firings on the single sign-on's 1\\,000-user crowds that day name one fingerprint in $98.2\\%$ of cases, and its filters there block a median $1.1\\%$ of the window's clients. The same crowds trigger the post hoc seasonal gate's cross-fitted beta-binomial in $97.6\\%$ of that day's windows" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: E4's held-out crowds of 1,000: {e4f['flash1000']*100:.1f}% vs {e4t['flash1000']*100:.1f}%, {cc4['top_fingerprint_share']*100:.1f}% of {cc4['fires']} firings on one fingerprint, median filter {e4f['flash1000_collateral_median']*100:.1f}%")
fc = [TD["fleets"]["per_endpoint"][e]["union|origins"]["flash1000_collateral_median"] * 100 for e in ("E2", "E3", "E4")]
good = ([f"{x:.1f}" for x in fc] == ["7.1", "18.6", "2.7"] and f"{fz['flash1000_collateral_p90']*100:.1f}" == "20.6"
        and "its filters block a median $7.1\\%$, $18.6\\%$ and $2.7\\%$ of the window's clients on E2 to E4, and $20.6\\%$ at the 90th percentile" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: flash-crowd filters per endpoint {[round(x, 1) for x in fc]}%, p90 {fz['flash1000_collateral_p90']*100:.1f}%")
FPj = json.load(open(R + "fleet_profile.json"))["fleets_per_endpoint"]["E1"]
good = (all(0.065 <= s <= 0.075 for s in FPj["profile_share"]) and set(FPj["fleets"]) <= {5, 6}
        and "on the busiest endpoint of fingerprints that carry about $7\\%$ of its profile" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D: E1's known fleets carry {min(FPj['profile_share'])*100:.1f}--{max(FPj['profile_share'])*100:.1f}% of its profile")
good = "$1.2\\%$ for $M = 25$ and $\\rho = 3$" in TEXN and "and there the ratio sets a harder limit" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D: the ratio limit is stated for rho = 3")
x36 = st_.median(x["beta_binomial"] for x in bB("xfit_od", "E1", "ranks_36_100", ""))
good = (x36 == 949 and b36 == 743 and o36 == 480
        and [st_.median(x["beta_binomial"] for x in bB("xfit_od", e, "ranks_36_100", "")) for e in ("E2", "E3", "E4")] == [509, 255, 84]
        and [st_.median(x["binomial"] for x in bB("fleets", e, "ranks_36_100", "")) for e in ("E2", "E3", "E4")] == [1898, 227, 84]
        and "though not everywhere on more common stacks against the in-sample binomial (Appendix~\\ref{app:window})" in TEXN
        and "the cross-fitted beta-binomial's floor on those ranks is also higher on the API (255 against 227), equal on the single sign-on and lower on the console (509 against 1\\,898)" in TEXN
        and "falls from 743 attackers under the binomial to 480 under the beta-binomial in sample, and rises to 949 cross-fitted" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D, App. E: E1 ranks 36-100 floor {b36} binomial, {o36} beta-binomial in sample, {x36} cross-fitted")
ufd = {e: TD["fleets"]["per_endpoint"][e]["unseen|none"]["clean_fires_by_fold"] for e in ("E1", "E2", "E3")}
good = (max(ufd["E1"].values()) == sum(ufd["E1"].values()) == 4 and max(ufd["E2"].values()) == sum(ufd["E2"].values()) == 2
        and max(ufd["E3"].values()) == 5 and sum(ufd["E3"].values()) == 6
        and "As its own trigger the unseen filter's misfires cluster by day: all 4 on the busiest endpoint and both on the console fall on one day, and 5 of the API's 6 on another" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: the unseen filter's own-trigger misfires by day {ufd}")
SI = json.load(open(R + "stix_ingest.json"))["versions"]
CPN = json.load(open(R + "compile_production_check.json"))
good = (SI["medallion"] == "3.0.0" and SI["misp-stix"] == "2026.9.16" and "the export drops such clients" in CPN["note"]
        and "(medallion 3.0.0)" in TEXN and "(misp-stix 2026.9.16)" in TEXN
        and "which reproduced the exported origin and /24-pair counts, and the JA4 pair counts where the WAF blocked no client (Appendix~\\ref{app:repro})" in TEXN
        and "It ran in the operator's log store, the artifact keeps only its counts, and the production evaluation reads the exports" in TEXN
        and "Elsewhere the export drops the clients the WAF partly blocked, which the compiled filter keeps" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI, App. F: what the compiled query reproduced, tool versions {SI}")
hs = lambda run, k: FD[run]["per_endpoint"]["E1"][k]["shared:x0.1"]["blocked"] * 100
hf = [FD[r_]["all"][k]["flash1000"] * 100 for r_ in ("fleets", "xfit_od") for k in ("union|origins", "union|seasonal", "union|none")]
good = ([f"{hs(r_, k):.1f}" for r_, k in (("fleets", "union|origins"), ("xfit_od", "union|origins"), ("fleets", "unseen|origins"))] == ["0.0"] * 3
        and [f"{hs(r_, k):.1f}" for r_, k in (("fleets", "union|seasonal"), ("xfit_od", "union|seasonal"), ("fleets", "unseen|seasonal"))] == ["11.9", "14.3", "0.0"]
        and [f"{hs(r_, k):.1f}" for r_, k in (("fleets", "union|none"), ("xfit_od", "union|none"), ("fleets", "unseen|none"))] == ["66.1", "83.3", "0.0"]
        and (f"{min(hf):.1f}", f"{max(hf):.1f}") == ("24.5", "25.1") and f"{FD['fleets']['all']['unseen|none']['flash1000']*100:.1f}" == "0.1"
        and "shared-stack cells read 0.0 (origin gate), 11.9, 14.3 and 0.0 (seasonal gate) and 66.1, 83.3 and 0.0 (no gate), and its flash-crowd cells $24.5$--$25.1\\%$ for the calibrated scopes against $0.1\\%$ for the unseen filter" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: Table VII's held-out shared and flash-crowd cells (flash {min(hf):.1f}--{max(hf):.1f}%)")
good = ("and past 4 to 19 times the median window on the small ones, as medians of the daily ratios" in TEXN
        and round(dF("fleets", "E1", "shared") * 100) == 8 and round(max(shS)) == 19)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the floor ratios are medians of the daily ratios")
print(f"\nTOTAL: {ok} OK, {bad} mismatches")
sys.exit(1 if bad else 0)
