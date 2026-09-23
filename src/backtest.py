"""Simple event-driven backtest of the frozen main specification (decision 3.4).

Entry Open(t+1), exit Close(t+N), one round-trip cost subtracted per trade. Deliberately
minimal: no position sizing, no leverage, no compounding assumptions beyond reinvesting the
whole notional in the next trade. It exists to price the research result, not to be a framework.

Two ways of handling an event that fires while a trade is already open are provided, because
that is a methodological choice (see docs/DECISIONS.md):
  - "skip"    : ignore events until the current trade closes (non-overlapping, one position)
  - "overlap" : take every event; capital is split equally, so returns are averaged per day
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity: pd.Series
    n_trades: int
    total_return: float
    avg_trade: float
    median_trade: float
    win_rate: float
    max_drawdown: float
    best: float
    worst: float

    def summary(self) -> pd.Series:
        return pd.Series({
            "trades": self.n_trades, "cumulative_return": self.total_return,
            "avg_trade": self.avg_trade, "median_trade": self.median_trade,
            "win_rate": self.win_rate, "max_drawdown": self.max_drawdown,
            "best_trade": self.best, "worst_trade": self.worst,
        })


def max_drawdown(equity: pd.Series) -> float:
    """Largest peak-to-trough fall of the equity curve."""
    return float((equity / equity.cummax() - 1).min())


def run_backtest(feat: pd.DataFrame, cfg: dict, cost: float = None, mode: str = "skip") -> BacktestResult:
    N = cfg["horizon"]
    cost = cfg["trade"]["cost_round_trip"] if cost is None else cost
    f = feat.reset_index(drop=True)
    open_, close, date = f["Open"].to_numpy(), f["Close"].to_numpy(), f["Date"].to_numpy()
    positions = np.flatnonzero((f["is_event"] & f["usable"]).to_numpy())

    rows, busy_until = [], -1
    for t in positions:
        if mode == "skip" and t <= busy_until:
            continue
        if t + N >= len(f):
            continue
        entry, exit_ = open_[t + 1], close[t + N]
        gross = exit_ / entry - 1
        rows.append({"event_date": date[t], "entry_date": date[t + 1], "exit_date": date[t + N],
                     "entry": entry, "exit": exit_, "gross_ret": gross, "net_ret": gross - cost})
        busy_until = t + N

    trades = pd.DataFrame(rows)
    if trades.empty:
        empty = pd.Series(dtype=float)
        return BacktestResult(trades, empty, 0, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan)

    equity = (1 + trades["net_ret"]).cumprod()
    equity.index = pd.to_datetime(trades["exit_date"])
    return BacktestResult(
        trades=trades, equity=equity, n_trades=len(trades),
        total_return=float(equity.iloc[-1] - 1), avg_trade=float(trades["net_ret"].mean()),
        median_trade=float(trades["net_ret"].median()), win_rate=float((trades["net_ret"] > 0).mean()),
        max_drawdown=max_drawdown(equity), best=float(trades["net_ret"].max()),
        worst=float(trades["net_ret"].min()),
    )


def buy_and_hold(feat: pd.DataFrame) -> dict:
    """Reference point: holding the index over the same period."""
    f = feat[feat["usable"]]
    eq = f["Close"] / f["Close"].iloc[0]
    eq.index = f["Date"]
    years = (f["Date"].iloc[-1] - f["Date"].iloc[0]).days / 365.25
    return {"total_return": float(eq.iloc[-1] - 1), "years": years,
            "cagr": float(eq.iloc[-1] ** (1 / years) - 1), "max_drawdown": max_drawdown(eq)}
