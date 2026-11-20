"""Usage: python -m plastickg.cli "Pyrolysis" [--out graph.json]"""
import argparse
import json
from .pipeline import PlasticKG


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword")
    ap.add_argument("--out")
    a = ap.parse_args()
    g = PlasticKG().search(a.keyword)
    s = g["stats"]
    print(f"{g['keyword']}: {s['claims']} claims, {s['entities']} entities, "
          f"{s['abstracts']} abstracts, uncertainty {s['uncertainty']}")
    for e in g["edges"]:
        if e["label"] in ("Supports", "Challenges", "Refines", "Inconclusive"):
            print(f"  {e['from']} --{e['label']}--> {e['to']}")
    if a.out:
        json.dump(g, open(a.out, "w"), indent=2)
        print("saved", a.out)


if __name__ == "__main__":
    main()
