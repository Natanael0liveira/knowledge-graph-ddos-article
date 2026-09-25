#!/usr/bin/env python3
"""Sprint 6 (NOMS) — compile the rule's count query from the ontology.

The equality-based relatedBy sub-properties partition a window's sessions into
classes, so Omega(S) and the enrichment scope need only class sizes (Section III-E).
This script reads, from ontology/ddos_ontology.owl, which sub-properties are
equalities (kg:classKey), what each one equates, its coordinationWeight, and the
unit classes are counted in (kg:countUnit on relatedTo), and emits the SQL a log
store runs to produce those counts. The only hand-written input is a binding that
maps each ontology property to a column expression of the log table.

    omega    per (window, endpoint): distinct origins and Omega(S), S being every
             session to the endpoint (condition ii);
    classes  per (window, endpoint, class value) of each equality sub-relation:
             distinct origins, the counts the enrichment scope reads.

Sub-properties without a class key (near-variant JA4, temporal, payload, identity
overlap) are not equivalences; the plan lists them as needing pairwise evaluation.

``--check`` verifies the compiled query without external data: on generated
sessions it compares Omega from DuckDB with decompose_omega(unit="origin"), then
adds a sub-property to a copy of the ontology and checks that the recompiled query
picks it up with no change to any code.

Usage:
    python compile_counts.py --binding ../bindings/clickhouse_azion.json      # print SQL
    python compile_counts.py --check --out ../results/compile_check.json
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "common"), str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from kg_ontology import KG, ONTOLOGY, count_unit, relations  # noqa: E402


def plan(ontology=ONTOLOGY, partition="targets"):
    """What the ontology says the count query must compute."""
    rels = relations(Path(ontology))
    unit = count_unit(Path(ontology))
    if unit is None:
        raise SystemExit(f"{ontology}: relatedTo carries no kg:countUnit")
    eq = {n: r for n, r in rels.items() if r["class_key"]}
    part = [n for n, r in eq.items() if r["class_key"] == partition]
    if len(part) != 1:
        raise SystemExit(f"{ontology}: expected one sub-property keyed on kg:{partition}, found {part}")
    return {"unit": unit, "partition": {"relation": part[0], "key": partition,
                                        "weight": eq[part[0]]["weight"]},
            "classes": [{"relation": n, "key": r["class_key"], "weight": r["weight"]}
                        for n, r in eq.items() if n != part[0]],
            "pairwise": sorted(n for n, r in rels.items() if not r["class_key"])}


def compile_sql(binding, ontology=ONTOLOGY, partition="targets"):
    """The two queries, as SQL over the binding's table."""
    p = plan(ontology, partition)
    cols = binding["columns"]
    missing = [k for k in [p["unit"], partition] + [c["key"] for c in p["classes"]] if k not in cols]
    if missing:
        raise SystemExit(f"binding lacks a column for kg:{', kg:'.join(missing)}")
    base = (f"SELECT {binding['window']} AS w, {cols[partition]} AS e, {cols[p['unit']]} AS o"
            + "".join(f", {cols[c['key']]} AS k{i}" for i, c in enumerate(p["classes"]))
            + f" FROM {binding['table']}")
    if binding.get("where"):
        base += f" WHERE {binding['where']}"
    # CTE and column names never coincide: some ClickHouse analyzers resolve
    # "n.n" ambiguously when a CTE and one of its columns share a name.
    ctes = [f"s AS ({base})", "tot AS (SELECT w, e, COUNT(DISTINCT o) AS cnt FROM s GROUP BY w, e)"]
    terms = [f"{p['partition']['weight']} * tot.cnt * (tot.cnt - 1) / 2"]
    joins, classes, pairs = "", {}, []
    for i, c in enumerate(p["classes"]):
        cnt = f"SELECT w, e, k{i} AS v, COUNT(DISTINCT o) AS cnt FROM s WHERE k{i} IS NOT NULL GROUP BY w, e, k{i}"
        ctes += [f"c{i} AS ({cnt})",
                 f"p{i} AS (SELECT w, e, SUM(cnt * (cnt - 1) / 2) AS pairs FROM c{i} GROUP BY w, e)"]
        joins += f" LEFT JOIN p{i} ON p{i}.w = tot.w AND p{i}.e = tot.e"
        terms.append(f"{c['weight']} * COALESCE(p{i}.pairs, 0)")
        pairs.append(f"COALESCE(p{i}.pairs, 0) AS pairs_{c['relation']}")
        classes[c["relation"]] = (f"WITH s AS ({base})\nSELECT w AS win, e AS endpoint, k{i} AS value, "
                                  f"COUNT(DISTINCT o) AS origins FROM s WHERE k{i} IS NOT NULL "
                                  f"GROUP BY w, e, k{i}")
    # "win", not "window": WINDOW is reserved in ClickHouse and DuckDB.
    omega = ("WITH " + ",\n     ".join(ctes)
             + "\nSELECT tot.w AS win, tot.e AS endpoint, tot.cnt AS origins,\n       "
             + "".join(f"{x},\n       " for x in pairs)
             + "\n     + ".join(terms) + " AS omega\nFROM tot" + joins + "\nORDER BY 1, 2")
    return {"plan": p, "omega": omega, "classes": classes}


# ---------------------------------------------------------------- the check
DUCKDB = {"dialect": "duckdb", "table": "sessions",
          "window": "time_bucket(INTERVAL 300 SECOND, start_ts)",
          "columns": {"originatesFrom": "src_ip_first",
                      "targets": "dst_ip_first || ':' || CAST(dst_port_first AS VARCHAR)",
                      "tlsJa4": "ja4",
                      "srcPrefix": r"regexp_replace(src_ip_first, '\.[0-9]+$', '')"}}


def sessions(n=6000, seed=7):
    """Generated sessions with what the count query must get right: clients that
    open several sessions (distinct counting), sessions without TLS, a botnet on
    few stacks, and several windows and endpoints."""
    rng = np.random.default_rng(seed)
    clients = rng.integers(0, 2500, n)
    bot = rng.random(n) < 0.3
    ip = np.where(bot, [f"{a}.{b}.{c}.{d}" for a, b, c, d in rng.integers(1, 224, (n, 4))],
                  [f"198.{(c // 256) % 256}.{c % 7}.{c % 256}" for c in clients])
    ja4 = np.where(bot, [f"t13d_bot_{k}" for k in rng.integers(0, 5, n)],
                   [f"t13d_benign_{k}" for k in np.minimum(rng.zipf(1.5, n), 400)]).astype(object)
    ja4[(~bot) & (rng.random(n) < 0.15)] = None                   # plain HTTP
    ep = np.where(bot, 1, rng.integers(1, 5, n))
    t0 = pd.Timestamp("2026-09-20 00:00:00")
    return pd.DataFrame({"src_ip_first": ip, "ja4": ja4, "dst_ip_first": [f"10.0.0.{e}" for e in ep],
                         "dst_port_first": 443,
                         "start_ts": t0 + pd.to_timedelta(rng.integers(0, 3 * 300, n), unit="s"),
                         "ua": [f"ua{k}" for k in rng.integers(0, 12, n)]})


def run_duckdb(sql, df):
    import duckdb
    con = duckdb.connect()
    con.register("sessions", df)
    out = con.execute(sql).df()
    out["win"] = pd.to_datetime(out["win"])
    return out.set_index(["win", "endpoint"])["omega"]


def reference(df, extra=None):
    """Omega per (window, endpoint) from decompose_omega, the paper's code path."""
    from evidence_mitigation import decompose_omega
    d = df.assign(window=df["start_ts"].dt.floor("300s"),
                  endpoint=df["dst_ip_first"] + ":" + df["dst_port_first"].astype(str))
    out = {}
    for (w, e), g in d.groupby(["window", "endpoint"]):
        om = decompose_omega(g, unit="origin")["omega"]
        if extra:
            col, weight = extra
            n = g.groupby(col)["src_ip_first"].nunique()
            om += weight * float((n * (n - 1) / 2).sum())
        out[(w, e)] = om
    return pd.Series(out)


def extended_ontology(path):
    """A copy of the ontology with one more equality sub-property: same User-Agent."""
    text = ONTOLOGY.read_text()
    new = (f'    <owl:ObjectProperty rdf:about="{KG}relatedBySameUserAgent">\n'
           f'        <rdfs:subPropertyOf rdf:resource="{KG}relatedTo"/>\n'
           f'        <coordinationWeight rdf:datatype="http://www.w3.org/2001/XMLSchema#decimal">0.5</coordinationWeight>\n'
           f'        <classKey rdf:resource="{KG}userAgent"/>\n'
           f'    </owl:ObjectProperty>\n')
    i = text.rindex("</rdf:RDF>")
    Path(path).write_text(text[:i] + new + text[i:])
    import rdflib
    size = lambda f: len(rdflib.Graph().parse(str(f)))
    return size(path) - size(ONTOLOGY)          # triples the new signal costs


def check(out):
    df = sessions()
    base = compile_sql(DUCKDB)
    got, ref = run_duckdb(base["omega"], df), reference(df)
    diff = float((got.reindex(ref.index) - ref).abs().max())
    with tempfile.TemporaryDirectory() as tmp:
        ext_path = Path(tmp) / "extended.owl"
        added = extended_ontology(ext_path)
        binding = {**DUCKDB, "columns": {**DUCKDB["columns"], "userAgent": "ua"}}
        ext = compile_sql(binding, ontology=ext_path)
        got_x, ref_x = run_duckdb(ext["omega"], df), reference(df, extra=("ua", 0.5))
        diff_x = float((got_x.reindex(ref_x.index) - ref_x).abs().max())
        rel_x = [c["relation"] for c in ext["plan"]["classes"]]
    res = {"sessions": int(len(df)), "origins": int(df["src_ip_first"].nunique()),
           "windows_x_endpoints": int(len(ref)), "plan": base["plan"],
           "omega_max_abs_diff": diff, "omega_max": float(ref.max()),
           "extension": {"relation": "relatedBySameUserAgent", "triples_added": added,
                         "code_lines_changed": 0, "compiled_classes": rel_x,
                         "omega_max_abs_diff": diff_x,
                         "omega_changed": bool((ref_x - ref).abs().max() > 0)},
           "duckdb_sql": base["omega"]}
    ok = diff < 1e-6 and diff_x < 1e-6 and "relatedBySameUserAgent" in rel_x
    res["ok"] = ok
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "duckdb_sql"}, indent=2, default=str))
    print(f"{'OK' if ok else 'FAILED'}: {out}")
    return ok


def compare_export(compiled_csv, export_dirs, out):
    """The compiled query's output against the hand-written export of the same day.

    E4 (same-/24 pairs over distinct clients, WAF-blocked requests dropped) uses the
    same filter as the compiled query, so origins and /24 pairs must match exactly.
    The result stays with the data; only the match counts are printed.
    """
    f = Path(compiled_csv)
    got = pd.read_csv(f) if f.suffix == ".csv" else pd.DataFrame(json.loads(f.read_text()))
    got["win"] = pd.to_datetime(got["win"], utc=True)
    parts = []
    for d in export_dirs:
        for f in sorted(Path(d).iterdir()):
            if f.name.startswith("._") or f.suffix not in (".csv", ".json"):
                continue
            df = pd.read_csv(f) if f.suffix == ".csv" else pd.DataFrame(json.loads(f.read_text()))
            if "pares_mesmo_prefixo" in df and "clientes" in df:
                parts.append(df)
    if not parts:
        raise SystemExit(f"{export_dirs}: no E4 export (pares_mesmo_prefixo over clientes)")
    e4 = pd.concat(parts, ignore_index=True)
    e4 = e4.rename(columns={"janela": "win", "host": "endpoint"})
    e4["win"] = pd.to_datetime(e4["win"], utc=True)
    e4 = e4[e4["endpoint"].isin(got["endpoint"].unique())
            & e4["win"].between(got["win"].min(), got["win"].max())]
    m = got.merge(e4, on=["win", "endpoint"], how="outer", indicator=True)
    both = m[m["_merge"] == "both"]
    res = {"windows_compiled": int(len(got)), "windows_export": int(len(e4)), "windows_both": int(len(both)),
           "origins_equal": int((both["origins"] == both["clientes"]).sum()),
           "net_pairs_equal": int((both["pairs_relatedByNetworkProximity"].round(6)
                                   == both["pares_mesmo_prefixo"].round(6)).sum())}
    Path(out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--binding", type=Path, help="JSON: table, window expression, property -> column")
    ap.add_argument("--ontology", type=Path, default=ONTOLOGY)
    ap.add_argument("--sql-out", type=Path, help="write the compiled queries here (.sql)")
    ap.add_argument("--check", action="store_true", help="verify on generated sessions (no data needed)")
    ap.add_argument("--out", type=Path, default=HERE.parents[1] / "results" / "compile_check.json")
    ap.add_argument("--compare", nargs="+", type=Path, metavar="PATH",
                    help="COMPILED_CSV EXPORT_DIR [EXPORT_DIR ...]: compare the compiled query's "
                         "output with the hand-written E4 exports of the same days")
    args = ap.parse_args()
    if args.compare:
        if len(args.compare) < 2:
            ap.error("--compare needs the compiled CSV and at least one export directory")
        compare_export(args.compare[0], args.compare[1:], args.out)
        return
    if args.check:
        sys.exit(0 if check(args.out) else 1)
    if not args.binding:
        ap.error("--binding or --check is required")
    q = compile_sql(json.loads(args.binding.read_text()), ontology=args.ontology)
    text = (f"-- Compiled from {args.ontology.name} by compile_counts.py; do not edit.\n"
            f"-- plan: {json.dumps(q['plan'])}\n\n-- Omega per window and endpoint\n{q['omega']};\n"
            + "".join(f"\n-- class sizes of {name}\n{sql};\n" for name, sql in q["classes"].items()))
    if args.sql_out:
        args.sql_out.write_text(text)
        print(f"OK: {args.sql_out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
