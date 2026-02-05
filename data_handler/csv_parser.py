# data_handler/csv_parser.py
import pandas as pd

from core.constants import Columns, TradeType
from core.schema import TransactionSchema, validate_schema


def clean_sbi_csv(filepath_or_buffer, encoding="shift_jis"):
    # Skip metadata and read from row 8 (0-indexed)
    df = pd.read_csv(filepath_or_buffer, skiprows=8, encoding=encoding)

    # Rename columns to standard English
    df.columns = [
        Columns.DATE,
        Columns.STOCK_NAME,
        Columns.STOCK_CODE,
        Columns.MARKET,
        Columns.TRADE_TYPE,
        Columns.TERM,
        Columns.ACCOUNT,
        Columns.TAX,
        Columns.QUANTITY,
        Columns.PRICE_PER_SHARE,
        Columns.FEE,
        Columns.TAX_AMOUNT,
        Columns.SETTLEMENT_DATE,
        Columns.TOTAL_AMOUNT,
    ]

    # Strip whitespace and normalize
    df[Columns.DATE] = pd.to_datetime(df[Columns.DATE], format="%Y/%m/%d")
    df[Columns.SETTLEMENT_DATE] = pd.to_datetime(
        df[Columns.SETTLEMENT_DATE], format="%Y/%m/%d")
    df[Columns.TRADE_TYPE] = df[Columns.TRADE_TYPE].str.strip().replace({
        "株式現物買": TradeType.BUY,
        "株式現物売": TradeType.SELL,
    })
    df[Columns.STOCK_CODE] = df[Columns.STOCK_CODE].astype(str).str.zfill(4)
    df[Columns.QUANTITY] = pd.to_numeric(df[Columns.QUANTITY], errors="coerce")
    df[Columns.PRICE_PER_SHARE] = pd.to_numeric(
        df[Columns.PRICE_PER_SHARE], errors="coerce")
    df[Columns.TOTAL_AMOUNT] = pd.to_numeric(df[Columns.TOTAL_AMOUNT], errors="coerce")

    # Remove invalid rows (optional)
    df = df.dropna(subset=[Columns.DATE, Columns.STOCK_CODE, Columns.TRADE_TYPE, Columns.QUANTITY])
    # print(df.head(3))  # Debug: print first few rows to verify

    # Combine exact duplicate rows (same date, stock_code, trade_type, price_per_share, etc.)
    group_cols = [
        Columns.DATE,
        Columns.STOCK_CODE,
        Columns.STOCK_NAME,
        Columns.TRADE_TYPE,
        Columns.PRICE_PER_SHARE,
        Columns.SETTLEMENT_DATE,
    ]
    agg_dict = {
        Columns.QUANTITY: "sum",
        Columns.TOTAL_AMOUNT: "sum",
        Columns.FEE: "sum",
    }
    # For other columns, keep the first value
    for col in df.columns:
        if col not in group_cols and col not in agg_dict:
            agg_dict[col] = "first"

    df = df.groupby(group_cols, as_index=False).agg(agg_dict)

    validate_schema(df, TransactionSchema.required, name="transactions_csv", raise_on_error=True)

    return df
