from __future__ import annotations

from typing import Any, Dict, Union
import pandas as pd

from core.ledger import build_trade_ledger
from core.constants import Columns


def analyze_stock_performance(
    stock_df: pd.DataFrame,
    current_price: float,
) -> Dict[str, Union[float, int, Dict[str, float], Any]]:
    stock_code = stock_df[Columns.STOCK_CODE].iloc[0]
    stock_names = stock_df[Columns.STOCK_NAME].unique()
    names_str = ", ".join(stock_names)

    ledger_df = build_trade_ledger(stock_df)

    buy_mask = stock_df[Columns.TRADE_TYPE].str.lower().str.contains("buy")
    sell_mask = stock_df[Columns.TRADE_TYPE].str.lower().str.contains("sell")

    total_buy_qty = stock_df.loc[buy_mask, Columns.QUANTITY].sum()
    total_buy_amount = stock_df.loc[buy_mask, Columns.TOTAL_AMOUNT].sum()
    avg_buy_price = (total_buy_amount / total_buy_qty) if total_buy_qty > 0 else 0

    total_sell_qty = stock_df.loc[sell_mask, Columns.QUANTITY].sum()
    total_sell_amount = stock_df.loc[sell_mask, Columns.TOTAL_AMOUNT].sum()
    avg_sell_price = (total_sell_amount / total_sell_qty) if total_sell_qty > 0 else 0

    realized_profit = ledger_df.iloc[-1][Columns.REALIZED_CUM]
    realized_profit_pct = (
        realized_profit / (total_sell_qty * avg_buy_price) * 100
    ) if total_sell_qty > 0 else 0

    holding_qty = total_buy_qty - total_sell_qty
    last_avg_buy_price = ledger_df.iloc[-1][Columns.AVG_COST_AFTER]
    holding_cost = holding_qty * last_avg_buy_price
    holding_value = holding_qty * current_price

    unrealized_profit = holding_value - holding_cost
    unrealized_profit_pct = (unrealized_profit / holding_cost * 100) if holding_cost > 0 else 0

    total_profit = total_sell_amount + holding_value - total_buy_amount
    total_profit_pct = ((total_profit / (total_buy_qty * avg_buy_price)) * 100) if total_buy_qty > 0 else 0

    break_even_point_price = (total_buy_amount - total_sell_amount) / holding_qty if holding_qty > 0 else 0
    break_even_point_price = break_even_point_price if break_even_point_price > 0 else 0

    return {
        "stock_code": stock_code,
        "stock_names": names_str,
        "total_buy_qty": int(total_buy_qty),
        "total_buy_amount": float(total_buy_amount),
        "avg_buy_price": float(avg_buy_price),
        "avg_sell_price": float(avg_sell_price),
        "total_sell_qty": int(total_sell_qty),
        "total_sell_amount": float(total_sell_amount),
        "realized_profit": float(realized_profit),
        "realized_profit_pct": float(realized_profit_pct),
        "unrealized_profit": float(unrealized_profit),
        "unrealized_profit_pct": float(unrealized_profit_pct),
        "total_profit": float(total_profit),
        "total_profit_pct": float(total_profit_pct),
        "holding_qty": int(holding_qty),
        "holding_value": float(holding_value),
        "break_even_point_price": float(break_even_point_price),
    }
