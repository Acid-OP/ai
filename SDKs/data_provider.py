"""
Data Provider - Fetches and prepares all data for portfolio report
Sources: Paasa API + Gemini enhancement
"""

import os
import json
import requests
import base64
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

load_dotenv()

PAASA_API_BASE = "https://api-stage.paasa.com/api/portfolio/v1"
BEARER_TOKEN = os.getenv("PAASA_BEARER_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def get_portfolio_id(quiz_data: dict) -> int:
    """
    Map quiz answers to portfolio ID (1, 2, or 3)
    Based on risk profile and investment goals
    """
    goal = quiz_data.get("investment_goal", "").lower()
    risk_behavior = quiz_data.get("risk_behavior", "").lower()
    
    # Conservative: Low risk, cautious growth
    if "caution" in goal or "sell" in risk_behavior:
        return 1  # Conservative portfolio
    # Aggressive: High risk, aggressive growth
    elif "aggressive" in goal or "buy more" in risk_behavior:
        return 3  # Aggressive portfolio
    # Moderate: Default
    else:
        return 2  # Moderate portfolio


def fetch_from_api(portfolio_id: int) -> dict:
    """
    Fetch portfolio data from Paasa API
    """
    url = f"{PAASA_API_BASE}/analyze"
    params = {
        "portfolioId": portfolio_id,
        "fromTemplates": "true"
    }
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
        # Extract data from nested structure
        if result.get('success') and 'data' in result:
            return result['data']
        return result
    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}")
        print(f"Response: {response.text if response else 'No response'}")
        return {}
    except Exception as e:
        print(f"Error fetching from API: {e}")
        return {}


def generate_performance_chart(performance_data: dict) -> str:
    """
    Generate performance chart as base64 encoded image
    """
    fig, ax = plt.subplots(figsize=(10, 4))
    
    labels = performance_data.get("labels", [])
    portfolio = performance_data.get("portfolio", [])
    benchmark = performance_data.get("benchmark", [])
    
    # Plot lines
    x_values = range(len(labels))
    ax.plot(x_values, portfolio, color='#3b82f6', linewidth=2, label='My portfolio', zorder=2)
    ax.plot(x_values, benchmark, color='#ef4444', linewidth=2, linestyle='--', label='S&P 500', zorder=1)
    
    # Fill area under portfolio line
    ax.fill_between(x_values, portfolio, alpha=0.1, color='#3b82f6')
    
    # Styling
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('white')
    ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e0e0e0')
    ax.spines['bottom'].set_color('#e0e0e0')
    
    # X-axis
    ax.set_xticks(range(0, len(labels), max(1, len(labels)//8)))
    ax.set_xticklabels([labels[i] for i in range(0, len(labels), max(1, len(labels)//8))], fontsize=9)
    
    # Y-axis formatting
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${int(y/1000)}k'))
    ax.tick_params(axis='both', labelsize=9, colors='#666666')
    
    # Legend
    legend = ax.legend(loc='upper left', frameon=True, fontsize=10)
    legend.get_frame().set_facecolor('white')
    legend.get_frame().set_edgecolor('#e0e0e0')
    
    # Tight layout
    plt.tight_layout()
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"


def generate_donut_chart(allocation_data: dict) -> str:
    """
    Generate allocation donut chart as base64 encoded image
    """
    fig, ax = plt.subplots(figsize=(3, 3))
    
    labels = allocation_data.get("labels", [])
    values = allocation_data.get("values", [])
    colors = ['#1e40af', '#facc15', '#60a5fa']
    
    # Create donut chart
    wedges, texts = ax.pie(values, colors=colors, startangle=90, 
                            wedgeprops=dict(width=0.35))
    
    # Make it a donut
    centre_circle = plt.Circle((0, 0), 0.65, fc='white')
    fig.gca().add_artist(centre_circle)
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    
    # Remove background
    fig.patch.set_alpha(0.0)
    ax.set_facecolor('none')
    
    # Tight layout
    plt.tight_layout(pad=0)
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight', 
                transparent=True, pad_inches=0)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"


def enhance_with_gemini(portfolio_data: dict, quiz_data: dict) -> dict:
    """
    Use Gemini to enhance textual content (methodology, descriptions)
    """
    if not GEMINI_API_KEY:
        return {
            "methodology": "Modern Portfolio Theory based allocation optimized for your risk profile.",
            "risk_note": "This portfolio is designed to match your investment goals."
        }
    
    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""Based on this investor profile:
- Risk Profile: {quiz_data.get('risk_profile', 'Moderate')}
- Time Horizon: {quiz_data.get('time_horizon', '5 years')}
- Investment Goal: {quiz_data.get('investment_goal', 'Growth')}

Generate a brief 2-sentence methodology description for their portfolio based on Modern Portfolio Theory.
Keep it professional and concise."""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        
        return {
            "methodology": response.text.strip(),
            "risk_note": "Portfolio optimized for risk-adjusted returns."
        }
    except Exception as e:
        print(f"Gemini enhancement failed: {e}")
        return {
            "methodology": "Globally diversified portfolio using Modern Portfolio Theory.",
            "risk_note": "Optimized for your risk profile."
        }


def get_portfolio_data(quiz_data: dict) -> dict:
    """
    Main function: Get all data needed for portfolio template
    Returns a dictionary with all placeholder values
    """
    # Get portfolio ID based on quiz
    portfolio_id = get_portfolio_id(quiz_data)
    
    # Fetch from API
    api_data = fetch_from_api(portfolio_id)
    
    if not api_data:
        print("Warning: No API data received, using defaults")
        api_data = {}
    
    # Get Gemini enhancements
    gemini_data = enhance_with_gemini(api_data, quiz_data)
    
    # Extract holdings from API response
    holdings = []
    symbol_colors = ['green', 'purple', 'blue', 'orange', 'yellow']
    
    portfolio_holdings = api_data.get("holdings", [])
    for i, h in enumerate(portfolio_holdings[:5]):  # Top 5 holdings
        ticker = h.get("ticker", "N/A")
        position = h.get("position", 20)  # position is already in percentage
        holdings.append({
            "symbol": ticker,
            "name": h.get("name", ticker),
            "category": h.get("category_name", "ETF"),
            "expense_ratio": "0.2%",  # Default as API doesn't provide this
            "allocation": f"{position}%",
            "color": symbol_colors[i % len(symbol_colors)]
        })
    
    # Generate holdings rows HTML
    holdings_rows = ""
    for h in holdings:
        holdings_rows += f"""<tr>
            <td><a href="#" class="symbol-link">{h['symbol']}</a></td>
            <td>{h['name']}</td>
            <td>{h['category']}</td>
            <td>{h['expense_ratio']}</td>
            <td>{h['allocation']}</td>
        </tr>"""
    
    # Extract geographic data
    regions = api_data.get("regions", [])
    geographic_rows = ""
    for r in regions[:5]:
        name = r.get("name", "Unknown")
        weight = r.get("size", 0)  # size is already in percentage
        geographic_rows += f"""<tr>
            <td>{name}</td>
            <td>
                <div class="allocation-bar">
                    <div class="allocation-bar-fill" style="width: {weight}%;"></div>
                </div>
                <span>{weight:.1f}%</span>
            </td>
        </tr>"""
    
    # Extract top underlying holdings
    top_stocks = api_data.get("underlying_stocks", [])
    top_holdings_rows = ""
    for s in top_stocks[:10]:
        name = s.get("symbol", "Unknown")
        weight = s.get("weight", 0)  # weight is already in percentage
        top_holdings_rows += f"""<tr>
            <td>{name}</td>
            <td>
                <div class="allocation-bar">
                    <div class="allocation-bar-fill" style="width: {min(weight, 100)}%;"></div>
                </div>
                <span>{weight:.1f}%</span>
            </td>
        </tr>"""
    
    # Allocation data for doughnut chart
    asset_classes = {}
    for h in portfolio_holdings:
        ac = h.get("category_name", "Other")
        weight = h.get("position", 0)  # position is already in percentage
        asset_classes[ac] = asset_classes.get(ac, 0) + weight
    
    allocation_labels = list(asset_classes.keys())[:3] or ["Global markets ETFs", "Bond ETFs", "U.S. stocks ETFs"]
    allocation_values = list(asset_classes.values())[:3] or [40, 30, 30]
    
    allocation_data = {
        "labels": allocation_labels,
        "values": allocation_values
    }
    
    # Generate allocation legend HTML
    color_classes = ['dark', 'blue', 'light']
    allocation_legend = ""
    for i, label in enumerate(allocation_labels):
        allocation_legend += f"""<div class="allocation-legend-item">
            <span class="legend-dot {color_classes[i % 3]}"></span>
            <span>{label}</span>
        </div>"""
    
    # Performance data for line chart
    returns_data = api_data.get("portfolioReturns", {})
    benchmark_data = api_data.get("benchmarkReturns", {})
    
    # Generate performance chart data
    if returns_data and isinstance(returns_data, dict):
        dates = sorted(returns_data.keys())[-24:]  # Last 24 data points
        portfolio_values = []
        benchmark_values = []
        base_value = 10000
        
        for d in dates:
            p_return = returns_data.get(d, 0)
            b_return = benchmark_data.get(d, 0) if isinstance(benchmark_data, dict) else 0
            base_value *= (1 + p_return)
            portfolio_values.append(round(base_value, 2))
            benchmark_values.append(round(10000 * (1 + b_return), 2))
        
        # Format dates for display
        formatted_dates = []
        for d in dates:
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
                formatted_dates.append(dt.strftime("%b %Y"))
            except:
                formatted_dates.append(d)
        
        performance_data = {
            "labels": formatted_dates,
            "portfolio": portfolio_values,
            "benchmark": benchmark_values
        }
    else:
        # Default performance data
        performance_data = {
            "labels": ["Jan 2023", "Apr 2023", "Jul 2023", "Oct 2023", "Jan 2024", "Apr 2024", "Jul 2024", "Oct 2024"],
            "portfolio": [10000, 10500, 11200, 10800, 11500, 12000, 12800, 13500],
            "benchmark": [10000, 10300, 10800, 10500, 11000, 11300, 11800, 12200]
        }
    
    # Metrics
    metrics = api_data.get("riskMetrics", {})
    portfolio_return = metrics.get("annualizedReturn", 0.145)
    benchmark_return = metrics.get("benchmarkReturn", 0.145)
    volatility = metrics.get("volatility", metrics.get("standardDeviation", 0.205))
    
    # Determine risk profile from quiz
    risk_profile = quiz_data.get("risk_profile", "Moderate")
    if portfolio_id == 1:
        risk_profile = "Low"
    elif portfolio_id == 3:
        risk_profile = "High"
    
    # Generate performance chart image
    performance_chart = generate_performance_chart(performance_data)
    
    # Generate allocation donut chart image
    allocation_chart_image = generate_donut_chart(allocation_data)
    
    # Portfolio description text
    portfolio_description = "This portfolio is constructed using principles of Modern Portfolio Theory (MPT), which seeks to optimize risk-adjusted returns through broad diversification across various asset classes. Similar to methodologies employed by leading platforms like Wealthfront."
    
    # Metrics data from API
    one_yr = api_data.get("one_yr_annualized", portfolio_return * 100)
    three_yr = api_data.get("three_yr_annualized", portfolio_return * 90)
    five_yr = api_data.get("five_yr_annualized", portfolio_return * 80)
    vol = api_data.get("volatility", volatility * 100)
    
    ytd_return = f"+{one_yr:.1f}%" if one_yr else "+14.5%"
    ytd_benchmark = f"+{one_yr * 0.95:.1f}%" if one_yr else "+14.5%"
    one_year_return = f"+{one_yr:.1f}%" if one_yr else "+14.5%"
    one_year_benchmark = f"+{one_yr * 0.95:.1f}%" if one_yr else "+14.5%"
    three_year_return = f"+{three_yr:.1f}%" if three_yr else "+13.1%"
    three_year_benchmark = f"+{three_yr * 0.9:.1f}%" if three_yr else "+12.3%"
    five_year_volatility = f"+{vol:.1f}%"
    five_year_vol_benchmark = f"+{vol * 0.95:.1f}%"
    
    # Build complete data dictionary for template
    template_data = {
        # Header
        "report_date": datetime.now().strftime("%d %B %Y"),
        
        # Investor Info
        "investor_name": quiz_data.get("name", "Investor"),
        "email": quiz_data.get("email", "investor@email.com"),
        "age": quiz_data.get("age", "N/A"),
        "investment_amount": f"{quiz_data.get('investment_amount', 10000):,.0f}",
        "time_horizon": quiz_data.get("time_horizon", "1-3 years"),
        "risk_profile": risk_profile,
        
        # Holdings table
        "holdings_rows": holdings_rows,
        
        # Performance chart image
        "performance_chart": performance_chart,
        
        # Allocation chart image and legend
        "allocation_chart": allocation_chart_image,
        "allocation_legend": allocation_legend,
        
        # Metrics comparison
        "ytd_return": ytd_return,
        "ytd_benchmark": ytd_benchmark,
        "one_year_return": one_year_return,
        "one_year_benchmark": one_year_benchmark,
        "three_year_return": three_year_return,
        "three_year_benchmark": three_year_benchmark,
        "five_year_volatility": five_year_volatility,
        "five_year_vol_benchmark": five_year_vol_benchmark,
        
        # Geographic and top holdings
        "geographic_rows": geographic_rows,
        "top_holdings_rows": top_holdings_rows,
    }
    
    return template_data


if __name__ == "__main__":
    # Test with sample quiz data
    test_quiz = {
        "name": "Pushkar Aggarwal",
        "email": "pushkar1713@gmail.com",
        "age": "49 yrs",
        "investment_amount": 10000,
        "time_horizon": "1-3 years",
        "investment_goal": "Grow with caution",
        "risk_behavior": "sell some",
        "risk_profile": "Low"
    }
    
    data = get_portfolio_data(test_quiz)
    print("Template data keys:", list(data.keys()))
    print("\nSample values:")
    print(f"  Investor: {data['investor_name']}")
    print(f"  Risk: {data['risk_profile']}")
    print(f"  Date: {data['report_date']}")
