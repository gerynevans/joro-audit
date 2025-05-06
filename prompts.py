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
    
    return f"""You are an expert UK commercial-insurance broker and business
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

• When referencing uploaded documents (file IDs: {file_ids}), cite the specific filename

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
</script>
"""