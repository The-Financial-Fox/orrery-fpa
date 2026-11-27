---
name: sign-off
description: >
  This skill should be used when the user asks "what needs my sign-off", "show the review queue",
  "approve PJ-0003", "approve all reconciliation items", "reject that journal", "mark the commentary
  approved", "who approved what", or "/sign-off" during an Orrery close.
metadata:
  version: "0.1.0"
---

# Sign-off

Manage the review queue that holds every agent proposal. Agents propose; only the user changes a status.

## Queue file

`orrery-close/<period>/review_queue.csv` with columns:
`item_id, agent, type, entity, summary, amount, evidence, status, reviewer, decided_at, note`

Statuses: `proposed`, `needs_info`, `approved`, `rejected`. Types: `journal`, `recon_break`, `journal_flag`, `variance_explanation`, `forecast_change`, `commentary`, `board_slide`.

## Showing the queue

Group pending items by agent, largest amount first. For each: item_id, one-line summary, amount, and the evidence file and row. End with counts: pending, approved, rejected.

## Recording a decision

1. Accept decisions only from the user in this conversation, by item_id, by group ("all reconciler journals under 500") or by type. Repeat back exactly which items will change and ask for a yes before writing when more than 5 items or any amount over the materiality threshold is affected.
2. Set `status`, `reviewer` (the name the user gives; ask once if unknown), `decided_at` (ISO timestamp), and `note` (the reason for any rejection or the answer to a `needs_info` question).
3. Append a line to `close_log.md`: time, reviewer, items, decision.
4. If an answer to a `needs_info` item changes a number (for example an owner confirms a variance is timing), tell the user which stage should re-run.

## Exports

After journals are approved, offer an ERP import file of approved proposals only (CSV with entity, date, debit account, credit account, amount, memo citing the item_id). Never include proposed or rejected items.
