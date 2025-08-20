from dash import html, dcc
from callbacks import analysis_callbacks


def get_layout():
    return html.Div([
        html.H2("Stock Analysis"),
        html.Div([
            html.Label("Select Stock:"),
            dcc.Dropdown(id="analysis-stock-dropdown",
                         placeholder="Choose a stock"),
        ], style={"width": "300px", "marginBottom": "24px"}),
        html.Div([
            html.Label("Expected Price:"),
            dcc.Input(id="expected-price-input", type="number",
                      placeholder="Enter expected price", style={"marginLeft": "10px"}),
        ], style={"marginBottom": "24px"}),
        html.Div(id="stock-metrics", style={"marginBottom": "24px"}),
        dcc.Graph(id="stock-price-graph", style={"marginBottom": "24px"}),
        dcc.Graph(id="stock-indicators-graph"),
        html.H4("Transaction Records"),
        html.Div(id="analysis-stock-table"),
    ])
