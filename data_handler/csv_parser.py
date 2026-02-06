# data_handler/csv_parser.py
import pandas as pd

from core.constants import Columns, TradeType
from core.schema import TransactionSchema, validate_schema


def clean_sbi_transaction_csv(filepath_or_buffer, encoding="shift_jis"):
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


def clean_sbi_cash_flow_csv(filepath_or_buffer, encoding="utf-8-sig"):
    # Cash flow log has a 9-line preamble; table header starts at line 10
    df = pd.read_csv(filepath_or_buffer, skiprows=9, encoding=encoding)

    df = df.rename(columns={
        "入出金日": "date",
        "区分": "category",
        "摘要": "description",
        "出金額": "debit",
        "入金額": "credit",
        "振替出金額": "transfer_debit",
        "振替入金額": "transfer_credit",
    })

    for col in ["debit", "credit", "transfer_debit", "transfer_credit"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .replace("-", "0")
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")

    df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d", errors="coerce")

    def classify(row):
        category = str(row["category"])
        desc = str(row["description"])

        tx_type = "Other"
        source = ""

        if category == "入金":
            tx_type = "Deposit"
            if "譲渡益税還付金" in desc:
                tx_type = "Tax"
                source = desc.strip()
            elif "配当" in desc:
                tx_type = "Dividend"
                parts = desc.split()
                source = parts[-1].strip() if len(parts) > 1 else desc.strip()
            else:
                if "即時入金" in desc:
                    source = desc.replace("即時入金", "").strip()
                else:
                    source = desc.strip()

        if category == "出金":
            tx_type = "Withdrawal"
            if "税" in desc:
                tx_type = "Tax"
            source = desc.strip()

        if category.startswith("振替"):
            tx_type = "Transfer"
            source = desc.strip()

        return pd.Series({"type": tx_type, "source": source})

    df[["type", "source"]] = df.apply(classify, axis=1)

    df["amount"] = (
        df["credit"] - df["debit"] - df["transfer_debit"] + df["transfer_credit"]
    )
    df["currency"] = "JPY"
    df["notes"] = df["description"]

    # Combine same-day cash movements to avoid duplicate rows from identical deposits
    agg_keys = ["date", "type", "source", "category", "description", "currency", "notes"]
    num_cols = ["debit", "credit", "transfer_debit", "transfer_credit", "amount"]
    for col in num_cols:
        if col not in df.columns:
            df[col] = 0
    df = (
        df.groupby(agg_keys, as_index=False)[num_cols]
        .sum()
    )

    return df


# Backward-compatible alias
clean_sbi_csv = clean_sbi_transaction_csv
