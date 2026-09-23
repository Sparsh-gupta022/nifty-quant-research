"""Research engine: event detection, recovery, forward returns, baseline and inference.

Every rule is read from config.yaml (see docs/DECISIONS.md for the reasoning behind each):

  3.1  event      : return(t) < -k * sigma(t-60..t-1)
  3.2  recovery   : any Close in t+1..t+N >= event Close + fraction * (prev Close - event Close)
  3.2a baseline   : same target expressed in sigma units, applied to non-event days
  3.3  horizon    : N trading days, window fixed from the event date
  3.4  trade      : entry Open(t+1), exit Close(t+N)
  3.5  episodes   : new episode when > gap trading days since the previous event
  3.6  baseline   : non-event days, post-event days kept
  3.6b inference  : whole-series block bootstrap of (event_mean - baseline_mean)
  3.7  split      : development vs out-of-sample by date
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.data import load_clean

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: str | Path = None) -> dict:
    with open(path or ROOT / "config.yaml") as fh:
        return yaml.safe_load(fh)


# --------------------------------------------------------------------------- features


def build_features(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Per-day quantities used by every later step. All forward-looking columns are
    computed from prices strictly after day t, so nothing here leaks into the signal."""
    n = len(df)
    N = cfg["horizon"]
    close, open_ = df["Close"].to_numpy(), df["Open"].to_numpy()

    out = df.copy()
    out["ret"] = out["Close"].pct_change()
    # sigma uses t-window .. t-1 only (shift(1) excludes day t itself)
    out["sigma"] = out["ret"].rolling(cfg["event"]["sigma_window"]).std().shift(1)
    out["is_event"] = (out["ret"] < -cfg["event"]["threshold_sigma"] * out["sigma"]).fillna(False)

    # forward return of the trade: Open(t+1) -> Close(t+N)
    fwd = np.full(n, np.nan)
    if n > N:
        fwd[: n - N] = close[N:] / open_[1 : n - N + 1] - 1
    out["fwd_ret"] = fwd

    # maximum Close reached in t+1..t+N, as a fraction above Close(t)
    max_fwd = np.full(n, np.nan)
    for t in range(n - N):
        max_fwd[t] = close[t + 1 : t + 1 + N].max() / close[t] - 1
    out["max_fwd_gain"] = max_fwd
    # same quantity in sigma units: how far the market ran up, relative to normal daily moves
    out["max_fwd_gain_sigma"] = out["max_fwd_gain"] / out["sigma"]

    # recovery target for a day, in sigma units (3.2 / 3.2a):
    #   level = Close(t) + fraction * (Close(t-1) - Close(t));  k = (level/Close(t) - 1) / sigma
    prev_close = out["Close"].shift(1)
    loss = prev_close - out["Close"]
    level = out["Close"] + cfg["recovery"]["fraction"] * loss
    out["target_k"] = (level / out["Close"] - 1) / out["sigma"]

    out["usable"] = out["sigma"].notna() & out["fwd_ret"].notna() & out["max_fwd_gain"].notna()
    return out


def assign_episodes(is_event: pd.Series, gap: int) -> pd.Series:
    """3.5 - consecutive events more than `gap` trading days apart start a new episode."""
    episode = pd.Series(np.nan, index=is_event.index)
    idx = np.flatnonzero(is_event.to_numpy())
    if len(idx):
        episode.iloc[idx] = np.cumsum(np.r_[0, np.diff(idx) > gap])
    return episode


def build_events(feat: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """One row per event, with everything the assignment asks to report per event."""
    ev = feat[feat["is_event"] & feat["usable"]].copy()
    ev["recovered"] = ev["max_fwd_gain_sigma"] >= ev["target_k"]
    ev["entry_price"] = feat["Open"].shift(-1).loc[ev.index]
    ev["exit_price"] = feat["Close"].shift(-cfg["horizon"]).loc[ev.index]
    ev["net_ret"] = ev["fwd_ret"] - cfg["trade"]["cost_round_trip"]
    ev["episode"] = assign_episodes(feat["is_event"] & feat["usable"], cfg["episode_gap_days"]).loc[ev.index]
    cols = ["Date", "Close", "ret", "sigma", "target_k", "entry_price", "exit_price",
            "fwd_ret", "net_ret", "recovered", "episode", "suspicious_open"]
    return ev[cols].reset_index(drop=True)


# --------------------------------------------------------------------------- statistics


def _baseline_recovery_rate(target_k: np.ndarray, base_gain_sigma: np.ndarray) -> float:
    """3.2a - for each event target (in sigma units), the share of baseline days whose own
    5-day run-up reaches that same sigma-distance; averaged across events."""
    if len(target_k) == 0 or len(base_gain_sigma) == 0:
        return np.nan
    srt = np.sort(base_gain_sigma)
    # share of baseline days with gain >= k, for every k at once
    hits = len(srt) - np.searchsorted(srt, target_k, side="left")
    return float(np.mean(hits / len(srt)))


@dataclass
class Comparison:
    n_events: int
    n_episodes: int
    n_baseline: int
    event_ret_mean: float
    event_ret_median: float
    baseline_ret_mean: float
    ret_diff: float
    event_win_rate: float
    baseline_win_rate: float
    event_recovery_rate: float
    baseline_recovery_rate: float
    recovery_diff: float
    event_ret_std: float
    baseline_ret_std: float

    def to_series(self) -> pd.Series:
        return pd.Series(self.__dict__)


def compare(feat: pd.DataFrame, cfg: dict) -> Comparison:
    """Point estimates: simple averages, exactly as decided in 3.6b."""
    usable = feat[feat["usable"]]
    ev = usable[usable["is_event"]]
    base = usable[~usable["is_event"]]
    if cfg["baseline"].get("exclude_post_event"):
        base = base[~_post_event_mask(usable, cfg).loc[base.index]]

    ev_rec = (ev["max_fwd_gain_sigma"] >= ev["target_k"]).mean()
    base_rec = _baseline_recovery_rate(ev["target_k"].to_numpy(), base["max_fwd_gain_sigma"].to_numpy())
    episodes = assign_episodes(usable["is_event"], cfg["episode_gap_days"]).nunique()

    return Comparison(
        n_events=len(ev), n_episodes=int(episodes), n_baseline=len(base),
        event_ret_mean=ev["fwd_ret"].mean(), event_ret_median=ev["fwd_ret"].median(),
        baseline_ret_mean=base["fwd_ret"].mean(),
        ret_diff=ev["fwd_ret"].mean() - base["fwd_ret"].mean(),
        event_win_rate=(ev["fwd_ret"] > 0).mean(), baseline_win_rate=(base["fwd_ret"] > 0).mean(),
        event_recovery_rate=float(ev_rec), baseline_recovery_rate=base_rec,
        recovery_diff=float(ev_rec) - base_rec,
        event_ret_std=ev["fwd_ret"].std(), baseline_ret_std=base["fwd_ret"].std(),
    )


def _post_event_mask(feat: pd.DataFrame, cfg: dict) -> pd.Series:
    """Days whose own window overlaps an event window (3.6a option A2, robustness only)."""
    N = cfg["horizon"]
    mask = np.zeros(len(feat), bool)
    for pos in np.flatnonzero(feat["is_event"].to_numpy()):
        mask[max(0, pos - N) : pos + N + 1] = True
    return pd.Series(mask, index=feat.index)


def block_bootstrap(feat: pd.DataFrame, cfg: dict, n_rep: int = None, block: int = None) -> pd.DataFrame:
    """3.6b - resample contiguous blocks of days carrying their labels and outcomes, and
    recompute (event mean - baseline mean) in each replicate. Returns one row per replicate."""
    rng = np.random.default_rng(cfg["bootstrap"]["seed"])
    block = block or cfg["bootstrap"]["block_length"]
    n_rep = n_rep or cfg["bootstrap"]["n_replicates"]

    usable = feat[feat["usable"]]
    is_ev = usable["is_event"].to_numpy()
    # 3.6a option A2 (robustness): baseline days whose window overlaps an event window are
    # dropped from the baseline side of every replicate as well, not just from the point estimate.
    keep_base = np.ones(len(usable), bool)
    if cfg["baseline"].get("exclude_post_event"):
        keep_base = ~_post_event_mask(usable, cfg).to_numpy()
    ret = usable["fwd_ret"].to_numpy()
    gain_sigma = usable["max_fwd_gain_sigma"].to_numpy()
    target_k = usable["target_k"].to_numpy()
    n = len(usable)
    n_blocks = int(np.ceil(n / block))
    starts_max = n - block

    rows = []
    for _ in range(n_rep):
        starts = rng.integers(0, starts_max + 1, n_blocks)
        take = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n]
        e, r, g, k = is_ev[take], ret[take], gain_sigma[take], target_k[take]
        b = (~e) & keep_base[take]
        if e.sum() < 2 or b.sum() < 2:
            continue
        rows.append({
            "ret_diff": r[e].mean() - r[b].mean(),
            "recovery_diff": (g[e] >= k[e]).mean() - _baseline_recovery_rate(k[e], g[b]),
            "n_events": int(e.sum()),
        })
    return pd.DataFrame(rows)


def ci_from_bootstrap(boot: pd.DataFrame, column: str, ci: float = 0.95) -> tuple[float, float, float]:
    """Percentile interval and a two-sided bootstrap p-value for H0: difference = 0."""
    vals = boot[column].to_numpy()
    lo, hi = np.percentile(vals, [(1 - ci) / 2 * 100, (1 + ci) / 2 * 100])
    p = 2 * min((vals <= 0).mean(), (vals >= 0).mean())
    return float(lo), float(hi), float(min(p, 1.0))


def newey_west_test(feat: pd.DataFrame, cfg: dict, lags: int = None) -> pd.Series:
    """3.9a secondary check: regress the 5-day forward return on an event dummy with
    Newey-West (HAC) standard errors. The coefficient is the same event-minus-baseline
    difference the bootstrap estimates; only the uncertainty is computed differently.
    Default lag length = horizon, the span over which windows mechanically overlap."""
    import statsmodels.api as sm

    usable = feat[feat["usable"]]
    y = usable["fwd_ret"].to_numpy()
    X = sm.add_constant(usable["is_event"].astype(float).to_numpy())
    lags = cfg["horizon"] if lags is None else lags
    fit = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    lo, hi = fit.conf_int()[1]
    return pd.Series({
        "difference (event - baseline)": fit.params[1], "std error (HAC)": fit.bse[1],
        "t statistic": fit.tvalues[1], "p value": fit.pvalues[1],
        "95% CI low": lo, "95% CI high": hi, "lags": lags, "n": int(fit.nobs),
    })


def split_periods(feat: pd.DataFrame, cfg: dict) -> dict[str, pd.DataFrame]:
    """3.7 - development vs out-of-sample."""
    cut = pd.Timestamp(cfg["split"]["dev_end"])
    return {"dev": feat[feat["Date"] <= cut], "oos": feat[feat["Date"] > cut]}


def load_features(cfg: dict = None) -> pd.DataFrame:
    cfg = cfg or load_config()
    df, _ = load_clean(ROOT / cfg["data"]["raw_path"])
    return build_features(df, cfg)
