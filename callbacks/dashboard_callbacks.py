# callbacks/dashboard_callbacks.py
from __future__ import annotations

import pandas as pd
from dash import Input, Output, State, callback

from data_handler.db_manager import get_all_transactions, get_cash_flows
from core.prices import get_price_map, get_price_map_asof
from core.ledger import build_holdings_snapshot, compute_realized_window
from core.portfolio import (
    build_portfolio_value_timeseries,
    build_stock_perf_timeseries,
    compute_account_growth,
    compute_irr,
    compute_twr,
)
from core.benchmarks import get_benchmark_series
from viz.dashboard_figures import fig_allocation_pie, fig_top_pnl_bar, fig_asset_growth, fig_stock_perf_area
from viz.dashboard_figures import fig_asset_growth
from core.formatting import yen as _yen, pct as _pct
from core.constants import Columns, PnLKind, PositionMode, TradeType


@callback(
    Output("dashboard-kpi-market-value", "children"),
    Output("dashboard-kpi-net-value", "children"),
    Output("dashboard-kpi-cash", "children"),
    Output("dashboard-kpi-total-pnl", "children"),
    Output("dashboard-kpi-realized", "children"),
    Output("dashboard-kpi-growth", "children"),
    Output("dashboard-kpi-irr", "children"),
    Output("dashboard-kpi-twr", "children"),
    Output("dashboard-fig-allocation", "figure"),
    Output("dashboard-fig-top-pnl", "figure"),
    Output("dashboard-fig-asset-growth", "figure"),
    Output("dashboard-fig-stock-perf", "figure"),
    Output("dashboard-holdings-table", "data"),
    Output("dashboard-benchmark-container", "style"),
    Output("dashboard-net-bar-fill", "style"),
    Output("dashboard-net-bar-label", "children"),
    Output("dashboard-net-icon", "style"),
    Output("dashboard-net-icon", "children"),
    Output("dashboard-goal-icon", "children"),
    Output("dashboard-net-deposit-value", "children"),
    Output("dashboard-tax-value", "children"),
    Output("dashboard-dividend-value", "children"),
    Input("dashboard-refresh-btn", "n_clicks"),
    Input("dashboard-start-date", "date"),
    Input("dashboard-end-date", "date"),
    Input("dashboard-positions-mode", "value"),
    Input("dashboard-topn", "value"),
    Input("dashboard-alloc-topn", "value"),
    Input("dashboard-target-net", "value"),
    Input("dashboard-net-icon-input", "value"),
    Input("dashboard-goal-icon-input", "value"),
    Input("dashboard-asset-view", "value"),
    Input("dashboard-benchmark", "value"),
    Input("dashboard-stock-perf-tab", "value"),
    Input("dashboard-pnl-kind", "value"),
)
def update_dashboard(
    n_clicks,
    start_date,
    end_date,
    positions_mode,
    topn,
    alloc_topn,
    target_net,
    net_icon,
    goal_icon,
    asset_view,
    benchmark_ticker,
    perf_tab,
    pnl_kind,
):
    cash_flows = get_cash_flows()
    net_deposit_total = 0.0
    tax_total = 0.0
    dividend_total = 0.0
    if cash_flows is not None and not cash_flows.empty:
        cf = cash_flows.copy()
        cf[Columns.DATE] = pd.to_datetime(cf[Columns.DATE], errors="coerce")
        cf["amount"] = pd.to_numeric(cf["amount"], errors="coerce").fillna(0.0)
        cf["type"] = cf["type"].astype(str)
        net_deposit_total = cf[cf["type"].isin(["Deposit", "Withdrawal"])]["amount"].sum()
        tax_total = cf[cf["type"] == "Tax"]["amount"].sum()
        dividend_total = cf[cf["type"] == "Dividend"]["amount"].sum()
    # 1) load transactions
    tx = get_all_transactions()
    if tx is None or tx.empty:
        empty_fig = {}
        return (
            "¥0",
            "¥0",
            "¥0",
            "¥0",
            "¥0",
            "0.00%",
            "0.00%",
            "0.00% / 0.00%",
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            [],
            {"display": "none"},
            {"height": "100%", "width": "0%", "background": "#2b6cb0", "borderRadius": "999px"},
            "Net: ¥0 / Target: ¥0 (0.00%)",
            {"position": "absolute", "top": "-12px", "left": "0%", "transform": "translateX(-50%)", "fontSize": "18px"},
            net_icon or "📍",
            goal_icon or "🏁",
            _yen(net_deposit_total),
            _yen(tax_total),
            _yen(dividend_total),
        )

    # 2) decide which stock codes to fetch prices for
    codes = sorted(tx[Columns.STOCK_CODE].astype(str).unique().tolist())
    if end_date:
        price_map = get_price_map_asof(codes, end_date)
    else:
        price_map = get_price_map(codes)  # uses yfinance

    # 3) build snapshot (date slicing here affects what trades are considered)
    snap = build_holdings_snapshot(
        transactions_df=tx,
        price_map=price_map,
        start_date=None,
        end_date=None,
        positions_mode=positions_mode or PositionMode.HOLDING,
    )

    # realized PnL within selected window (uses full history for cost basis)
    window_df = compute_realized_window(tx, start_date=start_date, end_date=end_date)

    if snap.empty:
        empty_fig = {}
        return (
            "¥0",
            "¥0",
            "¥0",
            "¥0",
            "¥0",
            "0.00%",
            "0.00%",
            "0.00% / 0.00%",
            empty_fig,
            empty_fig,
            empty_fig,
            empty_fig,
            [],
            {"display": "none"},
            {"height": "100%", "width": "0%", "background": "#2b6cb0", "borderRadius": "999px"},
            "Net: ¥0 / Target: ¥0 (0.00%)",
            {"position": "absolute", "top": "-12px", "left": "0%", "transform": "translateX(-50%)", "fontSize": "18px"},
            net_icon or "📍",
            goal_icon or "🏁",
            _yen(net_deposit_total),
            _yen(tax_total),
            _yen(dividend_total),
        )

    # 4) KPIs
    market_value = snap[Columns.MARKET_VALUE].sum()
    total_pnl = snap[Columns.TOTAL_PNL].sum()
    realized = snap[Columns.REALIZED].sum()
    unrealized = snap[Columns.UNREALIZED].sum()

    # period realized pnl (start/end window)
    realized_window = window_df[Columns.REALIZED_WINDOW].sum() if not window_df.empty else 0.0
    cost_basis_window = window_df[Columns.COST_BASIS_WINDOW].sum() if not window_df.empty else 0.0

    kpi_market = _yen(market_value)
    kpi_net_value = "¥0"
    kpi_cash = "¥0"
    # if a window is set, show period realized pnl; otherwise show total pnl
    has_window = bool(start_date or end_date)
    if has_window:
        kpi_total = _yen(realized_window)
    else:
        kpi_total = _yen(total_pnl)
    kpi_realized = _yen(realized)

    # 5) Figures
    fig_alloc = fig_allocation_pie(snap, top_n=int(alloc_topn or 4))
    fig_top = fig_top_pnl_bar(snap, kind=pnl_kind or PnLKind.UNREALIZED, top_n=int(topn or 10))
    asset_df = build_portfolio_value_timeseries(
        tx,
        price_map=price_map,
        as_of_date=end_date,
        cash_flows_df=cash_flows,
    )
    bench_df = None
    if asset_view == "return" and benchmark_ticker:
        bench_start = start_date
        bench_end = end_date
        if (not bench_start or not bench_end) and asset_df is not None and not asset_df.empty:
            bench_start = pd.to_datetime(asset_df[Columns.DATE]).min().strftime("%Y-%m-%d")
            bench_end = pd.to_datetime(asset_df[Columns.DATE]).max().strftime("%Y-%m-%d")
        print(f"Fetching benchmark {benchmark_ticker} from {bench_start} to {bench_end}")
        s = get_benchmark_series(benchmark_ticker, bench_start, bench_end)
        print(f"Benchmark series data points: {len(s)}")
        if not s.empty:
            s = s.sort_index()

            cf = cash_flows.copy() if cash_flows is not None else pd.DataFrame()
            if not cf.empty:
                cf = cf[cf["type"].isin(["Deposit", "Withdrawal"])].copy()
                cf[Columns.DATE] = pd.to_datetime(cf[Columns.DATE], errors="coerce")
                if end_date:
                    as_of_dt = pd.to_datetime(end_date, errors="coerce")
                    if not pd.isna(as_of_dt):
                        cf = cf[cf[Columns.DATE] <= as_of_dt]
                cf["amount"] = pd.to_numeric(cf["amount"], errors="coerce").fillna(0.0)
                cash_flow_by_date = cf.groupby(Columns.DATE)["amount"].sum()
                price_series = s.reindex(s.index.union(cash_flow_by_date.index)).sort_index().ffill().bfill()

                shares = 0.0
                net_dep = 0.0
                rows = []
                for dt, price in price_series.items():
                    flow = float(cash_flow_by_date.get(dt, 0.0))
                    if price and price != 0:
                        shares += flow / float(price)
                    net_dep += flow
                    value = shares * float(price)
                    ret = (value - net_dep) / net_dep * 100.0 if net_dep != 0 else 0.0
                    rows.append((dt, ret))

                bench_df = pd.DataFrame(
                    {
                        Columns.DATE: [r[0] for r in rows],
                        "benchmark_return_pct": [r[1] for r in rows],
                        "label": [f"{benchmark_ticker} (cash-flow matched)"] * len(rows),
                    }
                )
            else:
                first = float(s.iloc[0]) if len(s) else None
                if first and first != 0:
                    ret = (s / first - 1.0) * 100.0
                    bench_df = pd.DataFrame(
                        {
                            Columns.DATE: ret.index,
                            "benchmark_return_pct": ret.values,
                            "label": [benchmark_ticker] * len(ret),
                        }
                    )
    # account growth + capital return
    net_value = asset_df[Columns.NET_VALUE].iloc[-1] if Columns.NET_VALUE in asset_df.columns and not asset_df.empty else 0.0
    account_growth = compute_account_growth(float(net_value), float(net_deposit_total or 0))
    kpi_growth = _pct(account_growth)
    kpi_net_value = _yen(net_value)
    kpi_cash = _yen(net_value - market_value)

    irr = compute_irr(tx, ending_value=float(net_value), net_deposit=float(net_deposit_total or 0), cash_flows_df=cash_flows, as_of_date=end_date)
    twr = compute_twr(tx, price_map=price_map, net_deposit=float(net_deposit_total or 0), cash_flows_df=cash_flows, as_of_date=end_date)
    kpi_irr = _pct(irr)
    # annualize TWR based on span of transactions
    ann_twr = 0.0
    if tx is not None and not tx.empty:
        start_dt = pd.to_datetime(tx[Columns.DATE].min())
        end_dt = pd.to_datetime(tx[Columns.DATE].max())
        years = max((end_dt - start_dt).days / 365.0, 0.0)
        if years > 0:
            ann_twr = ((1.0 + (twr / 100.0)) ** (1.0 / years) - 1.0) * 100.0
    kpi_twr = f"{_pct(twr)} / {_pct(ann_twr)}"

    fig_asset = fig_asset_growth(
        asset_df,
        view_mode=asset_view or "value",
        benchmark_df=bench_df,
        twr_pct=float(twr),
    )
    perf_df = build_stock_perf_timeseries(tx, kind=perf_tab or "realized")
    fig_perf = fig_stock_perf_area(perf_df)

    # 6) Table data
    # Keep it light: round numeric for display
    table_df = snap.copy()
    table_df[Columns.AVG_COST] = table_df[Columns.AVG_COST].round(2)
    table_df[Columns.UNREALIZED_PCT] = table_df[Columns.UNREALIZED_PCT].round(2)

    data = table_df.to_dict("records")
    bench_style = {"display": "block"} if (asset_view == "return") else {"display": "none"}
    # net vs target progress bar
    target_val = float(target_net or 0)
    net_val = float(net_value or 0)
    pct = (net_val / target_val * 100.0) if target_val > 0 else 0.0
    pct_clamped = max(0.0, min(pct, 100.0))
    bar_style = {
        "height": "100%",
        "width": f"{pct_clamped:.2f}%",
        "background": "#2b6cb0",
        "borderRadius": "999px",
    }
    net_icon_style = {
        "position": "absolute",
        "top": "-18px",
        "left": f"{pct_clamped:.2f}%",
        "transform": "translateX(-50%)",
        "fontSize": "18px",
        "zIndex": 2,
        "pointerEvents": "none",
    }
    label = f"Net: ¥{int(net_val):,} / Target: ¥{int(target_val):,} ({pct:.2f}%)"

    return (
        kpi_market,
        kpi_net_value,
        kpi_cash,
        kpi_total,
        kpi_realized,
        kpi_growth,
        kpi_irr,
        kpi_twr,
        fig_alloc,
        fig_top,
        fig_asset,
        fig_perf,
        data,
        bench_style,
        bar_style,
        label,
        net_icon_style,
        net_icon or "📍",
        goal_icon or "🏁",
        _yen(net_deposit_total),
        _yen(tax_total),
        _yen(dividend_total),
    )


# import base64
# import io
# import pandas as pd
# from dash import Input, Output, State, callback, html
# from data_handler.csv_parser import clean_sbi_csv
# from data_handler.db_manager import insert_new_rows, fetch_summary

# from data_handler.db_manager import get_all_transactions


# @callback(
#     Output('upload-status', 'children'),
#     Input('upload-data', 'contents'),
#     State('upload-data', 'filename')
# )
# def handle_uploaded_file(contents, filename):    
#     if contents is None:
#         return ""

#     # Ensure both are lists
#     if not isinstance(contents, list):
#         contents = [contents]
#     if not isinstance(filename, list):
#         filename = [filename]

#     messages = []
#     for content, fname in zip(contents, filename):
#         try:
#             # Decode and read CSV
#             print(f"Processing file: {fname}")
#             print(f"Contents: {content[:100]}...")
#             content_type, content_string = content.split(',')
#             decoded = base64.b64decode(content_string)
#             file_buffer = io.StringIO(decoded.decode('shift_jis'))

#             # Clean and insert
#             df = clean_sbi_csv(file_buffer)
#             insert_new_rows(df)

#             messages.append(
#                 f"✅ Uploaded and inserted data from: {fname} (new rows only)")
#         except Exception as e:
#             messages.append(f"❌ Error processing file {fname}: {e}")

#     return html.Ul([html.Li(msg) for msg in messages])


# @callback(
#     Output('data-table', 'columns'),
#     Output('data-table', 'data'),
#     Input('upload-status', 'children'),
# )
# def update_data_table(_):
#     df = get_all_transactions()
#     columns = [{"name": i, "id": i} for i in df.columns]
#     data = df.to_dict('records')
    
#     return columns, data


# # @callback(
# #     Output('data-summary', 'children'),
# #     Input('upload-data', 'contents')
# # )
# # def update_summary_after_upload(_):
# #     summary = fetch_summary()
# #     return html.Ul([
# #         html.Li(
# #             f"{row[0]} - {row[1]} trades, total qty {row[2]}, total amount ¥{row[3]:,.0f}")
# #         for row in summary
# #     ])


# # @callback(
# #     Output('portfolio-value', 'figure'),
# #     Input('date-range', 'start_date'),
# #     Input('date-range', 'end_date'),
# #     Input('stock-selector', 'value')
# # )
# # def update_portfolio_value(start_date, end_date, stock_list):
# #     df = get_all_transactions()
# #     # Filter and calculate portfolio value
# #     ...
# #     return fig
