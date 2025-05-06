# app.py  ──────────────────────────────────────────────────────────
"""
Lightweight Flask + OpenAI service for the Joro audit front-end.

• / serves static/index.html
• POST /api/analyse-website   – crawl & summarise the site
• POST /api/upload-file       – accept docs, return short IDs
• POST /api/generate-audit    – call GPT-4o, return full HTML audit
-------------------------------------------------------------------
"""
import os, uuid, tempfile, pathlib, datetime, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai                             # 0.28.1 pinned in requirements.txt

# ─────────────────────── ENV & APP SET-UP
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

BASE_DIR = pathlib.Path(__file__).resolve().parent
TMP_DIR  = pathlib.Path(tempfile.gettempdir()) / "joro_uploads"
TMP_DIR.mkdir(exist_ok=True)

app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
CORS(app)                                 # allow Squarespace origin

# ─────────────────────── CONSTANTS
def short_id() -> str:
    return uuid.uuid4().hex[:12]

# !!  Paste the *beginning* of your original styled report below.
#    The model only needs the header / CSS and the first section
#    (a few kB is enough for style cues).  Trim if you like.
EXAMPLE_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Joro High Level Insurance Review &amp; Recommendations</title>
  <style>
    /* Global Styles – let your site CSS control fonts/colors */
    body { margin: 20px; line-height: 1.6; font-family: inherit; color: inherit; }
    h1,h2,h3,h4,h5 { margin-top: 1.2em; margin-bottom: 0.6em; font-weight: inherit; color: inherit; }
    p, ul, ol, table { margin-bottom: 1em; }
    ul, ol { padding-left: 20px; }
    /* Heading Icon */
    .heading-icon { width: 48px; vertical-align: middle; margin-right: 8px; }
    /* Table styles …  (cut for brevity) */
  </style>
</head>
<body>
  <h3>Joro High Level Insurance Review &amp; Recommendations</h3>
  <p><strong>Prepared by:</strong> JORO<br>
     <strong>For:</strong> Example Ltd<br>
     <strong>Date:</strong> 01 Jan 2025</p>
  <!-- … you can stop here if the rest is huge … -->
</body>
</html>
"""

# ─────────────────────── STATIC FILES
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ─────────────────────── API ENDPOINTS
@app.post("/api/analyse-website")
def analyse_website():
    website = request.json.get("website", "").strip()
    if not website:
        return jsonify(error="no website provided"), 400

    # fetch home page
    try:
        r = requests.get(
            website, timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; JoroAudit/1.0)"}
        )
        r.raise_for_status()
    except Exception as exc:
        return jsonify(error=f"failed to fetch website: {exc}"), 500

    # crude text extraction (first ~4 kB)
    text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:4000]

    prompt = (
        f"Summarise the key products, services and any insurance-relevant clues "
        f"you can infer from **{website}** in one concise paragraph.\n\n"
        f"EXTRACTED TEXT (truncated):\n{text}"
    )

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=256,
        )
        summary = resp.choices[0].message.content.strip()
    except Exception as exc:
        return jsonify(error=f"OpenAI error: {exc}"), 500

    return jsonify(ok=True, summary=summary)


@app.post("/api/upload-file")
def upload_file():
    f = request.files.get("file")
    if not f:
        return jsonify(error="no file"), 400

    fid  = short_id()
    path = TMP_DIR / f"{fid}_{f.filename}"
    f.save(path)

    return jsonify(id=fid, filename=f.filename)


@app.post("/api/generate-audit")
def generate_audit():
    data     = request.get_json(force=True)
    website  = data.get("website", "").strip()
    file_ids = data.get("files", [])

    today = datetime.date.today().strftime("%d %b %Y")

    prompt = f"""
You are an experienced UK commercial-insurance broker.

Produce a **complete, stand-alone HTML file** (including <html>, <head> with
inline CSS, and <body>).  Match the look & feel of the example report that
follows the delimiter.

Requirements
• Use the organisation’s name exactly as it appears on {website}.
• Use GBP symbols (£) and British spelling.
• Include: Executive summary, a coverage recommendations table, and 3–5
  actionable suggestions.
• Mention any uploaded document IDs if given: {file_ids!r}
• Insert today’s date like “Date: {today}”.
• Keep it under ~200 kB total.

──────────────────────── EXAMPLE REPORT ────────────────
{EXAMPLE_HTML}
────────────────────────────────────────────────────────
"""

    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=2048,
        )
        html = resp.choices[0].message.content
    except Exception as exc:
        return jsonify(error=f"OpenAI error: {exc}"), 500

    return jsonify(html=html)


# ─────────────────────── LOCAL DEV CONVENIENCE
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
