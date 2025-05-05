# app.py  ──────────────────────────────────────────────────────────────────
"""
Joro Audit – minimal Flask backend

• /                       → serves static/index.html
• /api/analyse-website    → GET a site, return a 1-paragraph summary
• /api/upload-file        → accept a file, return {id, filename}
• /api/generate-audit     → call OpenAI o3, return full HTML report
---------------------------------------------------------------------------
Built for Render: gunicorn launches the app object automatically. When you
run `python3 app.py` locally the __main__ block enables hot-reload & debug.
"""
import os, uuid, tempfile, pathlib, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai

# ─────────────── ENV & INIT ───────────────
load_dotenv()                                   # reads .env file
openai.api_key = os.getenv("OPENAI_API_KEY")    # required!

BASE_DIR = pathlib.Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
CORS(app)                                       # allow calls from Squarespace

# directory to stash uploads during generation
TMP_DIR = pathlib.Path(tempfile.gettempdir()) / "joro_uploads"
TMP_DIR.mkdir(exist_ok=True)

def short_id() -> str:
    """12-char unique ID for uploaded files"""
    return uuid.uuid4().hex[:12]

# ─────────────── STATIC ✦ root page ───────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# ─────────────── API: Analyse Website ───────────────
@app.route("/api/analyse-website", methods=["POST"])
def analyse_website():
    """Return a short summary of the public website."""
    website = (request.json or {}).get("website", "").strip()
    if not website:
        return jsonify(error="no website provided"), 400

    try:
        r = requests.get(
            website,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; JoroAudit/1.0)"},
        )
        r.raise_for_status()
    except Exception as e:
        return jsonify(error=f"failed to fetch website: {e}"), 500

    # crude, fast text scrape – first ~4 kB keeps token cost low
    text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:4000]

    prompt = f"""Summarise the key products / services and any insurance-relevant
details you can infer from **{website}** in ONE concise paragraph.

Extracted text (truncated):
{text}
"""

    try:
        resp = openai.ChatCompletion.create(
            model="o3-chat-completion",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        summary = resp.choices[0].message.content.strip()
    except Exception as e:
        return jsonify(error=f"OpenAI error: {e}"), 500

    return jsonify(ok=True, summary=summary)

# ─────────────── API: Upload File ───────────────
@app.route("/api/upload-file", methods=["POST"])
def upload_file():
    """Save one file to /tmp, return an ID used later in the prompt."""
    f = request.files.get("file")
    if not f:
        return jsonify(error="no file"), 400

    fid = short_id()
    path = TMP_DIR / f"{fid}_{f.filename}"
    f.save(path)

    return jsonify(id=fid, filename=f.filename)

# ─────────────── API: Generate Audit ───────────────
@app.route("/api/generate-audit", methods=["POST"])
def generate_audit():
    """Ask OpenAI for a full HTML risk-audit report."""
    data     = request.get_json(force=True) or {}
    website  = data.get("website", "").strip()
    file_ids = data.get("files", [])              # may be []

    prompt = f"""
Act as an expert commercial-insurance broker.  Write a comprehensive **risk
audit** for the organisation behind **{website}**.

If uploaded documents are referenced (IDs: {file_ids}) you may cite them by
filename, otherwise rely on the public website only.

Return a fully-formatted **stand-alone HTML** report that contains:
• Executive summary (one paragraph)  
• Table of recommended cover types, suggested limits & rationale  
• Actionable improvement suggestions (bullet list)  
• Friendly, professional tone
"""

    try:
        resp = openai.ChatCompletion.create(
            model="o3-chat-completion",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )
        html = resp.choices[0].message.content
    except Exception as e:
        return jsonify(error=f"OpenAI error: {e}"), 500

    return jsonify(html=html)

# ─────────────── LOCAL DEVELOPMENT ONLY ───────────────
# Render starts us with: gunicorn app:app   (so this block is skipped)
if __name__ == "__main__":                       # pragma: no cover
    #     http://localhost:5000/  (auto-reload + debug)
    app.run(debug=True, host="0.0.0.0", port=5000)
