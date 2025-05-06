# prompts.py - Contains all the prompts used in the application
import datetime

def get_analysis_prompt(website, extracted_text):
    """
    Generate a prompt for analyzing a website
    """
    return f"""Analyze the business activities found on **{website}** based on the extracted text.

1. Identify the industry/sector 
2. Determine the main business activities
3. Note any products or services mentioned
4. Identify any potential insurance-related risks
5. Summarize this all in ONE concise paragraph (max 100 words)

Extracted text (truncated):
{extracted_text}
"""

def get_audit_prompt(website, file_ids):
    """
    Generate a comprehensive prompt for the insurance audit report
    """
    today = datetime.date.today().strftime("%d %B %Y")
    
    return f"""You are an expert UK commercial insurance broker with over 30 years of experience. 
    Produce a **single, stand-alone HTML document** that follows the exact structure and formatting 
    provided in the example below.

    Your task is to create a complete insurance review for: {website}

    ━━━━━━━━━━  FORMATTING REQUIREMENTS  ━━━━━━━━━━
    • You MUST follow the exact HTML structure in the example below
    • Use all provided icon URLs for the section headings exactly as shown
    • Ensure all CSS styling is included exactly as provided
    • Make sure preference buttons functionality works with JavaScript
    • Ensure responsive table formatting with proper column widths

    ━━━━━━━━━━  SECTION ICONS  ━━━━━━━━━━
    Use these exact image URLs for section icons:
    • Overview icon: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb25470b8415a5795ed69/1743762005158/Icon+-+magnifying+glass.png
    • Coverage table icon: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2548246ac491eae87ce/1743762005156/Icon+-+Coverage+table.png
    • Red flags icon: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2540b0ebe5af8f8b121/1743762005078/Icon+-+red+flag.png
    • Test certificates icon: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2547bec2273aed7c754/1743762005181/Icon+-+test+certificates.png
    • Benefits icon: https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb254dc69af7a4b2ad623/1743762005197/Icon+-+benefits.png

    ━━━━━━━━━━  CONTENT REQUIREMENTS  ━━━━━━━━━━
    1. OVERVIEW
       • Analyze the business from {website} to determine industry and operation type
       • Provide a concise overview of standard insurance coverages for this business type
       • Include typical policies: Public Liability, Product Liability, Stock & Contents, 
         Employers' Liability, Business Interruption, etc.
       • Explain WHY each coverage exists (not just what it covers)
       • Use clear, direct language without jargon

    2. COVERAGE TABLE
       • Create a DETAILED 5-column table with exact styling from the example
       • Columns must be: Coverage Type, Category (Essential/Peace-of-Mind/Optional), 
         Client-specific claim scenarios, How to claim (timeline & cost expectations), Annual Cost
       • Add preference buttons under each coverage row with proper styling and functionality
       • Use color coding exactly as shown in the example

    3. RED FLAGS & REAL-LIFE SCENARIOS
       • Identify potential insurance gaps based on the business type
       • Provide ACTUAL documented claim examples (both successful and unsuccessful)
       • For each example, explain what helped the claim succeed or why it failed
       • Include time and financial consequences

    4. RECOMMENDED TESTS & CERTIFICATES BY PRODUCT/SERVICE
       • Break down the client's products/services into categories
       • For each category, list relevant certifications with styling as shown in the example
       • Explain how each certificate strengthens claims
       • Provide SPECIFIC potential premium savings (e.g., "Up to 10% discount")

    5. BENEFITS OF ADDITIONAL STEPS
       • Summarize financial benefits (premium reductions, lower excess/deductibles)
       • Explain operational advantages (faster claims, fewer disputes)
       • Highlight competitive advantages specific to this industry

    ━━━━━━━━━━  EXAMPLE HTML TEMPLATE TO FOLLOW EXACTLY  ━━━━━━━━━━
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Joro High Level Insurance Review &amp; Recommendations</title>
      <style>
        /* Global Styles – let your site CSS control fonts/colors */
        body {{
          margin: 20px;
          line-height: 1.6;
          font-family: inherit;
          color: inherit;
        }}
        h1, h2, h3, h4, h5 {{
          margin-top: 1.2em;
          margin-bottom: 0.6em;
          font-weight: inherit;
          /* Remove forced color so site defaults apply */
          color: inherit;
        }}
        p, ul, ol, table {{
          margin-bottom: 1em;
        }}
        ul, ol {{
          padding-left: 20px;
        }}

        /* Heading Icon Style – doubled to 48px */
        .heading-icon {{
          width: 48px;
          vertical-align: middle;
          margin-right: 8px;
        }}

        /* Table Styles */
        table {{
          border-collapse: collapse;
          width: 100%;
          margin-bottom: 20px;
        }}
        table, th, td {{
          border: 1px solid #ddd;
        }}
        th, td {{
          padding: 6px 8px;
          text-align: left;
          vertical-align: top;
        }}
        /* Updated table header styles */
        th {{
          background-color: #709fcc;
          color: #fff;
        }}
        /* Bold for first two columns in coverage table */
        table.coverage-table tbody tr td:nth-child(1),
        table.coverage-table tbody tr td:nth-child(2) {{
          font-weight: bold;
        }}
        col.group-col1 {{ width: 15%; }}
        col.group-col2 {{ width: 30%; }}
        col.group-col3 {{ width: 25%; }}
        col.group-col4 {{ width: 25%; }}
        col.group-col5 {{ width: 5%; }}

        /* Category Color Styles & Icons */
        .dark-red {{ color: #8B0000; }}
        .mid-red {{ color: #B22222; }}
        .orange-text {{ color: #FF4500; }}
        .green-text {{ color: #008000; }}
        .warning-icon::before {{ content: "⚠️ "; }}
        .thumbs-up-icon::before {{ content: "👍 "; }}
        .tick-icon {{ margin-left: 4px; }}

        /* Preference Buttons */
        .preference-buttons {{ margin-top: 0.5em; }}
        .pref-btn {{
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
          background-color: #D3D3D3 !important;
          color: #555 !important;
        }}

        /* Upload-to-profile Button */
        .upload-profile-btn {{
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
        }}
        .upload-profile-btn:hover {{
          background-color: #43a16b;
        }}
      </style>
    </head>
    <body>
      <!-- Header -->
      <h3>
        Joro High Level Insurance Review & Recommendations
      </h3>
      <p>
        <strong>Prepared by:</strong> JORO<br>
        <strong>For:</strong> [COMPANY NAME]<br>
        <strong>Date:</strong> {today}
      </p>

      <!-- Section 1: Overview -->
      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb25470b8415a5795ed69/1743762005158/Icon+-+magnifying+glass.png" alt="Overview Icon" class="heading-icon">
        1. OVERVIEW
      </h4>
      [YOUR CONTENT HERE]

      <!-- Section 2: Coverage Table -->
      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2548246ac491eae87ce/1743762005156/Icon+-+Coverage+table.png" alt="Coverage Table Icon" class="heading-icon">
        2. COVERAGE TABLE
      </h4>
      <table class="coverage-table">
        <colgroup>
          <col class="group-col1">
          <col class="group-col2">
          <col class="group-col3">
          <col class="group-col4">
          <col class="group-col5">
        </colgroup>
        <thead>
          <tr>
            <th><strong>Coverage Type</strong></th>
            <th><strong>Category</strong></th>
            <th>Client-specific claim scenarios</th>
            <th>How to claim (timeline & cost expectations)</th>
            <th>Annual Cost</th>
          </tr>
        </thead>
        <tbody>
          <!-- Row template: copy and modify for each coverage type -->
          <tr>
            <td>Coverage Name</td>
            <td>
              <p class="dark-red warning-icon">Category description</p>
              <p><strong>Preference for new policy</strong></p>
              <div class="preference-buttons">
                <button class="pref-btn btn-essential" data-label="Essential" data-selected="false">Essential</button>
                <button class="pref-btn btn-interested" data-label="Interested / optional" data-selected="false">Interested / optional</button>
                <button class="pref-btn btn-notInterested" data-label="Not interested" data-selected="false">Not interested</button>
              </div>
            </td>
            <td>Specific claim scenario for this industry</td>
            <td>Detailed claiming process</td>
            <td>Annual cost range</td>
          </tr>
        </tbody>
      </table>

      <!-- Section 3: Red Flags & Real-Life Scenarios -->
      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2540b0ebe5af8f8b121/1743762005078/Icon+-+red+flag.png" alt="Red Flag Icon" class="heading-icon">
        3. RED FLAGS &amp; REAL-LIFE SCENARIOS
      </h4>
      [YOUR CONTENT HERE]

      <!-- Section 4: Recommended Tests & Certificates -->
      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2547bec2273aed7c754/1743762005181/Icon+-+test+certificates.png" alt="Test Certificates Icon" class="heading-icon">
        4. RECOMMENDED TESTS &amp; CERTIFICATES
      </h4>
      [YOUR CONTENT HERE]

      <!-- Section 5: Benefits -->
      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb254dc69af7a4b2ad623/1743762005197/Icon+-+benefits.png" alt="Benefits Icon" class="heading-icon">
        5. BENEFITS OF ADDITIONAL STEPS
      </h4>
      [YOUR CONTENT HERE]

      <!-- Script for toggling preference buttons -->
      <script>
        document.addEventListener("DOMContentLoaded", function() {{
          const preferenceGroups = document.querySelectorAll('.preference-buttons');

          preferenceGroups.forEach(group => {{
            const buttons = group.querySelectorAll('.pref-btn');
            buttons.forEach(btn => {{
              btn.addEventListener('click', function() {{
                // Clear any existing selections in this group
                buttons.forEach(sibling => {{
                  sibling.classList.remove('btn-unselected');
                  sibling.innerHTML = sibling.getAttribute('data-label');
                  sibling.dataset.selected = "false";
                }});

                // Mark clicked button as selected and add tick
                btn.dataset.selected = "true";
                btn.innerHTML = btn.getAttribute('data-label') + ' <span class="tick-icon">✓</span>';

                // Grey out the other buttons
                buttons.forEach(sibling => {{
                  if (sibling !== btn) {{
                    sibling.classList.add('btn-unselected');
                  }}
                }});
              }});
            }});
          }});
        }});
      </script>
    </body>
    </html>

    ━━━━━━━━━━  IMPORTANT INSTRUCTIONS  ━━━━━━━━━━
    • Replace [COMPANY NAME] with the actual company name extracted from the website
    • Replace [YOUR CONTENT HERE] with industry-specific content as per requirements
    • Ensure ALL styling, HTML structure, and JavaScript functionality is preserved
    • Use the exact icon URLs provided
    • Do not omit any sections or elements from the template
    • Maintain color coding as per template: #4fb57d green (Essential), #f49547 orange (Peace-of-Mind), #ef6460 red (Optional)

    The final document must be standalone, fully functional and look exactly like the example, but with content specific to the business at {website} and industry.
    """
