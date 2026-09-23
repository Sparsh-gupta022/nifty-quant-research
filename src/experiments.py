"""Pre-specified robustness grid and the single out-of-sample run.

Nothing here selects a "best" setting: the main specification in config.yaml carries the
formal conclusion (decision 3.9d) and these variants only show how stable it is.
"""

import copy

import numpy as np
import pandas as pd

from src.engine import (block_bootstrap, build_features, ci_from_bootstrap, compare,
                        load_config, load_features, split_periods)


def run_spec(df_clean_cfg, cfg: dict, period: str = "dev", block: int = None,
             n_rep: int = None) -> dict:
    """Recompute features for this cfg variant and summarise the chosen period."""
    feat = build_features(df_clean_cfg, cfg)
    part = split_periods(feat, cfg)[period] if period in ("dev", "oos") else feat
    c = compare(part, cfg)
    boot = block_bootstrap(part, cfg, n_rep=n_rep, block=block)
    ret_lo, ret_hi, ret_p = ci_from_bootstrap(boot, "ret_diff", cfg["bootstrap"]["ci"])
    rec_lo, rec_hi, rec_p = ci_from_bootstrap(boot, "recovery_diff", cfg["bootstrap"]["ci"])
    cost = cfg["trade"]["cost_round_trip"]
    return {
        "n_events": c.n_events, "n_episodes": c.n_episodes,
        "event_ret": c.event_ret_mean, "baseline_ret": c.baseline_ret_mean,
        "ret_diff": c.ret_diff, "ret_ci_lo": ret_lo, "ret_ci_hi": ret_hi, "ret_p": ret_p,
        "net_ret_diff": c.ret_diff - cost,
        "recovery": c.event_recovery_rate, "baseline_recovery": c.baseline_recovery_rate,
        "recovery_diff": c.recovery_diff, "rec_ci_lo": rec_lo, "rec_ci_hi": rec_hi, "rec_p": rec_p,
        "event_win": c.event_win_rate, "baseline_win": c.baseline_win_rate,
        "event_std": c.event_ret_std, "baseline_std": c.baseline_ret_std,
    }


def with_override(cfg: dict, **path_values) -> dict:
    """cfg copy with dotted-path overrides, e.g. with_override(cfg, **{'event.threshold_sigma': 2.5})."""
    out = copy.deepcopy(cfg)
    for path, value in path_values.items():
        node = out
        *parents, leaf = path.split(".")
        for p in parents:
            node = node[p]
        node[leaf] = value
    return out


def fixed_threshold_features(df, cfg, level: float) -> pd.DataFrame:
    """Robustness only: the fixed -2% rule instead of the volatility-scaled rule (3.1)."""
    feat = build_features(df, cfg)
    feat["is_event"] = (feat["ret"] <= level).fillna(False)
    return feat
