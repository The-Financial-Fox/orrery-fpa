---
name: journal-screening
description: >
  This skill should be used when the user asks to "screen the journals", "check journals for fraud
  risk", "find risky journal entries", "journal entry testing", "any duplicate invoices",
  "who posted on the weekend", or "/journal-screening", and provides a journal or GL detail export.
  Runs the Orrery Sentinel.
metadata:
  version: "0.1.0"
---

# Journal Screening

Score every journal against risk rules and route the high-risk ones to a controller with a specific question.

## Steps

1. Identify the journal export and, if available, a vendor master list.
2. Read `orrery-close-policy.md` for the approval threshold, business hours and sensitive accounts. Defaults: 50000, 7-20, 1999.
3. Output folder: `orrery-close/<period>/sentinel/` during a close, otherwise `orrery-screening/`.
4. Dispatch the **sentinel** agent with the file paths, the absolute engine path (`scripts/screen_journals.py` in this skill's base directory), policy values, the period end date and the output and close folders.
   Inline alternative:
   `python3 scripts/screen_journals.py --journals J --out OUT [--vendors V] --approval 50000 --hours 7-20 --sensitive 1999 --period-end YYYY-MM-DD`
5. Present: screened and flagged counts by severity, then the cases (highest score first) as short cards: journal, amount, vendor, rules fired, the question to ask. Mention a noisy rule and the suggested setting if the agent reported one.

## Rule weights

weekend 2, after_hours 1, round_amount 1, below_threshold 2, new_vendor 2, duplicate 3, self_approved 3, sensitive_acct 2, period_end 1. Severity: high at 6 or more, medium at 3 to 5. Benford MAD on the population (close below 0.006, acceptable below 0.012, marginal below 0.015).

## Language

Describe what happened, not intent. "Posted Sunday 23:41 by a preparer outside business hours" is right; "suspicious entry by k.schulz" is not.
