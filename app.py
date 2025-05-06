# app.py  ──────────────────────────────────────────────────────────
import os, uuid, tempfile, pathlib, datetime, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI                      # Updated import
import prompts                                 # Import our prompts module

# ────────── ENV / PATHS
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Updated client initialization

BASE_DIR = pathlib.Path(__file__).resolve().parent
TMP_DIR  = pathlib.Path(tempfile.gettempdir()) / "joro_uploads"
TMP_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
CORS(app)

def short_id() -> str:
    return uuid.uuid4().hex[:12]

# ────────── serve front-end
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

# ────────── serve static assets
@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# ────────── quick site analysis
@app.post("/api/analyse-website")
def analyse_website():
    website = request.json.get("website", "").strip()
    if not website:
        return jsonify(error="no website provided"), 400
    try:
        r = requests.get(
            website,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (JoroAudit/1.0)"},
        )
        r.raise_for_status()
    except Exception as exc:
        return jsonify(error=f"failed to fetch website: {exc}"), 500

    text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:4000]
    prompt = prompts.get_analysis_prompt(website, text)  # Use our new prompt
    
    try:
        # Updated API call
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        return jsonify(ok=True, summary=resp.choices[0].message.content.strip())
    except Exception as exc:
        return jsonify(error=f"OpenAI error: {exc}"), 500

# ────────── file upload
@app.post("/api/upload-file")
def upload_file():
    f = request.files.get("file")
    if not f:
        return jsonify(error="no file"), 400
    fid = short_id()
    f.save(TMP_DIR / f"{fid}_{f.filename}")
    return jsonify(id=fid, filename=f.filename)

# ────────── file retrieval (helper function)
def get_uploaded_files(file_ids):
    """Get information about uploaded files"""
    files = []
    for fid in file_ids:
        for path in TMP_DIR.glob(f"{fid}_*"):
            filename = path.name[len(fid)+1:]  # Strip ID prefix
            files.append({
                "id": fid,
                "filename": filename,
                "path": str(path)
            })
    return files

# ────────── big report
@app.post("/api/generate-audit")
def generate_audit():
    data     = request.get_json(force=True)
    website  = data.get("website", "").strip()
    file_ids = data.get("files", [])            # may be []
    
    # Get enhanced prompt from our module
    prompt = prompts.get_audit_prompt(website, file_ids)  

    try:
        # Updated API call
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=3000,
        )
        html = resp.choices[0].message.content
        return jsonify(html=html)
    except Exception as exc:
        return jsonify(error=f"OpenAI error: {exc}"), 500

# ────────── local dev
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)