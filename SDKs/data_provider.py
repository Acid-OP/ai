"""
Data Provider - ONLY handles data retrieval
NO chart generation, NO UI logic
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from google import genai

load_dotenv()

# API Config
API_URL = "https://api-stage.paasa.com/api/portfolio/v1/analyze"
INTERNAL_TOKEN = "5omc7nmGZNTba/wUzkL/PskVWIpL3N3PgtAAJDgjz48="

# Gemini Config
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def get_portfolio_id(goal: str, risk_behavior: str) -> int:
    """Map quiz answers to portfolio ID (1=Preservation, 2=Balanced, 3=Growth)"""
    conservative = ["avoid losing", "grow with caution", "sell everything", "sell some"]
    aggressive = ["grow aggressively", "buy more"]
    
    goal_lower = goal.lower()
    risk_lower = risk_behavior.lower()
    
    if any(c in goal_lower or c in risk_lower for c in conservative):
        return 1
    if any(a in goal_lower or a in risk_lower for a in aggressive):
        return 3
    return 2


def fetch_from_api(portfolio_id: int, token: str) -> dict:
    """Fetch portfolio data from Paasa API"""
    response = requests.get(
        API_URL,
        params={'portfolioId': portfolio_id, 'fromTemplates': 'true'},
        headers={
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'build-version': '44',
            'x-internal-client-token': INTERNAL_TOKEN,
            'app-version': '6.0.2'
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    
    result = response.json()
    if not result.get('success'):
        raise Exception(f"API returned error: {result.get('message')}")
    
    return result.get('data', {})


def enhance_with_gemini(api_data: dict, user_profile: dict) -> dict:
    """Use Gemini to generate methodology and insights"""
    holdings = api_data.get('holdings', [])
    
    prompt = f"""You are a financial advisor explaining a portfolio to a client.

Portfolio: {api_data.get('title', 'Balanced')} ({api_data.get('risk_level', 'moderate')} risk)
Holdings: {', '.join([f"{h.get('ticker')} ({h.get('position')}%)" for h in holdings[:5]])}
Time Horizon: {user_profile.get('time_horizon', '5+ years')}
5-Year Return: {api_data.get('five_yr_annualized', 'N/A')}%
Volatility: {api_data.get('volatility', 'N/A')}%

Generate JSON:
{{
    "methodology_title": "Short title (5-8 words)",
    "methodology_text": "2-3 sentences on Modern Portfolio Theory, global diversification like Wealthfront.",
    "key_principles": ["4 short bullet points"]
}}

Return ONLY valid JSON."""

    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        print(f"Gemini error: {e}")
        return {
            "methodology_title": "Modern Portfolio Theory Approach",
            "methodology_text": "We construct portfolios using Modern Portfolio Theory, optimizing risk-adjusted returns through global diversification across asset classes and regions.",
            "key_principles": [
                "Global diversification across regions",
                "Risk-adjusted return optimization",
                "Low-cost index ETF selection",
                "Automatic portfolio rebalancing"
            ]
        }


def get_portfolio_data(user_profile: dict, token: str) -> dict:
    """Main function - gets ALL data needed for portfolio report"""
    
    portfolio_id = get_portfolio_id(
        user_profile.get('goal', ''),
        user_profile.get('risk_behavior', '')
    )
    
    print(f"Selected: Portfolio ID {portfolio_id}")
    print("Fetching data from Paasa API...")
    api_data = fetch_from_api(portfolio_id, token)
    
    print("Enhancing with Gemini...")
    gemini_data = enhance_with_gemini(api_data, user_profile)
    
    # Transform holdings
    holdings = []
    for h in api_data.get('holdings', []):
        holdings.append({
            'ticker': h.get('ticker', ''),
            'name': h.get('name', ''),
            'weight': h.get('position', 0),
            'category': h.get('category_name', ''),
            'color': h.get('progress_color', '#888888')
        })
    
    # Regions
    regions = []
    for r in api_data.get('regions', []):
        regions.append({
            'name': r.get('name', ''),
            'percentage': r.get('size', 0)
        })
    
    # Top stocks
    top_stocks = []
    for s in api_data.get('underlying_stocks', [])[:10]:
        top_stocks.append({
            'symbol': s.get('symbol', ''),
            'weight': s.get('weight', 0)
        })
    
    # Benchmark
    benchmark = api_data.get('benchmark', {})
    
    # Chart data (portfolioReturns is dict: {date: return})
    chart_data = []
    portfolio_returns = api_data.get('portfolioReturns', {})
    if isinstance(portfolio_returns, dict):
        cumulative = 100
        for date in sorted(portfolio_returns.keys()):
            ret = portfolio_returns[date]
            cumulative = cumulative * (1 + ret)
            chart_data.append({'date': date, 'value': round(cumulative, 2)})
    
    # Build allocation legend data
    alloc_legend = []
    categories = {}
    colors_map = {}
    for h in holdings:
        cat = h.get('category', 'Other')
        if cat not in categories:
            categories[cat] = 0
            colors_map[cat] = h.get('color', '#888888')
        categories[cat] += h.get('weight', 0)
    for cat, weight in categories.items():
        alloc_legend.append({
            'name': cat,
            'weight': weight,
            'color': colors_map[cat]
        })
    
    return {
        'generated_at': datetime.now().isoformat(),
        'report_date': datetime.now().strftime('%B %d, %Y'),
        
        'user': {
            'name': user_profile.get('user_name', ''),
            'email': user_profile.get('user_email', '')
        },
        
        'profile': {
            'goal': user_profile.get('goal', ''),
            'time_horizon': user_profile.get('time_horizon', ''),
            'risk_behavior': user_profile.get('risk_behavior', '')
        },
        
        'portfolio': {
            'id': api_data.get('portfolio_id'),
            'title': api_data.get('title', ''),
            'risk_level': api_data.get('risk_level', ''),
            'funds_type': api_data.get('funds_type', 'Index Funds')
        },
        
        'holdings': holdings,
        
        'metrics': {
            'volatility': round(api_data.get('volatility') or 0, 1),
            'five_yr_return': round(api_data.get('five_yr_annualized') or 0, 1),
            'three_yr_return': round(api_data.get('three_yr_annualized') or 0, 1),
            'one_yr_return': round(api_data.get('one_yr_annualized') or 0, 1)
        },
        
        'benchmark': {
            'name': benchmark.get('name', 'S&P 500'),
            'five_yr_return': round(benchmark.get('five_yr_annualized') or 0, 1),
            'volatility': round(benchmark.get('volatility') or 0, 1)
        },
        
        'regions': regions[:8],
        'top_stocks': top_stocks,
        'allocation_legend': alloc_legend,
        'chart_data': chart_data,
        
        'methodology': gemini_data
    }
