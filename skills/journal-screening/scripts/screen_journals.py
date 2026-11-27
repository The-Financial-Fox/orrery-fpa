#!/usr/bin/env python3
"""Orrery Sentinel engine: screen journal entries for risk indicators.

Rules (each adds to a risk score; weights in RULES):
  weekend          posted Saturday or Sunday
  after_hours      posted outside --hours (default 07-20 local)
  round_amount     amount >= 1,000 and a multiple of 1,000
  below_threshold  within 5% below the approval threshold (--approval)
  new_vendor       vendor not in --vendors master (or first appearance in the file)
  duplicate        same vendor and amount within 30 days, or near-identical invoice refs (INV-7781 / INV-7781A)
  self_approved    preparer equals approver, or approver missing
  sensitive_acct   account in --sensitive list (suspense, intercompany, manual revenue, etc.)
  period_end       posted in the last 2 days of the period or after period end (--period-end)
Population test: Benford first-digit mean absolute deviation (MAD) on amounts >= 10.

Usage:
  python3 screen_journals.py --journals journals.csv --out ./out [--vendors vendors.csv]
         [--approval 50000] [--hours 7-20] [--sensitive 1999,1800,4990] [--period-end 2026-10-31]

journals.csv columns: je_id, posted_at, entity, account, amount, vendor, description, preparer, approver[, invoice_ref]
Outputs: flags.csv (one row per flagged journal, highest risk first), screening_summary.json
"""
import argparse, json, math, re, sys
from pathlib import Path
import numpy as np
import pandas as pd

RULES = {"weekend": 2, "after_hours": 1, "round_amount": 1, "below_threshold": 2, "new_vendor": 2,
         "duplicate": 3, "self_approved": 3, "sensitive_acct": 2, "period_end": 1}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journals", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--vendors"); ap.add_argument("--approval", type=float, default=50000)
    ap.add_argument("--hours", default="7-20"); ap.add_argument("--sensitive", default="1999")
    ap.add_argument("--period-end"); ap.add_argument("--min-score", type=int, default=3)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    j = pd.read_csv(a.journals); j.columns = [c.strip().lower() for c in j.columns]
    need = {"je_id", "posted_at", "account", "amount"}
    if not need <= set(j.columns):
        sys.exit(f"journals file is missing {sorted(need - set(j.columns))}")
    for c in ("vendor", "description", "preparer", "approver", "invoice_ref", "entity"):
        if c not in j.columns: j[c] = ""
        j[c] = j[c].fillna("").astype(str).str.strip()
    j["posted_at"] = pd.to_datetime(j["posted_at"], errors="coerce")
    j["amount"] = pd.to_numeric(j["amount"], errors="coerce")
    j["account"] = j["account"].astype(str)
    h0, h1 = [int(x) for x in a.hours.split("-")]
    sens = {s.strip() for s in a.sensitive.split(",") if s.strip()}

    known = set()
    if a.vendors:
        v = pd.read_csv(a.vendors); v.columns = [c.strip().lower() for c in v.columns]
        known = set(v[v.columns[0]].astype(str).str.strip().str.lower())

    flags = {i: [] for i in j.index}
    amt = j.amount.abs()
    for i, r in j.iterrows():
        t = r.posted_at
        if pd.notna(t):
            if t.weekday() >= 5: flags[i].append(("weekend", t.strftime("%a %H:%M")))
            if t.hour < h0 or t.hour >= h1: flags[i].append(("after_hours", t.strftime("%H:%M")))
        if amt[i] >= 1000 and amt[i] % 1000 == 0: flags[i].append(("round_amount", f"{amt[i]:,.0f}"))
        if a.approval * 0.95 <= amt[i] < a.approval: flags[i].append(("below_threshold", f"{amt[i]:,.0f} vs limit {a.approval:,.0f}"))
        if not r.approver or r.approver.lower() == r.preparer.lower():
            flags[i].append(("self_approved", f"preparer {r.preparer or '?'} / approver {r.approver or 'none'}"))
        if any(r.account.startswith(s) for s in sens): flags[i].append(("sensitive_acct", r.account))
        if a.period_end and pd.notna(t):
            pe = pd.Timestamp(a.period_end)
            if t.normalize() > pe: flags[i].append(("period_end", "posted after period end"))
            elif (pe - t.normalize()).days <= 1: flags[i].append(("period_end", "last 2 days of period"))

    # new vendors
    vend = j[j.vendor != ""]
    if known:
        for i, r in vend.iterrows():
            if r.vendor.lower() not in known: flags[i].append(("new_vendor", f"{r.vendor} not in vendor master"))
    else:
        first = vend.sort_values("posted_at").drop_duplicates("vendor")
        cnt = vend.vendor.value_counts()
        for i, r in first.iterrows():
            if cnt[r.vendor] == 1: flags[i].append(("new_vendor", f"{r.vendor} appears once"))

    # duplicates
    srt = vend.sort_values("posted_at")
    for (vname, am), g in srt.groupby(["vendor", srt.amount.round(2)]):
        if len(g) > 1:
            times = g.posted_at.tolist(); ids = g.index.tolist()
            for k in range(1, len(ids)):
                if pd.notna(times[k]) and pd.notna(times[k-1]) and (times[k] - times[k-1]).days <= 30:
                    flags[ids[k]].append(("duplicate", f"same vendor+amount as {j.at[ids[k-1], 'je_id']}"))
    refs = j[j.invoice_ref != ""]
    base = refs.invoice_ref.str.upper().str.replace(r"([-_ ]?(A|B|DUP|COPY)|[-_ ][0-9])$", "", regex=True)
    for b, g in refs.groupby(base):
        if len(g) > 1 and g.invoice_ref.nunique() > 1:
            for i in g.index[1:]:
                if not any(f[0] == "duplicate" for f in flags[i]):
                    flags[i].append(("duplicate", f"invoice ref {j.at[i,'invoice_ref']} resembles {g.invoice_ref.iloc[0]}"))

    rows = []
    for i, fl in flags.items():
        if not fl: continue
        score = sum(RULES[k] for k, _ in fl)
        r = j.loc[i]
        rows.append({"je_id": r.je_id, "posted_at": r.posted_at, "entity": r.entity, "account": r.account,
                     "amount": r.amount, "vendor": r.vendor, "description": r.description,
                     "preparer": r.preparer, "approver": r.approver, "score": score,
                     "rules": "; ".join(k for k, _ in fl), "evidence": " | ".join(f"{k}: {e}" for k, e in fl),
                     "severity": "high" if score >= 6 else ("medium" if score >= a.min_score else "low")})
    f = pd.DataFrame(rows)
    if len(f): f = f.sort_values(["score", "amount"], ascending=False)
    f.to_csv(out / "flags.csv", index=False)

    # Benford
    big = amt[amt >= 10]
    fd = big.apply(lambda x: int(str(f"{x:.2f}").lstrip("0.")[0]))
    obs = fd.value_counts(normalize=True).reindex(range(1, 10)).fillna(0)
    exp = pd.Series({d: math.log10(1 + 1 / d) for d in range(1, 10)})
    mad = float((obs - exp).abs().mean())
    conformity = ("close" if mad < 0.006 else "acceptable" if mad < 0.012 else "marginal" if mad < 0.015 else "nonconformity")

    sev = f.severity.value_counts().to_dict() if len(f) else {}
    summary = {"journals_screened": int(len(j)), "flagged": int(len(f)),
               "by_severity": {k: int(sev.get(k, 0)) for k in ("high", "medium", "low")},
               "by_rule": {k: int(f.rules.str.contains(k).sum()) if len(f) else 0 for k in RULES},
               "top": f.head(10)[["je_id", "amount", "vendor", "score", "rules", "evidence"]].to_dict(orient="records") if len(f) else [],
               "benford": {"n": int(len(big)), "mad": round(mad, 4), "conformity": conformity,
                           "note": "Benford is a population signal only; under ~300 amounts it is unreliable"},
               "settings": {"approval_threshold": a.approval, "hours": a.hours, "sensitive_accounts": sorted(sens)},
               "files": ["flags.csv"]}
    (out / "screening_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))

if __name__ == "__main__":
    main()
