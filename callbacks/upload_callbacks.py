from dash import Input, Output, State, callback, html, dcc
import base64
import io
from data_handler.csv_parser import clean_sbi_csv  # your parser
from data_handler.db_manager import insert_transactions

@callback(
    Output("upload-section", "children"),
    Input("upload-type-tabs", "value"),
)
def render_upload_section(tab):
    label_map = {
        "transactions": "Upload Transactions CSV",
        "dividends": "Upload Dividends CSV",
        "cash_flows": "Upload Cash Flows CSV",
        "stock_splits": "Upload Stock Splits CSV"
    }
    return html.Div([
        html.H4(label_map[tab]),
        dcc.Upload(
            id=f"upload-{tab}",
            children=html.Div(["Drag and Drop or ", html.A("Select CSV File")]),
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
        df = clean_sbi_csv(file_buffer)  # Clean and return DataFrame
        insert_transactions(df)          # Insert DataFrame into DB
        return f"Uploaded and inserted {len(df)} transactions from: {filename}"
    except Exception as e:
        return f"❌ Error processing file {filename}: {e}"
