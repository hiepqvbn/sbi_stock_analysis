from dash import Input, Output, callback, html
from dash.dash_table import DataTable
from data_handler.db_manager import get_all_transactions, get_cash_flows
from core.constants import Columns, UI, TabValues


@callback(
    Output("data-record-table", "children"),
    Input("data-tabs", "value"),
)
def render_data_table(tab):
    if tab == TabValues.TRANSACTIONS:
        df = get_all_transactions()
        if df is None or df.empty:
            return html.Div(UI.NO_DATA)

        if Columns.DATE in df.columns:
            df[Columns.DATE] = df[Columns.DATE].astype(str)
        if Columns.SETTLEMENT_DATE in df.columns:
            df[Columns.SETTLEMENT_DATE] = df[Columns.SETTLEMENT_DATE].astype(str)

        return DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            style_table={"height": "500px", "overflowY": "auto", "overflowX": "auto"},
            sort_action="native",
            filter_action="native",
            page_action="none",
        )

    if tab == TabValues.DEPOSITS:
        df = get_cash_flows()
        if df is None or df.empty:
            return html.Div(UI.NO_DATA)

        return DataTable(
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            style_table={"height": "500px", "overflowY": "auto", "overflowX": "auto"},
            sort_action="native",
            filter_action="native",
            page_action="none",
        )

    return html.Div(UI.UNKNOWN_TAB)
