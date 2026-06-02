#!/usr/bin/env python3
"""Pilar 2 — raciocínio simbólico nativo, veredicto-como-derivação.

Avalia a regra coordinatedHTTPFlood por SOMA PONDERADA das sub-relações relatedBy_*,
em duas etapas simbólicas:

1. SWRL (par-a-par): materializa as arestas relatedBy_* a partir de sinais
   compartilhados. Aqui executadas como SPARQL CONSTRUCT (semanticamente equivalentes
   às regras de Horn em rules/relatedBy.swrl — rdflib não tem reasoner SWRL nativo,
   e essas regras não precisam de um: são CONSTRUCTs).
2. SPARQL (agregação): Ω(S) = Σ_i coordinationWeight(i) · |pares relatedBy_i em S| ≥ τ.
   Os pesos vêm da ONTOLOGIA (coordinationWeight no .owl) — nada hard-coded.

O VEREDICTO é a derivação que satisfez a regra: a regra disparada + os bindings
(quais sessões, quais sub-relações, com que peso, somando a Ω). NÃO é um score de
classificador interpretado a posteriori. Esse output alimenta o Pilar 4 (evidência+
mitigação).

Uso:
    python reason.py --demo                       # toy RDF offline
    python reason.py --data sessions.ttl --tau 5  # grafo RDF real
"""
import argparse
import logging
from pathlib import Path

from rdflib import Graph, Namespace, RDF, Literal
from rdflib.namespace import XSD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

KG = Namespace("http://security.example.org/ontology/ddos#")
ONT_OWL = Path(__file__).resolve().parents[3] / "ontology" / "ddos_ontology.owl"

# As 6 sub-relações com dado a nível de sessão → SPARQL CONSTRUCT (= regras SWRL).
CONSTRUCTS = {
    "relatedByTLSFingerprint": """
        CONSTRUCT { ?a kg:relatedByTLSFingerprint ?b }
        WHERE { ?a a kg:ApplicationSession ; kg:tlsJa4 ?j .
                ?b a kg:ApplicationSession ; kg:tlsJa4 ?j . FILTER(STR(?a) < STR(?b)) }""",
    "relatedByEndpointConvergence": """
        CONSTRUCT { ?a kg:relatedByEndpointConvergence ?b }
        WHERE { ?a a kg:ApplicationSession ; kg:targets ?e .
                ?b a kg:ApplicationSession ; kg:targets ?e . FILTER(STR(?a) < STR(?b)) }""",
    "relatedByNetworkProximity": """
        CONSTRUCT { ?a kg:relatedByNetworkProximity ?b }
        WHERE { ?a a kg:ApplicationSession ; kg:srcNet24 ?n .
                ?b a kg:ApplicationSession ; kg:srcNet24 ?n . FILTER(STR(?a) < STR(?b)) }""",
}


def load_weights(g: Graph) -> dict:
    """Pesos w_i lidos da ontologia (coordinationWeight) — não hard-coded."""
    if ONT_OWL.exists():
        g.parse(str(ONT_OWL), format="xml")
    q = """SELECT ?p ?w WHERE { ?p kg:coordinationWeight ?w }"""
    w = {str(p).split("#")[1]: float(wt) for p, wt in g.query(q, initNs={"kg": KG})}
    return w


def materialize(g: Graph) -> dict:
    """Etapa 1 (SWRL≡CONSTRUCT): instancia as arestas relatedBy_*."""
    counts = {}
    for name, q in CONSTRUCTS.items():
        edges = g.query(q, initNs={"kg": KG})
        n = 0
        for s, p, o in edges:
            g.add((s, p, o)); n += 1
        counts[name] = n
    return counts


def evaluate_rule(g: Graph, weights: dict, tau: float):
    """Etapa 2 (SPARQL): Ω(S) por endpoint-alvo (cluster = sessões no mesmo endpoint),
    soma ponderada das sub-relações internas; dispara coordinatedHTTPFlood se ≥ τ."""
    verdicts = []
    # endpoints candidatos
    eps = {e for (e,) in g.query(
        "SELECT DISTINCT ?e WHERE { ?s a kg:ApplicationSession ; kg:targets ?e }",
        initNs={"kg": KG})}
    for ep in eps:
        members = [s for (s,) in g.query(
            "SELECT ?s WHERE { ?s a kg:ApplicationSession ; kg:targets ?ep }",
            initNs={"kg": KG}, initBindings={"ep": ep})]
        if len(members) < 2:
            continue
        mset = set(members)
        contrib = {}
        for rel in ("relatedByTLSFingerprint", "relatedByEndpointConvergence",
                    "relatedByNetworkProximity"):
            P = KG[rel]
            pairs = sum(1 for a, b in g.subject_objects(P) if a in mset and b in mset)
            if pairs:
                contrib[rel] = {"pairs": pairs, "weight": weights.get(rel, 0.0),
                                "weighted": pairs * weights.get(rel, 0.0)}
        omega = sum(c["weighted"] for c in contrib.values())
        if omega >= tau:
            verdicts.append({"endpoint": str(ep), "size": len(members),
                             "omega": omega, "contrib": contrib,
                             "members": [str(m) for m in members]})
    return verdicts


def toy_graph() -> Graph:
    g = Graph(); g.bind("kg", KG)
    def sess(sid, ja4, net24, ep):
        s = KG[f"session/{sid}"]
        g.add((s, RDF.type, KG.ApplicationSession))
        g.add((s, KG.tlsJa4, Literal(ja4)))
        g.add((s, KG.srcNet24, Literal(net24)))
        g.add((s, KG.targets, KG[f"endpoint/{ep}"]))
    # 5 atacantes furtivos: MESMO JA4, /24 dispersos, MESMO endpoint :443
    for i in range(5):
        sess(f"atk{i}", "t13d_botnetX", f"10.{i}.0", "10.0.0.1_443")
    # 3 benignos no mesmo endpoint, JA4 diversos, /24 diversos
    for i, ja in enumerate(["jaWin", "jaMac", "jaIOS"]):
        sess(f"ben{i}", ja, f"100.{64+i}.7", "10.0.0.1_443")
    return g


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--data", type=Path)
    ap.add_argument("--tau", type=float, default=5.0)
    args = ap.parse_args()

    g = toy_graph() if args.demo else Graph()
    if args.data:
        g.parse(str(args.data))
    g.bind("kg", KG)

    weights = load_weights(g)
    log.info("Pesos da ontologia: %s", weights)
    counts = materialize(g)
    log.info("Arestas relatedBy_* materializadas (SWRL≡CONSTRUCT): %s", counts)
    verdicts = evaluate_rule(g, weights, args.tau)

    print("\n" + "=" * 66)
    print(f"PILAR 2 — RACIOCÍNIO SIMBÓLICO (veredicto-como-derivação, τ={args.tau})")
    print("=" * 66)
    if not verdicts:
        print("Nenhum cluster satisfez coordinatedHTTPFlood.")
    for v in verdicts:
        print(f"\n▶ REGRA DISPARADA: coordinatedHTTPFlood  @ {v['endpoint'].split('/')[-1]}")
        print(f"  Ω(S) = {v['omega']:.1f} ≥ τ={args.tau}   (|S|={v['size']})")
        print("  DERIVAÇÃO (sub-relações que satisfizeram a regra):")
        for rel, c in v["contrib"].items():
            print(f"    {rel:32s} {c['pairs']} pares × w={c['weight']} = {c['weighted']:.1f}")
        print(f"  veredicto = a derivação acima (não um score). Sessões: "
              f"{', '.join(m.split('/')[-1] for m in v['members'])}")
    print("\nNota: arestas relatedBy_* por SWRL (par-a-par); Ω≥τ por SPARQL (agregação);")
    print("pesos lidos de coordinationWeight na ontologia. Alimenta o Pilar 4.")


if __name__ == "__main__":
    main()
