"""End-to-end pipeline: keyword -> retrieval -> extraction -> graph."""
import json
import re
from pathlib import Path
from .retrieval import Retriever
from .extraction import extract_claims
from .graph_builder import build_graph
from .lexicon import ENTITY_REGEX

DATA = Path(__file__).resolve().parent.parent / "data"


class PlasticKG:
    def __init__(self, abstracts_path=None, keywords_path=None, backend="tfidf"):
        self.abstracts = json.loads(Path(abstracts_path or DATA / "abstracts.json").read_text("utf-8"))
        self.keyword_groups = json.loads(Path(keywords_path or DATA / "keywords.json").read_text("utf-8"))
        self.by_id = {a["id"]: a for a in self.abstracts}
        self.retriever = Retriever(self.abstracts, self.keyword_groups, backend)
        self._claims = {a["id"]: extract_claims(a) for a in self.abstracts}  # extract once

    def search(self, keyword):
        keyword = keyword.strip()
        retrieved = self.retriever.search(keyword)
        terms = self.retriever.expand(keyword)
        pats = [re.compile(r"\b" + re.escape(t) + r"\b", re.I) for t in terms]
        claims = []
        for r in retrieved:
            for c in self._claims[r["id"]]:
                # keep claims whose sentence mentions the keyword (or a synonym)
                if any(p.search(c.text) for p in pats) or any(
                        e["name"].lower() == keyword.lower() for e in c.entities):
                    claims.append(c)
        return build_graph(keyword, claims, self.by_id, retrieved)
