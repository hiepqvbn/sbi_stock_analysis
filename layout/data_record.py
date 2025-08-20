from dash import html, dcc
from dash import dash_table
from callbacks import record_callbacks

def get_layout():
    return html.Div([
        html.H2("Data Record"),
        dcc.Tabs(id="data-tabs", value="transactions", children=[
            dcc.Tab(label="Transactions", value="transactions"),
            dcc.Tab(label="Dividends", value="dividends"),
            dcc.Tab(label="Deposits", value="deposits"),
            dcc.Tab(label="Stock Splits", value="stock_splits"),
        ], style={"marginBottom": "16px"}),
        html.Div(id="data-record-table"),
    ])