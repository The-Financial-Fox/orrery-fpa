# Sentinel method

Score every journal entry against risk rules, rank the flagged ones, and run a Benford test on the population.

Implement this method as a short pandas script saved in the output folder (for example `<out>/screen_run.py`), run it, and read its outputs. Do not screen by eye. Every figure you report must come from the files the script writes.

## Parameters

| Name | Default | Meaning |
|---|---|---|
| approval | 50000 | Approval threshold |
| hours | 7-20 | Business hours: start hour inclusive, end hour exclusive |
| sensitive | 1999 | Comma-separated account prefixes |
| period_end | none | Last day of the period, YYYY-MM-DD |
| min_score | 3 | Lowest score that counts as medium |
| vendors | none | Optional vendor master; the first column holds vendor names |

## Load and validate

1. Read the CSV; lower-case and strip column names.
2. Required: `je_id`, `posted_at`, `account`, `amount`. If any is missing, stop and name them.
3. Add `vendor`, `description`, `preparer`, `approver`, `invoice_ref`, `entity` as empty text if absent; strip whitespace.
4. Parse `posted_at` as a timestamp, `amount` as numeric, `account` as text. Work with the absolute amount.

## Rules and weights

A journal can fire several rules. Its score is the sum of the weights. Record a short evidence text for each rule that fires.

| Rule | Weight | Fires when | Evidence |
|---|---|---|---|
| weekend | 2 | posted on Saturday or Sunday | weekday and time, e.g. `Sun 23:41` |
| after_hours | 1 | hour < start or hour >= end | `HH:MM` |
| round_amount | 1 | amount >= 1,000 and an exact multiple of 1,000 | amount |
| below_threshold | 2 | 0.95 × approval <= amount < approval | `amount vs limit approval` |
| self_approved | 3 | approver empty, or approver equals preparer (case-insensitive) | `preparer X / approver Y` |
| sensitive_acct | 2 | account starts with any sensitive prefix | account |
| period_end | 1 | posted date after period_end (`posted after period end`), or within 1 day before it (`last 2 days of period`) | as quoted |
| new_vendor | 2 | see below | see below |
| duplicate | 3 | see below | see below |

**new_vendor.** Only for rows with a vendor. With a vendor master: the vendor (lower-case) is not in the master; evidence `{vendor} not in vendor master`. Without one: the vendor appears exactly once in the file; flag that row; evidence `{vendor} appears once`.

**duplicate**, two tests:
1. Sort vendor rows by posted_at. Group by vendor and amount rounded to 2 decimals. Within a group, flag each entry posted 30 days or fewer after the previous one; evidence `same vendor+amount as {previous je_id}`.
2. For rows with an invoice_ref: base ref = upper-case ref with a trailing suffix removed (`A`, `B`, `DUP` or `COPY`, optionally preceded by `-`, `_` or a space; or `-`, `_` or a space followed by one digit). Group by base ref. Where a group has more than one distinct ref, flag every row after the first unless it already has a duplicate flag; evidence `invoice ref {ref} resembles {first ref}`.

## Severity

high if score >= 6, medium if score >= min_score, otherwise low.

## Benford test

Take absolute amounts >= 10. First significant digit = the first non-zero digit of the amount written to 2 decimals. Observed share of each digit 1–9 against expected log10(1 + 1/d). MAD = mean of the 9 absolute differences. Conformity: close if MAD < 0.006, acceptable < 0.012, marginal < 0.015, otherwise nonconformity. Note that under about 300 amounts the test is unreliable.

## Outputs

- `flags.csv`, one row per journal with at least one rule: je_id, posted_at, entity, account, amount, vendor, description, preparer, approver, score, rules (`; `-joined), evidence (`rule: text` joined with ` | `), severity. Sort by score, then amount, both descending.
- `screening_summary.json`: journals_screened, flagged, by_severity (high, medium, low), by_rule (count per rule), top (first 10 flags: je_id, amount, vendor, score, rules, evidence), benford (n, mad to 4 dp, conformity, note), settings (approval, hours, sensitive accounts).

## Checks that must pass before you report

1. journals_screened equals the number of input rows.
2. The by_severity counts add up to flagged.
3. Recompute the score of the top 3 flags from their rules and the weight table; they must match.

State in your report that these checks passed.
