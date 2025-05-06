#!/usr/bin/env python3
"""Flask backend for Joro uploads – fixed quoting & token issues."""

import os
import uuid
import tempfile
import pathlib
import datetime
import textwrap

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# ────────── configuration ────────────────────────────────────────────────────

load_dotenv()
CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY")
if not CLAUDE_KEY:
    raise RuntimeError("Environment variable ANTHROPIC_API_KEY is required.")

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "12000"))

BASE_DIR = pathlib.Path(__file__).resolve().parent
TMP_DIR = pathlib.Path(tempfile.gettempdir()) / "joro_uploads"
TMP_DIR.mkdir(exist_ok=True)

# ────────── Claude API helper ───────────────────────────────────────────────

def call_claude(prompt: str, *, temperature: float = 0.3, max_tokens: int | None = None) -> str:
    """Simple wrapper that POSTs to Anthropic's messages endpoint."""
    if max_tokens is None:
        max_tokens = MAX_TOKENS

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = {
        "model": CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }

    print(f"[Claude] → prompt length: {len(prompt)} chars | max_tokens={max_tokens}")
    resp = requests.post(url, headers=headers, json=data, timeout=60)
    print(f"[Claude] ← status {resp.status_code}")

    if resp.status_code != 200:
        raise RuntimeError(f"Claude API error {resp.status_code}: {resp.text}")

    payload = resp.json()
    if "content" in payload and payload["content"]:
        return payload["content"][0]["text"]
    raise RuntimeError("Unexpected Claude response format.")


# ────────── Flask setup ─────────────────────────────────────────────────────

app = Flask(__name__, static_folder=str(BASE_DIR / "static"))
CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.after_request
def _add_cors_headers(resp):
    resp.headers.setdefault("Access-Control-Allow-Origin", "*")
    resp.headers.setdefault("Access-Control-Allow-Headers", "Content-Type,Authorization")
    resp.headers.setdefault("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
    return resp


# ────────── helper utilities ────────────────────────────────────────────────

def short_id() -> str:
    return uuid.uuid4().hex[:12]


def _get_uploaded_files(file_ids: list[str]):
    files = []
    for fid in file_ids:
        for path in TMP_DIR.glob(f"{fid}_*"):
            filename = path.name[len(fid) + 1 :]
            files.append({"id": fid, "filename": filename, "path": str(path)})
    return files


# ────────── API endpoints ───────────────────────────────────────────────────

# Static front‑end
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# ---- quick site analysis ---------------------------------------------------
@app.post("/api/analyse-website")
def analyse_website():
    website = request.json.get("website", "").strip()
    if not website:
        return jsonify(error="no website provided"), 400

    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
        resp = requests.get(website, headers=headers, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return jsonify(error=str(exc)), 500

    text = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)[:4000]

    prompt = textwrap.dedent(
        f"""\nAnalyze the business activities found on **{website}**.\nProvide a concise summary (≤100 words) that includes:\n1. Industry / sector\n2. Main business activities\n3. Products or services offered\n4. Notable insurance‑relevant risks\n\nExtracted text (truncated):\n{text}\n"""
    )

    try:
        summary = call_claude(prompt, temperature=0.3, max_tokens=500)
        return jsonify(ok=True, summary=summary)
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 500


# ---- file upload -----------------------------------------------------------
@app.post("/api/upload-file")
def upload_file():
    f = request.files.get("file")
    if not f:
        return jsonify(error="no file"), 400
    fid = short_id()
    f.save(TMP_DIR / f"{fid}_{f.filename}")
    return jsonify(id=fid, filename=f.filename)


# ---- big audit report ------------------------------------------------------

STYLE_AND_SCRIPT = textwrap.dedent('''\
    <style>
    /* (truncated for brevity — keep full block from original if needed) */
    body {font-family: "Segoe UI", Arial, sans-serif;}
    </style>
    <script>
    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(".pref-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const group = btn.closest(".pref-button-group");
                group.querySelectorAll(".pref-btn").forEach(b => {
                    b.classList.add("btn-unselected");
                    b.textContent = b.textContent.replace(" ✓", "");
                });
                btn.classList.remove("btn-unselected");
                if (!btn.textContent.includes("✓")) btn.textContent += " ✓";
            });
        });
    });
    </script>''')


def build_audit_prompt(website: str, file_ids: list[str]) -> str:
    today = datetime.date.today().strftime("%d %B %Y")
    file_details = _get_uploaded_files(file_ids)
    file_names = [f["filename"] for f in file_details]
    file_list = "\n".join(f"- {name}" for name in file_names) or "No documents uploaded"

    return textwrap.dedent(
        f'''\
        You are an expert UK commercial-insurance broker with 30+ years' experience.

        Create a **single stand‑alone HTML document** following the JORO framework.

        ━━━━━━━━━━  METADATA  ━━━━━━━━━━
        Website: {website}
        Uploaded documents: {file_list}
        Date: {today}

        ━━━━━━━━━━  CONTENT  ━━━━━━━━━━
        1. OVERVIEW
           • Summarise typical insurance coverages for this industry
           • Explain WHY each coverage exists (no jargon)

        2. COVERAGE TABLE
           • Columns: Coverage | Category | Claim scenario | How to claim | Annual cost range
           • Include preference buttons under each row (Essential / Interested / Not Interested)

        3. RED FLAGS & REAL‑LIFE SCENARIOS
           • Identify potential gaps and cite real claim examples

        4. RECOMMENDED TESTS & CERTIFICATES
           • List relevant certifications and potential premium savings

        5. BENEFITS OF ADDITIONAL STEPS
           • Financial, operational, and competitive advantages

        ━━━━━━━━━━  DESIGN  ━━━━━━━━━━
        • Table header background: #709fcc; white text
        • Colour tokens: #4fb57d (green), #f49547 (orange), #ef6460 (red), #B22222 (deep‑red)
        • Use <h2> for main sections, <h3> with icons for subsections

        Inject the following style & script block into the <head>:
        {STYLE_AND_SCRIPT}

        Return ONLY valid HTML (no markdown fences).
        '''
    )


@app.post("/api/generate-audit")
def generate_audit():
    data = request.get_json(force=True)
    website = data.get("website", "").strip()
    file_ids = data.get("files", [])

    prompt = build_audit_prompt(website, file_ids)

    try:
        html = call_claude(prompt, temperature=0.4, max_tokens=4000)
        return jsonify(html=html)
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 500


# ---- CORS pre‑flight catch‑all --------------------------------------------
@app.route("/api/<path:_dummy>", methods=["OPTIONS"])
def _options(_dummy):
    return "", 200


# ────────── local development entrypoint ───────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
