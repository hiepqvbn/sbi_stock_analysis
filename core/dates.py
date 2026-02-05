from __future__ import annotations

from typing import Optional
import pandas as pd


def to_dt(s):
    return pd.to_datetime(s, errors="coerce")


def slice_by_date(
    df: pd.DataFrame,
    start_date: Optional[str],
    end_date: Optional[str],
    date_col: str = "date",
) -> pd.DataFrame:
    if df is None or df.empty or date_col not in df.columns:
        return df

    out = df.copy()
    out[date_col] = to_dt(out[date_col])

    if start_date:
        out = out[out[date_col] >= to_dt(start_date)]
    if end_date:
        out = out[out[date_col] <= to_dt(end_date)]
    return out


def slice_df_by_date_range(
    df: pd.DataFrame,
    start_date: pd.Timestamp | str | None,
    end_date: pd.Timestamp | str | None,
) -> pd.DataFrame:
    return slice_by_date(df, start_date, end_date, date_col="date")
