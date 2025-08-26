import pandas as pd
from typing import Dict, Any, Union
import numpy as np
import yfinance

def get_stock_current_price(stock_code: str) -> float | None:
    """
    Fetch the latest stock price using yfinance.

    Args:
        stock_code: Stock code (str)

    Returns:
        Latest closing price (float) or 0 if not found/error
    """
    ticker = f"{stock_code}.T"
    try:
        today_price = yfinance.Ticker(ticker).history(period="1d")["Close"].iloc[0]
        return float(today_price)
    except Exception as e:
        print(f"Warning: Failed to retrieve current price for {stock_code}: {e}")
        return None

def record_stock_split_adjustments(df: pd.DataFrame, stock_code) -> pd.DataFrame:
    stock_df = df[df["stock_code"] == stock_code]
    ticker = f"{stock_code}.T"
    try:
        splits = yfinance.Ticker(ticker).splits
        if not splits.empty:
            for split_date, split_ratio in splits.items():
                stock_df.loc[pd.to_datetime(stock_df['date']).dt.tz_localize(
                    'UTC') < split_date, 'quantity'] *= split_ratio
                stock_df.loc[pd.to_datetime(stock_df['date']).dt.tz_localize(
                    'UTC') < split_date, 'price_per_share'] /= split_ratio
        return stock_df
    except Exception as e:
        print(f"Warning: Failed to retrieve stock splits: {e}")
        return stock_df


def analyze_stock_performance(
    df: pd.DataFrame,
    stock_code: str,
    current_price: float,
    plot: bool = False
) -> Dict[str, Union[float, int, Dict[str, float], Any]]:
    """
    Analyze stock performance from transaction data.

    Args:
        df: DataFrame with columns ['stock_code','stock_name','trade_type','quantity','price_per_share','total_amount',...]
        stock_code: Stock code (str)
        current_price: Latest market price (float)
        plot: If True, returns a plotly figure as 'plot' key in result

    Returns:
        Dictionary with buy/sell stats, realized/unrealized/total profit, and optional plot
    """
    # Filter for the selected stock_code
    stock_df = df[df['stock_code'] == stock_code].copy()
    # Get all names used for this code (for display)
    stock_names = stock_df["stock_name"].unique()
    names_str = ", ".join(stock_names)

    buy_mask = stock_df['trade_type'].str.lower().str.contains('buy')
    sell_mask = stock_df['trade_type'].str.lower().str.contains('sell')

    # Buy stats
    total_buy_qty = stock_df.loc[buy_mask, 'quantity'].sum()
    total_buy_amount = stock_df.loc[buy_mask, 'total_amount'].sum()
    avg_buy_price = (total_buy_amount /
                     total_buy_qty) if total_buy_qty > 0 else 0

    # Sell stats
    total_sell_qty = stock_df.loc[sell_mask, 'quantity'].sum()
    total_sell_amount = stock_df.loc[sell_mask, 'total_amount'].sum()
    avg_sell_price = (total_sell_amount /
                      total_sell_qty) if total_sell_qty > 0 else 0

    # Realized profit (absolute and %)
    if total_buy_qty > 0:
        realized_profit = total_sell_amount - total_sell_qty * avg_buy_price
        realized_profit_pct = (
            realized_profit / (total_sell_qty * avg_buy_price) * 100) if total_sell_qty > 0 else 0
    else:
        realized_profit = 0
        realized_profit_pct = 0

    # Unrealized profit (absolute and %)
    holding_qty = total_buy_qty - total_sell_qty
    holding_cost = holding_qty * avg_buy_price
    holding_value = holding_qty * current_price
    unrealized_profit = holding_value - holding_cost
    unrealized_profit_pct = (
        unrealized_profit / holding_cost * 100) if holding_cost > 0 else 0

    # Total profit
    total_profit = realized_profit + unrealized_profit
    total_profit_pct = ((total_profit / (total_buy_qty *
                        avg_buy_price)) * 100) if total_buy_qty > 0 else 0

    break_even_point_price = (
        total_buy_amount - total_sell_amount) / holding_qty if holding_qty > 0 else 0
    break_even_point_price = break_even_point_price if break_even_point_price > 0 else 0

    result = {
        "stock_code": stock_code,
        "stock_names": names_str,
        "total_buy_qty": int(total_buy_qty),
        "total_buy_amount": float(total_buy_amount),
        "avg_buy_price": float(avg_buy_price),
        "avg_sell_price": float(avg_sell_price),
        "total_sell_qty": int(total_sell_qty),
        "total_sell_amount": float(total_sell_amount),
        "realized_profit": float(realized_profit),
        "realized_profit_pct": float(realized_profit_pct),
        "unrealized_profit": float(unrealized_profit),
        "unrealized_profit_pct": float(unrealized_profit_pct),
        "total_profit": float(total_profit),
        "total_profit_pct": float(total_profit_pct),
        "holding_qty": int(holding_qty),
        "holding_value": float(holding_value),
        "break_even_point_price": float(break_even_point_price),
    }

    def compute_realized_profit(df):
        realized_profits = []
        avg_cost = 0
        holding_qty = 0
        realized_profit = 0

        for idx, row in df.iterrows():
            qty = row['quantity']
            price = row['price_per_share']
            trade_type = row['trade_type'].lower()

            if 'buy' in trade_type:
                # Update average cost
                total_cost = avg_cost * holding_qty + price * qty
                holding_qty += qty
                avg_cost = total_cost / holding_qty if holding_qty > 0 else 0
                realized_profits.append(realized_profit)
            elif 'sell' in trade_type:
                # Realized profit for this sale
                if holding_qty >= qty:
                    profit = (price - avg_cost) * qty
                    realized_profit += profit
                    holding_qty -= qty
                else:
                    # Selling more than holding, treat as all you have
                    profit = (price - avg_cost) * holding_qty
                    realized_profit += profit
                    holding_qty = 0
                realized_profits.append(realized_profit)
            else:
                realized_profits.append(realized_profit)
        return realized_profits

    # Optional: Plot cumulative profit and holding value over time
    if plot and not stock_df.empty:
        import plotly.graph_objs as go

        stock_df = stock_df.sort_values(
            "date") if "date" in stock_df.columns else stock_df.sort_index()
        stock_df['signed_qty'] = stock_df.apply(
            lambda row: row['quantity'] if 'buy' in row['trade_type'].lower()
            else -row['quantity'] if 'sell' in row['trade_type'].lower()
            else 0,
            axis=1
        )
        stock_df['holding_qty'] = stock_df['signed_qty'].cumsum()
        stock_df['holding_value'] = stock_df['holding_qty'] * \
            stock_df['price_per_share']

        # Calculate realized profit over time
        stock_df['realized_profit'] = compute_realized_profit(stock_df)

        # Add today point
        if "date" in stock_df.columns:
            today = pd.Timestamp.today().normalize()
            last_date = pd.to_datetime(stock_df["date"].max())
            if today > last_date:
                today_row = {
                    "date": today,
                    "realized_profit": stock_df['realized_profit'].iloc[-1],
                    "holding_qty": stock_df['holding_qty'].iloc[-1],
                    "holding_value": stock_df['holding_qty'].iloc[-1] * current_price
                }
                stock_df = pd.concat(
                    [stock_df, pd.DataFrame([today_row])], ignore_index=True)
        else:
            today_row = {
                "realized_profit": stock_df['realized_profit'].iloc[-1],
                "holding_qty": stock_df['holding_qty'].iloc[-1],
                "holding_value": stock_df['holding_qty'].iloc[-1] * current_price
            }
            stock_df = pd.concat(
                [stock_df, pd.DataFrame([today_row])], ignore_index=True)

        stock_df['total_equity'] = stock_df['realized_profit'] + \
            stock_df['holding_value']

        x_axis = stock_df["date"] if "date" in stock_df.columns else stock_df.index

        fig_1 = go.Figure()
        fig_1.add_trace(go.Scatter(
            x=x_axis,
            y=stock_df['realized_profit'],
            mode='lines+markers',
            name='Realized Profit'
        ))
        fig_1.add_trace(go.Scatter(
            x=x_axis,
            y=stock_df['holding_value'],
            mode='lines+markers',
            name='Holding Value'
        ))
        fig_1.add_trace(go.Scatter(
            x=x_axis,
            y=stock_df['total_equity'],
            mode='lines+markers',
            name='Total Equity (Profit + Holding)'
        ))
        fig_1.update_layout(
            title=f"{names_str} ({stock_code}) Performance",
            xaxis_title="Date" if "date" in stock_df.columns else "Transaction Index",
            yaxis_title="Yen",
            legend_title="Metric"
        )

        # --- Figure 1: Price & Transactions ---
        fig_price = go.Figure()

        # Scatter plot: buys
        buys = stock_df[stock_df["trade_type"] == "Buy"]
        fig_price.add_trace(go.Scatter(
            x=buys["date"], y=buys["price_per_share"],
            mode="markers", name="Buy",
            marker=dict(color="green", size=10, symbol="triangle-up")
        ))

        # Scatter plot: sells
        sells = stock_df[stock_df["trade_type"] == "Sell"]
        fig_price.add_trace(go.Scatter(
            x=sells["date"], y=sells["price_per_share"],
            mode="markers", name="Sell",
            marker=dict(color="red", size=10, symbol="triangle-down")
        ))

        # Average cost line
        stock_df['avg_cost'] = np.nan
        stock_df['qty'] = np.nan
        stock_df['cash_flow'] = np.nan

        stock_df['cumulative_profit'] = np.nan
        stock_df['total_equity'] = np.nan

        stock_df['realized_step'] = np.nan
        stock_df['realized_pnl'] = np.nan
        stock_df['unrealized_profit'] = np.nan
        stock_df['total_pnl'] = np.nan
        stock_df['return_pct'] = np.nan
        # --- Running position & PnL using MOVING AVERAGE COST BASIS ---
        qty = 0.0  # current held quantity
        avg_cost = 0.0
        total_cost = 0.0  # book cost of current holdings = avg_cost * qty
        realized_pnl = 0.0
        cum_buys = 0.0   # total capital deployed (sum of buy cash outflows)
        for i, r in stock_df.iterrows():
            action = r['trade_type']
            sh = r['quantity']
            px = r['price_per_share']
            profit = r['total_amount']

            if i > 0:
                cumulative_profit = stock_df['cumulative_profit'].iloc[i - 1]
            else:
                cumulative_profit = 0.0

            if action == 'Buy':
                # cash flow (negative = outflow)
                cash_flow = -px * sh
                cum_buys += px * sh

                # update average cost
                new_qty = qty + sh
                if new_qty <= 0:
                    # should never happen on buy
                    raise ValueError(
                        "Invalid state: non-positive qty after BUY")

                total_cost = total_cost + px * sh
                avg_cost = total_cost / new_qty
                qty = new_qty

                cumulative_profit -= profit

                trade_realized = 0.0

            elif action == 'Sell':
                if sh > qty:
                    raise ValueError(
                        f"Selling more than held: sell {sh}, held {qty}")

                # cash flow (positive = inflow)
                cash_flow = px * sh

                # realized using current avg_cost
                trade_realized = (px - avg_cost) * sh
                realized_pnl += trade_realized

                # reduce book cost & qty
                total_cost = total_cost - avg_cost * sh
                qty = qty - sh

                cumulative_profit += profit

                # if position closed, reset avg_cost + total_cost to clean state
                if qty == 0:
                    avg_cost = 0.0
                    total_cost = 0.0
            else:
                # ignore unknown action
                cash_flow = 0.0

            # At each step, compute unrealized at EXPECTED price (a what-if snapshot)
            holding_value = stock_df['holding_value'].iloc[i]
            unrealized = cumulative_profit + holding_value
            total = realized_pnl + holding_value
            total_pnl = realized_pnl + unrealized

            # Return % relative to total deployed capital (guard divide by zero)
            ret_pct = (total_pnl / cum_buys * 100.0) if cum_buys > 0 else 0.0

            stock_df['avg_cost'].iloc[i] = avg_cost if qty > 0 else None
            stock_df['qty'].iloc[i] = qty
            stock_df['cash_flow'].iloc[i] = cash_flow
            stock_df['realized_step'].iloc[i] = trade_realized
            stock_df['realized_pnl'].iloc[i] = realized_pnl
            stock_df['unrealized_profit'].iloc[i] = unrealized
            stock_df['total_pnl'].iloc[i] = total_pnl
            stock_df['return_pct'].iloc[i] = ret_pct

            stock_df['cumulative_profit'].iloc[i] = cumulative_profit
            stock_df['total_equity'].iloc[i] = total

        # Moving average cost (step-like line: avg changes only on BUY)
        fig_price.add_trace(go.Scatter(
            x=stock_df['date'], y=stock_df['avg_cost'],
            mode='lines', name='Avg Cost (moving average)'
        ))

        # Expected price point
        fig_price.add_hline(y=current_price, line_dash="dash",
                            line_color="orange", annotation_text="Expected Price")

        fig_price.update_layout(
            title="Stock Price & Transactions",
            xaxis_title="Date",
            yaxis_title="Price (¥)",
            template="plotly_white"
        )

        # --- Figure 2: Performance ---
        # Cash flow & holdings
        # df["cash_flow"] = df.apply(lambda r: -r["price"]*r["shares"] if r["action"]=="BUY" else r["price"]*r["shares"], axis=1)
        # df["cum_cash"] = df["cash_flow"].cumsum()

        # # Unrealized value (if still holding)
        # df["cum_shares"] = df.apply(lambda r: r["shares"] if r["action"]=="BUY" else -r["shares"], axis=1).cumsum()
        # df["equity"] = df["cum_cash"] + df["cum_shares"] * expected_price

        # initial_invest = -df[df["action"]=="BUY"]["cash_flow"].sum()
        # df["return_pct"] = (df["equity"] - initial_invest) / initial_invest * 100

        # fig_perf = go.Figure()

        # fig_perf.add_trace(go.Scatter(
        #     x=df["date"], y=df["equity"],
        #     mode="lines+markers", name="Equity (¥)", line=dict(color="blue")
        # ))

        # fig_perf.add_trace(go.Scatter(
        #     x=df["date"], y=df["return_pct"],
        #     mode="lines+markers", name="Return (%)", yaxis="y2", line=dict(color="orange")
        # ))

        # fig_perf.update_layout(
        #     title="Portfolio Performance",
        #     xaxis_title="Date",
        #     yaxis=dict(title="Equity (¥)"),
        #     yaxis2=dict(title="Return (%)", overlaying="y", side="right"),
        #     template="plotly_white"
        # )
        # print(stock_df[[
        #     "date", "trade_type", "quantity", "price_per_share","cash_flow"
        # ]].tail(3))  # Debug: print last few rows to verify
        fig_perf = go.Figure()

        # Draw dash line at 0
        fig_perf.add_hline(y=0, line_dash="dash", line_color="gray")

        # --- Cash flow bars ---
        # buy=red, sell=green
        colors = ['red' if x < 0 else 'green' for x in stock_df['cash_flow']]
        fig_perf.add_trace(go.Bar(
            x=stock_df['date'],
            y=stock_df['cash_flow'],
            name='Cash Flow (buy=- / sell=+)',
            marker_color=colors,
            opacity=0.7,
        ))

        # --- Cumulative Profit line ---
        fig_perf.add_trace(go.Scatter(
            x=stock_df['date'],
            y=stock_df['cumulative_profit'],
            mode='lines+markers',
            name='Cumulative Profit (¥)',
            line=dict(color='blue'),
            yaxis='y1'
        ))
        # --- Holding value line ---
        fig_perf.add_trace(go.Scatter(
            x=stock_df['date'],
            y=stock_df['holding_value'],
            mode='lines+markers',
            name='Stock Holding Value (¥)',
            line=dict(color='green'),
            yaxis='y1'
        ))
        # --- Realize profit ---
        fig_perf.add_trace(go.Scatter(
            x=stock_df['date'],
            y=stock_df['realized_profit'],
            mode='lines+markers',
            name='Realized Profit (¥)',
            line=dict(color='purple'),
            yaxis='y1'
        ))

        # --- Unrealized profit ---
        fig_perf.add_trace(go.Scatter(
            x=stock_df['date'],
            y=stock_df['unrealized_profit'],
            mode='lines+markers',
            name='Unrealized Profit (¥)',
            line=dict(color='orange'),
            yaxis='y1'
        ))
        # --- Total equity ---
        fig_perf.add_trace(go.Scatter(
            x=stock_df['date'],
            y=stock_df['total_equity'],
            mode='lines+markers',
            name='Total Equity (¥)',
            line=dict(color='black'),
            yaxis='y1'
        ))
        # --- Return % line (secondary y-axis) ---
        # fig_perf.add_trace(go.Scatter(
        #     x=stock_df['date'],
        #     y=stock_df['return_pct'],
        #     mode='lines+markers',
        #     name='Return (%)',
        #     line=dict(color='orange'),
        #     yaxis='y2'
        # ))

        # --- Layout ---
        fig_perf.update_layout(
            title='Performance (Cumulative P&L & Return %) with Cash Flows',
            xaxis=dict(title='Date'),
            yaxis=dict(
                title='Cumulative P&L (¥)',
                side='left',
            ),
            yaxis2=dict(
                title='Return (%)',
                overlaying='y',
                side='right',
            ),
            barmode='relative',
            template='plotly_white'
        )

        result['plots'] = fig_price, fig_perf

    return result
