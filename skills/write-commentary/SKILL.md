---
name: write-commentary
description: >
  This skill should be used when the user asks to "write the commentary", "draft the CFO summary",
  "management commentary for the month", "explain the results in words", "exec summary of the close",
  or "/write-commentary", after variance or forecast outputs exist. Runs the Orrery Narrator with the
  house style and a citation on every figure.
metadata:
  version: "0.1.0"
---

# Write Commentary

Turn close outputs into short, causal, cited commentary in the house style.

## Steps

1. Find the close folder (`orrery-close/<period>/`) or the variance and forecast output folders. If there are no outputs yet, run **variance-analysis** first.
2. Confirm the audience: CFO (default), board, or entity owners. Each changes length and depth as set out in `references/house-style.md`.
3. Dispatch the **narrator** agent with the folder, audience, the absolute path to `references/house-style.md` in this skill's base directory, and the close policy if present.
4. Show the headline sentence, the commentary, and the open items. Offer two edits as quick choices: tighter (half the length) or more detail on one area.
5. If the user edits the text, save their version as `commentary_final.md` and keep citations intact.

## Quality bar

- Lead every paragraph with the cause, then the number.
- Every number carries a citation that matches `citations.csv`.
- Unconfirmed explanations are marked "owner to confirm" and listed as open items.
