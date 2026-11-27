---
name: rolling-forecast
description: >
  This skill should be used when the user asks to "roll the forecast", "reforecast the year",
  "where do we land", "full-year outlook", "landing estimate", "P10 P90 forecast", or
  "/rolling-forecast", and has monthly actuals history. Runs the Orrery Forecaster.
metadata:
  version: "0.1.0"
---

# Rolling Forecast

Roll the forecast forward from the latest actuals with P10/P50/P90 ranges and explicit adjustments for known events.

## Steps

1. Identify the monthly history (actuals only). Aim for 24 or more months so seasonality can be estimated; with less, the engine forecasts without seasonality and says so.
2. Establish the horizon (default: end of the fiscal year) and FY start from `orrery-close-policy.md` or the user.
3. Ask once whether there are known events to include (price changes, big contracts won or lost, hiring plans). Turn each into an adjustment; never fold it into the trend.
4. Output folder: `orrery-close/<period>/forecast/` during a close, otherwise `orrery-forecast/`.
5. Dispatch the **forecaster** agent with the history, horizon, FY start, adjustments, one-offs to exclude, the absolute engine path (`scripts/forecast.py` in this skill's base directory) and folders.
   Inline alternative:
   `python3 scripts/forecast.py --history H --through YYYY-MM --fy-start YYYY-MM --out OUT [--adjust revenue:2026-12:+250000]`
6. Present FY P10/P50/P90 per metric and derived EBITDA, the adjustments applied, and movement against the previous forecast. Offer a chart of the monthly fan (actuals line, P10 to P90 band, P50 line).

## Method

Multiplicative seasonal index per calendar month, linear trend on the de-seasonalised last 18 months, 4,000 block-bootstrapped residual paths. Derived EBITDA subtracts simulated cogs and opex from revenue path by path and assumes independent errors, so its band is slightly wide.
