---
name: variance-analysis
description: >
  This skill should be used when the user asks to "explain the variance", "why did we miss budget",
  "bridge plan EBITDA to actual", "price volume mix analysis", "PVM", "what drove the month",
  or "/variance-analysis", and has actuals and budget (optionally prior period and sales by product).
  Runs the Orrery Variance Analyst and produces an Excel workbook with live formulas.
metadata:
  version: "0.1.0"
---

# Variance Analysis

Explain actual versus budget and prior period down to drivers, with an EBITDA bridge that reconciles exactly.

## Steps

1. Identify actuals, budget, optional prior-period P&L and optional sales by product. Ask for the period if it is ambiguous.
2. Read `orrery-close-policy.md` for materiality and currency. Defaults: 50000 absolute, 5 percent, EUR.
3. Output folder: `orrery-close/<period>/variance/` during a close, otherwise `orrery-variance/`.
4. Dispatch the **variance-analyst** agent with the file paths, period, the absolute path to the method spec (`references/variance-method.md` in this skill's base directory), materiality, currency and folders.
   Inline alternative: read `references/variance-method.md`. Implement it as a script in the output folder, run it, and confirm the method's checks pass.
5. Present:
   - Plan EBITDA, actual EBITDA and the variance in one line.
   - The bridge as a short table (step, value), or an inline waterfall chart if a chart tool is available.
   - The top drivers with classification and confidence.
   - Questions for budget owners.
6. Deliver `variance.xlsx` (sheets: Variance with live formulas, Bridge with a running total and a check row, Price-Volume-Mix).

## Input schema

P&L files: `period, entity, account, line, type, amount`; type in revenue, cogs, opex, other; amounts positive. Sales: `period, entity, product, scenario (actual|budget), units, revenue`. If the user's export has another shape, the agent normalises it and states the mapping.

## Method

The full method is in `references/variance-method.md`. Volume effect at budget average price, mix at budget product prices, price at actual units. The three sum to the revenue variance per product (the check column must be 0). Material if the absolute variance meets the threshold, or the percent threshold is met and the variance is at least a quarter of the absolute threshold.
