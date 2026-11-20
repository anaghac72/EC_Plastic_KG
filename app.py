import os

from flask import Flask, jsonify, render_template, request
from plastickg import PlasticKG

app = Flask(__name__)
kg = PlasticKG(
    abstracts_path=os.environ.get(
        "PLASTICKG_ABSTRACTS", "data/openalex_abstracts.json"
    )
)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/keywords")
def keywords():
    return jsonify({cat: list(kws) for cat, kws in kg.keyword_groups.items()})


@app.get("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify(error="Enter a keyword to search."), 400
    return jsonify(kg.search(q))


@app.get("/api/abstracts")
def abstracts():
    return jsonify(kg.abstracts)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
