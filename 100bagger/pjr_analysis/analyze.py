import pickle, json, sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
data = pickle.load(open(sys.argv[1], 'rb')); sheet = {r['no']: r for r in json.load(open(sys.argv[2]))}
B = pd.Timestamp('2025-06-17'); B1 = pd.Timestamp('2026-06-17')
# financial-currency -> price-currency multiplier (approx FX on 2025-06-17)
FX = {'NVO': 1/6.45, 'SPOT': 1.15, 'STNE': 1/5.50, '9880.HK': 1/0.915}
def px(h, d, after=False):
    h = h['Close']; h.index = h.index.tz_localize(None)
    s = h[h.index >= d] if after else h[h.index <= d]
    return (s.iloc[0] if after else s.iloc[-1]) if len(s) else np.nan
def row(df, *names):
    for n in names:
        if df is not None and n in df.index: return df.loc[n]
    return None
rows = []
for t, d in data.items():
    if d['no'] is None: continue
    fin = d['fin']
    if fin is None or fin.empty: continue
    cols = sorted([c for c in fin.columns if c <= B - pd.Timedelta(days=45)])
    if not cols: continue
    fy = cols[-1]
    oi = row(fin, 'Operating Income', 'Total Operating Income As Reported')
    rd = row(fin, 'Research And Development')
    rev = row(fin, 'Total Revenue', 'Operating Revenue')
    ni = row(fin, 'Net Income Common Stockholders', 'Net Income')
    g = lambda s, c: (float(s[c]) if s is not None and c in s.index and pd.notna(s[c]) else np.nan)
    OI, RD, REV, NI = g(oi, fy), g(rd, fy), g(rev, fy), g(ni, fy)
    REVp = g(rev, cols[-2]) if len(cols) > 1 else np.nan
    if np.isnan(OI): continue
    rd_missing = np.isnan(RD); RD = 0.0 if rd_missing else RD
    # shares near B
    sh = np.nan
    s = d['shares']
    if s is not None and len(s):
        s = s.copy(); s.index = s.index.tz_localize(None); s = s[~s.index.duplicated(keep='last')]
        near = s[(s.index >= B - pd.Timedelta(days=60)) & (s.index <= B + pd.Timedelta(days=30))]
        if len(near): sh = float(near.median())
    if np.isnan(sh):
        for bs in (d['qbs'], d['bs']):
            r_ = row(bs, 'Ordinary Shares Number', 'Share Issued')
            if r_ is not None:
                r_ = r_.dropna(); r_ = r_[r_.index <= B + pd.Timedelta(days=100)]
                if len(r_): sh = float(r_.sort_index().iloc[-1]); break
    p0 = px(d['hist'], B); p1 = px(d['hist'], B1); pN = px(d['hist'], pd.Timestamp('2026-12-31'))
    fx = FX.get(t, 1.0)
    mcap = p0 * sh
    adj = (OI + RD) * fx
    rows.append(dict(no=d['no'], name=sheet[d['no']]['name'], ticker=t, fy=fy.date(), mcap=mcap,
                     op=OI*fx, rnd=RD*fx, rd_missing=rd_missing, adj=adj, rev=REV*fx, ni=NI*fx,
                     rev_g=REV/REVp-1 if REVp and REVp > 0 else np.nan,
                     pjr=mcap/adj if adj > 0 else np.nan, per_calc=mcap/(NI*fx) if NI > 0 else np.nan,
                     por=mcap/(OI*fx) if OI > 0 else np.nan, psr=mcap/(REV*fx) if REV > 0 else np.nan,
                     adj_margin=adj/(REV*fx) if REV > 0 else np.nan, op_margin=OI/REV if REV > 0 else np.nan,
                     r1y=p1/p0-1, rN=pN/p0-1, kr=t.endswith(('.KS', '.KQ')),
                     sheet_per=sheet[d['no']]['per_raw'], conclusion=sheet[d['no']]['conclusion']))
df = pd.DataFrame(rows)
bench = {b: (px(data[b]['hist'], B1)/px(data[b]['hist'], B)-1, px(data[b]['hist'], pd.Timestamp('2026-12-31'))/px(data[b]['hist'], B)-1) for b in ['SPY','QQQ','^KS11','^KQ11']}
df['ex1y'] = df['r1y'] - np.where(df.kr, bench['^KS11'][0], bench['SPY'][0])
df.to_csv(sys.argv[3], index=False, encoding='utf-8-sig')
json.dump({k: [float(v[0]), float(v[1])] for k, v in bench.items()}, open(sys.argv[3].replace('.csv', '_bench.json'), 'w'))
print('n=', len(df), 'profit(adj>0)=', df.pjr.notna().sum(), 'rd_missing=', df.rd_missing.sum())
print('bench', bench)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
print(df.sort_values('pjr')[['ticker','name','fy','mcap','op','rnd','rd_missing','pjr','por','psr','r1y','rN']].to_string())
