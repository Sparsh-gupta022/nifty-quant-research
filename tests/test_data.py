import pandas as pd
import pytest

from src.data import DataValidationError, validate


def _frame(**overrides):
    df = pd.DataFrame({
        "Date": pd.to_datetime(["2024-01-03", "2024-01-02", "2024-01-01"]),
        "Open": [101.0, 100.0, 99.0], "High": [102.0, 101.0, 100.0],
        "Low": [100.0, 99.0, 98.0], "Close": [101.5, 100.5, 99.5],
    })
    for col, (i, v) in overrides.items():
        df.loc[i, col] = v
    return df


def test_valid_frame_is_sorted_ascending():
    df, report = validate(_frame())
    assert df["Date"].is_monotonic_increasing
    assert not report.was_sorted_ascending


@pytest.mark.parametrize("col,value", [("Close", None), ("Open", 0.0), ("High", 50.0)])
def test_invalid_rows_fail_loudly(col, value):
    with pytest.raises(DataValidationError):
        validate(_frame(**{col: (1, value)}))


def test_duplicate_dates_fail_loudly():
    with pytest.raises(DataValidationError):
        validate(_frame(Date=(0, pd.Timestamp("2024-01-02"))))
