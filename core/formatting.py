from __future__ import annotations


def yen(x) -> str:
    try:
        return f"¥{int(round(float(x))):,}"
    except Exception:
        return "¥0"


def pct(x) -> str:
    try:
        return f"{float(x):.2f}%"
    except Exception:
        return "0.00%"
