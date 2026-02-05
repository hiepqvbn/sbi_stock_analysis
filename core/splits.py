from __future__ import annotations

import time
from typing import Dict
import pandas as pd
import yfinance

from core.constants import Columns

_SPLIT_CACHE: Dict[str, Dict[str, object]] = {
    # "7203.T": {"ts": 0.0, "data": pd.Series(...)}
}
SPLIT_CACHE_TTL_SEC = 24 * 60 * 60  # 24 hours


def _get_splits_for_ticker(ticker: str) -> pd.Series:
    now = time.time()
    cached = _SPLIT_CACHE.get(ticker)
    if cached and (now - float(cached.get("ts", 0.0)) < SPLIT_CACHE_TTL_SEC):
        return cached.get("data", pd.Series(dtype=float))

    try:
        splits = yfinance.Ticker(ticker).splits
        if splits is None:
            splits = pd.Series(dtype=float)
        _SPLIT_CACHE[ticker] = {"ts": now, "data": splits}
        return splits
    except Exception as e:
        if cached and "data" in cached:
            return cached["data"]  # type: ignore[return-value]
        print(f"Warning: Failed to retrieve stock splits for {ticker}: {e}")
        return pd.Series(dtype=float)


def record_stock_split_adjustments(df: pd.DataFrame, stock_code) -> pd.DataFrame:
    stock_df = df[df[Columns.STOCK_CODE] == stock_code].copy()
    ticker = f"{stock_code}.T"
    try:
        splits = _get_splits_for_ticker(ticker)
        if splits is not None and not splits.empty:
            dates = pd.to_datetime(stock_df[Columns.DATE], errors="coerce")
            if dates.dt.tz is None:
                dates = dates.dt.tz_localize("UTC")
            else:
                dates = dates.dt.tz_convert("UTC")
            for split_date, split_ratio in splits.items():
                mask = dates < split_date
                if mask.any():
                    stock_df.loc[mask, Columns.QUANTITY] *= split_ratio
                    stock_df.loc[mask, Columns.PRICE_PER_SHARE] /= split_ratio
            stock_df.sort_values(by=[Columns.DATE, "id"], inplace=True)
        return stock_df
    except Exception as e:
        print(f"Warning: Failed to retrieve stock splits: {e}")
        return stock_df


def stocks_split_adjustments(df: pd.DataFrame) -> pd.DataFrame:
    adjusted_rows = []
    for code, group in df.groupby(Columns.STOCK_CODE, sort=False):
        adjusted_group = record_stock_split_adjustments(group, code)
        adjusted_rows.append(adjusted_group)
    adjusted_df = pd.concat(adjusted_rows, ignore_index=True)
    return adjusted_df
