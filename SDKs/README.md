# Portfolio Generator

A sophisticated investment portfolio generator that combines quiz-based user profiling with AI-powered portfolio recommendations and professional PDF report generation.

## 🎯 Overview

Portfolio Generator is a Python application that:
- **Captures investor preferences** through structured quiz inputs
- **Generates AI-enhanced portfolios** using Google Gemini API
- **Fetches portfolio data** from the Paasa API
- **Renders professional reports** as HTML and PDF with performance charts

This project follows a **clean architecture** with clear separation of concerns: data retrieval, AI enhancement, and presentation layers.

---

## 📋 Features

### Core Functionality
- **Quiz Parser**: Converts user quiz responses into structured investor profiles
- **Portfolio Mapping**: Maps risk profiles to appropriate portfolio types (Preservation, Balanced, Growth)
- **API Integration**: Integrates with Paasa API for real portfolio data
- **AI Enhancement**: Uses Google Gemini to enhance and personalize portfolio recommendations
- **Report Generation**: Creates professional 2-page PDF reports with:
  - Investor profile summary
  - Investment methodology
  - Portfolio holdings table
  - Performance charts (portfolio vs S&P 500)
  - Key performance metrics

### Supported Portfolio Types
1. **Preservation Portfolio** (ID: 1) - Conservative, capital protection focus
2. **Balanced Portfolio** (ID: 2) - Moderate growth with risk management
3. **Growth Portfolio** (ID: 3) - Aggressive growth strategy

---

## 🛠️ Technology Stack

### Backend
- **Python 3.x** - Core application language
- **Google Genai SDK** - AI-powered portfolio enhancements
- **Requests** - HTTP client for API calls
- **python-dotenv** - Environment variable management

### Rendering
- **xhtml2pdf (pisa)** - HTML to PDF conversion
- **Matplotlib** - Performance chart generation
- **NumPy** - Numerical computations

### Frontend (Optional Browser View)
- **HTML5** - Report template structure
- **CSS3** - Professional styling and layouts
- **JavaScript** - Interactive elements

---

## 📁 Project Structure

```
SDKs/
├── main.py                          # Entry point and orchestration
├── data_provider.py                 # API calls and data retrieval
├── renderer.py                      # Report generation (HTML/PDF)
├── requirements.txt                 # Python dependencies
├── .env                            # API keys (not in repo)
│
├── templates/
│   ├── portfolio_template.html      # HTML report template
│   ├── styles.css                   # Report styling
│   └── script.js                    # Interactive features
│
├── utils/
│   └── accumulating_etfs.json       # ETF database (4000+ securities)
│
├── output/
│   ├── portfolio_1/
│   │   ├── portfolio_data.json      # Parsed portfolio data
│   │   └── portfolio_report.pdf     # Generated report
│   └── portfolio_N/                 # Additional portfolios
│
└── README.md                        # This file
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- API credentials (see below)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root directory:

```env
# Google Gemini API Key
GEMINI_API_KEY=your_google_genai_api_key_here

# Paasa API Bearer Token
PAASA_BEARER_TOKEN=your_paasa_bearer_token_here
```

**Note**: Never commit the `.env` file to version control.

### 3. Verify ETF Database

The `utils/accumulating_etfs.json` file contains 4000+ ETFs. This database is used for:
- ETF name lookups
- Category classification
- Holdings validation

---

## 🚀 Usage

### Running the Application

```bash
python main.py
```

### Input Format

The application accepts quiz results in the following format:

```
Investment Goals: Grow with caution
Withdraw Expectation: In 6-10 years
Scenario Question Answer: I'll do nothing
Portfolio Committed Capital: $5,000.00
Preferred Topics: World (all regions), Emerging markets, Asia-Pacific, Latin America, Healthcare, Technology, Industrials, Nuclear Energy, Electric Vehicles, Biotech, Corporate Bonds, Total Bond Market, Palladium, Uranium, Water
```

### Quiz Parsing Rules

The parser recognizes key phrases to determine investor profile:

**Conservative Indicators**:
- "avoid losing"
- "grow with caution"
- "sell everything"
- "sell some"

**Aggressive Indicators**:
- "grow aggressively"
- "buy more"

**Time Horizons**:
- Short: 0-3 years
- Medium: 3-10 years
- Long: 10+ years

### Output

For each generated portfolio, the application creates:

#### `portfolio_data.json`
```json
{
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "portfolio_id": 2,
  "risk_level": "Balanced",
  "investment_horizon": "6-10 years",
  "holdings": [
    {
      "ticker": "IWDA.L",
      "name": "iShares Core MSCI World UCITS ETF",
      "weight": 40,
      "category": "Global Equities"
    }
  ],
  "methodology": {...}
}
```

#### `portfolio_report.pdf`
A professional 2-page report including:
- Page 1: Profile, methodology, holdings table
- Page 2: Performance charts, metrics, recommendations

---

## 📊 Key Components

### main.py
**Responsibility**: Application orchestration and user interaction

**Key Functions**:
- `parse_user_input()` - Converts quiz strings to structured profiles
- `get_next_portfolio_number()` - Manages output folder numbering
- `main()` - Orchestrates the entire flow

### data_provider.py
**Responsibility**: Data retrieval and enhancement

**Key Functions**:
- `get_portfolio_id()` - Maps user profile to portfolio type
- `fetch_from_api()` - Calls Paasa API with authentication
- `enhance_with_gemini()` - Uses Google Gemini to personalize recommendations
- `get_portfolio_data()` - Main orchestration function

### renderer.py
**Responsibility**: Report generation

**Key Functions**:
- `generate_performance_chart()` - Creates matplotlib chart as base64
- `render_portfolio_to_html()` - Injects data into HTML template
- `render_portfolio()` - Main function: HTML → PDF conversion
- `generate_pdf_from_html()` - Uses xhtml2pdf for conversion

---

## 🔐 API Integration

### Paasa API

**Endpoint**: `https://api-stage.paasa.com/api/portfolio/v1/analyze`

**Method**: GET

**Parameters**:
```python
{
    'portfolioId': int,      # 1, 2, or 3
    'fromTemplates': 'true'
}
```

**Headers**:
```python
{
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json',
    'build-version': '44',
    'x-internal-client-token': INTERNAL_TOKEN,
    'app-version': '6.0.2'
}
```

### Google Gemini API

**Purpose**: Enhance portfolio recommendations with personalized insights

**Typical Use**:
- Generate investment methodology descriptions
- Create personalized recommendations based on user preferences
- Enhance holdings descriptions with market context

---

## 📈 Performance Chart Generation

The renderer creates comparison charts showing:
- **User Portfolio Performance** (blue line) - Actual portfolio returns
- **S&P 500 Benchmark** (red dashed line) - Market benchmark

**Features**:
- Dynamic sampling (max 80 data points for clarity)
- Matplotlib-based rendering
- Base64 encoding for HTML embedding
- Responsive sizing for PDF layout

---

## 🧪 Example Workflow

```
1. User runs: python main.py
   ↓
2. System prompts for quiz input
   ↓
3. User pastes quiz results and presses Enter
   ↓
4. parse_user_input() extracts: goal, risk, time horizon, etc.
   ↓
5. get_portfolio_id() maps to portfolio (1, 2, or 3)
   ↓
6. fetch_from_api() retrieves holdings from Paasa
   ↓
7. enhance_with_gemini() personalizes recommendations
   ↓
8. render_portfolio() generates HTML with charts
   ↓
9. xhtml2pdf converts to PDF
   ↓
10. Output saved to: output/portfolio_N/
    - portfolio_data.json
    - portfolio_report.pdf
```

---

## 📝 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Genai API key |
| `PAASA_BEARER_TOKEN` | Yes | Paasa API authentication token |

### Directory Defaults

| Variable | Value | Purpose |
|----------|-------|---------|
| `BASE_DIR` | Script directory | Project root |
| `OUTPUT_DIR` | `{BASE_DIR}/output` | Generated reports |
| `TEMPLATES_DIR` | `{BASE_DIR}/templates` | HTML templates |

---

## 🐛 Troubleshooting

### Common Issues

**Issue**: `GEMINI_API_KEY not found`
- **Solution**: Ensure `.env` file exists in project root with valid API key

**Issue**: `Bearer token invalid`
- **Solution**: Verify `PAASA_BEARER_TOKEN` is current and has proper permissions

**Issue**: PDF generation fails
- **Solution**: Ensure `xhtml2pdf` is installed: `pip install xhtml2pdf`

**Issue**: Chart not appearing in PDF
- **Solution**: Check matplotlib backend is set to 'Agg' (already configured)

---

## 🔄 Data Flow Diagram

```
User Quiz Input
      ↓
parse_user_input()  → Structured Profile
      ↓
get_portfolio_id()  → Portfolio Type (1/2/3)
      ↓
fetch_from_api()    → API Holdings
      ↓
enhance_with_gemini() → Personalized Recommendations
      ↓
generate_performance_chart() → Chart Image (Base64)
      ↓
render_portfolio_to_html() → HTML with Data
      ↓
generate_pdf_from_html() → PDF Report
      ↓
Output: portfolio_data.json + portfolio_report.pdf
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `google-genai` | Latest | Google Gemini API client |
| `python-dotenv` | Latest | Environment variable management |
| `xhtml2pdf` | Latest | HTML to PDF conversion |
| `requests` | Latest | HTTP requests |
| `matplotlib` | Latest | Chart generation |
| `numpy` | Latest | Numerical operations |

---

## 📄 License

Proprietary - Paasa Inc.

---

## 👥 Support

For issues or questions:
1. Check the **Troubleshooting** section above
2. Verify all API keys are correctly configured
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

---

## 🎓 Architecture Notes

### Design Principles

1. **Separation of Concerns**
   - Data layer (`data_provider.py`) - independent of presentation
   - Rendering layer (`renderer.py`) - agnostic to data source
   - Orchestration (`main.py`) - coordinates components

2. **Clean API Integration**
   - External APIs abstracted in dedicated functions
   - Error handling for network failures
   - Configurable authentication via environment variables

3. **Extensibility**
   - Easy to add new portfolio types by extending portfolio ID mapping
   - Template changes don't require code modifications
   - ETF database is JSON-based for easy updates

---

## 🚀 Future Enhancements

Potential improvements for future versions:
- Web UI for quiz input
- Email report delivery
- Portfolio backtesting and analytics
- Real-time market data integration
- Multi-currency support
- Advanced visualization options

---

**Last Updated**: December 2025
