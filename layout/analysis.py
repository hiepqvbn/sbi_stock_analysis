from dash import html, dcc
from callbacks import analysis_callbacks
from core.constants import UI


def get_layout():
    return html.Div([
        html.H2(UI.ANALYSIS_TITLE),
        html.Div([
            html.Label(UI.SELECT_STOCK),
            dcc.Dropdown(id="analysis-stock-dropdown",
                         placeholder=UI.SELECT_STOCK_PLACEHOLDER),
        ], style={"width": "300px", "marginBottom": "24px"}),
        html.Div(
            [html.Div([
                html.Label(UI.EXPECTED_PRICE),
                dcc.Input(id="expected-price-input", type="number",
                      placeholder=UI.EXPECTED_PRICE_PLACEHOLDER, style={"marginLeft": "10px"}),
            ], style={"marginBottom": "24px"}),
                html.Div([
                    html.Div(UI.DATE_RANGE_ANALYSIS, style={"marginBottom": "6px"}),
                    html.Div(
                        [
                            dcc.DatePickerSingle(
                                id="analysis-start-date",
                                date=None,
                                display_format="YYYY-MM-DD",
                                clearable=True,
                            ),
                            dcc.DatePickerSingle(
                                id="analysis-end-date",
                                date=None,
                                display_format="YYYY-MM-DD",
                                clearable=True,
                            ),
                        ],
                        style={"display": "flex", "gap": "10px"},
                    ),
                ], style={"marginTop": "10px"})],style={"display": "flex", "gap": "50px"}),
        html.Div(id="stock-metrics", style={"marginBottom": "24px"}),
        dcc.Graph(id="stock-indicators-graph"),
        dcc.Graph(id="stock-price-graph", style={"marginBottom": "24px"}),
        html.H4(UI.TRANSACTION_RECORDS),
        html.Div(id="analysis-stock-table"),
    ])
