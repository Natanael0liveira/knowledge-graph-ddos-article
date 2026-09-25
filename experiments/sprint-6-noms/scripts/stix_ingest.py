#!/usr/bin/env python3
"""Sprint 6 (NOMS) — do real consumers ingest the exported STIX 2.1, scope included?

stix_check.py shows the bundles are valid STIX 2.1. This script asks what two
consumers do with them, locally and with no attack traffic:

1. TAXII 2.1 transport. Security platforms receive STIX over TAXII. The OASIS
   reference server (medallion) runs on localhost with a memory backend; each
   bundle is posted to a collection and read back with the OASIS TAXII client, as
   a SIEM or SOAR would, and every object returned is compared with the one sent.
2. MISP import. The bundle goes through MISP's own STIX 2.1 importer
   (misp-stix, ExternalSTIX2toMISPParser), and the resulting event is checked for
   what a MISP-fed playbook would act on: the endpoint, the fingerprints of the
   scope, the course-of-action, and the importer's warnings.

STIX 2.1 has no JA4 property, so the exporter carries the fingerprints in a
property extension; whether a consumer keeps them is the point of step 2.

Usage:
    python stix_ingest.py --out ../results/stix_ingest.json
"""
import argparse
import json
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(HERE.parent)]
from stix_check import CHAINS, TARGET  # noqa: E402  (the bundles stix_check wrote)

API_ROOT = "kg"
NAMESPACE = uuid.UUID("7f4e3c2a-1b5d-4e6f-8a9b-0c1d2e3f4a5b")


def bundles():
    for path in CHAINS:
        out = TARGET.get(path, path.with_name(path.name.replace(".jsonld", ".stix.json")))
        yield path.name, json.loads(out.read_text())


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def taxii_roundtrip(items):
    """Post every bundle to a local TAXII 2.1 collection and read each object back.

    medallion 3.0.0 reads any object's "version" field as a timestamp
    (common.find_att), and a STIX 2.1 extension-definition carries a required
    semantic version ("1.0.0"): listing a collection that holds one, or fetching
    that object, fails with HTTP 500. Objects are therefore read back one by one,
    by id, and the failure is recorded per type.
    """
    from taxii2client.v21 import ApiRoot, Server
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    tmp = Path(tempfile.mkdtemp())
    data = {"/discovery": {"title": "local TAXII 2.1", "api_roots": [f"{base}/{API_ROOT}/"],
                           "default": f"{base}/{API_ROOT}/"},
            API_ROOT: {"information": {"title": "verdicts", "versions": ["application/taxii+json;version=2.1"],
                                       "max_content_length": 10485760},
                       "status": [],
                       "collections": [{"id": str(uuid.uuid5(NAMESPACE, name)), "title": name,
                                        "can_read": True, "can_write": True,
                                        "media_types": ["application/stix+json;version=2.1"],
                                        "objects": [], "manifest": []} for name, _ in items]}}
    (tmp / "data.json").write_text(json.dumps(data))
    (tmp / "config.json").write_text(json.dumps({
        "backend": {"module": "medallion.backends.memory_backend", "module_class": "MemoryBackend",
                    "filename": str(tmp / "data.json")},
        "users": {"kg": "kg"}, "taxii": {"max_page_size": 100}}))
    exe = Path(sys.executable).with_name("medallion")
    srv = subprocess.Popen([str(exe), "--host", "127.0.0.1", "--port", str(port), str(tmp / "config.json")],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.1)
        server = Server(f"{base}/taxii2/", user="kg", password="kg")   # TAXII 2.1 discovery
        root = ApiRoot(server.default.url, user="kg", password="kg")
        cols = {c.id: c for c in root.collections}
        rows = []
        for name, bundle in items:
            col = cols[str(uuid.uuid5(NAMESPACE, name))]
            t0 = time.perf_counter()
            status = col.add_objects(json.dumps(bundle))
            by_type = {}
            for o in bundle["objects"]:
                try:
                    got = col.get_object(o["id"])["objects"][0]
                    by_type[o["type"]] = "identical" if got == o else "differs"
                except Exception as e:                       # the server bug above
                    by_type[o["type"]] = f"server error: {str(e).split(' for url')[0]}"
            ms = (time.perf_counter() - t0) * 1000
            rows.append({"bundle": name, "objects_sent": len(bundle["objects"]),
                         "success_count": status.success_count, "failure_count": status.failure_count,
                         "by_type": by_type, "round_trip_ms": round(ms, 1)})
        types = sorted({t for r in rows for t in r["by_type"]})
        return {"server": "medallion (OASIS TAXII 2.1 reference)", "client": "taxii2-client (OASIS)",
                "bundles": rows,
                "accepted_all": all(r["failure_count"] == 0 and r["success_count"] == r["objects_sent"]
                                    for r in rows),
                "identical_by_type": {t: all(r["by_type"].get(t) == "identical" for r in rows) for t in types}}
    finally:
        srv.terminate()
        srv.wait(timeout=10)


def misp_import(items):
    """What MISP's STIX 2.1 importer keeps of each bundle."""
    import stix2
    from misp_stix_converter import ExternalSTIX2toMISPParser
    rows = []
    for name, bundle in items:
        ind = next(o for o in bundle["objects"] if o["type"] == "indicator")
        ext = next(iter(ind["extensions"].values()))
        ja4 = [v.strip().strip("'") for v in
               ind["pattern"].split(" IN (", 1)[1].rsplit(")", 1)[0].split(",")] if " IN (" in ind["pattern"] \
            else [p.split("= '", 1)[1].split("'", 1)[0] for p in ind["pattern"].split(" AND ") if ".ja4 =" in p]
        parser = ExternalSTIX2toMISPParser()
        parser.load_stix_bundle(stix2.parse(json.dumps(bundle), allow_custom=True))
        parser.parse_stix_bundle()
        event = parser.misp_event
        text = event.to_json()
        ev = json.loads(text)
        objects = [{"name": o["name"], "attributes": {a["object_relation"]: str(a["value"]) for a in o["Attribute"]}}
                   for o in ev.get("Object", [])]
        galaxies = [g["type"] for g in ev.get("Galaxy", [])]
        warnings = [w for ws in (parser.warnings or {}).values() for w in ws]
        endpoint = any(o["name"] == "network-traffic" and "dst_ip" in o["attributes"] for o in objects)
        rows.append({"bundle": name, "fingerprints_in_scope": len(ja4),
                     "fingerprints_kept": int(sum(f in text for f in ja4)),
                     "endpoint_kept": endpoint,
                     "course_of_action_kept": "stix-2.1-course-of-action" in galaxies,
                     "coordination_score_kept": str(ext.get("coordination_score")) in text,
                     "objects": objects, "galaxies": galaxies, "warnings": warnings})
    with_scope = [r for r in rows if r["fingerprints_in_scope"]]
    return {"importer": "misp-stix ExternalSTIX2toMISPParser", "bundles": rows,
            "fingerprints_in_scope": sum(r["fingerprints_in_scope"] for r in with_scope),
            "fingerprints_kept": sum(r["fingerprints_kept"] for r in with_scope),
            "endpoint_kept_where_scoped": all(r["endpoint_kept"] for r in with_scope),
            "course_of_action_kept": all(r["course_of_action_kept"] for r in rows)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=HERE.parents[1] / "results" / "stix_ingest.json")
    args = ap.parse_args()
    import importlib.metadata as md
    items = list(bundles())
    res = {"versions": {p: md.version(p) for p in ("medallion", "taxii2-client", "misp-stix", "stix2")},
           "taxii": taxii_roundtrip(items), "misp": misp_import(items)}
    args.out.write_text(json.dumps(res, indent=2))
    t, m = res["taxii"], res["misp"]
    print(f"TAXII 2.1 round trip: {len(t['bundles'])} bundles, accepted {t['accepted_all']}, "
          f"returned identical by type {t['identical_by_type']}; round trip "
          f"{min(r['round_trip_ms'] for r in t['bundles']):.0f}-{max(r['round_trip_ms'] for r in t['bundles']):.0f} ms")
    print(f"MISP import: course-of-action kept {m['course_of_action_kept']}, endpoint kept "
          f"{m['endpoint_kept_where_scoped']}, fingerprints kept {m['fingerprints_kept']}/{m['fingerprints_in_scope']}")
    for r in m["bundles"]:
        for w in r["warnings"]:
            print(f"  {r['bundle']}: {w[:120]}")
    print(f"OK: {args.out}")


if __name__ == "__main__":
    main()
