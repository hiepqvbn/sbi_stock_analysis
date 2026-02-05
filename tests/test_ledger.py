import pandas as pd

from core.ledger import build_trade_ledger, compute_realized_window
from core.constants import Columns, TradeType


def _make_tx_df(rows):
    return pd.DataFrame(rows)


def test_build_trade_ledger_basic():
    df = _make_tx_df(
        [
            {
                Columns.DATE: "2024-01-01",
                Columns.TRADE_TYPE: TradeType.BUY,
                Columns.QUANTITY: 10,
                Columns.PRICE_PER_SHARE: 100,
                Columns.FEE: 0,
            },
            {
                Columns.DATE: "2024-01-10",
                Columns.TRADE_TYPE: TradeType.SELL,
                Columns.QUANTITY: 4,
                Columns.PRICE_PER_SHARE: 120,
                Columns.FEE: 0,
            },
        ]
    )

    ledger = build_trade_ledger(df)
    last = ledger.iloc[-1]

    assert last[Columns.POS_QTY_AFTER] == 6
    assert round(last[Columns.AVG_COST_AFTER], 2) == 100.0
    assert round(last[Columns.REALIZED_CUM], 2) == 80.0
    assert round(last[Columns.HOLDING_VALUE], 2) == 720.0
    assert round(last[Columns.UNREALIZED_PROFIT], 2) == 120.0
    assert round(last[Columns.TOTAL_EQUITY], 2) == 200.0


def test_compute_realized_window():
    df = _make_tx_df(
        [
            {
                Columns.DATE: "2024-01-01",
                Columns.STOCK_CODE: "1111",
                Columns.TRADE_TYPE: TradeType.BUY,
                Columns.QUANTITY: 10,
                Columns.TOTAL_AMOUNT: 1000,
                Columns.FEE: 0,
            },
            {
                Columns.DATE: "2024-01-10",
                Columns.STOCK_CODE: "1111",
                Columns.TRADE_TYPE: TradeType.SELL,
                Columns.QUANTITY: 4,
                Columns.TOTAL_AMOUNT: 480,
                Columns.FEE: 0,
            },
            {
                Columns.DATE: "2024-02-10",
                Columns.STOCK_CODE: "1111",
                Columns.TRADE_TYPE: TradeType.SELL,
                Columns.QUANTITY: 2,
                Columns.TOTAL_AMOUNT: 180,
                Columns.FEE: 0,
            },
        ]
    )

    out = compute_realized_window(df, start_date="2024-01-05", end_date="2024-01-31")
    row = out.iloc[0]

    assert row[Columns.REALIZED_WINDOW] == 80
    assert round(row[Columns.COST_BASIS_WINDOW], 2) == 400.0
