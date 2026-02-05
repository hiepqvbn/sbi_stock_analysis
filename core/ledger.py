from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd
import numpy as np

from core.dates import to_dt, slice_by_date
from core.splits import stocks_split_adjustments
from core.constants import Columns, TradeType, PositionMode
from core.schema import (
    TransactionSchema,
    TradeLedgerInputSchema,
    RealizedWindowInputSchema,
    validate_schema,
)


def _normalize_fee(df: pd.DataFrame) -> pd.Series:
    if Columns.FEE not in df.columns:
        return pd.Series([0] * len(df), index=df.index)
    return pd.to_numeric(df[Columns.FEE], errors="coerce").fillna(0).astype(int)


def _stock_ledger_last_row(df_stock: pd.DataFrame, current_price: float) -> dict:
    g = df_stock.sort_values([Columns.DATE, "id"] if "id" in df_stock.columns else [Columns.DATE]).copy()
    g["fee"] = _normalize_fee(g)

    qty = 0
    cost_total = 0
    realized = 0

    for _, r in g.iterrows():
        t = str(r[Columns.TRADE_TYPE])
        sh = int(round(float(r[Columns.QUANTITY])))
        amount = int(round(float(r[Columns.TOTAL_AMOUNT])))
        fee = int(r["fee"])

        if t == TradeType.BUY:
            qty += sh
            cost_total += (amount + fee)
        elif t == TradeType.SELL:
            if sh > qty:
                raise ValueError(f"Selling more than held: sell {sh}, held {qty}")

            proceeds = amount - fee
            avg_cost = cost_total / qty if qty > 0 else 0.0
            cost_basis = avg_cost * sh

            realized_step = proceeds - cost_basis
            realized += realized_step

            cost_total -= cost_basis
            qty -= sh

            if qty == 0:
                cost_total = 0
        else:
            pass

    avg_cost_after = (cost_total / qty) if qty > 0 else 0.0
    market_value = int(round(current_price * qty))
    unrealized = market_value - int(round(cost_total))
    total_pnl = int(round(realized)) + int(round(unrealized))

    return {
        Columns.QTY: qty,
        Columns.COST_TOTAL: int(round(cost_total)),
        Columns.AVG_COST: float(avg_cost_after),
        Columns.CURRENT_PRICE: float(current_price),
        Columns.MARKET_VALUE: market_value,
        Columns.REALIZED: int(round(realized)),
        Columns.UNREALIZED: int(round(unrealized)),
        Columns.TOTAL_PNL: int(round(total_pnl)),
        Columns.UNREALIZED_PCT: (unrealized / cost_total * 100.0) if cost_total > 0 else 0.0,
    }


def build_holdings_snapshot(
    transactions_df: pd.DataFrame,
    price_map: Dict[str, float],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    positions_mode: str = PositionMode.HOLDING,
) -> pd.DataFrame:
    if transactions_df is None or transactions_df.empty:
        return pd.DataFrame(columns=[
            Columns.STOCK_CODE, Columns.STOCK_NAME, Columns.QTY, Columns.AVG_COST, Columns.COST_TOTAL,
            Columns.CURRENT_PRICE, Columns.MARKET_VALUE, Columns.UNREALIZED, Columns.REALIZED,
            Columns.TOTAL_PNL, Columns.UNREALIZED_PCT
        ])

    validate_schema(transactions_df, TransactionSchema.required, name="transactions_df", raise_on_error=True)

    df = transactions_df.copy()
    df = slice_by_date(df, start_date, end_date, date_col=Columns.DATE)

    df = stocks_split_adjustments(df)

    if df.empty:
        return pd.DataFrame(columns=[
            Columns.STOCK_CODE, Columns.STOCK_NAME, Columns.QTY, Columns.AVG_COST, Columns.COST_TOTAL,
            Columns.CURRENT_PRICE, Columns.MARKET_VALUE, Columns.UNREALIZED, Columns.REALIZED,
            Columns.TOTAL_PNL, Columns.UNREALIZED_PCT
        ])

    df[Columns.DATE] = to_dt(df[Columns.DATE])
    df[Columns.STOCK_CODE] = df[Columns.STOCK_CODE].astype(str)

    rows = []
    for code, g in df.groupby(Columns.STOCK_CODE, sort=False):
        if code not in price_map:
            continue

        last = _stock_ledger_last_row(g, current_price=price_map[code])

        name = g[Columns.STOCK_NAME].iloc[0] if Columns.STOCK_NAME in g.columns and len(g) else ""
        rows.append({
            Columns.STOCK_CODE: code,
            Columns.STOCK_NAME: name,
            **last,
        })

    snap = pd.DataFrame(rows)
    if snap.empty:
        return snap

    if positions_mode == PositionMode.HOLDING:
        snap = snap[snap[Columns.QTY] > 0].copy()

    snap = snap.sort_values("market_value", ascending=False).reset_index(drop=True)
    return snap


def compute_realized_window(
    transactions_df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    if transactions_df is None or transactions_df.empty:
        return pd.DataFrame(columns=[Columns.STOCK_CODE, Columns.REALIZED_WINDOW, Columns.COST_BASIS_WINDOW])

    validate_schema(transactions_df, RealizedWindowInputSchema.required, name="realized_window_input", raise_on_error=True)

    df = transactions_df.copy()
    df[Columns.DATE] = to_dt(df[Columns.DATE])
    df[Columns.STOCK_CODE] = df[Columns.STOCK_CODE].astype(str)

    start_dt = to_dt(start_date) if start_date else None
    end_dt = to_dt(end_date) if end_date else None

    rows = []
    for code, g in df.groupby(Columns.STOCK_CODE, sort=False):
        g = g.sort_values([Columns.DATE, "id"] if "id" in g.columns else [Columns.DATE]).copy()
        g["fee"] = _normalize_fee(g)

        qty = 0
        cost_total = 0.0
        realized_window = 0.0
        cost_basis_window = 0.0

        for _, r in g.iterrows():
            t = str(r[Columns.TRADE_TYPE])
            sh = int(round(float(r[Columns.QUANTITY])))
            amount = float(r[Columns.TOTAL_AMOUNT])
            fee = float(r["fee"])
            d = r["date"]

            if t == TradeType.BUY:
                qty += sh
                cost_total += (amount + fee)
            elif t == TradeType.SELL:
                if qty <= 0:
                    continue
                proceeds = amount - fee
                avg_cost = (cost_total / qty) if qty > 0 else 0.0
                cost_basis = avg_cost * sh

                in_window = True
                if start_dt is not None and d < start_dt:
                    in_window = False
                if end_dt is not None and d > end_dt:
                    in_window = False
                if in_window:
                    realized_window += (proceeds - cost_basis)
                    cost_basis_window += cost_basis

                cost_total -= cost_basis
                qty -= sh
                if qty == 0:
                    cost_total = 0.0

        rows.append({
            Columns.STOCK_CODE: code,
            Columns.REALIZED_WINDOW: int(round(realized_window)),
            Columns.COST_BASIS_WINDOW: float(cost_basis_window),
        })

    return pd.DataFrame(rows)


def compute_ledger_decimal(df_symbol: pd.DataFrame) -> pd.DataFrame:
    from decimal import Decimal, getcontext

    getcontext().prec = 28
    df = df_symbol.sort_values([Columns.DATE, "id"]).copy()

    pos_qty = Decimal("0")
    cost_total = Decimal("0")
    realized_cum = Decimal("0")

    ledger_rows = []

    for _, r in df.iterrows():
        t = r[Columns.TRADE_TYPE]
        qty = Decimal(str(int(r[Columns.QUANTITY])))
        price = Decimal(str(int(r[Columns.PRICE_PER_SHARE])))
        fee = Decimal(str(int(r[Columns.FEE]))) if r[Columns.FEE] not in (None, "", "None") else Decimal("0")

        realized_delta = Decimal("0")

        if t == "Buy":
            buy_total = Decimal(str(int(r[Columns.TOTAL_AMOUNT])))
            cost_total += buy_total + fee
            pos_qty += qty

        elif t == "Sell":
            sell_total = Decimal(str(int(r[Columns.TOTAL_AMOUNT])))
            proceeds = sell_total - fee

            if pos_qty == 0:
                raise ValueError("Sell while holding 0 shares")

            avg_cost = cost_total / pos_qty
            cost_basis = avg_cost * qty

            realized_delta = proceeds - cost_basis
            realized_cum += realized_delta

            cost_total -= cost_basis
            pos_qty -= qty

            if pos_qty == 0:
                cost_total = Decimal("0")

        ledger_rows.append({
            Columns.DATE: r[Columns.DATE],
            Columns.TRADE_TYPE: t,
            Columns.QTY: int(qty),
            Columns.POS_QTY_AFTER: int(pos_qty),
            "cost_total_after": float(cost_total),
            Columns.AVG_COST_AFTER: float(cost_total / pos_qty) if pos_qty != 0 else 0.0,
            Columns.REALIZED_DELTA: float(realized_delta),
            Columns.REALIZED_CUM: float(realized_cum),
        })

    return pd.DataFrame(ledger_rows)


def build_trade_ledger(df: pd.DataFrame) -> pd.DataFrame:
    validate_schema(df, TradeLedgerInputSchema.required, name="trade_ledger_input", raise_on_error=True)
    pos_qty = 0.0
    avg_cost = 0.0
    realized_cum = 0.0
    cash_flow = 0.0

    total_buy_amount = 0.0
    total_sell_amount = 0.0

    unrealized_profit = 0.0
    total_equity = 0.0
    holding_value = 0.0

    break_even_point_price = 0.0

    ledger_rows = []

    for _, row in df.iterrows():
        trade_type = row[Columns.TRADE_TYPE]
        qty = row[Columns.QUANTITY]
        price = row[Columns.PRICE_PER_SHARE]
        fee = row[Columns.FEE] if row[Columns.FEE] else 0.0

        realized_delta = 0.0

        if trade_type == TradeType.BUY:
            total_cost = pos_qty * avg_cost + qty * price + fee
            pos_qty += qty
            avg_cost = total_cost / pos_qty
            cash_flow = -(qty * price + fee)
            total_buy_amount += cash_flow * (-1)

        elif trade_type == TradeType.SELL:
            cost_basis = qty * avg_cost
            proceeds = qty * price - fee
            realized_delta = proceeds - cost_basis

            realized_cum += realized_delta
            pos_qty -= qty

            cash_flow = proceeds
            total_sell_amount += cash_flow

            if pos_qty == 0:
                avg_cost = 0.0
        holding_value = pos_qty * price
        unrealized_profit = holding_value - (pos_qty * avg_cost)
        total_equity = realized_cum + unrealized_profit

        break_even_point_price = (total_buy_amount - total_sell_amount) / pos_qty \
            if pos_qty > 0 else 0
        break_even_point_price = break_even_point_price if break_even_point_price > 0 else 0

        ledger_rows.append({
            Columns.DATE: row[Columns.DATE],
            Columns.TRADE_TYPE: trade_type,
            Columns.QUANTITY: qty,
            Columns.PRICE: price,
            Columns.POS_QTY_AFTER: pos_qty,
            Columns.AVG_COST_AFTER: avg_cost,
            Columns.REALIZED_DELTA: realized_delta,
            Columns.REALIZED_CUM: realized_cum,
            Columns.CASH_FLOW: cash_flow,
            Columns.UNREALIZED_PROFIT: unrealized_profit,
            Columns.TOTAL_EQUITY: total_equity,
            Columns.HOLDING_VALUE: holding_value,
            Columns.BREAK_EVEN: break_even_point_price,
        })

    return pd.DataFrame(ledger_rows)


def append_today_snapshot(df: pd.DataFrame, current_price: float) -> pd.DataFrame:
    if Columns.DATE not in df.columns or df.empty:
        return df

    today = pd.Timestamp.today().normalize()
    last_date = pd.to_datetime(df[Columns.DATE].max())

    if today <= last_date:
        return df

    last = df.iloc[-1].copy()
    last[Columns.DATE] = today
    qty = float(last[Columns.POS_QTY_AFTER]) if Columns.POS_QTY_AFTER in last else 0.0
    realized = float(last[Columns.REALIZED_CUM]) if Columns.REALIZED_CUM in last else 0.0
    avg_cost = float(last[Columns.AVG_COST_AFTER]) if Columns.AVG_COST_AFTER in last else 0.0

    last[Columns.HOLDING_VALUE] = qty * float(current_price)
    last[Columns.UNREALIZED_PROFIT] = last[Columns.HOLDING_VALUE] - (qty * avg_cost)
    last[Columns.TOTAL_EQUITY] = realized + last[Columns.UNREALIZED_PROFIT]

    last[Columns.TRADE_TYPE] = TradeType.TODAY
    last[Columns.QUANTITY] = 0
    last[Columns.PRICE] = 0
    last[Columns.CASH_FLOW] = 0
    last[Columns.REALIZED_DELTA] = 0

    return pd.concat([df, pd.DataFrame([last])], ignore_index=True)
