# Orrery close policy

Edit the values in the tables. Every Orrery agent reads this file at the start of each run.

## Company

| Setting | Value |
|---|---|
| Group name | Example Group |
| Reporting currency | EUR |
| Entities | NL-BV, DE-GmbH, UK-Ltd |
| Fiscal year start (month) | 01 |

## Close calendar

| Stage | Working day | Agent | Sign-off owner |
|---|---|---|---|
| Cash reconciliation | Day 1, 06:00 | reconciler | Controller |
| Journal screening | Day 1, 06:00 | sentinel | Controller |
| Variance analysis | Day 1, 09:30 | variance-analyst | FP&A lead |
| Forecast roll | Day 1, 14:00 | forecaster | FP&A lead |
| Commentary | Day 2, 06:00 | narrator | CFO |
| Board pack | Day 3, 08:00 | board-builder | CFO |

## Thresholds

| Setting | Value |
|---|---|
| Materiality, absolute | 50000 |
| Materiality, percent | 5 |
| Reconciliation date window (days) | 3 |
| Stale break age (days) | 30 |
| Journal approval threshold | 50000 |
| Business hours | 7-20 |
| Sensitive accounts | 1999 (suspense) |

## Commentary

| Setting | Value |
|---|---|
| Audience | CFO |
| Units | EUR thousands with one decimal for millions (e.g. EUR 1.8M, EUR 240k) |
| Length | Headline plus at most 250 words |

## Rules

- Agents never post journals or change source systems.
- Every figure in commentary or the board pack cites its source row.
- Items stay in the review queue until a named owner approves them.
