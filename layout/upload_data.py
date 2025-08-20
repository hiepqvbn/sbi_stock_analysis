from dash import html, dcc
from callbacks import upload_callbacks

def get_layout():
    return html.Div([
        html.H2("Upload Data 2"),
        dcc.Tabs(id="upload-type-tabs", value="transactions", children=[
            dcc.Tab(label="Transactions", value="transactions"),
            dcc.Tab(label="Dividends", value="dividends"),
            dcc.Tab(label="Cash Flows", value="cash_flows"),
            dcc.Tab(label="Stock Splits", value="stock_splits"),
        ]),
        html.Div(id="upload-section"),
    ])
