# data_handler/db_manager.py
import os
import sqlite3
import pandas as pd


def init_db(db_path="data/portfolio.db"):
    # make dir if data/ folder is not exist
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            stock_code TEXT,
            stock_name TEXT,
            trade_type TEXT,
            quantity REAL,
            price_per_share REAL,
            total_amount REAL,
            settlement_date TEXT,
            fee REAL,
            UNIQUE(date, stock_code, trade_type, quantity, price_per_share, total_amount)
        );
    """)
    # Dividends
    c.execute("""
        CREATE TABLE IF NOT EXISTS dividends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            ticker TEXT,
            amount REAL,
            currency TEXT,
            notes TEXT,
            UNIQUE(date, ticker, amount)
        );
    """)
    # Cash Flows
    c.execute("""
        CREATE TABLE IF NOT EXISTS cash_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            amount REAL,
            currency TEXT,
            notes TEXT,
            UNIQUE(date, type, amount)
        );
    """)
    # Stock Splits (optional)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stock_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            ticker TEXT,
            ratio REAL,
            notes TEXT,
            UNIQUE(date, ticker, ratio)
        );
    """)
    conn.commit()
    conn.close()


def insert_new_rows(df, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for _, row in df.iterrows():
        try:
            date_str = row["date"].strftime(
                "%Y-%m-%d") if not pd.isna(row["date"]) else None
            settlement_str = row["settlement_date"].strftime(
                "%Y-%m-%d") if not pd.isna(row["settlement_date"]) else None

            c.execute("""
                INSERT INTO trades (date, stock_code, stock_name, trade_type, quantity,
                                    price_per_share, total_amount, settlement_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date_str,
                row["stock_code"],
                row["stock_name"],
                row["trade_type"],
                int(row["quantity"]),
                float(row["price_per_share"]),
                float(row["total_amount"]),
                settlement_str
            ))
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()


def insert_fundamentals(df, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    for _, row in df.iterrows():
        try:
            date_str = row["date"].strftime(
                "%Y-%m-%d") if not pd.isna(row["date"]) else None

            c.execute("""
                INSERT INTO fundamentals (stock_code, date, pe_ratio, eps)
                VALUES (?, ?, ?, ?)
            """, (
                row["stock_code"],
                date_str,
                float(row["pe_ratio"]) if not pd.isna(row["pe_ratio"]) else None,
                float(row["eps"]) if not pd.isna(row["eps"]) else None
            ))
        except sqlite3.IntegrityError:
            continue

    conn.commit()
    conn.close()


def insert_portfolio_metrics(metrics_dict, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO portfolio_metrics (date, total_value, pe_ratio_avg, pe_ratio_weighted)
            VALUES (?, ?, ?, ?)
        """, (
            metrics_dict.get("date"),
            float(metrics_dict.get("total_value")) if metrics_dict.get("total_value") is not None else None,
            float(metrics_dict.get("pe_ratio_avg")) if metrics_dict.get("pe_ratio_avg") is not None else None,
            float(metrics_dict.get("pe_ratio_weighted")) if metrics_dict.get("pe_ratio_weighted") is not None else None
        ))
    except sqlite3.IntegrityError:
        pass
    conn.commit()
    conn.close()


def clear_db(db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DELETE FROM trades")
    conn.commit()
    conn.close()


def fetch_summary(db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        SELECT trade_type, COUNT(*), SUM(quantity), SUM(total_amount)
        FROM trades
        GROUP BY trade_type
    """)
    rows = c.fetchall()
    conn.close()
    return rows


def get_all_transactions(db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df


def get_fundamentals(stock_code, start_date=None, end_date=None, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    query = "SELECT date, pe_ratio, eps FROM fundamentals WHERE stock_code = ?"
    params = [stock_code]
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_portfolio_metrics(start_date=None, end_date=None, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    query = "SELECT date, total_value, pe_ratio_avg, pe_ratio_weighted FROM portfolio_metrics WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def insert_transactions(df, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for _, row in df.iterrows():
        # Replace '--' with None for numeric columns
        def safe_float(val):
            if val == '--' or pd.isna(val):
                return None
            try:
                return float(val)
            except Exception:
                return None

        def safe_int(val):
            if val == '--' or pd.isna(val):
                return None
            try:
                return int(val)
            except Exception:
                return None

        try:
            c.execute("""
                INSERT INTO transactions (
                    date, stock_code, stock_name, trade_type, quantity,
                    price_per_share, total_amount, settlement_date, fee
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["date"].strftime("%Y-%m-%d") if not pd.isna(row["date"]) else None,
                row["stock_code"],
                row["stock_name"],
                row["trade_type"],
                safe_int(row["quantity"]),
                safe_float(row["price_per_share"]),
                safe_float(row["total_amount"]),
                row["settlement_date"].strftime("%Y-%m-%d") if not pd.isna(row["settlement_date"]) else None,
                safe_float(row["fee"]) if "fee" in row else 0
            ))
        except sqlite3.IntegrityError as e:
            # print(f"IntegrityError: {e} for row: {row.to_dict()}")
            continue
    conn.commit()
    conn.close()


def insert_dividends(df, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for _, row in df.iterrows():
        try:
            c.execute("""
                INSERT INTO dividends (date, ticker, amount, currency, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["date"], row["ticker"], row["amount"], row.get("currency", "JPY"), row.get("notes", "")
            ))
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    conn.close()


def insert_cash_flows(df, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for _, row in df.iterrows():
        try:
            c.execute("""
                INSERT INTO cash_flows (date, type, amount, currency, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (
                row["date"], row["type"], row["amount"], row.get("currency", "JPY"), row.get("notes", "")
            ))
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    conn.close()


def insert_stock_splits(df, db_path="data/portfolio.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    for _, row in df.iterrows():
        try:
            c.execute("""
                INSERT INTO stock_splits (date, ticker, ratio, notes)
                VALUES (?, ?, ?, ?)
            """, (
                row["date"], row["ticker"], row["ratio"], row.get("notes", "")
            ))
        except sqlite3.IntegrityError:
            continue
    conn.commit()
    conn.close()

# Add similar get_* functions for querying each table as needed.