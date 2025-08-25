from dash import Input, Output, State, callback, html
from dash.dash_table import DataTable
from data_handler.db_manager import get_all_transactions
from utils.analysis_utils import analyze_stock_performance


@callback(
    Output("analysis-stock-dropdown", "options"),
    Input("url", "pathname"),
)
def update_stock_dropdown_options(_):
    df = get_all_transactions()
    # Get latest name for each stock_code
    latest_names = df.sort_values("date").groupby(
        "stock_code")["stock_name"].last()
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
)
def update_analysis(stock_code, expected_price):
    if not stock_code:
        return "Select a stock to see metrics.", {}, {}, None

    df = get_all_transactions()
    stock_df = df[df["stock_code"] == stock_code]

    if stock_df.empty:
        return "No data for this stock.", {}, {}, None

    # Use expected price if provided, else use latest price_per_share
    current_price = expected_price if expected_price is not None else (
        stock_df["price_per_share"].iloc[-1] if "price_per_share" in stock_df.columns else 0
    )

    perf = analyze_stock_performance(
        stock_df, stock_code, current_price, plot=True)

    metrics = html.Div([
        html.Div(f"Stock code: {stock_code}"),
        html.Div(f"Names used: {perf['stock_names']}"),
        html.Ul([
            html.Li(f"Total Buy Qty: {perf['total_buy_qty']:,}"),
            html.Li(f"Total Buy Amount: {int(perf['total_buy_amount']):,} Yen"),
            html.Li(f"Avg Buy Price: {perf['avg_buy_price']:,.1f} Yen"),
            html.Li(f"Total Sell Qty: {perf['total_sell_qty']:,}"),
            html.Li(f"Total Sell Amount: {int(perf['total_sell_amount']):,} Yen"),
            html.Li(
                f"Realized Profit: {int(perf['realized_profit']):,} Yen ({perf['realized_profit_pct']:.2f}%)"),
            html.Li(
                f"Unrealized Profit: {int(perf['unrealized_profit']):,} Yen ({perf['unrealized_profit_pct']:.2f}%)"),
            html.Li(
                f"Total Profit: {int(perf['total_profit']):,} Yen ({perf['total_profit_pct']:.2f}%)"),
        ])
    ])

    fig_price, fig_perf = perf.get("plots", {})

    # Format date columns for display if needed
    stock_df_disp = stock_df.copy()
    if "date" in stock_df_disp.columns:
        stock_df_disp["date"] = stock_df_disp["date"].astype(str)
    if "settlement_date" in stock_df_disp.columns:
        stock_df_disp["settlement_date"] = stock_df_disp["settlement_date"].astype(
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
