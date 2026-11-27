# Variance Analyst method

Budget versus actual (and versus prior period), materiality, price-volume-mix and an EBITDA bridge that reconciles to the cent, plus an Excel workbook with live formulas.

Implement this method as a pandas and openpyxl script saved in the output folder (for example `<out>/variance_run.py`), run it, and read its outputs. Every figure you report must come from the files the script writes.

## Parameters

| Name | Default | Meaning |
|---|---|---|
| period | required | YYYY-MM |
| prior_period | month before period | YYYY-MM |
| abs | 50000 | Absolute materiality |
| pct | 5 | Percent materiality |
| currency | EUR | Label only |

## Input

P&L files (actuals, budget, optional prior): `period, entity, account, line, type, amount`. `type` is revenue, cogs, opex or other (other is below EBITDA). Amounts are positive for revenue and costs.

Optional sales file: `period, entity, product, scenario (actual|budget), units, revenue`.

## Load and validate (each P&L file)

1. Lower-case column names. If a required column is missing, stop and name it.
2. `period` = first 7 characters. `type` lower-case and stripped; any value outside the four types stops the run with the bad values listed.
3. Keep rows for the period; if none remain, stop.
4. Warn if key rows (entity, account, line, type, period) are duplicated; sum them.
5. Aggregate amount by entity, account, line, type.

## Variance table

1. Outer-join actuals and budget on entity, account, line, type; missing amounts are 0. Columns `actual`, `budget`.
2. With a prior file: left-join prior for prior_period as `prior`, missing = 0; `vs_prior` = actual − prior.
3. `variance` = actual − budget. `variance_pct` = variance ÷ |budget| × 100 to 2 dp, blank where budget is 0.
4. `ebitda_impact` = variance for revenue, −variance for cogs and opex, 0 for other.
5. `direction`: favourable if ebitda_impact > 0, adverse if < 0, on plan if 0. For type other: favourable if variance < 0, adverse if > 0.
6. `material` = |variance| >= abs, OR (|variance_pct| >= pct AND |variance| >= 0.25 × abs).
7. Sort by |variance| descending and number rows `V001`, `V002`, … in a `row_id` column.

Write `variance.csv` and `material.csv` (material rows only).

## Price-volume-mix (only with a sales file)

For the period, sum units and revenue by entity and product for actual (a) and budget (b); outer-join, missing = 0. Price = revenue ÷ units (0 if units are 0). Per entity: Ua = total actual units, Ub = total budget units. For each product:

- share_b = units_b ÷ Ub
- volume = (Ua × share_b − units_b) × price_b
- mix = (units_a − Ua × share_b) × price_b
- price = (price_a − price_b) × units_a
- If units_b = 0 (new product): mix = revenue_a, volume = 0, price = 0
- total_variance = revenue_a − revenue_b
- check = volume + mix + price − total_variance, to 2 dp

Write `pvm.csv` with entity, product, units and prices for both scenarios, the three effects, total_variance and check.

## EBITDA bridge

EBITDA = revenue − cogs − opex. Steps:

1. `Plan EBITDA` (budget), kind total.
2. Revenue. With PVM: Volume, Price, Mix (sum of each effect, skipped if under 0.005), then `Other revenue` = total revenue variance − the three, if |value| >= 0.5. Without PVM: one step per revenue line, `Revenue: {line}`.
3. For cogs, then opex: sum ebitda_impact by line. Lines with |impact| >= 0.5 × abs get their own step (`COGS: {line}` or `Opex: {line}`). The rest combine into `COGS: other lines` or `Opex: other lines` if |sum| >= 0.5.
4. `Actual EBITDA`, kind total.

Each step has a source: pvm.csv or variance.csv for deltas, budget or actuals for totals. Write `bridge.csv` (step, value, kind, source). gap = plan + sum of deltas − actual, to 2 dp.

## Workbook `variance.xlsx`

- **Variance** sheet: Row, Entity, Account, Line, Type, Actual, Budget, then live formulas: Variance `=F−G`; Var % `=IF(G=0,"",H/ABS(G))`; EBITDA impact `=H×sign` (sign 1 revenue, −1 cogs and opex, 0 other); Material as an IF/OR formula matching rule 6 above. A blank row, then `Total EBITDA impact` with `=SUM()` of the impact column. Bold header, frozen top row, thousands format, percent format on Var %.
- **Bridge** sheet: Step, Value, Running (first row `=B2`, deltas `=C(prev)+B`, totals `=B`), Source, and a final check row `=C(second-last) − B(last)` that must show 0.
- **Price-Volume-Mix** sheet with the pvm table, when there is one.

## Summary `variance_summary.json`

period, currency, materiality, revenue (actual, budget), ebitda (actual, budget, variance), lines, material_lines, top_material (first 8 material rows: row_id, entity, line, type, actual, budget, variance, variance_pct, direction), pvm_total, pvm_check_max_abs, bridge, bridge_reconciles (gap = 0), bridge_gap.

## Checks that must pass before you report

1. `bridge_reconciles` is true (gap 0.00).
2. `pvm_check_max_abs` is 0 when there is a sales file.
3. Sum of ebitda_impact over all rows equals actual EBITDA − plan EBITDA, to the cent.
4. Open variance.xlsx with openpyxl and confirm the formula cells hold formulas, not values.

If any check fails, stop and report it instead of explaining the numbers.
