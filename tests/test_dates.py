import pandas as pd

from core.dates import slice_by_date
from core.constants import Columns


def test_slice_by_date_range():
    df = pd.DataFrame(
        {
            Columns.DATE: ["2024-01-01", "2024-02-01", "2024-03-01"],
            "value": [1, 2, 3],
        }
    )

    out = slice_by_date(df, start_date="2024-02-01", end_date="2024-03-01")
    assert out["value"].tolist() == [2, 3]

    out2 = slice_by_date(df, start_date=None, end_date="2024-02-01")
    assert out2["value"].tolist() == [1, 2]
