"""
Portfolio Generator - Main Entry Point
Clean architecture: Data (Python) + Template (HTML)
"""

import os
import re
from dotenv import load_dotenv
from data_provider import get_portfolio_data
from renderer import render_portfolio

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

BEARER_TOKEN = os.getenv("PAASA_BEARER_TOKEN", "")


def get_next_portfolio_number():
    """Get next portfolio folder number"""
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
        "goal": "", "risk_behavior": "", "time_horizon": "",
        "user_name": "", "user_email": "", "customer_id": ""
    }
    
    full_text = input_string.lower()
    original_text = input_string
    
    # Parse goal
    if "grow them aggressively" in full_text or "grow aggressively" in full_text:
        profile["goal"] = "Grow aggressively"
    elif "grow moderately" in full_text:
        profile["goal"] = "Grow moderately"
    elif "grow with caution" in full_text:
        profile["goal"] = "Grow with caution"
    elif "avoid losing money" in full_text:
        profile["goal"] = "Avoid losing money"
    
    # Parse time horizon
    if "1-3 year" in full_text or "in 1-3" in full_text:
        profile["time_horizon"] = "1-3 years"
    elif "3-5 year" in full_text or "in 3-5" in full_text:
        profile["time_horizon"] = "3-5 years"
    elif "6-10 year" in full_text or "in 6-10" in full_text:
        profile["time_horizon"] = "6-10 years"
    elif "10+ year" in full_text or "10 year" in full_text:
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
    
    # Parse Name (stop at newline or next field)
    name_match = re.search(r'Name:\s*\n?([A-Za-z][A-Za-z\s]*?)(?:\n|Customer|Email|$)', original_text, re.IGNORECASE)
    if name_match:
        profile["user_name"] = name_match.group(1).strip()
    
    # Parse Email
    email_match = re.search(r'Email:\s*\n?([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', original_text, re.IGNORECASE)
    if email_match:
        profile["user_email"] = email_match.group(1).strip()
    
    # Parse Customer ID
    id_match = re.search(r'Customer\s*Id:\s*\n?(\d+)', original_text, re.IGNORECASE)
    if id_match:
        profile["customer_id"] = id_match.group(1).strip()
    
    return profile


def run_portfolio(user_input: str, bearer_token: str = None):
    """
    Main workflow:
    1. Parse user input
    2. Get data (API + Gemini)
    3. Render to template
    """
    token = bearer_token or BEARER_TOKEN
    if not token:
        print("ERROR: No bearer token provided!")
        return None
    
    portfolio_num = get_next_portfolio_number()
    folder_path = os.path.join(OUTPUT_DIR, f"portfolio_{portfolio_num}")
    
    print(f"\n{'='*50}")
    print(f"GENERATING PORTFOLIO #{portfolio_num}")
    print(f"{'='*50}")
    
    # 1. Parse user input
    profile = parse_user_input(user_input)
    print(f"\nUser: {profile['user_name']} ({profile['user_email']})")
    print(f"Goal: {profile['goal']}")
    print(f"Risk: {profile['risk_behavior']}")
    print(f"Horizon: {profile['time_horizon']}")
    
    # 2. Get data (API + Gemini)
    print(f"\n--- DATA RETRIEVAL ---")
    data = get_portfolio_data(profile, token)
    
    # 3. Render to template
    print(f"\n--- RENDERING ---")
    output = render_portfolio(data, folder_path)
    
    print(f"\n{'='*50}")
    print(f"DONE! Output: output/portfolio_{portfolio_num}/")
    print(f"  - HTML: {output['html']}")
    print(f"  - JSON: {output['json']}")
    print(f"{'='*50}")
    
    return data


def main():
    print("="*50)
    print("PORTFOLIO GENERATOR")
    print("Data: Paasa API + Gemini")
    print("Template: HTML/CSS")
    print("="*50)
    
    if not BEARER_TOKEN:
        print("\nWARNING: No PAASA_BEARER_TOKEN in .env")
        token = input("Enter bearer token: ").strip()
    else:
        token = BEARER_TOKEN
    
    print("\nPaste quiz results and press Enter:\n")
    user_input = input("> ")
    
    if not user_input.strip():
        print("No input received!")
        return
    
    run_portfolio(user_input, token)


if __name__ == "__main__":
    main()
