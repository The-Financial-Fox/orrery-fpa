# Board chart method

Draw up to three 1600×900 PNG charts from a close folder into `<close folder>/board/charts/`. Write a short matplotlib script in that folder (for example `charts_run.py`, using the Agg backend), run it, then open each PNG once to confirm it rendered. Draw only from the close outputs; never type a number into a chart by hand.

## Style

- Figure 16×9 inches at 100 dpi. Background `#0D1419` for figure and axes. No spines.
- Ticks and axis labels `#8E9995`, size 11. Light horizontal grid (`#ECE7DB`, alpha 0.08) behind the bars.
- Colours: favourable `#63B9A7`, adverse `#E2775C`, totals `#8E9995`, accent `#D9A54A`, text `#ECE7DB`.
- Money labels: `12.4M` at 1 million or more, otherwise `850k`. Title left-aligned, size 18, text colour.
- Save with the background colour and `tight_layout`.

## bridge.png (needs `variance/bridge.csv`)

A waterfall in bridge order. Totals are full bars from 0 in the totals colour, labelled with the value in bold. Deltas float from the running total: favourable colour if >= 0, adverse otherwise, labelled `+850k` or `-600k`; a thin dotted connector to the next bar. X labels are the step names without any `COGS: ` or `Opex: ` prefix, wrapped at 12 characters. Y axis from 0 to 1.32 × the largest total or running value. Title: "EBITDA bridge, plan to actual".

## revenue.png (needs `variance/variance.csv`)

Revenue rows only, actual and budget summed by entity. Grouped bars per entity: budget in the totals colour, actual in the accent colour, with the actual − budget difference above the actual bar (favourable or adverse colour). Legend without frame. Title: "Revenue by entity, actual vs budget".

## forecast.png (needs `forecast/forecast.csv`)

For the chosen metric (default revenue). If a history file is given: the last 18 actual months as a solid text-colour line, with a dashed accent line joining the last actual to the first P50. A P10-to-P90 band in the favourable colour at alpha 0.22 and the P50 as a dashed accent line. X labels rotated 45°. Title: "{Metric} forecast range".

## Report

List the charts written. If a chart's input file is missing, say so and skip that chart.
