#!/usr/bin/env python3
"""Pilar 4 do paper — cadeia de evidência simbólica + mitigação cirúrgica.

Quando a regra coordinatedHTTPFlood dispara sobre um cluster S de sessões, este
módulo produz:

1. DECOMPOSIÇÃO de Ω(S) por sub-relação relatedBy_* (quais sinais ativaram, com peso).
2. ESCOPO de mitigação derivado AUTOMATICAMENTE do conjunto mínimo de propriedades
   compartilhadas pelo cluster — tipicamente (fingerprint TLS, padrão de endpoint),
   eventualmente reforçado por proximidade de rede.
3. CADEIA DE EVIDÊNCIA exportável em JSON-LD (vocabulário da ontologia) e STIX 2.1
   (Indicator + Course-of-Action + Relationship): o veredicto é a derivação que
   satisfez a regra, não a saída de um classificador.
4. DANO COLATERAL estimado: quantas sessões BENIGN o escopo cirúrgico atinge,
   versus um rate-limit GLOBAL no endpoint (que atinge todo o tráfego legítimo).

Contraste com KLAGE: lá o pipeline termina no relatório textual; aqui a mitigação
tem escopo derivado simbolicamente do discriminador do cluster.

Uso:
    python evidence_mitigation.py --demo                 # exemplo-brinquedo (offline)
    python evidence_mitigation.py --cluster s.parquet --benign b.parquet --out-dir out/
"""
import argparse
import json
import logging
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ONT = "http://security.example.org/ontology/ddos#"
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from kg_ontology import WEIGHTS  # noqa: E402  (coordinationWeight, read from the ontology)


def _pairs(n):
    return n * (n - 1) // 2


def _net24(ip):
    return str(ip).rsplit(".", 1)[0]


def decompose_omega(cluster: pd.DataFrame, unit: str = "session") -> dict:
    """Ω(S) decomposto por sub-relação: pares ligados × peso. Só as sub-relações
    com dado disponível a nível de sessão (TLS/JA4, endpoint, rede).

    ``unit="origin"`` counts each class in distinct source addresses, so pairs
    link origins and ``size`` is the number of origins (the paper's method).
    """
    cluster = cluster.copy()
    cluster["endpoint"] = cluster["dst_ip_first"].astype(str) + ":" + cluster["dst_port_first"].astype(str)
    cluster["net24"] = cluster["src_ip_first"].map(_net24)

    def classes(key, frame=cluster):
        grp = frame.groupby(key)
        return grp["src_ip_first"].nunique() if unit == "origin" else grp.size()

    contrib = {}
    # TLSFingerprint: pares que compartilham JA4 (não-nulo)
    contrib["relatedByTLSFingerprint"] = int(classes("ja4", cluster.dropna(subset=["ja4"])).map(_pairs).sum())
    # EndpointConvergence: pares no mesmo endpoint
    contrib["relatedByEndpointConvergence"] = int(classes("endpoint").map(_pairs).sum())
    # NetworkProximity: pares no mesmo /24
    contrib["relatedByNetworkProximity"] = int(classes("net24").map(_pairs).sum())

    activated = {k: {"pairs": v, "weight": WEIGHTS[k], "weighted": WEIGHTS[k] * v}
                 for k, v in contrib.items() if v > 0}
    omega = sum(a["weighted"] for a in activated.values())
    size = int(cluster["src_ip_first"].nunique()) if unit == "origin" else len(cluster)
    return {"omega": omega, "activated": activated, "size": size}


def derive_scope(cluster: pd.DataFrame, coverage: float = 0.9) -> dict:
    """Escopo mínimo: propriedades compartilhadas por ≥coverage do SUBCONJUNTO COORDENADO.

    O escopo descreve a coordenação que a regra flagrou, não o cluster bruto de
    (endpoint, janela). Num serviço sob ataque, usuários legítimos compartilham o
    endpoint mas têm JA4 diverso; computar a cobertura sobre o cluster inteiro diluiria
    o JA4 do atacante abaixo do limiar e degradaria o escopo para o endpoint inteiro
    (mitigação global). Restringimos ao subconjunto que compartilha o sinal de peso alto
    dominante (JA4 modal) --- a assinatura da campanha. Quando não há JA4 (tráfego não-TLS,
    como nos datasets CIC), recai sobre o cluster inteiro e o escopo fica em endpoint/rede
    --- honestamente igual à mitigação global (sem discriminador, sem ganho cirúrgico)."""
    cluster = cluster.copy()
    cluster["endpoint"] = cluster["dst_ip_first"].astype(str) + ":" + cluster["dst_port_first"].astype(str)
    cluster["net24"] = cluster["src_ip_first"].map(_net24)
    # subconjunto coordenado: sessões que compartilham o JA4 modal (≥2 sharers)
    coord = cluster
    if cluster["ja4"].notna().any():
        vc = cluster["ja4"].value_counts()
        if vc.iloc[0] >= 2:
            coord = cluster[cluster["ja4"] == vc.index[0]]
    n = len(coord)
    scope = {}
    # JA4 (peso 1.0): valor modal cobre ≥coverage do subconjunto coordenado?
    if coord["ja4"].notna().any():
        top_ja4, cnt = coord["ja4"].value_counts().index[0], coord["ja4"].value_counts().iloc[0]
        if cnt / n >= coverage:
            scope["tlsJa4"] = top_ja4
    # Endpoint (peso 0.6)
    top_ep, cnt = coord["endpoint"].value_counts().index[0], coord["endpoint"].value_counts().iloc[0]
    if cnt / n >= coverage:
        scope["endpoint"] = top_ep
    # /24 (peso 0.3): só entra como reforço se um único /24 dominar (botnet concentrado)
    top_net, cnt = coord["net24"].value_counts().index[0], coord["net24"].value_counts().iloc[0]
    if cnt / n >= coverage:
        scope["srcNet24"] = top_net + ".0/24"
    return scope


def matches_scope(df: pd.DataFrame, scope: dict) -> pd.Series:
    """Máscara das sessões que casam com TODAS as condições do escopo (conjunção)."""
    df = df.copy()
    df["endpoint"] = df["dst_ip_first"].astype(str) + ":" + df["dst_port_first"].astype(str)
    df["net24"] = df["src_ip_first"].map(_net24).astype(str) + ".0/24"
    m = pd.Series(True, index=df.index)
    if "tlsJa4" in scope:
        m &= (df["ja4"] == scope["tlsJa4"])
    if "endpoint" in scope:
        m &= (df["endpoint"] == scope["endpoint"])
    if "srcNet24" in scope:
        m &= (df["net24"] == scope["srcNet24"])
    return m


def evidence_chain_jsonld(decomp: dict, scope: dict, cluster_id: str) -> dict:
    """Cadeia de evidência simbólica em JSON-LD (vocabulário da ontologia)."""
    return {
        "@context": {"kg": ONT, "xsd": "http://www.w3.org/2001/XMLSchema#"},
        "@id": f"kg:cluster/{cluster_id}",
        "@type": "kg:CoordinatedHTTPFlood",
        "kg:clusterSize": decomp["size"],
        "kg:coordinationScore": round(decomp["omega"], 3),
        "kg:verdict": "coordinated-campaign",
        "kg:activatedSubRelations": [
            {"@type": f"kg:{name}", "kg:coordinationWeight": a["weight"],
             "kg:linkedPairs": a["pairs"], "kg:weightedContribution": round(a["weighted"], 3)}
            for name, a in decomp["activated"].items()
        ],
        "kg:derivedMitigationScope": {f"kg:{k}": v for k, v in scope.items()},
    }


# Namespace of the deterministic STIX identifiers: the same verdict always yields
# the same objects, so re-exporting a chain does not duplicate it downstream. The
# identifiers are well-formed UUIDv4, as STIX 2.1 recommends for SDOs and SROs,
# derived from a hash of the verdict instead of drawn at random.
STIX_NAMESPACE = uuid.UUID("0d3f8a52-6c1e-5b7a-9e4f-2a7c1b9d5e30")
ONTOLOGY_URL = ("https://github.com/Natanael0liveira/knowledge-graph-ddos-article/"
                "blob/main/ontology/ddos_ontology.owl")


def _stix_id(kind, *parts):
    h = uuid.uuid5(STIX_NAMESPACE, "|".join(map(str, (kind,) + parts))).bytes
    return f"{kind}--{uuid.UUID(bytes=h, version=4)}"


STIX_IDENTITY = _stix_id("identity", "knowledge-graph-ddos-article")
# One property extension carries what STIX has no property for: the TLS JA4 of a
# network-traffic object, and the derivation behind an indicator.
STIX_EXTENSION = _stix_id("extension-definition", "kg-ddos-evidence", "1.0.0")


def _stix_str(v):
    return "'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'"


def stix_pattern(scope: dict) -> str:
    """The derived scope as one STIX 2.1 observation expression.

    Endpoint, fingerprints and prefix constrain the same network-traffic object.
    The fingerprint travels in the property extension (STIX has no JA4 property),
    and a fragmented botnet's set of fingerprints becomes an IN clause.
    """
    terms = []
    if "endpoint" in scope:
        ip, _, port = str(scope["endpoint"]).rpartition(":")
        terms += [f"network-traffic:dst_ref.value = {_stix_str(ip)}",
                  f"network-traffic:dst_port = {int(port)}"]
    ja4 = scope.get("tlsJa4")
    if ja4:
        vals = sorted(ja4) if isinstance(ja4, (list, set, tuple)) else [ja4]
        path = f"network-traffic:extensions.'{STIX_EXTENSION}'.ja4"
        terms.append(f"{path} = {_stix_str(vals[0])}" if len(vals) == 1 else
                     f"{path} IN ({', '.join(_stix_str(v) for v in vals)})")
    if "srcNet24" in scope:
        net = str(scope["srcNet24"])
        terms.append(f"network-traffic:src_ref.value ISSUBSET {_stix_str(net if '/' in net else net + '.0/24')}")
    return "[" + " AND ".join(terms or ["network-traffic:protocols[*] = 'http'"]) + "]"


def stix_bundle(decomp: dict, scope: dict, cluster_id: str,
                created: str = "2026-09-24T00:00:00.000Z") -> dict:
    """STIX 2.1: an Indicator whose pattern is the scope, a Course-of-Action, and
    the Relationship ``course-of-action mitigates indicator``, with the identity
    and the property-extension definition they reference.

    The objects come from the derivation alone: the extension carries Omega(S),
    the cluster size and the decomposition per sub-relation, so a SIEM or SOAR
    ingests the evidence chain with no translation step. ``created`` is the
    verdict's time; identifiers are deterministic in the cluster and the scope.
    """
    key = json.dumps({"cluster": cluster_id, "scope": scope}, sort_keys=True, default=sorted)
    ind_id = _stix_id("indicator", key)
    coa_id = _stix_id("course-of-action", key)
    subrel = {name: {"linked_pairs": int(a["pairs"]), "coordination_weight": float(a["weight"])}
              for name, a in decomp["activated"].items()}
    return {
        "type": "bundle", "id": _stix_id("bundle", key),
        "objects": [
            {"type": "identity", "spec_version": "2.1", "id": STIX_IDENTITY,
             "created": created, "modified": created, "name": "knowledge-graph-ddos-article",
             "description": "Session-centric knowledge graph that derives the verdict and the "
                            "mitigation scope of coordinated application-layer DDoS.",
             "identity_class": "system"},
            {"type": "extension-definition", "spec_version": "2.1", "id": STIX_EXTENSION,
             "created_by_ref": STIX_IDENTITY, "created": created, "modified": created,
             "name": "kg-ddos-evidence",
             "description": "The TLS JA4 fingerprint of a network-traffic object, and the "
                            "derivation behind an indicator: coordination mass, cluster size "
                            "and the weighted relatedBy sub-relations, as the ontology defines them.",
             "schema": ONTOLOGY_URL, "version": "1.0.0",
             "extension_types": ["property-extension"]},
            {"type": "indicator", "spec_version": "2.1", "id": ind_id, "created_by_ref": STIX_IDENTITY,
             "created": created, "modified": created, "valid_from": created,
             "name": f"Coordinated HTTP flood, cluster {cluster_id}",
             "description": f"CoordinatedHTTPFlood: Omega(S) = {decomp['omega']:.1f} over "
                            f"{decomp['size']} origins; sub-relations: {', '.join(decomp['activated'])}.",
             "indicator_types": ["malicious-activity"],
             "pattern_type": "stix", "pattern": stix_pattern(scope),
             "extensions": {STIX_EXTENSION: {"extension_type": "property-extension",
                                             "coordination_score": round(float(decomp["omega"]), 3),
                                             "cluster_size": int(decomp["size"]),
                                             "subrelations": subrel}}},
            {"type": "course-of-action", "spec_version": "2.1", "id": coa_id,
             "created_by_ref": STIX_IDENTITY, "created": created, "modified": created,
             "name": "Scoped mitigation of a coordinated HTTP flood",
             "description": "Filter or challenge only the traffic that matches the indicator's "
                            "pattern, the discriminator the verdict derived; the endpoint's other "
                            "clients are left alone."},
            {"type": "relationship", "spec_version": "2.1", "id": _stix_id("relationship", key),
             "created_by_ref": STIX_IDENTITY, "created": created, "modified": created,
             "relationship_type": "mitigates", "source_ref": coa_id, "target_ref": ind_id},
        ],
    }


def collateral(scope: dict, benign: pd.DataFrame) -> dict:
    """Dano colateral: benignos pegos pelo escopo cirúrgico vs por rate-limit global."""
    surgical = int(matches_scope(benign, scope).sum())
    # rate-limit global = bloquear o endpoint inteiro → todo benigno naquele endpoint
    glob = 0
    if "endpoint" in scope:
        ep = benign["dst_ip_first"].astype(str) + ":" + benign["dst_port_first"].astype(str)
        glob = int((ep == scope["endpoint"]).sum())
    n = len(benign)
    return {"benign_total": n,
            "surgical_hits": surgical, "surgical_fpr": surgical / n if n else 0.0,
            "global_endpoint_hits": glob, "global_fpr": glob / n if n else 0.0}


def run(cluster: pd.DataFrame, benign: pd.DataFrame, cluster_id="c001") -> dict:
    decomp = decompose_omega(cluster)
    scope = derive_scope(cluster)
    return {
        "decomposition": decomp,
        "scope": scope,
        "evidence_jsonld": evidence_chain_jsonld(decomp, scope, cluster_id),
        "stix": stix_bundle(decomp, scope, cluster_id),
        "collateral": collateral(scope, benign) if benign is not None else None,
    }


def _toy():
    """Cluster-brinquedo: 12 atacantes furtivos (JA4 + endpoint compartilhados, /24
    dispersos) + 400 benignos no mesmo endpoint com JA4 diversos."""
    import numpy as np
    rng = np.random.default_rng(7)
    atk = [dict(session_id=f"a{i}", src_ip_first=f"10.{rng.integers(0,256)}.{rng.integers(0,256)}.{i+1}",
                dst_ip_first="10.0.0.1", dst_port_first=443, ja4="t13d_botnetX") for i in range(12)]
    ben = [dict(session_id=f"b{i}", src_ip_first=f"100.{rng.integers(64,128)}.{rng.integers(0,256)}.{rng.integers(1,255)}",
                dst_ip_first="10.0.0.1", dst_port_first=int(rng.choice([443,443,80,8080])),
                ja4=rng.choice(["jaWin","jaMac","jaAndroid","jaIOS",None])) for i in range(400)]
    return pd.DataFrame(atk), pd.DataFrame(ben)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--cluster", type=Path)
    ap.add_argument("--benign", type=Path)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    if args.demo:
        cluster, benign = _toy()
    else:
        if not args.cluster:
            ap.error("use --demo ou --cluster")
        cluster = pd.read_parquet(args.cluster)
        benign = pd.read_parquet(args.benign) if args.benign else None

    out = run(cluster, benign)
    d, sc, col = out["decomposition"], out["scope"], out["collateral"]

    print("\n" + "=" * 66)
    print("PILAR 4 — CADEIA DE EVIDÊNCIA + MITIGAÇÃO CIRÚRGICA")
    print("=" * 66)
    print(f"Ω(S) = {d['omega']:.1f}  ({d['size']} sessões)")
    print("Decomposição por sub-relação:")
    for name, a in d["activated"].items():
        print(f"  {name:32s} pares={a['pairs']:>6}  ×{a['weight']} = {a['weighted']:.1f}")
    print(f"\nESCOPO DE MITIGAÇÃO DERIVADO (discriminador mínimo): {json.dumps(sc, ensure_ascii=False)}")
    if col:
        print(f"\nDANO COLATERAL (em {col['benign_total']} sessões BENIGN):")
        print(f"  mitigação CIRÚRGICA (escopo derivado): {col['surgical_hits']} "
              f"({100*col['surgical_fpr']:.2f}%)")
        print(f"  rate-limit GLOBAL no endpoint:         {col['global_endpoint_hits']} "
              f"({100*col['global_fpr']:.2f}%)")
        red = (1 - col['surgical_fpr']/col['global_fpr']) * 100 if col['global_fpr'] else float('nan')
        print(f"  → redução de dano colateral: {red:.1f}%")
    print("\n--- CADEIA DE EVIDÊNCIA (JSON-LD) ---")
    print(json.dumps(out["evidence_jsonld"], indent=2, ensure_ascii=False)[:900])

    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "evidence.jsonld").write_text(json.dumps(out["evidence_jsonld"], indent=2, ensure_ascii=False))
        (args.out_dir / "mitigation.stix.json").write_text(json.dumps(out["stix"], indent=2, ensure_ascii=False))
        log.info("✅ evidence.jsonld + mitigation.stix.json em %s", args.out_dir)


if __name__ == "__main__":
    main()


# =====================================================================
# Derivação de escopo por ENRIQUECIMENTO (Sprint 6 / NOMS).
#
# O `derive_scope` acima escolhe o JA4 MODAL do subconjunto coordenado. Essa
# heurística falha exatamente onde importa: contra uma botnet heterogênea, cada
# stack do atacante fica menor que a cabeça da distribuição benigna, o modal do
# cluster passa a ser um fingerprint LEGÍTIMO, e o escopo derivado vira um filtro
# que bloqueia usuários e nenhum atacante (medido: 0% de cobertura do ataque,
# 40% de colateral).
#
# A causa é conceitual: frequência premia o que é comum, e o que é comum é o
# tráfego legítimo. O critério correto é ENRIQUECIMENTO — quanto um fingerprint
# está super-representado no cluster detectado em relação ao tráfego de fundo.
# É informação que o grafo já tem e que o modal descarta.
#
# Consequência desejável: quando o adversário se esconde num fingerprint benigno
# popular, o enriquecimento desse fingerprint é ~1 e ele é corretamente RECUSADO;
# o escopo cai para endpoint/rede e o arcabouço reporta honestamente que não há
# discriminador, em vez de emitir um filtro que só machuca legítimos.
# =====================================================================

def _origin_units(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (origin, fingerprint): the sessions of one client count once."""
    return df.drop_duplicates(["src_ip_first", "ja4"])


def _enrichment_inputs(cluster: pd.DataFrame, background, unit: str):
    """Fingerprint shares of the cluster, the profile, its prior and the test family."""
    units = _origin_units(cluster) if unit == "origin" else cluster
    c_freq = units["ja4"].value_counts(normalize=True)
    if isinstance(background, pd.Series):
        b_freq, n_bg = background, int(background.attrs.get("n", 1000))
    else:
        bg = _origin_units(background) if unit == "origin" else background
        b_freq, n_bg = bg["ja4"].value_counts(normalize=True), len(bg)
    # weak prior on the background: a fingerprint absent from the profile does
    # not become infinitely enriched on a single observation.
    eps = 1.0 / max(n_bg, 1)
    n_ja4 = int(units["ja4"].notna().sum())
    family = len(set(b_freq.index) | set(c_freq.index))
    return c_freq, b_freq, eps, n_ja4, family


def min_adjusted_p(cluster: pd.DataFrame, background, min_enrichment: float = 3.0,
                   unit: str = "session") -> float:
    """Smallest Bonferroni-adjusted binomial p-value among the enriched fingerprints.

    ``derive_scope_enriched(..., significance=a)`` names a fingerprint exactly when
    this value is below ``a``; ``inf`` when no fingerprint is enriched.
    """
    if not cluster["ja4"].notna().any() or not len(background):
        return float("inf")
    c_freq, b_freq, eps, n_ja4, family = _enrichment_inputs(cluster, background, unit)
    bf = b_freq.reindex(c_freq.index).fillna(0.0).to_numpy() + eps
    cf = c_freq.to_numpy()
    p = binom.sf(np.round(cf * n_ja4) - 1, n_ja4, np.minimum(bf, 1.0)) * family
    p = p[cf / bf >= min_enrichment]
    return float(p.min()) if len(p) else float("inf")


def calibrate_level(clean_clusters, background, min_enrichment: float = 3.0,
                    cap: float = 0.01, max_rate: float = 0.01, unit: str = "session") -> float:
    """Test level at which the scope names a filter in at most ``max_rate`` of clean clusters.

    The nominal level assumes each unit draws its fingerprint independently from
    the profile. Production traffic breaks that: legitimate fleets switch on
    together. The level is therefore calibrated per endpoint on attack-free
    clusters, as tau_cluster is, and never exceeds ``cap``. No label is used.
    """
    t = [min_adjusted_p(c, background, min_enrichment, unit) for c in clean_clusters]
    if not t:
        return cap
    return min(cap, float(np.percentile(t, 100 * max_rate, method="lower")))


def derive_scope_enriched(cluster: pd.DataFrame, background: pd.DataFrame,
                          min_enrichment: float = 3.0,
                          min_support: float = 0.01,
                          max_values: int = 32,
                          significance: float | None = None,
                          unit: str = "session") -> dict:
    """Escopo cujo discriminador é escolhido por enriquecimento, não por frequência.

    ``cluster``    sessões do cluster que disparou a regra.
    ``background`` PERFIL HISTÓRICO de prevalência de fingerprints — um DataFrame
                   de tráfego de referência ou uma Series ja4->prevalência. Precisa
                   vir de fora do episódio de ataque: usar a própria janela como
                   fundo não funciona, porque a campanha atravessa a janela inteira
                   e a prevalência no cluster iguala a do fundo (enriquecimento ~1
                   para tudo, medido). A suposição operacional é a que um defensor
                   real satisfaz: perfilar o tráfego normal fora de ataque. Nenhum
                   rótulo é usado em tempo de decisão.
    ``min_enrichment`` razão mínima entre a prevalência no cluster e no fundo.
    ``min_support``    fração mínima do cluster que o fingerprint deve cobrir,
                       para não catar ruído de cauda. 0.01 é o ponto de operação
                       medido: com 0.02 uma botnet de 25 stacks cai para 33% de
                       cobertura só porque cada stack fica abaixo do piso; com
                       0.01 recupera ~90% sem custo de colateral (0.00%).
    ``max_values``     teto de valores no filtro resultante (disjunção).
    ``significance``   when set, replaces the ``min_support`` floor by a one-sided
                       binomial test: a fingerprint seen c times among the n
                       sessions is kept only if P(X >= c) < significance / m for
                       X ~ Bin(n, b(f)). Bonferroni runs over m, every fingerprint
                       of the profile or of the cluster: which ones appear in the
                       cluster is itself random, so counting only those
                       undercounts the family. A fixed fraction ignores n: at window
                       scale 0.002 of the sessions is less than one, so any tail
                       fingerprint seen once passes. The test asks the same
                       question, whether f is over-represented against the
                       background, with the sample size in it. ``min_enrichment``
                       still applies as the effect size.
    ``unit``           "origin" counts each (source address, fingerprint) pair
                       once, in the cluster and in a background DataFrame, so a
                       client opening many sessions is one draw of the test; the
                       endpoint and /24 conjuncts then count origins too.
                       "session" is the count of earlier revisions.

    Retorna um escopo em que ``tlsJa4`` pode ser um CONJUNTO de fingerprints — é
    o que permite cobrir uma botnet fragmentada em vários stacks.
    """
    cluster = cluster.copy()
    cluster["endpoint"] = (cluster["dst_ip_first"].astype(str) + ":"
                           + cluster["dst_port_first"].astype(str))
    cluster["net24"] = cluster["src_ip_first"].map(_net24)
    n = len(cluster)
    scope = {}

    if cluster["ja4"].notna().any() and len(background):
        c_freq, b_freq, eps, n_ja4, family = _enrichment_inputs(cluster, background, unit)
        cut = significance / family if significance is not None else None
        picked = []
        for ja4, cf in c_freq.items():
            bf = float(b_freq.get(ja4, 0.0)) + eps
            if cut is None:
                if cf < min_support:
                    continue
            elif binom.sf(round(cf * n_ja4) - 1, n_ja4, min(bf, 1.0)) >= cut:
                continue
            if cf / bf >= min_enrichment:
                picked.append((ja4, cf, cf / bf))
            if len(picked) >= max_values:
                break
        if picked:
            scope["tlsJa4"] = {p[0] for p in picked}
            scope["_ja4_detail"] = [
                {"ja4": p[0], "cluster_share": round(p[1], 4),
                 "enrichment": round(p[2], 1)} for p in picked
            ]

    if unit == "origin":
        cluster = cluster.drop_duplicates("src_ip_first")
        n = len(cluster)
    top_ep = cluster["endpoint"].value_counts()
    if len(top_ep) and top_ep.iloc[0] / n >= 0.5:
        scope["endpoint"] = top_ep.index[0]
    top_net = cluster["net24"].value_counts()
    if len(top_net) and top_net.iloc[0] / n >= 0.5:
        scope["srcNet24"] = str(top_net.index[0]) + ".0/24"
    return scope


def matches_scope_multi(df: pd.DataFrame, scope: dict) -> pd.Series:
    """Como ``matches_scope``, mas ``tlsJa4`` pode ser um conjunto (disjunção)."""
    df = df.copy()
    df["endpoint"] = df["dst_ip_first"].astype(str) + ":" + df["dst_port_first"].astype(str)
    df["net24"] = df["src_ip_first"].map(_net24).astype(str) + ".0/24"
    m = pd.Series(True, index=df.index)
    if "tlsJa4" in scope:
        want = scope["tlsJa4"]
        want = want if isinstance(want, (set, list, tuple)) else {want}
        m &= df["ja4"].isin(list(want))
    if "endpoint" in scope:
        m &= (df["endpoint"] == scope["endpoint"])
    if "srcNet24" in scope:
        m &= (df["net24"] == scope["srcNet24"])
    return m
