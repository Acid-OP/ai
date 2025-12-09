import os
from datetime import datetime
from playwright.sync_api import sync_playwright

def render_portfolio(template_data, output_dir):
    """
    Renders portfolio report as PDF using Playwright (headless Chrome)
    This ensures the PDF looks exactly like the HTML in a browser
    
    Args:
        template_data: Dictionary with all template variables
        output_dir: Directory to save the PDF
    """
    # Read template
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'portfolio_template.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Replace all placeholders
    for key, value in template_data.items():
        placeholder = f"{{{{{key}}}}}"
        html_content = html_content.replace(placeholder, str(value))
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save HTML temporarily
    html_file = os.path.join(output_dir, 'portfolio_report.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Generate PDF using Playwright (headless Chrome)
    pdf_file = os.path.join(output_dir, 'portfolio_report.pdf')
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Load the HTML file
        page.goto(f'file:///{os.path.abspath(html_file)}')
        
        # Wait for any images to load
        page.wait_for_load_state('networkidle')
        
        # Generate PDF with proper settings
        page.pdf(
            path=pdf_file,
            format='A4',
            print_background=True,
            margin={
                'top': '0px',
                'right': '0px',
                'bottom': '0px',
                'left': '0px'
            }
        )
        
        browser.close()
    
    print(f"[OK] PDF report generated: {pdf_file}")
    
    return {
        'pdf': pdf_file,
        'html': html_file
    }
