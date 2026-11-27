# Orrery for FP&A

By **Christian Martinez**, The Financial Fox. [Website](https://www.christianmartinez-thefinancialfox.com/) · [LinkedIn](https://www.linkedin.com/in/christianmartinezthefinancialfox/)

Six AI agents that run the month-end close for an FP&A team. They reconcile, screen, explain, forecast, write and assemble. People approve. Nothing is posted to a ledger: every journal, explanation, forecast change and slide waits in a review queue for a named reviewer.

## Install

**Claude Code:**

```
/plugin marketplace add The-Financial-Fox/orrery-fpa
/plugin install orrery-fpa@financial-fox
```

**Claude app (web and desktop):** download this repository as a zip (Code > Download ZIP) and upload it from the plugins area of your Claude settings.

## Try it in one line

Say **"Show me an Orrery demo"**. Orrery generates a fictional three-entity October close (NL-BV, DE-GmbH, UK-Ltd, EUR) with planted issues, runs all six agents and stops at each sign-off gate.

## The crew

| Agent | Runs | What it does | Engine |
|---|---|---|---|
| reconciler | Day 1, 06:00 | Matches bank to GL cash per entity, proves the difference is fully explained by breaks, proposes clearing journals | `reconcile.py` |
| sentinel | Day 1, 06:00 | Scores every journal: weekend and after-hours, new vendors, duplicates, self-approval, just-under-limit amounts, sensitive accounts, Benford | `screen_journals.py` |
| variance-analyst | Day 1, 09:30 | Actual vs budget and prior, materiality, price-volume-mix, EBITDA bridge that reconciles to the cent, Excel with live formulas | `variance.py` |
| forecaster | Day 1, 14:00 | Rolls the year forward with P10/P50/P90, one-offs removed, known events as explicit adjustments, derived EBITDA range | `forecast.py` |
| narrator | Day 2, 06:00 | CFO commentary in house style with a citation on every figure | house-style guide |
| board-builder | Day 3, 08:00 | Board pack from approved figures only, with charts and a figure manifest | `charts.py` |

Numbers are always calculated by the Python engines, never estimated by the model.

## Skills

| Skill | Say | Does |
|---|---|---|
| close-run | "Run the October close", "continue the close" | Orchestrates all six agents with sign-off gates |
| close-setup | "Set up our close policy" | Writes `orrery-close-policy.md`: entities, materiality, approval limit, owners |
| reconcile-cash | "Reconcile the bank" | Reconciler on its own |
| journal-screening | "Screen the journals" | Sentinel on its own |
| variance-analysis | "Why did we miss budget?" | Variance Analyst on its own |
| rolling-forecast | "Where do we land this year?" | Forecaster on its own |
| write-commentary | "Draft the CFO summary" | Narrator on its own |
| board-pack | "Build the board pack" | Board Builder plus deck rendering |
| sign-off | "What needs my sign-off?", "approve PJ-0003" | Manages the review queue and audit log |

## Inputs

CSV or Excel exports. The agents map your column names; these are the minimum fields.

| Input | Minimum columns |
|---|---|
| Bank lines | date, amount, description (reference, entity optional) |
| GL cash lines | date, amount, description (reference, entity, je_id optional) |
| Journals | je_id, posted_at, account, amount (vendor, preparer, approver, invoice_ref recommended) |
| Actuals, budget, prior | period, entity, account, line, type (revenue, cogs, opex, other), amount |
| Sales by product (optional) | period, entity, product, scenario (actual or budget), units, revenue |
| Monthly history | period, metric, value |

## What it writes

```
orrery-close/2026-10/
  recon/       matched, breaks, proposed journals, summary
  sentinel/    flags, screening summary
  variance/    variance, material, pvm, bridge, variance.xlsx
  forecast/    monthly P10/P50/P90, FY outlook
  narrative/   commentary.md, citations.csv
  board/       board_pack.md, figures.csv, charts/
  review_queue.csv
  close_log.md
```

## Requirements

Python 3.9+ with pandas, numpy, openpyxl and matplotlib (present in Claude's standard environment). No API keys. Connect your ERP or planning tool as a connector if you want the agents to pull exports themselves; otherwise attach files.

## Controls by design

- Agents propose; only a person changes a status in the review queue.
- Every figure in commentary and the board pack cites its source row.
- Source files are never modified; normalised copies are written alongside.
- The close log records every stage, gate decision and reviewer.

## Learn to build agents like these

Orrery was built with the techniques taught in two programmes for finance professionals. The links below are partner links: I may earn a commission if you join.

- **AI Finance Club**: a yearly membership with monthly challenges on Claude, ChatGPT, Gemini and Copilot, live masterclasses, a recorded library and a forum with CFOs and finance leaders. [Join the Club](https://nicolasboucher.online/sp/ref-join-the-ai-finance-club/?utm_medium=aff-christianantonio-martinez-gmail-com&utm_content=&utm_source=)
- **AI Finance Accelerator**: a 6-week programme with weekly lectures and 1:1 coaching, from AI user to AI builder: dashboards, deterministic automation of finance data, Copilot agents and Claude skills. [See the Accelerator](https://nicolasboucher.online/sp/ai-finance-accelerator/?utm_medium=aff-christianantonio-martinez-gmail-com&utm_content=&utm_source=)
