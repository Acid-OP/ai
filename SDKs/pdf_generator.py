import os
import re
import tempfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
matplotlib.use('Agg')
from fpdf import FPDF
import yfinance as yf
import pandas as pd
import numpy as np

# Paasa Brand Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (23, 23, 23)
GRAY = (102, 102, 102)
LIGHT_GRAY = (170, 170, 170)
BG_GRAY = (247, 250, 252)
ACCENT = (0, 136, 255)

# Chart colors
PORTFOLIO_BLUE = '#0088ff'
SP500_RED = '#dc2626'
GREEN = '#16a34a'
BOND_ORANGE = '#f97316'

# Logo path
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'Logo.png')

# ETF ticker mapping
ETF_TICKER_MAP = {
    'vanguard ftse all-world': 'VWCE.DE',
    'ishares core msci world': 'IWDA.AS',
    'ishares msci world': 'IWDA.AS',
    'ishares core global aggregate bond': 'AGGH.L',
    'ishares global aggregate bond': 'AGGH.L',
    'xtrackers global aggregate bond': 'XGAG.DE',
    'spdr bloomberg global aggregate': 'GLAE.L',
    'ishares core msci emerging markets': 'EIMI.L',
    'ishares msci emerging markets': 'IEMG',
    'xtrackers msci world information technology': 'XDWT.DE',
    'ishares s&p 500 information technology': 'IUIT.L',
    'l&g global technology': 'IITU.L',
    'ishares global healthcare': 'IXJ',
    'ishares healthcare innovation': 'HEAL.L',
    'xtrackers msci world health care': 'XDWH.DE',
    'ishares global clean energy': 'ICLN',
    'invesco global clean energy': 'GCLE.L',
    'l&g clean water': 'GLUG.L',
    'ishares global water': 'IH2O.L',
    'global x uranium': 'URA',
    'xtrackers msci world industrials': 'XDWI.DE',
    'han-gins tech megatrend': 'ITEK.L',
    'ishares global corporate bond': 'CORP.L',
    'vanguard ftse developed world': 'VEVE.L',
    'ishares electric vehicles': 'ECAR.L',
    'vaneck electric vehicles': 'DRIV',
}


class PaasaPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header_bar(self):
        self.set_fill_color(*BLACK)
        self.rect(0, 0, 210, 28, 'F')
        # Logo
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=15, y=6, h=16)
        else:
            self.set_text_color(*WHITE)
            self.set_font('Helvetica', 'B', 18)
            self.set_xy(15, 8)
            self.cell(0, 10, 'Paasa')
        # Date
        self.set_text_color(*WHITE)
        self.set_font('Helvetica', '', 9)
        self.set_xy(155, 10)
        self.cell(0, 8, datetime.now().strftime('%B %d, %Y'))
        self.set_y(35)
        self.set_text_color(*DARK_GRAY)
    
    def section_title(self, title):
        self.ln(6)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*DARK_GRAY)
        self.cell(0, 7, title, ln=True)
        self.ln(3)
    
    def label_value(self, label, value, bold_value=False):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*GRAY)
        self.cell(48, 5, label)
        self.set_text_color(*DARK_GRAY)
        if bold_value:
            self.set_font('Helvetica', 'B', 9)
        self.cell(45, 5, str(value), ln=True)


def get_etf_ticker(etf_name):
    name_lower = etf_name.lower()
    for key, ticker in ETF_TICKER_MAP.items():
        if key in name_lower:
            return ticker
    return None


def fetch_backtest_data(etfs, years=3):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    sp500 = None
    try:
        sp500_raw = yf.download('^GSPC', start=start_date, end=end_date, progress=False)
        if not sp500_raw.empty:
            close = sp500_raw['Close']
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            first_val = float(close.iloc[0])
            sp500 = (close / first_val * 100).squeeze()
    except:
        pass
    
    portfolio_data = None
    total_weight = 0
    
    for etf in etfs:
        ticker = get_etf_ticker(etf['name'])
        if not ticker:
            continue
        try:
            raw = yf.download(ticker, start=start_date, end=end_date, progress=False)
            if raw.empty:
                continue
            close = raw['Close']
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            if len(close) > 100:
                first_val = float(close.iloc[0])
                normalized = (close / first_val * 100).squeeze()
                weight = etf['allocation'] / 100
                if portfolio_data is None:
                    portfolio_data = normalized * weight
                else:
                    common_idx = portfolio_data.index.intersection(normalized.index)
                    portfolio_data = portfolio_data.loc[common_idx] + normalized.loc[common_idx] * weight
                total_weight += weight
        except:
            continue
    
    if portfolio_data is not None and total_weight > 0:
        portfolio_data = portfolio_data / total_weight
    
    return portfolio_data, sp500


def create_backtest_chart(portfolio_data, sp500_data, investment_amount):
    fig, ax = plt.subplots(figsize=(5.2, 2.5), dpi=120)
    
    portfolio_return = None
    sp500_return = None
    
    try:
        if sp500_data is not None and len(sp500_data) > 0:
            sp500_dollars = sp500_data * (investment_amount / 100)
            ax.plot(sp500_data.index, sp500_dollars.values, color=SP500_RED, 
                    linewidth=2, label='S&P 500')
            sp500_return = (float(sp500_data.iloc[-1]) / 100 - 1) * 100
    except:
        pass
    
    try:
        if portfolio_data is not None and len(portfolio_data) > 0:
            portfolio_dollars = portfolio_data * (investment_amount / 100)
            ax.plot(portfolio_data.index, portfolio_dollars.values, color=PORTFOLIO_BLUE, 
                    linewidth=2.5, label='Your Portfolio')
            portfolio_return = (float(portfolio_data.iloc[-1]) / 100 - 1) * 100
    except:
        pass
    
    if portfolio_return is None and sp500_return is None:
        plt.close()
        return None, None, None
    
    ax.axhline(y=investment_amount, color='#d1d5db', linestyle='--', linewidth=1, alpha=0.7)
    
    ax.set_ylabel('Value ($)', fontsize=8, color='#666')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors='#666', labelsize=7)
    ax.grid(axis='y', alpha=0.3, color='#e5e7eb')
    ax.set_axisbelow(True)
    
    leg = ax.legend(loc='upper left', fontsize=8, frameon=True, 
                    facecolor='white', edgecolor='#e5e7eb', ncol=2)
    leg.get_frame().set_linewidth(0.5)
    
    plt.xticks(rotation=0)
    plt.tight_layout(pad=0.3)
    
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=120, facecolor='white')
    plt.close()
    
    return path, portfolio_return, sp500_return


def create_allocation_donut(equity_pct, bond_pct, total):
    fig, ax = plt.subplots(figsize=(2.2, 2.2), dpi=100)
    
    sizes = [equity_pct, bond_pct] if bond_pct > 0 else [100]
    colors = [PORTFOLIO_BLUE, BOND_ORANGE] if bond_pct > 0 else [PORTFOLIO_BLUE]
    
    ax.pie(sizes, colors=colors, startangle=90,
           wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))
    
    ax.text(0, 0.05, f'${total:,.0f}', ha='center', va='center', 
            fontsize=14, fontweight='bold', color='#171717')
    ax.text(0, -0.18, 'Total', ha='center', va='center', 
            fontsize=8, color='#666')
    
    plt.tight_layout(pad=0)
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=100, facecolor='white')
    plt.close()
    return path


def create_scenario_chart(equity_pct, bond_pct):
    fig, ax = plt.subplots(figsize=(4, 1.6), dpi=100)
    
    eq = equity_pct / 100
    bd = bond_pct / 100
    best = eq * 28 + bd * 10
    avg = eq * 9 + bd * 4
    worst = eq * -22 + bd * -2
    
    scenarios = ['Worst', 'Average', 'Best']
    values = [worst, avg, best]
    colors = [SP500_RED, PORTFOLIO_BLUE, GREEN]
    
    bars = ax.barh(scenarios, values, color=colors, height=0.55, edgecolor='none')
    
    for bar, val in zip(bars, values):
        if val >= 0:
            xpos = bar.get_width() + 1
        else:
            xpos = bar.get_width() - 4
        ax.text(xpos, bar.get_y() + bar.get_height()/2,
                f'{val:+.0f}%', va='center', fontsize=9, fontweight='bold',
                color=bar.get_facecolor())
    
    ax.axvline(x=0, color='#d1d5db', linewidth=1)
    # Fixed: extend x-axis to show full worst bar
    ax.set_xlim(min(values) - 12, max(values) + 10)
    
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.set_xticks([])
    ax.tick_params(axis='y', labelsize=9, colors='#171717')
    
    plt.tight_layout(pad=0.2)
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=100, facecolor='white')
    plt.close()
    return path, best, avg, worst


def parse_response(text, profile):
    data = {
        'amount': profile.get('amount', 5000),
        'goal': profile.get('goal', ''),
        'horizon': profile.get('time_horizon', ''),
        'behavior': profile.get('risk_behavior', ''),
        'equity_pct': 60,
        'bond_pct': 40,
        'expected_return': '',
        'volatility': '',
        'etfs': [],
    }
    
    match = re.search(r'Equity/Bond Split:\s*(\d+)%?\s*/\s*(\d+)%?', text)
    if match:
        data['equity_pct'] = int(match.group(1))
        data['bond_pct'] = int(match.group(2))
    
    match = re.search(r'Expected Return:\s*([\d\-\.\s%]+)', text)
    if match:
        data['expected_return'] = match.group(1).strip()
    
    match = re.search(r'Volatility:\s*(\w+)', text)
    if match:
        data['volatility'] = match.group(1)
    
    pattern = r'([A-Za-z][A-Za-z0-9\s&\-\']+(?:UCITS|ETF)[A-Za-z0-9\s\(\)\-]*)\s*-\s*(\d+)%\s*\(\$?([\d,\.]+)\)'
    matches = re.findall(pattern, text)
    
    seen = set()
    for name, alloc, amount in matches:
        name = name.strip()
        if name.lower().startswith('this etf') or name.lower().startswith('why'):
            continue
        if name not in seen and len(name) > 15:
            seen.add(name)
            pos = text.lower().find(name.lower())
            before = text[:pos].lower() if pos > 0 else ''
            is_thematic = 'thematic' in before[-400:]
            data['etfs'].append({
                'name': name,
                'allocation': float(alloc),
                'amount': float(amount.replace(',', '')),
                'is_thematic': is_thematic
            })
    
    return data


def generate_portfolio_pdf(response_text, profile, output_path="portfolio.pdf"):
    """Generate Paasa branded portfolio PDF"""
    
    data = parse_response(response_text, profile)
    
    print("Fetching historical data for backtesting...")
    portfolio_data, sp500_data = fetch_backtest_data(data['etfs'], years=3)
    
    # Generate charts
    alloc_chart = create_allocation_donut(data['equity_pct'], data['bond_pct'], data['amount'])
    scenario_chart, best, avg, worst = create_scenario_chart(data['equity_pct'], data['bond_pct'])
    backtest_chart, portfolio_return, sp500_return = create_backtest_chart(
        portfolio_data, sp500_data, data['amount']
    )
    
    pdf = PaasaPDF()
    
    # === PAGE 1 ===
    pdf.add_page()
    pdf.header_bar()
    
    # Title
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*DARK_GRAY)
    pdf.cell(0, 10, 'Investment Portfolio Report', ln=True)
    pdf.ln(2)
    
    # Profile section
    pdf.section_title('Investment Profile')
    pdf.label_value('Goal', data['goal'], True)
    pdf.label_value('Time Horizon', data['horizon'])
    pdf.label_value('Risk Behavior', data['behavior'])
    pdf.label_value('Investment', f"${data['amount']:,.2f}", True)
    
    # Summary section (inline with chart)
    summary_start_y = pdf.get_y()
    pdf.section_title('Portfolio Summary')
    pdf.label_value('Total ETFs', f"{len(data['etfs'])}")
    pdf.label_value('Equity', f"{data['equity_pct']}%", True)
    pdf.label_value('Bonds', f"{data['bond_pct']}%")
    if data['expected_return']:
        pdf.label_value('Expected Return', data['expected_return'])
    summary_end_y = pdf.get_y()
    
    # Allocation chart on right (position relative to Investment Profile start)
    if alloc_chart and os.path.exists(alloc_chart):
        pdf.image(alloc_chart, x=145, y=42, w=45)
        os.remove(alloc_chart)
    
    # Allocation legend below chart
    pdf.set_xy(140, 92)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_fill_color(0, 136, 255)
    pdf.cell(3, 3, '', 0, 0, 'L', True)
    pdf.set_text_color(*GRAY)
    pdf.cell(22, 3, f' Equity {data["equity_pct"]}%')
    pdf.set_xy(167, 92)
    pdf.set_fill_color(249, 115, 22)
    pdf.cell(3, 3, '', 0, 0, 'L', True)
    pdf.cell(22, 3, f' Bonds {data["bond_pct"]}%')
    
    # IMPORTANT: Set Y below both summary AND chart area
    pdf.set_y(max(summary_end_y, 100) + 10)
    
    # Holdings Table
    pdf.section_title('Holdings')
    
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(*BLACK)
    pdf.set_text_color(*WHITE)
    col_w = [8, 95, 18, 25, 18]
    headers = ['#', 'ETF', 'Weight', 'Amount', 'Type']
    for w, h in zip(col_w, headers):
        pdf.cell(w, 6, h, 0, 0, 'L', True)
    pdf.ln()
    
    pdf.set_text_color(*DARK_GRAY)
    for i, etf in enumerate(data['etfs'][:7], 1):
        pdf.set_font('Helvetica', '', 8)
        if i % 2 == 0:
            pdf.set_fill_color(*BG_GRAY)
            fill = True
        else:
            fill = False
        
        etype = 'T' if etf['is_thematic'] else 'C'
        name = etf['name'][:50] if len(etf['name']) > 50 else etf['name']
        
        pdf.cell(col_w[0], 5, str(i), 0, 0, 'L', fill)
        pdf.cell(col_w[1], 5, name, 0, 0, 'L', fill)
        pdf.cell(col_w[2], 5, f"{etf['allocation']:.0f}%", 0, 0, 'L', fill)
        pdf.cell(col_w[3], 5, f"${etf['amount']:,.0f}", 0, 0, 'L', fill)
        pdf.cell(col_w[4], 5, etype, 0, 0, 'L', fill)
        pdf.ln()
    
    # Type legend
    pdf.ln(2)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 4, 'C = Core (stable base)  |  T = Thematic (growth sectors)', ln=True)
    
    # Expected scenarios
    pdf.section_title('Expected Annual Returns')
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 4, f'Based on {data["equity_pct"]}% equity / {data["bond_pct"]}% bond allocation:', ln=True)
    pdf.ln(2)
    
    scenario_y = pdf.get_y()
    if scenario_chart and os.path.exists(scenario_chart):
        pdf.image(scenario_chart, x=15, w=78)
        os.remove(scenario_chart)
    
    # Metrics box
    pdf.set_fill_color(*BG_GRAY)
    pdf.rect(100, scenario_y, 50, 24, 'F')
    pdf.set_xy(104, scenario_y + 3)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(25, 4, 'Best Year')
    pdf.set_text_color(22, 163, 74)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(0, 4, f'+{best:.0f}%')
    pdf.set_xy(104, scenario_y + 10)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(25, 4, 'Average')
    pdf.set_text_color(0, 136, 255)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(0, 4, f'+{avg:.0f}%')
    pdf.set_xy(104, scenario_y + 17)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(25, 4, 'Worst Year')
    pdf.set_text_color(220, 38, 38)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(0, 4, f'{worst:.0f}%')
    
    # === PAGE 2 ===
    pdf.add_page()
    pdf.header_bar()
    
    # Backtest section
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*DARK_GRAY)
    pdf.cell(0, 10, 'Backtested Performance', ln=True)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 5, 'Historical simulation: how your portfolio would have performed over 3 years', ln=True)
    pdf.ln(4)
    
    if backtest_chart and os.path.exists(backtest_chart):
        chart_y = pdf.get_y()
        pdf.image(backtest_chart, x=15, w=115)
        os.remove(backtest_chart)
        
        # Returns box
        pdf.set_fill_color(*BG_GRAY)
        pdf.rect(135, chart_y, 60, 48, 'F')
        
        pdf.set_xy(140, chart_y + 5)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(0, 5, '3-Year Returns')
        
        if portfolio_return is not None:
            pdf.set_xy(140, chart_y + 15)
            pdf.set_fill_color(0, 136, 255)
            pdf.cell(3, 3, '', 0, 0, 'L', True)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*GRAY)
            pdf.cell(28, 4, ' Portfolio')
            color = (22, 163, 74) if portfolio_return >= 0 else (220, 38, 38)
            pdf.set_text_color(*color)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 4, f'{portfolio_return:+.1f}%')
        
        if sp500_return is not None:
            pdf.set_xy(140, chart_y + 24)
            pdf.set_fill_color(220, 38, 38)
            pdf.cell(3, 3, '', 0, 0, 'L', True)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*GRAY)
            pdf.cell(28, 4, ' S&P 500')
            color = (22, 163, 74) if sp500_return >= 0 else (220, 38, 38)
            pdf.set_text_color(*color)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 4, f'{sp500_return:+.1f}%')
        
        if portfolio_return is not None and sp500_return is not None:
            diff = portfolio_return - sp500_return
            pdf.set_xy(140, chart_y + 35)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*GRAY)
            pdf.cell(31, 4, 'Difference')
            color = (22, 163, 74) if diff >= 0 else (220, 38, 38)
            pdf.set_text_color(*color)
            pdf.set_font('Helvetica', 'B', 9)
            sign = '+' if diff >= 0 else ''
            pdf.cell(0, 4, f'{sign}{diff:.1f}%')
        
        pdf.set_y(chart_y + 55)
    
    pdf.ln(5)
    
    # Themes covered
    pdf.section_title('Themes Covered')
    all_themes = (profile.get('regions', []) + profile.get('sectors', []) + 
                  profile.get('trends', []) + profile.get('commodities', []))
    
    pdf.set_font('Helvetica', '', 9)
    col = 0
    for theme in all_themes[:12]:
        if col == 3:
            pdf.ln(5)
            col = 0
        pdf.set_x(15 + col * 62)
        pdf.set_text_color(22, 163, 74)
        pdf.cell(3, 5, '>')
        pdf.set_text_color(*DARK_GRAY)
        pdf.cell(55, 5, theme[:22])
        col += 1
    
    pdf.ln(10)
    
    # Getting started
    pdf.section_title('Next Steps')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*DARK_GRAY)
    
    steps = [
        f'1. Open a brokerage account with UCITS ETF access',
        f'2. Transfer ${data["amount"]:,.0f} to your account',
        f'3. Purchase ETFs in the allocations shown',
        f'4. Rebalance annually (or when drifting >5%)'
    ]
    for step in steps:
        pdf.cell(0, 5, step, ln=True)
    
    pdf.ln(4)
    
    # Cost
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(35, 5, 'Annual Cost:')
    pdf.set_font('Helvetica', '', 9)
    annual_cost = data['amount'] * 0.25 / 100
    pdf.cell(0, 5, f'~${annual_cost:.2f}/year (avg TER 0.25%)', ln=True)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(*LIGHT_GRAY)
    pdf.multi_cell(0, 3.5, 
        'Past performance does not guarantee future results. Backtested returns are simulated using historical data. '
        'This is not financial advice. Consult a qualified advisor before investing. '
        'Paasa, Inc. | support@paasa.com', align='C')
    
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    test_response = """
    Core Holdings (65%) - $3250
    Vanguard FTSE All-World UCITS ETF - 35% ($1750)
    iShares Core Global Aggregate Bond UCITS ETF - 30% ($1500)
    
    Thematic Holdings (35%) - $1750
    Xtrackers MSCI World Information Technology UCITS ETF - 12% ($600)
    iShares Healthcare Innovation UCITS ETF - 10% ($500)
    iShares Global Clean Energy UCITS ETF - 8% ($400)
    Global X Uranium UCITS ETF - 5% ($250)
    
    Equity/Bond Split: 70% / 30%
    Expected Return: 6-8%
    Volatility: Medium
    """
    
    test_profile = {
        'goal': 'Grow with caution',
        'time_horizon': '6-10 years',
        'risk_behavior': "I'll do nothing",
        'amount': 5000,
        'regions': ['World', 'Emerging markets'],
        'sectors': ['Healthcare', 'Technology'],
        'trends': ['Nuclear Energy', 'Clean Energy'],
        'commodities': ['Uranium', 'Water']
    }
    
    generate_portfolio_pdf(test_response, test_profile, "paasa_portfolio.pdf")
