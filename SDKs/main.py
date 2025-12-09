"""
Portfolio Generator - Main Entry Point
Orchestrates: Quiz Input → Data Provider → Renderer → Output
"""

import os
import re
import sys
from data_provider import get_portfolio_data
from renderer import render_portfolio


def parse_quiz_input(quiz_string: str) -> dict:
    """
    Parse quiz response string into structured data
    
    Expected format from quiz:
    Investment Goals: Grow with caution
    Withdraw Expectation: In 1-3 years
    Scenario Question: ... Answer: I'd sell some
    Portfolio Committed Capital: $1000
    Preferred Topics: Asia-Pacific, Semiconductors
    Name: Pushkar Aggarwal
    Customer Id: 218
    Email: pushkar1713@gmail.com
    """
    data = {
        "name": "Investor",
        "email": "investor@email.com",
        "customer_id": "",
        "age": "N/A",
        "investment_amount": 10000,
        "time_horizon": "3-5 years",
        "investment_goal": "Grow moderately",
        "risk_behavior": "hold",
        "risk_profile": "Moderate",
        "preferred_topics": []
    }
    
    # Extract Name
    name_match = re.search(r'Name:\s*([^\n]+?)(?:\s*Customer|\s*Email|$)', quiz_string, re.IGNORECASE)
    if name_match:
        data["name"] = name_match.group(1).strip()
    
    # Extract Email
    email_match = re.search(r'Email:\s*([\w\.-]+@[\w\.-]+)', quiz_string, re.IGNORECASE)
    if email_match:
        data["email"] = email_match.group(1).strip()
    
    # Extract Customer ID
    id_match = re.search(r'Customer\s*Id:\s*(\d+)', quiz_string, re.IGNORECASE)
    if id_match:
        data["customer_id"] = id_match.group(1).strip()
    
    # Extract Investment Goal
    goal_match = re.search(r'Investment Goals?:\s*([^\n]+)', quiz_string, re.IGNORECASE)
    if goal_match:
        data["investment_goal"] = goal_match.group(1).strip()
    
    # Extract Time Horizon
    horizon_match = re.search(r'Withdraw Expectation:\s*(?:In\s*)?(\d+-\d+\s*years?)', quiz_string, re.IGNORECASE)
    if horizon_match:
        data["time_horizon"] = horizon_match.group(1).strip()
    
    # Extract Risk Behavior from Scenario Answer
    answer_match = re.search(r'Answer:\s*([^\n]+)', quiz_string, re.IGNORECASE)
    if answer_match:
        answer = answer_match.group(1).lower()
        data["risk_behavior"] = answer
        # Determine risk profile
        if "sell" in answer:
            data["risk_profile"] = "Low"
        elif "buy" in answer:
            data["risk_profile"] = "High"
        else:
            data["risk_profile"] = "Moderate"
    
    # Extract Investment Amount
    capital_match = re.search(r'(?:Portfolio Committed Capital|Capital):\s*\$?([\d,]+(?:\.\d+)?)', quiz_string, re.IGNORECASE)
    if capital_match:
        amount_str = capital_match.group(1).replace(',', '')
        try:
            data["investment_amount"] = float(amount_str)
        except ValueError:
            pass
    
    # Extract Preferred Topics
    topics_match = re.search(r'Preferred Topics:\s*([^\n]+)', quiz_string, re.IGNORECASE)
    if topics_match:
        topics = [t.strip() for t in topics_match.group(1).split(',')]
        data["preferred_topics"] = topics
    
    return data


def generate_portfolio(quiz_input: str) -> str:
    """
    Main function to generate portfolio from quiz input
    
    Args:
        quiz_input: Raw quiz response string
    
    Returns:
        Path to generated report
    """
    print("=" * 50)
    print("PORTFOLIO GENERATOR")
    print("=" * 50)
    
    # Step 1: Parse quiz input
    print("\n[1/3] Parsing quiz input...")
    quiz_data = parse_quiz_input(quiz_input)
    print(f"  > Investor: {quiz_data['name']}")
    print(f"  > Email: {quiz_data['email']}")
    print(f"  > Risk Profile: {quiz_data['risk_profile']}")
    print(f"  > Time Horizon: {quiz_data['time_horizon']}")
    print(f"  > Investment: ${quiz_data['investment_amount']:,.0f}")
    
    # Step 2: Get portfolio data (API + Gemini)
    print("\n[2/3] Fetching portfolio data...")
    template_data = get_portfolio_data(quiz_data)
    print(f"  > Data fields ready: {len(template_data)}")
    
    # Step 3: Render report
    print("\n[3/3] Rendering report...")
    
    # Create output directory based on investor name
    investor_slug = quiz_data['name'].replace(" ", "_")
    output_dir = os.path.join("output", f"portfolio_{investor_slug}")
    
    output_result = render_portfolio(template_data, output_dir)
    output_path = output_result['pdf']
    
    print("\n" + "=" * 50)
    print("[OK] PORTFOLIO GENERATED SUCCESSFULLY")
    print(f"  Output: {output_path}")
    print("=" * 50)
    
    return output_path


# Sample quiz input for testing
SAMPLE_QUIZ = """Investment Goals: Grow with caution
Withdraw Expectation: In 1-3 years
Scenario Question: Imagine you started with a $2,000 investment. Then, in one month, your investment lost $200 in value. What would you do next?
Answer: I'd sell some
Portfolio Committed Capital: $10,000
Preferred Topics: Asia-Pacific, Semiconductors, Electric Vehicles
Name: Pushkar Aggarwal
Customer Id: 218
Email: pushkar1713@gmail.com"""


if __name__ == "__main__":
    # Check if quiz input provided via command line
    if len(sys.argv) > 1:
        # Join all arguments as quiz string
        quiz_input = " ".join(sys.argv[1:])
    else:
        # Prompt for input
        print("Enter quiz response (paste and press Enter twice to finish):")
        print("-" * 40)
        lines = []
        try:
            while True:
                line = input()
                if line == "":
                    if lines and lines[-1] == "":
                        break
                lines.append(line)
            quiz_input = "\n".join(lines[:-1]) if lines else ""
        except EOFError:
            quiz_input = "\n".join(lines)
        
        # If no input, use sample
        if not quiz_input.strip():
            print("\nNo input provided. Using sample quiz data...")
            quiz_input = SAMPLE_QUIZ
    
    # Generate portfolio
    result = generate_portfolio(quiz_input)
