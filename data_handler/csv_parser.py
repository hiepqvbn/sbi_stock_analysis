# data_handler/csv_parser.py
import pandas as pd

def clean_sbi_csv(filepath_or_buffer, encoding="shift_jis"):
    # Skip metadata and read from row 8 (0-indexed)
    df = pd.read_csv(filepath_or_buffer, skiprows=8, encoding=encoding)

    # Rename columns to standard English
    df.columns = [
        "date", "stock_name", "stock_code", "market", "trade_type", "term",
        "account", "tax", "quantity", "price_per_share", "fee", "tax_amount",
        "settlement_date", "total_amount"
    ]

    # Strip whitespace and normalize
    df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d")
    df["settlement_date"] = pd.to_datetime(df["settlement_date"], format="%Y/%m/%d")
    df["trade_type"] = df["trade_type"].str.strip().replace({
        "株式現物買": "Buy",
        "株式現物売": "Sell"
    })
    df["stock_code"] = df["stock_code"].astype(str).str.zfill(4)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price_per_share"] = pd.to_numeric(df["price_per_share"], errors="coerce")
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")

    # Remove invalid rows (optional)
    df = df.dropna(subset=["date", "stock_code", "trade_type", "quantity"])
    # print(df.head(3))  # Debug: print first few rows to verify

    # Combine exact duplicate rows (same date, stock_code, trade_type, price_per_share, etc.)
    group_cols = [
        "date", "stock_code", "stock_name", "trade_type",
        "price_per_share", "settlement_date"
    ]
    agg_dict = {
        "quantity": "sum",
        "total_amount": "sum",
        "fee": "sum"
    }
    # For other columns, keep the first value
    for col in df.columns:
        if col not in group_cols and col not in agg_dict:
            agg_dict[col] = "first"

    df = df.groupby(group_cols, as_index=False).agg(agg_dict)

    return df
