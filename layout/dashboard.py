# dashboard.py
from dash import html, dcc
from dash import dash_table
import dash_bootstrap_components as dbc


def get_layout():
    return html.Div([
        html.H2("Dashboard"),
        html.Div(id="portfolio-kpi-cards", style={"marginBottom": "24px"}),
        dcc.Graph(id="portfolio-performance-graph", style={"marginBottom": "24px"}),
        dcc.Graph(id="allocation-graph"),
        html.Hr(),
        html.H4("Portfolio Summary"),
        html.Div(id="dashboard-summary-table"),
        dcc.Upload(
            id='upload-data',
            children=html.Div(
                ['Drag and Drop or ', html.A('Select CSV Files')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            multiple=True
        ),
        html.Div(id='upload-status'),
        dash_table.DataTable(
            id='data-table',
            columns=[],
            data=[],
            style_table={'height': '500px',
                         'overflowY': 'auto', 'overflowX': 'auto'},
            sort_action='native',
            filter_action='native',
        )
    ])
# layout = dbc.Container([
#     html.H2("📈 Investment Dashboard"),
#     dbc.Row([
#         dbc.Col([
#             dcc.DatePickerRange(id='date-range'),
#             dcc.Dropdown(id='stock-selector', multi=True, placeholder="Select Stock")
#         ])
#     ], className="mb-4"),
#     dbc.Row([
#         dbc.Col(dcc.Graph(id='portfolio-value')),
#         dbc.Col(dcc.Graph(id='stock-pnl'))
#     ]),
#     dbc.Row([
#         dbc.Col(html.Div(id='transaction-table'))
#     ])
# ])
