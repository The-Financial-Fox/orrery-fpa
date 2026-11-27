---
name: close-setup
description: >
  This skill should be used when the user asks to "set up Orrery", "set up our close policy",
  "configure the close agents", "change our materiality threshold", "/close-setup", or wants
  to tell the agents about their entities, currency, approval limits, close calendar,
  sign-off owners or commentary style.
metadata:
  version: "0.1.0"
---

# Close Setup

Write the close policy that every Orrery agent reads: `orrery-close-policy.md` in the user's working folder.

## Steps

1. Start from `references/default-policy.md`. If `orrery-close-policy.md` already exists, read it and change only what the user asks.
2. Ask only for what is unknown, using AskUserQuestion with concrete options (at most 4 questions per round):
   - Entities and reporting currency.
   - Materiality: absolute amount and percentage (offer 25k/5%, 50k/5%, 100k/10%).
   - Journal approval threshold and business hours.
   - Sensitive accounts (suspense, intercompany, manual revenue).
   - Fiscal year start and close calendar (working days to close).
   - Sign-off owners per stage (reconciliation, variance, forecast, commentary, board pack).
   - Commentary audience and tone if it differs from the default house style.
   Infer what you can from files the user has attached (entity codes, currency, account ranges) and confirm instead of asking.
3. Write the policy file with the same headings as the default. Keep values in the tables so agents can read them.
4. Summarise the policy in five lines and point out any setting that will make an agent noisy (for example business hours narrower than the team's real hours).

## Notes

- The policy is plain markdown so a controller can edit it directly.
- Never store credentials or bank account numbers in the policy.
