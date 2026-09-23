# AI Usage Note — NIFTY Event-Driven Recovery Study

## 1. Tools and How I Used Them

I used AI as a research discussion partner, coding assistant, critic and limited writing assistant. I remained responsible for the research decisions, assumptions, interpretation and final conclusion.

**ChatGPT:** I used it to understand statistical and research concepts, compare methodological alternatives, challenge assumptions, and discuss issues such as look-ahead bias, overlapping observations, baselines, robustness, multiple testing and interpretation.

**Claude Code:** I mainly used Claude Code for implementation, debugging, running experiments, organizing the codebase and reproducing the analysis. I did not treat either tool as the person making the research conclusion.

## 2. Important Research Decisions

| Decision | AI input / alternatives | My final decision and reasoning |
|---|---|---|
| **Event definition** | I discussed fixed-percentage falls and volatility-scaled thresholds such as 1.5σ, 2σ and 2.5σ, along with different lookback windows. | I chose **return < −2σ of the previous 60 trading days**. I wanted to identify an unusually large fall relative to recent market volatility rather than use an arbitrary fixed percentage. Other thresholds became robustness checks. |
| **Recovery definition** | Different recovery levels and ways of measuring a rebound were discussed. | I chose **50% recovery within 5 trading days**. For example, 20,000 → 19,000 requires 19,500 to be reached. I kept this definition fixed instead of selecting the definition with the strongest result. |
| **Holding period** | AI helped compare 1, 3, 5 and 10 trading-day horizons and highlighted the risk of post-event selection. | I chose **5 days** as the main horizon and tested 1, 3 and 10 days as robustness checks. I rejected the idea of waiting for the first positive day because that would select the exit after observing the post-event path. |
| **Entry / execution** | I discussed event-close versus next-day execution and look-ahead concerns. | I used **next-day Open → day-5 Close** as the main tradable return. The event is only known after the event-day close, so entering earlier would be unrealistic. Next-day Close was tested as a robustness check. |
| **Overlapping events** | AI explained the dependence created by overlapping 5-day windows and suggested episode grouping. | I kept event-level observations for the study but grouped nearby events into episodes for dependence analysis. I also tested different block lengths and two backtest approaches. |
| **Statistical testing** | AI explained why ordinary independent-observation tests can be inappropriate when returns overlap and suggested a block bootstrap. Newey-West was also discussed as a secondary check. | I used a **block bootstrap** as the main inference method with 2,000 repetitions and 95% confidence intervals, with L=10 as the main block length. I also used Newey-West as a secondary check. |
| **OOS testing** | AI emphasized chronological testing to avoid using future information. | I used **2000–2017 for development and 2018–2026 for out-of-sample testing**. The setup was frozen before evaluating the later period. |
| **Costs / backtest** | AI helped me consider realistic execution and transaction-cost sensitivity. | I chose **0.10% round-trip cost** as the main assumption and tested 0.05% and 0.20%. I also retained both non-overlapping and every-event backtests because their different OOS results showed how sensitive the result was to overlap handling. |

## 3. My Own Research Considerations

A major part of my process was deciding **not to optimize the research for the best observed return**. I wanted the main specification to be fixed before interpreting the robustness results.

I also raised the concern that the positive non-overlapping backtest could be misleading if repeated events during a crash were skipped. Because of this, I retained the every-event backtest as a challenge to my own result.

I investigated the suspicious pre-2011 Open-price patterns, checked whether extreme COVID-period events were driving the result, and treated the one significant result among many OOS variants as a possible multiple-testing issue rather than changing the main conclusion.

These considerations were important to me because I wanted to **challenge the hypothesis rather than search only for evidence supporting it**.

## 4. Where I Agreed With AI

I accepted AI reasoning where it matched the research objective and statistical logic. Examples include using a chronological OOS split, using a block bootstrap because observations overlap, using the first observable price after the signal, and testing alternative thresholds, horizons, entry assumptions and transaction costs.

In these cases, AI helped me understand the trade-offs, but I made the final decisions and checked the resulting outputs.

## 5. Coding, Writing Assistance and Learning

**Coding:** Claude Code helped implement the data validation, event engine, experiments, statistical tests, backtests and notebook structure. I reviewed the outputs and verified the main results reproduced correctly.

**Writing assistance:** I also used AI **partially for both the Research Note and this AI Usage Note**. I wrote the underlying research content, decisions, results and interpretation. AI was used for limited writing assistance such as **grammar correction, improving sentence clarity, organizing sections, shortening repetitive wording and improving presentation**. Neither document was generated completely by AI as a replacement for my own research work.

**What I learned:** The most important lesson was to separate a statistically interesting **recovery pattern** from a **tradable return edge**, and to actively test whether a result survives out-of-sample data, transaction costs, overlapping-event assumptions and alternative definitions.