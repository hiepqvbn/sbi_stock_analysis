# viz/analysis_figures.py
from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from viz.common import ensure_sorted, base_layout
from core.ledger import build_trade_ledger, append_today_snapshot
from core.constants import Columns, TradeType


ONE_DAY = 24 * 60 * 60 * 1000  # in milliseconds

def make_analysis_figures(
    stock_df: pd.DataFrame,
    stock_code: str,
    names_str: str,
    current_price: float,
    add_today: bool = True,
) -> tuple[go.Figure, go.Figure]:
    """
    Returns: (fig_price, fig_perf)
    """

    if stock_df is None or stock_df.empty:
        return go.Figure(), go.Figure()

    df = ensure_sorted(stock_df)
    ledger = build_trade_ledger(df)
    if add_today:
        ledger = append_today_snapshot(ledger, current_price=current_price)

    # -------------------------
    # Figure A: Price & Transactions + Avg cost + Expected price
    # -------------------------
    fig_price = go.Figure()

    if Columns.DATE in ledger.columns:
        x = pd.to_datetime(ledger[Columns.DATE])
    else:
        x = ledger.index

    buys = ledger[ledger[Columns.TRADE_TYPE].astype(str) == TradeType.BUY]
    sells = ledger[ledger[Columns.TRADE_TYPE].astype(str) == TradeType.SELL]

    if not buys.empty:
        fig_price.add_trace(go.Scatter(
            x=pd.to_datetime(
                buys[Columns.DATE]) if Columns.DATE in buys.columns else buys.index,
            y=buys[Columns.PRICE],
            mode="markers",
            name="Buy",
            marker=dict(size=10, symbol="triangle-up"),
        ))

    if not sells.empty:
        fig_price.add_trace(go.Scatter(
            x=pd.to_datetime(
                sells[Columns.DATE]) if Columns.DATE in sells.columns else sells.index,
            y=sells[Columns.PRICE],
            mode="markers",
            name="Sell",
            marker=dict(size=10, symbol="triangle-down"),
        ))

    # avg cost (moving average) line
    fig_price.add_trace(go.Scatter(
        x=x,
        y=ledger[Columns.AVG_COST_AFTER],
        mode="lines",
        name="Avg Cost (moving avg)",
    ))

    # Break-even line
    fig_price.add_trace(go.Scatter(
        x=x,
        y=ledger[Columns.BREAK_EVEN],
        mode="lines",
        name="Break-even Point",
    ))

    # expected/current price horizontal line
    fig_price.add_hline(
        y=current_price,
        line_dash="dash",
        annotation_text="Current Price",
    )

    base_layout(
        fig_price,
        title=f"{names_str} ({stock_code}) Price & Transactions",
        x_title="Date" if Columns.DATE in ledger.columns else "Transaction Index",
        y_title="Price (¥)",
    )

    # -------------------------
    # Figure B: Performance (cash flow + pnl lines)
    # -------------------------
    fig_perf = go.Figure()
    fig_perf.add_hline(y=0, line_dash="dash")

    # cash flow bars (buy negative, sell positive)
    # color is optional; leaving default is fine, but you used red/green before.
    fig_perf.add_trace(go.Bar(
        x=x,
        y=ledger[Columns.CASH_FLOW],
        name="Cash Flow (buy=- / sell=+)",
        width=ONE_DAY * 0.8,
        opacity=0.7,
    ))

    fig_perf.add_trace(go.Scatter(
        x=x, y=ledger[Columns.HOLDING_VALUE],
        mode="lines+markers",
        name="Holding Value (¥)",
    ))

    fig_perf.add_trace(go.Scatter(
        x=x, y=ledger[Columns.REALIZED_CUM],
        mode="lines+markers",
        name="Realized PnL (¥)",
    ))

    fig_perf.add_trace(go.Scatter(
        x=x, y=ledger[Columns.UNREALIZED_PROFIT],
        mode="lines+markers",
        name="Unrealized PnL (¥)",
    ))

    fig_perf.add_trace(go.Scatter(
        x=x, y=ledger[Columns.TOTAL_EQUITY],
        mode="lines+markers",
        name="Total PnL (¥)",
    ))

    fig_perf.update_layout(
        title="Performance (PnL) + Cash Flows",
        xaxis_title="Date" if Columns.DATE in ledger.columns else "Transaction Index",
        yaxis=dict(title="Yen (¥)"),
        barmode="relative",
        template="plotly_white",
        legend_title="Metric",
    )

    return fig_price, fig_perf
