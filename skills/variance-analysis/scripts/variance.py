#!/usr/bin/env python3
"""Orrery Variance Analyst engine: budget vs actual (and vs prior period),
materiality flags, price-volume-mix decomposition and an EBITDA bridge.

Usage:
  python3 variance.py --actuals actuals.csv --budget budget.csv --period 2026-10 --out ./out
         [--prior prior.csv] [--sales sales.csv] [--abs 50000] [--pct 5] [--currency EUR]

P&L files (actuals, budget, prior) columns:
  period (YYYY-MM), entity, account, line, type, amount
  type is one of: revenue, cogs, opex, other  (other = below EBITDA, excluded from bridge)
  Amounts are positive for both revenue and costs.

Optional sales file for price/volume/mix (per product):
  period, entity, product, scenario (actual|budget), units, revenue

Outputs: variance.csv, material.csv, pvm.csv, bridge.csv, variance.xlsx (live formulas), variance_summary.json
"""
import argparse, json, sys
from pathlib import Path
import pandas as pd

KEYS = ["entity", "account", "line", "type"]
EBITDA_TYPES = ("revenue", "cogs", "opex")

def load(path, period, label):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    need = {"period", "entity", "account", "line", "type", "amount"}
    miss = need - set(df.columns)
    if miss:
        sys.exit(f"{label} is missing columns {sorted(miss)}")
    df["period"] = df["period"].astype(str).str[:7]
    df["type"] = df["type"].str.lower().str.strip()
    bad = set(df["type"]) - {"revenue", "cogs", "opex", "other"}
    if bad:
        sys.exit(f"{label} has unknown type values {sorted(bad)}; use revenue, cogs, opex or other")
    if period:
        df = df[df["period"] == period]
    if df.empty:
        sys.exit(f"{label} has no rows for period {period}")
    dups = df.duplicated(KEYS + ["period"]).sum()
    if dups:
        print(f"warning: {label} has {dups} duplicate key rows; they are summed", file=sys.stderr)
    return df.groupby(KEYS, as_index=False)["amount"].sum()

def fav_sign(t):
    return 1 if t == "revenue" else -1

def ebitda(df):
    s = df.groupby("type")["amount"].sum()
    return float(s.get("revenue", 0) - s.get("cogs", 0) - s.get("opex", 0))

def pvm(sales_path, period):
    s = pd.read_csv(sales_path)
    s.columns = [c.strip().lower() for c in s.columns]
    s["period"] = s["period"].astype(str).str[:7]
    s = s[s["period"] == period]
    s["scenario"] = s["scenario"].str.lower()
    a = s[s.scenario == "actual"].groupby(["entity", "product"])[["units", "revenue"]].sum()
    b = s[s.scenario == "budget"].groupby(["entity", "product"])[["units", "revenue"]].sum()
    df = a.join(b, lsuffix="_a", rsuffix="_b", how="outer").fillna(0).reset_index()
    df["price_a"] = (df.revenue_a / df.units_a).where(df.units_a > 0, 0)
    df["price_b"] = (df.revenue_b / df.units_b).where(df.units_b > 0, 0)
    rows = []
    for ent, g in df.groupby("entity"):
        ua, ub = g.units_a.sum(), g.units_b.sum()
        avg_pb = g.revenue_b.sum() / ub if ub else 0
        for r in g.itertuples():
            share_b = r.units_b / ub if ub else 0
            vol = (ua * share_b - r.units_b) * r.price_b
            mix = (r.units_a - ua * share_b) * r.price_b
            # new products (no budget price) -> whole effect is mix at actual price
            if r.units_b == 0:
                mix = r.revenue_a; vol = 0; price = 0
            else:
                price = (r.price_a - r.price_b) * r.units_a
            rows.append({"entity": ent, "product": r.product, "units_actual": r.units_a, "units_budget": r.units_b,
                         "price_actual": round(r.price_a, 4), "price_budget": round(r.price_b, 4),
                         "volume_effect": round(vol, 2), "mix_effect": round(mix, 2), "price_effect": round(price, 2),
                         "total_variance": round(r.revenue_a - r.revenue_b, 2)})
    out = pd.DataFrame(rows)
    if len(out):
        out["check"] = (out.volume_effect + out.mix_effect + out.price_effect - out.total_variance).round(2)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--actuals", required=True); ap.add_argument("--budget", required=True)
    ap.add_argument("--prior"); ap.add_argument("--sales")
    ap.add_argument("--period", required=True); ap.add_argument("--prior-period")
    ap.add_argument("--out", required=True)
    ap.add_argument("--abs", type=float, default=50000); ap.add_argument("--pct", type=float, default=5)
    ap.add_argument("--currency", default="EUR")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    act = load(a.actuals, a.period, "actuals"); bud = load(a.budget, a.period, "budget")
    df = act.merge(bud, on=KEYS, how="outer", suffixes=("_actual", "_budget")).fillna({"amount_actual": 0, "amount_budget": 0})
    df = df.rename(columns={"amount_actual": "actual", "amount_budget": "budget"})
    if a.prior:
        pp = a.prior_period or (pd.Period(a.period, "M") - 1).strftime("%Y-%m")
        pr = load(a.prior, pp, "prior").rename(columns={"amount": "prior"})
        df = df.merge(pr, on=KEYS, how="left").fillna({"prior": 0})
        df["vs_prior"] = df.actual - df.prior
    df["variance"] = df.actual - df.budget
    df["variance_pct"] = (df.variance / df.budget.abs() * 100).where(df.budget != 0).round(2)
    df["ebitda_impact"] = df.apply(lambda r: r.variance * fav_sign(r.type) if r.type in EBITDA_TYPES else 0, axis=1)
    df["direction"] = df.ebitda_impact.apply(lambda v: "favourable" if v > 0 else ("adverse" if v < 0 else "on plan"))
    df.loc[df.type == "other", "direction"] = df.loc[df.type == "other"].apply(
        lambda r: "favourable" if r.variance < 0 else ("adverse" if r.variance > 0 else "on plan"), axis=1)
    df["material"] = (df.variance.abs() >= a.abs) | ((df.variance_pct.abs() >= a.pct) & (df.variance.abs() >= a.abs * 0.25))
    df = df.sort_values("variance", key=lambda s: -s.abs()).reset_index(drop=True)
    df.insert(0, "row_id", [f"V{i+1:03d}" for i in range(len(df))])
    df.to_csv(out / "variance.csv", index=False)
    mat = df[df.material]
    mat.to_csv(out / "material.csv", index=False)

    # PVM
    pv = pvm(a.sales, a.period) if a.sales else pd.DataFrame()
    pv.to_csv(out / "pvm.csv", index=False)

    # Bridge
    plan_e, act_e = ebitda(bud), ebitda(act)
    items = []
    rev_var = float(df[df.type == "revenue"].variance.sum())
    if len(pv):
        for k in ("volume", "price", "mix"):
            v = float(pv[f"{k}_effect"].sum())
            if abs(v) >= 0.005:
                items.append((k.capitalize(), v, "pvm.csv"))
        other_rev = rev_var - sum(v for _, v, _ in items)
        if abs(other_rev) >= 0.5:
            items.append(("Other revenue", other_rev, "variance.csv"))
    else:
        for r in df[df.type == "revenue"].groupby("line").variance.sum().items():
            items.append((f"Revenue: {r[0]}", float(r[1]), "variance.csv"))
    for t in ("cogs", "opex"):
        g = df[df.type == t].groupby("line").ebitda_impact.sum()
        small = 0.0
        for line, v in g.items():
            if abs(v) >= a.abs * 0.5:
                items.append((f"{t.upper() if t == 'cogs' else 'Opex'}: {line}", float(v), "variance.csv"))
            else:
                small += float(v)
        if abs(small) >= 0.5:
            items.append((f"{'COGS' if t == 'cogs' else 'Opex'}: other lines", small, "variance.csv"))
    bridge = [{"step": "Plan EBITDA", "value": round(plan_e, 2), "kind": "total", "source": "budget"}]
    bridge += [{"step": n, "value": round(v, 2), "kind": "delta", "source": s} for n, v, s in items]
    bridge.append({"step": "Actual EBITDA", "value": round(act_e, 2), "kind": "total", "source": "actuals"})
    br = pd.DataFrame(bridge)
    gap = round(plan_e + sum(v for _, v, _ in items) - act_e, 2)
    br.to_csv(out / "bridge.csv", index=False)

    # Excel with live formulas
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment
        wb = Workbook(); ws = wb.active; ws.title = "Variance"
        hdr = ["Row", "Entity", "Account", "Line", "Type", "Actual", "Budget", "Variance", "Var %", "EBITDA impact", "Material"]
        ws.append(hdr)
        for i, r in enumerate(df.itertuples(), start=2):
            sign = 1 if r.type == "revenue" else (-1 if r.type in ("cogs", "opex") else 0)
            ws.append([r.row_id, r.entity, r.account, r.line, r.type, r.actual, r.budget,
                       f"=F{i}-G{i}", f'=IF(G{i}=0,"",H{i}/ABS(G{i}))', f"=H{i}*{sign}",
                       f'=IF(OR(ABS(H{i})>={a.abs},AND(ISNUMBER(I{i}),ABS(I{i})>={a.pct/100},ABS(H{i})>={a.abs*0.25})),"YES","")'])
        n = len(df) + 1
        ws.append([]); ws.append(["Total EBITDA impact", "", "", "", "", "", "", "", "", f"=SUM(J2:J{n})"])
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="0D1419")
        for col in "FGHJ":
            for c in ws[col][1:]:
                c.number_format = '#,##0;[Red]-#,##0'
        for c in ws["I"][1:]:
            c.number_format = "0.0%"
        for col, w in zip("ABCDEFGHIJK", [7, 10, 10, 26, 9, 14, 14, 14, 9, 15, 9]):
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "A2"
        wb2 = wb.create_sheet("Bridge")
        wb2.append(["Step", f"Value ({a.currency})", "Running", "Source"])
        for i, r in enumerate(br.itertuples(), start=2):
            run = f"=B{i}" if i == 2 else (f"=B{i}" if r.kind == "total" else f"=C{i-1}+B{i}")
            wb2.append([r.step, r.value, run, r.source])
        last = len(br) + 1
        wb2.append(["Check (running before actual minus actual)", "", f"=C{last-1}-B{last}", ""])
        for c in wb2[1]:
            c.font = Font(bold=True)
        for c in list(wb2["B"][1:]) + list(wb2["C"][1:]):
            c.number_format = '#,##0;[Red]-#,##0'
        wb2.column_dimensions["A"].width = 40; wb2.column_dimensions["B"].width = 16; wb2.column_dimensions["C"].width = 16
        if len(pv):
            w3 = wb.create_sheet("Price-Volume-Mix")
            w3.append(list(pv.columns))
            for r in pv.itertuples(index=False):
                w3.append(list(r))
        wb.save(out / "variance.xlsx")
    except Exception as e:
        print(f"warning: could not write xlsx ({e})", file=sys.stderr)

    summary = {
        "period": a.period, "currency": a.currency,
        "materiality": {"abs": a.abs, "pct": a.pct},
        "revenue": {"actual": round(float(act[act.type == "revenue"].amount.sum()), 2),
                    "budget": round(float(bud[bud.type == "revenue"].amount.sum()), 2)},
        "ebitda": {"actual": round(act_e, 2), "budget": round(plan_e, 2), "variance": round(act_e - plan_e, 2)},
        "lines": int(len(df)), "material_lines": int(len(mat)),
        "top_material": mat.head(8)[["row_id", "entity", "line", "type", "actual", "budget", "variance", "variance_pct", "direction"]]
                        .to_dict(orient="records"),
        "pvm_total": ({k: round(float(pv[f"{k}_effect"].sum()), 2) for k in ("volume", "price", "mix")} if len(pv) else None),
        "pvm_check_max_abs": (float(pv["check"].abs().max()) if len(pv) else None),
        "bridge": bridge, "bridge_reconciles": gap == 0, "bridge_gap": gap,
        "files": ["variance.csv", "material.csv", "pvm.csv", "bridge.csv", "variance.xlsx"],
    }
    (out / "variance_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))

if __name__ == "__main__":
    main()
