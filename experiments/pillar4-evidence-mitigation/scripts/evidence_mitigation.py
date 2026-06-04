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
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ONT = "http://security.example.org/ontology/ddos#"
# Pesos da família relatedTo (espelham coordinationWeight no .owl)
WEIGHTS = {
    "relatedByTLSFingerprint": 1.0,
    "relatedByReusedIdentity": 1.0,
    "relatedByTemporalPattern": 0.9,
    "relatedByPayloadSignature": 0.6,
    "relatedByEndpointConvergence": 0.6,
    "relatedByNetworkProximity": 0.3,
}


def _pairs(n):
    return n * (n - 1) // 2


def _net24(ip):
    return str(ip).rsplit(".", 1)[0]


def decompose_omega(cluster: pd.DataFrame) -> dict:
    """Ω(S) decomposto por sub-relação: pares ligados × peso. Só as sub-relações
    com dado disponível a nível de sessão (TLS/JA4, endpoint, rede)."""
    cluster = cluster.copy()
    cluster["endpoint"] = cluster["dst_ip_first"].astype(str) + ":" + cluster["dst_port_first"].astype(str)
    cluster["net24"] = cluster["src_ip_first"].map(_net24)

    contrib = {}
    # TLSFingerprint: pares que compartilham JA4 (não-nulo)
    ja4 = cluster["ja4"].dropna()
    contrib["relatedByTLSFingerprint"] = int(ja4.value_counts().map(_pairs).sum())
    # EndpointConvergence: pares no mesmo endpoint
    contrib["relatedByEndpointConvergence"] = int(cluster["endpoint"].value_counts().map(_pairs).sum())
    # NetworkProximity: pares no mesmo /24
    contrib["relatedByNetworkProximity"] = int(cluster["net24"].value_counts().map(_pairs).sum())

    activated = {k: {"pairs": v, "weight": WEIGHTS[k], "weighted": WEIGHTS[k] * v}
                 for k, v in contrib.items() if v > 0}
    omega = sum(a["weighted"] for a in activated.values())
    return {"omega": omega, "activated": activated, "size": len(cluster)}


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


def stix_bundle(decomp: dict, scope: dict, cluster_id: str) -> dict:
    """STIX 2.1 (representativo): Indicator (padrão do escopo) + Course-of-Action."""
    pat = []
    if "tlsJa4" in scope:
        pat.append(f"[x-tls:ja4 = '{scope['tlsJa4']}']")
    if "endpoint" in scope:
        ip, _, port = scope["endpoint"].rpartition(":")
        pat.append(f"[network-traffic:dst_ref.value = '{ip}' AND network-traffic:dst_port = {port}]")
    if "srcNet24" in scope:
        pat.append(f"[ipv4-addr:value ISSUBSET '{scope['srcNet24']}']")
    ind_id = f"indicator--coord-{cluster_id}"
    coa_id = f"course-of-action--coord-{cluster_id}"
    return {
        "type": "bundle", "id": f"bundle--coord-{cluster_id}",
        "objects": [
            {"type": "indicator", "id": ind_id, "spec_version": "2.1",
             "name": f"Coordinated HTTP Flood (cluster {cluster_id})",
             "indicator_types": ["malicious-activity"],
             "pattern_type": "stix", "pattern": " AND ".join(pat) or "[network-traffic:protocols[*] = 'http']",
             "description": f"Ω(S)={decomp['omega']:.1f}, {decomp['size']} sessões; "
                            f"sub-relações: {', '.join(decomp['activated'])}"},
            {"type": "course-of-action", "id": coa_id, "spec_version": "2.1",
             "name": "Mitigação cirúrgica de escopo derivado",
             "description": "Filtrar/desafiar apenas o tráfego que casa com o discriminador "
                            f"do cluster: {json.dumps(scope, ensure_ascii=False)}"},
            {"type": "relationship", "id": f"relationship--coord-{cluster_id}",
             "spec_version": "2.1", "relationship_type": "mitigates",
             "source_ref": coa_id, "target_ref": ind_id},
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
