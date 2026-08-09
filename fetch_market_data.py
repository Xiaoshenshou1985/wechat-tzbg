#!/usr/bin/env python3.11
"""Fetch A-share pre-market data for daily report - v2"""
from eltdx import Client

c = Client()

# ========== 1. Major Indexes via stock_profile_table ==========
idx_codes = ['999999', '399001', '399006']
table = c.helpers.stock_profile_table(idx_codes)
for r in table.rows:
    vol_yi = (r.amount or 0) / 1e8
    print(f"IDX|{r.code}|{r.name}|{r.last_price}|{r.change_pct}|{vol_yi:.2f}")
    # Also print attributes for debugging
    # print(f"  ATTRS: {[a for a in dir(r) if not a.startswith('_')]}")

print("---SEP---")

# Also try to get 科创50 and 上证50 via Tencent API
import urllib.request
codes = ['sh000016', 'sh000688']
url = 'http://qt.gtimg.cn/q=' + ','.join(codes)
resp = urllib.request.urlopen(url, timeout=5)
data = resp.read().decode('gbk')
for line in data.strip().split(';'):
    line = line.strip()
    if line and '="' in line:
        parts = line.split('="')[1].rstrip('";').split('~')
        name = parts[1]
        price = parts[3]
        change_pct = parts[7]
        print(f"TENCENT_IDX|{parts[0]}|{name}|{price}|{change_pct}")

print("---SEP---")

# ========== 2. Full Market Scan ==========
all_stocks = c.get_stock_codes_all()
a_share = []
for s in all_stocks:
    code = s.split('\t')[0]
    if code.startswith('sh6') or code.startswith('sh688') or \
       code.startswith('sz0') or code.startswith('sz001') or \
       code.startswith('sz002') or code.startswith('sz003') or \
       code.startswith('sz3'):
        a_share.append(code)

print(f"TOTAL_A|{len(a_share)}")

all_rows = []
for i in range(0, len(a_share), 1000):
    chunk = a_share[i:i+1000]
    table = c.helpers.quote_table(chunk)
    for r in table.rows:
        if r.change_pct is not None:
            all_rows.append(r)

print(f"QUERIED|{len(all_rows)}")

# Top gainers (limit up)
sorted_gainers = sorted(all_rows, key=lambda r: r.change_pct, reverse=True)[:30]
print("---GAINERS---")
limit_up_count = 0
for r in sorted_gainers:
    vol_yi = (r.amount or 0) / 1e8
    if r.change_pct >= 9.8:
        limit_up_count += 1
    print(f"G|{r.code}|{r.name}|{r.last_price}|{r.change_pct}|{vol_yi:.2f}")

# Top losers
sorted_losers = sorted(all_rows, key=lambda r: r.change_pct)[:30]
print("---LOSERS---")
limit_dn_count = 0
for r in sorted_losers:
    vol_yi = (r.amount or 0) / 1e8
    if r.change_pct <= -9.8:
        limit_dn_count += 1
    print(f"L|{r.code}|{r.name}|{r.last_price}|{r.change_pct}|{vol_yi:.2f}")

# Hot volume
sorted_vol = sorted(all_rows, key=lambda r: r.amount or 0, reverse=True)[:20]
print("---VOLUME---")
for r in sorted_vol:
    vol_yi = (r.amount or 0) / 1e8
    print(f"V|{r.code}|{r.name}|{r.last_price}|{r.change_pct}|{vol_yi:.2f}")

# Stats
up_count = sum(1 for r in all_rows if r.change_pct > 0)
down_count = sum(1 for r in all_rows if r.change_pct < 0)
flat_count = sum(1 for r in all_rows if r.change_pct == 0)
su = sum(1 for r in all_rows if r.change_pct >= 9.8)
sd = sum(1 for r in all_rows if r.change_pct <= -9.8)
print(f"STATS|up={up_count}|down={down_count}|flat={flat_count}|limit_up={su}|limit_down={sd}")

# ========== 3. Try push2 for sector/concept data ==========
print("---SECTOR_START---")
try:
    import ssl
    ctx = ssl.create_default_context()
    sector_url = 'https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=30&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:2&fields=f2,f3,f4,f12,f14'
    req = urllib.request.Request(sector_url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10, context=ctx)
    raw = resp.read().decode('utf-8')
    # Strip callback wrapper
    if raw.startswith('('):
        raw = raw[1:]
    if raw.endswith(')'):
        raw = raw[:-1]
    import json
    data = json.loads(raw)
    diff = data.get('data', {}).get('diff', {})
    if isinstance(diff, dict):
        items = list(diff.values())
    else:
        items = diff
    for item in items[:10]:
        name = item.get('f14', '')
        chg_raw = item.get('f3', 0)
        chg = chg_raw / 100 if isinstance(chg_raw, (int, float)) and abs(chg_raw) > 20 else chg_raw
        # f4 in sector context is net fund flow, not turnover
        f4_raw = item.get('f4', 0)
        f4_signal = '流入' if f4_raw > 0 else ('流出' if f4_raw < 0 else '持平')
        print(f"SECTOR|{name}|{chg}|{f4_signal}")
except Exception as e:
    print(f"SECTOR_ERR|{e}")

print("---CONCEPT_START---")
try:
    concept_url = 'https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=30&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:90+t:3&fields=f2,f3,f4,f12,f14'
    req = urllib.request.Request(concept_url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10, context=ctx)
    raw = resp.read().decode('utf-8')
    if raw.startswith('('):
        raw = raw[1:]
    if raw.endswith(')'):
        raw = raw[:-1]
    data = json.loads(raw)
    diff = data.get('data', {}).get('diff', {})
    if isinstance(diff, dict):
        items = list(diff.values())
    else:
        items = diff
    for item in items[:10]:
        name = item.get('f14', '')
        chg_raw = item.get('f3', 0)
        chg = chg_raw / 100 if isinstance(chg_raw, (int, float)) and abs(chg_raw) > 20 else chg_raw
        f4_raw = item.get('f4', 0)
        f4_signal = '流入' if f4_raw > 0 else ('流出' if f4_raw < 0 else '持平')
        print(f"CONCEPT|{name}|{chg}|{f4_signal}")
except Exception as e:
    print(f"CONCEPT_ERR|{e}")

# ========== 4. Try market fund flow ==========
print("---FUND_FLOW_START---")
try:
    ff_url = 'https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=1.000001&fields2=f51,f52,f53,f54,f55&klt=101&lmt=5'
    req = urllib.request.Request(ff_url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10, context=ctx)
    ff_data = json.loads(resp.read().decode('utf-8'))
    print(f"FF_RAW|{json.dumps(ff_data)[:500]}")
except Exception as e:
    print(f"FF_ERR|{e}")

# Try HTTP fallback for fund flow
try:
    ff_url_http = 'http://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=1.000001&fields2=f51,f52,f53,f54,f55&klt=101&lmt=5'
    req = urllib.request.Request(ff_url_http, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    ff_data = json.loads(resp.read().decode('utf-8'))
    print(f"FF_HTTP|{json.dumps(ff_data)[:500]}")
except Exception as e:
    print(f"FF_HTTP_ERR|{e}")