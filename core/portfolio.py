from __future__ import annotations

from typing import Dict, Optional
import pandas as pd

from core.constants import Columns, TradeType
from core.dates import to_dt
from core.splits import stocks_split_adjustments
from core.schema import TransactionSchema, validate_schema
from core.ledger import build_trade_ledger


def build_portfolio_value_timeseries(
    transactions_df: pd.DataFrame,
    price_map: Optional[Dict[str, float]] = None,
    as_of_date: Optional[str] = None,
    net_deposit: float = 0.0,
) -> pd.DataFrame:
    """
    Build a simple portfolio value time series using last known trade price
    for each stock. Optionally appends an as-of point using price_map.
    """
    if transactions_df is None or transactions_df.empty:
        return pd.DataFrame(columns=[Columns.DATE, Columns.MARKET_VALUE])

    validate_schema(transactions_df, TransactionSchema.required, name="transactions_df", raise_on_error=True)

    df = transactions_df.copy()
    df = stocks_split_adjustments(df)
    df[Columns.DATE] = to_dt(df[Columns.DATE])
    df = df.sort_values([Columns.DATE, "id"] if "id" in df.columns else [Columns.DATE])
    if as_of_date:
        as_of_dt = pd.to_datetime(as_of_date, errors="coerce")
        if not pd.isna(as_of_dt):
            df = df[df[Columns.DATE] <= as_of_dt]

    qty_by_code: Dict[str, float] = {}
    last_price_by_code: Dict[str, float] = {}
    rows = []
    net_cash_flow = 0.0

    for _, r in df.iterrows():
        code = str(r[Columns.STOCK_CODE])
        trade_type = str(r[Columns.TRADE_TYPE])
        qty = float(r[Columns.QUANTITY])
        price = float(r[Columns.PRICE_PER_SHARE])
        date = r[Columns.DATE]

        amount = r.get(Columns.TOTAL_AMOUNT, 0)
        fee_val = r.get(Columns.FEE, 0)
        try:
            amount = float(amount) if amount is not None else 0.0
        except Exception:
            amount = 0.0
        try:
            fee_val = float(fee_val) if fee_val is not None else 0.0
        except Exception:
            fee_val = 0.0

        if trade_type == TradeType.BUY:
            qty_by_code[code] = qty_by_code.get(code, 0.0) + qty
            net_cash_flow -= (amount + fee_val)
        elif trade_type == TradeType.SELL:
            qty_by_code[code] = qty_by_code.get(code, 0.0) - qty
            net_cash_flow += (amount - fee_val)

        last_price_by_code[code] = price

        holdings_value = 0.0
        for c, q in qty_by_code.items():
            if q <= 0:
                continue
            px = last_price_by_code.get(c)
            if px is None:
                continue
            holdings_value += q * px

        net_value = float(net_deposit) + net_cash_flow + float(holdings_value)
        rows.append({
            Columns.DATE: date,
            Columns.MARKET_VALUE: float(holdings_value),
            Columns.NET_VALUE: float(net_value),
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    out = out.groupby(Columns.DATE, as_index=False)[[Columns.MARKET_VALUE, Columns.NET_VALUE]].last()

    # optional as-of point using provided price_map
    if price_map:
        as_of = pd.to_datetime(as_of_date).normalize() if as_of_date else pd.Timestamp.today().normalize()
        holdings_value = 0.0
        for c, q in qty_by_code.items():
            if q <= 0:
                continue
            px = price_map.get(str(c))
            if px is None:
                continue
            holdings_value += q * px
        net_value = float(net_deposit) + net_cash_flow + float(holdings_value)
        out = pd.concat(
            [
                out,
                pd.DataFrame(
                    [{Columns.DATE: as_of, Columns.MARKET_VALUE: float(holdings_value), Columns.NET_VALUE: float(net_value)}]
                ),
            ],
            ignore_index=True,
        )

    return out


def build_stock_perf_timeseries(
    transactions_df: pd.DataFrame,
    kind: str,
) -> pd.DataFrame:
    """
    Build per-stock performance time series (stackable).
    kind: "realized" or "total"
    """
    if transactions_df is None or transactions_df.empty:
        return pd.DataFrame(columns=[Columns.DATE])

    validate_schema(transactions_df, TransactionSchema.required, name="transactions_df", raise_on_error=True)

    df = transactions_df.copy()
    df = stocks_split_adjustments(df)
    df[Columns.DATE] = to_dt(df[Columns.DATE])

    series_map = {}
    all_dates = set()

    for code, g in df.groupby(Columns.STOCK_CODE, sort=False):
        g = g.sort_values([Columns.DATE, "id"] if "id" in g.columns else [Columns.DATE])
        ledger = build_trade_ledger(g)
        if Columns.DATE not in ledger.columns:
            continue
        ledger_dates = pd.to_datetime(ledger[Columns.DATE])
        if kind == "realized":
            vals = ledger[Columns.REALIZED_CUM].astype(float).values
        else:
            vals = ledger[Columns.TOTAL_EQUITY].astype(float).values
        s = pd.Series(vals, index=ledger_dates).sort_index()
        if s.index.has_duplicates:
            s = s.groupby(level=0).last()
        series_map[str(code)] = s
        all_dates.update(s.index.tolist())

    if not series_map:
        return pd.DataFrame(columns=[Columns.DATE])

    all_dates = sorted(all_dates)
    out = pd.DataFrame({Columns.DATE: all_dates})
    out = out.set_index(Columns.DATE)

    for code, s in series_map.items():
        out[code] = s.reindex(out.index).ffill().fillna(0.0)

    out = out.reset_index()
    return out


def compute_account_growth(net_value: float, net_deposit: float) -> float:
    if net_deposit == 0:
        return 0.0
    return (net_value - net_deposit) / net_deposit * 100.0


def compute_capital_return(total_pnl: float, total_buy_amount: float) -> float:
    if total_buy_amount == 0:
        return 0.0
    return (total_pnl / total_buy_amount) * 100.0


def _xirr(cashflows: list[tuple[pd.Timestamp, float]]) -> float | None:
    if not cashflows:
        return None
    cashflows = sorted(cashflows, key=lambda x: x[0])
    t0 = cashflows[0][0]

    def npv(rate: float) -> float:
        total = 0.0
        for dt, cf in cashflows:
            days = (dt - t0).days
            total += cf / ((1.0 + rate) ** (days / 365.0))
        return total

    # bracket and bisection
    low, high = -0.999, 10.0
    f_low = npv(low)
    f_high = npv(high)
    if f_low * f_high > 0:
        return None

    for _ in range(80):
        mid = (low + high) / 2.0
        f_mid = npv(mid)
        if abs(f_mid) < 1e-6:
            return mid
        if f_low * f_mid < 0:
            high = mid
            f_high = f_mid
        else:
            low = mid
            f_low = f_mid
    return mid


def compute_irr(
    transactions_df: pd.DataFrame,
    ending_value: float,
    net_deposit: float,
) -> float:
    if transactions_df is None or transactions_df.empty:
        return 0.0

    df = transactions_df.copy()
    df = stocks_split_adjustments(df)
    df[Columns.DATE] = to_dt(df[Columns.DATE])
    df = df.sort_values([Columns.DATE, "id"] if "id" in df.columns else [Columns.DATE])

    cashflows: list[tuple[pd.Timestamp, float]] = []
    if net_deposit:
        cashflows.append((pd.to_datetime(df[Columns.DATE].min()), -float(net_deposit)))

    for _, r in df.iterrows():
        d = pd.to_datetime(r[Columns.DATE])
        amt = r.get(Columns.TOTAL_AMOUNT, 0) or 0
        fee = r.get(Columns.FEE, 0) or 0
        try:
            amt = float(amt)
        except Exception:
            amt = 0.0
        try:
            fee = float(fee)
        except Exception:
            fee = 0.0

        if r[Columns.TRADE_TYPE] == TradeType.BUY:
            cashflows.append((d, -(amt + fee)))
        elif r[Columns.TRADE_TYPE] == TradeType.SELL:
            cashflows.append((d, amt - fee))

    # ending value as final inflow
    last_date = pd.to_datetime(df[Columns.DATE].max())
    cashflows.append((last_date, float(ending_value)))

    irr = _xirr(cashflows)
    return (irr * 100.0) if irr is not None else 0.0


def compute_twr(
    transactions_df: pd.DataFrame,
    price_map: Dict[str, float],
    net_deposit: float,
    as_of_date: Optional[str] = None,
) -> float:
    if transactions_df is None or transactions_df.empty:
        return 0.0

    df = transactions_df.copy()
    df = stocks_split_adjustments(df)
    df[Columns.DATE] = to_dt(df[Columns.DATE])
    df = df.sort_values([Columns.DATE, "id"] if "id" in df.columns else [Columns.DATE])
    if as_of_date:
        as_of_dt = pd.to_datetime(as_of_date, errors="coerce")
        if not pd.isna(as_of_dt):
            df = df[df[Columns.DATE] <= as_of_dt]

    qty_by_code: Dict[str, float] = {}
    last_price_by_code: Dict[str, float] = {}
    prev_value = None
    twr = 1.0

    for date, g in df.groupby(Columns.DATE, sort=True):
        # start-of-period value
        if prev_value is None:
            prev_value = float(net_deposit)

        # apply trades and compute cash flow on this date
        cash_flow = 0.0
        for _, r in g.iterrows():
            code = str(r[Columns.STOCK_CODE])
            qty = float(r[Columns.QUANTITY])
            price = float(r[Columns.PRICE_PER_SHARE])
            amt = r.get(Columns.TOTAL_AMOUNT, 0) or 0
            fee = r.get(Columns.FEE, 0) or 0
            try:
                amt = float(amt)
            except Exception:
                amt = 0.0
            try:
                fee = float(fee)
            except Exception:
                fee = 0.0

            if r[Columns.TRADE_TYPE] == TradeType.BUY:
                qty_by_code[code] = qty_by_code.get(code, 0.0) + qty
                cash_flow += (amt + fee)
            elif r[Columns.TRADE_TYPE] == TradeType.SELL:
                qty_by_code[code] = qty_by_code.get(code, 0.0) - qty
                cash_flow -= (amt - fee)

            last_price_by_code[code] = price

        # end-of-period value using last trade prices
        holdings_value = 0.0
        for c, q in qty_by_code.items():
            if q <= 0:
                continue
            px = last_price_by_code.get(c)
            if px is None:
                continue
            holdings_value += q * px
        end_value = holdings_value + float(net_deposit)

        if prev_value > 0:
            period_return = (end_value - cash_flow) / prev_value - 1.0
            twr *= (1.0 + period_return)
        prev_value = end_value

    # adjust last value to as-of price_map if provided
    if price_map:
        holdings_value = 0.0
        for c, q in qty_by_code.items():
            if q <= 0:
                continue
            px = price_map.get(str(c))
            if px is None:
                continue
            holdings_value += q * px
        end_value = holdings_value + float(net_deposit)
        if prev_value and prev_value > 0:
            period_return = (end_value / prev_value) - 1.0
            twr *= (1.0 + period_return)

    return (twr - 1.0) * 100.0
