"""Keyword -> relevant abstracts.

Default backend is a dependency-free TF-IDF cosine ranker with synonym-based
query expansion and an exact-match boost. A sentence-transformers backend can
be swapped in (see SemanticBackend) for true embedding similarity.
"""
import math
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9][a-z0-9\-]+")


def tokenize(text):
    return TOKEN.findall(text.lower())


class TfidfBackend:
    def __init__(self, docs):
        self.docs = docs
        self.tokens = [tokenize(d) for d in docs]
        n = len(docs)
        df = Counter(t for toks in self.tokens for t in set(toks))
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = [self._vec(toks) for toks in self.tokens]

    def _vec(self, toks):
        tf = Counter(toks)
        v = {t: (1 + math.log(c)) * self.idf.get(t, 1.0) for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def scores(self, query):
        q = self._vec(tokenize(query))
        return [sum(w * d.get(t, 0.0) for t, w in q.items()) for d in self.vecs]


class SemanticBackend:
    """Optional: pip install sentence-transformers, then use backend='semantic'."""
    def __init__(self, docs, model="all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer, util
        self._util = util
        self.model = SentenceTransformer(model)
        self.emb = self.model.encode(docs, convert_to_tensor=True)

    def scores(self, query):
        q = self.model.encode(query, convert_to_tensor=True)
        return self._util.cos_sim(q, self.emb)[0].tolist()


class Retriever:
    def __init__(self, abstracts, keyword_groups, backend="tfidf"):
        self.abstracts = abstracts
        self.synonyms = {}
        for group in keyword_groups.values():
            for kw, syns in group.items():
                self.synonyms[kw.lower()] = [kw.lower()] + [s.lower() for s in syns]
        docs = [f"{a['title']}. {a['text']}" for a in abstracts]
        self.backend = SemanticBackend(docs) if backend == "semantic" else TfidfBackend(docs)

    def expand(self, query):
        q = query.strip().lower()
        return self.synonyms.get(q, [q])

    def search(self, query, min_score=0.05, top_k=10):
        terms = self.expand(query)
        base = self.backend.scores(" ".join(terms))
        out = []
        for a, s in zip(self.abstracts, base):
            blob = f"{a['title']} {a['text']}".lower()
            hit = any(re.search(r"\b" + re.escape(t) + r"\b", blob) for t in terms)
            score = s + (0.5 if hit else 0.0)
            if hit or s >= min_score:
                out.append({"id": a["id"], "title": a["title"], "score": round(score, 3),
                            "exact_match": hit})
        return sorted(out, key=lambda r: -r["score"])[:top_k]
