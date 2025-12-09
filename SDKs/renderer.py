import os
from datetime import datetime
from xhtml2pdf import pisa

def render_portfolio(template_data, output_dir):
    """
    Renders portfolio report as PDF only
    
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
    
    # Generate PDF
    pdf_file = os.path.join(output_dir, 'portfolio_report.pdf')
    with open(pdf_file, 'wb') as pdf:
        pisa_status = pisa.CreatePDF(html_content, dest=pdf)
    
    if pisa_status.err:
        raise Exception(f"PDF generation failed with errors")
    
    print(f"[OK] PDF report generated: {pdf_file}")
    
    return {
        'pdf': pdf_file
    }
