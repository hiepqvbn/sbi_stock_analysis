# app.py
from dash import Dash, Output, Input
import dash_bootstrap_components as dbc
from layout.main_layout import get_main_layout
from layout.dashboard import get_layout as dashboard_layout
from layout.data_record import get_layout as data_record_layout
from layout.analysis import get_layout as analysis_layout
from layout.upload_data import get_layout as upload_data_layout
from layout.settings import get_layout as settings_layout

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True
app.title = "Stock Portfolio"
app.layout = get_main_layout()

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def display_page(pathname):
    if pathname == "/":
        return dashboard_layout()
    elif pathname == "/analysis":
        return analysis_layout()
    elif pathname == "/data":
        return data_record_layout()
    elif pathname == "/upload":
        return upload_data_layout()
    elif pathname == "/settings":
        return settings_layout()
    else:
        return "404 Page Not Found"

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host="0.0.0.0", port=8050)
