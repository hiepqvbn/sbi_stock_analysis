# callbacks/dashboard_callbacks.py
import base64
import io
import pandas as pd
from dash import Input, Output, State, callback, html
from data_handler.csv_parser import clean_sbi_csv
from data_handler.db_manager import insert_new_rows, fetch_summary

from data_handler.db_manager import get_all_transactions


@callback(
    Output('upload-status', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def handle_uploaded_file(contents, filename):    
    if contents is None:
        return ""

    # Ensure both are lists
    if not isinstance(contents, list):
        contents = [contents]
    if not isinstance(filename, list):
        filename = [filename]

    messages = []
    for content, fname in zip(contents, filename):
        try:
            # Decode and read CSV
            print(f"Processing file: {fname}")
            print(f"Contents: {content[:100]}...")
            content_type, content_string = content.split(',')
            decoded = base64.b64decode(content_string)
            file_buffer = io.StringIO(decoded.decode('shift_jis'))

            # Clean and insert
            df = clean_sbi_csv(file_buffer)
            insert_new_rows(df)

            messages.append(
                f"✅ Uploaded and inserted data from: {fname} (new rows only)")
        except Exception as e:
            messages.append(f"❌ Error processing file {fname}: {e}")

    return html.Ul([html.Li(msg) for msg in messages])


@callback(
    Output('data-table', 'columns'),
    Output('data-table', 'data'),
    Input('upload-status', 'children'),
)
def update_data_table(_):
    df = get_all_transactions()
    columns = [{"name": i, "id": i} for i in df.columns]
    data = df.to_dict('records')
    
    return columns, data


# @callback(
#     Output('data-summary', 'children'),
#     Input('upload-data', 'contents')
# )
# def update_summary_after_upload(_):
#     summary = fetch_summary()
#     return html.Ul([
#         html.Li(
#             f"{row[0]} - {row[1]} trades, total qty {row[2]}, total amount ¥{row[3]:,.0f}")
#         for row in summary
#     ])


# @callback(
#     Output('portfolio-value', 'figure'),
#     Input('date-range', 'start_date'),
#     Input('date-range', 'end_date'),
#     Input('stock-selector', 'value')
# )
# def update_portfolio_value(start_date, end_date, stock_list):
#     df = get_all_transactions()
#     # Filter and calculate portfolio value
#     ...
#     return fig
