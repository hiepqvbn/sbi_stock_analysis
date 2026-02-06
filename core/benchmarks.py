from __future__ import annotations

import time
from typing import Dict, Optional
import pandas as pd
import yfinance as yf


_BENCH_CACHE: Dict[str, Dict[str, object]] = {}
BENCH_CACHE_TTL_SEC = 6 * 60 * 60  # 6 hours


def get_benchmark_series(
    ticker: str,
    start_date: Optional[str],
    end_date: Optional[str],
) -> pd.Series:
    if not ticker:
        return pd.Series(dtype=float)

    start_dt = pd.to_datetime(start_date, errors="coerce") if start_date else None
    end_dt = pd.to_datetime(end_date, errors="coerce") if end_date else None

    start = start_dt.strftime("%Y-%m-%d") if start_dt is not None and not pd.isna(start_dt) else None
    end = None
    if end_dt is not None and not pd.isna(end_dt):
        end = (end_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    cache_key = f"{ticker}|{start}|{end}"
    now = time.time()
    cached = _BENCH_CACHE.get(cache_key)
    if cached and (now - float(cached.get("ts", 0.0)) < BENCH_CACHE_TTL_SEC):
        return cached.get("data", pd.Series(dtype=float))
    print(f"Downloading benchmark prices for {ticker} from {start} to {end}...")
    try:
        data = yf.download(
            tickers=ticker,
            start=start,
            end=end,
            interval="1d",
            progress=False,
            auto_adjust=False,
            threads=True,
        )
        if not isinstance(data, pd.DataFrame) or data.empty:
            return pd.Series(dtype=float)

        s = None
        if isinstance(data.columns, pd.MultiIndex):
            lvl0 = data.columns.get_level_values(0)
            lvl1 = data.columns.get_level_values(1)
            if "Close" in lvl1:
                s = data.xs("Close", axis=1, level=1)
            elif "Close" in lvl0:
                s = data["Close"]
            elif "Adj Close" in lvl1:
                s = data.xs("Adj Close", axis=1, level=1)
            elif "Adj Close" in lvl0:
                s = data["Adj Close"]
        else:
            if "Close" in data.columns:
                s = data["Close"]
            elif "Adj Close" in data.columns:
                s = data["Adj Close"]

        if s is None:
            return pd.Series(dtype=float)

        if isinstance(s, pd.DataFrame):
            if ticker in s.columns:
                s = s[ticker]
            else:
                s = s.iloc[:, 0]
        s = s.dropna()
        s.index = pd.to_datetime(s.index)
    except Exception as e:
        print(f"Warning: Failed to download benchmark prices for {ticker}: {e}")
        return pd.Series(dtype=float)

    _BENCH_CACHE[cache_key] = {"ts": now, "data": s}
    return s
