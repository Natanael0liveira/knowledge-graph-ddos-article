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
chk("V-A: (c)", "only $0.499$ and $0.659$", (au(50, "rf", "c"), au(1000, "rf", "c")), "only {:.3f} and {:.3f}")
t = CT["K=1000"]; pb = {round(t[k]["p_bonferroni"] / 1e-9, 1) for k in ("d_vs_c", "d_vs_a")}
good = pb == {7.5} and all(t[k]["p_bonferroni"] < 0.05 for k in t) and "$p_{\\mathrm{Bonf}} = 7.5\\times 10^{-9}$" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-A: p_Bonf {pb} x 1e-9 for (d)-(c) and (d)-(a)")
chk("V-A: Cohen's d", "Cohen's $d = 13.5$ and $22.3$", (t["d_vs_c"]["cohens_d"], t["d_vs_a"]["cohens_d"]), "Cohen's d = {:.1f} and {:.1f}")
tr = [au(K, f, "d") for K in (50, 1000) for f in ("rf", "hgb")]
chk("V-A: tree ensembles on (d)", "that band ($0.92$--$0.99$)", (min(tr), max(tr)), "that band ({:.2f}--{:.2f})")
chk("V-A: the perceptron on (d)", "the perceptron reaches $0.86$ and $0.95$", (au(50, "mlp", "d"), au(1000, "mlp", "d")), "the perceptron reaches {:.2f} and {:.2f}")
chk("V-A: logistic regression on (d)", "is monotone, $0.87$ and $0.80$", (au(50, "logreg", "d"), au(1000, "logreg", "d")), "is monotone, {:.2f} and {:.2f}")
chk("VI: linear model over (d) against (a)", "attains $0.799$ against $0.495$", (au(1000, "logreg", "d"), au(1000, "logreg", "a")), "attains {:.3f} against {:.3f}")
chk("VII: (d) within one botnet structure", "ROC AUC $0.93$--$0.98$ only within one botnet structure", (au(50, "rf", "d"), au(1000, "rf", "d")),
    "ROC AUC {:.2f}--{:.2f} only within one botnet structure")
print("== Section V-A and Appendix C: cross-M (cross_m_generalization.json)")
XM = json.load(open(R + "cross_m_generalization.json")); XA = XM["aggregate"]
xm = lambda p, cf="d", k="cross_m": XA[p][cf][k]["mean"]
cv = XM["canonical_validation"]
good = max(cv["max_abs_diff_vs_canonical_runs_csv"].values()) < 1e-12 and abs(cv["recomputed_in_distribution"]["d"]["mean"] - au(1000, "rf", "d")) < 1e-12
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-M: the in-distribution protocol reproduces the canonical runs ({cv['max_abs_diff_vs_canonical_runs_csv']})")
good = XM["K"] == 1000 and XM["alpha"] == 1.5 and not set(XM["seed_halves"][0]) & set(XM["seed_halves"][1])
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} cross-M: K = {XM['K']}, alpha = {XM['alpha']}, disjoint seed halves")
chk("V-A: trained on 5, tested on 25 and 100", "(d) falls to $0.61$ and $0.63$", (xm("5->25"), xm("5->100")), "(d) falls to {:.2f} and {:.2f}")
chk("V-A: trained on 25, tested on 5", "to $0.48$ (Appendix", xm("25->5"), "to {:.2f} (Appendix")
chk("App. C: trained on 25, tested on 100", "reaches an AUC of $0.75$", xm("25->100"), "reaches an AUC of {:.2f}")
cs = [xm(p, "d", "cross_seed_same_m") for p in XA]
chk("App. C: same M, other seeds", "against $0.95$--$0.995$ trained on the same $M$ on other seeds", (min(cs), max(cs)),
    "against {:.2f}--{:.3f} trained on the same M on other seeds")
lk = [XA[p]["a"]["all_sessions"]["same_seed_reference_leaky"]["mean"] for p in XA]
chk("App. C: a same-seed split would score (a)", "(a) at $0.88$--$0.94$ from memorized copies", (min(lk), max(lk)), "(a) at {:.2f}--{:.2f} from memorized copies")
xs = [xm(p) for p in XA]
sym = json.load(open(R + "symbolic_detector.json"))["aggregate"]
print("== tab:symbolic (symbolic_detector.json)")
# the rows as printed in the table
rows = {"1.5:1:0": "Monolithic ($M{=}1$)", "1.5:5:0": "$M{=}5$ ", "1.5:25:0": "$M{=}25$ ",
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
       f"{us('shared_profile_tail', 25, 0, 'unseen', 'recall')*100:.1f}"]
good = nums == exp; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:symbolic row shared stacks {'':34s} printed={nums} data={exp}")
v = max(us("original", s, a_, "unseen", "fpr") for s, a_ in ((1, 0), (5, 0), (25, 0), (100, 0), (25, 1)))
good = round(v * 100, 2) <= 0.03 and "FPR at most $0.03\\%$" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:symbolic note: unseen FPR at most 0.03% ({v*100:.3f})")
print("== Section V-B text")
chk("unseen filter at M=100", "better at one hundred ($88.1\\%$)", us("original", 100, 0, "unseen", "recall")*100, "better at one hundred ({:.1f})")
chk("enrichment on shared stacks", "the rule $85.4\\%$ at", us("shared_profile_tail", 25, 0, "enrichment", "recall")*100, "the rule {:.1f} at")
chk("enrichment collateral on shared stacks", "at $2.23\\%$ collateral", us("shared_profile_tail", 25, 0, "enrichment", "fpr")*100, "at {:.2f} collateral")
chk("uncalibrated z-score on shared stacks", "$z$-score $89.9\\%$ at", us("shared_profile_tail", 25, 0, "zscore", "recall")*100, "z-score {:.1f} at")
chk("its collateral", "at $3.37\\%$.", us("shared_profile_tail", 25, 0, "zscore", "fpr")*100, "at {:.2f}.")
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
chk("rule per origin, calibrated (V-D)", "brings the rule to $0.2\\%$", m["clean"]["pipeline"]*100, "brings the rule to {:.1f}")
v = c["collateral_pipeline_median"]; good = 0.4 <= v <= 0.6 and "blocking about half of that window's clients" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} App. E: false alarms block 'about half' of clients: {v:.3f}")
cells = [x for sec in ("attack_fresh_M25", "attack_tail_M25", "attack_relative_M25") for x in a[sec].values()]
good = (c["origins_enrichment_pipeline"] <= 0.55 * c["pipeline"]
        and all(x["origins_enrichment_blocked"] >= x["blocked_pipeline"] for x in cells)
        and "halves the false alarms as the gate with no loss of detection" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: origin gate halves false alarms ({c['origins_enrichment_pipeline']*100:.2f} vs "
      f"{c['pipeline']*100:.2f}%), no loss in any of {len(cells)} attack cells")
n_org, n_om = round(c["origins_enrichment_pipeline"] * c["windows"]), round(c["pipeline"] * c["windows"])
good = f"({n_org} against {n_om} windows)" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: origin gate {n_org} against {n_om} clean false alarms")
vb = P["volume_baseline"]; lo, hi = vb["agreement_range"]
good = f"${lo*100:.0f}$--${hi*100:.1f}\\%$" in TEX; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: Omega vs origin threshold agree {lo*100:.1f}--{hi*100:.1f}%")
more = all(x["origins"] >= x["omega"] for x in list(vb["attack_fresh_M25"].values()) + list(vb["attack_relative_M25"].values()))
ok += more; bad += not more; print(f"{'OK ' if more else 'XX '} V-D: the origin threshold catches at least as many attacks")
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
chk("App. E: rho moves a collateral median by up to", "up to $7.2$", moves[1]*100, "up to {:.1f}")
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
TD, FD, FL = PT["test_days"], PT["fresh_day"], PT["floor"]
tf = ["2026-09-20", "2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24"]
fmt = lambda v: "--" if v is None else f"{v*100:.1f}"
# the scopes as the table names them: the evaluated configuration, the same over the
# beta-binomial background, the calibrated z-score, and the base rule of the protocol
SCOPE = {"binomial": ("fleets", "union|origins"), "beta-bin.": ("od", "union|origins"),
         "$z$-score": ("base", "zcal|origins"), "rule": ("base", "enrichment|omega")}
COLS = ["new:x0.1", "new:x1", "shared:x0.1", "shared:x1"]
def prod_rows():
    s = TEX[TEX.index("\\label{tab:production}"):]
    s = s[:s.index("\\end{tabular}")]
    group, rows = None, []
    for l in s.splitlines():
        if "Fresh day" in l:
            group = "fresh"; continue
        cells = [x.strip() for x in l.strip().rstrip("\\").split("&")]
        vals = cells[2:]
        if len(vals) != 7 or not all(re.fullmatch(r"\d+\.\d|--", x) for x in vals):
            continue
        group = cells[0] or group
        rows.append((group, cells[1].replace("$^{*}$", ""), vals))
    return rows
def prod_cell(group, name):
    run, key = SCOPE[name]
    if group == "fresh": return FD[run]["all"][key]
    if group == "All": return TD[run]["all"][key]
    return TD[run]["per_endpoint"][group][key]
rows = prod_rows()
for group, name, printed in rows:
    r = prod_cell(group, name)
    exp = [fmt(r["clean_rate"]), fmt(r["clean_collateral_median"]), fmt(r["flash100"])] + [fmt(r[x]["blocked"]) for x in COLS]
    good = printed == exp; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} tab:production {group:5s} {name:10s} printed={printed} data={exp}")
want = [(e, n) for e in ("E1", "E2", "E3", "E4", "All") for n in ("binomial", "beta-bin.", "$z$-score")] + \
       [("fresh", n) for n in ("rule", "binomial", "beta-bin.", "$z$-score")]
good = [(g, n) for g, n, _ in rows] == want; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:production holds the {len(want)} rows in order ({len(rows)} parsed)")
fz, ob, zc = TD["fleets"]["all"]["union|origins"], TD["od"]["all"]["union|origins"], TD["base"]["all"]["zcal|origins"]
ff_, fo, zf = FD["fleets"]["all"]["union|origins"], FD["od"]["all"]["union|origins"], FD["base"]["all"]["zcal|origins"]
good = fz["clean_windows"] == 5643 and ff_["clean_windows"] == 1152 and "(5\\,643 on the test days, 1\\,152 on the fresh day)" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} tab:production note: {fz['clean_windows']} clean windows on the test days, {ff_['clean_windows']} on the fresh day")
good = "$^{*}$Built after the fresh day was read" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:production note: the beta-binomial marked as built after the fresh day")
# the beta-binomial needs no allow-list: no fold names a known fleet, and the run with
# the fleet profile switched on gives the same numbers
kf = {r: [FL[r][e][f]["known_fleets"] for e in FL[r] for f in FL[r][e]] for r in FL}
same = all(TD["od"][k] == TD["od_fleets"][k] and FD["od"][k] == FD["od_fleets"][k] for k in ("all", "per_endpoint"))
good = max(kf["od_fleets"]) == 0 and same and "no fingerprint qualifies as a known fleet, so no allow-list is needed" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: beta-binomial names no known fleet in any fold ({max(kf['od_fleets'])}), identical with the fleet profile: {same}")

print("== tab:floor (production_tables.json)")
med = lambda run, e: st_.median(FL[run][e][f]["new"]["min_fraction_of_window"] for f in tf)
lvl = lambda run, e: st_.median(FL[run][e][f]["level"] for f in tf)
ef = lambda v: f"{v:.2f}" if v < 1 else f"{v:.1f}"
for e, lab in [("E1", "E1, RUM beacons"), ("E2", "E2, web console"), ("E3", "E3, API"), ("E4", "E4, SSO")]:
    line = [l for l in TEX.splitlines() if l.strip().startswith(lab) and "&" in l]
    cl = [x.strip() for x in line[0].strip().rstrip("\\").split("&")] if line else []
    printed = ([cl[1]] + [re.search(r"10\^\{(-?\d+)\}", x).group(1) for x in cl[2:4]] + cl[4:7] + [cl[7].replace("\\%", "")]) if len(cl) == 8 else cl
    no = st_.median(FL["base"][e][f]["median_origins"] for f in tf)
    w = TD["base"]["waf"][e]["enrichment"]["precision"]
    wc = "--" if not TD["base"]["waf"][e]["waf_clients"] else (f"{w*100:.0f}" if w >= 0.1 else f"{w*100:.1f}")
    exp = ["$>10^3$" if no > 1000 else "$<10^2$" if no < 100 else "?", str(round(math.log10(lvl("base", e)))),
           str(round(math.log10(lvl("od", e)))), ef(med("base", e)), ef(med("fleets", e)), ef(med("od", e)), wc]
    good = printed == exp; ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} tab:floor {lab:16s} printed={printed} data={exp}")
good = not TD["base"]["waf"]["E1"]["waf_clients"] and "E1 has no WAF activity" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} tab:floor note: E1 has no WAF activity")

print("== Section V-D prose (production_tables.json)")
f1 = FL["base"]["E1"]
so = sorted(f1[f]["new"]["min_stack_origins"] for f in tf)
good = f"past {so[0]} to {so[-1]} origins" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: E1 names a stack only past {so[0]} to {so[-1]} origins")
chk("V-D: E1 floor", "$16\\%$ of the typical window", med("base", "E1")*100, "{:.0f} of the typical window")
chk("V-D: E1 floor with known fleets", "falls to $7\\%$ once the", med("fleets", "E1")*100, "falls to {:.0f} once the")
kn = sorted(set(FL["fleets"]["E1"][f]["known_fleets"] for f in tf))
good = kn == [5, 6] and "five or six known fleets" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: E1 exempts {kn} known fleets per test day")
small = [med("base", e) for e in ("E2", "E3", "E4")]
good = round(min(small)) == 4 and round(max(small)) == 12 and "floor is 4 to 12 times the whole window" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: small endpoints' floor {min(small):.1f}--{max(small):.1f} times the window")
l1 = lvl("od", "E1")
good = (f"level rises to ${l1 / 1e-5:.0f}\\times 10^{{-5}}$, where three origins name a stack" in TEXN
        and all(FL["od"]["E1"][f]["new"]["min_stack_origins"] == 3 for f in tf)
        and all(abs(lvl("od", e) - 0.01) < 1e-12 for e in ("E2", "E3", "E4")) and "and the others' to the $0.01$ cap" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: beta-binomial level {l1:.2e} on E1 (three origins), the 0.01 cap elsewhere")
chk("V-D: beta-binomial floor, E1", "falls to $3\\%$ of the busiest window", med("od", "E1")*100, "falls to {:.0f} of the busiest window")
so_ = [med("od", e) for e in ("E2", "E3", "E4")]
chk("V-D: beta-binomial floor elsewhere", "to $0.9$--$2.8$ windows elsewhere", (min(so_), max(so_)), "to {:.1f}--{:.1f} windows elsewhere")
e2b, e2z = TD["od"]["per_endpoint"]["E2"]["union|origins"]["clean_rate"], TD["base"]["per_endpoint"]["E2"]["zcal|origins"]["clean_rate"]
good = e2b > 0.01 and e2z > 0.01; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: on the console both exceed the 1% budget ({e2b*100:.2f}, {e2z*100:.2f})")
chk("V-D: over budget on the console", "exceed the budget ($1.3\\%$), as do the calibrated $z$-score's ($1.1\\%$)",
    (e2b*100, e2z*100), "exceed the budget ({:.1f}), as do the calibrated z-score's ({:.1f})")
S3 = [("fleets", "union|origins"), ("od", "union|origins"), ("base", "zcal|origins")]
x1 = [TD[r]["per_endpoint"]["E1"][k][x]["blocked"] for r, k in S3 for x in ("new:x1", "shared:x1")]
x01 = [TD[r]["per_endpoint"]["E1"][k][x]["blocked"] for r, k in S3 for x in ("new:x0.1", "shared:x0.1")]
chk("V-D: E1, every calibrated scope at 1x", "stops $67$--$71\\%$ of a botnet the size of its typical window",
    (min(x1)*100, max(x1)*100), "stops {:.0f}--{:.0f} of a botnet the size of its typical window")
chk("V-D: E1, every calibrated scope at 0.1x", "and $8$--$12\\%$ of one a tenth of it", (min(x01)*100, max(x01)*100), "and {:.0f}--{:.0f} of one a tenth of it")
sm = lambda r, k: [TD[r]["per_endpoint"][e][k]["new:x1"]["blocked"] for e in ("E2", "E3", "E4")]
b3, o3 = sm(*S3[0]), sm(*S3[1]) + sm(*S3[2])
good = all(med("fleets", e) > 1 for e in ("E2", "E3", "E4")) and "a botnet the size of the window lies below the binomial's floor" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: on the small endpoints the binomial's floor exceeds the window")
chk("V-D: small endpoints, binomial at 1x", "which stops $2$--$5\\%$ of it on new stacks", (min(b3)*100, max(b3)*100), "which stops {:.0f}--{:.0f} of it on new stacks")
chk("V-D: small endpoints, beta-binomial and z-score at 1x", "same budget stop $6$--$26\\%$", (min(o3)*100, max(o3)*100), "same budget stop {:.0f}--{:.0f}")
good = fz["clean_fires"] == 5 and fmt(fz["clean_rate"]) == "0.1" and "fires on $0.1\\%$ of clean windows (5 of 5\\,643)" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: the binomial configuration, {fz['clean_fires']} false alarms on the test days")
chk("V-D: the binomial configuration, pooled", "stops $38.4\\%$ and $77.7\\%$ of 100 and 1\\,000 attackers on new stacks and $21.7\\%$ and $63.3\\%$ on shared ones",
    tuple(fz[x]["blocked"]*100 for x in ("new:A100", "new:A1000", "shared:A100", "shared:A1000")),
    "stops {:.1f} and {:.1f} of 100 and 1\\,000 attackers on new stacks and {:.1f} and {:.1f} on shared ones")
un = TD["base"]["all"]["unseen|origins"]
good = un["shared:A100"]["blocked"] == un["shared:A1000"]["blocked"] == 0 and "where the unseen filter alone stops none" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: the unseen filter alone stops no shared stack")
good = (fmt(zc["clean_rate"]) == fmt(ob["clean_rate"]) == "0.4" and (zc["clean_fires"], ob["clean_fires"]) == (20, 22)
        and "fire on $0.4\\%$ (20 and 22 windows)" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: z-score and beta-binomial fire on {zc['clean_fires']} and {ob['clean_fires']} clean windows")
chk("V-D: z-score and beta-binomial at 100 attackers", "($54.7\\%$ and $59.8\\%$ on new stacks, $23.7\\%$ and $40.5\\%$ on shared ones)",
    tuple(s[x]["blocked"]*100 for x in ("new:A100", "shared:A100") for s in (zc, ob)), "({:.1f} and {:.1f} on new stacks, {:.1f} and {:.1f} on shared ones)")
good = all(s[x]["blocked"] >= fz[x]["blocked"] for s in (zc, ob) for x in ("new:A100", "shared:A100")) and "stop as many or more at 100 attackers" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: both stop as many or more at 100 attackers")
chk("V-D: lighter alarms", "($10.8\\%$ and $10.5\\%$ of the window's clients against $32.9\\%$)",
    (zc["clean_collateral_median"]*100, ob["clean_collateral_median"]*100, fz["clean_collateral_median"]*100),
    "({:.1f} and {:.1f} of the window's clients against {:.1f})")
good = (fz["clean_rate"] < min(zc["clean_rate"], ob["clean_rate"]) and all(med("fleets", e) > med("od", e) for e in ("E1", "E2", "E3", "E4"))
        and "The binomial buys its lower false-alarm rate with a higher floor" in TEXN)
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: the binomial fires least and has the highest floor on every endpoint")
calib = [TD[r]["all"][k] for r, k in S3 + [("base", "enrichment|omega"), ("base", "union|origins")]]
good = all(x["attack_collateral_median"] == 0 for x in calib) and "every calibrated scope blocks a median $0\\%$ of legitimate clients" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: calibrated scopes block a median 0% of legitimate clients in attack windows")
good = med("fleets", "E1") < 0.1 < med("base", "E1") and "sits above its floor once known fleets are exempted" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} V-D: 0.1x on E1 lies between the floors with and without known fleets")
S1 = PT["stealth_E1"]["fleets"]["fresh:x0.1"]; S2 = PT["stealth_E1"]["fleets"]["tail:x0.1"]
gt = [S1[f]["gate"] for f in tf]; rw = [S1[f]["recall_where_named"] for f in tf]
nm = [S[f]["named"] for S in (S1, S2) for f in tf + ["2026-09-25"]]
good = min(nm) == 1.0 and all(0.85 <= x <= 0.95 for x in rw) and f"${min(gt)*100:.1f}$--${max(gt)*100:.0f}\\%$ of those windows" in TEX \
    and S1["2026-09-25"]["gate"] == 0 and "the trigger never fired" in TEXN and "on new and on shared stacks" in TEXN
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} V-D: E1 at 0.1x named in every window (new and shared stacks), gate {min(gt)*100:.1f}--{max(gt)*100:.1f}%, none on the fresh day")
e1f, e1o = TD["fleets"]["per_endpoint"]["E1"], TD["od"]["per_endpoint"]["E1"]
chk("V-D: E1 0.1x blocked with fleets", "so $11.8\\%$ of the", e1f["union|origins"]["new:x0.1"]["blocked"]*100, "so {:.1f} of the")
chk("V-D: scope alone, E1 0.1x, binomial", "stops $89.6\\%$ of them on new stacks and $61.1\\%$ on shared ones at $1.0\\%$",
    (e1f["union|none"]["new:x0.1"]["blocked"]*100, e1f["union|none"]["shared:x0.1"]["blocked"]*100, e1f["union|none"]["clean_rate"]*100),
    "stops {:.1f} of them on new stacks and {:.1f} on shared ones at {:.1f}")
chk("V-D: scope alone, E1 0.1x, beta-binomial", "and $90.0\\%$ and $78.3\\%$ at $2.1\\%$ with the beta-binomial",
    (e1o["union|none"]["new:x0.1"]["blocked"]*100, e1o["union|none"]["shared:x0.1"]["blocked"]*100, e1o["union|none"]["clean_rate"]*100),
    "and {:.1f} and {:.1f} at {:.1f} with the beta-binomial")
chk("App. E: scope alone with fleets, all endpoints", "on $2.2\\%$ of pooled", TD["fleets"]["all"]["union|none"]["clean_rate"]*100, "on {:.1f} of pooled")
chk("App. E: same, fresh day", "and $0.5\\%$ on the fresh day", FD["fleets"]["all"]["union|none"]["clean_rate"]*100, "and {:.1f} on the fresh day")
chk("App. E: scope alone without fleets", "against $3.5\\%$ and", TD["base"]["all"]["union|none"]["clean_rate"]*100, "against {:.1f} and")
chk("App. E: same, fresh day, without fleets", "and $8.8\\%$ without", FD["base"]["all"]["union|none"]["clean_rate"]*100, "and {:.1f} without")
good = "push $\\lambda_e$ to the levels of Table~\\ref{tab:floor}" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: levels given by tab:floor (checked above)")
zh = TD["base"]["all"]["zhist|origins"]
good = 0.45 <= zh["flash100"] <= 0.55 and "own history on half of them" in TEXN; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} App. E: historical z-score fires on half the flash crowds ({zh['flash100']*100:.1f})")
chk("App. E: uncalibrated z-score, clean", "fires on $2.6\\%$ of clean", TD["base"]["all"]["zscore|omega"]["clean_rate"]*100, "fires on {:.1f} of clean")
chk("App. E: uncalibrated z-score, flash", "and $64.5\\%$ of flash crowds", TD["base"]["all"]["zscore|omega"]["flash100"]*100, "and {:.1f} of flash crowds")
wa_ = TD["base"]["waf"]
chk("App. E: WAF agreement on E3", "blocked $84\\%$ and", wa_["E3"]["enrichment"]["precision"]*100, "blocked {:.0f} and")
chk("App. E: WAF agreement on E4", "and $96\\%$ on the two", wa_["E4"]["enrichment"]["precision"]*100, "and {:.0f} on the two")
chk("App. E: WAF agreement on E2", "and $1.5\\%$ on the one", wa_["E2"]["enrichment"]["precision"]*100, "and {:.1f} on the one")
chk("App. E: WAF coverage", "matches $16.7\\%$ of all", wa_["all"]["enrichment"]["coverage"]*100, "matches {:.1f} of all")

print("== the fresh day (production_tables.json, compile_production_check_fresh.json)")
from scipy.stats import binom as _binom
pv = _binom.sf(ff_["clean_fires"] - 1, ff_["clean_windows"], fz["clean_fires"] / fz["clean_windows"])
good = ff_["clean_fires"] == 2 and "gives the binomial configuration 2 false alarms in 1\\,152 clean windows" in TEXN \
    and f"($P = {pv:.2f}$)" in TEX and pv >= 0.05
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} fresh day: {ff_['clean_fires']} of {ff_['clean_windows']}, P = {pv:.3f} (protocol: consistent)")
good = FD["fleets"]["per_endpoint"]["E2"]["union|origins"]["clean_fires"] == 2 and PT["endpoints"]["E2"] == "web console" \
    and "Both fall on the web console" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} fresh day: both false alarms on the web console")
chk("fresh day: collateral of the two", "block a median $41.2\\%$ of their", ff_["clean_collateral_median"]*100, "block a median {:.1f} of their")
chk("fresh day: blocked", "stops $38.9\\%$ and $73.4\\%$ of 100 and 1\\,000 attackers on new stacks and $21.5\\%$ and $60.9\\%$ on shared ones",
    tuple(ff_[x]["blocked"]*100 for x in ("new:A100", "new:A1000", "shared:A100", "shared:A1000")),
    "stops {:.1f} and {:.1f} of 100 and 1\\,000 attackers on new stacks and {:.1f} and {:.1f} on shared ones")
chk("fresh day, calibrated z-score at 100", "attackers ($58.3\\%$ and $26.7\\%$)", (zf["new:A100"]["blocked"]*100, zf["shared:A100"]["blocked"]*100),
    "attackers ({:.1f} and {:.1f})")
ov, ot, orl = FD["overlap_frozen_zcal"], TD["overlap_frozen_zcal"], FD["overlap_frozen_rule"]
good = orl["frozen"] == orl["rule"] == orl["both"] == 2 and ov["frozen"] == ov["zcal"] == ov["both"] == 2 \
    and "the base rule, the protocol's reference, fired on the same two windows" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} fresh day: the z-score {ov} and the base rule {orl} fired on the same two windows")
good = ot["frozen"] == 5 and ot["both"] == 4 and "it shared 4 of the test's 5 false alarms" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} test days: the calibrated z-score shared {ot['both']} of the test's {ot['frozen']} false alarms")
good = fo["clean_fires"] == 0 and "The beta-binomial, built after the day was read, raised none" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} fresh day: the beta-binomial raised {fo['clean_fires']} false alarms")
cpf = json.load(open(R + "compile_production_check_fresh.json"))
good = cpf["origins_equal"] == cpf["net24_pairs_equal"] == cpf["windows"] == 1152 and "equal to the export in all 1\\,152 windows" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} fresh day: compiled query equals the export in {cpf['origins_equal']}/{cpf['windows']} windows")
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
        and "and the JA4 class sizes wherever the WAF blocked no client" in TEXN)
ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} compiled query in the operator's store: origins and /24 pairs equal the export "
      f"in {cp['origins_equal']}/{cp['windows']} windows")
sv = json.load(open(R + "stix_validation.json"))
good = (sv["ok"] and sv["errors"] == 0 and sv["warnings"] == 0 and sv["strict_errors"] == 0
        and all(c["valid_strict"] for c in sv["chains"]) and "pass the OASIS validator in strict mode" in TEXN
        and sv["bundles"] == 4 and "passes the exported bundles through the OASIS STIX~2.1 validator in strict mode" in TEXN)
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
        and mi["course_of_action_kept"] and "MISP's importer drops the fingerprints" in TEXN)
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
good = fp["eligible"] == [fp["chosen_share"]] and len(fp["design"]) == 5 and "was the only one that did not raise false alarms" in TEXN
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
print("== abstract and conclusion")
ab = re.sub(r"\s+", " ", TEX[TEX.index("\\begin{abstract}"):TEX.index("\\end{abstract}")])
def abs_chk(label, phrase, value, fmt_):
    global ok, bad
    got = fmt_.format(*value) if isinstance(value, tuple) else fmt_.format(value)
    good = phrase in ab and got == phrase.replace("\\%", "").replace("$", "")
    ok += good; bad += not good
    print(f"{'OK ' if good else 'XX '} abstract: {label:44s} phrase={phrase!r} data={got}")
abs_chk("modal blocks none", "blocks $0\\%$ of a", g(1.5, 5, 0, "modal_cov"), "blocks {:.0f} of a")
abs_chk("modal hits legitimate traffic", "and $39\\%$ of legitimate", g(1.5, 5, 0, "modal_coll"), "and {:.0f} of legitimate")
abs_chk("enrichment up to 25 stacks", "blocks $90\\%$ up to 25", g(1.5, 25, 0, "enr_cov"), "blocks {:.0f} up to 25")
abs_chk("enrichment on shared stacks, collateral", "and $85\\%$ at $2\\%$ collateral on stacks",
        (us("shared_profile_tail", 25, 0, "enrichment", "recall")*100, us("shared_profile_tail", 25, 0, "enrichment", "fpr")*100), "and {:.0f} at {:.0f} collateral on stacks")
good = us("shared_profile_tail", 25, 0, "unseen", "recall") == 0 and "where that filter blocks none" in ab; ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: the unseen filter blocks no shared stack")
good = all(us("original", s, 0, "unseen", "recall") == us("original", s, 0, "enrichment", "recall") for s in (1, 5, 25))
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the unseen filter blocks as much as the test up to 25 stacks")
abs_chk("the unseen filter's collateral", "as does an unseen-fingerprint filter at $0.03\\%$",
        max(us("original", s, 0, "unseen", "fpr") for s in (1, 5, 25))*100, "as does an unseen-fingerprint filter at {:.2f}")
abs_chk("learned model, in and out of distribution", "(AUC $0.98$) falls to $0.48$--$0.75$ on another stack count",
        (au(1000, "rf", "d"), min(xs), max(xs)), "(AUC {:.2f}) falls to {:.2f}--{:.2f} on another stack count")
abs_chk("binomial floor", "names is $16\\%$ of the busiest endpoint's window and $4$--$12$ windows on the small ones",
        (med("base", "E1")*100, min(small), max(small)), "names is {:.0f} of the busiest endpoint's window and {:.0f}--{:.0f} windows on the small ones")
abs_chk("beta-binomial floor", "lowers it to $3\\%$ and $0.9$--$2.8$ windows", (med("od", "E1")*100, min(so_), max(so_)), "lowers it to {:.0f} and {:.1f}--{:.1f} windows")
abs_chk("beta-binomial at the z-score's operating point", "the same budget, $0.4\\%$ of clean windows", ob["clean_rate"]*100, "the same budget, {:.1f} of clean windows")
good = fmt(ob["clean_rate"]) == fmt(zc["clean_rate"]); ok += good; bad += not good
print(f"{'OK ' if good else 'XX '} abstract: beta-binomial and calibrated z-score share the operating point ({ob['clean_rate']*100:.2f}, {zc['clean_rate']*100:.2f})")
abs_chk("every calibrated scope at the busiest window", "stops $67$--$71\\%$ of a botnet as large", (min(x1)*100, max(x1)*100), "stops {:.0f}--{:.0f} of a botnet as large")
good = "gives the binomial 2 false alarms in 1\\,152 windows" in ab and ff_["clean_fires"] == 2 and ff_["clean_windows"] == 1152
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: fresh day, 2 false alarms in 1,152 windows")
good = cp["origins_equal"] == cp["windows"] and cpf["origins_equal"] == cpf["windows"] and "reproducing the operator's origin and /24-pair counts on two days" in ab
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} abstract: the compiled query reproduces the exports on two days")
chk("VII: floors under both backgrounds", "$16\\%$ of the busiest endpoint's window under the binomial and $3\\%$ under a beta-binomial",
    (med("base", "E1")*100, med("od", "E1")*100), "{:.0f} of the busiest endpoint's window under the binomial and {:.0f} under a beta-binomial")
good = fmt(ob["clean_rate"]) == fmt(zc["clean_rate"]) and "that models them, at the operating point of a calibrated $z$-score" in TEXN
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: the beta-binomial at the calibrated z-score's operating point")
good = "A fresh day is consistent with the binomial configuration's false-alarm rate" in TEXN and pv >= 0.05
ok += good; bad += not good; print(f"{'OK ' if good else 'XX '} VII: the fresh day is consistent (P = {pv:.2f})")
print(f"\nTOTAL: {ok} OK, {bad} mismatches")
sys.exit(1 if bad else 0)
