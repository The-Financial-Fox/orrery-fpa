---
name: close-run
description: >
  This skill should be used when the user asks to "run the close", "run the month-end close",
  "start the October close", "continue the close", "where are we in the close", "/close-run",
  or "show me an Orrery demo" / "try Orrery on sample data". It orchestrates the six Orrery agents
  (reconciler, sentinel, variance-analyst, forecaster, narrator, board-builder) through the close
  calendar with human sign-off gates between stages.
metadata:
  version: "0.1.0"
---

# Close Run

Orchestrate a month-end close with the six Orrery agents. Agents do the work; people approve it. Nothing is ever posted to a ledger; every journal, explanation, forecast change and slide is a proposal in the review queue.

## 0. Set up the run

1. Determine the period (YYYY-MM). Default: the most recent complete month. State the assumption.
2. Read the close policy `orrery-close-policy.md` in the working folder. If it is missing, use the defaults in `../close-setup/references/default-policy.md` and say once that `/close-setup` can tailor them.
3. Locate the inputs. Look for files in the working folder or attachments; match by content, not only by name:

| Input | Used by | Minimum columns |
|---|---|---|
| Bank statement lines | reconciler | date, amount, description |
| GL cash lines | reconciler | date, amount, description |
| Journal entries | sentinel | je_id, posted_at, account, amount |
| Actuals and budget P&L | variance-analyst | period, entity, account, line, type, amount |
| Sales by product (optional) | variance-analyst | period, entity, product, scenario, units, revenue |
| Monthly history | forecaster | period, metric, value |

   If a connected ERP or planning tool can export these, use it. If inputs are missing, run the stages that have data and list what is missing; do not stop the whole close.
4. **Demo mode.** If the user asks for a demo or has no data, generate the sample close by following `references/demo-data.md` in this skill's base directory (shown as "Base directory for this skill"). Then use period 2026-10, period end 2026-10-31, FY start 2026-01, sensitive accounts `1999,4100`, and say the data is fictional.
5. Create the close folder `orrery-close/<period>/` with subfolders `recon, sentinel, variance, forecast, narrative, board`, and `review_queue.csv` with header `item_id,agent,type,entity,summary,amount,evidence,status,reviewer,decided_at,note`. Start `close_log.md` with the period, inputs found, policy values and the time.
6. Create a task list with the stages below so progress is visible.

Resolve each method spec from this skill's base directory: they live in sibling skills, at `../reconcile-cash/references/reconcile-method.md`, `../journal-screening/references/screening-method.md`, `../variance-analysis/references/variance-method.md`, `../rolling-forecast/references/forecast-method.md`. Pass absolute paths to agents. Each agent implements its method as a script in its output folder, runs it and confirms the method's checks pass.

## 1. Day 1 morning: reconcile and screen (parallel)

Dispatch **reconciler** and **sentinel** in the same turn. Give each: input paths, method spec path, output folder, close folder, policy values, period end. Wait for both.

Gate A: show the user a short table: match rate and unexplained difference per entity, breaks needing a person, high-risk journals. Ask for sign-off on the reconciliation (or note who signed off if the policy names an approver and the user confirms). Proceed to stage 2 if cash is fully explained even while individual breaks are open; record open breaks.

## 2. Day 1 afternoon: explain variances

Dispatch **variance-analyst** with actuals, budget, prior, sales, policy materiality and the method spec path. When it returns, check `bridge_reconciles: true`. Show the bridge as a compact table and the questions for budget owners.

## 3. Day 1 evening: roll the forecast

Dispatch **forecaster** with history, horizon (end of fiscal year), FY start, the one-offs identified by the variance analyst, any known events the user mentioned, and the method spec path. Show FY P10/P50/P90 and the movement.

## 4. Day 2: commentary

Dispatch **narrator** with the close folder, audience (default CFO), and the style guide path `../write-commentary/references/house-style.md`. Show the headline sentence and open items.

Gate B: ask the user to approve, edit or reject the commentary and the forecast change. Record decisions with the **sign-off** skill's conventions (status, reviewer, decided_at). If the user edits text, save their version as `narrative/commentary_final.md`.

## 5. Day 3: board pack

Run the **board-pack** skill, which dispatches **board-builder** and renders the deck.

## 6. Close summary

Finish with: what closed, what is pending sign-off (count by agent), the deck, and the close folder. Update `close_log.md` with each stage, timestamps, and gate decisions. Offer the Excel variance workbook and the deck as the two things worth opening.

## Resuming

If the user says "continue the close" or "where are we", read `close_log.md` and `review_queue.csv`, report the current stage and pending approvals, then continue from the first incomplete stage. Never re-run a completed stage unless asked or its inputs changed.

## Rules

- Agents propose; people approve. Do not mark anything approved without the user saying so.
- Quote numbers only from the outputs of the scripts the agents ran.
- Keep chat updates short; details live in the close folder.
