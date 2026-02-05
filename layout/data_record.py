from dash import html, dcc
from dash import dash_table
from callbacks import record_callbacks
from core.constants import UI, TabValues

def get_layout():
    return html.Div([
        html.H2(UI.DATA_RECORD_TITLE),
        dcc.Tabs(id="data-tabs", value=TabValues.TRANSACTIONS, children=[
            dcc.Tab(label=UI.TAB_TRANSACTIONS, value=TabValues.TRANSACTIONS),
            dcc.Tab(label=UI.TAB_DIVIDENDS, value=TabValues.DIVIDENDS),
            dcc.Tab(label=UI.TAB_DEPOSITS, value=TabValues.DEPOSITS),
            dcc.Tab(label=UI.TAB_STOCK_SPLITS, value=TabValues.STOCK_SPLITS),
        ], style={"marginBottom": "16px"}),
        html.Div(id="data-record-table"),
    ])
