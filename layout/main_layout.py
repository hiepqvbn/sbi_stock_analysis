# layout/main_layout.py
from dash import html, dcc
import dash_bootstrap_components as dbc

from core.constants import UI

def get_main_layout():
    sidebar = dbc.Nav(
        [
            dbc.NavLink(UI.NAV_DASHBOARD, href="/", active="exact"),
            dbc.NavLink(UI.NAV_ANALYSIS, href="/analysis", active="exact"),
            dbc.NavLink(UI.NAV_DATA_RECORD, href="/data", active="exact"),
            dbc.NavLink(UI.NAV_UPLOAD, href="/upload", active="exact"),
            dbc.NavLink(UI.NAV_SETTINGS, href="/settings", active="exact"),
        ],
        vertical=True,
        pills=True,
        style={
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": "200px",
            "padding": "20px",
            "background": "#f8f9fa",
        }
    )

    content = html.Div(id="page-content", style={"marginLeft": "220px", "padding": "20px"})

    return html.Div([
        dcc.Location(id="url"),
        sidebar,
        content
    ])


# layout = html.Div([
#     html.H2("📈 Stock Portfolio Dashboard"),

#     dcc.Upload(
#         id='upload-data',
#         children=html.Div([
#             '📁 Drag and Drop or ',
#             html.A('Select CSV File')
#         ]),
#         style={
#             'width': '50%',
#             'height': '60px',
#             'lineHeight': '60px',
#             'borderWidth': '1px',
#             'borderStyle': 'dashed',
#             'borderRadius': '5px',
#             'textAlign': 'center',
#             'margin': '10px'
#         },
#         multiple=False
#     ),

#     html.Div(id='upload-status'),

#     html.Hr(),

#     html.Div(id='data-summary')  # Placeholder for summary (optional)
# ])
