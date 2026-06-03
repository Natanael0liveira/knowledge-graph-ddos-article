#!/usr/bin/env python3
"""§5.6 (nível A) — análise qualitativa estrutural das cadeias de evidência.

Para uma amostra de clusters REAIS detectados (um por tipo de ataque, nos datasets
reais), gera a cadeia de evidência (decomposição de Ω + escopo derivado + JSON-LD +
STIX) e avalia:
  - COMPLETUDE: a cadeia enumera regra/verdito, sessões, sub-relações ativadas + pesos,
    Ω, discriminador e escopo de mitigação? (checklist)
  - ACIONABILIDADE: o escopo derivado é um filtro concreto e não-vazio?
Salva 2 cadeias-exemplo (JSON-LD + STIX) para o apêndice do paper.

NÃO substitui o estudo com analistas humanos (tempo-até-decisão), que fica como
trabalho futuro — esta é a análise estrutural/automatizada.

Uso: python qualitative_evidence.py --sessions ds1=p1.parquet ds2=p2.parquet --out-dir out/
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[2] / "sprint-1" / "scripts"))
sys.path.insert(0, str(HERE.parent))
from compute_coordination import assign_detection_clusters, compute_omega  # noqa: E402
from evidence_mitigation import (decompose_omega, derive_scope, collateral,  # noqa: E402
                                 evidence_chain_jsonld, stix_bundle)

REQUIRED = ["verdict", "clusterSize", "activatedSubRelations", "coordinationScore",
            "derivedMitigationScope"]


def completeness(jsonld: dict) -> dict:
    chk = {
        "regra/veredito": jsonld.get("kg:verdict") is not None,
        "tamanho do cluster": "kg:clusterSize" in jsonld,
        "sub-relações+pesos": all("kg:coordinationWeight" in s for s in jsonld.get("kg:activatedSubRelations", [])) and len(jsonld.get("kg:activatedSubRelations", [])) > 0,
        "score Ω": "kg:coordinationScore" in jsonld,
        "escopo de mitigação": bool(jsonld.get("kg:derivedMitigationScope")),
    }
    return chk


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sessions", nargs="+", required=True, help="NOME=parquet")
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--coverage", type=float, default=0.5)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows, examples = [], []
    for pair in args.sessions:
        name, _, path = pair.partition("=")
        df = pd.read_parquet(path)
        df["start_ts"] = pd.to_datetime(df["start_ts"]); df["end_ts"] = pd.to_datetime(df["end_ts"])
        d = assign_detection_clusters(df, 300)
        cl = compute_omega(d)
        benign = df[df["label_first"] == "BENIGN"]
        # um cluster por tipo de ataque (o de maior Ω, attack-dominante)
        for atk in sorted(set(df["label_first"].unique()) - {"BENIGN", "UNLABELED"}):
            sub = cl[(cl["dominant_label"] == atk) & (cl["attack_frac"] >= 0.5)]
            if not len(sub):
                continue
            cid = sub.sort_values("omega", ascending=False).iloc[0]["det_cluster"]
            cluster = d[d["det_cluster"] == cid]
            decomp = decompose_omega(cluster)
            scope = derive_scope(cluster, coverage=args.coverage)
            jsonld = evidence_chain_jsonld(decomp, scope, f"{name}-{atk}")
            col = collateral(scope, benign) if len(benign) else None
            chk = completeness(jsonld)
            rows.append({
                "dataset": name, "ataque": atk, "|S|": decomp["size"],
                "Ω": round(decomp["omega"], 0),
                "sub-relações": "+".join(s.split("#")[-1].replace("relatedBy", "") for s in
                                         [x["@type"] for x in jsonld["kg:activatedSubRelations"]]),
                "escopo": ",".join(k.split(":")[-1] for k in scope),
                "completa": all(chk.values()),
                "acionável": bool(scope),
            })
            if len(examples) < 2:
                ex = {"jsonld": jsonld, "stix": stix_bundle(decomp, scope, f"{name}-{atk}")}
                (args.out_dir / f"chain_{name}_{atk}.jsonld").write_text(json.dumps(ex["jsonld"], indent=2, ensure_ascii=False))
                (args.out_dir / f"chain_{name}_{atk}.stix.json").write_text(json.dumps(ex["stix"], indent=2, ensure_ascii=False))
                examples.append(f"chain_{name}_{atk}")

    res = pd.DataFrame(rows)
    print("\n" + "=" * 92)
    print("§5.6 — CADEIAS DE EVIDÊNCIA (clusters reais): COMPLETUDE + ACIONABILIDADE")
    print("=" * 92)
    print(res.to_string(index=False))
    print(f"\nCompletas: {res['completa'].sum()}/{len(res)} | Acionáveis (escopo não-vazio): {res['acionável'].sum()}/{len(res)}")
    print(f"Exemplos salvos p/ apêndice em {args.out_dir}: {', '.join(examples)}")
    res.to_csv(args.out_dir / "completeness_table.csv", index=False)


if __name__ == "__main__":
    main()
