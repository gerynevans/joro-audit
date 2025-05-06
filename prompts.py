def get_audit_prompt(website, file_ids):
    """
    Generate a comprehensive prompt for the insurance audit report
    """
    today = datetime.date.today().strftime("%d %B %Y")
    
    return f"""You are an expert UK commercial insurance broker with over 30 years of experience. 
    Create an HTML document that EXACTLY matches the formatting and functionality of the example.

    Website to analyze: {website}
    
    CRITICAL FORMATTING REQUIREMENTS:
    1. Create a COMPLETE, standalone HTML document with ALL required styling and JavaScript
    2. Use EXACTLY the same HTML structure, CSS styling, and JavaScript as shown in the example
    3. Include ALL interactive buttons with working JavaScript for toggling selection
    4. Use the EXACT same section headings with icons as shown in the example
    5. Make sure the table formatting matches EXACTLY, with proper columns and styling
    6. Include a COMPLETE and thorough analysis for ALL sections - don't cut any section short
    
    COPY THIS HTML STRUCTURE AND STYLING EXACTLY - DO NOT MODIFY OR SIMPLIFY IT:
    
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>Joro High Level Insurance Review &amp; Recommendations</title>
      <style>
        /* Global Styles */
        body {{
          margin: 20px;
          line-height: 1.6;
          font-family: Arial, sans-serif;
          color: #333;
        }}
        h1, h2, h3, h4, h5 {{
          margin-top: 1.2em;
          margin-bottom: 0.6em;
          font-weight: bold;
          color: #3a5a7c;
        }}
        p, ul, ol, table {{
          margin-bottom: 1em;
        }}
        ul, ol {{
          padding-left: 20px;
        }}

        /* Heading Icon Style */
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
        th {{
          background-color: #709fcc;
          color: #fff;
        }}
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
      <h3>
        Joro High Level Insurance Review & Recommendations
      </h3>
      <p>
        <strong>Prepared by:</strong> JORO<br>
        <strong>For:</strong> [COMPANY NAME]<br>
        <strong>Date:</strong> {today}
      </p>

      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb25470b8415a5795ed69/1743762005158/Icon+-+magnifying+glass.png" alt="Overview Icon" class="heading-icon">
        1. OVERVIEW
      </h4>
      
      <!-- YOUR OVERVIEW CONTENT WILL GO HERE -->

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
            <th>Industry-specific claim scenarios</th>
            <th>How to claim (timeline & cost expectations)</th>
            <th>Annual Cost</th>
          </tr>
        </thead>
        <tbody>
          <!-- COVERAGE ROWS WILL GO HERE -->
        </tbody>
      </table>

      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2540b0ebe5af8f8b121/1743762005078/Icon+-+red+flag.png" alt="Red Flag Icon" class="heading-icon">
        3. RED FLAGS &amp; REAL-LIFE SCENARIOS
      </h4>
      
      <!-- RED FLAGS CONTENT WILL GO HERE -->

      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb2547bec2273aed7c754/1743762005181/Icon+-+test+certificates.png" alt="Test Certificates Icon" class="heading-icon">
        4. RECOMMENDED TESTS &amp; CERTIFICATES
      </h4>
      
      <!-- CERTIFICATES CONTENT WILL GO HERE -->

      <h4>
        <img src="https://static1.squarespace.com/static/67d9cdeade7c0a44db4c187f/t/67efb254dc69af7a4b2ad623/1743762005197/Icon+-+benefits.png" alt="Benefits Icon" class="heading-icon">
        5. BENEFITS OF ADDITIONAL STEPS
      </h4>
      
      <!-- BENEFITS CONTENT WILL GO HERE -->

      <script>
        document.addEventListener("DOMContentLoaded", function() {{
          const preferenceGroups = document.querySelectorAll('.preference-buttons');

          preferenceGroups.forEach(group => {{
            const buttons = group.querySelectorAll('.pref-btn');
            buttons.forEach(btn => {{
              btn.addEventListener('click', function() {{
                // Clear any existing selections in this group
                buttons.forEach(sibling => {{
                  sibling.classList.add('btn-unselected');
                  sibling.innerHTML = sibling.getAttribute('data-label');
                  sibling.dataset.selected = "false";
                }});

                // Mark clicked button as selected and add tick
                this.classList.remove('btn-unselected');
                this.dataset.selected = "true";
                this.innerHTML = this.getAttribute('data-label') + ' <span class="tick-icon">✓</span>';
              }});
            }});
          }});
        }});
      </script>
    </body>
    </html>

    FOR EACH COVERAGE TYPE, INCLUDE A TABLE ROW WITH THIS EXACT FORMAT (WITH WORKING BUTTONS):
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

    YOUR CONTENT SHOULD BE SPECIFIC TO THE {website} BUSINESS AND INCLUDE:
    
    1. Detailed overview of insurance needs for the specific industry
    2. At least 6-10 coverage types with detailed scenarios specific to the business
    3. Red flags specific to the business with real-life examples
    4. Detailed certificates and tests applicable to this industry with premium reductions
    5. Comprehensive benefits section with financial, operational and competitive advantages
    
    DO NOT abbreviate or cut short any section. Create a COMPLETE report with ALL sections fully detailed.
    """
