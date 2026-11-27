# Forecaster method

Roll a monthly forecast forward with P10/P50/P90 bands. The method is deliberately simple and explainable: seasonal index × linear trend, with block-bootstrapped residual bands.

Implement this method as a numpy and pandas script saved in the output folder (for example `<out>/forecast_run.py`), run it, and read its outputs. Do not estimate figures in your head. Every number you report must come from the files the script writes.

## Parameters

| Name | Default | Meaning |
|---|---|---|
| through | required | Last month to forecast, YYYY-MM |
| fy_start | none | First month of the fiscal year, YYYY-MM |
| metrics | all in file | Which metrics to forecast |
| sims | 4000 | Simulated paths |
| trend_window | 18 | Months used for the trend |
| seed | 7 | Random seed: always set it, so a rerun gives the same answer |
| adjustments | none | List of (metric, YYYY-MM, signed amount) for known events |

## Input

`period, metric, value`, actuals only, monthly.

## Per metric

1. Sum value by period and sort. Under 6 months: skip the metric and note it.
2. If months are missing inside the range, fill them by linear interpolation and note how many.
3. **Seasonal index.** With 24+ months: 12-month centred moving average (only where a full window exists); ratio = value ÷ average; mean ratio per calendar month (missing months = 1.0); divide the 12 indices by their mean so they average 1. Under 24 months: all indices = 1.0, and note "seasonality off".
4. De-seasonalise: value ÷ index for its month.
5. **Trend.** Take the last `trend_window` de-seasonalised values; fit a straight line on x = 0, 1, 2, … (least squares). fitted = intercept + slope × x.
6. **Residuals** (relative): (value − fitted) ÷ fitted (use 1 where fitted is 0). Subtract their mean.
7. **Horizon**: every month after the last actual up to and including `through`. If empty, note it and skip.
8. **Point forecast** for horizon month i (i = 0, 1, …): (intercept + slope × (window length + i)) × seasonal index of that month, plus any adjustment for that metric and month.
9. **Simulation.** For each of `sims` paths, build a residual path of horizon length by repeatedly picking a random start j in [0, max(1, n_resid − 2)) and appending resid[j : j + 3] (blocks of 3) until long enough; truncate. Path value = point × (1 + residual). Use one random generator seeded with `seed` for everything.
10. P10, P50, P90 = 10th, 50th, 90th percentile across paths, per month.
11. **Full-year outlook** (when fy_start is given): YTD actual = sum of actuals from fy_start to the last actual. Per path: YTD + simulated values for horizon months inside the fiscal year (fy_start to fy_start + 11). FY P10/P50/P90 are percentiles of those totals. Also report the sum of point forecasts for those months as remaining_point.
12. Note per metric: slope per month, residual standard deviation in %, seasonality on or off.

## Derived EBITDA

If revenue, cogs and opex all have FY simulations: per path, revenue − cogs − opex; report P10/P50/P90. Note that this assumes independent errors, so the band is slightly wide.

## Outputs

- `forecast.csv`: metric, period, p10, p50, p90, point, seasonal_index, adjustment (money to 2 dp).
- `fy_outlook.csv`: metric, fy_start, actual_months, ytd_actual, remaining_point, fy_p10, fy_p50, fy_p90; plus an `ebitda (derived)` row when available.
- `forecast_summary.json`: through, metrics, fy_outlook, notes, method, files.

## Checks that must pass before you report

1. For every row, p10 <= p50 <= p90.
2. For every FY row, fy_p10 <= fy_p50 <= fy_p90, and ytd_actual equals the sum of the actuals in the fiscal year (recompute it).
3. Every adjustment you were given appears in forecast.csv in the right month.
4. The seed was set. Running the script twice gives identical outputs.

State in your report that these checks passed.
