# Does NIFTY recover after a significant one-day fall?

An event study on NIFTY 50 daily data, 2000–2026, testing the claim:

> *"After a significant one-day fall in NIFTY, the market tends to recover over the next few trading days."*

**Headline result.** The claim is **true as a statement about price paths** and **not supported as a tradable edge**.
After a fall of more than 2× recent volatility, NIFTY regains at least half of that fall within 5 trading
sessions far more often than comparable normal days (**+15.1pp** in development, **+19.1pp** out-of-sample,
both significant). But the 5-day return from a realistic entry is **statistically indistinguishable from
zero** in development (+0.34pp, p=0.46) and **negative out-of-sample** (−0.44pp, p=0.61), with roughly
double the volatility and a win rate no better than baseline.

---

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python src/fetch_data.py                 # downloads the raw data (already committed)
.venv/bin/python -m pytest tests                   # data-validation tests
.venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/research.ipynb
```

The notebook runs top to bottom in about 15 seconds and reproduces every number in this README.
Open `notebooks/research.ipynb` to read the study in order.

## Repository layout

| Path | Contents |
|---|---|
| `notebooks/research.ipynb` | The full study: data → validation → design → events → results → robustness → out-of-sample → challenges → backtest |
| `config.yaml` | Every experimental rule (threshold, horizon, costs, split, bootstrap). Change a value here and rerun; no code edits needed |
| `src/fetch_data.py` | Downloads NIFTY 50 daily OHLC from NSE Indices |
| `src/data.py` | Loading, validation, cleaning policy, suspicious-Open flags |
| `src/engine.py` | Event detection, recovery, forward returns, baseline, block bootstrap, Newey–West |
| `src/experiments.py` | Robustness grid runner |
| `src/backtest.py` | Event-driven backtest and buy-and-hold reference |
| `tests/test_data.py` | Unit tests for the validator |
| `docs/DECISIONS.md` | **Decision log**: every research choice, the alternatives, and why one was picked |
| `docs/RESEARCH_NOTE_OUTLINE.md` | Outline of the Research Note |
| `data/raw/` | Raw download, committed unmodified |
| `data/clean/` | Generated results: robustness grid, trade list |

## Data

| | |
|---|---|
| Source | [NSE Indices](https://www.niftyindices.com/reports/historical-data) (official index provider) |
| Series | NIFTY 50 price index, daily Open/High/Low/Close |
| Coverage | 3 Jan 2000 – 21 Sep 2026, **6,644 trading days** (6,583 usable after the 60-day volatility warm-up) |
| Retrieval | `src/fetch_data.py`, one request. The site's 1-year-per-query limit is enforced only in browser JavaScript; the page's own backend endpoint returns the full range |

**Validation results:** 0 missing values, 0 duplicate dates, 0 non-positive prices, 0 rows where High/Low
fail to bound Open/Close. The source delivers rows newest-first, so they are re-sorted. 12 calendar gaps
longer than 4 days, all 5–6 days (a holiday next to a weekend). Every full year has 243–254 trading days.

**Cleaning policy**
- Invalid rows raise an error rather than being silently dropped (none occur).
- Calendar gaps are reported, never filled — market holidays are not missing data.
- Extreme days are **kept**: the largest moves (23 Mar 2020 −13.0%, 17 May 2004 −12.2%, 24 Oct 2008 −12.2%,
  18 May 2009 +17.7%) are real events and are precisely what the hypothesis concerns.
- **Known data-quality issue:** before 2011, the Open is often stale — equal to the previous Close on 2–11%
  of days, and exactly at the day's High or Low on 11–26% (vs ~0% and 2–5% from 2011 onward). Rows are
  flagged, not altered, and the issue is tested rather than assumed away (see Limitations).

## Methodology

| Element | Rule | Why |
|---|---|---|
| **Event** | Close-to-close return < −2 × σ, where σ = standard deviation of returns over days t−60 … t−1 | A fixed −2% rule puts 61 events in 2008 and none in 2017 or 2023 — it identifies turbulent years, not unusual falls. Scaling by recent volatility makes "significant" mean unusual *for current conditions*. Day t is excluded from σ, so there is no look-ahead |
| **Recovery** | Any Close in t+1 … t+5 ≥ event Close + 50% × (previous Close − event Close) | Closes, not Highs, so a brief intraday touch does not count |
| **Baseline for recovery** | Same target converted to σ units and applied to non-event days using their own σ | Keeps the target equally difficult in calm and turbulent markets |
| **Holding period** | N = 5 trading days, window fixed from the event date | "The next few trading days". The clock never waits for the first up day, which would condition on post-event price action |
| **Entry / exit** | Enter Open(t+1), exit Close(t+5) | The event is only known at the close of day t, so Open(t+1) is the first executable price. Exiting at Close(t+5) covers exactly the window the recovery test observes |
| **Costs** | 0.10% round trip (0.05% / 0.20% sensitivity) | A **modelling assumption** for total friction, not a measured average |
| **Baseline for returns** | Non-event days, post-event days retained | 856 baseline days (13.4%) follow an event within 5 days; keeping them biases the comparison *against* the hypothesis |
| **Inference** | Whole-series block bootstrap, block = 10 days, 2,000 replicates, two-sided; Newey–West (5 lags) as a secondary check | Consecutive 5-day windows share days. Measured autocorrelation is 0.80 / 0.58 / 0.37 / 0.16 at lags 1–4 and −0.02 at lag 5, so dependence is mechanical and dies exactly at the window length |
| **Split** | Develop on 2000–2017 (142 events), test once on 2018–2026 (72 events) | Rules frozen before the out-of-sample was evaluated |

Events are also grouped into **episodes** (a new episode starts after a gap of more than 5 trading days):
214 events form **146 episodes**, the largest being 8 events from 24 Feb to 23 Mar 2020.

Every choice above, including the alternatives considered and why they were rejected, is recorded in
[`docs/DECISIONS.md`](docs/DECISIONS.md).

## Key assumptions

1. Index prices are tradable proxies; no futures roll, tracking error or bid-ask spread is modelled.
2. 0.10% round-trip friction. NSE's official Close is a 30-minute VWAP, so exact fills are not achievable.
3. Orders always execute at the assumed Open/Close, with no partial fills or liquidity constraints.
4. NIFTY 50 composition changes over 26 years are not modelled.
5. Volatility is measured by a 60-day rolling standard deviation (20-day tested as robustness).

## Results

### Main specification

| Measure | Development 2000–2017 | Out-of-sample 2018–2026 |
|---|---|---|
| Events (episodes) | 142 (96) | 72 (50) |
| **Recovery rate**, event vs baseline | 55.6% vs 40.5% → **+15.1pp**<br>95% CI [+7.2, +22.0], p<0.001 | 58.3% vs 39.2% → **+19.1pp**<br>95% CI [+7.5, +31.6], p=0.001 |
| **5-day return**, event vs baseline | +0.556% vs +0.215% → **+0.34pp**<br>95% CI [−0.44, +0.99], p=0.46 | −0.319% vs +0.122% → **−0.44pp**<br>95% CI [−1.76, +0.69], p=0.61 |
| Newey–West check on the return difference | t = 0.890, p = 0.374 | t = −0.707, p = 0.479 |
| Win rate | 55.6% vs 56.3% | 50.0% vs 53.4% |
| Return volatility | 4.82% vs 3.30% | 4.10% vs 2.14% |

### Robustness

**The recovery effect holds** across thresholds (1.5σ +9.3pp, 2σ +15.1pp, 2.5σ +15.9pp), horizons
(+6.1 to +17.8pp), block lengths 5/10/21, a stricter 100% retracement (+23.2pp), a 20-day σ window
(+9.9pp), the alternative baseline (+13.5pp), the clean 2011–2026 subset (+13.4pp), and **all 8 regime
cuts** (+10.7 to +23.1pp). It does **not** hold under a fixed −2% event rule: **+2.7pp, p=0.38**.

**The return effect is absent everywhere.** No threshold, horizon, regime, sub-period, entry-price
variant or data subset produces a significant positive difference. It is +0.43pp in uptrends and
−0.57pp in downtrends. One variant (out-of-sample, N=1) shows +0.30pp with p=0.015 — about what chance
produces across ~20 pre-specified variants, and it is not the main specification.

### Backtest

Entry Open(t+1), exit Close(t+5), 0.10% round trip. **Mode A** (main) holds one position at a time;
**Mode B** takes every event.

| | Trades | Cumulative | Avg trade | Win rate | Max drawdown |
|---|---|---|---|---|---|
| Mode A, development | 103 | +9.73% | +0.191% | 54.4% | −23.3% |
| Mode A, out-of-sample | 56 | +6.64% | +0.162% | 53.6% | −19.9% |
| Mode A, full sample | 159 | +17.01% | +0.181% | 54.1% | −25.3% |
| Mode B, out-of-sample | 72 | **−30.67%** | −0.419% | 50.0% | −50.4% |
| Mode B, full sample | 214 | +12.32% | +0.162% | 53.3% | −53.6% |

Cost sensitivity (Mode A, full sample): 0.05% → +26.69%, 0.10% → +17.01%, **0.20% → −0.20%**.

Buy and hold over the same 26.4 years returned **+1,431%** (CAGR 10.9%), though the strategy is invested
only about 12% of days.

## Limitations

1. **The overlap rule decides the backtest's sign.** Mode A returns +6.64% out-of-sample, Mode B −30.67%.
   The only difference is whether repeat events during the COVID crash are traded — and those are the
   worst trades, so Mode A's result is flattered by the rule rather than by risk control.
2. **Costs are assumed, not measured.** At a 0.20% assumption, 26 years of trading returns −0.20%.
3. **The recovery finding is definition-dependent**: under a fixed −2% rule it drops to +2.7pp (p=0.38).
4. **Small effective sample:** 214 events, ~146 independent episodes, only 72 out-of-sample.
5. **Recovery is a path statistic.** Touching a level intraweek is not a captured return; exits are
   mechanical at t+5.
6. **A few days carry much of the weight:** excluding the 5 largest events moves the out-of-sample mean
   return from −0.319% to +0.371%. Four COVID-crash trades drive the negative result.
7. **Multiple testing:** ~20 pre-specified variants were run, so roughly one chance-level "significant"
   result is expected, and one appeared.
8. **Pre-2011 Open quality** is poor, though testing shows it does not drive the results (suspicious-Open
   events average +0.276% vs +0.258% for clean ones).

## Conclusion

The hypothesis survives in its descriptive form and fails in its tradable form.

NIFTY does bounce back more often after a significant fall: it regains half the loss within a week
materially more often than comparable ordinary days, and this held out-of-sample on data that played no
part in any design choice. The most likely mechanism is volatility, not direction — post-event volatility
runs at 1.5–1.9× baseline, and larger swings make a partial retracement more likely to be touched.

That bounce did not convert into money. The 5-day return advantage is indistinguishable from zero before
the out-of-sample test and negative after it, while the risk taken is roughly double. Against the
pre-registered rejection criterion, the tradable interpretation is **rejected** and the recovery
interpretation **survives**.

A negative result on tradability, honestly obtained, is the finding here.
