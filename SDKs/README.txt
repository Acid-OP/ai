SETUP
-----
1. Install dependencies:
   pip install -r requirements.txt

2. Set your Gemini API key in .env file:
   GEMINI_API_KEY=your_key_here

USAGE
-----
Run: python main.py

Test input:
Then paste quiz results 
Investment Goals: Grow with caution
Withdraw Expectation: In 6-10 years
Scenario Question Answer: I'll do nothing
Portfolio Committed Capital: $5,000.00
Preferred Topics: World (all regions), Emerging markets, Asia-Pacific, Latin America, Healthcare, Technology, Industrials, Nuclear Energy, Electric Vehicles, Biotech, Corporate Bonds, Total Bond Market, Palladium, Uranium, Water

and press Enter.

Output goes to: output/portfolio_X/
  - portfolio_data.json
  - portfolio_report.pdf


FILES
-----
main.py                  - Entry point
portfolio_json_generator.py - Creates JSON from Gemini response
pdf_generator.py         - Creates PDF with charts
utils/                   - Logo and ETF database
templates/               - HTML template (for browser viewing)
output/                  - Generated portfolios

