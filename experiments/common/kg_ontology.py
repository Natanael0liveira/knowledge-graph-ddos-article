"""The parts of the ontology the numeric code reads: weights, class keys, count unit.

Every script that computes Omega(S) used to carry its own copy of the
coordinationWeight annotations. They now read them here, from
ontology/ddos_ontology.owl, so a change to the ontology reaches the synthetic
evaluation, the production evaluation, the cost model and the compiled count
query (sprint-6-noms/scripts/compile_counts.py) alike.

- ``relations()``  every relatedBy sub-property with its coordinationWeight and,
  for the equality-based ones, its classKey: the session property whose equal
  values define its equivalence classes;
- ``count_unit()`` the property classes are counted in (originatesFrom: origins);
- ``WEIGHTS``      name -> weight, for the code that only needs the weights.
"""
from functools import lru_cache
from pathlib import Path

import rdflib

KG = "http://security.example.org/ontology/ddos#"
ONTOLOGY = Path(__file__).resolve().parents[2] / "ontology" / "ddos_ontology.owl"

_QUERY = """
PREFIX kg: <http://security.example.org/ontology/ddos#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?rel ?w ?key WHERE {
  ?rel rdfs:subPropertyOf kg:relatedTo ; kg:coordinationWeight ?w .
  OPTIONAL { ?rel kg:classKey ?key }
}"""


def _local(iri):
    return str(iri).split("#", 1)[1]


@lru_cache(maxsize=None)
def _graph(path):
    g = rdflib.Graph()
    g.parse(str(path))
    return g


@lru_cache(maxsize=None)
def relations(path=ONTOLOGY):
    """{sub-property: {"weight": w, "class_key": property or None}}, by name."""
    out = {}
    for row in _graph(Path(path)).query(_QUERY):
        out[_local(row.rel)] = {"weight": float(row.w),
                                "class_key": _local(row.key) if row.key is not None else None}
    if not out:
        raise SystemExit(f"{path}: no relatedBy sub-property carries a coordinationWeight")
    return out


@lru_cache(maxsize=None)
def count_unit(path=ONTOLOGY):
    """The property classes are counted in, from relatedTo's countUnit annotation."""
    units = list(_graph(Path(path)).objects(rdflib.URIRef(KG + "relatedTo"),
                                            rdflib.URIRef(KG + "countUnit")))
    return _local(units[0]) if units else None


WEIGHTS = {name: r["weight"] for name, r in relations().items()}
