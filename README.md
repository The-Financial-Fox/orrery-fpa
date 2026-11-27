# Orrery for FP&A

By **Christian Martinez**, The Financial Fox. [Website](https://www.christianmartinez-thefinancialfox.com/) · [LinkedIn](https://www.linkedin.com/in/christianmartinezthefinancialfox/) · [Privacy](https://github.com/The-Financial-Fox/orrery-fpa/blob/directory/PRIVACY.md)

**Directory edition.** This edition ships every calculation as a written method that Claude implements and runs as code in your session, with checks that must pass before any number is reported. The [full edition on GitHub](https://github.com/The-Financial-Fox/orrery-fpa) (branch `main`) ships the same methods as fixed Python engines.

Six AI agents that run the month-end close for an FP&A team. They reconcile, screen, explain, forecast, write and assemble. People approve. Nothing is posted to a ledger: every journal, explanation, forecast change and slide waits in a review queue for a named reviewer.

## Important: educational use

Orrery is a free, open-source **educational and demonstration tool**. It shows how AI agents can support a month-end close. It is not accounting, audit, tax, legal or financial advice, and it is not a substitute for your own controls or for a qualified professional.

- Every output is a **draft**: reconciliations, journal flags, variances, forecasts, commentary and board slides must be reviewed and approved by a qualified person before anyone relies on them.
- AI can make mistakes, including in calculations. Check the figures against your source systems.
- Nothing is posted to any ledger. You remain responsible for every decision and every number you use.
- Only use data you are permitted to share with Claude under your organisation's policies.
- The demo company, people and figures are fictional.

Orrery is provided "as is", without warranty of any kind, and the author accepts no liability for its use, as set out in the [MIT licence](LICENSE).

## Install

Install this edition from the plugin directory in Claude.

For the full edition with the Python engines, in Claude Code:

```
/plugin marketplace add The-Financial-Fox/orrery-fpa
/plugin install orrery-fpa@financial-fox
```

## Try it in one line

Say **"Show me an Orrery demo"**. Orrery generates a fictional three-entity October close (NL-BV, DE-GmbH, UK-Ltd, EUR) with planted issues, runs all six agents and stops at each sign-off gate.

## The crew

| Agent | Runs | What it does | Method |
|---|---|---|---|
| reconciler | Day 1, 06:00 | Matches bank to GL cash per entity, proves the difference is fully explained by breaks, proposes clearing journals | `reconcile-method.md` |
| sentinel | Day 1, 06:00 | Scores every journal: weekend and after-hours, new vendors, duplicates, self-approval, just-under-limit amounts, sensitive accounts, Benford | `screening-method.md` |
| variance-analyst | Day 1, 09:30 | Actual vs budget and prior, materiality, price-volume-mix, EBITDA bridge that reconciles to the cent, Excel with live formulas | `variance-method.md` |
| forecaster | Day 1, 14:00 | Rolls the year forward with P10/P50/P90, one-offs removed, known events as explicit adjustments, derived EBITDA range | `forecast-method.md` |
| narrator | Day 2, 06:00 | CFO commentary in house style with a citation on every figure | house-style guide |
| board-builder | Day 3, 08:00 | Board pack from approved figures only, with charts and a figure manifest | `charts-method.md` |

Numbers are always calculated in code that Claude writes from these methods and runs in your session, never estimated by the model. Each method ends with checks (the reconciliation difference is fully explained, the bridge sums to the cent, P10 ≤ P50 ≤ P90) that must pass before anything is reported.

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

Claude's code execution with Python, pandas, numpy, openpyxl and matplotlib (present in Claude's standard environment). The plugin itself contains only Markdown and JSON. It sends nothing anywhere and fetches nothing: every calculation runs on the files you attach, inside your session. No API keys. Connect your ERP or planning tool as a connector if you want the agents to pull exports themselves; otherwise attach files.

## Controls by design

- Agents propose; only a person changes a status in the review queue.
- Every figure in commentary and the board pack cites its source row.
- Source files are never modified; normalised copies are written alongside.
- The close log records every stage, gate decision and reviewer.

## Learn to build agents like these

Orrery was built with the techniques taught in two programmes for finance professionals. The links below are partner links: I may earn a commission if you join.

- **AI Finance Club**: a yearly membership with monthly challenges on Claude, ChatGPT, Gemini and Copilot, live masterclasses, a recorded library and a forum with CFOs and finance leaders. [Join the Club](https://nicolasboucher.online/sp/ref-join-the-ai-finance-club/?utm_medium=aff-christianantonio-martinez-gmail-com&utm_content=&utm_source=)
- **AI Finance Accelerator**: a 6-week programme with weekly lectures and 1:1 coaching, from AI user to AI builder: dashboards, deterministic automation of finance data, Copilot agents and Claude skills. [See the Accelerator](https://nicolasboucher.online/sp/ai-finance-accelerator/?utm_medium=aff-christianantonio-martinez-gmail-com&utm_content=&utm_source=)
