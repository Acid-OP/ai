"""
Portfolio Generator - Main Entry Point
Paste quiz results, press Enter, get JSON + PDF in output/portfolio_X/
"""

import os
import re
import json
from difflib import SequenceMatcher
from dotenv import load_dotenv
from google import genai
from portfolio_json_generator import generate_portfolio_json
from pdf_generator import generate_pdf

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(BASE_DIR, 'utils')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

with open(os.path.join(UTILS_DIR, "extracted_names.json"), "r") as f:
    ETF_DATABASE = json.load(f)

# Quiz options for parsing user input
REGIONS = ["World (all regions)", "US Market", "Europe", "Asia-Pacific", "Emerging markets", 
           "Developed markets", "China", "Latin America", "Poland"]
SECTORS = ["Technology", "Fintech", "Healthcare", "Energy", "Real Estate", "Industrials",
           "Semiconductors", "Materials and Mining", "Consumer"]
TRENDS = ["AI", "Nuclear Energy", "Clean Energy", "Electric Vehicles", "Crypto", 
          "Cybersecurity", "Robotics", "Defense", "Biotech"]
BONDS = ["Treasury Bonds", "Corporate Bonds", "Total Bond Market"]
COMMODITIES = ["Gold", "Silver", "Palladium", "Platinum", "Uranium", "Oil", "Water"]


def get_next_portfolio_number():
    """Get next portfolio folder number (portfolio_1, portfolio_2, etc.)"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        return 1
    existing = [d for d in os.listdir(OUTPUT_DIR) if d.startswith('portfolio_')]
    if not existing:
        return 1
    numbers = []
    for d in existing:
        try:
            numbers.append(int(d.split('_')[1]))
        except:
            pass
    return max(numbers) + 1 if numbers else 1


def parse_user_input(input_string: str) -> dict:
    """Parse quiz result string into structured profile dict"""
    profile = {
        "goal": "", "risk_behavior": "", "time_horizon": "", "amount": 5000,
        "regions": [], "sectors": [], "trends": [], "bonds": [], "commodities": []
    }
    
    full_text = input_string.lower()
    
    # Parse goal
    if "grow them aggressively" in full_text or "grow aggressively" in full_text:
        profile["goal"] = "Grow them aggressively"
    elif "grow moderately" in full_text:
        profile["goal"] = "Grow moderately"
    elif "grow with caution" in full_text:
        profile["goal"] = "Grow with caution"
    elif "avoid losing money" in full_text:
        profile["goal"] = "Avoid losing money"
    
    # Parse time horizon
    if "1-3 year" in full_text:
        profile["time_horizon"] = "1-3 years"
    elif "3-5 year" in full_text:
        profile["time_horizon"] = "3-5 years"
    elif "6-10 year" in full_text:
        profile["time_horizon"] = "6-10 years"
    elif "10+ year" in full_text:
        profile["time_horizon"] = "10+ years"
    
    # Parse risk behavior
    if "sell everything" in full_text:
        profile["risk_behavior"] = "I'd sell everything"
    elif "sell some" in full_text:
        profile["risk_behavior"] = "I'd sell some"
    elif "do nothing" in full_text:
        profile["risk_behavior"] = "I'll do nothing"
    elif "buy more" in full_text:
        profile["risk_behavior"] = "I'd buy more"
    
    # Parse amount
    amount_match = re.search(r'(?:capital|amount)[:\s]*\$?([\d,]+(?:\.\d{2})?)', input_string, re.IGNORECASE)
    if amount_match:
        try:
            profile["amount"] = float(amount_match.group(1).replace(',', ''))
        except:
            pass
    
    # Parse preferences
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
    """Normalize text for fuzzy matching"""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def fuzzy_match(name: str, threshold: float = 0.6):
    """Find best matching ETF from database"""
    name_normalized = normalize(name)
    best_match, best_score = None, 0
    
    for etf in ETF_DATABASE:
        etf_normalized = normalize(etf)
        if name_normalized in etf_normalized or etf_normalized in name_normalized:
            return etf, 1.0
        score = SequenceMatcher(None, name_normalized, etf_normalized).ratio()
        if score > best_score:
            best_score, best_match = score, etf
    
    return (best_match, best_score) if best_score >= threshold else (None, 0)


def validate_portfolio(response_text: str) -> list:
    """Validate ETF names from Gemini response against approved list"""
    pattern = r'([A-Za-z][A-Za-z0-9\s&\-\']+(?:UCITS|ETF)[A-Za-z0-9\s&\-\'\(\)]*)'
    found = set()
    for match in re.findall(pattern, response_text):
        clean = match.strip()
        if len(clean) > 15 and not clean.startswith("This ETF"):
            found.add(clean)
    
    results = []
    for name in found:
        match, score = fuzzy_match(name)
        if match:
            results.append({"gemini_said": name, "matched_to": match, "score": score})
    return results


# System prompt for Gemini
SYSTEM_PROMPT = """You are a UCITS-compliant portfolio advisor.
Recommend real UCITS ETFs with full official names. Maximum 7 ETFs. No markdown tables.

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

Investment Rationale
[Why this portfolio fits their profile]

Rebalancing: [recommendation]
"""


def generate_portfolio(user_profile: dict) -> str:
    """Call Gemini API to generate portfolio recommendation"""
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


def run_portfolio(user_input: str):
    """Main workflow: parse input -> generate portfolio -> save JSON + PDF"""
    portfolio_num = get_next_portfolio_number()
    folder_path = os.path.join(OUTPUT_DIR, f"portfolio_{portfolio_num}")
    os.makedirs(folder_path, exist_ok=True)
    
    print(f"\n{'='*50}")
    print(f"GENERATING PORTFOLIO #{portfolio_num}")
    print(f"{'='*50}")
    
    # Parse user input
    profile = parse_user_input(user_input)
    print(f"\nProfile: {profile['goal']} | {profile['time_horizon']} | ${profile['amount']:,.0f}")
    
    # Generate portfolio with Gemini
    print(f"\nCalling Gemini...")
    response = generate_portfolio(profile)
    print(response.replace('✓', '*').replace('✔', '*'))
    
    # Validate ETFs
    validation = validate_portfolio(response)
    print(f"\n{len(validation)} ETFs matched in approved list")
    
    # Save JSON
    json_path = os.path.join(folder_path, 'portfolio_data.json')
    json_data = generate_portfolio_json(response, profile, validation, json_path)
    
    # Generate PDF
    print(f"\nGenerating PDF...")
    pdf_path = os.path.join(folder_path, 'portfolio_report.pdf')
    generate_pdf(json_data, pdf_path)
    
    print(f"\n{'='*50}")
    print(f"DONE! Output: output/portfolio_{portfolio_num}/")
    print(f"{'='*50}")


def main():
    print("="*50)
    print("PORTFOLIO GENERATOR")
    print("="*50)
    user_input = input("\nPaste quiz results and press Enter: ")
    run_portfolio(user_input)


if __name__ == "__main__":
    main()
