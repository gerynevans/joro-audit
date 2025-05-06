# ───────────────────────────────────────── app.py (replace everything) ───
import os, uuid, tempfile, pathlib, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai

# ───────────── ENV & INITIALISATION
load_dotenv()                                   # reads .env in the repo root
openai.api_key = os.getenv("OPENAI_API_KEY")    # your secret key

BASE_DIR = pathlib.Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
CORS(app)                                       # allow Squarespace or any origin

# ───────────── HELPERS
TMP_DIR = pathlib.Path(tempfile.gettempdir()) / "joro_uploads"
TMP_DIR.mkdir(exist_ok=True)

def short_id() -> str:
    """12-char ID for uploaded files."""
    return uuid.uuid4().hex[:12]

# ───────────── STATIC LANDING PAGE
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# ───────────── API ENDPOINTS
@app.route("/api/analyse-website", methods=["POST"])
def analyse_website():
    """Fetch the public site, summarise in one paragraph."""
    website = request.json.get("website", "").strip()
    if not website:
        return jsonify(error="no website provided"), 400

    # fetch HTML
    try:
        r = requests.get(website, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        return jsonify(error=f"failed to fetch website: {e}"), 500

    # basic text extraction (truncate ~4 kB for tokens)
    text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:4000]

    prompt = f"""Summarise the key products / services and any insurance-relevant
    risks you can infer from **{website}** in one concise paragraph.

    Extracted text (truncated):
    {text}
    """

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",                       # <<<<<<<<<<<<<<<<<<
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        summary = resp.choices[0].message.content.strip()
    except Exception as e:
        return jsonify(error=f"OpenAI error: {e}"), 500

    return jsonify(ok=True, summary=summary)

@app.route("/api/upload-file", methods=["POST"])
def upload_file():
    """Receive a file, stash in /tmp, return its ID & original name."""
    f = request.files.get("file")
    if not f:
        return jsonify(error="no file"), 400

    fid = short_id()
    path = TMP_DIR / f"{fid}_{f.filename}"
    f.save(path)

    return jsonify(id=fid, filename=f.filename)

@app.route("/api/generate-audit", methods=["POST"])
def generate_audit():
    """Full HTML insurance audit – website + optional uploaded docs."""
    data     = request.get_json(force=True)
    website  = data.get("website", "").strip()
    file_ids = data.get("files", [])          # may be an empty list

    prompt = f"""
Act as an expert commercial-insurance broker.  Produce a risk-audit report for
the organisation behind **{website}**.  If uploaded documents are provided,
reference them by filename and incorporate any relevant insights.

Uploaded-file IDs: {file_ids}

Return a fully-formatted **HTML** document that includes:
• Executive summary  
• A table of recommended cover types & limits  
• Actionable improvement suggestions
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",                   # <<<<<<<<<<<<<<<<<<
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2048,
        )
        html = resp.choices[0].message.content
    except Exception as e:
        return jsonify(error=f"OpenAI error: {e}"), 500

    return jsonify(html=html)

# ───────────── LOCAL DEV (ignored by gunicorn on Render)
if __name__ == "__main__":
    app.run(debug=True)
# ───────────────────────────────────────────────────────────────────────────
