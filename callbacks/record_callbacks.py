from dash import Input, Output, callback, html
from dash.dash_table import DataTable
from data_handler.db_manager import get_all_transactions


@callback(
    Output("data-record-table", "children"),
    Input("data-tabs", "value"),
)
def render_data_table(tab):
    if tab != "transactions":
        return html.Div("Unknown tab selected.")

    df = get_all_transactions()
    if df is None or df.empty:
        return html.Div("No data available.")

    # Format date columns for display if needed
    if "date" in df.columns:
        df["date"] = df["date"].astype(str)
    if "settlement_date" in df.columns:
        df["settlement_date"] = df["settlement_date"].astype(str)

    return DataTable(
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        style_table={"height": "500px", "overflowY": "auto", "overflowX": "auto"},
        sort_action="native",
        filter_action="native",
        page_action="none",
    )
