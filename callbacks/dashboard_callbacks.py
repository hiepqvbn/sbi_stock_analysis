# callbacks/dashboard_callbacks.py
from __future__ import annotations

import pandas as pd
from dash import Input, Output, State, callback

from data_handler.db_manager import get_all_transactions
from core.prices import get_price_map, get_price_map_asof
from core.ledger import build_holdings_snapshot, compute_realized_window
from core.portfolio import build_portfolio_value_timeseries, build_stock_perf_timeseries
from viz.dashboard_figures import fig_allocation_pie, fig_top_pnl_bar, fig_asset_growth, fig_stock_perf_area
from viz.dashboard_figures import fig_asset_growth
from core.formatting import yen as _yen, pct as _pct
from core.constants import Columns, PnLKind, PositionMode


@callback(
    Output("dashboard-kpi-market-value", "children"),
    Output("dashboard-kpi-total-pnl", "children"),
    Output("dashboard-kpi-return-pct", "children"),
    Output("dashboard-kpi-split", "children"),
    Output("dashboard-fig-allocation", "figure"),
    Output("dashboard-fig-top-pnl", "figure"),
    Output("dashboard-fig-asset-growth", "figure"),
    Output("dashboard-fig-stock-perf", "figure"),
    Output("dashboard-holdings-table", "data"),
    Input("dashboard-refresh-btn", "n_clicks"),
    Input("dashboard-start-date", "date"),
    Input("dashboard-end-date", "date"),
    Input("dashboard-positions-mode", "value"),
    Input("dashboard-topn", "value"),
    Input("dashboard-alloc-topn", "value"),
    Input("dashboard-initial-capital", "value"),
    Input("dashboard-stock-perf-tab", "value"),
    Input("dashboard-pnl-kind", "value"),
)
def update_dashboard(n_clicks, start_date, end_date, positions_mode, topn, alloc_topn, initial_capital, perf_tab, pnl_kind):
    # 1) load transactions
    tx = get_all_transactions()
    if tx is None or tx.empty:
        empty_fig = {}
        return "¥0", "¥0", "0.00%", "¥0 / ¥0", empty_fig, empty_fig, empty_fig, empty_fig, []

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
        return "¥0", "¥0", "0.00%", "¥0 / ¥0", empty_fig, empty_fig, empty_fig, empty_fig, []

    # 4) KPIs
    market_value = snap[Columns.MARKET_VALUE].sum()
    total_pnl = snap[Columns.TOTAL_PNL].sum()
    realized = snap[Columns.REALIZED].sum()
    unrealized = snap[Columns.UNREALIZED].sum()

    # period realized pnl (start/end window)
    realized_window = window_df[Columns.REALIZED_WINDOW].sum() if not window_df.empty else 0.0
    cost_basis_window = window_df[Columns.COST_BASIS_WINDOW].sum() if not window_df.empty else 0.0

    kpi_market = _yen(market_value)
    # if a window is set, show period realized pnl; otherwise show total pnl
    has_window = bool(start_date or end_date)
    if has_window:
        kpi_total = _yen(realized_window)
        return_pct = (realized_window / cost_basis_window * 100.0) if cost_basis_window > 0 else 0.0
    else:
        # cost_total might be 0 if only closed positions; guard
        total_cost = snap[Columns.COST_TOTAL].sum()
        kpi_total = _yen(total_pnl)
        return_pct = (total_pnl / total_cost * 100.0) if total_cost > 0 else 0.0
    kpi_ret = _pct(return_pct)
    kpi_split = f"{_yen(realized)} / {_yen(unrealized)}"

    # 5) Figures
    fig_alloc = fig_allocation_pie(snap, top_n=int(alloc_topn or 4))
    fig_top = fig_top_pnl_bar(snap, kind=pnl_kind or PnLKind.UNREALIZED, top_n=int(topn or 10))
    asset_df = build_portfolio_value_timeseries(
        tx,
        price_map=price_map,
        as_of_date=end_date,
        initial_capital=float(initial_capital or 0),
    )
    fig_asset = fig_asset_growth(asset_df, initial_capital=float(initial_capital or 0))
    perf_df = build_stock_perf_timeseries(tx, kind=perf_tab or "realized")
    fig_perf = fig_stock_perf_area(perf_df)

    # 6) Table data
    # Keep it light: round numeric for display
    table_df = snap.copy()
    table_df[Columns.AVG_COST] = table_df[Columns.AVG_COST].round(2)
    table_df[Columns.UNREALIZED_PCT] = table_df[Columns.UNREALIZED_PCT].round(2)

    data = table_df.to_dict("records")
    return kpi_market, kpi_total, kpi_ret, kpi_split, fig_alloc, fig_top, fig_asset, fig_perf, data


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
