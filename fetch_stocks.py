#!/usr/bin/env python3
"""Fetch stock data from various free data sources."""
import urllib.request, json, ssl, re, time, sys

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

tickers = ["AAPL", "MSFT", "AMZN", "NVDA", "META", "GOOGL", "GOOG"]

# Try multiple data sources
sources = [
    ("MSN Money", "https://www.msn.com/en-us/money/stockdetails/{}"),
    ("MarketScreener", "https://www.marketscreener.com/quote/stock/{}/"),
    ("WSJ Markets", "https://www.wsj.com/market-data/quotes/{}/"),
]

for t in tickers:
    found = False
    for src_name, url_template in sources:
        try:
            url = url_template.format(t)
            if src_name == "Marketscreener":
                # Need different URL format for marketscreener
                continue
            req = urllib.request.Request(url, headers=headers)
            resp = urllib.request.urlopen(req, timeout=10, context=ctx)
            html = resp.read().decode("utf-8", errors="replace")
            
            # Try various patterns
            patterns = [
                r'"regularMarketPrice":\{"raw":([\d.]+).*?"regularMarketChange":\{"raw":([\d.-]+).*?"regularMarketChangePercent":\{"raw":([\d.-]+)',
                r'"price":\s*([\d.]+)',
                r'data-price="([\d.]+)"',
                r'currentPrice":\s*([\d.]+)',
            ]
            
            for pat in patterns:
                m = re.search(pat, html)
                if m:
                    groups = m.groups()
                    price = groups[0]
                    chg = groups[1] if len(groups) > 1 else "N/A"
                    pct = groups[2] if len(groups) > 2 else "N/A"
                    print(f"{t}|{price}|{chg}|{pct}|{src_name}")
                    found = True
                    break
            if found:
                break
        except Exception as e:
            continue
    if not found:
        print(f"{t}|NO_DATA_FOUND")

print("---DONE---")