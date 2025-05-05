# app.py
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()                                    # reads the .env file in this folder

import openai
openai.api_key = os.getenv("OPENAI_API_KEY")     # <-- pulls your key out of .env

from flask import Flask, request, jsonify, send_from_directory

# ---------------------------------------------------------------------------
#  Flask setup
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, static_folder=str(BASE_DIR / "static"))

# ---------------------------------------------------------------------------
#  Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    # serves static/index.html (your Code 1 page)
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/generate-audit", methods=["POST"])
def generate_audit():
    """
    Expects JSON like {"website": "https://example.com"}
    Returns {"html": "<full Code-2 style HTML>"} that the browser will open.
    """
    data = request.get_json(force=True)
    website = data.get("website", "").strip()

    # -------- Prompt -------------------------------------------------------
    # Paste your full Prompt 1 text below, *inside the triple quotes*.
    # You can keep a {{WEBSITE}} placeholder that we fill with the user's URL.
    prompt = f"""
Act as an expert insurance broker …
(Website provided: {website})
"""
    # ----------------------------------------------------------------------

    completion = openai.ChatCompletion.create(
        model="o3-chat-completion",   # OpenAI o3 model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048               # adjust if needed
    )

    html_report = completion.choices[0].message.content
    return jsonify({"html": html_report})


# ---------------------------------------------------------------------------
#  Run locally:  python3 app.py
#  (Render will launch with gunicorn app:app)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
