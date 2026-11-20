"""Rule-based extraction of claims, entities, evidence, uncertainty and scope."""
import re
from dataclasses import dataclass, field, asdict
from . import lexicon as L

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


@dataclass
class Claim:
    id: str
    abstract_id: str
    text: str
    start: int
    end: int
    entities: list
    subject: dict
    object: dict
    polarity: str
    uncertainty: str
    uncertainty_cue: str
    scope: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def split_sentences(text):
    """Yield (sentence, start, end) with character offsets into text."""
    pos = 0
    for part in SENT_SPLIT.split(text):
        start = text.find(part, pos)
        end = start + len(part)
        pos = end
        yield part, start, end


def find_entities(sentence):
    """Longest-match, non-overlapping entity spans, returned in text order."""
    cands = []
    for name, etype, rx in L.ENTITY_REGEX:
        for m in rx.finditer(sentence):
            cands.append((m.start(), m.end(), name, etype))
    cands.sort(key=lambda c: -(c[1] - c[0]))
    taken, out = [], []
    for s, e, name, etype in cands:
        if all(e <= ts or s >= te for ts, te in taken):
            taken.append((s, e))
            out.append({"name": name, "type": etype, "pos": s})
    return sorted(out, key=lambda x: x["pos"])


def pick_subject_object(ents):
    uniq = []
    for e in ents:
        if e["name"] not in [u["name"] for u in uniq]:
            uniq.append(e)
    subject = next((e for t in L.SUBJECT_TYPES for e in uniq if e["type"] == t), uniq[0])
    rest = [e for e in uniq if e["name"] != subject["name"]]
    obj = (next((e for e in rest if e["type"] == "Outcome"), None)
           or next((e for e in rest if e["type"] in ("Product", "Monomer")), None)
           or (rest[0] if rest else None))
    return subject, obj


def uncertainty_of(sentence):
    m = L.U3_CUES.search(sentence)
    if m:
        return "U3", m.group(0)
    m = L.U2_CUES.search(sentence)
    if m:
        return "U2", m.group(0)
    return "U1", ""


def polarity_of(sentence):
    pos, neg = len(L.POSITIVE.findall(sentence)), len(L.NEGATIVE.findall(sentence))
    return "positive" if pos > neg else "negative" if neg > pos else "neutral"


def scope_of(sentence, ents):
    scope = {}
    if (m := L.TEMP_RE.search(sentence)):
        scope["temperature"] = f"{m.group(1)} °C"
    if (m := L.TIME_RE.search(sentence)):
        scope["reaction_time"] = f"{m.group(1)} {m.group(2)}"
    polys = [e["name"] for e in ents if e["type"] == "Polymer"]
    if polys:
        scope["polymer"] = ", ".join(dict.fromkeys(polys))
    if L.NO_CATALYST_RE.search(sentence):
        scope["catalyst"] = "none"
    else:
        cats = [e["name"] for e in ents if e["type"] == "Catalyst"]
        if cats:
            scope["catalyst"] = ", ".join(dict.fromkeys(cats))
    if (m := L.MEDIUM_RE.search(sentence)):
        scope["medium"] = next(g for g in m.groups() if g)
    return scope


def extract_claims(abstract):
    """Return Claim objects for one abstract; abstract-level scope fills gaps."""
    text = abstract["text"]
    sents = list(split_sentences(text))
    # Abstract-level experimental conditions (first mention) for inheritance.
    abstract_scope = {}
    for s, _, _ in sents:
        for k, v in scope_of(s, find_entities(s)).items():
            abstract_scope.setdefault(k, v)

    claims = []
    for i, (s, start, end) in enumerate(sents):
        ents = find_entities(s)
        if not ents or (L.DESCRIPTIVE_ONLY.search(s) and not re.search(r"\d", s)):
            continue
        if not (L.FINDING_CUES.search(s) or re.search(r"\d", s)):
            continue
        subj, obj = pick_subject_object(ents)
        level, cue = uncertainty_of(s)
        scope = scope_of(s, ents)
        inherited = []
        for k in ("temperature", "reaction_time", "catalyst", "polymer"):
            if k not in scope and k in abstract_scope and k in ("temperature", "reaction_time", "catalyst"):
                scope[k] = abstract_scope[k]
                inherited.append(k)
        if inherited:
            scope["inherited_from_abstract"] = inherited
        claims.append(Claim(
            id=f"C_{abstract['id']}_{i+1}", abstract_id=abstract["id"], text=s,
            start=start, end=end, entities=ents, subject=subj, object=obj,
            polarity=polarity_of(s), uncertainty=level, uncertainty_cue=cue, scope=scope))
    return claims
