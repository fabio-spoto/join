"""
Einfaches Join-Backend: ersetzt die Firebase Realtime Database REST-API
(GET/PUT auf /<name>.json) mit lokaler JSON-Persistenz.
"""

import json
import os
from pathlib import Path

from flask import Flask, Response, request

app = Flask(__name__)

DATA_FILE = Path(
    os.environ.get("JOIN_DATA_PATH", str(Path(__file__).resolve().parent / "join_data.json"))
)


def load_store() -> dict:
    if not DATA_FILE.exists():
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_store(store: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


def add_cors(resp: Response) -> Response:
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, PUT, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.after_request
def cors_after(resp):
    return add_cors(resp)


@app.route("/<path:subpath>.json", methods=["OPTIONS"])
def preflight(subpath):
    return add_cors(Response(status=204))


@app.route("/<path:subpath>.json", methods=["GET", "PUT"])
def firebase_compat(subpath):
    """
    Firebase RTDB REST: Pfad ohne führenden Slash, z. B. contacts.json, tasks.json.
    optional/tief/nested.json — gespeichert als ein Key "optional/tief/nested".
    """
    key = subpath.strip("/") or "_root"
    store = load_store()

    if request.method == "GET":
        if key not in store:
            return Response("null", mimetype="application/json")
        return Response(json.dumps(store[key], ensure_ascii=False), mimetype="application/json")

    payload = request.get_json(silent=True)
    store[key] = payload
    save_store(store)
    return Response(json.dumps(payload, ensure_ascii=False), mimetype="application/json")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=True)
