# app.py  ──────────────────────────────────────────────────────────
import os, uuid, tempfile, pathlib, datetime, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai                                   # 0.28.1 pinned

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

# ────────── helper – tiny site summary
@app.post("/api/analyse-website")
def analyse_website():
    website = request.json.get("website", "").strip()
    if not website:
        return jsonify(error="no website provided"), 400
    try:
        r = requests.get(website, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0 (JoroAudit/1.0)"})
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

    PROMPT = f"""
You are an expert UK commercial-insurance broker and business advisor with 30+
years’ experience.  Produce a **single, stand-alone HTML document** – DO NOT wrap
it in ``` fences – following the exact 5-section flow below and matching the
polished styling used by JORO (fonts/colors defined by the receiving CSS).

Use British spelling (£), insert **Date: {today}**, and treat the organisation
name exactly as it appears on {website}.  If uploaded document IDs are present
({file_ids}), reference them where relevant.

━━━━━━━━━━  REQUIRED REPORT STRUCTURE  ━━━━━━━━━━
1  Overview  
   • Summarise current policies (Public/Product Liability, Stock & Contents,
     Employers’ Liability, Business Interruption, etc.).  
   • Plain language – no “plain-English” label, no jargon.

2  Coverage Table  
   • Columns: Coverage Type | Category (Essential / Peace-of-Mind /
     Optional) | Client Claim Scenarios | How to Claim (timeline & cost).  
   • Incorporate existing premiums & insurers from uploaded docs.

3  Red Flags & Real-Life Scenarios  
   • Identify gaps (missing tests, expired policies, exclusions).  
   • Provide ACTUAL documented winning & losing claim examples in this sector
     (cite what made them succeed/fail, time & cost impact).

4  Recommended Tests & Certificates by Product Category  
   • Map each product category to standards/certs (ISO, BS EN, CE, REACH …).  
   • Add indicative premium-reduction percentages (e.g. 5-10 %).  

5  Benefits of Additional Steps  
   • Show financial savings, risk reduction, long-term insurer confidence.  
   • Connect every benefit back to the client and insurer.

━━━━━━━━━━  STYLE & FORMAT  ━━━━━━━━━━
• Headings <h3>/<h4>; body text <p>, <ul>, <table>.  
• Re-use JORO colour palette (#709fcc header rows, #4fb57d buttons, etc.).  
• Tables with <thead>, <tbody>; no inline JS other than minimal button logic
  if you wish.  
• Keep total <= 200 kB.

Return ONLY valid HTML – **no markdown back-ticks**, no commentary.
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": PROMPT}],
            temperature=0.4,
            max_tokens=2048,
        )
        html = resp.choices[0].message.content
        return jsonify(html=html)
    except Exception as exc:
        return jsonify(error=f"OpenAI error: {exc}"), 500

# ────────── local dev
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
