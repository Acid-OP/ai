import os
import tempfile
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib
matplotlib.use('Agg')
from fpdf import FPDF
import yfinance as yf
import pandas as pd

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (23, 23, 23)
GRAY = (102, 102, 102)
LIGHT_GRAY = (170, 170, 170)
BG_GRAY = (247, 250, 252)
PORTFOLIO_BLUE = '#0088ff'
SP500_RED = '#dc2626'
GREEN = '#16a34a'
BOND_ORANGE = '#f97316'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, 'utils', 'Logo.png')

# ETF ticker mapping for backtest charts
ETF_TICKER_MAP = {
    'vanguard ftse all-world': 'VWCE.DE',
    'ishares core msci world': 'IWDA.AS',
    'ishares core global aggregate bond': 'AGGH.L',
    'ishares core msci emerging markets': 'EIMI.L',
    'ishares msci emerging markets': 'IEMG',
    'ishares global healthcare': 'IXJ',
    'ishares healthcare innovation': 'HEAL.L',
    'ishares global clean energy': 'ICLN',
    'l&g clean water': 'GLUG.L',
    'ishares global water': 'IH2O.L',
    'global x uranium': 'URA',
    'ishares electric vehicles': 'ECAR.L',
}


class PaasaPDF(FPDF):
    """Custom PDF with Paasa branding"""
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header_bar(self):
        self.set_fill_color(*BLACK)
        self.rect(0, 0, 210, 28, 'F')
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=15, y=6, h=16)
        else:
            self.set_text_color(*WHITE)
            self.set_font('Helvetica', 'B', 18)
            self.set_xy(15, 8)
            self.cell(0, 10, 'Paasa')
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
    
    def label_value(self, label, value, bold=False):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*GRAY)
        self.cell(48, 5, label)
        self.set_text_color(*DARK_GRAY)
        if bold:
            self.set_font('Helvetica', 'B', 9)
        self.cell(45, 5, str(value), ln=True)


def get_etf_ticker(etf_name):
    name_lower = etf_name.lower()
    for key, ticker in ETF_TICKER_MAP.items():
        if key in name_lower:
            return ticker
    return None


def fetch_backtest_data(etfs, years=3):
    """Fetch historical data for charts"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    sp500 = None
    try:
        sp500_raw = yf.download('^GSPC', start=start_date, end=end_date, progress=False)
        if not sp500_raw.empty:
            close = sp500_raw['Close']
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            sp500 = (close / float(close.iloc[0]) * 100).squeeze()
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
                normalized = (close / float(close.iloc[0]) * 100).squeeze()
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


def create_backtest_chart(portfolio_data, sp500_data, amount):
    """Create backtest line chart"""
    fig, ax = plt.subplots(figsize=(5.2, 2.5), dpi=120)
    portfolio_return = sp500_return = None
    
    if sp500_data is not None and len(sp500_data) > 0:
        ax.plot(sp500_data.index, sp500_data.values * amount / 100, 
                color=SP500_RED, linewidth=2, label='S&P 500')
        sp500_return = (float(sp500_data.iloc[-1]) / 100 - 1) * 100
    
    if portfolio_data is not None and len(portfolio_data) > 0:
        ax.plot(portfolio_data.index, portfolio_data.values * amount / 100, 
                color=PORTFOLIO_BLUE, linewidth=2.5, label='Your Portfolio')
        portfolio_return = (float(portfolio_data.iloc[-1]) / 100 - 1) * 100
    
    if portfolio_return is None and sp500_return is None:
        plt.close()
        return None, None, None
    
    ax.axhline(y=amount, color='#d1d5db', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_ylabel('Value ($)', fontsize=8, color='#666')
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %y'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors='#666', labelsize=7)
    ax.grid(axis='y', alpha=0.3, color='#e5e7eb')
    ax.legend(loc='upper left', fontsize=8, frameon=True, facecolor='white')
    plt.tight_layout(pad=0.3)
    
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=120, facecolor='white')
    plt.close()
    return path, portfolio_return, sp500_return


def create_allocation_donut(equity_pct, bond_pct, total):
    """Create allocation donut chart"""
    fig, ax = plt.subplots(figsize=(2.2, 2.2), dpi=100)
    sizes = [equity_pct, bond_pct] if bond_pct > 0 else [100]
    colors = [PORTFOLIO_BLUE, BOND_ORANGE] if bond_pct > 0 else [PORTFOLIO_BLUE]
    ax.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))
    ax.text(0, 0.05, f'${total:,.0f}', ha='center', va='center', fontsize=14, fontweight='bold', color='#171717')
    ax.text(0, -0.18, 'Total', ha='center', va='center', fontsize=8, color='#666')
    plt.tight_layout(pad=0)
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=100, facecolor='white')
    plt.close()
    return path


def create_scenario_chart(equity_pct, bond_pct):
    """Create expected returns bar chart"""
    fig, ax = plt.subplots(figsize=(4, 1.6), dpi=100)
    eq, bd = equity_pct / 100, bond_pct / 100
    best = eq * 28 + bd * 10
    avg = eq * 9 + bd * 4
    worst = eq * -22 + bd * -2
    
    bars = ax.barh(['Worst', 'Average', 'Best'], [worst, avg, best], 
                   color=[SP500_RED, PORTFOLIO_BLUE, GREEN], height=0.55)
    for bar, val in zip(bars, [worst, avg, best]):
        xpos = bar.get_width() + 1 if val >= 0 else bar.get_width() - 4
        ax.text(xpos, bar.get_y() + bar.get_height()/2, f'{val:+.0f}%', 
                va='center', fontsize=9, fontweight='bold', color=bar.get_facecolor())
    
    ax.axvline(x=0, color='#d1d5db', linewidth=1)
    ax.set_xlim(min([worst, avg, best]) - 12, max([worst, avg, best]) + 10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.set_xticks([])
    plt.tight_layout(pad=0.2)
    
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=100, facecolor='white')
    plt.close()
    return path, best, avg, worst


def generate_pdf(json_data, output_path):
    """Generate complete PDF report from JSON data"""
    profile = json_data['profile']
    portfolio = json_data['portfolio']
    
    print("Fetching historical data for charts...")
    portfolio_series, sp500_series = fetch_backtest_data(portfolio['etfs'], years=3)
    
    # Create charts
    alloc_chart = create_allocation_donut(portfolio['equity_pct'], portfolio['bond_pct'], profile['amount'])
    scenario_chart, best, avg, worst = create_scenario_chart(portfolio['equity_pct'], portfolio['bond_pct'])
    backtest_chart, portfolio_return, sp500_return = create_backtest_chart(portfolio_series, sp500_series, profile['amount'])
    
    pdf = PaasaPDF()
    
    # PAGE 1
    pdf.add_page()
    pdf.header_bar()
    
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*DARK_GRAY)
    pdf.cell(0, 10, 'Investment Portfolio Report', ln=True)
    pdf.ln(2)
    
    # Profile section
    pdf.section_title('Investment Profile')
    pdf.label_value('Goal', profile['goal'], True)
    pdf.label_value('Time Horizon', profile['time_horizon'])
    pdf.label_value('Risk Behavior', profile['risk_behavior'])
    pdf.label_value('Investment', f"${profile['amount']:,.2f}", True)
    
    # Summary section
    pdf.section_title('Portfolio Summary')
    pdf.label_value('Total ETFs', f"{portfolio['total_etfs']}")
    pdf.label_value('Equity', f"{portfolio['equity_pct']}%", True)
    pdf.label_value('Bonds', f"{portfolio['bond_pct']}%")
    if portfolio['expected_return']:
        pdf.label_value('Expected Return', portfolio['expected_return'])
    summary_end_y = pdf.get_y()
    
    # Allocation chart
    if alloc_chart and os.path.exists(alloc_chart):
        pdf.image(alloc_chart, x=145, y=42, w=45)
        os.remove(alloc_chart)
    
    # Legend
    pdf.set_xy(140, 92)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_fill_color(0, 136, 255)
    pdf.cell(3, 3, '', 0, 0, 'L', True)
    pdf.set_text_color(*GRAY)
    pdf.cell(22, 3, f' Equity {portfolio["equity_pct"]}%')
    pdf.set_xy(167, 92)
    pdf.set_fill_color(249, 115, 22)
    pdf.cell(3, 3, '', 0, 0, 'L', True)
    pdf.cell(22, 3, f' Bonds {portfolio["bond_pct"]}%')
    
    pdf.set_y(max(summary_end_y, 100) + 10)
    
    # Holdings table
    pdf.section_title('Holdings')
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(*BLACK)
    pdf.set_text_color(*WHITE)
    for w, h in zip([8, 95, 18, 25, 18], ['#', 'ETF', 'Weight', 'Amount', 'Type']):
        pdf.cell(w, 6, h, 0, 0, 'L', True)
    pdf.ln()
    
    pdf.set_text_color(*DARK_GRAY)
    for i, etf in enumerate(portfolio['etfs'][:7], 1):
        pdf.set_font('Helvetica', '', 8)
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(*BG_GRAY)
        etype = 'T' if etf['type'] == 'Thematic' else 'C'
        name = etf['name'][:50]
        pdf.cell(8, 5, str(i), 0, 0, 'L', fill)
        pdf.cell(95, 5, name, 0, 0, 'L', fill)
        pdf.cell(18, 5, f"{etf['allocation']:.0f}%", 0, 0, 'L', fill)
        pdf.cell(25, 5, f"${etf['amount']:,.0f}", 0, 0, 'L', fill)
        pdf.cell(18, 5, etype, 0, 0, 'L', fill)
        pdf.ln()
    
    pdf.ln(2)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 4, 'C = Core (stable base)  |  T = Thematic (growth sectors)', ln=True)
    
    # Scenario section
    pdf.section_title('Expected Annual Returns')
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(0, 4, f'Based on {portfolio["equity_pct"]}% equity / {portfolio["bond_pct"]}% bond allocation:', ln=True)
    pdf.ln(2)
    
    scenario_y = pdf.get_y()
    if scenario_chart and os.path.exists(scenario_chart):
        pdf.image(scenario_chart, x=15, w=78)
        os.remove(scenario_chart)
    
    # Metrics box
    pdf.set_fill_color(*BG_GRAY)
    pdf.rect(100, scenario_y, 50, 24, 'F')
    for i, (label, val, color) in enumerate([('Best Year', f'+{best:.0f}%', (22, 163, 74)), 
                                              ('Average', f'+{avg:.0f}%', (0, 136, 255)),
                                              ('Worst Year', f'{worst:.0f}%', (220, 38, 38))]):
        pdf.set_xy(104, scenario_y + 3 + i*7)
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(*GRAY)
        pdf.cell(25, 4, label)
        pdf.set_text_color(*color)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(0, 4, val)
    
    # PAGE 2
    pdf.add_page()
    pdf.header_bar()
    
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
            pdf.set_text_color(*((22, 163, 74) if portfolio_return >= 0 else (220, 38, 38)))
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 4, f'{portfolio_return:+.1f}%')
        
        if sp500_return is not None:
            pdf.set_xy(140, chart_y + 24)
            pdf.set_fill_color(220, 38, 38)
            pdf.cell(3, 3, '', 0, 0, 'L', True)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*GRAY)
            pdf.cell(28, 4, ' S&P 500')
            pdf.set_text_color(*((22, 163, 74) if sp500_return >= 0 else (220, 38, 38)))
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 4, f'{sp500_return:+.1f}%')
        
        if portfolio_return is not None and sp500_return is not None:
            diff = portfolio_return - sp500_return
            pdf.set_xy(140, chart_y + 35)
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*GRAY)
            pdf.cell(31, 4, 'Difference')
            pdf.set_text_color(*((22, 163, 74) if diff >= 0 else (220, 38, 38)))
            pdf.set_font('Helvetica', 'B', 9)
            pdf.cell(0, 4, f'{diff:+.1f}%')
        
        pdf.set_y(chart_y + 55)
    
    pdf.ln(5)
    
    # Themes
    pdf.section_title('Themes Covered')
    all_themes = (profile['themes'].get('regions', []) + profile['themes'].get('sectors', []) + 
                  profile['themes'].get('trends', []) + profile['themes'].get('commodities', []))
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
    
    # Next steps
    pdf.section_title('Next Steps')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*DARK_GRAY)
    for step in [f'1. Open a brokerage account with UCITS ETF access',
                 f'2. Transfer ${profile["amount"]:,.0f} to your account',
                 f'3. Purchase ETFs in the allocations shown',
                 f'4. Rebalance annually (or when drifting >5%)']:
        pdf.cell(0, 5, step, ln=True)
    
    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(35, 5, 'Annual Cost:')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 5, f'~${profile["amount"] * 0.0025:.2f}/year (avg TER 0.25%)', ln=True)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(*LIGHT_GRAY)
    pdf.multi_cell(0, 3.5, 
        'Past performance does not guarantee future results. Backtested returns are simulated using historical data. '
        'This is not financial advice. Consult a qualified advisor before investing. Paasa, Inc. | support@paasa.com', align='C')
    
    pdf.output(output_path)
    print(f"PDF saved: {output_path}")
