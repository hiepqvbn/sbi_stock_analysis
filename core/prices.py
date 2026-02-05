from __future__ import annotations

import time
from typing import Dict, List, Tuple
import pandas as pd
import yfinance as yf


_PRICE_CACHE = {
    "ts": 0.0,
    "data": {},  # { "6526": 1234.0 }
}
# keep prices for a few minutes to avoid repeated yfinance calls
CACHE_TTL_SEC = 300

_HIST_PRICE_CACHE: Dict[Tuple[str, str], float] = {}


def _to_yf_ticker_jp(stock_code: str) -> str:
    code = str(stock_code).strip()
    return f"{code}.T"


def get_stock_current_price(stock_code: str) -> float | None:
    ticker = f"{stock_code}.T"
    try:
        today_price = yf.Ticker(ticker).history(period="1d")["Close"].iloc[0]
        return float(today_price)
    except Exception as e:
        print(f"Warning: Failed to retrieve current price for {stock_code}: {e}")
        return None


def get_price_map(stock_codes: List[str]) -> Dict[str, float]:
    if not stock_codes:
        return {}
    now = time.time()
    cached = _PRICE_CACHE["data"]

    if now - _PRICE_CACHE["ts"] < CACHE_TTL_SEC and all(str(c) in cached for c in stock_codes):
        return {str(c): float(cached[str(c)]) for c in stock_codes}

    missing = [str(c) for c in stock_codes if str(c) not in cached]
    if not missing and now - _PRICE_CACHE["ts"] < CACHE_TTL_SEC:
        return {str(c): float(cached[str(c)]) for c in stock_codes}

    if not missing:
        return {str(c): float(cached[str(c)]) for c in stock_codes if str(c) in cached}

    tickers = [_to_yf_ticker_jp(c) for c in missing]
    try:
        data = yf.download(
            tickers=tickers,
            period="2d",
            interval="1d",
            progress=False,
            group_by="ticker",
            auto_adjust=False,
            threads=True,
        )
    except Exception as e:
        print(f"Warning: Failed to download prices: {e}")
        return {str(c): float(cached[str(c)]) for c in stock_codes if str(c) in cached}

    result: Dict[str, float] = {}
    for code, tk in zip(missing, tickers):
        px = None
        try:
            if len(tickers) == 1:
                px = float(data["Close"].dropna().iloc[-1])
            else:
                px = float(data[(tk, "Close")].dropna().iloc[-1])
        except Exception:
            px = None

        if px is not None:
            result[code] = px
            cached[code] = px

    _PRICE_CACHE["ts"] = now
    _PRICE_CACHE["data"] = cached

    out = {}
    for c in stock_codes:
        key = str(c)
        if key in cached:
            out[key] = float(cached[key])
    return out


def get_price_map_asof(stock_codes: List[str], end_date: str) -> Dict[str, float]:
    if not stock_codes or not end_date:
        return {}

    end_dt = pd.to_datetime(end_date, errors="coerce")
    if pd.isna(end_dt):
        return {}

    start = end_dt.strftime("%Y-%m-%d")
    end = (end_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    result: Dict[str, float] = {}
    missing: List[str] = []

    for code in stock_codes:
        key = (start, str(code))
        if key in _HIST_PRICE_CACHE:
            result[str(code)] = float(_HIST_PRICE_CACHE[key])
        else:
            missing.append(str(code))

    if not missing:
        return result

    tickers = [_to_yf_ticker_jp(c) for c in missing]
    try:
        data = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            interval="1d",
            progress=False,
            group_by="ticker",
            auto_adjust=False,
            threads=True,
        )
    except Exception as e:
        print(f"Warning: Failed to download historical prices: {e}")
        return result

    for code, tk in zip(missing, tickers):
        px = None
        try:
            if len(tickers) == 1:
                px = float(data["Close"].dropna().iloc[-1])
            else:
                px = float(data[(tk, "Close")].dropna().iloc[-1])
        except Exception:
            px = None

        if px is not None:
            key = (start, str(code))
            _HIST_PRICE_CACHE[key] = px
            result[str(code)] = px

    return result
