from dash import html, dcc

def get_layout():
    return html.Div([
        html.H2("Settings"),
        html.Div([
            html.Label("Currency:"),
            dcc.Dropdown(
                id="settings-currency-dropdown",
                options=[
                    {"label": "JPY", "value": "JPY"},
                    {"label": "USD", "value": "USD"},
                    {"label": "EUR", "value": "EUR"},
                ],
                placeholder="Select currency",
                style={"width": "200px"}
            ),
        ], style={"marginBottom": "16px"}),
        html.Div([
            html.Label("Default Chart Style:"),
            dcc.Dropdown(
                id="settings-chart-style-dropdown",
                options=[
                    {"label": "Light", "value": "light"},
                    {"label": "Dark", "value": "dark"},
                ],
                placeholder="Select chart style",
                style={"width": "200px"}
            ),
        ], style={"marginBottom": "16px"}),
        html.Div([
            html.Label("Risk Profile:"),
            dcc.RadioItems(
                id="settings-risk-profile",
                options=[
                    {"label": "Conservative", "value": "conservative"},
                    {"label": "Balanced", "value": "balanced"},
                    {"label": "Aggressive", "value": "aggressive"},
                ],
                inline=True,
            ),
        ], style={"marginBottom": "16px"}),
        html.Button("Save Settings", id="save-settings-btn"),
        html.Div(id="settings-save-status", style={"marginTop": "16px"}),
    ])