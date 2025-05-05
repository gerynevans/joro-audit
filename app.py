# app.py  ── complete replacement
import os, uuid, tempfile, pathlib, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai

# ─────────────────────────────── ENV & SET-UP
load_dotenv()                                   # reads .env
openai.api_key = os.getenv("OPENAI_API_KEY")

BASE_DIR = pathlib.Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
CORS(app)                                       # allow calls from Squarespace

# ─────────────────────────────── HELPERS
TMP_DIR = pathlib.Path(tempfile.gettempdir()) / "joro_uploads"
TMP_DIR.mkdir(exist_ok=True)

def short_id() -> str:
    return uuid.uuid4().hex[:12]

# ─────────────────────────────── STATIC
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# ─────────────────────────────── API
@app.route("/api/analyse-website", methods=["POST"])
def analyse_website():
    """Quickly analyse the public website and return a one-paragraph summary."""
    website = request.json.get("website", "").strip()
    if not website:
        return jsonify(error="no website provided"), 400

    # fetch the page
    try:
        r = requests.get(website, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        return jsonify(error=f"failed to fetch website: {e}"), 500

    # crude text extraction (first 4 kB for token budget)
    text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:4000]

    prompt = f"""Summarise the key products / services and insurance-relevant
    details you can infer from **{website}** in one concise paragraph.

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

@app.route("/api/upload-file", methods=["POST"])
def upload_file():
    """Accept a single file, save it to /tmp, return an ID."""
    f = request.files.get("file")
    if not f:
        return jsonify(error="no file"), 400

    fid = short_id()
    path = TMP_DIR / f"{fid}_{f.filename}"
    f.save(path)

    return jsonify(id=fid, filename=f.filename)

@app.route("/api/generate-audit", methods=["POST"])
def generate_audit():
    """Generate the full HTML audit (website + optional file IDs)."""
    data      = request.get_json(force=True)
    website   = data.get("website", "").strip()
    file_ids  = data.get("files", [])          # may be []

    prompt = f"""
Act as an expert commercial-insurance broker.  Prepare a risk-audit report for
the organisation behind **{website}**.  If any uploaded documents are provided
(refer to them by filename), incorporate relevant details.

Uploaded-file IDs: {file_ids}

Return a fully-formatted **HTML** report that includes:
• An executive summary  
• A table recommending cover types & limits  
• Actionable improvement suggestions
"""

    resp = openai.ChatCompletion.create(
        model="o3-chat-completion",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
    )
    html = resp.choices[0].message.content
    return jsonify(html=html)

# ─────────────────────────────── LOCAL DEV
if __name__ == "__main__":
    app.run(debug
