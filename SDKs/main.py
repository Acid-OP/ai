import os
import sys
from data_provider import get_portfolio_data
from renderer import render_portfolio


def parse_input(input_string: str) -> tuple:
    """Parse user input with Portfolio ID"""
    data = {
        "name": None,
        "email": None,
        "age": None,
        "investment_amount": None,
        "time_horizon": None,
        "investment_goal": None,
        "risk_behavior": None,
        "preferred_topics": []
    }
    
    portfolio_id = None
    
    # Parse line by line for key-value pairs
    for line in input_string.split('\n'):
        line = line.strip()
        if ':' not in line:
            continue
        
        key, value = line.split(':', 1)
        key = key.strip().lower()
        value = value.strip()
        
        if not value:
            continue
        
        # Portfolio ID (required for direct mode)
        if 'portfolio' in key and 'id' in key:
            try:
                portfolio_id = int(value)
            except ValueError:
                pass
        
        # Name
        elif 'name' in key:
            data["name"] = value
        
        # Email
        elif 'email' in key:
            data["email"] = value
        
        # Age
        elif 'age' in key:
            data["age"] = value
        
        # Investment Amount
        elif 'amount' in key or 'investment amount' in key:
            amount_str = value.replace('$', '').replace(',', '').strip()
            try:
                data["investment_amount"] = float(amount_str)
            except ValueError:
                pass
        
        # Time Horizon
        elif 'time' in key or 'horizon' in key:
            data["time_horizon"] = value
        
        # Investment Goal
        elif 'goal' in key:
            data["investment_goal"] = value
        
        # Preferred Topics
        elif 'topic' in key or 'preferred' in key:
            data["preferred_topics"] = [t.strip() for t in value.split(',') if t.strip()]
    
    return data, portfolio_id


def generate_portfolio(user_input: str) -> str:
    print("=" * 80)
    print("PORTFOLIO GENERATOR")
    print("=" * 80)
    
    print("\n[1/3] Parsing input...")
    quiz_data, portfolio_id = parse_input(user_input)
    
    if portfolio_id is None:
        print("ERROR: Portfolio ID is required!")
        print("\nExpected format:")
        print("  Portfolio ID: 53")
        print("  Name: John Doe")
        print("  Email: john@example.com")
        print("  Age: 44")
        print("  Investment Amount: 25000")
        print("  Time Horizon: 5+ years")
        sys.exit(1)
    
    print(f"  > Portfolio ID: {portfolio_id}")
    print(f"  > Investor: {quiz_data['name']}")
    print(f"  > Time Horizon: {quiz_data['time_horizon']}")
    
    print(f"\n[2/3] Fetching portfolio data from API...")
    template_data = get_portfolio_data(quiz_data, portfolio_id=portfolio_id)
    
    print("\n[3/3] Rendering report...")
    investor_slug = quiz_data.get('name') or f"portfolio_{portfolio_id}"
    if investor_slug and investor_slug != "-":
        investor_slug = investor_slug.replace(" ", "_")
    else:
        investor_slug = f"portfolio_{portfolio_id}"
    output_dir = os.path.join("output", investor_slug)
    
    output_result = render_portfolio(template_data, output_dir)
    output_path = output_result['pdf']
    
    print("\n" + "=" * 80)
    print("[OK] PORTFOLIO GENERATED SUCCESSFULLY")
    print(f"  Output: {output_path}")
    print("=" * 80)
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check if it's a file path
        arg = sys.argv[1]
        if os.path.isfile(arg):
            print(f"[INPUT] Reading from file: {arg}")
            with open(arg, 'r', encoding='utf-8') as f:
                user_input = f.read()
        else:
            user_input = " ".join(sys.argv[1:])
    else:
        print("=" * 80)
        print("PORTFOLIO GENERATOR")
        print("=" * 80)
        print("\nUSAGE:")
        print("  python main.py input.txt")
        print("\nINPUT FILE FORMAT (input.txt):")
        print("  Portfolio ID: 52")
        print("  Name: John Doe")
        print("  Email: john@example.com")
        print("  Age: 44")
        print("  Investment Amount: 25000")
        print("  Time Horizon: 5+ years")
        print("  Investment Goal: Growth (optional)")
        print("  Preferred Topics: Tech, Biotech (optional)")
        print("\n" + "=" * 80)
        sys.exit(1)
    
    result = generate_portfolio(user_input)
