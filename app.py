# --- app.py — API-only backend using ChatGPT-o3 ---------------------------
import os, json, requests
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())                              # reads .env
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")            # <-- your key

from flask import Flask, request, jsonify
from flask_cors import CORS

# -------------------------------------------------------------------------
#  Flask / CORS setup
# -------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)                                               # allow all origins
BASE_DIR = Path(__file__).resolve().parent

# -------------------------------------------------------------------------
#  0. Health check
# -------------------------------------------------------------------------
@app.route("/ping")
def ping():
    return "pong", 200

# -------------------------------------------------------------------------
#  1. Lite audit – analyse a public website URL
# -------------------------------------------------------------------------
@app.route("/analyse_website", methods=["POST"])
def analyse_website():
    data   = request.get_json(force=True)
    site   = data.get("website", "").strip()
    if not site:
        return jsonify(error="website missing"), 400

    try:
        html = requests.get(site, timeout=10).text[:5000]   # first 5 kB
    except Exception as e:
        return jsonify(error=f"unable to fetch: {e}"), 400

    prompt = f"""Act as an expert insurance broker. Summarise what you learn
about {site} from this HTML:
```{html}```"""
    res = openai.chat.completions.create(
        model="o3-chat-completion",                       # ← ChatGPT o3
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    summary = res.choices[0].message.content.strip()
    return jsonify(summary=summary), 200

# -------------------------------------------------------------------------
#  2. File upload – for Mid / Deep audits
# -------------------------------------------------------------------------
UPLOAD_DIR = "/tmp"
@app.route("/upload", methods=["POST"])
def upload():
    files = request.files.getlist("file")
    if not files:
        return jsonify(error="no files"), 400

    saved = []
    for f in files:
        path = os.path.join(UPLOAD_DIR, f.filename)
        f.save(path)
        saved.append(path)
    return jsonify(files=saved), 200

# -------------------------------------------------------------------------
#  3. Generate the full audit
# -------------------------------------------------------------------------
@app.route("/generate_audit", methods=["POST"])
def generate_audit():
    data    = request.get_json(force=True)
    website = data.get("website", "").strip()
    extras  = data.get("extras", [])          # paths returned by /upload

    big_prompt = f"""
{website=}
{extras=}

Act as an expert insurance broker and business advisor (30 years experience).
Produce a concise HTML insurance audit covering:
1. Overview
2. Coverage table
3. Red flags & real-life scenarios
4. Recommended tests / certificates
5. Benefits of additional steps

Return only valid HTML.
"""
    res = openai.chat.completions.create(
        model="o3-chat-completion",                       # ← ChatGPT o3
        messages=[{"role": "user", "content": big_prompt}],
        temperature=0.3,
        max_tokens=2048
    )
    audit_html = res.choices[0].message.content.strip()
    return jsonify(audit=audit_html), 200

# -------------------------------------------------------------------------
#  Local run / Render entry-point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
