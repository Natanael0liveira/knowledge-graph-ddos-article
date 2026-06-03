#!/usr/bin/env python3
"""Compute coordination score Ω(S) and validate Sprint-1 gates G3 + G4.

Implements the coordination model from papers/http-session/article.tex §3.3, scoped
to the sub-relations computable from the session data (decision: "3 limpas"):

    relatedByTLSFingerprint    w = 1.0   (shared JA4)
    relatedByEndpointConvergence w = 0.6 (shared dst endpoint)
    relatedByNetworkProximity  w = 0.3   (shared src /24)

Ω(S) = Σ_i w_i · |{(s_a,s_b) ∈ S×S, s_a≠s_b : (s_a, relatedBy_i, s_b) ∈ E}|

The other three sub-relations (ReusedIdentity, TemporalPattern, PayloadSignature)
need data not present at session granularity in this dataset, so they are reported
as inactive.

**Anti-circularity:** the ground-truth `cluster_id` is derived from
[label, dst_ip, dst_port] (see derive_clusters.py), so it embeds the answer. We do
NOT use it as the cluster S. Instead we form *detection clusters* label-agnostically
by (endpoint, time-window). Ground-truth labels are used ONLY to evaluate the gates.

Pairwise edge counts are computed in O(N) via group cardinalities — for a value v
shared by n sessions inside S, the number of internal pairs is C(n,2) = n(n-1)/2 —
never materializing the O(N²) edge set.

Gates:
  G3: ROC AUC ≥ 0.85 for a simple classifier (attack vs benign) using behavioral +
      coordination features (label-agnostic).
  G4: the coordinatedHTTPFlood rule returns ≥ 1 detection cluster with Ω(S) ≥ τ,
      |S| ≥ k_min and aggregate request rate ≥ τ_rate.
"""
import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

W_TLS = 1.0
W_ENDPOINT = 0.6
W_NET = 0.3

# Dataset-agnostic: attack = any labeled session that is not benign. Works for
# cic-iot-2023 (HTTP-Flood/Slowloris) and cicids2017 (Hulk/GoldenEye/Slow*/DoS-Other).
BENIGN_LABELS = {"BENIGN"}
NON_LABELS = {"UNLABELED", None}


def _is_attack(s: pd.Series) -> pd.Series:
    return ~s.isin(BENIGN_LABELS | NON_LABELS)


def _pairs(n: pd.Series) -> pd.Series:
    """C(n,2) = n(n-1)/2, vectorized."""
    return n * (n - 1) // 2


def assign_detection_clusters(df: pd.DataFrame, window_s: int) -> pd.DataFrame:
    """Label-agnostic clustering: same endpoint, contiguous within ``window_s``."""
    df = df.copy()
    df["endpoint"] = (
        df["dst_ip_first"].astype(str) + ":" + df["dst_port_first"].astype(str)
    )
    df["net24"] = df["src_ip_first"].astype(str).str.rsplit(".", n=1).str[0]
    df = df.sort_values(["endpoint", "start_ts"]).reset_index(drop=True)

    ep_change = df["endpoint"] != df["endpoint"].shift()
    gap = df["start_ts"].diff().dt.total_seconds()
    breaks = ep_change | (gap > window_s)
    df["det_cluster"] = breaks.cumsum()
    return df


def compute_omega(df: pd.DataFrame) -> pd.DataFrame:
    """Per detection-cluster Ω(S) + descriptive fields (for G4 + evaluation)."""
    g = df.groupby("det_cluster")

    size = g.size().rename("size")

    # pairs sharing endpoint = C(size,2), since cluster IS one endpoint
    pairs_ep = _pairs(size).rename("pairs_endpoint")

    # pairs sharing JA4 (non-null only)
    ja4 = df.dropna(subset=["ja4"])
    pairs_ja4 = (
        ja4.groupby(["det_cluster", "ja4"]).size().pipe(_pairs)
        .groupby(level=0).sum().rename("pairs_ja4")
    )

    # pairs sharing src /24
    pairs_net = (
        df.groupby(["det_cluster", "net24"]).size().pipe(_pairs)
        .groupby(level=0).sum().rename("pairs_net")
    )

    out = pd.concat([size, pairs_ep, pairs_ja4, pairs_net], axis=1).fillna(0)
    out["omega"] = (
        W_TLS * out["pairs_ja4"]
        + W_ENDPOINT * out["pairs_endpoint"]
        + W_NET * out["pairs_net"]
    )

    # aggregate request rate to the endpoint (req/s over the cluster span)
    span = (g["end_ts"].max() - g["start_ts"].min()).dt.total_seconds().rename("span_s")
    reqs = g["n_requests"].sum().rename("total_requests")
    out = out.join(span).join(reqs)
    out["agg_rate"] = out["total_requests"] / out["span_s"].clip(lower=1.0)

    # descriptive (NOT used for detection): endpoint + dominant ground-truth label
    out = out.join(g["endpoint"].first())
    label_col = "label_first" if "label_first" in df.columns else "label"
    dom = g[label_col].agg(lambda s: s.value_counts().idxmax()).rename("dominant_label")
    attack_frac = (
        g[label_col].agg(lambda s: _is_attack(s).mean())
        .rename("attack_frac")
    )
    out = out.join(dom).join(attack_frac)
    return out.reset_index()


def gate_g4(clusters: pd.DataFrame, tau_cluster: float, k_min: int, tau_rate: float,
            http_ports: set | None = None):
    """coordinatedHTTPFlood: clusters with Ω ≥ τ, |S| ≥ k_min, rate ≥ τ_rate.

    The rule is HTTP-specific, so when ``http_ports`` is given we restrict to
    endpoints on those ports — otherwise high-volume benign services (e.g. DNS on
    :53) dominate Ω purely via endpoint-convergence mass.
    """
    c = clusters
    if http_ports:
        port = c["endpoint"].str.rsplit(":", n=1).str[1]
        c = c[pd.to_numeric(port, errors="coerce").isin(http_ports)]
    hits = c[
        (c["omega"] >= tau_cluster)
        & (c["size"] >= k_min)
        & (c["agg_rate"] >= tau_rate)
    ].sort_values("omega", ascending=False)
    return hits


def session_features(df: pd.DataFrame) -> pd.DataFrame:
    """Per-session features for G3, all label-agnostic."""
    g = df.groupby("det_cluster")
    df = df.copy()
    df["cluster_size"] = g["session_id"].transform("size")
    # peers in same cluster sharing JA4 / /24 (0 when ja4 missing)
    df["share_ja4"] = (
        df.groupby(["det_cluster", "ja4"])["session_id"].transform("size") - 1
    ).fillna(0)
    df["share_net"] = (
        df.groupby(["det_cluster", "net24"])["session_id"].transform("size") - 1
    )
    df["req_per_s"] = df["n_requests"] / df["duration_s"].clip(lower=0.001)
    return df


def gate_g3(df: pd.DataFrame):
    """Simple classifiers (LogReg + RandomForest); report ROC AUC (attack vs benign).

    Both are off-the-shelf "simple" models. LogReg is linear; RF captures the
    non-linear interactions the coordination features exhibit. We report both
    honestly — the gate asks whether the features *can* separate the classes.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    label_col = "label_first" if "label_first" in df.columns else "label"
    y = _is_attack(df[label_col]).astype(int).values

    feats = [
        "n_requests", "duration_s", "req_per_s",
        "fwd_bytes_sum", "bwd_bytes_sum", "fwd_pkts_sum", "bwd_pkts_sum",
        "iat_mean_mean", "iat_std_mean",
        "cluster_size", "share_ja4", "share_net",
    ]
    feats = [f for f in feats if f in df.columns]
    X = df[feats].replace([np.inf, -np.inf], np.nan).fillna(0.0).values

    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    scaler = StandardScaler().fit(Xtr)
    lr = LogisticRegression(max_iter=1000, class_weight="balanced")
    lr.fit(scaler.transform(Xtr), ytr)
    auc_lr = roc_auc_score(yte, lr.predict_proba(scaler.transform(Xte))[:, 1])

    rf = RandomForestClassifier(
        n_estimators=200, n_jobs=-1, random_state=42, class_weight="balanced"
    )
    rf.fit(Xtr, ytr)
    auc_rf = roc_auc_score(yte, rf.predict_proba(Xte)[:, 1])
    importances = dict(sorted(zip(feats, rf.feature_importances_),
                              key=lambda kv: -kv[1]))

    # Ablation: isolate the contribution of the coordination (relatedBy_*) features
    # from the purely behavioral flow features — the gate asks about relatedBy_*.
    coord_feats = [f for f in ("cluster_size", "share_ja4", "share_net") if f in feats]
    behav_feats = [f for f in feats if f not in coord_feats]

    def _auc(cols):
        idx = [feats.index(c) for c in cols]
        m = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=42,
                                   class_weight="balanced")
        m.fit(Xtr[:, idx], ytr)
        return roc_auc_score(yte, m.predict_proba(Xte[:, idx])[:, 1])

    auc_coord = _auc(coord_feats) if coord_feats else float("nan")
    auc_behav = _auc(behav_feats) if behav_feats else float("nan")
    ablation = {"coordination_only": auc_coord, "behavioral_only": auc_behav,
                "coord_feats": coord_feats, "behav_feats": behav_feats}
    return auc_lr, auc_rf, feats, importances, ablation


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--out", type=Path, default=None, help="cluster coordination CSV")
    ap.add_argument("--window-s", type=int, default=300)
    ap.add_argument("--k-min", type=int, default=5)
    ap.add_argument("--tau-rate", type=float, default=1.0)
    ap.add_argument("--tau-cluster", type=float, default=None,
                    help="Ω threshold; default = 99th pct of benign-dominant clusters")
    ap.add_argument("--http-ports", default="80,443,8080,8000,8008,8443,8888",
                    help="comma ports treated as HTTP for the G4 rule; empty = no filter")
    ap.add_argument("--emit-nt", type=Path, default=None,
                    help="Write detection-cluster coordination triples (N-Triples) "
                         "for SPARQL-side G4 — load into Fuseki with tdb2.tdbloader.")
    args = ap.parse_args()

    df = pd.read_parquet(args.sessions)
    log.info("Loaded %d sessions", len(df))

    df = assign_detection_clusters(df, args.window_s)
    n_clusters = df["det_cluster"].nunique()
    log.info("Formed %d label-agnostic detection clusters (window=%ds)",
             n_clusters, args.window_s)

    clusters = compute_omega(df)
    multi = clusters[clusters["size"] >= 2]
    log.info("Clusters with ≥2 sessions: %d", len(multi))

    # data-driven τ_cluster: separate from benign-dominant background
    benign = clusters[clusters["dominant_label"] == "BENIGN"]
    if args.tau_cluster is None:
        tau = float(np.percentile(benign["omega"], 99)) if len(benign) else 1.0
        tau = max(tau, 1.0)
    else:
        tau = args.tau_cluster
    log.info("τ_cluster = %.3f (k_min=%d, τ_rate=%.2f)", tau, args.k_min, args.tau_rate)

    # ---- G4 ----
    http_ports = {int(p) for p in args.http_ports.split(",") if p.strip()} or None
    hits = gate_g4(clusters, tau, args.k_min, args.tau_rate, http_ports)
    if http_ports:
        log.info("  (filtro HTTP ativo: portas %s)", sorted(http_ports))
    g4_pass = len(hits) >= 1
    attack_purity = hits["attack_frac"].mean() if len(hits) else float("nan")
    n_attack_dom = int((hits["attack_frac"] >= 0.5).sum()) if len(hits) else 0
    log.info("=== G4 coordinatedHTTPFlood ===")
    log.info("  clusters detectados: %d (Ω≥%.2f, |S|≥%d, rate≥%.2f)",
             len(hits), tau, args.k_min, args.tau_rate)
    log.info("  attack-dominant: %d/%d | pureza média: %.3f",
             n_attack_dom, len(hits), attack_purity)
    if len(hits):
        log.info("  top 5 por Ω:")
        for _, r in hits.head(5).iterrows():
            log.info("    %s Ω=%.1f |S|=%d rate=%.1f label=%s",
                     r["endpoint"], r["omega"], r["size"], r["agg_rate"],
                     r["dominant_label"])
    log.info("  G4 %s", "PASS ✅" if g4_pass else "FAIL ❌")

    # ---- G3 ----
    df = session_features(df)
    auc_lr, auc_rf, feats, importances, ablation = gate_g3(df)
    auc = max(auc_lr, auc_rf)
    g3_pass = auc >= 0.85
    log.info("=== G3 ROC AUC ===")
    log.info("  features (%d): %s", len(feats), ", ".join(feats))
    log.info("  AUC LogReg = %.4f | AUC RandomForest = %.4f", auc_lr, auc_rf)
    log.info("  ABLAÇÃO RF: coordenação-só = %.4f (%s) | comportamental-só = %.4f",
             ablation["coordination_only"], ",".join(ablation["coord_feats"]),
             ablation["behavioral_only"])
    log.info("  G3 (melhor=%.4f) %s", auc, "PASS ✅" if g3_pass else "FAIL ❌")
    log.info("  importâncias RF: %s",
             ", ".join(f"{k}={v:.2f}" for k, v in list(importances.items())[:6]))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        clusters.to_csv(args.out, index=False)
        log.info("Coordination CSV → %s", args.out)

    if args.emit_nt:
        emit = clusters[clusters["size"] >= 2]
        args.emit_nt.parent.mkdir(parents=True, exist_ok=True)
        kg = "http://security.example.org/ontology/ddos#"
        xsd = "http://www.w3.org/2001/XMLSchema#"
        rdf_type = "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
        n = 0
        with open(args.emit_nt, "w", encoding="utf-8") as fh:
            for _, r in emit.iterrows():
                c = f"<{kg}detcluster/{int(r['det_cluster'])}>"
                ep = str(r["endpoint"]).replace("\\", "\\\\").replace('"', '\\"')
                fh.write(f"{c} {rdf_type} <{kg}DetectionCluster> .\n")
                fh.write(f'{c} <{kg}coordinationScore> "{r["omega"]:.4f}"^^<{xsd}double> .\n')
                fh.write(f'{c} <{kg}clusterSize> "{int(r["size"])}"^^<{xsd}integer> .\n')
                fh.write(f'{c} <{kg}aggregateRate> "{r["agg_rate"]:.4f}"^^<{xsd}double> .\n')
                fh.write(f'{c} <{kg}targetEndpoint> "{ep}" .\n')
                n += 5
        log.info("Emitted %d coordination triples → %s", n, args.emit_nt)

    print("\n========== RESUMO GATES ==========")
    print(f"G3 ROC AUC = {auc:.4f} (LR={auc_lr:.4f}, RF={auc_rf:.4f})  "
          f"({'PASS' if g3_pass else 'FAIL'})")
    print(f"G4 coordinatedHTTPFlood: {len(hits)} clusters, {n_attack_dom} attack-dom "
          f"(τ={tau:.2f})  ({'PASS' if g4_pass else 'FAIL'})")


if __name__ == "__main__":
    main()
