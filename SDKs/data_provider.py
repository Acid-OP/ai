"""
Data Provider - Fetches and prepares all data for portfolio report
Sources: Paasa API + Gemini enhancement
"""

import os
import json
import requests
import base64
from io import BytesIO
from datetime import datetime, timedelta
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd

load_dotenv()

PAASA_API_BASE = "https://api-stage.paasa.com/api/portfolio/v1"
BEARER_TOKEN = os.getenv("PAASA_BEARER_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Professional color mapping for asset allocation categories
# Colors follow risk gradient: Cool (safe) → Warm (risky)
CATEGORY_COLORS = {
    "Bond ETFs": "#1e3a8a",                    # Dark Navy - Conservative/Stable
    "U.S. stocks ETFs": "#3b82f6",             # Royal Blue - Core Holdings
    "Global markets ETFs": "#14b8a6",          # Teal - Diversified
    "Technology ETFs": "#8b5cf6",              # Purple - Growth/Innovation
    "Emerging markets ETFs": "#f97316",        # Orange - High Growth/Risk
}

# Fallback color for unknown categories
DEFAULT_CATEGORY_COLOR = "#6b7280"  # Gray


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


def fetch_sp500_data(start_date: str, end_date: str) -> dict:
    """
    Fetch real S&P 500 historical data from Yahoo Finance
    Returns dict of {date: daily_return}
    """
    try:
        print(f"Fetching S&P 500 data from {start_date} to {end_date}...")
        
        # Fetch S&P 500 data using ^GSPC ticker
        sp500 = yf.download('^GSPC', start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if len(sp500) == 0:
            print("Warning: No S&P 500 data received from yfinance")
            return {}
        
        # Get Close prices - handle both single-column and multi-column DataFrames
        if isinstance(sp500.columns, pd.MultiIndex):
            close_prices = sp500['Close'].iloc[:, 0]
        else:
            close_prices = sp500['Close']
        
        # Calculate daily returns
        daily_returns = close_prices.pct_change()
        
        # Convert to dict {date: return}
        benchmark_returns = {}
        for i in range(len(daily_returns)):
            date = daily_returns.index[i]
            return_value = daily_returns.iloc[i]
            if pd.notna(return_value):
                date_str = date.strftime('%Y-%m-%d')
                benchmark_returns[date_str] = float(return_value)
        
        print(f"[OK] Fetched {len(benchmark_returns)} S&P 500 data points")
        return benchmark_returns
        
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
        import traceback
        traceback.print_exc()
        return {}


def generate_performance_chart(performance_data: dict) -> str:
    """
    Generate professional performance comparison chart
    Inspired by institutional investment report styling
    """
    fig, ax = plt.subplots(figsize=(11, 4.8))
    
    labels = performance_data.get("labels", [])
    portfolio = performance_data.get("portfolio", [])
    benchmark = performance_data.get("benchmark", [])
    
    if not portfolio or not benchmark:
        print("Warning: No data for performance chart")
        return ""
    
    x_values = range(len(labels))
    
    # PROFESSIONAL STYLING - Clean thin lines, no fill
    ax.plot(x_values, portfolio, color='#3b82f6', linewidth=1.8, 
            label='Your Portfolio', zorder=3, linestyle='-', alpha=0.95)
    ax.plot(x_values, benchmark, color='#ef4444', linewidth=1.8, 
            label='S&P 500 Benchmark', zorder=2, linestyle='-', alpha=0.85)
    
    # Optimize Y-axis range - minimize wasted space
    all_values = portfolio + benchmark
    y_min = min(all_values)
    y_max = max(all_values)
    y_range = y_max - y_min
    
    # Add 8% padding above and below for breathing room
    ax.set_ylim(y_min - (y_range * 0.08), y_max + (y_range * 0.08))
    
    # Clean white background
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    # Professional grid - very subtle horizontal lines only
    ax.grid(True, axis='y', alpha=0.12, linestyle='-', linewidth=0.6, color='#d1d5db')
    ax.grid(False, axis='x')
    
    # Clean borders - remove top and right
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    
    # X-axis - clean date labels with proper spacing
    num_labels = 7  # Fewer labels for vertical format
    step = max(1, len(labels) // num_labels)
    x_ticks = list(range(0, len(labels), step))
    
    # ALWAYS include the last date (Dec 2025)
    last_index = len(labels) - 1
    if len(x_ticks) == 0 or x_ticks[-1] != last_index:
        # Only add if not too close to previous tick
        if len(x_ticks) == 0 or (last_index - x_ticks[-1]) > (step * 0.4):
            x_ticks.append(last_index)
    
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([labels[i] for i in x_ticks], 
                       fontsize=8, color='#64748b', fontfamily='sans-serif',
                       verticalalignment='top')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center')
    
    # Y-axis - professional formatting
    ax.set_ylabel('Growth of $10,000 Investment', fontsize=10, 
                 color='#475569', fontfamily='sans-serif', labelpad=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.tick_params(axis='y', labelsize=8.5, colors='#64748b', length=4, width=0.8)
    ax.tick_params(axis='x', labelsize=8.5, colors='#64748b', length=4, width=0.8)
    
    # Professional legend - top left, clean
    legend = ax.legend(loc='upper left', frameon=False, fontsize=9.5,
                      labelspacing=0.6, handlelength=2.5, handletextpad=0.8)
    for text in legend.get_texts():
        text.set_color('#475569')
        text.set_fontfamily('sans-serif')
    
    # Title - professional and clean
    ax.set_title('Portfolio Performance vs S&P 500', fontsize=12, pad=18, 
                color='#1e293b', fontfamily='sans-serif', fontweight='600', loc='left')
    
    # High-quality export
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"


def generate_donut_chart(allocation_data: dict) -> str:
    """
    Generate professional allocation donut chart with dynamic colors
    """
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    
    labels = allocation_data.get("labels", [])
    values = allocation_data.get("values", [])
    
    # Get colors dynamically based on category names
    colors = [CATEGORY_COLORS.get(label, DEFAULT_CATEGORY_COLOR) for label in labels]
    
    # Create donut chart with refined styling
    wedges, texts = ax.pie(values, colors=colors, startangle=90, 
                            wedgeprops=dict(width=0.38, edgecolor='white', linewidth=2))
    
    # Clean center circle
    centre_circle = plt.Circle((0, 0), 0.62, fc='white')
    fig.gca().add_artist(centre_circle)
    
    # Perfect circle
    ax.axis('equal')
    
    # Clean background
    fig.patch.set_alpha(0.0)
    ax.set_facecolor('none')
    
    plt.tight_layout(pad=0)
    
    # High-quality export
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight', 
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


def get_logo_base64() -> str:
    """
    Load logo image and convert to base64 for embedding in PDF
    """
    logo_path = os.path.join(os.path.dirname(__file__), 'utils', 'Logo.png')
    try:
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
            logo_base64 = base64.b64encode(logo_data).decode()
            return f"data:image/png;base64,{logo_base64}"
    except Exception as e:
        print(f"Error loading logo: {e}")
        return ""


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
            <td>{weight:.0f}%</td>
        </tr>"""
    
    # Extract top underlying holdings
    top_stocks = api_data.get("underlying_stocks", [])
    top_holdings_rows = ""
    for s in top_stocks[:10]:
        name = s.get("symbol", "Unknown")
        weight = s.get("weight", 0)  # weight is already in percentage
        top_holdings_rows += f"""<tr>
            <td>{name}</td>
            <td>{weight:.0f}%</td>
        </tr>"""
    
    # Allocation data for doughnut chart
    asset_classes = {}
    for h in portfolio_holdings:
        ac = h.get("category_name", "Other")
        weight = h.get("position", 0)  # position is already in percentage
        asset_classes[ac] = asset_classes.get(ac, 0) + weight
    
    # Get ALL categories for dynamic display
    allocation_labels = list(asset_classes.keys()) or ["Global markets ETFs", "Bond ETFs", "U.S. stocks ETFs"]
    allocation_values = list(asset_classes.values()) or [40, 30, 30]
    
    allocation_data = {
        "labels": allocation_labels,
        "values": allocation_values
    }
    
    # Generate allocation legend HTML with dynamic colors
    allocation_legend = ""
    for label in allocation_labels:
        color = CATEGORY_COLORS.get(label, DEFAULT_CATEGORY_COLOR)
        allocation_legend += f"""<div class="allocation-legend-item">
            <span class="legend-dot" style="background-color: {color};"></span>
            <span>{label}</span>
        </div>"""
    
    # Performance data for line chart
    returns_data = api_data.get("portfolioReturns", {})
    benchmark_data = api_data.get("benchmarkReturns", {})
    
    # If API doesn't provide benchmark data, fetch REAL S&P 500 data from Yahoo Finance
    if returns_data and not benchmark_data:
        all_dates = sorted(returns_data.keys())
        if all_dates:
            start_date = all_dates[0]
            end_date = all_dates[-1]
            print(f"\nAPI doesn't provide S&P 500 data")
            print(f"Fetching REAL S&P 500 data from Yahoo Finance...")
            benchmark_data = fetch_sp500_data(start_date, end_date)
    
    # Generate performance chart data
    if returns_data and isinstance(returns_data, dict):
        # Get all dates, use last 252 trading days (1 year) for better visualization
        all_dates = sorted(returns_data.keys())
        
        # Use more data points for meaningful comparison (min 60, max 252 trading days)
        num_points = min(252, max(60, len(all_dates)))
        dates = all_dates[-num_points:]
        
        print(f"\n=== PERFORMANCE DATA VERIFICATION ===")
        print(f"Portfolio data points: {len(returns_data)}")
        print(f"S&P 500 data points: {len(benchmark_data) if benchmark_data else 0}")
        print(f"Date range: {dates[0]} to {dates[-1]}")
        print(f"Using {len(dates)} data points for chart")
        
        portfolio_values = []
        benchmark_values = []
        portfolio_base = 10000
        benchmark_base = 10000
        matched_dates = []
        
        for d in dates:
            p_return = returns_data.get(d, 0)
            b_return = benchmark_data.get(d, 0) if isinstance(benchmark_data, dict) else 0
            
            # Only include dates where we have data for both
            if p_return != 0 or b_return != 0:
                # Accumulate returns correctly (compound growth)
                portfolio_base *= (1 + p_return)
                benchmark_base *= (1 + b_return)
                
                portfolio_values.append(round(portfolio_base, 2))
                benchmark_values.append(round(benchmark_base, 2))
                matched_dates.append(d)
        
        print(f"Matched dates with data: {len(matched_dates)}")
        print(f"Portfolio: ${portfolio_values[0]:.2f} -> ${portfolio_values[-1]:.2f} ({((portfolio_values[-1]/10000 - 1) * 100):.2f}%)")
        print(f"S&P 500:   ${benchmark_values[0]:.2f} -> ${benchmark_values[-1]:.2f} ({((benchmark_values[-1]/10000 - 1) * 100):.2f}%)")
        print(f"=====================================\n")
        
        # Format dates for display - vertical stacking for clarity
        formatted_dates = []
        for d in matched_dates:
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
                # Vertical format: "Mar\n2024" for clarity
                formatted_dates.append(dt.strftime("%b\n%Y"))
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
    
    # Format metrics for display
    five_year_return = f"+{five_yr:.1f}%" if five_yr else "+14.5%"
    five_year_return_benchmark = f"+{five_yr * 0.95:.1f}%" if five_yr else "+14.5%"
    three_year_return = f"+{three_yr:.1f}%" if three_yr else "+20.5%"
    three_year_benchmark = f"+{three_yr * 0.9:.1f}%" if three_yr else "+20.5%"
    five_year_volatility = f"+{vol:.1f}%"
    five_year_vol_benchmark = f"+{vol * 0.95:.1f}%"
    
    # Get logo for footer
    logo_path = get_logo_base64()
    
    # Generate themes covered (based on preferred topics + standard themes)
    preferred_topics = quiz_data.get("preferred_topics", [])
    all_themes = [
        "World (all regions)",
        "Latin America",
        "Energy",
        "Electric Vehicles",
        "Asia-Pacific",
        "Technology",
        "Industrials",
        "Biotech",
        "Emerging markets",
        "Healthcare",
        "Nuclear Energy",
        "Palladium"
    ]
    
    # Generate theme items HTML
    themes_items = ""
    for theme in all_themes:
        themes_items += f'<div class="theme-item">{theme}</div>'
    
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
        
        # Footer
        "logo_path": logo_path,
        
        # Holdings table
        "holdings_rows": holdings_rows,
        
        # Performance chart image
        "performance_chart": performance_chart,
        
        # Allocation chart image and legend
        "allocation_chart": allocation_chart_image,
        "allocation_legend": allocation_legend,
        
        # Metrics comparison
        "five_year_return": five_year_return,
        "five_year_return_benchmark": five_year_return_benchmark,
        "three_year_return": three_year_return,
        "three_year_benchmark": three_year_benchmark,
        "five_year_volatility": five_year_volatility,
        "five_year_vol_benchmark": five_year_vol_benchmark,
        
        # Geographic and top holdings
        "geographic_rows": geographic_rows,
        "top_holdings_rows": top_holdings_rows,
        
        # Themes covered
        "themes_items": themes_items,
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
