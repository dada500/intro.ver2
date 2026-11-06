import openpyxl, re, json, sys
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
ws = wb['재무지표분석(연간)']
YEARS = {c: str(ws.cell(1, c).value) for c in range(11, 24)}  # K..W

def num(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip().replace(',', '').replace('$', '')
    if s in ('-', '', 'N/A'): return None
    m = re.match(r'^\(?(-?\d+(?:\.\d+)?)\)?\s*(%)?', s)
    if not m: return None
    x = float(m.group(1))
    if m.group(2): x /= 100
    if s.startswith('(') and x > 0: x = -x
    return x

def classify(label):
    l = (label or '').replace(' ', '')
    if '조정' in l and '률' in l: return 'adj_margin'
    if '조정' in l or ('R&D' in l.upper() and ('추가' in l or '더한' in l)):
        return 'adj_margin' if '률' in l else 'adj_oi'
    if ('R&D' in l.upper() or '알앤디' in l or '연구개발' in l): return 'rnd'
    if '성장률' in l: return 'growth'
    if '영업이익률' in l: return 'op_margin'
    if '영업이익' in l: return 'op'
    if '매출총이익' in l or '매출이익' in l: return 'gp'
    if '순이익' in l: return 'ni'
    if '매출' in l: return 'rev'
    return None

starts = [r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value not in (None, '')]
out = []
for i, r0 in enumerate(starts):
    r1 = (starts[i + 1] - 1) if i + 1 < len(starts) else ws.max_row
    rec = {'no': ws.cell(r0, 1).value, 'name': ws.cell(r0, 2).value, 'ticker': ws.cell(r0, 3).value,
           'mcap_raw': ws.cell(r0, 4).value, 'rev_raw': ws.cell(r0, 5).value, 'per_raw': ws.cell(r0, 6).value,
           'conclusion': ws.cell(r0, 24).value, 'row': r0, 'items': {}}
    for r in range(r0, r1 + 1):
        k = classify(ws.cell(r, 10).value)
        if not k or k in rec['items']: continue
        rec['items'][k] = {YEARS[c]: num(ws.cell(r, c).value) for c in YEARS if num(ws.cell(r, c).value) is not None}
    out.append(rec)
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1, default=str)
print(len(out), 'blocks')
for o in out:
    a = o['items'].get('adj_oi', {}); op = o['items'].get('op', {}); rd = o['items'].get('rnd', {})
    print(o['no'], o['name'], o['ticker'], o['mcap_raw'], '| adjOI', {k: a[k] for k in ('2023', '2024', '2025') if k in a},
          '| op24', op.get('2024'), 'rd24', rd.get('2024'))
