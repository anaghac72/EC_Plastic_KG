"""Fetch a small, reproducible plastic-waste abstract dataset from OpenAlex.

Uses one Works API page (up to 100 records), reconstructs the abstract text
from OpenAlex's abstract_inverted_index, and saves a pipeline-compatible JSON
array. An optional OPENALEX_API_KEY may be supplied through the environment.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "openalex_abstracts.json"
QUERY = (
    '"plastic waste" OR "plastic recycling" OR "plastic pollution" OR '
    '"polymer recycling" OR "plastic pyrolysis" OR microplastics'
)


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """Restore abstract tokens to their original position order."""
    if not inverted_index:
        return ""
    positions = {
        int(position): token
        for token, token_positions in inverted_index.items()
        for position in token_positions
    }
    if not positions:
        return ""
    return " ".join(positions.get(i, "") for i in range(max(positions) + 1)).strip()


def fetch_works(limit: int = 100) -> list[dict]:
    if not 1 <= limit <= 100:
        raise ValueError("OpenAlex per_page must be between 1 and 100.")

    params = {
        "search.title_abstract_keywords": QUERY,
        "filter": "has_abstract:true,type:article",
        "per_page": limit,
        "select": (
            "id,doi,title,publication_year,authorships,abstract_inverted_index"
        ),
    }
    api_key = os.getenv("OPENALEX_API_KEY")
    if api_key:
        params["api_key"] = api_key

    url = "https://api.openalex.org/works?" + urlencode(params)
    request = Request(
        url,
        headers={"User-Agent": "ECPlasticKG/1.0 (abstract dataset retrieval)"},
    )
    with urlopen(request, timeout=90) as response:
        payload = json.load(response)

    records = []
    seen = set()
    for work in payload.get("results", []):
        abstract = reconstruct_abstract(work.get("abstract_inverted_index"))
        title = (work.get("title") or "").strip()
        work_id = work.get("id")
        if not title or not abstract or not work_id or work_id in seen:
            continue
        seen.add(work_id)
        authors = [
            authorship.get("author", {}).get("display_name")
            for authorship in (work.get("authorships") or [])
            if authorship.get("author", {}).get("display_name")
        ]
        records.append(
            {
                "id": work_id.rsplit("/", 1)[-1],
                "title": title,
                "text": abstract,
                "openalex_id": work_id,
                "doi": work.get("doi"),
                "publication_year": work.get("publication_year"),
                "authors": authors,
                "source": "OpenAlex",
            }
        )

    if not records:
        raise RuntimeError("OpenAlex returned no records with reconstructable abstracts.")

    return records


def main() -> int:
    output = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        records = fetch_works()
    except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError) as exc:
        print(f"OpenAlex retrieval failed: {exc}", file=sys.stderr)
        return 1

    output.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(records)} abstracts to {output}")
    print(f"Query: {QUERY}")
    print(f"Retrieved: {date.today().isoformat()}")
    if len(records) < 100:
        print("Note: fewer than 100 abstracts had usable titles and abstract text.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
