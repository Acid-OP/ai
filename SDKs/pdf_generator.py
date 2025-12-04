"""
Professional Portfolio PDF Generator
Clean, minimalist design with proper spacing
"""

import os
import re
import tempfile
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from fpdf import FPDF

# Colors
NAVY = (15, 23, 42)
BLUE = (59, 130, 246)
GREEN = (34, 197, 94)
ORANGE = (249, 115, 22)
RED = (239, 68, 68)
GRAY = (100, 116, 139)
LIGHT = (241, 245, 249)
WHITE = (255, 255, 255)


class PortfolioPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
    
    def header_section(self):
        self.set_fill_color(*NAVY)
        self.rect(0, 0, 210, 30, 'F')
        self.set_text_color(*WHITE)
        self.set_font('Helvetica', 'B', 18)
        self.set_xy(15, 8)
        self.cell(0, 10, 'Portfolio Recommendation')
        self.set_font('Helvetica', '', 9)
        self.set_xy(15, 18)
        self.cell(0, 5, f'Generated {datetime.now().strftime("%B %d, %Y")}')
        self.ln(35)
        self.set_text_color(*NAVY)
    
    def section(self, title):
        self.ln(2)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*NAVY)
        self.cell(0, 7, title.upper(), ln=True)
        self.set_draw_color(*BLUE)
        self.set_line_width(0.5)
        self.line(15, self.get_y(), 55, self.get_y())
        self.ln(4)
        self.set_text_color(*NAVY)
    
    def metric_row(self, label, value, highlight=False):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*GRAY)
        self.cell(50, 5, label)
        self.set_text_color(*NAVY)
        if highlight:
            self.set_font('Helvetica', 'B', 9)
        self.cell(40, 5, str(value), ln=True)
        self.set_font('Helvetica', '', 9)


def create_allocation_chart(equity_pct, bond_pct, total):
    """Minimal donut chart with bigger center text"""
    fig, ax = plt.subplots(figsize=(3, 3), dpi=100)
    
    sizes = [equity_pct, bond_pct] if bond_pct > 0 else [100]
    colors = ['#3B82F6', '#F97316'] if bond_pct > 0 else ['#3B82F6']
    
    wedges, _ = ax.pie(sizes, colors=colors, startangle=90,
                       wedgeprops=dict(width=0.35, edgecolor='white', linewidth=2))
    
    # Bigger, bolder center text
    ax.text(0, 0.08, f'${total:,.0f}', ha='center', va='center', 
            fontsize=16, fontweight='bold', color='#0F172A')
    ax.text(0, -0.18, 'Total', ha='center', va='center', 
            fontsize=9, color='#64748B')
    
    plt.tight_layout(pad=0)
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=100, facecolor='white', edgecolor='none')
    plt.close()
    return path


def create_performance_chart(equity_pct, bond_pct):
    """Clean horizontal bar chart for performance scenarios"""
    fig, ax = plt.subplots(figsize=(4, 1.8), dpi=100)
    
    eq = equity_pct / 100
    bd = bond_pct / 100
    
    best = eq * 28 + bd * 10
    avg = eq * 9 + bd * 4
    worst = eq * -22 + bd * -2
    
    scenarios = ['Worst Year', 'Average', 'Best Year']
    values = [worst, avg, best]
    colors = ['#EF4444', '#3B82F6', '#22C55E']
    
    bars = ax.barh(scenarios, values, color=colors, height=0.6, edgecolor='none')
    
    for bar, val in zip(bars, values):
        xpos = bar.get_width() + 1 if val >= 0 else bar.get_width() - 5
        ax.text(xpos, bar.get_y() + bar.get_height()/2,
                f'{val:+.1f}%', va='center', fontsize=10, fontweight='bold',
                color=bar.get_facecolor())
    
    ax.axvline(x=0, color='#E2E8F0', linewidth=1)
    ax.set_xlim(min(values) - 10, max(values) + 10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(left=False, bottom=False)
    ax.set_xticks([])
    ax.tick_params(axis='y', labelsize=9, colors='#0F172A')
    
    plt.tight_layout(pad=0.3)
    path = tempfile.mktemp(suffix='.png')
    plt.savefig(path, bbox_inches='tight', dpi=100, facecolor='white', edgecolor='none')
    plt.close()
    return path, best, avg, worst


def parse_response(text, profile):
    """Extract real data from portfolio response"""
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
    
    # Parse ETFs - cleaner regex
    pattern = r'([A-Za-z][A-Za-z0-9\s&\-\']+(?:UCITS|ETF)[A-Za-z0-9\s\(\)\-]*)\s*-\s*(\d+)%\s*\(\$?([\d,\.]+)\)'
    matches = re.findall(pattern, text)
    
    seen = set()
    for name, alloc, amount in matches:
        name = name.strip()
        # Skip if it's actually a description
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
    """Generate clean professional PDF"""
    
    data = parse_response(response_text, profile)
    
    # Generate charts
    alloc_chart = create_allocation_chart(data['equity_pct'], data['bond_pct'], data['amount'])
    perf_chart, best, avg, worst = create_performance_chart(data['equity_pct'], data['bond_pct'])
    
    pdf = PortfolioPDF()
    
    # === PAGE 1 ===
    pdf.add_page()
    pdf.header_section()
    
    # Profile
    pdf.section('Your Investment Profile')
    pdf.metric_row('Investment Goal', data['goal'], True)
    pdf.metric_row('Time Horizon', data['horizon'])
    pdf.metric_row('Risk Behavior', data['behavior'])
    pdf.metric_row('Investment Amount', f"${data['amount']:,.2f}", True)
    
    pdf.ln(3)
    
    # Summary
    pdf.section('Portfolio Summary')
    pdf.metric_row('Number of Holdings', f"{len(data['etfs'])} ETFs")
    pdf.metric_row('Equity Allocation', f"{data['equity_pct']}%", True)
    pdf.metric_row('Bond Allocation', f"{data['bond_pct']}%")
    if data['expected_return']:
        pdf.metric_row('Expected Return', data['expected_return'])
    if data['volatility']:
        pdf.metric_row('Volatility', data['volatility'])
    
    # Chart on right
    if alloc_chart and os.path.exists(alloc_chart):
        pdf.image(alloc_chart, x=135, y=48, w=55)
        os.remove(alloc_chart)
    
    pdf.ln(6)
    
    # ETF Table
    pdf.section('Your Portfolio Holdings')
    
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(*NAVY)
    pdf.set_text_color(*WHITE)
    col_w = [8, 90, 18, 25, 20]
    headers = ['#', 'ETF Name', 'Weight', 'Amount', 'Type']
    for w, h in zip(col_w, headers):
        pdf.cell(w, 6, h, 0, 0, 'L', True)
    pdf.ln()
    
    pdf.set_text_color(*NAVY)
    for i, etf in enumerate(data['etfs'][:7], 1):
        pdf.set_font('Helvetica', '', 8)
        fill = i % 2 == 0
        if fill:
            pdf.set_fill_color(*LIGHT)
        
        etype = 'Thematic' if etf['is_thematic'] else 'Core'
        name = etf['name'][:48] if len(etf['name']) > 48 else etf['name']
        
        pdf.cell(col_w[0], 5, str(i), 0, 0, 'L', fill)
        pdf.cell(col_w[1], 5, name, 0, 0, 'L', fill)
        pdf.cell(col_w[2], 5, f"{etf['allocation']:.0f}%", 0, 0, 'L', fill)
        pdf.cell(col_w[3], 5, f"${etf['amount']:,.0f}", 0, 0, 'L', fill)
        pdf.cell(col_w[4], 5, etype, 0, 0, 'L', fill)
        pdf.ln()
    
    # === PAGE 2 ===
    pdf.add_page()
    pdf.header_section()
    
    # Performance Section
    pdf.section('Historical Performance Scenarios')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(170, 4, f'Based on your {data["equity_pct"]}% equity / {data["bond_pct"]}% bond split, historical data suggests:')
    pdf.ln(3)
    
    chart_y = pdf.get_y()
    if perf_chart and os.path.exists(perf_chart):
        pdf.image(perf_chart, x=15, y=chart_y, w=80)
        os.remove(perf_chart)
    
    # Key metrics box on right
    pdf.set_fill_color(*LIGHT)
    pdf.rect(108, chart_y - 2, 80, 32, 'F')
    
    pdf.set_xy(112, chart_y)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_text_color(*NAVY)
    pdf.cell(0, 5, 'Key Metrics')
    
    pdf.set_xy(112, chart_y + 8)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*GRAY)
    pdf.cell(35, 5, 'Best Year')
    pdf.set_text_color(*GREEN)
    pdf.cell(0, 5, f'+{best:.1f}%')
    
    pdf.set_xy(112, chart_y + 15)
    pdf.set_text_color(*GRAY)
    pdf.cell(35, 5, 'Average Return')
    pdf.set_text_color(*BLUE)
    pdf.cell(0, 5, f'+{avg:.1f}%')
    
    pdf.set_xy(112, chart_y + 22)
    pdf.set_text_color(*GRAY)
    pdf.cell(35, 5, 'Worst Year')
    pdf.set_text_color(*RED)
    pdf.cell(0, 5, f'{worst:.1f}%')
    
    pdf.set_y(chart_y + 38)
    
    # Allocation Legend
    pdf.section('Allocation Types')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_fill_color(*BLUE)
    pdf.cell(5, 5, '', 0, 0, 'L', True)
    pdf.set_text_color(*NAVY)
    pdf.cell(40, 5, '  Core Holdings - Stable, diversified base')
    pdf.ln(6)
    pdf.set_fill_color(*GREEN)
    pdf.cell(5, 5, '', 0, 0, 'L', True)
    pdf.cell(40, 5, '  Thematic Holdings - Growth-focused sectors')
    
    pdf.ln(10)
    
    # Themes
    pdf.section('Investment Themes Covered')
    all_themes = (profile.get('regions', []) + profile.get('sectors', []) + 
                  profile.get('trends', []) + profile.get('commodities', []))
    
    pdf.set_font('Helvetica', '', 9)
    col = 0
    for theme in all_themes[:12]:
        if col == 3:
            pdf.ln(5)
            col = 0
        pdf.set_x(15 + col * 62)
        pdf.set_text_color(*GREEN)
        pdf.cell(3, 5, '>')
        pdf.set_text_color(*NAVY)
        pdf.cell(55, 5, theme[:22])
        col += 1
    
    pdf.ln(12)
    
    # Getting Started
    pdf.section('Getting Started')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*NAVY)
    
    steps = [
        'Open a brokerage account that offers UCITS ETFs',
        f'Transfer ${data["amount"]:,.0f} to your account',
        'Purchase the ETFs with the allocations above',
        'Set annual rebalancing reminder'
    ]
    for i, step in enumerate(steps, 1):
        pdf.cell(5, 5, f'{i}.')
        pdf.cell(0, 5, step, ln=True)
    
    pdf.ln(5)
    
    # Cost
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 5, 'Estimated Annual Cost', ln=True)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(*GRAY)
    annual_cost = data['amount'] * 0.25 / 100
    pdf.cell(0, 4, f'Based on avg ETF expense ratios (~0.25%): ${annual_cost:.2f}/year', ln=True)
    
    # Footer
    pdf.set_y(-25)
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(0, 3.5, 
        'This recommendation is for informational purposes only. Historical performance does not guarantee future results. '
        'Consult a qualified financial advisor before investing.', align='C')
    
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    test_response = """
    Core Holdings (65%) - $3250
    Vanguard FTSE All-World UCITS ETF - 35% ($1750)
    iShares Global Corporate Bond UCITS ETF - 30% ($1500)
    
    Thematic Holdings (35%) - $1750
    Xtrackers MSCI World Information Technology UCITS ETF - 12% ($600)
    iShares Healthcare Innovation UCITS ETF - 10% ($500)
    iShares Global Clean Energy UCITS ETF - 8% ($400)
    Global X Uranium UCITS ETF - 5% ($250)
    
    Portfolio Characteristics
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
    
    generate_portfolio_pdf(test_response, test_profile, "test_fixed.pdf")
