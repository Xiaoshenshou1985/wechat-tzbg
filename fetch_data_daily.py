#!/usr/bin/env python3.11
"""Fetch A-share pre-market data v2 - fixed field mapping"""
import json, urllib.request, urllib.error, ssl, time, re

def get_tencent_quote(code):
    """Get real-time quote from Tencent QT API. Returns dict or None."""
    url = f"http://qt.gtimg.cn/q={code}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        raw = resp.read().decode('gbk', errors='replace')
        m = re.search(r'"(.*?)"', raw)
        if not m: return None
        parts = m.group(1).split('~')
        # Tencent QT format: [3]=price, [4]=yclose, [5]=open, [31]=change, [32]=chg%, [33]=high, [34]=low
        # [6]=volume(手), [37]=amount(万元)
        price = parts[3] if len(parts) > 3 else '0'
        yclose = parts[4] if len(parts) > 4 else '0'
        chg = parts[31] if len(parts) > 31 else '0'
        chg_pct = parts[32] if len(parts) > 32 else '0'
        volume = parts[6] if len(parts) > 6 else '0'
        amount_wan = parts[37] if len(parts) > 37 else '0'
        high = parts[33] if len(parts) > 33 else '0'
        low = parts[34] if len(parts) > 34 else '0'
        open_p = parts[5] if len(parts) > 5 else '0'
        return {
            'name': parts[1],
            'code': parts[2],
            'price': float(price),
            'yclose': float(yclose),
            'change': float(chg),
            'change_pct': float(chg_pct),
            'volume': int(volume),
            'amount_wan': float(amount_wan),
            'high': float(high),
            'low': float(low),
            'open': float(open_p),
        }
    except Exception as e:
        return {'error': str(e), 'code': code}

# ─── 1. Major Indices ───
print("=== 五大指数 ===")
indices = {}
for code in ['sh000001', 'sz399001', 'sz399006', 'sh000688', 'sh000016']:
    q = get_tencent_quote(code)
    if q and 'error' not in q:
        indices[q['code']] = q
        print(f"  {q['name']}: {q['price']:.2f} ({q['change_pct']:+.2f}%) 成交{q['amount_wan']/10000:.0f}亿")
    time.sleep(0.3)

# ─── 2. Global Indices via Sina ───
print("\n=== 全球指数 ===")
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request('https://finance.sina.com.cn/', headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
    })
    resp = urllib.request.urlopen(req, timeout=8, context=ctx)
    html = resp.read().decode('utf-8', errors='replace')
    # Try to find index blocks
    for pat in ['道琼斯', '纳斯达克', '标普500', '恒生指数', '日经', '富时']:
        for m in re.finditer(rf'({pat})\s*([\d,]+\.?\d*)\s*([+-]?\d+\.?\d*)\s*([+-]?\d+\.?\d*)%?', html):
            print(f"  {m.group(1)}: {m.group(2)} ({m.group(3)}{m.group(4)}%)")
except Exception as e:
    print(f"  Error: {e}")

# ─── 3. Concept Sector Rankings ───
print("\n=== 概念板块排行 ===")
try:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = "https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=15&po=1&np=1&fields=f2,f3,f4,f12,f14&fs=m:90+t:3"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=8, context=ctx)
    raw = resp.read().decode('utf-8')
    data = json.loads(raw)
    diff = data.get('data', {}).get('diff', {})
    concepts = []
    if isinstance(diff, dict):
        items = list(diff.values())
    elif isinstance(diff, list):
        items = diff
    else:
        items = []
    for item in items[:15]:
        name = item.get('f14', '')
        chg = item.get('f3', 0)
        if isinstance(chg, (int, float)) and abs(chg) > 20:
            chg = chg / 100
        concepts.append({'name': name, 'change_pct': chg, 'f4': item.get('f4', 0)})
        print(f"  {name}: {chg:+.2f}%")
except Exception as e:
    print(f"  Error: {e}")
    concepts = []

# ─── 4. Industry Rankings ───
print("\n=== 行业板块排行 ===")
try:
    url = "https://push2.eastmoney.com/api/qt/clist/get?cb=&pn=1&pz=10&po=1&np=1&fields=f2,f3,f4,f12,f14&fs=m:90+t:2"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=8, context=ctx)
    raw = resp.read().decode('utf-8')
    data = json.loads(raw)
    diff = data.get('data', {}).get('diff', {})
    industries = []
    if isinstance(diff, dict):
        items = list(diff.values())
    elif isinstance(diff, list):
        items = diff
    else:
        items = []
    for item in items[:10]:
        name = item.get('f14', '')
        chg = item.get('f3', 0)
        if isinstance(chg, (int, float)) and abs(chg) > 20:
            chg = chg / 100
        industries.append({'name': name, 'change_pct': chg, 'f4': item.get('f4', 0)})
        print(f"  {name}: {chg:+.2f}%")
except Exception as e:
    print(f"  Error: {e}")
    industries = []

# ─── 5. Market Fund Flow ───
print("\n=== 市场资金流 ===")
try:
    url = "https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get?secid=1.000001&fields2=f51,f52,f53,f54,f55&klt=101&lmt=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=8, context=ctx)
    raw = resp.read().decode('utf-8')
    data = json.loads(raw)
    klines = data.get('data', {}).get('klines', [])
    fund_flow = []
    if klines:
        for line in klines[-3:]:
            parts = line.split('~')
            date = parts[0]
            main_in = float(parts[1]) if len(parts) > 1 and parts[1] else 0
            small_in = float(parts[2]) if len(parts) > 2 and parts[2] else 0
            mid_in = float(parts[3]) if len(parts) > 3 and parts[3] else 0
            big_in = float(parts[4]) if len(parts) > 4 and parts[4] else 0
            total_in = main_in + small_in + mid_in + big_in
            fund_flow.append({'date': date, 'main_net': main_in, 'small_net': small_in, 'mid_net': mid_in, 'big_net': big_in, 'total': total_in})
            print(f"  {date}: 主力{main_in:+.0f}亿 散户{small_in:+.0f}亿 合计{total_in:+.0f}亿")
    else:
        print("  No fund flow data available")
except Exception as e:
    print(f"  Error: {e}")
    fund_flow = []

# ─── 6. eltdx full market scan for top gainers/losers ───
print("\n=== 全市场扫描（涨跌幅排行）===")
try:
    from eltdx import Client
    c = Client()
    all_stocks = c.get_stock_codes_all()
    a_share_codes = []
    for s in all_stocks:
        code = s.split('\t')[0]
        if code.startswith('sh6') or code.startswith('sh688') or \
           code.startswith('sz0') or code.startswith('sz001') or \
           code.startswith('sz002') or code.startswith('sz003') or \
           code.startswith('sz3'):
            a_share_codes.append(code)

    all_rows = []
    for i in range(0, len(a_share_codes), 1000):
        chunk = a_share_codes[i:i+1000]
        table = c.helpers.quote_table(chunk)
        all_rows.extend(table.rows)
        print(f"  Chunk {i//1000+1}: {len(table.rows)} rows")
        time.sleep(0.5)

    # Filter None change_pct
    valid = [r for r in all_rows if r.change_pct is not None]
    top_gainers = sorted(valid, key=lambda r: r.change_pct, reverse=True)[:30]
    top_losers = sorted(valid, key=lambda r: r.change_pct)[:30]
    hot_volume = sorted(valid, key=lambda r: r.amount or 0, reverse=True)[:20]

    print(f"\n  涨幅TOP10:")
    for r in top_gainers[:10]:
        print(f"    {r.name}({r.code}): +{r.change_pct:.2f}% 成交{(r.amount or 0)/1e8:.0f}亿")

    print(f"\n  跌幅TOP10:")
    for r in top_losers[:10]:
        print(f"    {r.name}({r.code}): {r.change_pct:.2f}% 成交{(r.amount or 0)/1e8:.0f}亿")

    print(f"\n  成交额TOP10:")
    for r in hot_volume[:10]:
        print(f"    {r.name}({r.code}): 成交{(r.amount or 0)/1e8:.0f}亿 {r.change_pct:+.2f}%")

    # Save full scan results
    scan_result = {
        'top_gainers': [{'code': r.code, 'name': r.name, 'change_pct': r.change_pct, 'amount': r.amount} for r in top_gainers[:30]],
        'top_losers': [{'code': r.code, 'name': r.name, 'change_pct': r.change_pct, 'amount': r.amount} for r in top_losers[:30]],
        'hot_volume': [{'code': r.code, 'name': r.name, 'change_pct': r.change_pct, 'amount': r.amount} for r in hot_volume[:20]],
    }
except Exception as e:
    print(f"  Error: {e}")
    scan_result = {'top_gainers': [], 'top_losers': [], 'hot_volume': []}

# ─── Save all results ───
result = {
    'indices': indices,
    'concepts': concepts,
    'industries': industries,
    'fund_flow': fund_flow,
    'scan': scan_result,
}
with open('/tmp/premarket_data.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\n✅ All data saved to /tmp/premarket_data.json")