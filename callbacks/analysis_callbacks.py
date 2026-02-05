from dash import Input, Output, State, callback, html
from dash.dash_table import DataTable
from data_handler.db_manager import get_all_transactions
from core.dates import slice_df_by_date_range
from core.analysis import analyze_stock_performance
from core.splits import record_stock_split_adjustments
from core.prices import get_stock_current_price
from core.constants import Columns, UI
from viz.analysis_figures import make_analysis_figures


@callback(
    Output("analysis-stock-dropdown", "options"),
    Input("url", "pathname"),
)
def update_stock_dropdown_options(_):
    df = get_all_transactions()
    # Get latest name for each stock_code
    latest_names = df.sort_values(Columns.DATE).groupby(
        Columns.STOCK_CODE)[Columns.STOCK_NAME].last()
    options = [
        {"label": f"{name} ({code})", "value": code}
        for code, name in latest_names.items()
    ]
    return options


@callback(
    Output("stock-metrics", "children"),
    Output("stock-price-graph", "figure"),
    Output("stock-indicators-graph", "figure"),
    Output("analysis-stock-table", "children"),
    Input("analysis-stock-dropdown", "value"),
    Input("expected-price-input", "value"),
    Input("analysis-start-date", "date"),
    Input("analysis-end-date", "date"),
)
def update_analysis(stock_code, expected_price, start_date, end_date):
    if not stock_code:
        return UI.ANALYSIS_SELECT_STOCK_MSG, {}, {}, None

    df = get_all_transactions()
    stock_df = record_stock_split_adjustments(df, stock_code)
    
    stock_df = slice_df_by_date_range(
        stock_df,
        start_date=start_date,
        end_date=end_date,
    )
    
    stock_names = stock_df[Columns.STOCK_NAME].unique()
    names_str = ", ".join(stock_names)

    if stock_df.empty:
        return UI.ANALYSIS_NO_DATA_MSG, {}, {}, None
    current_price = get_stock_current_price(stock_code)
    current_price = current_price if current_price is not None else (
        stock_df[Columns.PRICE_PER_SHARE].iloc[-1] if Columns.PRICE_PER_SHARE in stock_df.columns else 0
    )
    # Use expected price if provided, else use latest price_per_share
    current_price = expected_price if expected_price is not None else current_price

    perf = analyze_stock_performance(
        stock_df, current_price)

    metrics = html.Div([
        html.Div(f"Stock code: {stock_code}"),
        html.Div(
            f"Names used: {perf['stock_names']}  Current Price: {current_price:,.1f} Yen"),
        html.Ul([
            html.Li(
                f"Holding Qty/Amount: {perf['holding_qty']:,} / {int(perf['holding_value']):,} Yen"),
            html.Li(
                f"Break Even Point Price: {perf['break_even_point_price']:,.1f} Yen"),
            html.Li(
                f"Total Buy Qty/Amount: {perf['total_buy_qty']:,} / {int(perf['total_buy_amount']):,} Yen \
                        --> Avg Buy Price: {perf['avg_buy_price']:,.1f} Yen"),
            html.Li(
                f"Total Sell Qty/Amount: {perf['total_sell_qty']:,} / {int(perf['total_sell_amount']):,} Yen \
                      --> Avg Sell Price: {perf['avg_sell_price']:,.1f} Yen"),
            html.Li(
                f"Realized Profit: {int(perf['realized_profit']):,} Yen ({perf['realized_profit_pct']:.2f}%)"),
            html.Li(
                f"Unrealized Profit: {int(perf['unrealized_profit']):,} Yen ({perf['unrealized_profit_pct']:.2f}%)"),
            html.Li(
                f"Total Profit: {int(perf['total_profit']):,} Yen ({perf['total_profit_pct']:.2f}%)"),
        ])
    ])

    fig_price, fig_perf = make_analysis_figures(
        stock_df=stock_df,
        stock_code=stock_code,
        names_str=names_str,
        current_price=current_price,
        add_today=True,
    )

    # Format date columns for display if needed
    stock_df_disp = stock_df.copy()
    if Columns.DATE in stock_df_disp.columns:
        stock_df_disp[Columns.DATE] = stock_df_disp[Columns.DATE].astype(str)
    if Columns.SETTLEMENT_DATE in stock_df_disp.columns:
        stock_df_disp[Columns.SETTLEMENT_DATE] = stock_df_disp[Columns.SETTLEMENT_DATE].astype(
            str)

    table = DataTable(
        columns=[{"name": i, "id": i} for i in stock_df_disp.columns],
        data=stock_df_disp.to_dict("records"),
        style_table={"height": "400px",
                     "overflowY": "auto", "overflowX": "auto"},
        sort_action="native",
        filter_action="native",
        page_action="none",
    )

    return metrics, fig_price, fig_perf, table
