from __future__ import annotations


class Columns:
    DATE = "date"
    STOCK_CODE = "stock_code"
    STOCK_NAME = "stock_name"
    TRADE_TYPE = "trade_type"
    QUANTITY = "quantity"
    PRICE_PER_SHARE = "price_per_share"
    PRICE = "price"
    TOTAL_AMOUNT = "total_amount"
    SETTLEMENT_DATE = "settlement_date"
    FEE = "fee"
    MARKET = "market"
    TERM = "term"
    ACCOUNT = "account"
    TAX = "tax"
    TAX_AMOUNT = "tax_amount"

    # snapshot/ledger fields
    QTY = "qty"
    AVG_COST = "avg_cost"
    COST_TOTAL = "cost_total"
    CURRENT_PRICE = "current_price"
    MARKET_VALUE = "market_value"
    REALIZED = "realized"
    UNREALIZED = "unrealized"
    TOTAL_PNL = "total_pnl"
    UNREALIZED_PCT = "unrealized_pct"
    REALIZED_WINDOW = "realized_window"
    COST_BASIS_WINDOW = "cost_basis_window"
    NET_VALUE = "net_value"

    # ledger outputs
    POS_QTY_AFTER = "pos_qty_after"
    AVG_COST_AFTER = "avg_cost_after"
    REALIZED_DELTA = "realized_delta"
    REALIZED_CUM = "realized_cum"
    CASH_FLOW = "cash_flow"
    UNREALIZED_PROFIT = "unrealized_profit"
    TOTAL_EQUITY = "total_equity"
    HOLDING_VALUE = "holding_value"
    BREAK_EVEN = "break_even_point_price"


class TradeType:
    BUY = "Buy"
    SELL = "Sell"
    TODAY = "Today"


class KPI:
    MARKET_VALUE = "Market Value"
    TOTAL_PNL = "Total PnL"
    RETURN_PCT = "Return %"
    REALIZED_UNREALIZED = "Realized / Unrealized"
    ACCOUNT_GROWTH = "Account Growth"
    CAPITAL_RETURN = "Capital Return"
    IRR = "IRR"
    TWR = "TWR"
    TWR_ANNUAL = "TWR / Ann."


class PnLKind:
    UNREALIZED = "unrealized"
    REALIZED = "realized"
    TOTAL = "total"


class PositionMode:
    HOLDING = "holding"
    ALL = "all"


class UI:
    DASHBOARD_TITLE = "Dashboard"
    DASHBOARD_SUBTITLE = "Portfolio overview (current snapshot)"
    REFRESH = "Refresh"
    DATE_RANGE = "Date range"
    START_DATE = "Start date"
    END_DATE = "End date"
    POSITIONS = "Positions"
    HOLDING_ONLY = "Holding only"
    INCLUDE_CLOSED = "Include closed"
    TOP_N = "Top N"
    ALLOC_TOP_N = "Allocation Top N"
    ALLOC_TITLE = "Allocation (Market Value)"
    TOP_PNL_TITLE = "Top PnL"
    HOLDINGS_TITLE = "Holdings"
    ASSET_GROWTH_TITLE = "Asset Growth Over Time"
    NET_DEPOSIT = "Net Deposit (¥)"
    NET_DEPOSIT_PLACEHOLDER = "e.g., 3500000"
    ASSET_TAB_VALUE = "Value"
    ASSET_TAB_RETURN = "Return %"
    BENCHMARK = "Benchmark"
    BENCHMARK_NONE = "None"
    BENCHMARK_SP500 = "S&P 500 (SPY)"
    STOCK_PERF_TITLE = "Stock Performance"
    TAB_REALIZED = "Realized PnL"
    TAB_TOTAL = "Total PnL"
    PNL_KIND_UNREALIZED = "Unrealized PnL"
    PNL_KIND_REALIZED = "Realized PnL"
    PNL_KIND_TOTAL = "Total PnL"

    ANALYSIS_TITLE = "Stock Analysis"
    SELECT_STOCK = "Select Stock:"
    SELECT_STOCK_PLACEHOLDER = "Choose a stock"
    EXPECTED_PRICE = "Expected Price:"
    EXPECTED_PRICE_PLACEHOLDER = "Enter expected price"
    DATE_RANGE_ANALYSIS = "Date range"
    TRANSACTION_RECORDS = "Transaction Records"
    ANALYSIS_SELECT_STOCK_MSG = "Select a stock to see metrics."
    ANALYSIS_NO_DATA_MSG = "No data for this stock."
    UNKNOWN_TAB = "Unknown tab selected."
    NO_DATA = "No data available."
    DATA_RECORD_TITLE = "Data Record"
    UPLOAD_DATA_TITLE = "Upload Data"
    SETTINGS_TITLE = "Settings"

    NAV_DASHBOARD = "Dashboard"
    NAV_ANALYSIS = "Analysis"
    NAV_DATA_RECORD = "Data Record"
    NAV_UPLOAD = "Upload Data"
    NAV_SETTINGS = "Settings"

    TAB_TRANSACTIONS = "Transactions"
    TAB_DIVIDENDS = "Dividends"
    TAB_DEPOSITS = "Deposits"
    TAB_STOCK_SPLITS = "Stock Splits"
    TAB_CASH_FLOWS = "Cash Flows"

    SETTINGS_CURRENCY = "Currency:"
    SETTINGS_CURRENCY_PLACEHOLDER = "Select currency"
    SETTINGS_CHART_STYLE = "Default Chart Style:"
    SETTINGS_CHART_STYLE_PLACEHOLDER = "Select chart style"
    SETTINGS_RISK_PROFILE = "Risk Profile:"
    SETTINGS_SAVE = "Save Settings"

    UPLOAD_LABEL_TRANSACTIONS = "Upload Transactions CSV"
    UPLOAD_LABEL_DIVIDENDS = "Upload Dividends CSV"
    UPLOAD_LABEL_CASH_FLOWS = "Upload Cash Flows CSV"
    UPLOAD_LABEL_STOCK_SPLITS = "Upload Stock Splits CSV"
    UPLOAD_DROP = "Drag and Drop or "
    UPLOAD_SELECT = "Select CSV File"
    UPLOAD_SUCCESS_PREFIX = "Uploaded and inserted"
    UPLOAD_ERROR_PREFIX = "Error processing file"


class TableLabels:
    CODE = "Code"
    NAME = "Name"
    QTY = "Qty"
    AVG_COST = "Avg Cost"
    CURRENT_PRICE = "Cur Price"
    MARKET_VALUE = "Market Value"
    UNREALIZED = "Unrealized"
    REALIZED = "Realized"
    TOTAL_PNL = "Total PnL"
    UNREALIZED_PCT = "Unrealized %"


class TabValues:
    TRANSACTIONS = "transactions"
    DIVIDENDS = "dividends"
    DEPOSITS = "deposits"
    STOCK_SPLITS = "stock_splits"
    CASH_FLOWS = "cash_flows"
