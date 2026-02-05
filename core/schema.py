from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import pandas as pd

from core.constants import Columns


@dataclass(frozen=True)
class TransactionSchema:
    required: List[str] = (
        Columns.DATE,
        Columns.STOCK_NAME,
        Columns.STOCK_CODE,
        Columns.TRADE_TYPE,
        Columns.QUANTITY,
        Columns.PRICE_PER_SHARE,
        Columns.TOTAL_AMOUNT,
        Columns.SETTLEMENT_DATE,
        Columns.FEE,
    )


@dataclass(frozen=True)
class HoldingsSnapshotSchema:
    required: List[str] = (
        Columns.STOCK_CODE,
        Columns.STOCK_NAME,
        Columns.QTY,
        Columns.AVG_COST,
        Columns.COST_TOTAL,
        Columns.CURRENT_PRICE,
        Columns.MARKET_VALUE,
        Columns.UNREALIZED,
        Columns.REALIZED,
        Columns.TOTAL_PNL,
        Columns.UNREALIZED_PCT,
    )


@dataclass(frozen=True)
class RealizedWindowSchema:
    required: List[str] = (
        Columns.STOCK_CODE,
        Columns.REALIZED_WINDOW,
        Columns.COST_BASIS_WINDOW,
    )


@dataclass(frozen=True)
class TradeLedgerInputSchema:
    required: List[str] = (
        Columns.DATE,
        Columns.TRADE_TYPE,
        Columns.QUANTITY,
        Columns.PRICE_PER_SHARE,
        Columns.FEE,
    )


@dataclass(frozen=True)
class RealizedWindowInputSchema:
    required: List[str] = (
        Columns.DATE,
        Columns.STOCK_CODE,
        Columns.TRADE_TYPE,
        Columns.QUANTITY,
        Columns.TOTAL_AMOUNT,
        Columns.FEE,
    )


def missing_columns(df: pd.DataFrame, required: Iterable[str]) -> List[str]:
    if df is None:
        return list(required)
    cols = set(df.columns)
    return [c for c in required if c not in cols]


def validate_schema(
    df: pd.DataFrame,
    required: Iterable[str],
    *,
    name: str = "data",
    raise_on_error: bool = True,
) -> bool:
    missing = missing_columns(df, required)
    if missing:
        msg = f"Missing required columns in {name}: {missing}"
        if raise_on_error:
            raise ValueError(msg)
        print(f"Warning: {msg}")
        return False
    return True
