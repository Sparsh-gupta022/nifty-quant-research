"""Load, clean and validate NIFTY 50 daily OHLC data.

Cleaning policy (see docs/DECISIONS.md):
- Raw file is never modified; cleaning happens here only.
- Rows are sorted ascending by date (source delivers newest-first).
- Invalid rows (unparseable date, missing/non-positive price, High/Low inconsistent,
  duplicate date) raise DataValidationError -- nothing is silently dropped.
- Calendar gaps are reported, not filled (market holidays are not missing data).
- Suspicious Opens (Open == previous Close, or Open exactly at the day's High/Low) are
  flagged, not changed. They are common before ~2011 and matter for next-day-Open entry.
"""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

PRICE_COLS = ["Open", "High", "Low", "Close"]


class DataValidationError(ValueError):
    pass


@dataclass
class ValidationReport:
    n_rows: int
    start: pd.Timestamp
    end: pd.Timestamp
    was_sorted_ascending: bool
    gaps: pd.DataFrame
    rows_per_year: pd.Series
    suspicious_open_by_year: pd.DataFrame
    largest_moves: pd.DataFrame
    errors: list = field(default_factory=list)

    def summary(self) -> str:
        return "\n".join([
            f"Rows: {self.n_rows}  |  Coverage: {self.start.date()} -> {self.end.date()}",
            f"Source sorted ascending: {self.was_sorted_ascending} (re-sorted ascending)",
            f"Calendar gaps > {GAP_DAYS} days: {len(self.gaps)} (max {int(self.gaps['days'].max()) if len(self.gaps) else 0} days)",
            f"Trading days per full year: min {self.rows_per_year.iloc[:-1].min()}, max {self.rows_per_year.iloc[:-1].max()}",
            f"Validation errors: {len(self.errors)}",
        ])


GAP_DAYS = 4


def load_raw(path: str | Path) -> pd.DataFrame:
    """Parse the niftyindices raw CSV into Date + numeric OHLC, keeping source order."""
    raw = pd.read_csv(path, dtype=str)
    df = pd.DataFrame({"Date": pd.to_datetime(raw["HistoricalDate"], format="%d %b %Y", errors="coerce")})
    for col in PRICE_COLS:
        df[col] = pd.to_numeric(raw[col.upper()].str.replace(",", ""), errors="coerce")
    return df


def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, ValidationReport]:
    """Validate and sort. Raises DataValidationError on any invalid row."""
    errors = []
    if df["Date"].isna().any():
        errors.append(f"{df['Date'].isna().sum()} unparseable dates")
    if df[PRICE_COLS].isna().any().any():
        errors.append(f"missing prices: {df[PRICE_COLS].isna().sum().to_dict()}")
    if (df[PRICE_COLS] <= 0).any().any():
        errors.append(f"{(df[PRICE_COLS] <= 0).any(axis=1).sum()} rows with non-positive prices")
    if df["Date"].duplicated().any():
        errors.append(f"{df['Date'].duplicated().sum()} duplicate dates")
    bad_hl = (df["High"] < df[["Open", "Close", "Low"]].max(axis=1)) | (df["Low"] > df[["Open", "Close", "High"]].min(axis=1))
    if bad_hl.any():
        errors.append(f"{bad_hl.sum()} rows where High/Low don't bound Open/Close, e.g. {df.loc[bad_hl, 'Date'].head(3).dt.date.tolist()}")
    if errors:
        raise DataValidationError("; ".join(errors))

    was_sorted = df["Date"].is_monotonic_increasing
    df = df.sort_values("Date").reset_index(drop=True)

    gap_days = df["Date"].diff().dt.days
    gaps = pd.DataFrame({"from": df["Date"].shift()[gap_days > GAP_DAYS], "to": df["Date"][gap_days > GAP_DAYS],
                         "days": gap_days[gap_days > GAP_DAYS]}).reset_index(drop=True)

    df = add_open_flags(df)
    by_year = df.groupby(df["Date"].dt.year).agg(
        days=("Close", "size"),
        open_eq_prev_close=("open_eq_prev_close", "mean"),
        open_at_high_or_low=("open_at_high_or_low", "mean"),
    )

    ret = df["Close"].pct_change()
    largest = pd.concat([df.assign(ret=ret).nsmallest(5, "ret"), df.assign(ret=ret).nlargest(5, "ret")])[["Date", "ret"]]

    report = ValidationReport(
        n_rows=len(df), start=df["Date"].iloc[0], end=df["Date"].iloc[-1], was_sorted_ascending=was_sorted,
        gaps=gaps, rows_per_year=by_year["days"], suspicious_open_by_year=by_year,
        largest_moves=largest.reset_index(drop=True), errors=errors,
    )
    return df, report


def add_open_flags(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["open_eq_prev_close"] = np.isclose(df["Open"], df["Close"].shift())
    df["open_at_high_or_low"] = (df["Open"] == df["High"]) | (df["Open"] == df["Low"])
    df["suspicious_open"] = df["open_eq_prev_close"] | df["open_at_high_or_low"]
    return df


def load_clean(path: str | Path) -> tuple[pd.DataFrame, ValidationReport]:
    return validate(load_raw(path))
