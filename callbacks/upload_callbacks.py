from dash import Input, Output, State, callback, html, dcc
import base64
import io
from data_handler.csv_parser import clean_sbi_transaction_csv, clean_sbi_cash_flow_csv  # your parser
from data_handler.db_manager import insert_transactions, insert_cash_flows
from core.constants import UI, TabValues

@callback(
    Output("upload-section", "children"),
    Input("upload-type-tabs", "value"),
)
def render_upload_section(tab):
    label_map = {
        TabValues.TRANSACTIONS: UI.UPLOAD_LABEL_TRANSACTIONS,
        TabValues.DIVIDENDS: UI.UPLOAD_LABEL_DIVIDENDS,
        TabValues.CASH_FLOWS: UI.UPLOAD_LABEL_CASH_FLOWS,
        TabValues.STOCK_SPLITS: UI.UPLOAD_LABEL_STOCK_SPLITS,
    }
    return html.Div([
        html.H4(label_map[tab]),
        dcc.Upload(
            id=f"upload-{tab}",
            children=html.Div([UI.UPLOAD_DROP, html.A(UI.UPLOAD_SELECT)]),
            style={
                "width": "100%", "height": "60px", "lineHeight": "60px",
                "borderWidth": "1px", "borderStyle": "dashed",
                "borderRadius": "5px", "textAlign": "center", "marginBottom": "16px"
            },
        ),
        html.Div(id=f"upload-status-{tab}"),
    ])

@callback(
    Output("upload-status-transactions", "children"),
    Input("upload-transactions", "contents"),
    State("upload-transactions", "filename"),
)
def handle_upload_transactions(contents, filename):
    if contents is None:
        return ""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file_buffer = io.StringIO(decoded.decode('shift_jis'))  # or utf-8 if needed
        df = clean_sbi_transaction_csv(file_buffer)  # Clean and return DataFrame
        insert_transactions(df)          # Insert DataFrame into DB
        return f"{UI.UPLOAD_SUCCESS_PREFIX} {len(df)} transactions from: {filename}"
    except Exception as e:
        return f"{UI.UPLOAD_ERROR_PREFIX} {filename}: {e}"


@callback(
    Output("upload-status-cash_flows", "children"),
    Input("upload-cash_flows", "contents"),
    State("upload-cash_flows", "filename"),
)
def handle_upload_cash_flows(contents, filename):
    if contents is None:
        return ""
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        file_buffer = io.StringIO(decoded.decode('utf-8-sig'))
        df = clean_sbi_cash_flow_csv(file_buffer)
        insert_cash_flows(df)
        return f"{UI.UPLOAD_SUCCESS_PREFIX} {len(df)} cash flows from: {filename}"
    except Exception as e:
        return f"{UI.UPLOAD_ERROR_PREFIX} {filename}: {e}"
