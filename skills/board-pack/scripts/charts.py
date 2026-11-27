#!/usr/bin/env python3
"""Orrery Board Builder chart engine. Reads a close folder and writes 1600x900 PNG charts:
  bridge.png       EBITDA bridge waterfall (plan to actual)
  revenue.png      revenue actual vs budget by entity
  forecast.png     monthly fan: actuals, P10-P90 band, P50 (first metric or --metric)

Usage: python3 charts.py --close orrery-close/2026-10 [--history history.csv] [--metric revenue] [--currency EUR]
"""
import argparse, json, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

INK, PANEL, FG, MUTED = "#0D1419", "#0D1419", "#ECE7DB", "#8E9995"
FAV, ADV, TOT, ACC = "#63B9A7", "#E2775C", "#8E9995", "#D9A54A"

def style(ax, fig):
    fig.patch.set_facecolor(INK); ax.set_facecolor(PANEL)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=11); ax.yaxis.label.set_color(MUTED)
    ax.grid(axis="y", color="#ECE7DB", alpha=.08); ax.set_axisbelow(True)

def fmt_m(v):
    return f"{v/1e6:,.1f}M" if abs(v) >= 1e6 else f"{v/1e3:,.0f}k"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--close", required=True); ap.add_argument("--history")
    ap.add_argument("--metric", default="revenue"); ap.add_argument("--currency", default="EUR")
    a = ap.parse_args()
    c = Path(a.close); out = c / "board" / "charts"; out.mkdir(parents=True, exist_ok=True)
    made = []

    br = c / "variance" / "bridge.csv"
    if br.exists():
        b = pd.read_csv(br)
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100); style(ax, fig)
        run = 0; xs = range(len(b))
        for i, r in b.iterrows():
            if r.kind == "total":
                ax.bar(i, r.value, color=TOT, width=.62); top = r.value; run = r.value
                ax.text(i, top, fmt_m(r.value), ha="center", va="bottom", color=FG, fontsize=12, fontweight="bold")
            else:
                lo, hi = sorted([run, run + r.value])
                ax.bar(i, hi - lo, bottom=lo, color=FAV if r.value >= 0 else ADV, width=.62)
                ax.text(i, hi, ("+" if r.value >= 0 else "-") + fmt_m(abs(r.value)), ha="center", va="bottom", color=FG, fontsize=11)
                if i < len(b) - 1:
                    ax.plot([i + .31, i + .69], [run + r.value] * 2, color=MUTED, lw=.8, ls=":")
                run += r.value
        ax.set_xticks(list(xs)); ax.set_xticklabels([textwrap.fill(s.split(": ", 1)[-1], 12) for s in b.step], color=MUTED, fontsize=10)
        ax.set_ylabel(f"{a.currency}"); ax.set_ylim(0, max(b.value.max(), run) * 1.32)
        ax.yaxis.set_major_formatter(lambda v, _: fmt_m(v))
        ax.set_title("EBITDA bridge, plan to actual", color=FG, fontsize=18, loc="left", pad=16)
        fig.tight_layout(); fig.savefig(out / "bridge.png", facecolor=INK); plt.close(fig); made.append("bridge.png")

    vc = c / "variance" / "variance.csv"
    if vc.exists():
        v = pd.read_csv(vc); r = v[v.type == "revenue"].groupby("entity")[["actual", "budget"]].sum()
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100); style(ax, fig)
        x = range(len(r)); w = .36
        ax.bar([i - w/2 for i in x], r.budget, w, color=TOT, label="Budget")
        ax.bar([i + w/2 for i in x], r.actual, w, color=ACC, label="Actual")
        for i, (ent, row) in enumerate(r.iterrows()):
            d = row.actual - row.budget
            ax.text(i + w/2, row.actual, ("+" if d >= 0 else "-") + fmt_m(abs(d)), ha="center", va="bottom",
                    color=FAV if d >= 0 else ADV, fontsize=12)
        ax.set_xticks(list(x)); ax.set_xticklabels(r.index, color=FG, fontsize=13)
        ax.yaxis.set_major_formatter(lambda v, _: fmt_m(v)); ax.set_ylabel(a.currency)
        ax.legend(frameon=False, labelcolor=FG, fontsize=12)
        ax.set_title("Revenue by entity, actual vs budget", color=FG, fontsize=18, loc="left", pad=16)
        fig.tight_layout(); fig.savefig(out / "revenue.png", facecolor=INK); plt.close(fig); made.append("revenue.png")

    fc = c / "forecast" / "forecast.csv"
    if fc.exists():
        f = pd.read_csv(fc); f = f[f.metric == a.metric]
        fig, ax = plt.subplots(figsize=(16, 9), dpi=100); style(ax, fig)
        if a.history and Path(a.history).exists():
            h = pd.read_csv(a.history); h = h[h.metric == a.metric].tail(18)
            ax.plot(h.period, h.value, color=FG, lw=2, label="Actual")
            if len(f):
                ax.plot([h.period.iloc[-1], f.period.iloc[0]], [h.value.iloc[-1], f.p50.iloc[0]], color=ACC, lw=2, ls="--")
        ax.fill_between(f.period, f.p10, f.p90, color=FAV, alpha=.22, label="P10 to P90")
        ax.plot(f.period, f.p50, color=ACC, lw=2.4, ls="--", label="P50")
        ax.yaxis.set_major_formatter(lambda v, _: fmt_m(v)); ax.set_ylabel(a.currency)
        ax.tick_params(axis="x", rotation=45); ax.legend(frameon=False, labelcolor=FG, fontsize=12)
        ax.set_title(f"{a.metric.capitalize()} forecast range", color=FG, fontsize=18, loc="left", pad=16)
        fig.tight_layout(); fig.savefig(out / "forecast.png", facecolor=INK); plt.close(fig); made.append("forecast.png")

    print(json.dumps({"charts": [str(out / m) for m in made]}, indent=2))

if __name__ == "__main__":
    main()
