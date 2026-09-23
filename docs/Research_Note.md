# Research Note: Event-Driven NIFTY Recovery Study

# The outline of Research_Note is:

## 1. Hypothesis

Research question: If NIFTY 50 gets a significant fall, then will it be able to recover over the following trading days?

Hypothesis: After a significant one-day fall, NIFTY 50 is more likely to recover part of the fall over the following five trading days than during normal market periods.

## 2. Data and Event Definition

### Data

After researching on the internet, I chose and finally used NIFTY 50 OHLC data from the official NSE Indices historical data source. The dataset covers 3 January 2000 to 21 September 2026 and contains 6,644 trading days with Date, Open, High, Low and Close fields.

Then I analyzed the data and checked for missing or duplicate dates, incorrect ordering, invalid OHLC values and suspicious observations before running the analysis and making the decisions for the project.

### Event Definition

For the definition of an event, I used a technique of volatility-scaled rule. An event occurs when the daily return is less than -2 times the standard deviation of returns calculated over the previous 60 trading days. I used the previous 60 trading days to measure recent market volatility and set the threshold. This helps identify falls that are unusually large compared with NIFTY's recent movements.

### Recovery Definition

I defined recovery as recovering 50% of the event-day loss. For example, if NIFTY falls from 20,000 to 19,000, it is considered recovered if its closing price reaches 19,500 or above within the next five trading days.

## 3. Methodology

For every significant fall, I entered the trade at the Open of the next trading day and exited at the Close after five trading days. I used the next day's Open because the fall is only known after the event day's market has closed.

I compared the returns after significant-fall events with the returns on normal non-event days. I looked at statistics like mean, median, win rate and volatility to understand how the market behaved after these falls.

### Problem of Overlapping

Since some 5-day periods can overlap with each other, I used a block bootstrap to calculate the confidence intervals and statistical significance.

### Testing Sample

I divided the data into two periods. I used 2000–2017 for developing the method and kept 2018–2026 as the out-of-sample period. This allowed me to check whether the result continued to hold on data that was not used when making the research decisions.

### Backtesting

For the backtest, I assumed a 0.10% round-trip transaction cost and also tested 0.05% and 0.20% as sensitivity checks. I chose 0.10% as the main assumption because I felt it was reasonable.

## 4. Development-Sample Results

### Return Results

In the development period from 2000–2017, I found 142 significant-fall events.

The average 5-day return after these events was +0.56%, compared with +0.22% on normal non-event days. This gives a difference of around +0.34 percentage points. This does not look like a significant difference. The median event return was +0.75%.

### Recovery Results

For the recovery measure, 55.6% of event days achieved at least 50% recovery within five trading days, compared with 40.5% for normal days. This gives a difference of +15.1 percentage points, which is more supportive of our hypothesis.

However, the event-period returns were more volatile than normal days. The volatility was 4.82% for event days compared with 3.30% for the baseline.

### Statistical Results

The return difference was not statistically significant, while the recovery difference was statistically significant.

## 5. Out-of-Sample Results

### Return Results

In the out-of-sample period from 2018–2026, I found 72 significant-fall events.

The average 5-day return after these events was -0.32%, compared with +0.12% on normal non-event days. This gives a difference of around -0.44 percentage points. This does not support the idea of getting a positive return after a significant fall, showing that the return-based result did not hold out-of-sample.

### Recovery Results

For the recovery measure, 58.3% of event days achieved at least 50% recovery within five trading days, compared with 39.2% for normal days. This gives a difference of +19.1 percentage points, which still supports the recovery part of our hypothesis.

### Statistical Significance

The return difference was not statistically significant. The recovery difference was statistically significant.

Overall, the recovery result continued to appear in the out-of-sample period, but the positive return seen in the development period did not continue.

## 6. Baseline Comparison

### Return Comparison

The return advantage did not persist out-of-sample. The difference was +0.34 percentage points in the development period compared with -0.44 percentage points in the out-of-sample period.

### Recovery Comparison

The recovery result was more consistent. The recovery difference was +15.1 percentage points in the development period and +19.1 percentage points in the out-of-sample period.

This means that the recovery difference remained positive even when tested on the out-of-sample data.

## 7. Robustness and Falsification

### Different Event Thresholds

I tested different thresholds of 1.5σ, 2σ and 2.5σ instead of using only the 2σ threshold. The recovery difference remained positive across these thresholds. However, when I used a fixed -2% fall, the recovery difference became much smaller.

### Different Holding Periods

I also tested holding periods of 1, 3 and 10 trading days instead of only 5 days. The recovery result remained positive across these different periods, although the size of the difference changed.

### Other Checks

I tested different entry prices, recovery definitions, volatility windows and market regimes. The recovery result was generally consistent, but the return result did not show a stable positive advantage.

I also removed the five largest events as a check for whether a few extreme days were driving the result. The main recovery result remained similar.

### Multiple Testing

I tested many different variations, so some significant results could appear by chance. Therefore, I kept the 2σ and 5-day setup as the main specification instead of choosing the version with the best result.

## 8. Backtest

### Backtesting

I used the same entry and exit rules for the backtest: entry at the next trading day's Open and exit at the Close after five trading days, with a 0.10% round-trip transaction cost.

I mainly used a non-overlapping approach where a new trade was not taken while another trade was already open. In this setup, the strategy gave +6.64% cumulative return in the out-of-sample period, with a maximum drawdown of -19.9%.

I also tested a second approach where every qualifying event was traded, including overlapping events. This gave -30.67% in the out-of-sample period with a maximum drawdown of -50.4%.

This difference shows that the backtest result is sensitive to how overlapping events are handled, so I would not consider the positive backtest return as strong evidence of a trading edge.

## 9. Limitations

### Main Limitations

1. There are some important limitations to this study. The number of significant-fall events was relatively small, especially in the out-of-sample period, so the results may not be very stable.

2. The events can also occur close to each other, which makes the observations less independent and can affect statistical testing.

3. The recovery result also depends on how a significant fall and recovery are defined. When I used a fixed -2% threshold, the recovery difference became much smaller.

4. Transaction costs were assumed rather than measured from actual trading data. Higher costs can reduce or completely remove the backtest returns.

5. The backtest was also sensitive to how overlapping events were handled. The out-of-sample result changed from +6.64% to -30.67% when all overlapping events were traded.

Finally, the historical data contains some suspicious Open-price patterns before 2011. I tested this issue and found that it did not appear to be driving the main recovery result.

## 10. Conclusion

The main aim of this study was to check whether NIFTY 50 tends to recover after a significant one-day fall.

The results show that NIFTY was more likely to recover 50% of the fall within five trading days compared with normal days. This recovery difference was also present in the out-of-sample period.

However, the return results were not as strong. The positive return difference seen in the development period did not continue in the out-of-sample period. The return difference was not statistically significant, and the backtest was also sensitive to transaction costs and overlapping events.

Overall, the study provides evidence for the recovery part of the hypothesis, but not for a consistent tradable return advantage. A larger out-of-sample sample with more reliable execution and cost data would be needed to test this further.