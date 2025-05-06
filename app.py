# app.py  ──────────────────────────────────────────────────────────
import os, uuid, tempfile, pathlib, datetime, requests, json
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

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
    """Call Claude API with the provided prompt"""
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-haiku-20240307",  # Using the latest Haiku model
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        print(f"Sending request to Claude API with prompt length: {len(prompt)}")
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

    # Define the prompt for Claude
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

# ────────── Define get_audit_prompt function here 
def get_audit_prompt(website, file_ids):
    """
    Generate a comprehensive prompt for the insurance audit report
    """
    today = datetime.date.today().strftime("%d %B %Y")
    file_details = get_uploaded_files(file_ids)
    file_names = [f["filename"] for f in file_details]
    file_info = "\n".join([f"- {f}" for f in file_names]) if file_names else "No documents uploaded"
    
    return f"""
    You are an expert UK commercial-insurance broker and business
    advisor with over 30 years of experience. Produce a **single, stand-alone HTML document** 
    that follows the JORO framework below.

    ━━━━━━━━━━  DESIGN REQUIREMENTS  ━━━━━━━━━━
    • Inject the full <style> block shown at the end of this prompt.
    • Use these heading icon URLs:  
      • https://storage.googleapis.com/joro-audit-icons/Icon+-+magnifying+glass.png  
      • https://storage.googleapis.com/joro-audit-icons/Icon+-+Coverage+table.png  
      • https://storage.googleapis.com/joro-audit-icons/Icon+-+red+flag.png  
      • https://storage.googleapis.com/joro-audit-icons/Icon+-+test+certificates.png  
      • https://storage.googleapis.com/joro-audit-icons/Icon+-+benefits.png  
    • Table header background: #709fcc with white text
    • Add preference-button clusters (3 pills) with classes:
      .pref-btn btn-essential / btn-interested / btn-notInterested
    • Ensure interactive button functionality that adds ✓ when selected and toggles the btn-unselected class
    • Colour tokens:  
      #4fb57d green (Essential/Recommended), 
      #f49547 orange (Peace of Mind/Optional), 
      #ef6460 red (Warnings/Red Flags), 
      #B22222 deep-red (Critical Issues)
    • Use <h2> for main sections, <h3> for subsections with icons, <h4> for minor headings

    ━━━━━━━━━━  CONTENT REQUIREMENTS  ━━━━━━━━━━
    1. OVERVIEW
       • Analyze the business from {website} to determine industry and operation type
       • Provide a concise overview of standard insurance coverages for this business type
       • Include typical policies: Public Liability, Product Liability, Stock & Contents, 
         Employers' Liability, Business Interruption, etc.
       • Explain WHY each coverage exists (not just what it covers)
       • Use clear, direct language without jargon or phrases like "plain English"

    2. COVERAGE TABLE
       • Create a DETAILED 5-column table:
         - Coverage Type 
         - Category (Essential/Peace-of-Mind/Optional)
         - Client-specific claim scenarios relevant to THIS business
         - How to claim (timeline & cost expectations)
         - Annual Cost (estimated range if not in documents)
       • Add preference buttons under each coverage row to let client mark as:
         Essential / Interested / Not Interested

    3. RED FLAGS & REAL-LIFE SCENARIOS
       • Identify potential insurance gaps based on the business type
       • Provide ACTUAL documented claim examples (successful and unsuccessful)
       • For each example:
         - Explain what helped the claim succeed (or why it failed)
         - Detail the time and financial consequences
         - Connect directly to the client's business situation
       • Use real industry examples, not hypotheticals

    4. RECOMMENDED TESTS & CERTIFICATES BY PRODUCT/SERVICE
       • Break down the client's products/services into categories
       • For each category:
         - List relevant certifications (ISO, BS EN, CE marking, REACH, etc.)
         - Explain how each certificate strengthens claims
         - Provide SPECIFIC potential premium savings (e.g., "Up to 10% discount")
       • Create a table linking product categories to recommended certifications
       • Include estimated savings percentage for each recommendation

    5. BENEFITS OF ADDITIONAL STEPS
       • Summarize financial benefits (premium reductions, lower excess/deductibles)
       • Explain operational advantages (faster claims, fewer disputes)
       • Highlight competitive advantages (market trust, improved reputation)
       • Show how risk reduction creates long-term value

    ━━━━━━━━━━  METADATA  ━━━━━━━━━━
    • Add report header:  
      "Joro High Level Insurance Review & Recommendations"  
      Prepared by JORO  
      For: <extract organization name from {website}>  
      Date: {today}

    • When referencing uploaded documents, cite the specific filename
    • Uploaded documents: {file_info}

    ━━━━━━━━━━  STYLE BLOCK  ━━━━━━━━━━
    <style>
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        h1, h2, h3, h4 {
            color: #3a5a7c;
            margin-top: 1.5em;
        }
        
        h1 {
            font-size: 28px;
            text-align: center;
            margin-bottom: 5px;
        }
        
        h2 {
            font-size: 24px;
            border-bottom: 2px solid #709fcc;
            padding-bottom: 10px;
        }
        
        h3 {
            font-size: 20px;
            display: flex;
            align-items: center;
        }
        
        h3 img {
            height: 24px;
            margin-right: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th {
            background-color: #709fcc;
            color: white;
            padding: 10px;
            text-align: left;
        }
        
        td {
            padding: 10px;
            border: 1px solid #ddd;
        }
        
        tr:nth-child(even) {
            background-color: #f2f7fd;
        }
        
        .highlight-green {
            color: #4fb57d;
            font-weight: bold;
        }
        
        .highlight-orange {
            color: #f49547;
            font-weight: bold;
        }
        
        .highlight-red {
            color: #ef6460;
            font-weight: bold;
        }
        
        .highlight-deep-red {
            color: #B22222;
            font-weight: bold;
        }
        
        .metadata {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .metadata p {
            margin: 5px 0;
        }
        
        .pref-button-group {
            display: flex;
            gap: 10px;
            margin: 10px 0;
        }
        
        .pref-btn {
            padding: 5px 15px;
            border-radius: 20px;
            border: none;
            color: white;
            font-weight: bold;
            cursor: pointer;
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
            opacity: 0.6;
        }
        
        .section-icon {
            width: 40px;
            height: 40px;
            margin-right: 15px;
        }
    </style>

    <script>
        // Add event listeners to all preference buttons
        document.addEventListener('DOMContentLoaded', function() {
            const prefButtons = document.querySelectorAll('.pref-btn');
            
            prefButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Find the button group
                    const group = this.closest('.pref-button-group');
                    
                    // Remove 'selected' class from all buttons in the group
                    group.querySelectorAll('.pref-btn').forEach(btn => {
                        btn.classList.add('btn-unselected');
                        // Remove check mark
                        btn.textContent = btn.textContent.replace(' ✓', '');
                    });
                    
                    // Add 'selected' to the clicked button
                    this.classList.remove('btn-unselected');
                    // Add check mark
                    if (!this.textContent.includes('✓')) {
                        this.textContent += ' ✓';
                    }
                });
            });
        });
    </script>"""
    """

# ────────── big report
@app.post("/api/generate-audit")
def generate_audit():
    data = request.get_json(force=True)
    website = data.get("website", "").strip()
    file_ids = data.get("files", [])            # may be []
    today = datetime.date.today().strftime("%d %B %Y")
    
    print(f"Generating audit for website: {website} with file IDs: {file_ids}")
    
    # Get file details
    file_details = get_uploaded_files(file_ids)
    file_names = [f["filename"] for f in file_details]
    file_info = "\n".join([f"- {f}" for f in file_names]) if file_names else "No documents uploaded"
    
    # First, try to get content from the website to determine industry
    industry_analysis = "Unable to determine specific industry details."
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        r = requests.get(website, timeout=20, headers=headers)
        r.raise_for_status()
        text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)[:6000]
        
        # Create industry analysis prompt
        industry_prompt = "Analyze the following text extracted from the website " + website + " and determine:\n"
        industry_prompt += "1. The precise industry or business sector (be specific)\n"
        industry_prompt += "2. The main business activities\n"
        industry_prompt += "3. The important risk areas relevant to insurance\n"
        industry_prompt += "4. The company name\n\n"
        industry_prompt += "Be very specific about the industry. For example, if it's construction, specify what type (residential, commercial, etc.).\n\n"
        industry_prompt += "Extracted text:\n" + text
        
        # Get industry analysis
        industry_analysis = call_claude(industry_prompt, temperature=0.2, max_tokens=600)
        print(f"Industry analysis: {industry_analysis[:100]}...")
        
    except Exception as exc:
        print(f"Industry analysis error: {exc}")
    
    # Define the audit prompt
    AUDIT_PROMPT = f"""
    You are an expert UK commercial insurance broker with over 30 years of experience. 
    
    I need you to create a comprehensive insurance review and recommendation document for:
    
    Website: {website}
    Uploaded insurance documents: {file_info}
    
    Industry analysis based on website content:
    {industry_analysis}
    
    Create a complete, professional HTML document with the following structure:
    
    1. OVERVIEW
    - Summarize typical insurance coverage for this specific industry (Public/Product Liability, Stock & Contents, Employers' Liability, Business Interruption, etc.)
    - Use clear, professional language
    - Be specific to the type of business/industry identified
    
    2. COVERAGE TABLE
    - Create a 5-column table with:
      - Coverage Type 
      - Category (Essential/Peace-of-Mind/Optional)
      - Industry-specific claim scenarios
      - How to claim (timeline & cost expectations)
      - Annual Cost (estimated range)
    - Make all examples SPECIFIC to the identified industry
    
    3. RED FLAGS & REAL-LIFE SCENARIOS
    - Identify potential insurance gaps based on the specific business type
    - Provide REAL industry-specific claim examples (both successful and unsuccessful)
    - For each example, explain what helped the claim succeed or why it failed
    - Include time and financial consequences
    
    4. RECOMMENDED TESTS & CERTIFICATES
    - List industry-specific certifications relevant to this business type
    - Explain how each certificate strengthens claims
    - Include potential premium savings percentages
    
    5. BENEFITS OF ADDITIONAL STEPS
    - Financial benefits (premium reductions, lower excess/deductibles)
    - Operational advantages (faster claims, fewer disputes)
    - Competitive advantages specific to this industry
    
    FORMAT REQUIREMENTS:
    - Title: "Joro High Level Insurance Review & Recommendations"
    - Header info: "Prepared by JORO" + "For: [Company Name]" + "Date: {today}"
    - Use professional styling with a clean look
    - Include preference buttons under each coverage item
    - Table header background color: #709fcc with white text
    - Color scheme: #4fb57d green, #f49547 orange, #ef6460 red, #B22222 deep-red
    
    IMPORTANT: All examples, scenarios, and recommendations MUST be very specific to the exact industry of this business.
    DO NOT use generic examples. DO NOT mention pets or pet stores unless this is actually a pet-related business.
    
    Return ONLY valid HTML (no markdown or code blocks).
    """
    
    try:
        # Call Claude API with a max_tokens value within Claude's limits
        html = call_claude(AUDIT_PROMPT, temperature=0.4, max_tokens=4000)
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
