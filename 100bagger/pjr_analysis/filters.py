import pandas as pd, numpy as np, sys, json
from scipy.stats import spearmanr, mannwhitneyu
px = pd.read_pickle(sys.argv[1]); px.index = pd.to_datetime(px.index).tz_localize(None)
df = pd.read_csv(sys.argv[2]); gr = pd.read_csv(sys.argv[3])
B = pd.Timestamp('2025-06-17')
def at(s, d): s = s[:d].dropna(); return s.iloc[-1] if len(s) else np.nan
rows = []
for t in df.ticker:
    s = px[t].dropna(); h = s[:B]
    p0 = at(s, B)
    r = {k: (p0 / at(s, B - pd.Timedelta(days=k)) - 1) if len(h) and h.index[0] <= B - pd.Timedelta(days=k - 5) else np.nan for k in (91, 182, 273, 365)}
    rs = 0.4 * r[91] + 0.2 * r[182] + 0.2 * r[273] + 0.2 * r[365]
    ma50 = h[-50:].mean() if len(h) >= 50 else np.nan; ma200 = h[-200:].mean() if len(h) >= 200 else np.nan
    rows.append(dict(ticker=t, rs_raw=rs, r6m=r[182], above50=p0 > ma50 if ma50 == ma50 else np.nan,
                     above200=p0 > ma200 if ma200 == ma200 else np.nan))
F = df.merge(pd.DataFrame(rows), on='ticker').merge(gr[['ticker', 'dadj_rev']], on='ticker', how='left')
spy = px['SPY']; spy_rs = 0.4*(at(spy,B)/at(spy,B-pd.Timedelta(days=91))-1)+0.2*(at(spy,B)/at(spy,B-pd.Timedelta(days=182))-1)+0.2*(at(spy,B)/at(spy,B-pd.Timedelta(days=273))-1)+0.2*(at(spy,B)/at(spy,B-pd.Timedelta(days=365))-1)
F['rs_pct'] = F.rs_raw.rank(pct=True) * 99
musd = np.where(F.kr, F.mcap / 1380, np.where(F.ticker == '9880.HK', F.mcap / 7.8, F.mcap))
F['mcap_usd'] = musd
F['f_rs'] = F.rs_pct >= 80
F['f_ma'] = (F.above50 == True) & (F.above200 == True)
F['f_cap'] = (F.mcap_usd >= 1e9) & (F.mcap_usd <= 5e10)
F['f_all'] = F.f_rs & F.f_ma & F.f_cap
F['s2'] = (F.adj > 0) & (F.dadj_rev > 0)
print('SPY RS raw', round(spy_rs, 3), '| RS available n=', F.rs_raw.notna().sum(), '| MA available', F.above200.notna().sum())
def sp(x, y):
    m = x.notna() & y.notna(); r, p = spearmanr(x[m].astype(float), y[m]); return f'ρ={r:+.2f} (p={p:.2f}, n={m.sum()})'
def cmp(name, mask, sub):
    a, b = sub[mask], sub[~mask & mask.notna()]
    out = {}
    for col in ('r1y', 'rN'):
        p = mannwhitneyu(a[col].dropna(), b[col].dropna()).pvalue if len(a) > 2 and len(b) > 2 else np.nan
        out[col] = (a[col].median(), b[col].median(), p)
    print(f'  {name:28s} 통과 {len(a):3d} / 탈락 {len(b):3d} | 1y {out["r1y"][0]:+.0%} vs {out["r1y"][1]:+.0%} (p={out["r1y"][2]:.2f})'
          f' | 현재 {out["rN"][0]:+.0%} vs {out["rN"][1]:+.0%} (p={out["rN"][2]:.2f}) | SPY이긴비율 1y {(a.r1y>0.254).mean():.0%} vs {(b.r1y>0.254).mean():.0%}')
for nm, sub in [('ALL', F), ('US', F[~F.kr])]:
    print(f'\n### {nm} n={len(sub)}')
    print('  RS raw vs 1y', sp(sub.rs_raw, sub.r1y), '| vs now', sp(sub.rs_raw, sub.rN))
    print('  6m mom vs 1y', sp(sub.r6m, sub.r1y), '| vs now', sp(sub.r6m, sub.rN))
    q = pd.qcut(sub.rs_raw, 4, labels=['RS Q1(약)', 'Q2', 'Q3', 'RS Q4(강)'])
    print(sub.groupby(q, observed=False).agg(n=('ticker','size'), med1y=('r1y','median'), medN=('rN','median')).round(2).to_string())
    sub2 = sub[sub.rs_raw.notna()]
    cmp('RS≥80 (유니버스 내)', sub2.f_rs, sub2)
    cmp('RS > SPY', sub2.rs_raw > spy_rs, sub2)
    s3 = sub[sub.above200.notna()]
    cmp('50·200일선 위', s3.f_ma, s3)
    cmp('시총 10억~500억불', sub.f_cap, sub)
    cmp('1차 3개 모두 통과', sub2.f_all, sub2)
    cmp('2차(흑자+개선)', sub.s2, sub)
    cmp('1차 전부 + 2차', sub2.f_all & sub2.s2, sub2)
    cmp('RS≥80 + 2차', sub2.f_rs & sub2.s2, sub2)
    cmp('MA위 + 2차', s3.f_ma & s3.s2, s3)
    cmp('시총밴드 + 2차', sub.f_cap & sub.s2, sub)
print('\n1차 전부 통과 종목 (US+KR):')
print(F[F.f_all][['ticker','name','rs_pct','mcap_usd','pjr','s2','r1y','rN']].round(2).sort_values('rs_pct').to_string())
F.drop(columns=['conclusion','sheet_per'], errors='ignore').round(4).to_csv(sys.argv[4], index=False, encoding='utf-8-sig')
