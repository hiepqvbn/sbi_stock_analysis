# layout/dashboard.py
from __future__ import annotations

from dash import dcc, html, dash_table
import pandas as pd

from callbacks import dashboard_callbacks
from core.constants import Columns, KPI, UI, PnLKind, PositionMode, TableLabels


def get_layout() -> html.Div:
    today = pd.Timestamp.today().normalize()

    return html.Div(
        [
            # =========================
            # Header + Controls
            # =========================
            html.Div(
                [
                    html.Div(
                        [
                            html.H2(UI.DASHBOARD_TITLE, style={"margin": "0"}),
                            html.Div(
                                UI.DASHBOARD_SUBTITLE,
                                style={"opacity": "0.7", "marginTop": "4px"},
                            ),
                        ],
                        style={"display": "flex", "flexDirection": "column"},
                    ),
                    html.Div(
                        [
                            html.Button(
                                UI.REFRESH,
                                id="dashboard-refresh-btn",
                                n_clicks=0,
                                style={
                                    "padding": "10px 14px",
                                    "borderRadius": "10px",
                                    "border": "1px solid #ddd",
                                    "background": "white",
                                    "cursor": "pointer",
                                },
                            ),
                        ],
                        style={"display": "flex", "gap": "10px",
                               "alignItems": "center"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "gap": "16px",
                    "marginBottom": "16px",
                },
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.Div(UI.DATE_RANGE, style={
                                     "marginBottom": "6px"}),
                            html.Div(
                                [
                                    dcc.DatePickerSingle(
                                        id="dashboard-start-date",
                                        date=None,
                                        min_date_allowed=pd.Timestamp(
                                            "2000-01-01"),
                                        max_date_allowed=today,
                                        display_format="YYYY-MM-DD",
                                        clearable=True,
                                    ),
                                    dcc.DatePickerSingle(
                                        id="dashboard-end-date",
                                        date=None,
                                        min_date_allowed=pd.Timestamp(
                                            "2000-01-01"),
                                        max_date_allowed=today,
                                        display_format="YYYY-MM-DD",
                                        clearable=True,
                                    ),
                                ],
                                style={"display": "flex", "gap": "10px"},
                            ),
                        ],
                        style={"minWidth": "360px"},
                    ),
                    html.Div(
                        [
                            html.Div(UI.POSITIONS, style={
                                     "marginBottom": "6px"}),
                            dcc.RadioItems(
                                id="dashboard-positions-mode",
                                options=[
                                    {"label": UI.HOLDING_ONLY,
                                        "value": PositionMode.HOLDING},
                                    {"label": UI.INCLUDE_CLOSED,
                                        "value": PositionMode.ALL},
                                ],
                                value=PositionMode.HOLDING,
                                inline=True,
                            ),
                        ],
                        style={"minWidth": "320px"},
                    ),
                    html.Div(
                        [
                            html.Div(UI.TOP_N, style={"marginBottom": "6px"}),
                            dcc.Slider(
                                id="dashboard-topn",
                                min=5,
                                max=30,
                                step=1,
                                value=10,
                                marks={5: "5", 10: "10", 20: "20", 30: "30"},
                                tooltip={"placement": "bottom",
                                         "always_visible": False},
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.Div(UI.ALLOC_TOP_N, style={
                                     "marginBottom": "6px"}),
                            dcc.Slider(
                                id="dashboard-alloc-topn",
                                min=2,
                                max=10,
                                step=1,
                                value=4,
                                marks={2: "2", 4: "4",
                                       6: "6", 8: "8", 10: "10"},
                                tooltip={"placement": "bottom",
                                         "always_visible": False},
                            ),
                        ],
                        style={"flex": "1"},
                    ),
                    html.Div(
                        [
                            html.Div(UI.INITIAL_CAPITAL, style={"marginBottom": "6px"}),
                            dcc.Input(
                                id="dashboard-initial-capital",
                                type="number",
                                value=3500000,
                                placeholder=UI.INITIAL_CAPITAL_PLACEHOLDER,
                                style={"width": "180px"},
                            ),
                        ],
                        style={"minWidth": "220px"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "16px",
                    "flexWrap": "wrap",
                    "padding": "12px",
                    "border": "1px solid #eee",
                    "borderRadius": "14px",
                    "marginBottom": "16px",
                    "background": "white",
                },
            ),

            # =========================
            # KPI Cards
            # =========================
            html.Div(
                [
                    _kpi_card(KPI.MARKET_VALUE,
                              "dashboard-kpi-market-value", "¥0"),
                    _kpi_card(KPI.TOTAL_PNL, "dashboard-kpi-total-pnl", "¥0"),
                    _kpi_card(KPI.RETURN_PCT,
                              "dashboard-kpi-return-pct", "0.00%"),
                    _kpi_card(KPI.REALIZED_UNREALIZED,
                              "dashboard-kpi-split", "¥0 / ¥0"),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(4, minmax(0, 1fr))",
                    "gap": "12px",
                    "marginBottom": "16px",
                },
            ),

            # =========================
            # Charts Rows   
            # =========================
            html.Div(
                [
                    html.Div(
                        [
                            html.H4(UI.ALLOC_TITLE,
                                    style={"margin": "0 0 8px 0"}),
                            dcc.Graph(
                                id="dashboard-fig-allocation",
                                figure={},
                                config={"displayModeBar": False},
                                style={"height": "360px"},
                            ),
                        ],
                        style=_panel_style(),
                    ),
                    html.Div(
                        [
                            html.H4(UI.TOP_PNL_TITLE, style={
                                    "margin": "0 0 8px 0"}),
                            dcc.Dropdown(
                                id="dashboard-pnl-kind",
                                options=[
                                    {"label": UI.PNL_KIND_TOTAL,
                                        "value": PnLKind.TOTAL},
                                    {"label": UI.PNL_KIND_UNREALIZED,
                                        "value": PnLKind.UNREALIZED},
                                    {"label": UI.PNL_KIND_REALIZED,
                                        "value": PnLKind.REALIZED},
                                ],
                                value=PnLKind.UNREALIZED,
                                clearable=False,
                                style={"marginBottom": "8px"},
                            ),
                            dcc.Graph(
                                id="dashboard-fig-top-pnl",
                                figure={},
                                config={"displayModeBar": False},
                                style={"height": "360px"},
                            ),
                        ],
                        style=_panel_style(),
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "12px",
                    "marginBottom": "16px",
                },
            ),
            # figure: Asset Growth Over Time
            html.Div(
                [
                    html.Div(
                        [
                            html.H4(UI.ASSET_GROWTH_TITLE, style={
                                    "margin": "0 0 8px 0"}),
                            dcc.Graph(
                                id="dashboard-fig-asset-growth",
                                figure={},
                                config={"displayModeBar": False},
                                style={"height": "360px"},
                            ),
                        ],
                        style=_panel_style(),
                    ),
                ],
                style={"marginBottom": "16px"},
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H4(UI.STOCK_PERF_TITLE, style={"margin": "0 0 8px 0"}),
                            dcc.Tabs(
                                id="dashboard-stock-perf-tab",
                                value="realized",
                                children=[
                                    dcc.Tab(label=UI.TAB_REALIZED, value="realized"),
                                    dcc.Tab(label=UI.TAB_TOTAL, value="total"),
                                ],
                                style={"marginBottom": "8px"},
                            ),
                            dcc.Graph(
                                id="dashboard-fig-stock-perf",
                                figure={},
                                config={"displayModeBar": False},
                                style={"height": "360px"},
                            ),
                        ],
                        style=_panel_style(),
                    ),
                ],
                style={"marginBottom": "16px"},
            ),

            # =========================
            # Holdings Table
            # =========================
            html.Div(
                [
                    html.H4(UI.HOLDINGS_TITLE, style={"margin": "0 0 8px 0"}),
                    dash_table.DataTable(
                        id="dashboard-holdings-table",
                        columns=[
                            {"name": TableLabels.CODE, "id": Columns.STOCK_CODE},
                            {"name": TableLabels.NAME, "id": Columns.STOCK_NAME},
                            {"name": TableLabels.QTY,
                                "id": Columns.QTY, "type": "numeric"},
                            {"name": TableLabels.AVG_COST,
                                "id": Columns.AVG_COST, "type": "numeric"},
                            {"name": TableLabels.CURRENT_PRICE, "id": Columns.CURRENT_PRICE,
                                "type": "numeric"},
                            {"name": TableLabels.MARKET_VALUE,
                                "id": Columns.MARKET_VALUE, "type": "numeric"},
                            {"name": TableLabels.UNREALIZED, "id": Columns.UNREALIZED,
                                "type": "numeric"},
                            {"name": TableLabels.REALIZED,
                                "id": Columns.REALIZED, "type": "numeric"},
                            {"name": TableLabels.TOTAL_PNL, "id": Columns.TOTAL_PNL,
                                "type": "numeric"},
                            {"name": TableLabels.UNREALIZED_PCT,
                                "id": Columns.UNREALIZED_PCT, "type": "numeric"},
                        ],
                        data=[],
                        page_size=15,
                        sort_action="native",
                        filter_action="native",
                        row_selectable="single",
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "padding": "8px",
                            "fontFamily": "system-ui",
                            "fontSize": "13px",
                            "whiteSpace": "nowrap",
                        },
                        style_header={
                            "backgroundColor": "#fafafa",
                            "fontWeight": "600",
                            "borderBottom": "1px solid #eee",
                        },
                        style_data={
                            "borderBottom": "1px solid #f2f2f2",
                        },
                    ),
                    html.Div(
                        id="dashboard-holdings-note",
                        children="Tip: click a row to jump to Analysis tab later (optional).",
                        style={"opacity": "0.65",
                               "marginTop": "8px", "fontSize": "12px"},
                    ),
                ],
                style=_panel_style(),
            ),

            # hidden store(s) if you want caching later
            dcc.Store(id="dashboard-cache", data={}),
            dcc.Store(id="dashboard-snapshot-store", data=None),
            dcc.Store(id="dashboard-last-refresh-store", data={"n": 0}),
        ],
        style={
            "padding": "18px",
            "maxWidth": "1200px",
            "margin": "0 auto",
        },
    )


def _kpi_card(title: str, value_id: str, default_value: str) -> html.Div:
    return html.Div(
        [
            html.Div(title, style={"opacity": "0.7", "fontSize": "12px"}),
            html.Div(
                default_value,
                id=value_id,
                style={"fontSize": "22px",
                       "fontWeight": "700", "marginTop": "6px"},
            ),
        ],
        style={
            "padding": "12px 14px",
            "borderRadius": "14px",
            "border": "1px solid #eee",
            "background": "white",
            "boxShadow": "0 1px 2px rgba(0,0,0,0.04)",
        },
    )


def _panel_style() -> dict:
    return {
        "padding": "12px 14px",
        "borderRadius": "14px",
        "border": "1px solid #eee",
        "background": "white",
        "boxShadow": "0 1px 2px rgba(0,0,0,0.04)",
    }


# from dash import html, dcc
# from dash import dash_table
# import dash_bootstrap_components as dbc


# def get_layout():
#     return html.Div([
#         html.H2("Dashboard"),
#         html.Div(id="portfolio-kpi-cards", style={"marginBottom": "24px"}),
#         dcc.Graph(id="portfolio-performance-graph", style={"marginBottom": "24px"}),
#         dcc.Graph(id="allocation-graph"),
#         html.Hr(),
#         html.H4("Portfolio Summary"),
#         html.Div(id="dashboard-summary-table"),
#         dcc.Upload(
#             id='upload-data',
#             children=html.Div(
#                 ['Drag and Drop or ', html.A('Select CSV Files')]),
#             style={
#                 'width': '100%',
#                 'height': '60px',
#                 'lineHeight': '60px',
#                 'borderWidth': '1px',
#                 'borderStyle': 'dashed',
#                 'borderRadius': '5px',
#                 'textAlign': 'center',
#                 'margin': '10px'
#             },
#             multiple=True
#         ),
#         html.Div(id='upload-status'),
#         dash_table.DataTable(
#             id='data-table',
#             columns=[],
#             data=[],
#             style_table={'height': '500px',
#                          'overflowY': 'auto', 'overflowX': 'auto'},
#             sort_action='native',
#             filter_action='native',
#         )
#     ])
# # layout = dbc.Container([
# #     html.H2("📈 Investment Dashboard"),
# #     dbc.Row([
# #         dbc.Col([
# #             dcc.DatePickerRange(id='date-range'),
# #             dcc.Dropdown(id='stock-selector', multi=True, placeholder="Select Stock")
# #         ])
# #     ], className="mb-4"),
# #     dbc.Row([
# #         dbc.Col(dcc.Graph(id='portfolio-value')),
# #         dbc.Col(dcc.Graph(id='stock-pnl'))
# #     ]),
# #     dbc.Row([
# #         dbc.Col(html.Div(id='transaction-table'))
# #     ])
# # ])
