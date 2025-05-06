# app.py  ──────────────────────────────────────────────────────────
import os, uuid, tempfile, pathlib, datetime, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI                       # Updated import

# ────────── ENV / PATHS
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Updated client initialization

BASE_DIR = pathlib.Path(__file__).resolve().parent
TMP_DIR  = pathlib.Path(tempfile.gettempdir()) / "joro_uploads"
TMP_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
# Enable CORS for all domains
CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type"], "methods": ["GET", "POST", "OPTIONS"]}})

# Additional CORS handling
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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
    
    # Print for debugging
    print(f"Attempting to analyze website: {website}")
    
    try:
        # Use a more standard user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Increase timeout
        r = requests.get(website, timeout=20, headers=headers)
        r.raise_for_status()
        
        # Print response details for debugging
        print(f"Response status: {r.status_code}, Content length: {len(r.text)}")
        
    except requests.exceptions.SSLError as exc:
        print(f"SSL Error: {exc}")
        return jsonify(error=f"SSL verification failed. The website might have security issues."), 500
    except requests.exceptions.ConnectionError as exc:
        print(f"Connection Error: {exc}")
        return jsonify(error=f"Could not connect to the website. Please check the URL."), 500
    except requests.exceptions.Timeout as exc:
        print(f"Timeout Error: {exc}")
        return jsonify(error=f"The website took too long to respond."), 500
    except requests.exceptions.RequestException as exc:
        print(f"Request Error: {exc}")
        return jsonify(error=f"Failed to fetch website: {exc}"), 500
    except Exception as exc:
        print(f"Unexpected Error: {exc}")
        return jsonify(error=f"An unexpected error occurred: {exc}"), 500

    # Continue with text processing
    try:
        text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:4000]
        print(f"Successfully extracted text, length: {len(text)}")
    except Exception as exc:
        print(f"Text extraction error: {exc}")
        return jsonify(error=f"Failed to parse website content: {exc}"), 500

    # Define the prompt directly
    prompt = (
        f"Summarise the business activities found on **{website}** in one "
        f"concise paragraph.  Extracted text (truncated):\n{text}"
    )
    
    try:
        # Updated API call
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        summary = resp.choices[0].message.content.strip()
        print(f"Successfully generated summary: {summary[:50]}...")
        return jsonify(ok=True, summary=summary)
    except Exception as exc:
        print(f"OpenAI Error: {exc}")
        return jsonify(error=f"OpenAI error: {exc}"), 500

# ────────── handle OPTIONS requests for CORS preflight
@app.route('/api/analyse-website', methods=['OPTIONS'])
def handle_options_analyse():
    return '', 200

# ────────── file upload
@app.post("/api/upload-file")
def upload_file():
    f = request.files.get("file")
    if not f:
        return jsonify(error="no file"), 400
    fid = short_id()
    f.save(TMP_DIR / f"{fid}_{f.filename}")
    return jsonify(id=fid, filename=f.filename)

# ────────── handle OPTIONS requests for file upload
@app.route('/api/upload-file', methods=['OPTIONS'])
def handle_options_upload():
    return '', 200

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
    data = request.get_json(force=True)
    website = data.get("website", "").strip()
    file_ids = data.get("files", [])            # may be []
    today = datetime.date.today().strftime("%d %B %Y")
    
    print(f"Generating audit for website: {website} with file IDs: {file_ids}")
    
    # Define the enhanced prompt directly
    PROMPT = f"""You are an expert UK commercial-insurance broker and business
advisor (30+ years). Produce a **single, stand-alone HTML document** – NO ``` –
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
  tiny JS that toggles 'btn-unselected' & adds the ✓ exactly as demo HTML.  
• Colour tokens:  
  #4fb57d green, #f49547 orange, #ef6460 red, #B22222 deep-red.  
• <h3>/<h4> section headings, body text <p>, bullet lists <ul>/<ol>, data tables
  with <thead>/<tbody>.  
• Max total size 180 kB.

━━━━━━━━━━  CONTENT FLOW  ━━━━━━━━━━
1 OVERVIEW – summarise existing cover (Public/Product Liab., Stock & Contents,
  Employers' Liab., Business Interruption, etc.). Clear language – NO phrase
  "plain-English".

2 COVERAGE TABLE – build a 5-column table exactly like the example:
  Coverage Type | Category (Essential / Peace-of-Mind / Optional) |
  Client-specific claim scenarios | How to claim (timeline & cost) |
  Annual Cost (pull figures from uploaded docs if present).

3 RED FLAGS & REAL-LIFE SCENARIOS – combine gaps with ACTUAL documented winning &
  losing claims (pet industry or similar SME examples). Include time & money
  consequences.

4 RECOMMENDED TESTS & CERTIFICATES BY PRODUCT CATEGORY – map each product line
  to relevant ISO/BS/CE/REACH etc. Add potential % premium savings.

5 BENEFITS OF ADDITIONAL STEPS – financial, claims-speed, insurer confidence,
  competitive advantage.

━━━━━━━━━━  METADATA  ━━━━━━━━━━
• Top of report:  
  "Joro High Level Insurance Review & Recommendations"  
  Prepared by JORO  
  For: <org name from {website}>  
  Date: {today}

• If file IDs {file_ids} exist, cite filenames when referencing their data.

Return **raw HTML only** with the in-line CSS + minimal JS for preference
buttons. No markdown fences, no explanatory text.

━━━━━━━━━━  STYLE BLOCK  ━━━━━━━━━━
<style>
    body {{
        font-family: 'Segoe UI', Arial, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }}
    
    h1, h2, h3, h4 {{
        color: #3a5a7c;
        margin-top: 1.5em;
    }}
    
    h1 {{
        font-size: 28px;
        text-align: center;
        margin-bottom: 5px;
    }}
    
    h2 {{
        font-size: 24px;
        border-bottom: 2px solid #709fcc;
        padding-bottom: 10px;
    }}
    
    h3 {{
        font-size: 20px;
        display: flex;
        align-items: center;
    }}
    
    h3 img {{
        height: 24px;
        margin-right: 10px;
    }}
    
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }}
    
    th {{
        background-color: #709fcc;
        color: white;
        padding: 10px;
        text-align: left;
    }}
    
    td {{
        padding: 10px;
        border: 1px solid #ddd;
    }}
    
    tr:nth-child(even) {{
        background-color: #f2f7fd;
    }}
    
    .highlight-green {{
        color: #4fb57d;
        font-weight: bold;
    }}
    
    .highlight-orange {{
        color: #f49547;
        font-weight: bold;
    }}
    
    .highlight-red {{
        color: #ef6460;
        font-weight: bold;
    }}
    
    .highlight-deep-red {{
        color: #B22222;
        font-weight: bold;
    }}
    
    .metadata {{
        text-align: center;
        margin-bottom: 30px;
    }}
    
    .metadata p {{
        margin: 5px 0;
    }}
    
    .pref-button-group {{
        display: flex;
        gap: 10px;
        margin: 10px 0;
    }}
    
    .pref-btn {{
        padding: 5px 15px;
        border-radius: 20px;
        border: none;
        color: white;
        font-weight: bold;
        cursor: pointer;
    }}
    
    .btn-essential {{
        background-color: #4fb57d;
    }}
    
    .btn-interested {{
        background-color: #f49547;
    }}
    
    .btn-notInterested {{
        background-color: #ef6460;
    }}
    
    .btn-unselected {{
        opacity: 0.6;
    }}
    
    .section-icon {{
        width: 40px;
        height: 40px;
        margin-right: 15px;
    }}
</style>
"""

    try:
        # Updated API call
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": PROMPT}],
            temperature=0.4,
            max_tokens=3000,
        )
        html = resp.choices[0].message.content
        print(f"Successfully generated audit HTML (length: {len(html)})")
        return jsonify(html=html)
    except Exception as exc:
        print(f"OpenAI Error: {exc}")
        return jsonify(error=f"OpenAI error: {exc}"), 500

# ────────── handle OPTIONS requests for audit
@app.route('/api/generate-audit', methods=['OPTIONS'])
def handle_options_audit():
    return '', 200

# ────────── local dev
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)