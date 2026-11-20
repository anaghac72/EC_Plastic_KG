"""Assemble a keyword-specific claim graph from extracted claims."""
from . import lexicon as L

EDGE_LABELS = ["Subject", "Has Object", "Evidence", "Supports", "Challenges",
               "Refines", "Inconclusive", "From Finding"]
SCOPE_KEYS = ("temperature", "reaction_time", "catalyst", "polymer")


def claim_relation(new, old):
    """Relation of claim `new` towards claim `old` (same subject + object)."""
    if "U3" in (new.uncertainty, old.uncertainty):
        return "Inconclusive"
    if new.polarity != old.polarity and "neutral" not in (new.polarity, old.polarity):
        return "Challenges"
    differs = any(k in new.scope and k in old.scope and new.scope[k] != old.scope[k]
                  for k in SCOPE_KEYS)
    return "Refines" if differs else "Supports"


def build_graph(keyword, claims, abstracts_by_id, retrieved):
    nodes, edges, seen = {}, [], set()

    def add_node(nid, ntype, label, **data):
        nodes.setdefault(nid, {"id": nid, "type": ntype, "label": label, "data": data})

    def add_edge(src, dst, label, **data):
        key = (src, dst, label)
        if key not in seen:
            seen.add(key)
            edges.append({"from": src, "to": dst, "label": label, "data": data})

    for c in claims:
        ab = abstracts_by_id[c.abstract_id]
        for role, ent, label in (("subject", c.subject, "Subject"), ("object", c.object, "Has Object")):
            if ent is None:
                continue
            nid = f"E_{ent['name']}"
            add_node(nid, "Entity", ent["name"], entity_type=ent["type"],
                     is_query=ent["name"].lower() == keyword.lower())
            if role == "subject":
                add_edge(f"{c.id}", nid, label)
            else:
                add_edge(f"{c.id}", nid, label)
        short = c.text if len(c.text) <= 90 else c.text[:87] + "..."
        add_node(c.id, "Claim", short, full_text=c.text, abstract_id=c.abstract_id,
                 polarity=c.polarity, scope=c.scope)
        ev = f"EV_{c.id}"
        add_node(ev, "Evidence", f"[{c.abstract_id}] \"{c.text[:60]}...\"", passage=c.text,
                 abstract_id=c.abstract_id, abstract_title=ab["title"], start=c.start, end=c.end,
                 context=ab["text"])
        add_edge(c.id, ev, "Evidence")
        un = f"U_{c.id}"
        add_node(un, "Uncertainty", c.uncertainty, level=c.uncertainty,
                 description=L.UNCERTAINTY_LEVELS[c.uncertainty], cue=c.uncertainty_cue)
        add_edge(un, c.id, "From Finding")

    # Claim-to-claim relations: same subject and same object, across abstracts.
    for i, new in enumerate(claims):
        for old in claims[:i]:
            if new.abstract_id == old.abstract_id or new.object is None or old.object is None:
                continue
            if new.subject["name"] == old.subject["name"] and new.object["name"] == old.object["name"]:
                add_edge(new.id, old.id, claim_relation(new, old))

    return {
        "keyword": keyword,
        "nodes": list(nodes.values()),
        "edges": edges,
        "retrieved_abstracts": retrieved,
        "stats": {
            "claims": sum(n["type"] == "Claim" for n in nodes.values()),
            "entities": sum(n["type"] == "Entity" for n in nodes.values()),
            "abstracts": len({c.abstract_id for c in claims}),
            "uncertainty": {lv: sum(c.uncertainty == lv for c in claims) for lv in ("U1", "U2", "U3")},
        },
    }
