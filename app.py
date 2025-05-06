# app.py  ──────────────────────────────────────────────────────────
import os, uuid, tempfile, pathlib, datetime, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai                                   # pinned at 0.28.1

# ────────── ENV / PATHS
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

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
    prompt = (
        f"Summarise the business activities found on **{website}** in one "
        f"concise paragraph.  Extracted text (truncated):\n{text}"
    )
    try:
        resp = openai.ChatCompletion.create(
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

# ────────── big report
@app.post("/api/generate-audit")
def generate_audit():
    data     = request.get_json(force=True)
    website  = data.get("website", "").strip()
    file_ids = data.get("files", [])            # may be []
    today    = datetime.date.today().strftime("%d %B %Y")

    PROMPT = f"""You are an expert UK commercial-insurance broker and business
advisor (30 + yrs).  Produce a **single, stand-alone HTML document** – NO ``` –
that follows **exactly** the visual framework JORO provided.

━━━━━━━━━━  DESIGN REQUIREMENTS  ━━━━━━━━━━
• Inject the full <style> block shown below (adjust colours/widths only if
  necessary for readability).  
• Use the SAME heading-icon URLs:  
  • magnifying glass → …/Icon+-+magnifying+glass.png  
  • coverage table  → …/Icon+-+Coverage+table.png  
  • red flag        → …/Icon+-+red+flag.png  
  • test certs      → …/Icon+-+test+certificates.png  
  • benefits        → …/Icon+-+benefits.png  
• Table header background: #709fcc white text.  
• Preference-button cluster (3 pills) with classes:
  .pref-btn btn-essential / btn-interested / btn-notInterested – include the
  tiny JS that toggles ‘btn-unselected’ & adds the ✓ exactly as demo HTML.  
• Colour tokens:  
  #4fb57d green, #f49547 orange, #ef6460 red, #B22222 deep-red.  
• <h3>/<h4> section headings, body text <p>, bullet lists <ul>/<ol>, data tables
  with <thead>/<tbody>.  
• Max total size 180 kB.

━━━━━━━━━━  CONTENT FLOW  ━━━━━━━━━━
1 OVERVIEW – summarise existing cover (Public/Product Liab., Stock & Contents,
  Employers’ Liab., Business Interruption, etc.).  Clear language – NO phrase
  “plain-English”.

2 COVERAGE TABLE – build a 5-column table exactly like the example:
  Coverage Type | Category (Essential / Peace-of-Mind / Optional) |
  Client-specific claim scenarios | How to claim (timeline & cost) |
  Annual Cost (pull figures from uploaded docs if present).

3 RED FLAGS & REAL-LIFE SCENARIOS – combine gaps with ACTUAL documented winning &
  losing claims (pet industry or similar SME examples).  Include time & money
  consequences.

4 RECOMMENDED TESTS & CERTIFICATES BY PRODUCT CATEGORY – map each product line
  to relevant ISO/BS/CE/REACH etc.  Add potential % premium savings.

5 BENEFITS OF ADDITIONAL STEPS – financial, claims-speed, insurer confidence,
  competitive advantage.

━━━━━━━━━━  METADATA  ━━━━━━━━━━
• Top of report:  
  “Joro High Level Insurance Review & Recommendations”  
  Prepared by JORO  
  For: <org name from {website}>  
  Date: {today}

• If file IDs {file_ids} exist, cite filenames when referencing their data.

Return **raw HTML only** with the in-line CSS + minimal JS for preference
buttons.  No markdown fences, no explanatory text.
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": PROMPT}],
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
