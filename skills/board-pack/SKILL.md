---
name: board-pack
description: >
  This skill should be used when the user asks to "build the board pack", "make the board deck",
  "prepare the monthly board slides", "turn the close into a deck", or "/board-pack", after the close
  outputs exist. Runs the Orrery Board Builder and renders a deck that uses approved figures only.
metadata:
  version: "0.1.0"
---

# Board Pack

Assemble the board deck from approved close outputs and render it.

## Steps

1. Find the close folder `orrery-close/<period>/`. If the variance, forecast or commentary outputs are missing, say which and offer to run those stages first.
2. Read `review_queue.csv`. Tell the user how many items are approved and pending. If the commentary or forecast is not approved, ask once: approve now, or build a DRAFT with a pending slide.
3. Dispatch the **board-builder** agent with the close folder, period, currency, company name, the history file path, and absolute paths (from this skill's base directory) to `references/board-outline.md` and the chart engine `scripts/charts.py`.
4. Render the deck from `board/board_pack.md` and `board/charts/`:
   - If a slide-deck artifact type is available in this session, create the deck from it.
   - If the user asked for PowerPoint, or no slide type exists, load the pptx skill and build a .pptx.
   - Use the company's design system or brand if one is available; otherwise a restrained dark-ink and brass palette with the charts full-width.
5. Check the rendered deck once: every slide title is an assertion, every figure matches `figures.csv`, DRAFT appears on every slide when anything is pending.
6. Deliver the deck with one line: slide count, FINAL or DRAFT, and pending items.
