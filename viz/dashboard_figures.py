# viz/dashboard_figures.py
from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from core.constants import Columns, UI
from viz.common import base_layout

def fig_allocation_pie(snapshot_df: pd.DataFrame, top_n: int = 4) -> go.Figure:
    fig = go.Figure()
    if snapshot_df is None or snapshot_df.empty:
        fig.update_layout(template="plotly_white", title="Allocation (empty)")
        return fig

    d = snapshot_df.copy()
    d["label"] = d.apply(lambda r: f'{r[Columns.STOCK_CODE]} {r[Columns.STOCK_NAME]}', axis=1)
    d = d.sort_values(Columns.MARKET_VALUE, ascending=False)

    top = d.head(top_n)
    other = d.iloc[top_n:]

    labels = top["label"].tolist()
    values = top[Columns.MARKET_VALUE].tolist()
    if not other.empty:
        labels.append(f"Other ({len(other)} ticks)")
        values.append(other[Columns.MARKET_VALUE].sum())

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        hovertemplate="%{label}<br>Value: ¥%{value:,}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=30, b=10))
    return fig


def fig_top_pnl_bar(snapshot_df: pd.DataFrame, kind: str = "unrealized", top_n: int = 10) -> go.Figure:
    """
    kind in {"unrealized","realized","total"}
    """
    fig = go.Figure()
    if snapshot_df is None or snapshot_df.empty:
        fig.update_layout(template="plotly_white", title="Top PnL (empty)")
        return fig

    col = {"unrealized": Columns.UNREALIZED, "realized": Columns.REALIZED, "total": Columns.TOTAL_PNL}.get(
        kind, Columns.UNREALIZED
    )
    d = snapshot_df.copy()

    d["label"] = d.apply(lambda r: f'{r[Columns.STOCK_CODE]} {r[Columns.STOCK_NAME]}', axis=1)

    # take top absolute movers (more useful than just biggest positive)
    d = d.reindex(d[col].abs().sort_values(ascending=False).head(top_n).index)
    d = d.sort_values(col, ascending=True)  # for horizontal bar nice ordering

    fig.add_trace(go.Bar(
        x=d[col],
        y=d["label"],
        orientation="h",
        hovertemplate="%{y}<br>PnL: ¥%{x:,}<extra></extra>",
    ))

    fig.add_vline(x=0, line_dash="dash")
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="Yen (¥)",
        yaxis_title="",
    )
    return fig


def fig_asset_growth(asset_df: pd.DataFrame, initial_capital: float | None = None) -> go.Figure:
    fig = go.Figure()
    if asset_df is None or asset_df.empty:
        fig.update_layout(template="plotly_white", title=UI.ASSET_GROWTH_TITLE)
        return fig

    fig.add_trace(go.Scatter(
        x=pd.to_datetime(asset_df[Columns.DATE]),
        y=asset_df[Columns.MARKET_VALUE],
        mode="lines+markers",
        name="Holdings Value",
        hovertemplate="%{x|%Y-%m-%d}<br>Value: ¥%{y:,.0f}<extra></extra>",
    ))

    if Columns.NET_VALUE in asset_df.columns:
        fig.add_trace(go.Scatter(
            x=pd.to_datetime(asset_df[Columns.DATE]),
            y=asset_df[Columns.NET_VALUE],
            mode="lines+markers",
            name="Net Value",
            hovertemplate="%{x|%Y-%m-%d}<br>Net: ¥%{y:,.0f}<extra></extra>",
        ))

    if initial_capital is not None:
        fig.add_hline(
            y=float(initial_capital),
            line_dash="dash",
            annotation_text="Initial Capital",
        )

    base_layout(
        fig,
        title=UI.ASSET_GROWTH_TITLE,
        x_title="Date",
        y_title="Yen (¥)",
    )
    return fig


def fig_stock_perf_area(perf_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if perf_df is None or perf_df.empty:
        fig.update_layout(template="plotly_white", title=UI.STOCK_PERF_TITLE)
        return fig

    x = pd.to_datetime(perf_df[Columns.DATE])
    for col in perf_df.columns:
        if col == Columns.DATE:
            continue
        fig.add_trace(go.Scatter(
            x=x,
            y=perf_df[col],
            mode="lines",
            stackgroup="one",
            name=str(col),
            hovertemplate="%{x|%Y-%m-%d}<br>¥%{y:,.0f}<extra></extra>",
        ))

    fig.update_layout(
        template="plotly_white",
        title=UI.STOCK_PERF_TITLE,
        xaxis_title="Date",
        yaxis_title="Yen (¥)",
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig
