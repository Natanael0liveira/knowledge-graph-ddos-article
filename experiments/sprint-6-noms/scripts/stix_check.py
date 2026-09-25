#!/usr/bin/env python3
"""Sprint 6 (NOMS) — the exported STIX 2.1, checked by the OASIS validator.

The paper says the verdict, its decomposition and the scope are exported to STIX
2.1 "without translation". This script makes that checkable. It builds the bundle
of every committed evidence chain (JSON-LD) with evidence_mitigation.stix_bundle,
using nothing but what the chain holds, then:

- validates it with the OASIS stix2-validator (STIX 2.1), counting errors and
  warnings, and again in strict mode, where every SHOULD of the specification is
  an error and custom properties are rejected;
- parses it with the stix2 library, as a consumer would;
- checks that the indicator's pattern names every fingerprint of the scope.

The bundles are written next to their chains, replacing the earlier ones, which
the validator rejected (identifiers not of the form type--UUID; created, modified
and valid_from missing; a fingerprint set rendered as a Python list).

Usage:
    python stix_check.py --out ../results/stix_validation.json
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
EXP = HERE.parents[2]
sys.path[:0] = [str(EXP / "common"), str(EXP / "pillar4-evidence-mitigation" / "scripts")]
from evidence_mitigation import stix_bundle  # noqa: E402

P4 = EXP / "pillar4-evidence-mitigation" / "results"
CHAINS = [HERE.parents[1] / "results" / "example_chain.jsonld", P4 / "evidence.jsonld",
          *sorted((P4 / "chains").glob("*.jsonld"))]
# Where each chain's bundle goes: next to it, as the exporters name it.
TARGET = {P4 / "evidence.jsonld": P4 / "mitigation.stix.json"}


def from_jsonld(chain):
    """decompose_omega's and derive_scope's output, read back from a chain."""
    decomp = {"omega": chain["kg:coordinationScore"], "size": chain["kg:clusterSize"],
              "activated": {a["@type"].split(":", 1)[1]: {"pairs": a["kg:linkedPairs"],
                                                          "weight": a["kg:coordinationWeight"]}
                            for a in chain["kg:activatedSubRelations"]}}
    scope = {k.split(":", 1)[1]: v for k, v in chain["kg:derivedMitigationScope"].items()}
    return decomp, scope, chain["@id"].rsplit("/", 1)[-1]


def validate(bundle, strict):
    """The validator's verdict, errors and warnings. ``strict`` also turns every
    SHOULD of the specification into an error and rejects custom properties."""
    from stix2validator import ValidationOptions, validate_string
    r = validate_string(json.dumps(bundle), ValidationOptions(version="2.1", strict=strict,
                                                              strict_properties=strict))
    objs = r.object_results if hasattr(r, "object_results") else [r]
    return (bool(r.is_valid), [str(e) for o in objs for e in o.errors],
            [str(w) for o in objs for w in o.warnings])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=HERE.parents[1] / "results" / "stix_validation.json")
    args = ap.parse_args()
    import stix2

    rows, ok = [], True
    for path in CHAINS:
        decomp, scope, cid = from_jsonld(json.loads(path.read_text()))
        bundle = stix_bundle(decomp, scope, cid)
        valid, errors, warnings = validate(bundle, strict=False)
        strict_ok, strict_errors, _ = validate(bundle, strict=True)
        parsed = stix2.parse(json.dumps(bundle), allow_custom=True)
        pattern = next(o for o in bundle["objects"] if o["type"] == "indicator")["pattern"]
        ja4 = scope.get("tlsJa4") or []
        ja4 = [ja4] if isinstance(ja4, str) else ja4
        named = all(f"'{j}'" in pattern for j in ja4)
        out = TARGET.get(path, path.with_name(path.name.replace(".jsonld", ".stix.json")))
        out.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
        rows.append({"chain": path.name, "objects": len(bundle["objects"]),
                     "fingerprints_in_scope": len(ja4), "pattern_names_every_fingerprint": named,
                     "valid": valid, "errors": errors, "warnings": warnings,
                     "valid_strict": strict_ok, "strict_errors": strict_errors,
                     "parsed_objects": len(parsed.objects)})
        good = valid and strict_ok and not errors and not warnings and named
        ok &= good and len(parsed.objects) == len(bundle["objects"])
        print(f"{'OK ' if good else 'XX '} {path.name}: {len(bundle['objects'])} objects, "
              f"{len(ja4)} fingerprints, {len(errors)} errors, {len(warnings)} warnings, "
              f"strict {'valid' if strict_ok else 'INVALID'}")
        for m in errors + warnings + strict_errors:
            print("     ", m[:150])
    res = {"validator": "stix2-validator (OASIS), STIX 2.1", "bundles": len(rows), "ok": ok,
           "errors": sum(len(r["errors"]) for r in rows), "warnings": sum(len(r["warnings"]) for r in rows),
           "strict_errors": sum(len(r["strict_errors"]) for r in rows),
           "chains": rows}
    args.out.write_text(json.dumps(res, indent=2))
    print(f"{'OK' if ok else 'FAILED'}: {args.out}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
