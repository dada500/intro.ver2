import pandas as pd, numpy as np, json, sys
from scipy.stats import spearmanr, pearsonr, mannwhitneyu
df = pd.read_csv(sys.argv[1]); bench = json.load(open(sys.argv[1].replace('.csv','_bench.json')))
def sp(x, y):
    m = x.notna() & y.notna(); r, p = spearmanr(x[m], y[m]); return f'rho={r:+.3f} p={p:.3f} n={m.sum()}'
print('BENCH 1y SPY %.1f%% QQQ %.1f%% | latest SPY %.1f%% QQQ %.1f%%' % (bench['SPY'][0]*100, bench['QQQ'][0]*100, bench['SPY'][1]*100, bench['QQQ'][1]*100))
for name, sub in [('ALL', df), ('US', df[~df.kr]), ('US & has R&D', df[~df.kr & ~df.rd_missing])]:
    print(f'\n### {name}  (n={len(sub)}, PJR defined={sub.pjr.notna().sum()})')
    for col in ['pjr', 'por', 'per_calc', 'psr', 'adj_margin', 'op_margin', 'rev_g']:
        print(f'  {col:10s} vs 1y: {sp(sub[col], sub.r1y)}  | vs now: {sp(sub[col], sub.rN)}')
    # log-pjr pearson
    m = sub.pjr.notna()
    print('  pearson log(PJR) vs log(1+r1y):', pearsonr(np.log(sub.pjr[m]), np.log1p(sub.r1y[m])))
    bands = pd.cut(sub.pjr, [0, 20, 50, 100, 1e9], labels=['<20', '20-50', '50-100', '>100'])
    bands = bands.cat.add_categories('적자(조정영익<0)').fillna('적자(조정영익<0)')
    g = sub.groupby(bands, observed=False).agg(n=('ticker', 'size'), med1y=('r1y', 'median'), mean1y=('r1y', 'mean'),
        hit_spy=('r1y', lambda s: (s > bench['SPY'][0]).mean()), win=('r1y', lambda s: (s > 0).mean()),
        medN=('rN', 'median'), meanN=('rN', 'mean'))
    print(g.round(3).to_string())
    q = pd.qcut(sub.pjr, 4, labels=['Q1(저PJR)', 'Q2', 'Q3', 'Q4(고PJR)'])
    print(sub.groupby(q, observed=False).agg(n=('ticker','size'), pjr_rng=('pjr', lambda s: f'{s.min():.0f}-{s.max():.0f}'), med1y=('r1y','median'), mean1y=('r1y','mean'), medN=('rN','median')).round(3).to_string())
    a = sub.r1y[sub.pjr.notna()]; b = sub.r1y[sub.pjr.isna()]
    print('  흑자 vs 적자 1y median %.3f vs %.3f, MWU p=%.3f; mean %.3f vs %.3f' % (a.median(), b.median(), mannwhitneyu(a, b).pvalue, a.mean(), b.mean()))
    a = sub.rN[sub.pjr.notna()]; b = sub.rN[sub.pjr.isna()]
    print('  흑자 vs 적자 now median %.3f vs %.3f, MWU p=%.3f' % (a.median(), b.median(), mannwhitneyu(a, b).pvalue))
# 20-50 sweet spot test
us = df[~df.kr]
s = us.pjr.between(20, 50)
print('\nUS PJR 20-50 vs rest(흑자) 1y median', us.r1y[s].median(), us.r1y[~s & us.pjr.notna()].median(), mannwhitneyu(us.r1y[s], us.r1y[~s & us.pjr.notna()]).pvalue)
# Does R&D add info beyond POR? Among US with R&D and OI>0: rank of pjr vs por difference
m = us.por.notna() & ~us.rd_missing
print('US OI>0 & R&D: POR', sp(us.por[m], us.r1y[m]), ' PJR', sp(us.pjr[m], us.r1y[m]))
# companies where OI<0 but adj>0 (R&D turns them positive) — PJR's unique territory
u = us[(us.op <= 0) & (us.adj > 0)]
print('\n영업적자→조정흑자 (PJR만 정의됨):', len(u), 'median1y', u.r1y.median(), 'mean', u.r1y.mean())
print(u[['ticker','name','pjr','r1y','rN']].round(2).to_string())
