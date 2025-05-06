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

# ────────── get uploaded files
def get_uploaded_files(file_ids):
    uploaded_files = []
    for fid in file_ids:
        for filepath in TMP_DIR.glob(f"{fid}_*"):
            if filepath.is_file():
                uploaded_files.append({
                    "id": fid,
                    "filename": filepath.name[len(fid)+1:],
                    "path": str(filepath)
                })
    return uploaded_files

# ────────── read file contents
def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        # If text reading fails, treat as binary file
        return "[Binary file content - cannot be displayed]"

# ────────── generate audit HTML template with CSS
def get_audit_html_template():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Joro High Level Insurance Review &amp; Recommendations</title>
  <style>
    /* Global Styles */
    body {
      margin: 20px;
      line-height: 1.6;
      font-family: inherit;
      color: inherit;
    }
    h1, h2, h3, h4, h5 {
      margin-top: 1.2em;
      margin-bottom: 0.6em;
      font-weight: inherit;
      color: inherit;
    }
    p, ul, ol, table {
      margin-bottom: 1em;
    }
    ul, ol {
      padding-left: 20px;
    }

    /* Heading Icon Style */
    .heading-icon {
      width: 48px;
      vertical-align: middle;
      margin-right: 8px;
    }

    /* Table Styles */
    table {
      border-collapse: collapse;
      width: 100%;
      margin-bottom: 20px;
    }
    table, th, td {
      border: 1px solid #ddd;
    }
    th, td {
      padding: 6px 8px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background-color: #709fcc;
      color: #fff;
    }
    table.coverage-table tbody tr td:nth-child(1),
    table.coverage-table tbody tr td:nth-child(2) {
      font-weight: bold;
    }
    col.group-col1 { width: 15%; }
    col.group-col2 { width: 30%; }
    col.group-col3 { width: 25%; }
    col.group-col4 { width: 25%; }
    col.group-col5 { width: 5%; }

    /* Category Color Styles & Icons */
    .dark-red { color: #8B0000; }
    .mid-red { color: #B22222; }
    .orange-text { color: #FF4500; }
    .green-text { color: #008000; }
    .warning-icon::before { content: "⚠️ "; }
    .thumbs-up-icon::before { content: "👍 "; }
    .tick-icon { margin-left: 4px; }

    /* Preference Buttons */
    .preference-buttons { margin-top: 0.5em; }
    .pref-btn {
      display: inline-block;
      border: none;
      padding: 6px 14px;
      margin-right: 4px;
      border-radius: 9999px;
      color: #fff;
      cursor: pointer;
      font-size: 14px;
      font-family: inherit;
      transition: background-color 0.3s ease;
      line-height: 1.2;
    }
    .btn-essential {
      background-color: #4fb57d;
    }
    .btn-interested {
      background-color: #f49547;
    }
    .btn-notInterested {
      background-color: #ef6460;
    }
    .btn-unselected {
      background-color: #D3D3D3 !important;
      color: #555 !important;
    }

    /* Upload-to-profile Button */
    .upload-profile-btn {
      display: inline-block;
      background-color: #4fb57d;
      color: #fff;
      padding: 8px 16px;
      font-size: 14px;
      border: none;
      border-radius: 4px;
      text-transform: uppercase;
      text-decoration: none;
      cursor: pointer;
      transition: background-color 0.3s ease;
      margin-top: 1em;
      margin-bottom: 1em;
    }
    .upload-profile-btn:hover {
      background-color: #43a16b;
    }
  </style>
</head>
<body>
  <!-- Content will be inserted here by the AI -->
  
  <!-- Script for toggling preference buttons -->
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      const preferenceGroups = document.querySelectorAll('.preference-buttons');

      preferenceGroups.forEach(group => {
        const buttons = group.querySelectorAll('.pref-btn');
        buttons.forEach(btn => {
          btn.addEventListener('click', function() {
            // Clear any existing selections in this group
            buttons.forEach(sibling => {
              sibling.classList.remove('btn-unselected');
              sibling.innerHTML = sibling.getAttribute('data-label');
              sibling.dataset.selected = "false";
            });

            // Mark clicked button as selected and add tick
            btn.dataset.selected = "true";
            btn.innerHTML = btn.getAttribute('data-label') + ' <span class="tick-icon">✓</span>';

            // Grey out the other buttons
            buttons.forEach(sibling => {
              if (sibling !== btn) {
                sibling.classList.add('btn-unselected');
              }
            });
          });
        });
      });
    });
  </script>
</body>
</html>"""

# ────────── big report
@app.post("/api/generate-audit")
def generate_audit():
    data = request.get_json(force=True)
    website = data.get("website", "").strip()
    file_ids = data.get("files", [])            # may be []
    today = datetime.date.today().strftime("%d %B %Y")
    
    # Get business description from website
    business_description = ""
    if website:
        try:
            r = requests.get(
                website,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (JoroAudit/1.0)"},
            )
            r.raise_for_status()
            text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:4000]
            site_prompt = (
                f"Summarise the business activities found on **{website}** in one "
                f"concise paragraph. Extracted text (truncated):\n{text}"
            )
            resp = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": site_prompt}],
                temperature=0.3,
                max_tokens=256,
            )
            business_description = resp.choices[0].message.content.strip()
        except Exception:
            # If website analysis fails, continue with empty description
            pass
    
    # Get uploaded files information
    uploaded_files = get_uploaded_files(file_ids)
    file_info = []
    
    for file in uploaded_files:
        content = read_file_content(file["path"])
        file_info.append({
            "filename": file["filename"],
            "content": content[:10000]  # Limit content length
        })
    
    # Extract organization name from website
    org_name = ""
    if website:
        try:
            domain = website.lower()
            if domain.startswith("http://"):
                domain = domain[7:]
            elif domain.startswith("https://"):
                domain = domain[8:]
            
            # Extract domain name without www and extension
            if domain.startswith("www."):
                domain = domain[4:]
            
            domain = domain.split("/")[0]  # Remove path
            parts = domain.split(".")
            if len(parts) >= 2:
                org_name = parts[-2].capitalize()  # Use the domain name as org name
                
            # If org_name looks like a generic domain, try to get from website title
            if org_name in ["Com", "Net", "Org", "Co", "Io"]:
                try:
                    soup = BeautifulSoup(r.text, "html.parser")
                    if soup.title:
                        org_name = soup.title.string.split("|")[0].strip()
                        org_name = org_name.split("-")[0].strip()
                except Exception:
                    pass
        except Exception:
            org_name = "Client"
    
    if not org_name:
        org_name = "Client"

    # Build the comprehensive audit prompt including the template
    PROMPT = f"""Act as an expert insurance broker and business advisor with over 30 years of experience. 
Your task is to produce a Comprehensive Insurance Report, prepared by JORO, for {org_name}.

The information we have about the client:
- Website: {website}
- Business Description: {business_description}

Files provided for analysis: {len(file_info)} document(s)
{chr(10).join([f"- {file['filename']}" for file in file_info])}

Your task is to produce a Comprehensive Insurance Report that follows the exact HTML design from the template below.
This HTML document should be fully functional with appropriate styling, preference buttons, and the same icon URLs.

Please make sure to implement the following 5-section flow exactly as described:

1. OVERVIEW
   - Provide an overview of the client's existing insurance coverage based on any information available
   - Keep the language clear and easy to understand without sounding condescending
   - Summarize key policies such as Public Liability, Product Liability, Stock & Contents, Employers' Liability, Business Interruption
   - Highlight why each coverage exists and any typical coverage limits, avoid unnecessary insurance jargon

2. COVERAGE TABLE
   - Create a table that categorizes each coverage into:
     * Highly recommended / business essential
     * Recommended for peace of mind
     * Optional (removable to save money, noting reduced coverage)
   - Include these columns:
     * Coverage Type
     * Category (Essential / Peace-of-Mind / Optional)
     * Client-specific claim scenarios
     * How to claim (timeline & cost)
     * Annual Cost (pull figures from uploaded docs if present)
   - Each row should include the preference buttons exactly as in the template

3. RED FLAGS & REAL-LIFE SCENARIOS
   - Combine gaps with ACTUAL documented winning & losing claims (pet industry or similar SME examples)
   - Include time & money consequences
   - Provide actual documented examples of successful and unsuccessful claims
   - Explain the impact on time and money for each scenario

4. RECOMMENDED TESTS & CERTIFICATES BY PRODUCT CATEGORY
   - Map each product line to relevant ISO/BS/CE/REACH etc. standards
   - Add potential % premium savings for each certification
   - Break down the client's product categories and specify which certificates or safety standards help strengthen claims
   - Include indicative financial savings that may be achieved through compliance

5. BENEFITS OF ADDITIONAL STEPS
   - Summarize financial benefits, operational benefits, and long-term relationship benefits
   - Explain how these steps save money, reduce risk, and create long-term value

IMPORTANT: Use the exact same heading icons:
- Overview: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb25470b8415a5795ed69/1743762005158/Icon+-+magnifying+glass.png
- Coverage Table: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2548246ac491eae87ce/1743762005156/Icon+-+Coverage+table.png
- Red Flag: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2540b0ebe5af8f8b121/1743762005078/Icon+-+red+flag.png
- Test Certificates: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2547bec2273aed7c754/1743762005181/Icon+-+test+certificates.png
- Benefits: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb254dc69af7a4b2ad623/1743762005197/Icon+-+benefits.png

Use these colors for categorization:
- #4fb57d green (optional)
- #f49547 orange (peace of mind)
- #ef6460 red (essential)
- #B22222 deep-red (highly essential)

The final document must include:
- Header: "Joro High Level Insurance Review & Recommendations"
- Prepared by: JORO
- For: {org_name}
- Date: {today}

File contents for reference:
{chr(10).join([f"--------- {file['filename']} ---------\n{file['content'][:1000]}...\n" for file in file_info])}

Return raw HTML only (no markdown) based on this template:
"""

    # Add the HTML template as reference
    PROMPT += get_audit_html_template()

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": PROMPT}],
            temperature=0.4,
            max_tokens=4000,  # Increased max_tokens to handle larger HTML output
        )
        html = resp.choices[0].message.content
        
        # Check if the response is HTML and not wrapped in code blocks
        if html.startswith("```html"):
            html = html.replace("```html", "", 1)
            if html.endswith("```"):
                html = html[:-3]
            html = html.strip()
            
        return jsonify(html=html)
    except Exception as exc:
        return jsonify(error=f"OpenAI error: {exc}"), 500

# ────────── local dev
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)