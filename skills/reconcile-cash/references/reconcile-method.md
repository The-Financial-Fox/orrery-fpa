# Reconciler method

Match bank statement lines to GL cash lines, classify every break, and propose (never post) the journals that clear bank-only items.

Implement this method as a short pandas script saved in the output folder (for example `<out>/recon_run.py`), run it, and read its outputs. Do not match by eye. Every figure you report must come from the files the script writes.

## Parameters

| Name | Default | Meaning |
|---|---|---|
| date_window | 3 | Days allowed between bank date and GL date in pass 2 |
| amount_tol | 0.01 | Amount tolerance in pass 3 |
| min_sim | 0.55 | Minimum description similarity in pass 3 |

## Load and validate

1. Read both CSVs. Lower-case and strip column names.
2. Required columns in both: `date`, `amount`, `description`. If one is missing, stop and name it with the columns found.
3. Parse `date`; if any date fails to parse, stop and list up to 5 bad rows.
4. Convert `amount` to numeric and round to 2 decimals. Amounts are signed: money in is positive.
5. If `reference` or `entity` is absent, add it as empty text. Strip whitespace.
6. Give each row a `rowid` (0-based position in its file).

## Matching (each match is one-to-one; earlier passes win)

Keep two sets of used rowids, one per file.

**Pass 1, reference.** For each bank line with a non-empty reference, find an unused GL line with the same reference (case-insensitive), the same amount and the same entity. Take the first. Rule label: `reference+amount`.

**Pass 2, amount and date.** For each unmatched bank line, candidates are unused GL lines with the same amount and entity whose date is within `date_window` days. Pick the closest date; break ties by higher description similarity. Rule label: `amount+date±{date_window}d`.

**Pass 3, fuzzy.** For each unmatched bank line, candidates are unused GL lines in the same entity with `|amount difference| <= amount_tol` and date within `2 × date_window`. Pick the highest description similarity; accept only if it is at least `min_sim`. Rule label: `fuzzy(sim=0.xx)`.

Description similarity: lower-case, replace every character that is not a-z, 0-9 or space with a space, split into words, join with single spaces, then take the `difflib.SequenceMatcher` ratio of the two strings.

## Break classification

Bank-only lines (unmatched bank): classify from the description, first match wins (case-insensitive, whole words):

| break_type | Words | proposed_account |
|---|---|---|
| bank_fee | fee, charge, commission, kosten, gebuehr, gebühr | 6810 Bank charges |
| interest | interest, rente, zins | 7900 Interest income/expense |
| fx | fx, revaluation, exchange, koers, kurs | 7950 FX gains/losses |
| card | card, visa, mastercard, amex | 2150 Card clearing |
| unknown | anything else | 1999 Suspense (investigate) |

GL-only lines (unmatched GL): amount < 0 is `outstanding_payment`, otherwise `deposit_in_transit`.

`age_days` for a break = latest date in its own file minus the break's date.

## Proposed journals

One per bank-only line, numbered `PJ-0001`, `PJ-0002`, … in bank-break order:

- Money out (amount < 0): debit `proposed_account`, credit `1010 Bank`.
- Money in: debit `1010 Bank`, credit `proposed_account`.
- `amount` = absolute value; `evidence` = `bank row {rowid}: {description}`.
- `confidence` = high unless break_type is unknown, then low.
- `status` = `proposed (needs reviewer)`.

## Outputs

- `matched.csv`: bank_row, gl_row, rule, all bank columns prefixed `bank_`, all GL columns prefixed `gl_`, and `date_diff_days` (GL date minus bank date).
- `bank_breaks.csv`, `gl_breaks.csv`: the unmatched lines with break_type, proposed_account (bank only), age_days and the original row number.
- `proposed_journals.csv`.
- `recon_summary.json` with: bank_lines, gl_lines, matched_pairs, auto_match_rate_bank (matched bank lines ÷ bank lines × 100, 2 dp), match_rules (count per rule with the bracketed part removed), bank_breaks, bank_breaks_total, gl_breaks, gl_breaks_total, breaks_older_than_30d, proposed_journals, and `by_entity`.

`by_entity`, for each entity found in either file: bank_lines, gl_lines, bank_total, gl_total, difference (bank_total minus gl_total), unmatched_bank, unmatched_gl, explained_by_breaks (sum of unmatched bank amounts minus sum of unmatched GL amounts) and unexplained (difference minus explained_by_breaks). All money to 2 decimals.

## Checks that must pass before you report

1. Every bank rowid and every GL rowid appears exactly once: either in matched.csv or in its breaks file.
2. `unexplained` is 0.00 for every entity. Matched pairs have equal amounts in passes 1 and 2, so the bank-to-GL difference must equal the breaks. If it is not 0.00, stop and report it as the headline problem: either a pass 3 amount difference, or the two files do not cover the same population.
3. The number of proposed journals equals the number of bank breaks.

State in your report that these checks passed.
