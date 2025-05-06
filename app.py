# app.py  ──────────────────────────────────────────────────────────
import os, uuid, tempfile, pathlib, datetime, requests, json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from prompts import get_audit_prompt  # Import just the audit prompt function

# ────────── ENV / PATHS
load_dotenv()
CLAUDE_KEY = os.getenv("ANTHROPIC_API_KEY")

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

# ────────── Claude API integration
def call_claude(prompt, temperature=0.3, max_tokens=4000):
    """Call Claude API with the provided prompt using direct API call"""
    try:
        print(f"Sending request to Claude API with prompt length: {len(prompt)}")
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": CLAUDE_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": "claude-3-haiku-20240307",  # Using a model that should be available
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        print(f"Sending direct API request to Claude with model: {data['model']}")
        response = requests.post(url, headers=headers, json=data)
        print(f"Claude API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return f"Error: Claude API returned status code {response.status_code}"
        
        result = response.json()
        
        # Handle the response structure correctly
        if "content" in result and len(result["content"]) > 0:
            return result["content"][0]["text"]
        else:
            print(f"Unexpected response structure: {result}")
            return "Error: Unexpected response format from Claude API"
            
    except Exception as e:
        print(f"Claude API error: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Response text: {response.text}")
        raise

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

    # Define the prompt directly instead of importing it
    prompt = f"""
    Analyze the business activities found on **{website}** based on the extracted text.
    
    Provide a concise summary (max 100 words) that includes:
    1. The industry/sector
    2. Main business activities
    3. Products or services offered
    4. Notable insurance-relevant risks for this type of business
    
    Extracted text (truncated):
    {text}
    """
    
    try:
        # Call Claude API
        summary = call_claude(prompt, temperature=0.3, max_tokens=500)
        print(f"Successfully generated summary: {summary[:50]}...")
        return jsonify(ok=True, summary=summary)
    except Exception as exc:
        print(f"Claude API Error: {exc}")
        return jsonify(error=f"Claude API error: {exc}"), 500

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
    
    print(f"Generating audit for website: {website} with file IDs: {file_ids}")
    
    # Get file details
    file_details = get_uploaded_files(file_ids)
    
    # Get the audit prompt from prompts.py
    prompt = get_audit_prompt(website, file_ids)
    
    try:
        # Call Claude API
        html = call_claude(prompt, temperature=0.4, max_tokens=10000)
        print(f"Successfully generated audit HTML (length: {len(html)})")
        return jsonify(html=html)
    except Exception as exc:
        print(f"Claude API Error: {exc}")
        return jsonify(error=f"Claude API error: {exc}"), 500

# ────────── handle OPTIONS requests for audit
@app.route('/api/generate-audit', methods=['OPTIONS'])
def handle_options_audit():
    return '', 200

# ────────── local dev
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
