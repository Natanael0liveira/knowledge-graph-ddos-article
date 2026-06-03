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

KG = Namespace("http://security.example.org/ontology/ddos#")


def _add_session_triples(g: Graph, row) -> None:
    """Add the triples for a single session row to graph ``g``.

    Single source of truth for the session→RDF mapping, shared by the
    in-memory builder (``build_graph``) and the streaming N-Triples
    exporter (``export_ntriples_streaming``).
    """
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


def build_graph(
    sessions: pd.DataFrame, clusters: pd.DataFrame, ontology_path: Path
) -> Graph:
    """Build a full in-memory RDF graph from sessions + clusters.

    Holds every triple in RAM — fine for the chunked HTTP path on small
    datasets, but for large ones (>~400k sessions) it thrashes swap. Prefer
    ``export_ntriples_streaming`` + native ``tdb2.tdbloader`` (see
    ``make load-kg-bulk``).
    """
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
    for _, row in sessions.iterrows():
        _add_session_triples(g, row)

    log.info("Graph has %d triples", len(g))
    return g


def export_ntriples_streaming(
    sessions: pd.DataFrame,
    ontology_path: Path,
    out_path: Path,
    batch_size: int = 20_000,
) -> int:
    """Stream sessions to an N-Triples file in bounded memory.

    Builds at most ``batch_size`` sessions worth of triples at a time, serializes
    that batch to N-Triples, appends it, then drops it. Memory stays flat
    regardless of dataset size — the fix for the swap-thrashing seen when
    materializing the whole graph in rdflib. Output (.nt) is fed straight to
    ``tdb2.tdbloader``. Concatenated N-Triples needs no prefixes, so batches
    append cleanly.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    log.info("Streaming %d sessions to %s (batch=%d) ...",
             len(sessions), out_path, batch_size)

    with open(out_path, "w", encoding="utf-8") as fh:
        # Ontology first, as N-Triples.
        if ontology_path and ontology_path.exists():
            og = Graph()
            try:
                og.parse(str(ontology_path),
                         format="xml" if ontology_path.suffix in (".owl", ".rdf") else "turtle")
                fh.write(og.serialize(format="nt"))
                total += len(og)
                log.info("Wrote ontology (%d triples)", len(og))
            except Exception as e:
                log.warning("Could not parse ontology: %s. Continuing.", e)

        batch = Graph()
        n_in_batch = 0
        for i, (_, row) in enumerate(sessions.iterrows(), 1):
            _add_session_triples(batch, row)
            n_in_batch += 1
            if n_in_batch >= batch_size:
                fh.write(batch.serialize(format="nt"))
                total += len(batch)
                batch = Graph()
                n_in_batch = 0
                log.info("  ... %d/%d sessions (%d triples written)",
                         i, len(sessions), total)
        if n_in_batch:
            fh.write(batch.serialize(format="nt"))
            total += len(batch)

    log.info("Streamed %d triples to %s", total, out_path)
    return total


def upload_to_fuseki(
    graph: Graph,
    fuseki_url: str,
    dataset: str,
    admin_password: str = "kgddos",
    chunk_triples: int = 50_000,
):
    """POST graph to Fuseki in chunks (single huge POST times out for >1M triples).

    Each chunk is a fresh rdflib Graph with the same namespace bindings, holding
    up to ``chunk_triples`` triples. We use HTTP POST (additive) on the gsp-rw
    endpoint so successive chunks accumulate instead of replacing.
    """
    endpoint = f"{fuseki_url}/{dataset}/data"
    total = len(graph)
    log.info("Uploading %d triples to %s in chunks of %d ...", total, endpoint, chunk_triples)

    chunk = Graph()
    for prefix, ns in graph.namespaces():
        chunk.bind(prefix, ns)

    sent = 0
    chunk_idx = 0

    def _flush_chunk() -> None:
        nonlocal chunk, chunk_idx, sent
        if len(chunk) == 0:
            return
        data = chunk.serialize(format="turtle")
        try:
            r = requests.post(
                endpoint,
                data=data,
                headers={"Content-Type": "text/turtle"},
                auth=("admin", admin_password),
                timeout=600,
            )
            r.raise_for_status()
        except requests.exceptions.ConnectionError:
            log.error("Cannot reach Fuseki at %s. Did you run `make fuseki-up`?", fuseki_url)
            sys.exit(2)
        except requests.exceptions.HTTPError as e:
            log.error("Fuseki HTTP error on chunk %d: %s", chunk_idx, e)
            log.error("Response: %s", r.text[:500])
            sys.exit(3)
        sent += len(chunk)
        log.info("  chunk %d ok (%d/%d triples, %.1f%%)",
                 chunk_idx, sent, total, 100.0 * sent / total)
        chunk_idx += 1
        # reset chunk
        chunk = Graph()
        for prefix, ns in graph.namespaces():
            chunk.bind(prefix, ns)

    for triple in graph:
        chunk.add(triple)
        if len(chunk) >= chunk_triples:
            _flush_chunk()
    _flush_chunk()
    log.info("Upload OK — %d triples in %d chunks", sent, chunk_idx)


def ensure_dataset(fuseki_url: str, dataset: str, admin_password: str = "kgddos"):
    """Check that dataset exists in Fuseki. Pre-created via assembler config."""
    check = requests.get(f"{fuseki_url}/$/datasets", auth=("admin", admin_password))
    if check.status_code == 200 and dataset in check.text:
        log.info("Dataset %s already exists in Fuseki", dataset)
        return
    log.error(
        "Dataset %s not found in Fuseki. Pre-create via assembler at "
        "$DATA_ROOT/kg/fuseki-tdb2/configuration/<dataset>.ttl and restart.",
        dataset,
    )
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", required=True, type=Path)
    ap.add_argument("--clusters", required=True, type=Path)
    ap.add_argument("--ontology", type=Path, default=None)
    ap.add_argument("--fuseki-url", default="http://localhost:3030")
    ap.add_argument("--dataset", default="cic-ddos-2019")
    ap.add_argument("--export-ttl", type=Path, default=None)
    ap.add_argument(
        "--reuse-ttl", action="store_true",
        help="Skip rebuild — read graph from --export-ttl directly",
    )
    ap.add_argument(
        "--export-only", action="store_true",
        help="Build + export TTL and stop (no HTTP upload). For native "
             "tdb2.tdbloader bulk loading — see `make load-kg-bulk`.",
    )
    ap.add_argument(
        "--stream", action="store_true",
        help="Stream sessions to an N-Triples file in bounded memory "
             "(no full in-memory graph). Implies --export-only. Writes to "
             "--export-ttl. The fix for swap-thrashing on large datasets.",
    )
    ap.add_argument(
        "--chunk", type=int, default=200_000,
        help="Triples per POST chunk (default: 200000)",
    )
    args = ap.parse_args()

    # Streaming path: bounded-memory N-Triples export, no in-memory graph, no upload.
    if args.stream:
        if not args.export_ttl:
            log.error("--stream requires --export-ttl (output .nt path)")
            sys.exit(2)
        sessions = pd.read_parquet(args.sessions)
        log.info("Loaded %d sessions", len(sessions))
        n = export_ntriples_streaming(sessions, args.ontology, args.export_ttl)
        log.info("✅ stream done: %d triples in %s. Load with `tdb2.tdbloader`.",
                 n, args.export_ttl)
        return

    if args.reuse_ttl and args.export_ttl and args.export_ttl.exists():
        log.info("Reusing existing TTL at %s (skip rebuild)", args.export_ttl)
        g = Graph()
        g.bind("kg", KG)
        g.bind("xsd", XSD)
        g.parse(str(args.export_ttl), format="turtle")
        log.info("Loaded %d triples from TTL", len(g))
    else:
        sessions = pd.read_parquet(args.sessions)
        clusters = pd.read_csv(args.clusters)
        log.info("Loaded %d sessions and %d clusters", len(sessions), len(clusters))
        g = build_graph(sessions, clusters, args.ontology)
        if args.export_ttl:
            args.export_ttl.parent.mkdir(parents=True, exist_ok=True)
            g.serialize(destination=str(args.export_ttl), format="turtle")
            log.info("Exported %s", args.export_ttl)

    if args.export_only:
        log.info("✅ export-only: TTL pronto em %s (sem upload HTTP). "
                 "Use `tdb2.tdbloader` para a carga.", args.export_ttl)
        return

    ensure_dataset(args.fuseki_url, args.dataset)
    upload_to_fuseki(g, args.fuseki_url, args.dataset, chunk_triples=args.chunk)

    log.info("✅ KG loaded. Query at %s/%s/sparql", args.fuseki_url, args.dataset)
    log.info("   Example: SELECT (COUNT(*) AS ?n) WHERE { ?s a kg:ApplicationSession }")


if __name__ == "__main__":
    main()
