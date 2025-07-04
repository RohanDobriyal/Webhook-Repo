import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from flask_cors import CORS
from dotenv import load_dotenv

# ─── Config & Initialization ─────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# Mongo settings
MONGO_URI        = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB         = os.getenv("MONGO_DB", "github_events")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "events")

client = MongoClient(MONGO_URI)
db     = client[MONGO_DB]
events = db[MONGO_COLLECTION]
logging.info(f"MongoDB → {MONGO_URI} | DB: {MONGO_DB} | Collection: {MONGO_COLLECTION}")

# ─── Routes ────────────────────────────────────────────────────────────────

@app.route("/")
def serve_ui():
    """Serve the static UI page."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Receive GitHub webhooks. Support both:
     - application/json
     - application/x-www-form-urlencoded (payload=<JSON>)
    Normalize into {request_id, author, action, from_branch, to_branch, timestamp} and save.
    """
    try:
        # parse payload
        content_type = request.headers.get("Content-Type", "")
        if "application/x-www-form-urlencoded" in content_type:
            raw     = request.form.get("payload", "{}")
            payload = json.loads(raw)
        else:
            payload = request.get_json(force=True, silent=True) or {}

        gh_event = request.headers.get("X-GitHub-Event", "")
        doc = None

        # ── Push ───────────────────────────────────────────────────────────
        if gh_event == "push":
            doc = {
                "request_id": payload.get("after"),
                "author":     payload["pusher"]["name"],
                "action":     "PUSH",
                "from_branch": None,
                "to_branch":  payload["ref"].split("/")[-1],
                "timestamp":  payload["head_commit"]["timestamp"]
            }

        # ── Pull Request / Merge ──────────────────────────────────────────
        elif gh_event == "pull_request":
            pr      = payload["pull_request"]
            pr_id   = str(pr["number"])
            user    = pr["user"]["login"]
            src     = pr["head"]["ref"]
            dst     = pr["base"]["ref"]
            created = pr["created_at"]
            merged  = pr.get("merged_at")

            if payload.get("action") == "closed" and pr.get("merged"):
                doc = {
                    "request_id": pr_id,
                    "author":     user,
                    "action":     "MERGE",
                    "from_branch": src,
                    "to_branch":  dst,
                    "timestamp":  merged
                }
            else:
                doc = {
                    "request_id": pr_id,
                    "author":     user,
                    "action":     "PULL_REQUEST",
                    "from_branch": src,
                    "to_branch":  dst,
                    "timestamp":  created
                }

        else:
            return jsonify({"status": "ignored"}), 200

        events.insert_one(doc)
        logging.info(f"Inserted event: {doc}")
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logging.exception("Error in /webhook")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/events", methods=["GET"])
def list_events():
    """
    Return the most recent 50 events for the UI to poll.
    """
    try:
        cursor = events.find({}, {"_id": 0}).sort("timestamp", -1).limit(50)
        data   = list(cursor)
        return jsonify(data), 200
    except Exception as e:
        logging.exception("Error in /events")
        return jsonify({"status": "error", "message": str(e)}), 500


# ─── Entry Point ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
