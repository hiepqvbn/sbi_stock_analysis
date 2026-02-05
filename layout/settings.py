from dash import html, dcc
from core.constants import UI

def get_layout():
    return html.Div([
        html.H2(UI.SETTINGS_TITLE),
        html.Div([
            html.Label(UI.SETTINGS_CURRENCY),
            dcc.Dropdown(
                id="settings-currency-dropdown",
                options=[
                    {"label": "JPY", "value": "JPY"},
                    {"label": "USD", "value": "USD"},
                    {"label": "EUR", "value": "EUR"},
                ],
                placeholder=UI.SETTINGS_CURRENCY_PLACEHOLDER,
                style={"width": "200px"}
            ),
        ], style={"marginBottom": "16px"}),
        html.Div([
            html.Label(UI.SETTINGS_CHART_STYLE),
            dcc.Dropdown(
                id="settings-chart-style-dropdown",
                options=[
                    {"label": "Light", "value": "light"},
                    {"label": "Dark", "value": "dark"},
                ],
                placeholder=UI.SETTINGS_CHART_STYLE_PLACEHOLDER,
                style={"width": "200px"}
            ),
        ], style={"marginBottom": "16px"}),
        html.Div([
            html.Label(UI.SETTINGS_RISK_PROFILE),
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
        html.Button(UI.SETTINGS_SAVE, id="save-settings-btn"),
        html.Div(id="settings-save-status", style={"marginTop": "16px"}),
    ])
