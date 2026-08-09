#!/usr/bin/env python3.11
"""Fetch A-share market data for daily summary report."""
import urllib.request
import json
import ssl
import time

# ========== 1. Index data via Tencent QT ==========
def fetch_tencent_qt(codes):
    """Fetch real-time data from Tencent QT API. Returns dict of {name: fields}."""
    url = 'http://qt.gtimg.cn/q=' + ','.join(codes)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read().decode('gbk')
    results = {}
    for line in raw.split(';'):
        if line.strip() and '=' in line:
            fields = line.split('=')[1].strip('"').split('~')
            if len(fields) >= 44:
                name = fields[1]
                results[name] = {
                    'code': fields[2],
                    'price': fields[3],
                    'change': fields[4],
                    'change_pct': fields[5],
                    'volume': fields[6],
                    'amount_yuan': fields[9],
                    'high': fields[33],
                    'low': fields[34],
                    'open': fields[35],
                    'pre_close': fields[36],
                    'turnover': fields[38],
                    'amplitude': fields[43],
                }
    return results

# 五大指数
index_codes = ['sh000001','sz399001','sz399006','sh000016','sh000688','sh000300','sh000905']
print("=== INDEX DATA ===")
indices = fetch_tencent_qt(index_codes)
for name, data in indices.items():
    print(f"{name}|{data['price']}|{data['change']}|{data['change_pct']}|{data['amount_yuan']}|{data['high']}|{data['low']}")

# ========== 2. Key sector representative stocks ==========
print("=== SECTOR STOCKS ===")
sector_codes = [
    'sh600519','sz000858','sh600036','sh601398','sz002594','sz300750',
    'sh601012','sz002129','sh603259','sh600276','sh600887','sz000333',
    'sh601088','sh601899','sh600176','sh600309','sh600048','sh601318',
    'sh601857','sh600030','sz300059','sh600893','sh600584','sz002371',
    'sh603019','sz300308','sh600487','sz002156','sz300502','sh603986',
    'sz000938','sz002415','sz002714','sh600809','sz000568','sz002230',
    'sz300124','sh600438','sz300450','sh600196','sz000002','sz001979',
    'sh600585','sh600690','sz300413','sh600745','sz002475','sz300661',
    'sh688256','sh688012','sh688981','sh600703','sz300274','sz002460',
    'sh600089','sh600029','sh601390','sh601668','sh601985','sz002202',
    'sh601225','sh600188','sh600036','sh601166','sh600030','sz002736',
    'sz002142','sz300059','sh600837','sh601688','sh600918','sh601899',
]

# Batch query (max 13 per batch, 0.3s interval)
all_results = []
for i in range(0, len(sector_codes), 13):
    batch = sector_codes[i:i+13]
    try:
        stocks = fetch_tencent_qt(batch)
        for name, data in stocks.items():
            print(f"{name}|{data['code']}|{data['price']}|{data['change']}|{data['change_pct']}|{data['amount_yuan']}|{data['turnover']}")
    except Exception as e:
        print(f"Batch {i} error: {e}")
    time.sleep(0.3)

# ========== 3. Market fund flow via push2 ==========
print("=== FUND FLOW ===")
# Try market fund flow daykline
url = 'https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=1.000001&fields2=f51,f52,f53,f54,f55&klt=101&lmt=5'
try:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10, context=ctx)
    data = json.loads(resp.read().decode('utf-8'))
    klines = data.get('data', {}).get('klines', [])
    print(f"Daykline count: {len(klines)}")
    for kline in klines:
        if kline:
            parts = kline.split('~')
            print(f"date={parts[0]}, main_force={parts[1]}, retail={parts[2]}, mid={parts[3]}, super_large={parts[4]}, large={parts[5]}")
except Exception as e:
    print(f"Daykline error: {e}")

# ========== 4. Try Sina finance for narrative ==========
print("=== NARRATIVE ===")

# ========== 5. K-line data for technical indicators ==========
print("=== KLINE ===")
# 上证指数日K线
url_k = 'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh000001,day,,,60,qfq'
try:
    req = urllib.request.Request(url_k, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    raw = resp.read()
    # Try UTF-8 first, then gbk
    try:
        text = raw.decode('utf-8')
    except:
        text = raw.decode('gbk')
    data = json.loads(text)
    klines = data.get('data', {}).get('sh000001', {}).get('day', [])
    if klines:
        print(f"SH Klines: {len(klines)}")
        for k in klines[-5:]:
            print(f"date={k[0]}, o={k[1]}, c={k[2]}, h={k[3]}, l={k[4]}, v={k[5]}")
except Exception as e:
    print(f"SH Kline error: {e}")

# 创业板指日K线
url_k2 = 'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz399006,day,,,60,qfq'
try:
    req = urllib.request.Request(url_k2, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    text = resp.read().decode('utf-8')
    data = json.loads(text)
    klines = data.get('data', {}).get('sz399006', {}).get('day', [])
    if klines:
        print(f"SZ Klines: {len(klines)}")
        for k in klines[-5:]:
            extra = ''
            if len(k) >= 7:
                extra = f", amount={k[6]}"
            print(f"date={k[0]}, o={k[1]}, c={k[2]}, h={k[3]}, l={k[4]}, v={k[5]}{extra}")
except Exception as e:
    print(f"SZ Kline error: {e}")