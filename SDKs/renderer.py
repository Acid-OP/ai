"""
Renderer - ONLY injects data into template skeleton
NO chart generation, NO PDF - just HTML output
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')


def render_portfolio(data: dict, output_dir: str) -> dict:
    """Read template skeleton, inject data, output HTML"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Read template and CSS
    with open(os.path.join(TEMPLATES_DIR, 'portfolio_template.html'), 'r', encoding='utf-8') as f:
        html = f.read()
    with open(os.path.join(TEMPLATES_DIR, 'styles.css'), 'r', encoding='utf-8') as f:
        css = f.read()
    
    # Inline CSS
    html = html.replace('<link rel="stylesheet" href="styles.css">', f'<style>\n{css}\n</style>')
    
    # Extract data
    user = data.get('user', {})
    profile = data.get('profile', {})
    portfolio = data.get('portfolio', {})
    methodology = data.get('methodology', {})
    holdings = data.get('holdings', [])
    metrics = data.get('metrics', {})
    benchmark = data.get('benchmark', {})
    regions = data.get('regions', [])[:8]
    top_stocks = data.get('top_stocks', [])[:8]
    alloc_legend = data.get('allocation_legend', [])
    
    # Risk class
    risk = (portfolio.get('risk_level') or '').lower()
    risk_class = 'low' if risk == 'low' else 'medium' if risk == 'medium' else 'high'
    
    # Build holdings rows
    holdings_rows = ''
    for i, h in enumerate(holdings):
        holdings_rows += f'''<tr>
            <td style="text-align:center;color:#6B7280;">{i+1}</td>
            <td class="ticker">{h.get('ticker', '')}</td>
            <td>{h.get('name', '')}</td>
            <td class="weight">{h.get('weight', 0)}%</td>
            <td style="color:#6B7280;">{h.get('category', '')}</td>
        </tr>'''
    
    # Build principles list
    principles = ''.join([f'<li>{p}</li>' for p in methodology.get('key_principles', [])])
    
    # Build regions rows
    regions_rows = ''.join([f'''<tr>
        <td>{r.get('name', '')}</td>
        <td>{r.get('percentage', 0)}%</td>
    </tr>''' for r in regions])
    
    # Build stocks list
    stocks_list = ''
    for s in top_stocks:
        stocks_list += f'<span class="stock-item"><span class="stock-symbol">{s.get("symbol", "")}</span> <span class="stock-weight">{s.get("weight", 0)}%</span></span> '
    
    # Build allocation legend
    legend_html = ''
    for item in alloc_legend:
        legend_html += f'''<div class="legend-item">
            <span class="legend-color" style="background:{item.get('color', '#888')};"></span>
            <span class="legend-name">{item.get('name', '')}</span>
            <span class="legend-percent">{item.get('weight', 0)}%</span>
        </div>'''
    
    # Replace all static placeholders
    replacements = {
        '{{REPORT_DATE}}': data.get('report_date', ''),
        '{{USER_NAME}}': user.get('name', '-'),
        '{{USER_EMAIL}}': user.get('email', '-'),
        '{{RISK_LEVEL}}': (portfolio.get('risk_level') or '-').upper(),
        '{{TIME_HORIZON}}': profile.get('time_horizon', '-'),
        '{{METHODOLOGY_TITLE}}': methodology.get('methodology_title', 'Modern Portfolio Theory'),
        '{{METHODOLOGY_TEXT}}': methodology.get('methodology_text', ''),
        '{{PRINCIPLES_LIST}}': principles,
        '{{HOLDINGS_ROWS}}': holdings_rows,
        '{{FIVE_YR_RETURN}}': str(metrics.get('five_yr_return', '-')),
        '{{THREE_YR_RETURN}}': str(metrics.get('three_yr_return', '-')),
        '{{VOLATILITY}}': str(metrics.get('volatility', '-')),
        '{{SP500_RETURN}}': str(benchmark.get('five_yr_return', '-')),
        '{{ALLOCATION_LEGEND}}': legend_html,
        '{{REGIONS_ROWS}}': regions_rows,
        '{{STOCKS_LIST}}': stocks_list,
    }
    
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))
    
    # Add risk class to badge
    html = html.replace('class="risk-badge"', f'class="risk-badge {risk_class}"')
    
    # Inject full data as JSON for charts (JS will read this)
    portfolio_json = json.dumps(data, ensure_ascii=False)
    html = html.replace('{{PORTFOLIO_JSON}}', portfolio_json)
    
    # Save HTML
    html_path = os.path.join(output_dir, 'portfolio_report.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML saved: {html_path}")
    
    # Save JSON (for debugging)
    json_path = os.path.join(output_dir, 'portfolio_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved: {json_path}")
    
    return {'html': html_path, 'json': json_path}
