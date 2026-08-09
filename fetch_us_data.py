#!/usr/bin/env python3
"""Fetch US stock market data from multiple sources."""

import urllib.request, json, ssl, re, time, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

def fetch_yahoo_quote(ticker):
    """Fetch stock quote data from Yahoo Finance HTML page."""
    url = f'https://finance.yahoo.com/quote/{ticker}/'
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        html = resp.read().decode('utf-8', errors='replace')
        
        price_m = re.search(r'"regularMarketPrice":\{"raw":([\d.]+)', html)
        change_m = re.search(r'"regularMarketChange":\{"raw":([\d.-]+)', html)
        pct_m = re.search(r'"regularMarketChangePercent":\{"raw":([\d.-]+)', html)
        
        if price_m:
            price = float(price_m.group(1))
            change = float(change_m.group(1)) if change_m else None
            pct = float(pct_m.group(1)) if pct_m else None
            return {'price': price, 'change': change, 'change_pct': pct}
        else:
            return None
    except Exception as e:
        return {'error': str(e)}

def fetch_yahoo_etf(ticker, label):
    """Fetch ETF/index data from Yahoo Finance."""
    return fetch_yahoo_quote(ticker)

# Test with a few symbols
for t in ['^DJI', '^GSPC', '^IXIC', 'AAPL', 'MSFT', 'AMZN', 'NVDA', 'META', 'GOOGL', 'GOOG', 'GC=F', 'CL=F', 'SI=F']:
    result = fetch_yahoo_quote(t)
    if result and 'price' in result:
        print(f'{t}|{result["price"]}|{result.get("change")}|{result.get("change_pct")}')
    elif result and 'error' in result:
        print(f'{t}|ERROR: {result["error"]}')
    else:
        print(f'{t}|NO_DATA')
    time.sleep(2)