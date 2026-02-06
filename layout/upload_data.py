from dash import html, dcc
from callbacks import upload_callbacks
from core.constants import UI, TabValues

def get_layout():
    return html.Div([
        html.H2(UI.UPLOAD_DATA_TITLE),
        dcc.Tabs(id="upload-type-tabs", value=TabValues.TRANSACTIONS, children=[
            dcc.Tab(label=UI.TAB_TRANSACTIONS, value=TabValues.TRANSACTIONS),
            dcc.Tab(label=UI.TAB_CASH_FLOWS, value=TabValues.CASH_FLOWS),
        ]),
        html.Div(id="upload-section"),
    ])
