"""
Data Provider - Fetches and prepares all data for portfolio report
"""

import os
import requests
import base64
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd

load_dotenv()

PAASA_API_BASE = os.getenv("PAASA_API_BASE")
BEARER_TOKEN = os.getenv("PAASA_BEARER_TOKEN")

if not PAASA_API_BASE:
    raise ValueError("PAASA_API_BASE not found in .env file. Please set it.")
if not BEARER_TOKEN:
    raise ValueError("PAASA_BEARER_TOKEN not found in .env file. Please set it.")

CATEGORY_COLORS = {
    "Bond ETFs": "#1e3a8a",                    # Dark Navy - Conservative/Stable
    "U.S. stocks ETFs": "#3b82f6",             # Royal Blue - Core Holdings
    "Global markets ETFs": "#14b8a6",          # Teal - Diversified
    "Technology ETFs": "#8b5cf6",              # Purple - Growth/Innovation
    "Emerging markets ETFs": "#f97316",        # Orange - High Growth/Risk
    "Commodities ETFs": "#eab308",             # Gold/Yellow - Commodities (Gold, 
}

# Fallback color for unknown categories
DEFAULT_CATEGORY_COLOR = "#6b7280"  # Gray


def fetch_from_api(portfolio_id: int) -> dict:
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
        if result.get('success') and 'data' in result:
            return result['data']
        return result
    except Exception as e:
        print(f"Error fetching from API: {e}")
        return {}


def fetch_sp500_data(start_date: str, end_date: str) -> dict:
    try:
        sp500 = yf.download('^GSPC', start=start_date, end=end_date, progress=False, auto_adjust=True)
        
        if len(sp500) == 0:
            return {}
        
        if isinstance(sp500.columns, pd.MultiIndex):
            close_prices = sp500['Close'].iloc[:, 0]
        else:
            close_prices = sp500['Close']
        
        daily_returns = close_prices.pct_change()
        
        benchmark_returns = {}
        for i in range(len(daily_returns)):
            date = daily_returns.index[i]
            return_value = daily_returns.iloc[i]
            if pd.notna(return_value):
                date_str = date.strftime('%Y-%m-%d')
                benchmark_returns[date_str] = float(return_value)
        
        return benchmark_returns
        
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
        return {}


def generate_performance_chart(performance_data: dict) -> str:
    fig, ax = plt.subplots(figsize=(11, 3.8))
    
    labels = performance_data.get("labels", [])
    portfolio = performance_data.get("portfolio", [])
    benchmark = performance_data.get("benchmark", [])
    
    if not portfolio or not benchmark:
        return ""
    
    x_values = range(len(labels))
    
    ax.plot(x_values, portfolio, color='#3b82f6', linewidth=1.8, 
            label='Your Portfolio', zorder=3, linestyle='-', alpha=0.95)
    ax.plot(x_values, benchmark, color='#ef4444', linewidth=1.8, 
            label='S&P 500 Benchmark', zorder=2, linestyle='-', alpha=0.85)
    
    all_values = portfolio + benchmark
    y_min = min(all_values)
    y_max = max(all_values)
    y_range = y_max - y_min
    ax.set_ylim(y_min - (y_range * 0.08), y_max + (y_range * 0.08))
    
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    
    ax.grid(True, axis='y', alpha=0.12, linestyle='-', linewidth=0.6, color='#d1d5db')
    ax.grid(False, axis='x')
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cbd5e1')
    ax.spines['bottom'].set_color('#cbd5e1')
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    
    num_labels = 7
    step = max(1, len(labels) // num_labels)
    x_ticks = list(range(0, len(labels), step))
    
    last_index = len(labels) - 1
    if len(x_ticks) == 0 or x_ticks[-1] != last_index:
        if len(x_ticks) == 0 or (last_index - x_ticks[-1]) > (step * 0.4):
            x_ticks.append(last_index)
    
    ax.set_xticks(x_ticks)
    ax.set_xticklabels([labels[i] for i in x_ticks], 
                       fontsize=8, color='#64748b', fontfamily='sans-serif',
                       verticalalignment='top')
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=0, ha='center')
    
    ax.set_ylabel('Growth of $10,000 Investment', fontsize=10, 
                 color='#475569', fontfamily='sans-serif', labelpad=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.tick_params(axis='y', labelsize=8.5, colors='#64748b', length=4, width=0.8)
    ax.tick_params(axis='x', labelsize=8.5, colors='#64748b', length=4, width=0.8)
    
    legend = ax.legend(loc='upper left', frameon=False, fontsize=9.5,
                      labelspacing=0.6, handlelength=2.5, handletextpad=0.8)
    for text in legend.get_texts():
        text.set_color('#475569')
        text.set_fontfamily('sans-serif')
    
    ax.set_title('Portfolio Performance vs S&P 500', fontsize=12, pad=18, 
                color='#1e293b', fontfamily='sans-serif', fontweight='600', loc='left')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight', 
               facecolor='white', edgecolor='none')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"


def generate_donut_chart(allocation_data: dict) -> str:
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    
    labels = allocation_data.get("labels", [])
    values = allocation_data.get("values", [])
    colors = [CATEGORY_COLORS.get(label, DEFAULT_CATEGORY_COLOR) for label in labels]
    
    wedges, texts = ax.pie(values, colors=colors, startangle=90, 
                            wedgeprops=dict(width=0.38, edgecolor='white', linewidth=2))
    
    centre_circle = plt.Circle((0, 0), 0.62, fc='white')
    fig.gca().add_artist(centre_circle)
    ax.axis('equal')
    fig.patch.set_alpha(0.0)
    ax.set_facecolor('none')
    plt.tight_layout(pad=0)
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=200, bbox_inches='tight', 
                transparent=True, pad_inches=0)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    
    return f"data:image/png;base64,{image_base64}"


def get_methodology_content(quiz_data: dict, risk_profile: str = None) -> dict:
    """
    Generate dynamic methodology content based on risk profile and time horizon
    
    Args:
        quiz_data: User quiz data
        risk_profile: Override risk profile (useful when using API data)
    """
    if risk_profile is None:
        risk_profile = quiz_data.get('risk_profile', 'Moderate')
    time_horizon = quiz_data.get('time_horizon', '3-5 years')
    
    # Categorize time horizon
    if '10+' in time_horizon or 'more than 10' in time_horizon.lower():
        time_category = 'long'
    elif any(x in time_horizon.lower() for x in ['5+', '5-7', '5-10', '6-10', '7-10', '5 years', '7 years', '10 years']):
        time_category = 'medium'
    else:
        time_category = 'short'
    methodology_map = {
        'Low': {
            'title': 'Global Diversification for Short-Term Preservation',
            'description': 'We construct this conservative portfolio with 50% global markets exposure and 40% bond allocation to prioritize capital preservation. The allocation emphasizes stability through fixed-income securities while maintaining modest growth potential through globally diversified equity ETFs. This balanced approach mitigates market volatility while providing steady, predictable returns.',
            'bullets': [
                'Prioritizes capital preservation and low volatility.',
                'Globally diversified across equities, bonds, and stable assets.',
                'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                'Strategic asset allocation tailored for 1-3 year horizons.'
            ]
        },
        'Moderate': {
            'short': {
                'title': 'Global Diversification for Short-Term Preservation',
                'description': 'We construct this balanced portfolio with 50% US equities as the core holding, complemented by strategic allocations to technology and emerging markets (10% each), and 30% bonds for stability. This mix targets steady growth while managing downside risk through diversified bond exposure and sector allocation across domestic and international markets.',
                'bullets': [
                    'Balances growth potential with capital preservation.',
                    'Globally diversified across equities, bonds, and growth sectors.',
                    'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                    'Strategic asset allocation tailored for 1-3 year horizons.'
                ]
            },
            'medium': {
                'title': 'Global Diversification for Mid-Term Preservation',
                'description': 'We construct this balanced portfolio with 50% US equities as the core holding, strategically enhanced by technology and emerging market exposure (10% each), and stabilized with 30% bonds. This allocation balances growth potential with risk management, providing steady wealth accumulation through diversified sector and geographic exposure.',
                'bullets': [
                    'Balances growth and stability for mid-term goals.',
                    'Globally diversified across equities, bonds, and emerging markets.',
                    'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                    'Strategic asset allocation tailored for 5-10 year horizons.'
                ]
            },
            'long': {
                'title': 'Global Diversification for Long-Term Preservation',
                'description': 'We construct this balanced portfolio with 50% US equities as the foundation, augmented by technology and emerging market allocations (10% each), and anchored by 30% bonds. This long-term allocation emphasizes consistent growth through diversified equity exposure while maintaining stability through strategic fixed-income positioning.',
                'bullets': [
                    'Balances growth and stability for long-term horizons.',
                    'Globally diversified across equities, bonds, and international markets.',
                    'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                    'Strategic asset allocation optimized for 10+ year horizons.'
                ]
            }
        },
        'High': {
            'short': {
                'title': 'Global Diversification for Short-Term Preservation',
                'description': 'We construct this growth-focused portfolio with 50% US equities and 30% technology exposure to maximize capital appreciation. Strategic allocation to emerging markets (10%) provides additional growth potential, with minimal bond exposure (10%) for stability during market volatility. This aggressive positioning targets maximum returns through concentrated exposure to high-growth sectors.',
                'bullets': [
                    'Maximizes growth potential through strategic concentration.',
                    'Globally diversified across technology and emerging markets.',
                    'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                    'Aggressive asset allocation optimized for 1-3 year horizons.'
                ]
            },
            'medium': {
                'title': 'Global Diversification for Mid-Term Aggressive Growth',
                'description': 'This aggressive growth portfolio combines high-growth emerging markets, technology innovation, and alternative assets (commodities) to maximize capital appreciation over a 5+ year horizon. By maintaining equal weightings across these three pillars, we capture growth from technological advancement, emerging economy expansion, and inflation-hedging commodities. This concentrated strategy foregoes bonds entirely in favor of maximum growth potential, suitable for investors with high risk tolerance and long-term wealth-building goals.',
                'bullets': [
                    'Maximizes long-term growth through high-conviction asset classes.',
                    'Globally diversified across emerging markets, technology, and commodities.',
                    'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                    'Aggressive 100% equity allocation optimized for 5+ year horizons.'
                ]
            },
            'long': {
                'title': 'Global Diversification for Long-Term Preservation',
                'description': 'We construct this growth-focused portfolio with 50% US equities and 30% technology exposure to maximize long-term capital appreciation. Strategic emerging markets allocation (10%) captures high-growth opportunities, while minimal bond exposure (10%) provides stability. This aggressive positioning leverages technology innovation and emerging market growth for maximum wealth accumulation.',
                'bullets': [
                    'Maximizes long-term growth through aggressive positioning.',
                    'Globally diversified across technology and emerging markets.',
                    'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                    'Aggressive asset allocation optimized for 10+ year horizons.'
                ]
            }
        },
        'Custom': {
            'medium': {
                'title': 'Custom Diversified Portfolio for Mid-Term Growth',
                'description': 'This custom portfolio is strategically designed with a balanced allocation across multiple asset classes to optimize risk-adjusted returns. The portfolio combines growth-oriented equities with stability-focused bonds and alternative assets, creating a diversified approach suitable for investors seeking balanced growth with managed risk over a 5+ year horizon.',
                'bullets': [
                    'Custom asset allocation tailored to specific investment goals.',
                    'Globally diversified across equities, bonds, and alternative assets.',
                    'Utilizes cost-effective Exchange Traded Funds (ETFs).',
                    'Strategic balance between growth and stability for 5+ year horizons.'
                ]
            }
        }
    }
    
    if risk_profile == 'Low':
        content = methodology_map['Low']
    elif risk_profile == 'Moderate':
        content = methodology_map['Moderate'].get(time_category, methodology_map['Moderate']['medium'])
    elif risk_profile == 'Custom':
        content = methodology_map['Custom'].get(time_category, methodology_map['Custom']['medium'])
    else:
        content = methodology_map['High'].get(time_category, methodology_map['High']['medium'])
    
    return content


def fetch_expense_ratio(ticker: str) -> str:
    # Special case: Gold ETC not available in yfinance
    if ticker == "IGLN.L":
        return "0.12%"
    
    try:
        etf = yf.Ticker(ticker)
        info = etf.info
        
        expense_ratio = info.get('expenseRatio') or info.get('netExpenseRatio')
        
        if expense_ratio is not None:
            if 'netExpenseRatio' in info and info['netExpenseRatio'] is not None:
                # netExpenseRatio is already in percentage form
                return f"{expense_ratio:.2f}%"
            else:
                # expenseRatio is in decimal form, multiply by 100
                return f"{expense_ratio * 100:.2f}%"
        else:
            return "N/A"
    except Exception as e:
        return "N/A"

# paasa Logo
def get_logo_base64() -> str: 
    logo_path = os.path.join(os.path.dirname(__file__), 'utils', 'Logo.png')
    try:
        with open(logo_path, 'rb') as f:
            logo_data = f.read()
            logo_base64 = base64.b64encode(logo_data).decode()
            return f"data:image/png;base64,{logo_base64}"
    except Exception as e:
        print(f"Error loading logo: {e}")
        return ""


def get_portfolio_data(quiz_data: dict, portfolio_id: int) -> dict:
    """
    Get all data needed for portfolio template
    
    Args:
        quiz_data: User input (name, email, age, investment_amount, time_horizon, preferred_topics, etc.)
        portfolio_id: Portfolio ID to fetch from API (required)
    """
    api_data = fetch_from_api(portfolio_id)
    
    if not api_data:
        api_data = {}
    holdings = []
    portfolio_holdings = api_data.get("holdings", [])
    for h in portfolio_holdings[:8]:
        ticker = h.get("ticker", "N/A")
        position = h.get("position", "-")
        
        expense_ratio = fetch_expense_ratio(ticker)
        
        holdings.append({
            "symbol": ticker,
            "name": h.get("name", "N/A"),
            "category": h.get("category_name", "N/A"),
            "expense_ratio": expense_ratio,
            "allocation": f"{position}%"
        })
    holdings_rows = ""
    for h in holdings:
        holdings_rows += f"""<tr>
            <td><a href="#" class="symbol-link">{h['symbol']}</a></td>
            <td>{h['name']}</td>
            <td>{h['category']}</td>
            <td>{h['expense_ratio']}</td>
            <td>{h['allocation']}</td>
        </tr>"""
    
    regions = api_data.get("regions", [])
    geographic_rows = ""
    for r in regions[:5]:
        name = r.get("name", "N/A")
        weight = r.get("size", 0)
        geographic_rows += f"""<tr>
            <td>{name}</td>
            <td>{weight:.1f}%</td>
        </tr>"""
    
    top_stocks = api_data.get("underlying_stocks", [])
    top_holdings_rows = ""
    for s in top_stocks[:10]:
        name = s.get("symbol", "N/A")
        weight = s.get("weight", 0)
        top_holdings_rows += f"""<tr>
            <td>{name}</td>
            <td>{weight:.2f}%</td>
        </tr>"""
    asset_classes = {}
    for h in portfolio_holdings:
        ac = h.get("category_name", "N/A")
        weight = h.get("position", 0)
        asset_classes[ac] = asset_classes.get(ac, 0) + weight
    
    allocation_labels = list(asset_classes.keys())
    allocation_values = list(asset_classes.values())
    
    allocation_data = {
        "labels": allocation_labels,
        "values": allocation_values
    }
    allocation_legend = ""
    for label in allocation_labels:
        color = CATEGORY_COLORS.get(label, DEFAULT_CATEGORY_COLOR)
        allocation_legend += f"""<div class="allocation-legend-item">
            <span class="legend-dot" style="background-color: {color};"></span>
            <span>{label}</span>
        </div>"""
    
    returns_data = api_data.get("portfolioReturns", {})
    benchmark_data = api_data.get("benchmarkReturns", {})
    
    if returns_data and not benchmark_data:
        all_dates = sorted(returns_data.keys())
        if all_dates:
            start_date = all_dates[0]
            end_date = all_dates[-1]
            benchmark_data = fetch_sp500_data(start_date, end_date)
    if returns_data and isinstance(returns_data, dict):
        all_dates = sorted(returns_data.keys())
        num_points = min(252, max(60, len(all_dates)))
        dates = all_dates[-num_points:]
        
        portfolio_values = []
        benchmark_values = []
        portfolio_base = 10000
        benchmark_base = 10000
        matched_dates = []
        
        for d in dates:
            p_return = returns_data.get(d, 0)
            b_return = benchmark_data.get(d, 0) if isinstance(benchmark_data, dict) else 0
            
            if p_return != 0 or b_return != 0:
                portfolio_base *= (1 + p_return)
                benchmark_base *= (1 + b_return)
                
                portfolio_values.append(round(portfolio_base, 2))
                benchmark_values.append(round(benchmark_base, 2))
                matched_dates.append(d)
        
        formatted_dates = []
        for d in matched_dates:
            try:
                dt = datetime.strptime(d, "%Y-%m-%d")
                formatted_dates.append(dt.strftime("%b\n%Y"))
            except:
                formatted_dates.append(d)
        
        performance_data = {
            "labels": formatted_dates,
            "portfolio": portfolio_values,
            "benchmark": benchmark_values
        }
    else:
        # No performance data available - chart will not be rendered
        performance_data = None
    # Use API's risk_level if available, otherwise map from portfolio_id
    api_risk_level = api_data.get("risk_level", "").lower()
    if api_risk_level == "high":
        risk_profile = "High"
    elif api_risk_level == "low":
        risk_profile = "Low"
    elif api_risk_level == "medium" or api_risk_level == "moderate":
        risk_profile = "Moderate"
    elif api_risk_level == "custom":
        risk_profile = "Custom"  # Show "Custom" for custom portfolios
    else:
        # Fallback to portfolio_id mapping
        risk_profile = quiz_data.get("risk_profile", "-")
        if portfolio_id == 1:
            risk_profile = "Low"
        elif portfolio_id == 3:
            risk_profile = "High"
    
    # Only generate charts if we have data
    performance_chart = generate_performance_chart(performance_data) if performance_data else ""
    allocation_chart_image = generate_donut_chart(allocation_data) if allocation_labels and allocation_values else ""
    
    # Get portfolio metrics from API
    five_yr = api_data.get("five_yr_annualized")
    three_yr = api_data.get("three_yr_annualized")
    one_yr = api_data.get("one_yr_annualized")
    vol = api_data.get("volatility")
    
    # Get benchmark data from API only - NO hardcoding
    benchmark_info = api_data.get("benchmark", {})
    benchmark_five_yr = benchmark_info.get("five_yr_annualized")
    benchmark_vol = benchmark_info.get("volatility")
    
    # Calculate 3YR benchmark from S&P 500 daily returns if we have them
    benchmark_three_yr = None
    if benchmark_data and isinstance(benchmark_data, dict):
        # Get last 3 years of data (roughly 756 trading days)
        all_benchmark_dates = sorted(benchmark_data.keys())
        if len(all_benchmark_dates) >= 252 * 3:  # At least 3 years of data
            three_year_dates = all_benchmark_dates[-(252 * 3):]
            benchmark_base = 1.0
            for d in three_year_dates:
                benchmark_base *= (1 + benchmark_data.get(d, 0))
            # Annualize: ((final_value)^(1/3)) - 1
            benchmark_three_yr = ((benchmark_base ** (1/3)) - 1) * 100
    
    # Format values - show N/A if not available
    five_year_return = f"+{five_yr:.1f}%" if five_yr is not None else "N/A"
    three_year_return = f"+{three_yr:.1f}%" if three_yr is not None else "N/A"
    five_year_volatility = f"+{vol:.1f}%" if vol is not None else "N/A"
    
    # Benchmark values from API only
    five_year_return_benchmark = f"+{benchmark_five_yr:.1f}%" if benchmark_five_yr is not None else "N/A"
    three_year_benchmark = f"+{benchmark_three_yr:.1f}%" if benchmark_three_yr is not None else "N/A"
    five_year_vol_benchmark = f"+{benchmark_vol:.1f}%" if benchmark_vol is not None else "N/A"
    
    logo_path = get_logo_base64()
    preferred_topics = quiz_data.get("preferred_topics", [])
    dynamic_themes = []
    
    holding_categories = []
    for h in portfolio_holdings[:3]:
        cat = h.get("category_name", "")
        if cat and cat not in holding_categories:
            simplified = cat.replace(" ETFs", "").replace("markets", "Markets")
            holding_categories.append(simplified)
    dynamic_themes.extend(holding_categories)
    
    region_themes = []
    for r in regions[:2]:
        region_name = r.get("name", "")
        if region_name and region_name not in region_themes:
            region_themes.append(region_name)
    dynamic_themes.extend(region_themes)
    
    for topic in preferred_topics[:5]:
        if topic and topic not in dynamic_themes:
            dynamic_themes.append(topic)
    
    filler_themes = ["Diversification", "Global Markets", "Cost-Effective ETFs", "Strategic Allocation", 
                     "Risk Management", "Capital Growth", "Market Exposure", "Asset Balance"]
    for filler in filler_themes:
        if len(dynamic_themes) >= 10:
            break
        if filler not in dynamic_themes:
            dynamic_themes.append(filler)
    
    all_themes = dynamic_themes[:10]
    themes_items = ""
    for theme in all_themes:
        themes_items += f'<div class="theme-item">{theme}</div>'
    
    methodology_content = get_methodology_content(quiz_data, risk_profile=risk_profile)
    methodology_bullets_html = "\n".join([f'<li>{bullet}</li>' for bullet in methodology_content['bullets']])
    # Handle investment_amount - convert string to number if needed
    inv_amount_raw = quiz_data.get('investment_amount', None)
    if inv_amount_raw is None:
        inv_amount_str = "-"
    elif isinstance(inv_amount_raw, str):
        inv_amount_raw = inv_amount_raw.replace('$', '').replace(',', '').strip()
        try:
            inv_amount = float(inv_amount_raw)
            inv_amount_str = f"{inv_amount:,.0f}"
        except:
            inv_amount_str = "-"
    else:
        # Already a number
        inv_amount_str = f"{inv_amount_raw:,.0f}"
    
    template_data = {
        "report_date": datetime.now().strftime("%d %B %Y"),
        "investor_name": quiz_data.get("name", "-"),
        "email": quiz_data.get("email", "-"),
        "age": quiz_data.get("age", "-"),
        "investment_amount": inv_amount_str,
        "time_horizon": quiz_data.get("time_horizon", "-"),
        "risk_profile": risk_profile,
        "logo_path": logo_path,
        "holdings_rows": holdings_rows,
        "performance_chart": performance_chart,
        "allocation_chart": allocation_chart_image,
        "allocation_legend": allocation_legend,
        "five_year_return": five_year_return,
        "five_year_return_benchmark": five_year_return_benchmark,
        "three_year_return": three_year_return,
        "three_year_benchmark": three_year_benchmark,
        "five_year_volatility": five_year_volatility,
        "five_year_vol_benchmark": five_year_vol_benchmark,
        "geographic_rows": geographic_rows,
        "top_holdings_rows": top_holdings_rows,
        "themes_items": themes_items,
        "methodology_title": methodology_content['title'],
        "methodology_description": methodology_content['description'],
        "methodology_bullets": methodology_bullets_html,
    }
    
    return template_data
