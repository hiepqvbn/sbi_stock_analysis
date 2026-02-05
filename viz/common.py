# viz/common.py
from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go


def ensure_sorted(df: pd.DataFrame) -> pd.DataFrame:
    if "date" in df.columns:
        # stable ordering (important when same-day buy/sell)
        sort_cols = ["date"] + (["id"] if "id" in df.columns else [])
        return df.sort_values(sort_cols).reset_index(drop=True)
    return df.sort_index().reset_index(drop=True)


def base_layout(fig: go.Figure, title: str, x_title: str, y_title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        template="plotly_white",
        legend_title="Metric",
    )
    return fig
