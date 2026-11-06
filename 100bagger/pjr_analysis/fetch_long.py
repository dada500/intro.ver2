import pandas as pd, yfinance as yf, sys
df = pd.read_csv(sys.argv[1])
t = list(df.ticker) + ['SPY', '^KS11']
px = yf.download(t, start='2024-01-01', end='2026-11-07', auto_adjust=True, progress=False, threads=True)['Close']
px.to_pickle(sys.argv[2]); print(px.shape, px.iloc[:, :].notna().sum().min())
print(px.notna().sum().sort_values().head(8))
