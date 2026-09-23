# Research Note — outline (bullets only; prose to be written by the author)

Suggested space budget for 2 pages: Hypothesis + Data/Definitions ~0.5 page · Methodology ~0.4 ·
Dev + OOS + Baseline ~0.5 · Robustness/Falsification ~0.3 · Backtest ~0.2 · Limitations + Conclusion ~0.3

## 1. Hypothesis
- Informal claim tested: "After a significant one-day fall in NIFTY, the market tends to recover over the next few trading days."
- Split into two separately testable claims:
  - **Path claim (recovery):** after a qualifying fall, the index regains ≥ 50% of that fall within 5 trading days more often than on comparable normal days.
  - **Return claim (tradable):** a position entered after the fall earns a higher 5-day return than normal days, net of costs.
- Null hypothesis in both cases: no difference vs the non-event baseline. Two-sided test.
- Pre-registered rejection criterion (written before any outcome was computed): reject if the out-of-sample shows no positive advantage over baseline, or if the advantage is not robust to the pre-specified sensitivity checks.

## 2. Data and event definition
- Source: NSE Indices (niftyindices.com), NIFTY 50 price index, daily OHLC. Fetched in one request by `src/fetch_data.py`.
- Coverage: 3 Jan 2000 – 21 Sep 2026, **6,644 trading days**; **6,583** usable after the 60-day σ warm-up.
- Validation: 0 missing values, 0 duplicate dates, 0 non-positive prices, 0 High/Low inconsistencies; source arrives newest-first and is re-sorted; 12 calendar gaps > 4 days (all 5–6 days, holiday+weekend); 243–254 trading days in every full year.
- Cleaning policy: invalid rows raise an error (never silently dropped); gaps reported, not filled; extreme days kept (largest: 23 Mar 2020 −13.0%, 17 May 2004 −12.2%, 24 Oct 2008 −12.2%, 18 May 2009 +17.7%).
- Data-quality finding: pre-2011 Opens often stale — Open = previous Close on 2–11% of days and Open exactly at the day's High/Low on 11–26% (vs ~0% and 2–5% from 2011). Flagged per row, data retained, sensitivity tested (§7).
- **Event definition (3.1):** close-to-close return < −2 × σ, σ = std of returns over days t−60…t−1 (day t excluded → no look-ahead).
- Why volatility-scaled, not fixed −2%: a fixed rule puts **61 events in 2008 alone and 0 in 2017 and 2023**; it identifies turbulent years rather than unusual falls.
- Result: **214 events** (142 development, 72 out-of-sample); events spread evenly across volatility quintiles (49/48/42/39/36); median σ on event days 0.96% vs 1.04% on all days.

## 3. Recovery and return methodology
- **Recovery (3.2):** loss = prev-day Close − event-day Close; recovery level = event Close + 0.50 × loss; recovered if **any daily Close in t+1…t+5** ≥ that level. Closes used, not Highs, so a brief intraday touch does not count.
- **Baseline target (3.2a):** each event's target converted to σ units, k = (level/Close − 1)/σ; a normal day must rise k × its own σ. Keeps targets equally difficult across volatility regimes.
- **Holding period (3.3):** N = 5 trading days, window fixed from the event date; explicitly not "wait for the first up day" (that would condition on post-event price action).
- **Trade (3.4):** entry Open(t+1) — the first executable price after the signal; exit Close(t+5) — same window the recovery test observes. Rejected Open(t+6): adds an overnight beyond the window and relies on two fragile prices instead of one.
- **Costs (3.8):** 0.10% round trip as a **modelling assumption** for total friction (brokerage, STT, fees, spread, slippage), not a measured historical average; 0.05% / 0.20% as sensitivity.
- **Baseline set (3.6/3.6a):** non-event days (6,369 of 6,583); post-event days retained — 856 baseline days (13.4%) lie within 5 days of an event, which biases *against* the hypothesis.
- **Inference (3.5/3.6b/3.9):** whole-series block bootstrap, block L = 10 trading days, 2,000 replicates, two-sided, recomputing event mean − baseline mean in each replicate. Justified by measured overlap autocorrelation 0.80 / 0.58 / 0.37 / 0.16 / −0.02 at lags 1–5. Events also grouped into episodes (new episode after > 5 trading days): 214 events → **146 episodes**, largest 8 (24 Feb–23 Mar 2020).
- **Split (3.7):** development 2000–2017, out-of-sample 2018–2026, run once, no feedback into methodology.
- Configurability: every rule lives in `config.yaml`; changing a threshold or horizon requires no code change.

## 4. Development results (2000–2017, 142 events, 96 episodes, 4,280 baseline days)
- Recovery rate **55.6%** vs baseline **40.5%** → **+15.1pp**, 95% CI **[+7.2, +22.0]**, p < 0.001.
- Mean 5-day return **+0.556%** vs baseline **+0.215%** → **+0.34pp**, 95% CI **[−0.44, +0.99]**, p = 0.46.
- Median event return +0.751%.
- Win rate **55.6%** vs baseline **56.3%** (slightly lower).
- Return volatility **4.82%** vs baseline **3.30%** (~1.5×).
- Reading: path claim supported in development; return claim not distinguishable from zero.

## 5. Out-of-sample results (2018–2026, 72 events, 50 episodes, single run)
- Recovery rate **58.3%** vs baseline **39.2%** → **+19.1pp**, 95% CI **[+7.5, +31.6]**, p = 0.001 — stronger than development.
- Mean 5-day return **−0.319%** vs baseline **+0.122%** → **−0.44pp**, 95% CI **[−1.76, +0.69]**, p = 0.61 — sign flipped; net of 0.10% cost **−0.54pp**.
- Win rate **50.0%** vs baseline **53.4%**; volatility **4.10%** vs **2.14%** (~1.9×).
- Reading: recovery persisted out-of-sample; the return advantage did not.

## 6. Baseline comparison
- Baseline is the comparison that makes the numbers interpretable: a ~56% recovery rate alone is meaningless — random-walk reasoning alone implies ~55–65% for a +1% touch within 5 days.
- Event vs baseline is the reported quantity throughout, for both recovery (+15.1pp dev / +19.1pp OOS) and return (+0.34pp dev / −0.44pp OOS).
- Baseline variant A2 (excluding days whose window overlaps an event window): recovery **+13.5pp**, p < 0.001; return **−0.12pp** — conclusion unchanged.
- Buy-and-hold reference over the same periods: dev **+589%** (CAGR 11.5%), OOS **+124%** (CAGR 9.7%), full **+1,431%** (CAGR 10.9%, max DD −59.9%).

## 7. Robustness and falsification checks
- Thresholds (dev): 1.5σ **+9.3pp** (p<0.001) · 2σ **+15.1pp** · 2.5σ **+15.9pp** (p=0.006); return differences +0.08 / +0.34 / +0.64pp, all p ≥ 0.43.
- Horizons (dev): N=1 **+10.8pp** · N=3 **+17.8pp** · N=5 **+15.1pp** · N=10 **+6.1pp** (only N=10 insignificant, p=0.13); return differences −0.08 / +0.38 / +0.34 / +0.11pp, none significant.
- Block length 5/10/21: recovery CI essentially unchanged ([+7.1,+22.7] / [+7.3,+21.8] / [+7.6,+22.9]).
- Stricter recovery (100% retracement): **+23.2pp**, 95% CI [+15.0, +30.3], p < 0.001.
- σ window 20 days: **+9.9pp**, p = 0.008 (163 events).
- **Fixed −2% rule: +2.7pp, p = 0.38 — not significant.** The recovery finding depends on the volatility-scaled definition.
- Regimes (descriptive, cuts fixed in advance): calm **+10.7pp** · turbulent **+23.1pp** · uptrend **+16.8pp** · downtrend **+17.9pp**; sub-periods 2000–07 **+20.5pp**, 2008–13 **+10.7pp**, 2014–19 **+11.1pp**, 2020–26 **+20.4pp** — positive in all 8. Return difference by regime: uptrend **+0.43pp**, downtrend **−0.57pp**; sub-periods +0.26 / +0.66 / −0.16 / −0.46pp — no stable sign.
- Extreme-event sensitivity (pre-specified): dropping the 5 largest |forward return| events leaves recovery unchanged (56.5% → 56.5% full sample) but moves the OOS mean return from **−0.319% to +0.371%** — four COVID trades (16 Mar −18.0%, 6 Mar −14.4%, 9 Mar −13.2%, 12 Mar 2020 −9.3%) drive the negative OOS result.
- Data-quality sensitivity: suspicious-Open events mean **+0.276%** vs clean-Open **+0.258%**; restricting everything to 2011–2026 gives recovery **+13.4pp** (p<0.001) and return **−0.14pp** (p=0.85) — same conclusion.
- Entry-price sensitivity: Close(t+1) entry gives dev **+0.44pp** (p=0.28), OOS **−0.73pp** (p=0.32); recovery unchanged.
- Multiple testing: ~20 pre-specified variants were run, so ~1 chance-level "significant" result is expected. The one that appeared — OOS N=1, **+0.30pp, p=0.015** — is not the main specification and is treated as noise, not as a finding.
- Look-ahead controls: σ excludes day t; entry is the first price after the signal; the OOS period was evaluated once, after all rules were frozen; only event counts and data-quality statistics were inspected across the full sample before freezing.

## 8. Backtest
- Specification: enter Open(t+1), exit Close(t+5), 0.10% round trip, one position at a time (**Mode A**: events during an open trade are skipped).
- Mode A: dev **103 trades, +9.73%**, avg **+0.191%**, win **54.4%**, max DD **−23.3%**; OOS **56 trades, +6.64%**, avg +0.162%, win 53.6%, max DD −19.9%; full **159 trades, +17.01%**, avg +0.181%, win 54.1%, max DD **−25.3%**.
- Mode B (take every event) as challenge: dev **142 trades, +61.99%**, max DD −34.2%; OOS **72 trades, −30.67%**, avg −0.419%, max DD **−50.4%**; full **+12.32%**, max DD −53.6%.
- **Mode A vs Mode B out-of-sample: +6.64% vs −30.67%** — the difference is only whether repeat COVID-crash events are traded, and those are the worst trades. Mode A's positive result is flattered by the overlap rule.
- Cost sensitivity (Mode A, full): 0.05% → **+26.69%** · 0.10% → **+17.01%** · 0.20% → **−0.20%**.
- Exposure context: 159 trades × 5 days ≈ 795 days ≈ **12%** of the 6,583-day sample, vs buy-and-hold +1,431%.

## 9. Limitations
- The overlap rule flips the backtest's sign out-of-sample (+6.64% vs −30.67%).
- Costs are an assumption, not a measurement; at 0.20% the full-sample result is −0.20%.
- The recovery effect is definition-dependent: fixed −2% gives only +2.7pp (p=0.38).
- Effective sample is small: 214 events, **146 independent episodes**, only 72 out-of-sample.
- Recovery is a path statistic — touching a level intraweek is not a captured return; exits are mechanical at t+5.
- Four COVID trades flip the out-of-sample return sign.
- ~20 variants tested → ~1 false positive expected (OOS N=1 is the likely one).
- Index-level analysis: no futures roll, tracking error or bid-ask modelled; the official Close is a 30-minute VWAP, so exact fills are not achievable; pre-2011 Opens are unreliable though shown not to drive results.
- Survivorship/index-composition changes in NIFTY 50 over 26 years are not modelled.

## 10. Final conclusion
- Supported: after a 2σ one-day fall, NIFTY regains ≥ 50% of the loss within 5 sessions **more often than volatility-matched normal days** — **+15.1pp** development, **+19.1pp** out-of-sample, positive in all 8 regime cuts and across thresholds, horizons, block lengths, the stricter 100% definition and the clean-data subset.
- Mechanism consistent with the data: post-event volatility rises to **1.5–1.9× baseline**, so a partial retracement is more likely to be touched — the bounce is a volatility effect more than a directional one.
- Not supported: a capturable return advantage. **+0.34pp (p=0.46)** in development, **−0.44pp (p=0.61)** out-of-sample, negative after costs, win rate at or below baseline, roughly double the volatility.
- Against the pre-registered rejection criterion: **tradable interpretation rejected; recovery interpretation survives.**
- Practical statement of the result: the "recovery after a fall" pattern is real as a description of price paths, but it did not convert into a return a trader could bank under realistic entry, exit and cost assumptions.
- Negative result stated as such — no re-specification was performed after seeing the out-of-sample outcome.
