import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pytest
from plastickg import PlasticKG

kg = PlasticKG()
KEYWORDS = [k for g in kg.keyword_groups.values() for k in g]


def types(g, t):
    return [n for n in g["nodes"] if n["type"] == t]


def test_pyrolysis_graph_has_all_node_types():
    g = kg.search("Pyrolysis")
    for t in ("Entity", "Claim", "Evidence", "Uncertainty"):
        assert types(g, t), t
    labels = {e["label"] for e in g["edges"]}
    assert {"Subject", "Has Object", "Evidence", "From Finding"} <= labels


def test_scope_extracted():
    g = kg.search("Pyrolysis")
    scopes = [n["data"]["scope"] for n in types(g, "Claim")]
    assert any(s.get("temperature") == "500 °C" and s.get("reaction_time") == "30 min" for s in scopes)


def test_graphs_differ_per_keyword():
    a, b = kg.search("Pyrolysis"), kg.search("Biodegradation")
    assert {n["id"] for n in a["nodes"]} != {n["id"] for n in b["nodes"]}


def test_evidence_is_verbatim_substring():
    for kw in ("PET", "Gasification"):
        for n in types(kg.search(kw), "Evidence"):
            d = n["data"]
            assert d["context"][d["start"]:d["end"]] == d["passage"]


def test_uncertainty_levels():
    g = kg.search("Microplastics")
    levels = {n["data"]["level"] for n in types(g, "Uncertainty")}
    assert "U3" in levels


def test_cross_abstract_relations_exist():
    labels = {e["label"] for e in kg.search("Pyrolysis")["edges"]}
    assert labels & {"Supports", "Challenges", "Refines", "Inconclusive"}


@pytest.mark.parametrize("kw", KEYWORDS)
def test_every_keyword_returns_a_graph(kw):
    assert kg.search(kw)["stats"]["claims"] > 0, kw
