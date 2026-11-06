import pickle, json, pandas as pd, numpy as np, sys, warnings
from scipy.stats import spearmanr, mannwhitneyu
warnings.filterwarnings('ignore')
data = pickle.load(open(sys.argv[1], 'rb')); sheet = {r['no']: r for r in json.load(open(sys.argv[2]))}
df = pd.read_csv(sys.argv[3])
def sp(x, y):
    m = x.notna() & y.notna(); r, p = spearmanr(x[m], y[m]); return f'rho={r:+.3f} p={p:.3f} n={m.sum()}'
# (1) sheet-recorded PJR: D(억불)*100 / adjOI 2024 (백만달러)
rec = []
for _, r in df[~df.kr].iterrows():
    s = sheet[r.no]; a = s['items'].get('adj_oi', {})
    try: d = float(s['mcap_raw'])
    except: continue
    adj = a.get('2024') or a.get('2023')
    if adj and adj > 0: rec.append(dict(ticker=r.ticker, pjr_sheet=d * 100 / adj, pjr_calc=r.pjr, r1y=r.r1y, rN=r.rN))
rs = pd.DataFrame(rec); print('SHEET-RECORDED PJR (US):'); print(rs.round(2).sort_values('pjr_sheet').to_string())
print(' sheet PJR vs 1y', sp(rs.pjr_sheet, rs.r1y), '| vs now', sp(rs.pjr_sheet, rs.rN))
print(' agreement sheet vs calc', sp(rs.pjr_sheet, rs.pjr_calc))
# (2) adjOI growth FY(base) -> next FY vs return
B = pd.Timestamp('2025-06-17'); g = []
for _, r in df.iterrows():
    fin = data[r.ticker]['fin']; cols = sorted(fin.columns)
    base = pd.Timestamp(r.fy); nxt = [c for c in cols if c > base + pd.Timedelta(days=300)]
    if not nxt: continue
    c = nxt[0]
    oi = fin.loc['Operating Income', c] if 'Operating Income' in fin.index else np.nan
    rd = fin.loc['Research And Development', c] if 'Research And Development' in fin.index else 0
    rd = 0 if pd.isna(rd) else rd
    adj1 = (oi + rd) * (r.adj / ((r.op + r.rnd) if (r.op + r.rnd) else 1))  # same fx scale
    rev1 = fin.loc['Total Revenue', c] if 'Total Revenue' in fin.index else np.nan
    g.append(dict(ticker=r.ticker, kr=r.kr, adj0=r.adj, adj1=adj1, dadj_rev=(adj1 - r.adj) / abs(r.rev) if r.rev else np.nan,
                  adj_g=(adj1 / r.adj - 1) if r.adj > 0 else np.nan, r1y=r.r1y, rN=r.rN, pjr=r.pjr,
                  fwd_pjr=r.mcap / adj1 if adj1 > 0 else np.nan, turned=(r.adj <= 0) and (adj1 > 0)))
G = pd.DataFrame(g); U = G[~G.kr]
print('\nADJ-OI GROWTH next FY vs return (US):')
print(' adjOI growth (base>0) vs 1y', sp(U.adj_g, U.r1y), '| now', sp(U.adj_g, U.rN))
print(' Δ조정영익/매출 (all) vs 1y', sp(U.dadj_rev, U.r1y), '| now', sp(U.dadj_rev, U.rN))
print(' "미래 PJR"(시총/다음해 조정영익) vs 1y', sp(U.fwd_pjr, U.r1y), '| now', sp(U.fwd_pjr, U.rN))
up = U.dadj_rev > 0
print(' 조정영익 개선 vs 악화: 1y median %.3f vs %.3f (p=%.3f), now %.3f vs %.3f (p=%.3f), n=%d/%d' % (
    U.r1y[up].median(), U.r1y[~up].median(), mannwhitneyu(U.r1y[up], U.r1y[~up]).pvalue,
    U.rN[up].median(), U.rN[~up].median(), mannwhitneyu(U.rN[up], U.rN[~up]).pvalue, up.sum(), (~up).sum()))
q = pd.qcut(U.dadj_rev, 4, labels=['Q1 악화', 'Q2', 'Q3', 'Q4 개선'])
print(U.groupby(q, observed=False).agg(n=('ticker', 'size'), med1y=('r1y', 'median'), medN=('rN', 'median')).round(3).to_string())
G.to_csv(sys.argv[3].replace('.csv', '_growth.csv'), index=False, encoding='utf-8-sig')
# (3) user's own buy calls
print('\nYOUR CALLS (결론 column):')
c = df[df.conclusion.notna()][['ticker', 'name', 'conclusion', 'pjr', 'r1y', 'rN']].copy()
c['conclusion'] = c.conclusion.str.replace('\n', ' ').str[:25]
print(c.round(2).to_string()); print(' median 1y %.3f, now %.3f, n=%d' % (c.r1y.median(), c.rN.median(), len(c)))
