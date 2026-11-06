import json, sys, time, pickle, warnings
import yfinance as yf, pandas as pd
warnings.filterwarnings('ignore')
sheet = json.load(open(sys.argv[1]))
KR = {'토모큐브':'475960.KQ','알테오젠':'196170.KQ','삼천당제약':'000250.KQ','두산에너빌리티':'034020.KS',
      '리가켐바이오':'141080.KQ','시프트업':'462870.KS','메디톡스':'086900.KQ','삼양식품':'003230.KS',
      '실리콘투':'257720.KQ','한화솔루션':'009830.KS','퍼스텍':'010820.KS','원텍':'336570.KQ','두산로보틱스':'454910.KS'}
US_FIX = {'나비타스 세미컨덕터':'NVTS','사운드하운드AI':'SOUN','레드캣홀딩스':'RCAT','C3 AI':'AI','퍼스트솔라':'FSLR',
          '엔페이즈 에너지':'ENPH','넥스트랙커':'NXT','솔라엣지':'SEDG','엔비디아':'NVDA','솔리드파워':'SLDP',
          'UBTECH Robotics':'9880.HK','파이서브':'FISV'}
SKIP = {'HFG','LMBS','SOLT','WISE.L'}  # ETFs / no fundamentals
tick = {}
for r in sheet:
    n = (r['name'] or '').strip(); t = (r['ticker'] or '').strip()
    t = KR.get(n) or US_FIX.get(n) or t
    if t and t not in SKIP and t not in tick.values(): tick[r['no']] = t
print(len(tick), 'tickers')
data = {}
for no, t in tick.items():
    for attempt in range(3):
        try:
            tk = yf.Ticker(t)
            h = tk.history(start='2025-01-01', end='2026-11-07', auto_adjust=True)
            fin = tk.income_stmt; qfin = tk.quarterly_income_stmt
            bs = tk.balance_sheet; qbs = tk.quarterly_balance_sheet
            try: sh = tk.get_shares_full(start='2025-01-01', end='2025-12-31')
            except Exception: sh = None
            info = {}
            try: fi = tk.fast_info; info = {'currency': fi.get('currency'), 'shares': fi.get('shares')}
            except Exception: pass
            data[t] = dict(no=no, hist=h[['Close']], fin=fin, qfin=qfin, bs=bs, qbs=qbs, shares=sh, info=info)
            print(t, len(h), fin.shape if fin is not None else None, flush=True); break
        except Exception as e:
            print('ERR', t, e, flush=True); time.sleep(3)
    time.sleep(0.4)
for b in ['SPY', 'QQQ', '^KS11', '^KQ11']:
    data[b] = dict(no=None, hist=yf.Ticker(b).history(start='2025-01-01', end='2026-11-07', auto_adjust=True)[['Close']])
pickle.dump(data, open(sys.argv[2], 'wb'))
