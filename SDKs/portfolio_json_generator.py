"""
Portfolio JSON Generator
Parses Gemini response and creates structured JSON with backtest data
"""

import json
import re
import os
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

# ETF name to Yahoo Finance ticker mapping
ETF_TICKER_MAP = {
    'vanguard ftse all-world': 'VWCE.DE',
    'ishares core msci world': 'IWDA.AS',
    'ishares msci world': 'IWDA.AS',
    'ishares core global aggregate bond': 'AGGH.L',
    'ishares global aggregate bond': 'AGGH.L',
    'xtrackers global aggregate bond': 'XGAG.DE',
    'vanguard global aggregate bond': 'VAGP.L',
    'ishares core msci emerging markets': 'EIMI.L',
    'ishares msci emerging markets': 'IEMG',
    'xtrackers msci world information technology': 'XDWT.DE',
    'ishares s&p 500 information technology': 'IUIT.L',
    'ishares global healthcare': 'IXJ',
    'ishares healthcare innovation': 'HEAL.L',
    'ishares global clean energy': 'ICLN',
    'l&g clean water': 'GLUG.L',
    'ishares global water': 'IH2O.L',
    'global x uranium': 'URA',
    'ishares global corporate bond': 'CORP.L',
    'ishares electric vehicles': 'ECAR.L',
    'l&g battery value-chain': 'BATG.L',
}


def get_etf_ticker(etf_name):
    """Get Yahoo Finance ticker for ETF name"""
    name_lower = etf_name.lower()
    for key, ticker in ETF_TICKER_MAP.items():
        if key in name_lower:
            return ticker
    return None


def fetch_backtest_data(etfs, years=3):
    """Fetch 3-year historical data for portfolio and S&P 500"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years*365)
    
    # S&P 500 data
    sp500_dates, sp500_values, sp500_return = [], [], None
    try:
        sp500_raw = yf.download('^GSPC', start=start_date, end=end_date, progress=False)
        if not sp500_raw.empty:
            close = sp500_raw['Close']
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            first_val = float(close.iloc[0])
            normalized = close / first_val * 100
            sp500_dates = [d.strftime('%Y-%m-%d') for d in normalized.index]
            sp500_values = [round(float(v), 2) for v in normalized.values]
            sp500_return = round((float(close.iloc[-1]) / first_val - 1) * 100, 1)
    except:
        pass
    
    # Portfolio data (weighted average of ETFs)
    portfolio_data, portfolio_dates, portfolio_values, portfolio_return = None, [], [], None
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
                normalized = close / first_val * 100
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
        portfolio_dates = [d.strftime('%Y-%m-%d') for d in portfolio_data.index]
        portfolio_values = [round(float(v), 2) for v in portfolio_data.values]
        portfolio_return = round((portfolio_values[-1] / 100 - 1) * 100, 1)
    
    return {
        'portfolio': {'dates': portfolio_dates, 'values': portfolio_values, 'return_3y': portfolio_return},
        'sp500': {'dates': sp500_dates, 'values': sp500_values, 'return_3y': sp500_return}
    }


def parse_portfolio_response(text, profile):
    """Extract portfolio details from Gemini response text"""
    data = {'equity_pct': 60, 'bond_pct': 40, 'expected_return': '', 'volatility': '', 'etfs': []}
    
    # Parse equity/bond split
    match = re.search(r'Equity/Bond Split:\s*(\d+)%?\s*/\s*(\d+)%?', text)
    if match:
        data['equity_pct'] = int(match.group(1))
        data['bond_pct'] = int(match.group(2))
    
    # Parse expected return and volatility
    match = re.search(r'Expected Return:\s*([\d\-\.\s%]+)', text)
    if match:
        data['expected_return'] = match.group(1).strip()
    match = re.search(r'Volatility:\s*(\w+)', text)
    if match:
        data['volatility'] = match.group(1)
    
    # Parse ETFs: [Name] - [X]% ($[amount])
    pattern = r'([A-Za-z][A-Za-z0-9\s&\-\']+(?:UCITS|ETF)[A-Za-z0-9\s\(\)\-]*)\s*-\s*(\d+)%\s*\(\$?([\d,\.]+)\)'
    seen = set()
    for name, alloc, amount in re.findall(pattern, text):
        name = name.strip()
        if name.lower().startswith('this etf') or name in seen or len(name) <= 15:
            continue
        seen.add(name)
        pos = text.lower().find(name.lower())
        is_thematic = 'thematic' in text[:pos].lower()[-400:] if pos > 0 else False
        data['etfs'].append({
            'name': name, 'allocation': float(alloc),
            'amount': float(amount.replace(',', '')),
            'type': 'Thematic' if is_thematic else 'Core'
        })
    
    return data


def calculate_scenarios(equity_pct, bond_pct):
    """Calculate expected return scenarios based on allocation"""
    eq, bd = equity_pct / 100, bond_pct / 100
    return {
        'best': round(eq * 28 + bd * 10),
        'average': round(eq * 9 + bd * 4),
        'worst': round(eq * -22 + bd * -2)
    }


def generate_portfolio_json(response_text, profile, validation=None, output_path="portfolio_data.json"):
    """Generate complete portfolio JSON file"""
    portfolio = parse_portfolio_response(response_text, profile)
    scenarios = calculate_scenarios(portfolio['equity_pct'], portfolio['bond_pct'])
    
    print("Fetching historical data...")
    backtest = fetch_backtest_data(portfolio['etfs'], years=3)
    
    data = {
        'generated_at': datetime.now().isoformat(),
        'profile': {
            'goal': profile.get('goal', ''),
            'time_horizon': profile.get('time_horizon', ''),
            'risk_behavior': profile.get('risk_behavior', ''),
            'amount': profile.get('amount', 5000),
            'themes': {
                'regions': profile.get('regions', []),
                'sectors': profile.get('sectors', []),
                'trends': profile.get('trends', []),
                'bonds': profile.get('bonds', []),
                'commodities': profile.get('commodities', [])
            }
        },
        'portfolio': {
            'equity_pct': portfolio['equity_pct'],
            'bond_pct': portfolio['bond_pct'],
            'expected_return': portfolio['expected_return'],
            'volatility': portfolio['volatility'],
            'total_etfs': len(portfolio['etfs']),
            'etfs': portfolio['etfs']
        },
        'scenarios': scenarios,
        'backtest': backtest,
        'validation': validation or []
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"JSON saved: {output_path}")
    return data
