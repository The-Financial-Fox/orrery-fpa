#!/usr/bin/env python3
"""Orrery Forecaster engine: roll a monthly forecast forward with P10/P50/P90 bands.

Method (deliberately simple and explainable):
  * multiplicative seasonal index per calendar month (needs >= 24 months, otherwise none)
  * linear trend on the de-seasonalised last --trend-window months
  * uncertainty: block-bootstrap of de-seasonalised residuals, --sims paths
  * optional driver overrides, e.g. --adjust "revenue:2026-12:+250000" for known events

Usage:
  python3 forecast.py --history history.csv --out ./out --through 2026-12 [--fy-start 2026-01]
         [--metrics revenue,opex] [--sims 4000] [--trend-window 18] [--adjust metric:YYYY-MM:+/-amount ...]

history.csv columns: period (YYYY-MM), metric, value   (actuals only)
Outputs: forecast.csv (monthly P10/P50/P90), fy_outlook.csv, forecast_summary.json
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

def season_index(s):
    if len(s) < 24:
        return pd.Series(1.0, index=range(1, 13))
    df = pd.DataFrame({"v": s.values}, index=s.index)
    df["ma"] = df.v.rolling(12, center=True, min_periods=12).mean()
    df["ratio"] = df.v / df.ma
    df["m"] = [p.month for p in df.index]
    idx = df.groupby("m").ratio.mean().reindex(range(1, 13)).fillna(1.0)
    return idx / idx.mean()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--history", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--through", required=True, help="last month to forecast, YYYY-MM")
    ap.add_argument("--fy-start", help="first month of the fiscal year, YYYY-MM")
    ap.add_argument("--metrics"); ap.add_argument("--sims", type=int, default=4000)
    ap.add_argument("--trend-window", type=int, default=18)
    ap.add_argument("--adjust", action="append", default=[])
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)

    h = pd.read_csv(a.history); h.columns = [c.strip().lower() for c in h.columns]
    if not {"period", "metric", "value"} <= set(h.columns):
        sys.exit("history needs columns period, metric, value")
    h["period"] = pd.PeriodIndex(h["period"].astype(str).str[:7], freq="M")
    metrics = a.metrics.split(",") if a.metrics else sorted(h.metric.unique())
    through = pd.Period(a.through, "M")
    adj = {}
    for s in a.adjust:
        m, p, v = s.split(":"); adj[(m, pd.Period(p, "M"))] = float(v)

    rows, fy, notes, fy_sims = [], [], [], {}
    for met in metrics:
        s = h[h.metric == met].groupby("period").value.sum().sort_index()
        if len(s) < 6:
            notes.append(f"{met}: only {len(s)} months of history, skipped (need 6+)"); continue
        full = pd.period_range(s.index.min(), s.index.max(), freq="M")
        if len(full) != len(s):
            notes.append(f"{met}: {len(full)-len(s)} missing months filled by interpolation")
            s = s.reindex(full).interpolate()
        si = season_index(s)
        ds = s / np.array([si[p.month] for p in s.index])
        w = ds.iloc[-a.trend_window:]
        x = np.arange(len(w)); slope, icpt = np.polyfit(x, w.values, 1)
        fitted = icpt + slope * x
        resid = (w.values - fitted) / np.where(fitted == 0, 1, fitted)  # relative residuals
        resid = resid - resid.mean()
        last = s.index.max()
        horizon = pd.period_range(last + 1, through, freq="M")
        if len(horizon) == 0:
            notes.append(f"{met}: history already reaches {through}"); continue
        n = len(horizon)
        base = np.array([(icpt + slope * (len(w) - 1 + i + 1)) * si[p.month] for i, p in enumerate(horizon)])
        for i, p in enumerate(horizon):
            base[i] += adj.get((met, p), 0.0)
        # block bootstrap (blocks of 3) of relative residuals
        sims = np.empty((a.sims, n))
        for k in range(a.sims):
            path = []
            while len(path) < n:
                j = rng.integers(0, max(1, len(resid) - 2)); path.extend(resid[j:j + 3])
            sims[k] = base * (1 + np.array(path[:n]))
        p10, p50, p90 = np.percentile(sims, [10, 50, 90], axis=0)
        for i, p in enumerate(horizon):
            rows.append({"metric": met, "period": str(p), "p10": round(p10[i], 2), "p50": round(p50[i], 2),
                         "p90": round(p90[i], 2), "point": round(base[i], 2),
                         "seasonal_index": round(float(si[p.month]), 3), "adjustment": adj.get((met, p), 0.0)})
        if a.fy_start:
            fs = pd.Period(a.fy_start, "M")
            ytd = float(s[(s.index >= fs) & (s.index <= last)].sum())
            in_fy = np.array([(p >= fs) and (p < fs + 12) for p in horizon])
            rem = sims[:, in_fy].sum(axis=1)
            tot = ytd + rem
            fy_sims[met] = tot
            q = np.percentile(tot, [10, 50, 90])
            fy.append({"metric": met, "fy_start": str(fs), "actual_months": int(((s.index >= fs) & (s.index <= last)).sum()),
                       "ytd_actual": round(ytd, 2), "remaining_point": round(float(base[in_fy].sum()), 2),
                       "fy_p10": round(q[0], 2), "fy_p50": round(q[1], 2), "fy_p90": round(q[2], 2)})
        notes.append(f"{met}: trend {slope:+,.0f}/month (de-seasonalised), residual sd {np.std(resid)*100:.1f}%, "
                     f"seasonality {'on' if len(s) >= 24 else 'off (under 24 months)'}")

    if {"revenue", "cogs", "opex"} <= set(fy_sims):
        e = fy_sims["revenue"] - fy_sims["cogs"] - fy_sims["opex"]
        q = np.percentile(e, [10, 50, 90])
        fy.append({"metric": "ebitda (derived)", "fy_start": a.fy_start, "actual_months": None, "ytd_actual": None,
                   "remaining_point": None, "fy_p10": round(q[0], 2), "fy_p50": round(q[1], 2), "fy_p90": round(q[2], 2)})
        notes.append("ebitda (derived): revenue minus cogs minus opex per simulated path; assumes independent errors, so bands are slightly wide")
    f = pd.DataFrame(rows); f.to_csv(out / "forecast.csv", index=False)
    pd.DataFrame(fy).to_csv(out / "fy_outlook.csv", index=False)
    summary = {"through": a.through, "metrics": metrics, "fy_outlook": fy, "notes": notes,
               "method": "seasonal index x linear trend, block-bootstrapped residual bands",
               "files": ["forecast.csv", "fy_outlook.csv"]}
    (out / "forecast_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
