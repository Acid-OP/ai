import os
import re
import json
from difflib import SequenceMatcher
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

with open("extracted_names.json", "r") as f:
    ETF_DATABASE = json.load(f)

# All possible options from the quiz
REGIONS = ["World (all regions)", "US Market", "Europe", "Asia-Pacific", "Emerging markets", 
           "Developed markets", "China", "Latin America", "Poland"]
SECTORS = ["Technology", "Fintech", "Healthcare", "Energy", "Real Estate", "Industrials",
           "Semiconductors", "Materials and Mining", "Consumer"]
TRENDS = ["AI", "Nuclear Energy", "Clean Energy", "Electric Vehicles", "Crypto", 
          "Cybersecurity", "Robotics", "Defense", "Biotech"]
BONDS = ["Treasury Bonds", "Corporate Bonds", "Total Bond Market"]
COMMODITIES = ["Gold", "Silver", "Palladium", "Platinum", "Uranium", "Oil", "Water"]


def parse_user_input(input_string: str) -> dict:
    """Parse the quiz result string into a profile dict"""
    
    profile = {
        "goal": "",
        "risk_behavior": "",
        "time_horizon": "",
        "amount": 5000,
        "regions": [],
        "sectors": [],
        "trends": [],
        "bonds": [],
        "commodities": []
    }
    
    lines = input_string.strip().split('\n')
    full_text = input_string.lower()
    
    # Parse Investment Goal
    if "grow them aggressively" in full_text or "grow aggressively" in full_text:
        profile["goal"] = "Grow them aggressively"
    elif "grow moderately" in full_text:
        profile["goal"] = "Grow moderately"
    elif "grow with caution" in full_text:
        profile["goal"] = "Grow with caution"
    elif "avoid losing money" in full_text:
        profile["goal"] = "Avoid losing money"
    
    # Parse Time Horizon
    if "1-3 year" in full_text or "1 to 3" in full_text:
        profile["time_horizon"] = "1-3 years"
    elif "3-5 year" in full_text or "3 to 5" in full_text:
        profile["time_horizon"] = "3-5 years"
    elif "6-10 year" in full_text or "6 to 10" in full_text:
        profile["time_horizon"] = "6-10 years"
    elif "10+ year" in full_text or "more than 10" in full_text:
        profile["time_horizon"] = "10+ years"
    
    # Parse Risk Behavior
    if "sell everything" in full_text:
        profile["risk_behavior"] = "I'd sell everything"
    elif "sell some" in full_text:
        profile["risk_behavior"] = "I'd sell some"
    elif "do nothing" in full_text:
        profile["risk_behavior"] = "I'll do nothing"
    elif "buy more" in full_text:
        profile["risk_behavior"] = "I'd buy more"
    
    # Parse Amount (look for Capital/Amount followed by dollar value)
    amount_match = re.search(r'(?:capital|amount)[:\s]*\$?([\d,]+(?:\.\d{2})?)', input_string, re.IGNORECASE)
    if amount_match:
        try:
            profile["amount"] = float(amount_match.group(1).replace(',', ''))
        except:
            pass
    
    # Parse Preferred Topics
    for region in REGIONS:
        if region.lower() in full_text:
            profile["regions"].append(region)
    
    for sector in SECTORS:
        if sector.lower() in full_text:
            profile["sectors"].append(sector)
    
    for trend in TRENDS:
        if trend.lower() in full_text:
            profile["trends"].append(trend)
    
    for bond in BONDS:
        if bond.lower() in full_text:
            profile["bonds"].append(bond)
    
    for commodity in COMMODITIES:
        if commodity.lower() in full_text:
            profile["commodities"].append(commodity)
    
    return profile


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fuzzy_match(name: str, threshold: float = 0.6) -> tuple[str | None, float]:
    name_normalized = normalize(name)
    best_match = None
    best_score = 0
    
    for etf in ETF_DATABASE:
        etf_normalized = normalize(etf)
        if name_normalized in etf_normalized or etf_normalized in name_normalized:
            return etf, 1.0
        score = SequenceMatcher(None, name_normalized, etf_normalized).ratio()
        if score > best_score:
            best_score = score
            best_match = etf
    
    if best_score >= threshold:
        return best_match, best_score
    return None, 0


def extract_etf_names(response_text: str) -> list[str]:
    etf_patterns = [
        r'([A-Za-z][A-Za-z0-9\s&\-\']+(?:UCITS|ETF)[A-Za-z0-9\s&\-\'\(\)]*)',
    ]
    found = set()
    for pattern in etf_patterns:
        matches = re.findall(pattern, response_text)
        for match in matches:
            clean = match.strip()
            if len(clean) > 15 and not clean.startswith("This ETF"):
                found.add(clean)
    return list(found)


def validate_portfolio_fuzzy(response_text: str) -> list[dict]:
    etf_names = extract_etf_names(response_text)
    results = []
    for name in etf_names:
        match, score = fuzzy_match(name)
        if match:
            results.append({
                "gemini_said": name,
                "matched_to": match,
                "score": score
            })
    return results


SYSTEM_PROMPT = """You are a UCITS-compliant portfolio advisor.

Recommend real UCITS ETFs. Be specific with full ETF names.

Rules:
- Maximum 7 ETFs
- Use full official ETF names
- No markdown tables

Response format:

Portfolio Overview

Total Capital: $[amount]
Risk Profile: [profile]
Time Horizon: [horizon]
Strategy: [one line]

Asset Allocation (7 ETFs)

Core Holdings ([X]%) - $[amount]

[Full ETF Name] - [X]% ($[amount])
- [Why this ETF]

Thematic Holdings ([X]%) - $[amount]

[Full ETF Name] - [X]% ($[amount])
- [Why this ETF]

Portfolio Characteristics

Equity/Bond Split: [X]% / [X]%
Expected Return: [X-X]%
Volatility: [Low/Medium/High]

Key Features

* [Feature 1]
* [Feature 2]
* [Feature 3]

Investment Rationale

[Why this portfolio fits their profile]

Rebalancing: [recommendation]
"""


def generate_portfolio(user_profile: dict) -> str:
    prompt = f"""Create a personalized UCITS portfolio:

Investment Goal: {user_profile.get('goal')}
Risk Behavior: "{user_profile.get('risk_behavior')}"
Time Horizon: {user_profile.get('time_horizon')}
Amount: ${user_profile.get('amount', 5000)}

Preferences:
- Regions: {', '.join(user_profile.get('regions', [])) or 'Any'}
- Sectors: {', '.join(user_profile.get('sectors', [])) or 'Any'}
- Trends: {', '.join(user_profile.get('trends', [])) or 'Any'}
- Bonds: {', '.join(user_profile.get('bonds', [])) or 'None'}
- Commodities: {', '.join(user_profile.get('commodities', [])) or 'None'}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"system_instruction": SYSTEM_PROMPT}
    )
    return response.text


def save_to_pdf(portfolio: str, profile: dict, validation: list, filename: str):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Page 1: User Input Summary
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "USER INPUT (Quiz Results)", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Parsed Profile:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, f"Goal: {profile.get('goal', 'N/A')}")
    pdf.multi_cell(0, 6, f"Time Horizon: {profile.get('time_horizon', 'N/A')}")
    pdf.multi_cell(0, 6, f"Risk Behavior: {profile.get('risk_behavior', 'N/A')}")
    pdf.multi_cell(0, 6, f"Amount: ${profile.get('amount', 0):,.2f}")
    pdf.multi_cell(0, 6, f"Regions: {', '.join(profile.get('regions', [])) or 'None'}")
    pdf.multi_cell(0, 6, f"Sectors: {', '.join(profile.get('sectors', [])) or 'None'}")
    pdf.multi_cell(0, 6, f"Trends: {', '.join(profile.get('trends', [])) or 'None'}")
    pdf.multi_cell(0, 6, f"Bonds: {', '.join(profile.get('bonds', [])) or 'None'}")
    pdf.multi_cell(0, 6, f"Commodities: {', '.join(profile.get('commodities', [])) or 'None'}")
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"ETF Validation ({len(validation)} matched in approved list):", ln=True)
    pdf.set_font("Arial", size=9)
    for r in validation:
        text = f"[{r['score']:.0%}] {r['matched_to']}"
        pdf.multi_cell(0, 5, text.encode('latin-1', 'replace').decode('latin-1'))
    
    # Page 2: Portfolio
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "GENERATED PORTFOLIO", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    for line in portfolio.split('\n'):
        line = line.replace('✓', '*').replace('✔', '*').replace('•', '*')
        clean_line = line.encode('latin-1', 'replace').decode('latin-1')
        if line.startswith(('Portfolio Overview', 'Asset Allocation', 'Core Holdings', 
                           'Thematic', 'Portfolio Characteristics', 'Key Features',
                           'Investment Rationale', 'Rebalancing')):
            pdf.set_font("Arial", "B", 11)
            pdf.ln(3)
            pdf.multi_cell(0, 6, clean_line)
            pdf.set_font("Arial", size=10)
        else:
            pdf.multi_cell(0, 5, clean_line)
    
    pdf.output(filename)
    print(f"Saved to {filename}")


def run_portfolio(user_input: str):
    """Generate portfolio from input string"""
    print("\n" + "-" * 60)
    print("PARSED PROFILE:")
    print("-" * 60)
    
    profile = parse_user_input(user_input)
    print(f"  Goal:         {profile['goal']}")
    print(f"  Time Horizon: {profile['time_horizon']}")
    print(f"  Risk Behavior: {profile['risk_behavior']}")
    print(f"  Amount:       ${profile['amount']:,.2f}")
    print(f"  Regions:      {', '.join(profile['regions']) or 'None'}")
    print(f"  Sectors:      {', '.join(profile['sectors']) or 'None'}")
    print(f"  Trends:       {', '.join(profile['trends']) or 'None'}")
    print(f"  Bonds:        {', '.join(profile['bonds']) or 'None'}")
    print(f"  Commodities:  {', '.join(profile['commodities']) or 'None'}")
    
    print("\n" + "=" * 60)
    print("GENERATING PORTFOLIO...")
    print("=" * 60 + "\n")
    
    response = generate_portfolio(profile)
    print(response.replace('✓', '*').replace('✔', '*'))
    
    print("\n" + "-" * 60)
    print("VALIDATION:")
    print("-" * 60)
    
    fuzzy_results = validate_portfolio_fuzzy(response)
    print(f"  {len(fuzzy_results)} ETFs matched in approved list:")
    for r in fuzzy_results:
        print(f"    [{r['score']:.0%}] {r['matched_to'][:50]}...")
    
    save_to_pdf(response, profile, fuzzy_results, "portfolio.pdf")
    return profile, response, fuzzy_results


def main():
    import sys
    
    # Test mode with sample input
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("=" * 60)
        print("RUNNING TEST WITH SAMPLE INPUT")
        print("=" * 60)
        
        sample_input = """Investment Goals: Grow with caution
Withdraw Expectation: In 6-10 years
Scenario Question Answer: I'll do nothing
Portfolio Committed Capital: $5,000.00
Preferred Topics: World (all regions), Emerging markets, Asia-Pacific, Latin America, Healthcare, Technology, Industrials, Nuclear Energy, Electric Vehicles, Biotech, Corporate Bonds, Total Bond Market, Palladium, Uranium, Water"""
        
        print("\nSAMPLE INPUT:")
        print(sample_input)
        run_portfolio(sample_input)
        return
    
    # Interactive mode
    print("=" * 60)
    print("PORTFOLIO GENERATOR")
    print("=" * 60)
    print("\nPaste the quiz results (press Enter twice when done):\n")
    
    lines = []
    while True:
        line = input()
        if line == "":
            if lines and lines[-1] == "":
                break
            lines.append(line)
        else:
            lines.append(line)
    
    user_input = '\n'.join(lines)
    run_portfolio(user_input)


if __name__ == "__main__":
    main()
