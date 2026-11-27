---
name: reconcile-cash
description: >
  This skill should be used when the user asks to "reconcile the bank", "match bank to GL",
  "do the cash reconciliation", "why doesn't the bank tie to the ledger", "find the reconciling
  items", or "/reconcile-cash", and provides bank statement lines and GL cash lines for one or
  more entities. Runs the Orrery Reconciler.
metadata:
  version: "0.1.0"
---

# Reconcile Cash

Match bank lines to GL cash lines, explain every difference and propose clearing journals for review.

## Steps

1. Identify the bank file and the GL cash file. If either is missing, ask for it (one question).
2. Read `orrery-close-policy.md` from the working folder if present for the date window and stale-age settings.
3. Choose the output folder: `orrery-close/<period>/recon/` when a close is running, otherwise `orrery-recon/`.
4. Dispatch the **reconciler** agent with: both file paths, the absolute path to the method spec (`references/reconcile-method.md` in this skill's base directory), the output folder, the close folder for the review queue, and the date window.
   For a single small file pair you can follow the method inline instead: read `references/reconcile-method.md`. Implement it as a script in the output folder, run it, and confirm the method's checks pass.
5. Present the result:
   - One line per entity: match rate, difference, "fully explained" or the unexplained amount.
   - The breaks needing a person, largest first, with the question to answer.
   - The proposed journals count and where they are.
6. Offer to turn `proposed_journals.csv` into an import file for the user's ERP after approval.

## Method reference

The full method is in `references/reconcile-method.md`. Matching passes: reference plus amount, then amount plus date window, then fuzzy description within tolerance. Bank-only items are classified as bank fee, interest, FX, card or unknown. Outputs: `matched.csv`, `bank_breaks.csv`, `gl_breaks.csv`, `proposed_journals.csv`, `recon_summary.json`. Each entity in the summary has `unexplained`, which must be 0.00 when both files cover the same accounts and dates.
