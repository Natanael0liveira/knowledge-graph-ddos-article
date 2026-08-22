#!/usr/bin/env python3
"""Sprint 6 (NOMS) — latency/throughput of the session-centric KG pipeline.

The paper claims a per-insertion cost of O(|S_W| * c) and relies on the sliding
window W to keep the graph bounded, but reports no measurement. This benchmark
fills that gap by timing the two layers separately, because they run at
different rates and have different complexity:

  Layer 1 - ADMISSION (per request, hot path).  Admitting a new session into a
      window that already holds |S_W| sessions: resolve the session, then
      instantiate relatedBy_* edges against the active window using the
      inverted indices described in the paper (JA4 bucket, endpoint bucket,
      /24 bucket). Cost per candidate pair is O(1); the number of candidates
      is what grows.

  Layer 2 - SYMBOLIC EVALUATION (per window, audit path).  Materialising the
      relatedBy_* edges as RDF via SPARQL CONSTRUCT (equivalent to the SWRL
      Horn rules in pillar2-symbolic-reasoning/rules/relatedBy.swrl) and then
      running the weighted Omega(S) aggregation that fires the rule.

No dataset is required: latency depends on |S_W| and on the coordination
structure of the window, not on the traffic being real. The session mix is
parameterised and reported alongside the timings so the numbers are
interpretable.

Usage:
    python bench_latency.py --sizes 100 250 500 1000 2500 5000 10000 \\
        --repeats 5 --out ../results
"""
import argparse
import json
import logging
import random
import time
from collections import defaultdict
from pathlib import Path
from statistics import median

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Weights as declared in the ontology (coordinationWeight).
WEIGHTS = {
    "relatedByTLSFingerprint": 1.0,
    "relatedByEndpointConvergence": 0.6,
    "relatedByNetworkProximity": 0.3,
}


# --------------------------------------------------------------------------- mix
def make_window(n, coord_frac, n_endpoints, ja4_pool, seed):
    """Build a synthetic active window in the realistic same-service regime.

    A fraction ``coord_frac`` of sessions are attackers sharing ONE botnet JA4
    and converging on the attacked endpoint, dispersed across /24s. The rest are
    benign: JA4 drawn from a pool of ``ja4_pool`` fingerprints, spread over
    ``n_endpoints`` endpoints (the attacked one included, so benign traffic
    shares it), and dispersed /24s.
    """
    rng = random.Random(seed)
    n_attack = int(n * coord_frac)
    sessions = []
    for i in range(n):
        attacker = i < n_attack
        if attacker:
            ja4 = "t13d_botnet"
            endpoint = "10.0.0.1:443"
        else:
            ja4 = f"t13d_benign{rng.randrange(ja4_pool)}"
            endpoint = ("10.0.0.1:443" if rng.random() < 0.5
                        else f"10.0.0.{rng.randrange(2, 2 + n_endpoints)}:443")
        sessions.append({
            "sid": f"s{i}",
            "ja4": ja4,
            "endpoint": endpoint,
            "net24": f"{rng.randrange(1, 224)}.{rng.randrange(256)}.{rng.randrange(256)}",
            "attacker": attacker,
        })
    rng.shuffle(sessions)
    return sessions


# ------------------------------------------------------------------- layer 1
class WindowIndex:
    """Inverted indices over the active window, as described in Section III-C."""

    def __init__(self):
        self.by_ja4 = defaultdict(list)
        self.by_endpoint = defaultdict(list)
        self.by_net24 = defaultdict(list)
        self.n = 0

    def admit(self, s):
        """Instantiate relatedBy_* edges for one new session. Returns edge count."""
        edges = 0
        for peer in self.by_ja4[s["ja4"]]:
            edges += 1                      # relatedByTLSFingerprint
        for peer in self.by_endpoint[s["endpoint"]]:
            edges += 1                      # relatedByEndpointConvergence
        for peer in self.by_net24[s["net24"]]:
            edges += 1                      # relatedByNetworkProximity
        self.by_ja4[s["ja4"]].append(s["sid"])
        self.by_endpoint[s["endpoint"]].append(s["sid"])
        self.by_net24[s["net24"]].append(s["sid"])
        self.n += 1
        return edges


def bench_admission(sessions, n_probe, seed):
    """Fill the window, then time the admission of ``n_probe`` further sessions."""
    idx = WindowIndex()
    for s in sessions:
        idx.admit(s)
    probes = make_window(n_probe, 0.5, 8, 2000, seed + 7919)
    lat_us, edges = [], []
    for s in probes:
        t0 = time.perf_counter()
        e = idx.admit(s)
        lat_us.append((time.perf_counter() - t0) * 1e6)
        edges.append(e)
    return {
        "admission_p50_us": median(lat_us),
        "admission_p95_us": sorted(lat_us)[int(0.95 * len(lat_us)) - 1],
        "admission_mean_edges": sum(edges) / len(edges),
    }


# ------------------------------------------------------------------- layer 2
def bench_symbolic(sessions, tau, pair_cap):
    """Time RDF materialisation (SWRL-equivalent CONSTRUCTs) + Omega aggregation.

    Returns None when the window would exceed ``pair_cap`` matched pairs, so the
    sweep degrades gracefully instead of exhausting memory; the cap itself is
    reported, since the quadratic term is a finding rather than an accident.
    """
    from rdflib import Graph, Literal, Namespace, RDF

    # cheap a-priori estimate of the matched-pair count
    est = 0
    for key in ("ja4", "endpoint", "net24"):
        buckets = defaultdict(int)
        for s in sessions:
            buckets[s[key]] += 1
        est += sum(b * (b - 1) // 2 for b in buckets.values())
    if est > pair_cap:
        return {"skipped": True, "estimated_pairs": est}

    KG = Namespace("http://security.example.org/ontology/ddos#")
    g = Graph()
    g.bind("kg", KG)

    t0 = time.perf_counter()
    for s in sessions:
        node = KG[f"session/{s['sid']}"]
        g.add((node, RDF.type, KG.ApplicationSession))
        g.add((node, KG.tlsJa4, Literal(s["ja4"])))
        g.add((node, KG.srcNet24, Literal(s["net24"])))
        g.add((node, KG.targets, KG[f"endpoint/{s['endpoint'].replace(':', '_')}"]))
    t_build = time.perf_counter() - t0

    constructs = {
        "relatedByTLSFingerprint": """
            CONSTRUCT { ?a kg:relatedByTLSFingerprint ?b }
            WHERE { ?a a kg:ApplicationSession ; kg:tlsJa4 ?j .
                    ?b a kg:ApplicationSession ; kg:tlsJa4 ?j .
                    FILTER(STR(?a) < STR(?b)) }""",
        "relatedByEndpointConvergence": """
            CONSTRUCT { ?a kg:relatedByEndpointConvergence ?b }
            WHERE { ?a a kg:ApplicationSession ; kg:targets ?e .
                    ?b a kg:ApplicationSession ; kg:targets ?e .
                    FILTER(STR(?a) < STR(?b)) }""",
        "relatedByNetworkProximity": """
            CONSTRUCT { ?a kg:relatedByNetworkProximity ?b }
            WHERE { ?a a kg:ApplicationSession ; kg:srcNet24 ?n .
                    ?b a kg:ApplicationSession ; kg:srcNet24 ?n .
                    FILTER(STR(?a) < STR(?b)) }""",
    }
    t0 = time.perf_counter()
    n_edges = 0
    for q in constructs.values():
        for triple in g.query(q, initNs={"kg": KG}):
            g.add(triple)
            n_edges += 1
    t_materialise = time.perf_counter() - t0

    # Omega aggregation per candidate endpoint, weights from the ontology.
    t0 = time.perf_counter()
    endpoints = {e for (e,) in g.query(
        "SELECT DISTINCT ?e WHERE { ?s a kg:ApplicationSession ; kg:targets ?e }",
        initNs={"kg": KG})}
    n_fired = 0
    for ep in endpoints:
        members = {s for (s,) in g.query(
            "SELECT ?s WHERE { ?s a kg:ApplicationSession ; kg:targets ?ep }",
            initNs={"kg": KG}, initBindings={"ep": ep})}
        if len(members) < 2:
            continue
        omega = 0.0
        for rel, w in WEIGHTS.items():
            pairs = sum(1 for a, b in g.subject_objects(KG[rel])
                        if a in members and b in members)
            omega += pairs * w
        if omega >= tau:
            n_fired += 1
    t_omega = time.perf_counter() - t0

    return {
        "skipped": False,
        "build_s": t_build,
        "materialise_s": t_materialise,
        "omega_s": t_omega,
        "total_s": t_build + t_materialise + t_omega,
        "edges": n_edges,
        "triples": len(g),
        "rules_fired": n_fired,
    }


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sizes", type=int, nargs="+",
                    default=[100, 250, 500, 1000, 2500, 5000, 10000])
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--coord-frac", type=float, default=0.30,
                    help="fraction of the window that is a coordinated campaign")
    ap.add_argument("--endpoints", type=int, default=8)
    ap.add_argument("--ja4-pool", type=int, default=2000,
                    help="distinct benign JA4 fingerprints")
    ap.add_argument("--probes", type=int, default=200,
                    help="sessions admitted per repeat when timing layer 1")
    ap.add_argument("--tau", type=float, default=5.0)
    ap.add_argument("--pair-cap", type=int, default=3_000_000,
                    help="skip the symbolic layer above this matched-pair estimate")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = []
    for n in args.sizes:
        for rep in range(args.repeats):
            seed = 1000 * rep + n
            win = make_window(n, args.coord_frac, args.endpoints, args.ja4_pool, seed)
            row = {"n_sessions": n, "repeat": rep,
                   "coord_frac": args.coord_frac, "ja4_pool": args.ja4_pool}
            row.update(bench_admission(win, args.probes, seed))
            sym = bench_symbolic(win, args.tau, args.pair_cap)
            row.update({f"sym_{k}": v for k, v in sym.items()})
            rows.append(row)
            log.info("n=%-6d rep=%d  admission p50=%.1f us (%.0f edges)  symbolic=%s",
                     n, rep, row["admission_p50_us"], row["admission_mean_edges"],
                     "skipped" if sym.get("skipped") else f"{sym['total_s']:.2f} s")

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(args.out / "latency_raw.csv", index=False)

    summary = {}
    for n, sub in df.groupby("n_sessions"):
        s = {
            "admission_p50_us": float(sub["admission_p50_us"].median()),
            "admission_p95_us": float(sub["admission_p95_us"].median()),
            "admission_mean_edges": float(sub["admission_mean_edges"].mean()),
        }
        done = sub[sub["sym_skipped"] == False]  # noqa: E712
        if len(done):
            s.update({
                "symbolic_total_s": float(done["sym_total_s"].median()),
                "symbolic_materialise_s": float(done["sym_materialise_s"].median()),
                "symbolic_omega_s": float(done["sym_omega_s"].median()),
                "symbolic_edges": float(done["sym_edges"].median()),
            })
        else:
            s["symbolic_skipped_estimated_pairs"] = float(
                sub["sym_estimated_pairs"].median())
        summary[str(n)] = s

    (args.out / "latency_summary.json").write_text(json.dumps(
        {"config": vars(args) | {"out": str(args.out)}, "by_window_size": summary},
        indent=2, default=str))

    print("\n" + "=" * 78)
    print("LATENCY — session-centric KG pipeline")
    print("=" * 78)
    print(f"{'|S_W|':>7} {'admit p50':>11} {'admit p95':>11} {'edges/adm':>10} "
          f"{'symbolic':>11} {'RDF edges':>11}")
    print("-" * 78)
    for n in args.sizes:
        s = summary[str(n)]
        sym = (f"{s['symbolic_total_s']:.2f} s" if "symbolic_total_s" in s
               else f"skip>{s['symbolic_skipped_estimated_pairs']:.0f}p")
        edg = (f"{s['symbolic_edges']:.0f}" if "symbolic_edges" in s else "—")
        print(f"{n:>7} {s['admission_p50_us']:>9.1f}us {s['admission_p95_us']:>9.1f}us "
              f"{s['admission_mean_edges']:>10.0f} {sym:>11} {edg:>11}")
    print(f"\nOK: {args.out}/latency_summary.json + latency_raw.csv")


if __name__ == "__main__":
    main()
