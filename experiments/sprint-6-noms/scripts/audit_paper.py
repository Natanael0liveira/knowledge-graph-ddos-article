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
good = CR["alpha"] == 1.5 and CR["stacks"] == 25 and CR["seeds"] == 30 and "($\\alpha = 1.5$, $M = 25$, $n = 30$ seeds)" in TEXN
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
chk("V-A: Cohen's d", "Cohen's $d = 13.5$ and $22.3$", (t["d_vs_c"]["cohens_d"], t["d_vs_a"]["cohens_d"]), "Cohen's d = {:.1f} and {:.1f}")
tr = [au(K, f, "d") for K in (50, 1000) for f in ("rf", "hgb")]
chk("App. C: tree ensembles on (d)", "carve out the band one $M$ produces ($0.92$--$0.99$)", (min(tr), max(tr)),
    "carve out the band one M produces ({:.2f}--{:.2f})")
chk("V-A: the perceptron on (d)", "the perceptron reaches $0.86$ and $0.95$", (au(50, "mlp", "d"), au(1000, "mlp", "d")), "the perceptron reaches {:.2f} and {:.2f}")
chk("V-A: logistic regression on (d)", "is monotone, $0.87$ and $0.80$", (au(50, "logreg", "d"), au(1000, "logreg", "d")), "is monotone, {:.2f} and {:.2f}")
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
chk("V-A: (d) across stack counts", "its AUC falls from $0.93$--$0.98$ to $0.48$--$0.75$", (au(50, "rf", "d"), au(1000, "rf", "d"), min(xs), max(xs)),
    "its AUC falls from {:.2f}--{:.2f} to {:.2f}--{:.2f}")
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
good = f"{v*100:.2f}" == "0.03" and f"{vm*100:.1f}" == "0.5" and "mean FPR $0.03\\%$ (at most $0.5\\%$ in one seed)" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:symbolic note: unseen FPR mean {v*100:.3f}%, largest seed {vm*100:.2f}%")
zf0 = [us("original", s, 0, "zscore", "fpr") for s in (1, 5, 25, 100)]
good = (max(zf0) == 0 and f"{us('shared_profile_tail', 25, 0, 'zscore', 'fpr')*100:.2f}" == "3.37"
        and f"{us('original', 25, 1, 'zscore', 'fpr')*100:.1f}" == "11.3"
        and "FPR $0\\%$ except $3.37\\%$ (shared) and $11.3\\%$ (adversarial)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:symbolic note: z-score FPR 0 except shared and adversarial")
mf = [us("original", s, a_, "modal", "fpr") for s, a_ in ((5, 0), (25, 0), (100, 0), (25, 1))] + [us("shared_profile_tail", 25, 0, "modal", "fpr")]
good = (us("original", 1, 0, "modal", "fpr") == 0 and all(f"{x*100:.1f}" == "39.0" for x in mf)
        and f"{us('original', 25, 0, 'modal', 'fpr', alpha=2.0)*100:.1f}" == "61.1"
        and "Modal: the alarm's most common fingerprint, FPR $0\\%$ at $M{=}1$ (monolithic) and $39.0\\%$ elsewhere ($61.1\\%$ with $\\alpha = 2.0$)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:symbolic note: modal FPR 0 at M=1, 39.0% elsewhere, 61.1% at alpha 2.0")
print("== Section V-B text")
good = all(abs(us("original", s, 0, "zscore", "recall") - us("original", s, 0, "enrichment", "recall")) < 5e-4
           and us("original", s, 0, "zscore", "fpr") == 0 for s in (5, 25)) and "The binomial test and the $z$-score block $90.0\\%$ and $90.3\\%$ of the attack at five and 25 stacks" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the z-score blocks as the test at 5 and 25 stacks, zero FPR")
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
    print(f"{'OK ' if good else 'XX '} tab:perwindow {kind:14s} printed={printed} data={exp} (windows in csv {len(x)})")
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
v = c["collateral_pipeline_median"]; good = 0.4 <= v <= 0.6 and "blocking about half of that window's clients" in TEXN
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
vb = P["volume_baseline"]; lo, hi = vb["agreement_range"]
good = f"${lo*100:.0f}$--${hi*100:.1f}\\%$" in TEX; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: Omega vs origin threshold agree {lo*100:.1f}--{hi*100:.1f}%")
more = all(x["origins"] >= x["omega"] for x in list(vb["attack_fresh_M25"].values()) + list(vb["attack_relative_M25"].values()))
ok += more; bad += not more; print(f"{'OK ' if more else 'XX '} V-D: the origin threshold catches at least as many attacks")
good = vb["clean_omega_only"]["windows"] == 13 and vb["clean_omega_only"]["scope_named"] == 8 and \
    "The 13 clean windows that only $\\Omega$ admits, 8 of them with the scope firing" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: eight clean windows only Omega admits, scope firing: {vb['clean_omega_only']}")
chk("App. E: their share of Omega outside the endpoint term", "$33\\%$ of their", vb["clean_omega_only"]["non_endpoint_share_median"]*100, "{:.0f} of their")
elsew = [vb["clean_origins_only"]["non_endpoint_share_median"], vb["clean_both"]["non_endpoint_share_median"]]
good = all(round(x*100) in (11, 12) for x in elsew) and "against $12\\%$ elsewhere" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: 12% elsewhere: {[round(x*100,1) for x in elsew]}")
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

print("== tab:production and tab:perendpoint (production_tables.json)")
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
        if "Test days, in sample" in l: group = "in"; continue
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
                     + [("fresh", n) for n in ("rule", "binomial", "beta-bin.", "$z$-score")]),
                    ("tab:perendpoint", [(e, n) for e in ("E1", "E2", "E3", "E4") for n in ("binomial", "beta-bin.")])):
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
good = "$^{*}$Built after the held-out day was read" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:production note: the beta-binomial marked as built after the held-out day")
nfa = {e: [TD[r]["per_endpoint"][e][f"{s}|origins"]["clean_fires"] for r, s in (("fleets", "union"), ("od", "union"))] for e in ("E1", "E2", "E3", "E4")}
good = (min(nfa["E2"]), max(nfa["E2"])) == (4, 19) and max(max(nfa[e]) for e in ("E1", "E3", "E4")) == 2 \
    and "Coll. is a median over few alarms: 4 to 19 on E2, at most 2 elsewhere" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:perendpoint note: alarms per endpoint {nfa}")
kf = {r: [FL[r][e][f]["known_fleets"] for e in FL[r] for f in FL[r][e]] for r in FL}
same = all(TD["od"][k] == TD["od_fleets"][k] and FD["od"][k] == FD["od_fleets"][k] for k in ("all", "per_endpoint"))
good = (max(kf["od_fleets"]) == 0 and same and "no fingerprint qualifies as a known fleet in sample" in TEXN
        and "& beta-bin. & --             & post hoc" in TEX)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: beta-binomial names no known fleet in any fold in sample ({max(kf['od_fleets'])}), identical with the fleet profile: {same}")
good = ("Five choices were made on the test days: counting origins, calibrating $\\lambda_e$, the gate, the union with the unseen filter and the $5\\%$ fleet share" in TEXN
        and "Post hoc: after the held-out day was read, as was the cross-fitted calibration" in TEXN)
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
good = PT["endpoints_exported"] == 12 and "They are the four of the 12 exported that carry TLS with a median window of at least $k_{\\min}$ origins" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} IV: the four evaluated endpoints of the {PT['endpoints_exported']} exported")
good = (all(FPD["fleets"][e][f]["25"]["new"]["min_attackers"] == math.ceil(5 * 25 / 0.9) and FPD["fleets"][e][f]["25"]["new"]["set_by"] == "unseen"
            for e in ("E1", "E2", "E3") for f in tf) and "On new stacks the unseen filter bounds it at 139" in TEXN
        and "from $\\lceil k_{\\min} M/0.9 \\rceil$ attackers whatever the level, 139 for $M = 25$" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D, tab:floor: the unseen filter sets the new-stack floor at 139 attackers on E1-E3")
good = ("A shared stack takes the median prevalence past the profile's ten most common fingerprints and, under the beta-binomial, their median correlation" in TEXN
        and FB["bands"]["ranks_11_plus"] == [11, None])
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:floor caption: shared stacks at the tail's median prevalence and correlation")
lim = 0.9 / (3.0 * 25)
above = [FB["per_endpoint"][e][f]["fingerprints_above_limit"] for e in ("E1", "E2", "E3", "E4") for f in tf]
share = [FB["per_endpoint"][e][f]["origin_share_above_limit"] for e in ("E1", "E2", "E3", "E4") for f in tf]
good = (f"{lim*100:.1f}" == "1.2" and all(abs(FB["per_endpoint"][e][f]["enrichment_limit"] - lim) < 1e-12 for e in ("E1", "E2", "E3", "E4") for f in tf)
        and "no botnet on $M$ stacks is enriched on a fingerprint of prevalence above $0.9/(\\rho M)$, $1.2\\%$ for $M = 25$" in TEXN
        and (min(above), max(above)) == (4, 28) and round(min(share) * 100) == 86 and round(max(share) * 100) == 94
        and "the 4 to 28 most common fingerprints of each endpoint, which carry $86$--$94\\%$ of its origins, are never enriched by a 25-stack botnet" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-D, V-B: the ratio limit 0.9/(rho M) = {lim:.3f}; {min(above)}--{max(above)} fingerprints above it carry {min(share)*100:.1f}--{max(share)*100:.1f}% of origins")
b36 = st_.median(x["binomial"] for x in bB("fleets", "E1", "ranks_36_100", ""))
o36 = st_.median(x["beta_binomial"] for x in bB("od", "E1", "ranks_36_100", ""))
good = (b36 == 743 and o36 == 480
        and "on ranks 36 to 100 the busiest endpoint's floor rises to 743 attackers under the binomial and to 480 under the beta-binomial" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B, V-C: E1 floors on profile ranks 36-100, binomial {b36}, beta-binomial {o36}")
tailb = [FB["per_endpoint"][e][f]["tail_prevalence_median"] for e in ("E1",) for f in tf]
good = max(tailb) < 1e-5 and "The shared stacks come from the profile past its ten most common fingerprints, mostly rare ones" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared stacks are mostly rare (E1 tail median prevalence {max(tailb):.1e})")

print("== Section V-B prose (production_tables.json)")
f1 = FL["base"]["E1"]
so = sorted(f1[f]["new"]["min_stack_origins"] for f in tf)
good = f"past {so[0]} to {so[-1]} origins" in TEXN and round(math.log10(lvl("base", "E1"))) == -60 and "fleets push $\\lambda_e$ to $10^{-60}$" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: E1 level 10^-60 names a stack only past {so[0]} to {so[-1]} origins")
kn = sorted(set(FL["fleets"]["E1"][f]["known_fleets"] for f in tf))
good = kn == [5, 6] and "five or six known fleets" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: E1 exempts {kn} known fleets per test day")
nw = [dA("fleets", e, "new") for e in ("E1", "E2", "E3", "E4")]
good = nw == [139, 139, 139, 84] and "on new stacks from 139 attackers per window on E1 to E3, a bound $k_{\\min}$ sets, and from 84 on E4" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: binomial configuration's new-stack floors {nw}")
shA, shF = dA("fleets", "E1", "shared"), dF("fleets", "E1", "shared")
shS = [dF("fleets", e, "shared") for e in ("E2", "E3", "E4")]
good = (shA == 254 and round(shF * 100) == 8 and round(min(shS)) == 4 and round(max(shS)) == 19
        and "it names the botnet only past 254 attackers on the busiest endpoint, $8\\%$ of its window, and past 4 to 19 times the day's median window on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: shared-stack floors E1 {shA} ({shF*100:.1f}%), small endpoints {[round(x, 1) for x in shS]} windows")
l1 = lvl("od", "E1")
good = (round(math.log10(l1)) == -4 and "the busiest endpoint's level rises to about $10^{-4}$ and the others' to the $0.01$ cap" in TEXN
        and all(FL["od"]["E1"][f]["new"]["min_stack_origins"] == 3 for f in tf)
        and all(FL["od"][e][f]["new"]["min_stack_origins"] == 2 for e in ("E2", "E3", "E4") for f in tf)
        and all(abs(lvl("od", e) - 0.01) < 1e-12 for e in ("E2", "E3", "E4")))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: beta-binomial level {l1:.2e} on E1 (three origins), the 0.01 cap elsewhere (two)")
bsA, bsF = exact("od", "E1"), exactW("od", "E1")
bsS = [exactW("od", e) for e in ("E2", "E3", "E4")]
good = (bsA == 86 and round(bsF * 100) == 3 and f"{min(bsS):.1f}" == "1.4" and f"{max(bsS):.1f}" == "4.2"
        and "Its floor on shared stacks falls to 86 attackers on the busiest endpoint ($3\\%$) and to 1.4 to 4.2 windows elsewhere" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: beta-binomial shared floors E1 {bsA} ({bsF*100:.1f}%), elsewhere {[round(x, 2) for x in bsS]}")
SW = PT["sweep"]
m = SW["fleets"]["E1"]["new:M25:A100"]
good = (round(m["blocked_alone"] * 100) == round(m["model_blocked_alone"] * 100) == 43
        and "below it the scope names the stacks chance makes larger, $43\\%$ of 100 attackers on new stacks on the busiest endpoint, as a binomial model of stack sizes predicts" in TEXN)
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
chk("V-B: gate and scope are not independent", "(5 windows against 3.5)", (jb["clean_fires"], jb["clean_joint_expected"]), "({} windows against {:.1f})")
jo = TD["od"]["all"]["union|origins"]
chk("App. E: the same for the beta-binomial and the z-score", "for the beta-binomial and the calibrated $z$-score, 22 and 20 windows against 7.5 and 11.9",
    (jo["clean_fires"], jz["clean_fires"], jo["clean_joint_expected"], jz["clean_joint_expected"]),
    "for the beta-binomial and the calibrated z-score, {} and {} windows against {:.1f} and {:.1f}")
good = all(TD[r]["all"][k]["clean_fires"] > TD[r]["all"][k]["clean_joint_expected"] for r, k in (("fleets", "union|origins"), ("od", "union|origins"), ("base", "zcal|origins"),
                                                                                                ("xfit_fleets", "union|origins"), ("xfit_od", "union|origins"), ("xfit", "zcal|origins")))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: joint misfires exceed independence in every configuration, in sample and cross-fitted")
good = all(v > 0.01 for v in alone.values()) and "Every calibrated component exceeds its $1\\%$ target" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: every calibrated component exceeds 1% out of sample ({ {k: round(v*100, 2) for k, v in alone.items()} })")
ci = fz["clean_ci95"]
good = (fz["clean_fires"] == 5 and fmt(fz["clean_rate"]) == "0.1"
        and f"fires on $0.1\\%$ of clean windows (5 of 5\\,643, 95\\% interval ${ci[0]*100:.2f}$--${ci[1]*100:.2f}\\%$, or ${fz['clean_ci95_cluster'][0]*100:.2f}$--${fz['clean_ci95_cluster'][1]*100:.2f}\\%$ from a bootstrap over endpoint-days)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the binomial configuration, {fz['clean_fires']} false alarms on the test days")
e2day = lambda r, k: TD[r]["per_endpoint"]["E2"][k]["clean_fires_by_fold"]["2026-09-23"]
good = (fmt(zc["clean_rate"]) == fmt(ob["clean_rate"]) == "0.4" and (zc["clean_fires"], ob["clean_fires"]) == (20, 22)
        and e2day("base", "zcal|origins") == e2day("od", "union|origins") == 13
        and "The calibrated $z$-score fires on $0.4\\%$ with lighter filters, its misfires clustered on one day of the console" in TEXN
        and zc["clean_collateral_mean"] < fz["clean_collateral_mean"]
        and f"Their misfires cluster, 13 of each on one day of the console, which lifts their bootstrap upper bounds from ${ob['clean_ci95'][1]*100:.2f}\\%$ and ${zc['clean_ci95'][1]*100:.2f}\\%$ to ${ob['clean_ci95_cluster'][1]*100:.2f}\\%$ and ${zc['clean_ci95_cluster'][1]*100:.2f}\\%$" in TEXN
        and "In sample it fires on $0.4\\%$ of clean windows" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: z-score and beta-binomial fire on {zc['clean_fires']} and {ob['clean_fires']} clean windows")
chk("V-B: mean collateral per alarm", "Its misfires block a mean $30.6\\%$ of the window's clients", fz["clean_collateral_mean"]*100,
    "Its misfires block a mean {:.1f} of the window's clients")
chk("V-C: the beta-binomial's mean collateral", "with filters that block a mean $7.7\\%$ of the window's clients", ob["clean_collateral_mean"]*100,
    "with filters that block a mean {:.1f} of the window's clients")
chk("V-B: expected collateral per clean window", "about $0.03\\%$ of legitimate clients per clean window", fz["clean_rate"] * fz["clean_collateral_mean"] * 100,
    "about {:.2f} of legitimate clients per clean window")
per_day = {k: s["clean_fires"] / 20 for k, s in (("bin", fz), ("z", zc), ("beta", ob))}
good = (per_day["bin"] == 0.25 and all(0.95 <= per_day[k] <= 1.15 for k in ("z", "beta")) and fz["clean_windows"] == 5643
        and "0.25 times per endpoint and day" in TEXN and round(288 * 0.01, 1) == 2.9
        and "about 2.9 of a day's 288" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B, VI: false alarms per endpoint and day {per_day}, budget 2.9")
chk("V-B: flash crowds of 1,000", "triggers the configuration in $22.2\\%$ of windows", fz["flash1000"]*100, "triggers the configuration in {:.1f} of windows")
chk("App. E: the z-score and flash crowds", "triggers the calibrated $z$-score in $13.1\\%$ of windows", zc["flash1000"]*100, "triggers the calibrated z-score in {:.1f} of windows")
good = (round(1000 / no_[1]) == 16 and round(1000 / no_[3]) == 50
        and "A crowd of 1\\,000 users, 16 to 50 typical windows of a small endpoint" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: 1,000 users are {1000/no_[1]:.1f} to {1000/no_[3]:.1f} typical windows of the small endpoints")
S3 = [("fleets", "union|origins"), ("od", "union|origins"), ("base", "zcal|origins")]
sw1 = SW["fleets"]["E1"]
g_small = [sw1[f"new:M25:A{A}"]["gate"] for A in (25, 50, 100, 250)] + [sw1["new:M25:x0.1"]["gate"]]
good = (round(min(g_small) * 100) == 6 and round(max(g_small) * 100) == 13 and round(sw1["new:M25:A1000"]["gate"] * 100) == 45
        and round(sw1["new:M25:x1"]["gate"] * 100) == 79 and 0.3 < 1000 / no_[0] < 0.35
        and "the gate opens in $6$--$13\\%$ of the windows of botnets of 25 attackers to a tenth of the window" in TEXN
        and "in $45\\%$ at a third and in $79\\%$ at a whole window" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: E1 gate in attack windows {min(g_small)*100:.1f}--{max(g_small)*100:.1f}% up to a tenth, {sw1['new:M25:A1000']['gate']*100:.1f}% at 1,000, {sw1['new:M25:x1']['gate']*100:.1f}% at 1x")
chk("V-B: E1, the binomial configuration stops", "therefore stops $3.4\\%$ of 100 attackers and $11.8\\%$ of a tenth of the window, against $70.8\\%$ of a whole one",
    (sw1["new:M25:A100"]["blocked"]*100, sw1["new:M25:x0.1"]["blocked"]*100, sw1["new:M25:x1"]["blocked"]*100),
    "therefore stops {:.1f} of 100 attackers and {:.1f} of a tenth of the window, against {:.1f} of a whole one")
S1 = PT["stealth_E1"]["fleets"]["fresh:x0.1"]; S2 = PT["stealth_E1"]["fleets"]["tail:x0.1"]
gt = [S1[f]["gate"] for f in tf]; rw = [S1[f]["recall_where_named"] for f in tf]
nm = [S[f]["named"] for S in (S1, S2) for f in tf + ["2026-09-25"]]
good = min(nm) == 1.0 and all(0.85 <= x <= 0.95 for x in rw) and f"the gate opens in ${min(gt)*100:.1f}$--${max(gt)*100:.0f}\\%$ of the windows of a botnet a tenth of the window depending on the day" in TEX \
    and S1["2026-09-25"]["gate"] == 0 and "the trigger never fired" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-B: E1 at 0.1x named in every window (new and shared stacks), gate {min(gt)*100:.1f}--{max(gt)*100:.1f}%, none on the held-out day")
e1f, e1o = TD["fleets"]["per_endpoint"]["E1"], TD["od"]["per_endpoint"]["E1"]
good = abs(e1f["union|origins"]["new:x0.1"]["blocked"] - sw1["new:M25:x0.1"]["blocked"]) < 1e-12
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} the sweep reproduces the E1 0.1x cell of Table VI")
sm = lambda r, k: [TD[r]["per_endpoint"][e][k]["new:x1"] for e in ("E2", "E3", "E4")]
b3 = [c["blocked"] for c in sm(*S3[0])]
o3 = [c for c in sm(*S3[1]) + sm(*S3[2])]
gx1 = [SW["fleets"][e]["new:M25:x1"]["gate"] for e in ("E2", "E3", "E4")]
good = (all(dA("fleets", e, "new") > no_[i + 1] for i, e in enumerate(("E2", "E3", "E4")))
        and f"and on the small endpoints in ${min(gx1)*100:.0f}$--${max(gx1)*100:.0f}\\%$ at a whole window" in TEXN
        and "and $2$--$5\\%$ of a botnet the size of the window" in TEXN
        and f"{min(b3)*100:.0f}" == "2" and f"{max(b3)*100:.0f}" == "5")
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: small endpoints at 1x: gate {min(gx1)*100:.1f}--{max(gx1)*100:.1f}%, below the floors, {min(b3)*100:.1f}--{max(b3)*100:.1f}% stopped")
s100 = [SW["fleets"][e]["new:M25:A100"] for e in ("E2", "E3", "E4")]; h100 = [SW["fleets"][e]["shared:M25:A100"] for e in ("E2", "E3", "E4")]
good = (min(x["gate"] for x in s100) > 0.5 and f"{100 / no_[1]:.1f}" == "1.6" and f"{100 / no_[3]:.0f}" == "5"
        and f"the configuration stops ${min(x['blocked'] for x in s100)*100:.0f}$--${max(x['blocked'] for x in s100)*100:.0f}\\%$ of it on new stacks" in TEXN
        and "On the small endpoints a botnet of 100 attackers, 1.6 to 5 windows there, opens the gate, and the floor decides" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: small endpoints at 100 attackers: gate {min(x['gate'] for x in s100)*100:.0f}%+, new {[round(x['blocked']*100, 1) for x in s100]}, shared {[round(x['blocked']*100, 1) for x in h100]}")
chk("V-B: the binomial configuration, pooled", "stops $38.4\\%$ and $77.7\\%$ of 100 and 1\\,000 attackers on new stacks and $21.7\\%$ and $63.3\\%$ on shared ones",
    tuple(fz[x]["blocked"]*100 for x in ("new:A100", "new:A1000", "shared:A100", "shared:A1000")),
    "stops {:.1f} and {:.1f} of 100 and 1\\,000 attackers on new stacks and {:.1f} and {:.1f} on shared ones")
un = TD["base"]["all"]["unseen|origins"]
good = un["shared:A100"]["blocked"] == un["shared:A1000"]["blocked"] == 0
ok += good; bad += not good
chk("App. E: the unseen filter alone, the z-score and the beta-binomial at 100", "Of 100 attackers on new stacks, the unseen filter alone stops $29.4\\%$, the calibrated $z$-score $54.7\\%$ ($23.7\\%$ on shared ones) and the beta-binomial $59.8\\%$ ($40.5\\%$)",
    (un["new:A100"]["blocked"]*100, zc["new:A100"]["blocked"]*100, zc["shared:A100"]["blocked"]*100, ob["new:A100"]["blocked"]*100, ob["shared:A100"]["blocked"]*100),
    "Of 100 attackers on new stacks, the unseen filter alone stops {:.1f}, the calibrated z-score {:.1f} ({:.1f} on shared ones) and the beta-binomial {:.1f} ({:.1f})")
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
chk("V-B: adversarial botnet, binomial configuration", "stops $7.0\\%$ and $23.8\\%$ of 100 and 1\\,000 attackers, and none on the two largest endpoints",
    (adv[0]*100, adv[1]*100), "stops {:.1f} and {:.1f} of 100 and 1\\,000 attackers, and none on the two largest endpoints")
ab2 = [FB["per_endpoint"][e][f]["fingerprints_above_limit"] for e in ("E1", "E2") for f in tf]
good = (max(e12) == 0 and [e for e in ("E1", "E2", "E3", "E4")] == sorted(PT["endpoints"]) and min(ab2) >= 23
        and "and none on the two largest endpoints, where nearly all of those fingerprints lie past the ratio limit" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: the adversarial botnet is blocked 0% on E1 and E2 ({e12})")
CH = json.load(open(R + "ja4_churn.json"))
newd = [r["new_fingerprints"] for e in CH["per_endpoint"] for f, r in CH["per_endpoint"][e].items() if f in tf]
e1n = [CH["per_endpoint"]["E1"][f]["new_fingerprints"] for f in tf]
good = (min(newd) > 0 and max(e1n) == 345 and "Fingerprints the profile has never seen appear every day but rarely concentrate" in TEXN
        and f"{CH['test_days']['windows_with_candidate_share']*100:.2f}" == "0.21" and "$0.21\\%$ of the test days' windows" in TEXN
        and CH["test_days"]["windows"] == 5643)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-B: JA4 churn, new fingerprints every day (E1 up to {max(e1n)}), candidates in {CH['test_days']['windows_with_candidate_share']*100:.2f}% of windows")
chk("App. E: scope alone, E1 0.1x, binomial", "it stops $89.6\\%$ of the attackers on new stacks and $61.1\\%$ on shared ones at $1.0\\%$",
    (e1f["union|none"]["new:x0.1"]["blocked"]*100, e1f["union|none"]["shared:x0.1"]["blocked"]*100, e1f["union|none"]["clean_rate"]*100),
    "it stops {:.1f} of the attackers on new stacks and {:.1f} on shared ones at {:.1f}")
chk("App. E: scope alone, E1 0.1x, beta-binomial", "and $90.0\\%$ and $78.3\\%$ at $2.1\\%$ with the beta-binomial",
    (e1o["union|none"]["new:x0.1"]["blocked"]*100, e1o["union|none"]["shared:x0.1"]["blocked"]*100, e1o["union|none"]["clean_rate"]*100),
    "and {:.1f} and {:.1f} at {:.1f} with the beta-binomial")
chk("App. E: scope alone with fleets, all endpoints", "on $2.2\\%$ of pooled", TD["fleets"]["all"]["union|none"]["clean_rate"]*100, "on {:.1f} of pooled")
chk("App. E: same, held-out day", "and $0.5\\%$ on the held-out day", FD["fleets"]["all"]["union|none"]["clean_rate"]*100, "and {:.1f} on the held-out day")
chk("App. E: scope alone without fleets", "against $3.5\\%$ and", TD["base"]["all"]["union|none"]["clean_rate"]*100, "against {:.1f} and")
chk("App. E: same, held-out day, without fleets", "and $8.8\\%$ without", FD["base"]["all"]["union|none"]["clean_rate"]*100, "and {:.1f} without")
zh = TD["base"]["all"]["zhist|origins"]
good = 0.45 <= zh["flash100"] <= 0.55 and "own history on half of the smaller ones" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: historical z-score fires on half the flash crowds of 100 ({zh['flash100']*100:.1f})")
chk("App. E: uncalibrated z-score, clean", "fires on $2.6\\%$ of clean", TD["base"]["all"]["zscore|omega"]["clean_rate"]*100, "fires on {:.1f} of clean")
chk("App. E: uncalibrated z-score, flash", "and $64.5\\%$ of flash crowds", TD["base"]["all"]["zscore|omega"]["flash100"]*100, "and {:.1f} of flash crowds")

print("== the held-out day (production_tables.json, compile_production_check_fresh.json)")
from scipy.stats import binom as _binom
pv = _binom.sf(ff_["clean_fires"] - 1, ff_["clean_windows"], fz["clean_fires"] / fz["clean_windows"])
good = ff_["clean_fires"] == 2 and "gives the binomial configuration 2 false alarms in 1\\,152 clean windows" in TEXN \
    and f"($P = {pv:.2f}$, as up to 3 would have been)" in TEX and pv >= 0.05
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: {ff_['clean_fires']} of {ff_['clean_windows']}, P = {pv:.3f} (protocol: consistent)")
r_ = fz["clean_fires"] / fz["clean_windows"]
p3, p4 = _binom.sf(2, ff_["clean_windows"], r_), _binom.sf(3, ff_["clean_windows"], r_)
good = p3 >= 0.05 > p4 and "as up to 3 would have been" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: up to 3 false alarms would pass (P = {p3:.3f}), 4 would not (P = {p4:.3f})")
pw = _binom.sf(3, ff_["clean_windows"], 3 * r_)
chk("held-out day: power against a tripled rate", "a tripled rate would be flagged $37\\%$ of the time", pw*100,
    "a tripled rate would be flagged {:.0f} of the time")
gw = ff_["clean_gate_windows"]; pc2 = _binom.sf(1, gw, fz["clean_fires"] / fz["clean_gate_windows"])
good = (gw == 3 and fz["clean_gate_windows"] == 168 and ff_["clean_fires"] == 2 and f"{pc2:.3f}" == "0.003"
        and f"{TD['fleets']['all']['gates_clean']['origins']*100:.1f}" == "3.0"
        and "and the gate opened in only 3 clean windows, two of which the scope misfired on, both on the web console ($P = 0.003$ at the test days' rate given the gate)" in TEXN)
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
chk("held-out day: blocked", "stops $38.9\\%$ and $73.4\\%$ of 100 and 1\\,000 attackers on new stacks and $21.5\\%$ and $60.9\\%$ on shared ones",
    tuple(ff_[x]["blocked"]*100 for x in ("new:A100", "new:A1000", "shared:A100", "shared:A1000")),
    "stops {:.1f} and {:.1f} of 100 and 1\\,000 attackers on new stacks and {:.1f} and {:.1f} on shared ones")

ov, ot, orl = FD["overlap_frozen_zcal"], TD["overlap_frozen_zcal"], FD["overlap_frozen_rule"]
good = orl["frozen"] == orl["rule"] == orl["both"] == 2 and ov["frozen"] == ov["zcal"] == ov["both"] == 2 \
    and "The base rule, the protocol's reference, fired on the same two windows, as did the calibrated $z$-score, outside the protocol" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held-out day: the z-score {ov} and the base rule {orl} fired on the same two windows")
good = ot["frozen"] == 5 and ot["both"] == 4
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} test days: the calibrated z-score shared {ot['both']} of the configuration's {ot['frozen']} false alarms")
good = fo["clean_fires"] == 0 and "and on the held-out day it raised no false alarm" in TEXN
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
        and f"and the JA4 class sizes in the {cp['windows_without_waf_blocks']} windows a day of the endpoint where the WAF blocked no client" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} compiled query in the operator's store: origins and /24 pairs equal the export "
      f"in {cp['origins_equal']}/{cp['windows']} windows")
sv = json.load(open(R + "stix_validation.json"))
good = (sv["ok"] and sv["errors"] == 0 and sv["warnings"] == 0 and sv["strict_errors"] == 0
        and all(c["valid_strict"] for c in sv["chains"]) and "pass the OASIS validator in strict mode" in TEXN
        and sv["bundles"] == 4 and "passes the exported bundles through the OASIS STIX~2.1 validator, TAXII~2.1 and MISP's importer" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} {sv['bundles']} STIX bundles valid, strict included "
      f"({sv['errors']} errors, {sv['warnings']} warnings, {sv['strict_errors']} strict errors)")
si = json.load(open(R + "stix_ingest.json")); tx, mi = si["taxii"], si["misp"]
good = (tx["accepted_all"] and all(tx["identical_by_type"][t] for t in ("indicator", "course-of-action",
                                                                     "relationship", "identity"))
        and not tx["identical_by_type"]["extension-definition"]
        and "cross the reference TAXII~2.1 server unchanged, save the extension definition" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} TAXII 2.1: accepted, identical by type {tx['identical_by_type']}")
good = (mi["fingerprints_kept"] == 0 and mi["fingerprints_in_scope"] > 0 and mi["endpoint_kept_where_scoped"]
        and mi["course_of_action_kept"] and "MISP's importer drops the fingerprints" in TEXN
        and "an extension the importer does not map to MISP's own JA4 object (\\texttt{ja4-plus})" in TEX)
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
fe = fp["fleets_per_endpoint"]["E1"]
good = sorted(set(fe["fleets"])) == [5, 6] and "five or six known fleets" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} E1 known fleets per fold: {fe['fleets']}")
lv = round(math.log10(float(np.median(fe["level"]))))
good = f"to about $10^{{{lv}}}$" in TEXN and round(math.log10(E["E1"]["scope_level_median"])) == -60
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} E1 level rises from 10^-60 to 10^{lv}")
hb, hf = fp["held_out_per_endpoint"]["E1"]["base"], fp["held_out_per_endpoint"]["E1"]["fleets"]
chk("held out: E1 0.1x new stacks, base", "from $0.7\\%$ to $6.3\\%$", hb["fresh:x0.1"]*100, "from {:.1f} to 6.3")
chk("held out: E1 0.1x new stacks, fleets", "from $0.7\\%$ to $6.3\\%$", hf["fresh:x0.1"]*100, "from 0.7 to {:.1f}")
ho = fp["held_out"]
good = f"at {ho['fleets']['false_alarms']} false alarms against {ho['base']['false_alarms']}" in TEXN \
    and ho["fleets"]["false_alarms"] <= ho["base"]["false_alarms"]
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held out: {ho['fleets']['false_alarms']} false alarms against {ho['base']['false_alarms']}")
sec = {k: v for k, v in fp["held_out_secondary_all_shares"].items() if k != fp["chosen_share"]}
c0 = fp["held_out_secondary_all_shares"][fp["chosen_share"]]
good = all(v["false_alarms"] >= 1.8 * c0["false_alarms"] and v["collateral_median"] < c0["collateral_median"]
           and v["flash100"] > c0["flash100"] and v["mean_blocked"] > c0["mean_blocked"] for v in sec.values()) \
    and "fire twice as often, on lighter filters" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} held out, smaller shares: more blocked, ~2x false alarms, lighter, more flash crowds")
chk("held out, smaller shares' collateral, low end", "a median $11$--$12\\%$ of clients", min(v["collateral_median"] for v in sec.values())*100, "a median {:.0f}--12 of clients")
chk("held out, smaller shares' collateral, high end", "a median $11$--$12\\%$ of clients", max(v["collateral_median"] for v in sec.values())*100, "a median 11--{:.0f} of clients")
chk("held out, chosen share's collateral", "of clients against $51\\%$", c0["collateral_median"]*100, "of clients against {:.0f}")
good = (fp["eligible"] == [fp["chosen_share"]] and len(fp["design"]) == 5
        and f"only one whose false alarms did not exceed the base rule's ({d0[fp['chosen_share']]['false_alarms']} against {d0['base']['false_alarms']}, the others {min(v['false_alarms'] for s, v in d0.items() if s not in ('base', fp['chosen_share']))} to {max(v['false_alarms'] for s, v in d0.items() if s not in ('base', fp['chosen_share']))})" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} only one of four shares kept false alarms at or below the base rule's")
hp = fp["held_out_per_endpoint"]
good = all(hp[e]["base"] == hp[e]["fleets"] for e in ("E2", "E3", "E4")) and "leaves E2 to E4 unchanged" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} held out: E2 to E4 unchanged by the known fleets")
print("== generator: window sweep and the vocabulary-tail variant")
ws = json.load(open(R + "window_sweep.json"))["aggregate"]["K=1000"]
mx = sorted(round(v["max_cluster_size"]) for v in ws.values()); mn = sorted(round(v["mean_cluster_size"]) for v in ws.values())
good = f"holds $1\\,{mx[0] - 1000:03d}$--$1\\,{mx[-1] - 1000:03d}$ sessions at every $W$" in TEX and f"grows from {mn[0]} to {mn[-1]}" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. D: campaign cluster {mx[0]}--{mx[-1]} sessions at every W, mean {mn[0]}--{mn[-1]}")
for meth, val in (("unseen", "84.4"), ("enrichment", "89.8")):
    v = us("shared_vocab_tail", 25, 0, meth, "recall") * 100
    chk(f"tab:symbolic note: vocabulary-tail stacks, {meth}", val, v, pct)
print("== cross-fitted calibration (production_tables.json: xfit, xfit_fleets, xfit_od)")
xb, xo, xz = TD["xfit_fleets"]["all"]["union|origins"], TD["xfit_od"]["all"]["union|origins"], TD["xfit"]["all"]["zcal|origins"]
xa = {"bin": TD["xfit_fleets"]["all"]["union|none"]["clean_rate"], "z": TD["xfit"]["all"]["zcal|none"]["clean_rate"],
      "z_E2": TD["xfit"]["per_endpoint"]["E2"]["zcal|none"]["clean_rate"], "beta": TD["xfit_od"]["all"]["union|none"]["clean_rate"],
      "beta_E2": TD["xfit_od"]["per_endpoint"]["E2"]["union|none"]["clean_rate"], "beta_fresh": FD["xfit_od"]["all"]["union|none"]["clean_rate"]}
good = (xb["clean_fires"] == 6 and fz["clean_fires"] == 5 and f"{xa['bin']*100:.1f}" == "1.9"
        and "The binomial configuration barely moves, with 6 false alarms against 5" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: binomial scope alone {xa['bin']*100:.2f}%, {xb['clean_fires']} false alarms against {fz['clean_fires']}")
good = abs(xb["new:A100"]["blocked"] - fz["new:A100"]["blocked"]) < 0.03
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: the binomial stops {xb['new:A100']['blocked']*100:.1f}% against {fz['new:A100']['blocked']*100:.1f}% of 100 attackers")
zr = [FL["xfit"][e][f]["zcal_threshold"] / FL["base"][e][f]["zcal_threshold"] for e in ("E1", "E2", "E3", "E4") for f in tf]
good = f"threshold rises by a median factor of {st_.median(zr):.1f}" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: z threshold ratio median {st_.median(zr):.2f} (range {min(zr):.2f}--{max(zr):.2f})")
good = f"{xa['z']*100:.1f}" == "2.5" and "its lead in detection came from the in-sample threshold" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: the z-score alone fires in {xa['z']*100:.2f}% (Table IV), its lead was in-sample")
chk("App. E: cross-fitted z-score at 100 attackers", "stops $33.6\\%$ of 100 attackers against $54.7\\%$", (xz["new:A100"]["blocked"]*100, zc["new:A100"]["blocked"]*100),
    "stops {:.1f} of 100 attackers against {:.1f}")
chk("cross-fit: beta-binomial alone", "its scope alone fires in $1.1\\%$ of clean windows", xa["beta"]*100, "its scope alone fires in {:.1f} of clean windows")
chk("App. E: cross-fitted beta-binomial on the held-out day", "its scope alone fires in $1.2\\%$ of the held-out day's windows", xa["beta_fresh"]*100,
    "its scope alone fires in {:.1f} of the held-out day's windows")
good = min(xa["beta"], xa["bin"], xa["z"]) == xa["beta"] and "Only the beta-binomial nearly meets its target out of sample" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: only the beta-binomial comes near its 1% target")
xl = [FL["xfit_od"][e][f]["log10_level"] for e in ("E1", "E2", "E3", "E4") for f in tf]
good = (max(xl) < -2 + 1e-9 and round(min(xl)) == -17 and round(max(xl)) == -2 and xo["clean_fires"] == 6
        and "The beta-binomial's levels then fall to between $10^{-17}$ and $10^{-2}$" in TEXN and "It too raises 6 false alarms" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: beta-binomial levels 10^{min(xl):.1f}..10^{max(xl):.1f}, {xo['clean_fires']} false alarms")
chk("cross-fit: beta-binomial's filters", "with filters that block a median $2.0\\%$ of the window's clients", xo["clean_collateral_median"]*100,
    "with filters that block a median {:.1f} of the window's clients")
xk = [FL["xfit_od_fleets"]["E1"][f]["known_fleets"] for f in tf]
good = xk.count(1) == 3 and xk.count(0) == 2 and "and one known fleet appears on the busiest endpoint on three of the five days" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: E1 known fleets under the beta-binomial {xk}")

xs1, xsS = exactW("xfit_od", "E1"), [exactW("xfit_od", e) for e in ("E2", "E3", "E4")]
good = round(xs1 * 100) == 6 and f"{max(xsS):.1f}" == "4.4" and "its floor on shared stacks falls to $6\\%$ of the busiest window and at most 4.4 windows elsewhere" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-fit: beta-binomial shared floors {xs1*100:.1f}% and {[round(x, 2) for x in xsS]}")
shB = [dA("xfit_fleets", e, "shared") for e in ("E1", "E2", "E3", "E4")]; shO = [exact("xfit_od", e) for e in ("E1", "E2", "E3", "E4")]
good = (xo["clean_fires"] == xb["clean_fires"] and xo["clean_collateral_median"] < xb["clean_collateral_median"] and xo["flash1000"] < xb["flash1000"]
        and all(o < b for o, b in zip(shO, shB)) and xz["new:A100"]["blocked"] < xb["new:A100"]["blocked"] + 0.05
        and "It too raises 6 false alarms, with filters that block a median $2.0\\%$ of the window's clients" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: cross-fitted, the beta-binomial matches the binomial's false alarms with lower shared floors {shO} vs {shB}")
good = ("A first design, which calibrated on the last calibration day alone, was dropped" in TEXN
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
chk("WAF: the implied precision floor", "only if $80$--$88\\%$ of its clients were blocked", (min(fl_["E3"], fl_["E4"])*100, max(fl_["E3"], fl_["E4"])*100),
    "only if {:.0f}--{:.0f} of its clients were blocked")
na = [WA[e]["scores"][c]["named"] for e in ("E3", "E4") for c in CF]
pa = [WA[e]["scores"][c]["precision"] for e in ("E3", "E4") for c in CF]
br = [WA[e]["base_rate"] for e in ("E3", "E4")]
good = (f"{min(na)*100:.0f}" == "2" and f"{max(na)*100:.0f}" == "3" and f"{min(pa)*100:.1f}" == "0.4" and f"{max(pa)*100:.0f}" == "33"
        and max(WA[e]["scores"][c]["lift"] for e in ("E3", "E4") for c in CF) < 1
        and f"{min(br)*100:.0f}" == "41" and f"{max(br)*100:.0f}" == "63"
        and "With a profile of all clients, $0.4$--$33\\%$ of the clients the scopes would block were blocked, less than a random pick ($41$--$63\\%$)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF, all-client profile: named {min(na)*100:.1f}--{max(na)*100:.1f}%, precision {min(pa)*100:.1f}--{max(pa)*100:.1f}% vs random {min(br)*100:.1f}--{max(br)*100:.1f}%")
dets = [WA[e]["surges"]["detected"][c] for e in ("E3", "E4") for c in CF]
chance = [WA[e]["surges"]["expected_by_chance"][c] for e in ("E3", "E4") for c in CF]
eps_ = WA["E3"]["surges"]["episodes"] + WA["E4"]["surges"]["episodes"]
good = (min(dets) == 0 and max(dets) == 2 and eps_ == 38 and f"{max(chance):.1f}" == "0.5"
        and "The scopes catch the WAF's surges at chance, above it only on the console and there with under $1\\%$ of the blocked clients" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF surges on E3+E4: {eps_} episodes, detected {min(dets)}--{max(dets)}, chance at most {max(chance):.2f}")
S2 = WA["E2"]["surges"]
e2d = [S2["detected"][c] for c in ("beta-binomial", "z-score")]
e2c = [S2["expected_by_chance"][c] for c in ("beta-binomial", "z-score")]
e2r = [S2["scores"][c]["recall"] for c in ("beta-binomial", "z-score")]
good = (e2d == [5, 5] and S2["detected"]["binomial"] == 0 and S2["episodes"] == 33 and max(e2c) < 1 and max(e2r) < 0.01
        and "above it only on the console and there with under $1\\%$ of the blocked clients" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF surges on E2: detected {e2d} of {S2['episodes']}, chance {[round(x, 2) for x in e2c]}, recall {[round(x*100, 2) for x in e2r]}%")
mr = [WC[e]["scores"]["modal"]["recall"] for e in ("E2", "E3", "E4")]; nc = [WC[e]["ceiling"]["no_clean"] for e in ("E2", "E3", "E4")]
good = (round(min(mr) * 100) == 13 and round(max(mr) * 100) == 55 and max(nc) < 0.5
        and "most of them on fingerprints that unblocked clients also present" in TEXN
        and "The verdicts cannot validate the scope, and the scope, which reads deviations from everyday traffic, does not recover what this WAF blocks" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} WAF: blocked clients on common fingerprints (modal {[round(x*100) for x in mr]}%, no unblocked peer {[round(x*100) for x in nc]}%), negative result both ways")
good = "WAF verdicts prove unusable as labels" in re.sub(r"\s+", " ", TEX[TEX.index("\\begin{abstract}"):TEX.index("\\end{abstract}")])
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the WAF's verdicts prove unusable as labels")
print("== methodology and calibration text")
dd = json.load(open(HERE.parent / "sprint-2" / "distributions" / "session_duration.json"))["count"]
rr = json.load(open(HERE.parent / "sprint-2" / "distributions" / "session_requests.json"))["count"]
ks = json.load(open(HERE.parent / "sprint-2" / "results" / "ks_validation.json"))["features"]
good = (dd == 40351 and rr == 322658 and f"{ks['n_requests']['ks_D']:.3f}" == "0.002" and f"{ks['duration_s']['ks_D']:.3f}" == "0.003"
        and "all $322\\,658$ for the first and the $40\\,351$ with two or more requests for the second" in TEXN
        and "distances of $D = 0.002$ and $0.003$ between generated and real sessions only check the sampler" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} IV: request counts from {rr}, durations from {dd} sessions, KS D {ks['n_requests']['ks_D']} and {ks['duration_s']['ks_D']}")
good = f"{0.9 / 0.384:.1f}" == "2.3" and "with the measured $p_1 = 38.4\\%$" in TEXN and "only while $M < 2.3$" in TEXN and "the most common accounting for $38.4\\%$ of requests" in TEXN
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
abs_chk("modal blocks none, hits legitimate traffic", "blocks no attacker and $39\\%$ of legitimate traffic once the botnet spans five TLS stacks",
        us("original", 5, 0, "modal", "fpr")*100, "blocks no attacker and {:.0f} of legitimate traffic once the botnet spans five TLS stacks")
good = us("original", 5, 0, "modal", "recall") == 0; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: the modal scope blocks no attacker at five stacks")
pr = [us("original", s, 0, m, "recall") for s in (5, 25) for m in ("enrichment", "zscore")]
pf = [us("original", s, 0, m, "fpr") for s in (5, 25) for m in ("enrichment", "zscore")]
good = all(round(x * 100) == 90 for x in pr) and max(pf) == 0 and "profile-relative scopes block $90\\%$ up to 25 stacks with no observed collateral" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: binomial test and z-score block 90% up to 25 stacks at zero FPR")
abs_chk("the deployed configuration's false alarms", "raises false alarms on $0.1\\%$ of clean windows, although its scope alone fires on $2.2\\%$ against a $1\\%$ target",
        (fz["clean_rate"]*100, alone["bin"]*100), "raises false alarms on {:.1f} of clean windows, although its scope alone fires on {:.1f} against a 1 target")
abs_chk("the floor on shared stacks", "is named only past $8\\%$ of the busiest endpoint's window and 4 to 19 windows elsewhere",
        (shF*100, min(shS), max(shS)), "is named only past {:.0f} of the busiest endpoint's window and {:.0f} to {:.0f} windows elsewhere")
good = min(share) > 0.5 and "and never on those carrying most origins" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: never named on the fingerprints carrying most origins ({min(share)*100:.0f}%+)")
good = (round(sw1["new:M25:x0.1"]["blocked"] * 100) == 12 and sw1["new:M25:x0.1"]["gate"] < 0.2
        and "the distinct-origin trigger seldom fires: only $12\\%$ of one a tenth of the busiest window is stopped" in ab)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the trigger seldom fires on a small botnet ({sw1['new:M25:x0.1']['gate']*100:.1f}%), {sw1['new:M25:x0.1']['blocked']*100:.1f}% stopped")
abs_chk("the cross-fitted beta-binomial's floor", "lowers the floor to $6\\%$ and at most 4.4 windows", (xs1*100, max(xsS)),
        "lowers the floor to {:.0f} and at most {:.1f} windows")
good = xa["beta"] < 0.012 and "built after a held-out day was read, nearly meets the target out of sample" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the cross-fitted beta-binomial nearly meets its target ({xa['beta']*100:.2f}%), post hoc")
good = pv >= 0.05 and "The held-out day does not contradict the false-alarm rate" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the held-out day is consistent")
good = (cp["origins_equal"] == cp["windows"] and cpf["origins_equal"] == cpf["windows"] and cp["net24_pairs_equal"] == cp["windows"]
        and "An OWL ontology specifies the counts, which its compiled query reproduces on real data" in ab)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the compiled query reproduces origins and /24 pairs")
e1f_ = [dA(r, "E1", "shared") for r in ("fleets", "od", "xfit_fleets", "xfit_od")]
e1r_ = [dF(r, "E1", "shared") for r in ("fleets", "od", "xfit_fleets", "xfit_od")]
good = (max(e1r_) < 0.1 and (min(e1f_), max(e1f_)) == (86, 286)
        and "every calibrated configuration names a botnet of 86 to 286 attackers per window, under a tenth of its typical window" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: E1 shared floors {e1f_} attackers ({[round(x*100, 1) for x in e1r_]}%)")
nwW = [dF("fleets", e, "new") for e in ("E2", "E3", "E4")]
good = ("the binomial configuration names shared stacks only past 4 to 19 windows and new stacks from 2 to 4 windows" in TEXN
        and min(nw[1:]) == 84 and max(nw[1:]) == 139 and round(min(nwW)) == 2 and round(max(nwW)) == 4)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VI: the small endpoints' floors and the new-stack filter range")
good = (xb["clean_fires"] <= fz["clean_fires"] + 1 and ff_["clean_fires"] == 2 and pv >= 0.05 and alone["bin"] > 0.01
        and "It keeps its false-alarm rate out of sample and on a held-out day, though its scope alone exceeds its target and its trigger lets most of a small botnet through" in TEXN
        and "only past $8\\%$ of the busiest endpoint's window and 4 to 19 windows on the small ones" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: the binomial configuration holds its rate out of sample, its scope alone does not")
good = (xa["beta"] < 0.012 and all(o < b for o, b in zip(shO, shB))
        and "A beta-binomial background, built post hoc, nearly meets that target out of sample and lowers the floor" in TEXN
        and "A pre-specified test of the beta-binomial and of triggers driven by the scope on new days" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: the cross-fitted beta-binomial comes close to the target and lowers the floor")
good = ("so no attack label is involved" in TEXN and "it also excludes the clients the operator's WAF blocked, since the scope runs behind the WAF" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} III-C: no attack label; the profile excludes WAF-blocked clients, the scope runs behind the WAF")
print(f"\nTOTAL: {ok} OK, {bad} mismatches")
sys.exit(1 if bad else 0)
