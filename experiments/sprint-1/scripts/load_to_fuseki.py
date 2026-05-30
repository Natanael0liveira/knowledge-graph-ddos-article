#!/usr/bin/env python3
"""Load sessions + clusters as RDF triples into Apache Jena Fuseki.

Each session becomes a kg:ApplicationSession instance with primary relations
(hasIdentity, targets, exhibitsBehavior) populated. Cross-session sub-relations
(relatedBy_*) are NOT populated here — that's the job of the runtime pipeline
during rule evaluation.

Output: triples in Fuseki dataset + optional Turtle export.

Usage:
    python load_to_fuseki.py --sessions sessions.parquet --clusters clusters.csv \\
                              --ontology ../../ontology/ddos_ontology.owl \\
                              --fuseki-url http://localhost:3030 \\
                              --dataset cic-ddos-2019 \\
                              --export-ttl /path/to/snapshot.ttl
"""
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import requests
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import XSD

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

KG = Namespace("https://kg-ddos.example/ontology#")


def build_graph(
    sessions: pd.DataFrame, clusters: pd.DataFrame, ontology_path: Path
) -> Graph:
    """Build RDF graph from sessions + clusters."""
    g = Graph()
    g.bind("kg", KG)
    g.bind("xsd", XSD)

    # Try to load the ontology, but don't fail if it's missing
    if ontology_path and ontology_path.exists():
        try:
            g.parse(str(ontology_path), format="xml" if ontology_path.suffix in (".owl", ".rdf") else "turtle")
            log.info("Loaded ontology from %s", ontology_path)
        except Exception as e:
            log.warning("Could not parse ontology: %s. Continuing.", e)

    log.info("Building triples for %d sessions ...", len(sessions))

    # Session instances
    for _, row in sessions.iterrows():
        sid = str(row["session_id"])
        s = URIRef(KG + f"session/{sid}")
        g.add((s, RDF.type, KG.ApplicationSession))
        g.add((s, KG.sessionId, Literal(sid)))

        # Endpoint
        ep_str = f"{row.get('dst_ip_first', row.get('dst_ip', ''))}:{row.get('dst_port_first', row.get('dst_port', ''))}"
        ep = URIRef(KG + f"endpoint/{ep_str.replace(':', '_')}")
        g.add((ep, RDF.type, KG.Endpoint))
        g.add((ep, KG.path, Literal(ep_str)))
        g.add((s, KG.targets, ep))

        # Identity (composed)
        identity_uri = URIRef(KG + f"identity/{sid}")
        g.add((identity_uri, RDF.type, KG.Identity))
        if pd.notna(row.get("ja4")):
            g.add((identity_uri, KG.tlsJa4, Literal(row["ja4"])))
        if pd.notna(row.get("src_ip_first", row.get("src_ip"))):
            src_ip = row.get("src_ip_first", row.get("src_ip"))
            g.add((identity_uri, KG.srcIp, Literal(src_ip)))
        g.add((s, KG.hasIdentity, identity_uri))

        # Behavior (placeholder; full classification by rule engine)
        beh = URIRef(KG + f"behavior/{sid}")
        g.add((beh, RDF.type, KG.Behavior))
        if pd.notna(row.get("duration_s")):
            g.add((beh, KG.durationSeconds,
                   Literal(float(row["duration_s"]), datatype=XSD.float)))
        if pd.notna(row.get("n_requests")):
            g.add((beh, KG.requestCount,
                   Literal(int(row["n_requests"]), datatype=XSD.integer)))
        g.add((s, KG.exhibitsBehavior, beh))

        # Cluster (from ground truth)
        if pd.notna(row.get("cluster_id")):
            cluster_uri = URIRef(KG + f"cluster/{row['cluster_id']}")
            g.add((s, KG.belongsToCluster, cluster_uri))

        # Label (ground truth)
        label_col = "label_first" if "label_first" in row else "label"
        if label_col in row and pd.notna(row[label_col]):
            g.add((s, KG.groundTruthLabel, Literal(str(row[label_col]))))

    log.info("Graph has %d triples", len(g))
    return g


def upload_to_fuseki(graph: Graph, fuseki_url: str, dataset: str):
    """POST graph to Fuseki dataset endpoint."""
    endpoint = f"{fuseki_url}/{dataset}/data"
    log.info("Uploading %d triples to %s ...", len(graph), endpoint)
    data = graph.serialize(format="turtle")
    try:
        r = requests.post(
            endpoint,
            data=data,
            headers={"Content-Type": "text/turtle"},
            timeout=300,
        )
        r.raise_for_status()
        log.info("Upload OK (%d bytes)", len(data))
    except requests.exceptions.ConnectionError:
        log.error("Cannot reach Fuseki at %s. Did you run `make fuseki-up`?", fuseki_url)
        sys.exit(2)
    except requests.exceptions.HTTPError as e:
        log.error("Fuseki HTTP error: %s", e)
        log.error("Response: %s", r.text[:500])
        sys.exit(3)


def ensure_dataset(fuseki_url: str, dataset: str, admin_password: str = "kgddos"):
    """Create dataset in Fuseki if it doesn't exist."""
    # Check if exists
    check = requests.get(f"{fuseki_url}/$/datasets", auth=("admin", admin_password))
    if check.status_code == 200 and dataset in check.text:
        log.info("Dataset %s already exists in Fuseki", dataset)
        return

    log.info("Creating Fuseki dataset %s ...", dataset)
    r = requests.post(
        f"{fuseki_url}/$/datasets",
        data={"dbName": dataset, "dbType": "tdb2"},
        auth=("admin", admin_password),
    )
    if r.status_code in (200, 201):
        log.info("Dataset created OK")
    else:
        log.warning("Could not create dataset (%d). Continuing — Fuseki may already have it via config.", r.status_code)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--clusters", required=True, type=Path)
    ap.add_argument("--ontology", type=Path, default=None)
    ap.add_argument("--fuseki-url", default="http://localhost:3030")
    ap.add_argument("--dataset", default="cic-ddos-2019")
    ap.add_argument("--export-ttl", type=Path, default=None)
    args = ap.parse_args()

    sessions = pd.read_parquet(args.sessions)
    clusters = pd.read_csv(args.clusters)
    log.info("Loaded %d sessions and %d clusters", len(sessions), len(clusters))

    g = build_graph(sessions, clusters, args.ontology)

    if args.export_ttl:
        args.export_ttl.parent.mkdir(parents=True, exist_ok=True)
        g.serialize(destination=str(args.export_ttl), format="turtle")
        log.info("Exported %s", args.export_ttl)

    ensure_dataset(args.fuseki_url, args.dataset)
    upload_to_fuseki(g, args.fuseki_url, args.dataset)

    log.info("✅ KG loaded. Query at %s/%s/sparql", args.fuseki_url, args.dataset)
    log.info("   Example: SELECT (COUNT(*) AS ?n) WHERE { ?s a kg:ApplicationSession }")


if __name__ == "__main__":
    main()
