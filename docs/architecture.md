# Architecture notes

## Why claim-centric?
Entities alone lose context. Making the *claim* a node lets us attach evidence, uncertainty and
experimental scope to one finding, and lets claims from different abstracts support, challenge or
refine one another.

## Example (Pyrolysis)
```
Uncertainty(U1) --From Finding--> Claim C_A01_2 --Subject--> Pyrolysis
                                      |--Has Object--> Yield
                                      |--Evidence--> Evidence(passage from A01)
Claim C_A02_2 --Refines--> Claim C_A01_2     (same polarity, different temperature/catalyst)
```

## Extension points
- `lexicon.py`: add entities, cues, units.
- `extraction.py`: replace with an LLM extractor; keep the `Claim` dataclass as the contract.
- `retrieval.py`: `backend="semantic"` for embedding retrieval.
- `graph_builder.py`: broaden relation matching (e.g. by outcome category instead of exact object).
- Export: graph JSON maps directly to Neo4j (nodes/edges) or GraphML.
