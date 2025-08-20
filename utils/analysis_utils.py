import pandas as pd
from typing import Dict, Any, Union

def analyze_stock_performance(
    df: pd.DataFrame,
    stock: str,
    current_price: float,
    plot: bool = False
) -> Dict[str, Union[float, int, Dict[str, float], Any]]:
    """
    Analyze stock performance from transaction data.

    Args:
        df: DataFrame with columns ['stock_name','trade_type','quantity','price_per_share','total_amount']
        stock: Stock name (str)
        current_price: Latest market price (float)
        plot: If True, returns a plotly figure as 'plot' key in result

    Returns:
        Dictionary with buy/sell stats, realized/unrealized/total profit, and optional plot
    """
    # Filter for the selected stock
    stock_df = df[df['stock_name'] == stock].copy()
    buy_mask = stock_df['trade_type'].str.contains('買')
    sell_mask = stock_df['trade_type'].str.contains('売')

    # Buy stats
    total_buy_qty = stock_df.loc[buy_mask, 'quantity'].sum()
    total_buy_amount = stock_df.loc[buy_mask, 'total_amount'].sum()
    avg_buy_price = (total_buy_amount / total_buy_qty) if total_buy_qty > 0 else 0

    # Sell stats
    total_sell_qty = stock_df.loc[sell_mask, 'quantity'].sum()
    total_sell_amount = stock_df.loc[sell_mask, 'total_amount'].sum()

    # Realized profit (absolute and %)
    if total_buy_qty > 0:
        realized_profit = total_sell_amount - total_sell_qty * avg_buy_price
        realized_profit_pct = (realized_profit / (total_sell_qty * avg_buy_price) * 100) if total_sell_qty > 0 else 0
    else:
        realized_profit = 0
        realized_profit_pct = 0

    # Unrealized profit (absolute and %)
    holding_qty = total_buy_qty - total_sell_qty
    holding_cost = holding_qty * avg_buy_price
    holding_value = holding_qty * current_price
    unrealized_profit = holding_value - holding_cost
    unrealized_profit_pct = (unrealized_profit / holding_cost * 100) if holding_cost > 0 else 0

    # Total profit
    total_profit = realized_profit + unrealized_profit
    total_profit_pct = ((total_profit / (total_buy_qty * avg_buy_price)) * 100) if total_buy_qty > 0 else 0

    result = {
        "total_buy_qty": int(total_buy_qty),
        "total_buy_amount": float(total_buy_amount),
        "avg_buy_price": float(avg_buy_price),
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
    }

    # Optional: Plot cumulative profit and holding value over time
    if plot and not stock_df.empty:
        import plotly.graph_objs as go

        stock_df = stock_df.sort_values("date") if "date" in stock_df.columns else stock_df.sort_index()
        stock_df['signed_amount'] = stock_df.apply(
            lambda row: -row['total_amount'] if '買' in row['trade_type']
            else row['total_amount'] if '売' in row['trade_type']
            else 0,
            axis=1
        )
        stock_df['cumulative_profit'] = stock_df['signed_amount'].cumsum()
        stock_df['signed_qty'] = stock_df.apply(
            lambda row: row['quantity'] if '買' in row['trade_type']
            else -row['quantity'] if '売' in row['trade_type']
            else 0,
            axis=1
        )
        stock_df['holding_qty'] = stock_df['signed_qty'].cumsum()
        stock_df['holding_value'] = stock_df['holding_qty'] * current_price

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=stock_df["date"] if "date" in stock_df.columns else stock_df.index,
            y=stock_df['cumulative_profit'],
            mode='lines+markers',
            name='Cumulative Profit'
        ))
        fig.add_trace(go.Scatter(
            x=stock_df["date"] if "date" in stock_df.columns else stock_df.index,
            y=stock_df['holding_value'],
            mode='lines+markers',
            name='Holding Value (at current price)'
        ))
        fig.update_layout(
            title=f"{stock} Performance",
            xaxis_title="Date" if "date" in stock_df.columns else "Transaction Index",
            yaxis_title="Yen",
            legend_title="Metric"
        )
        result['plot'] = fig

    return result