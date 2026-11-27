#!/usr/bin/env python3
"""Orrery Reconciler engine: match bank statement lines to GL cash lines.

Matching passes (each one-to-one, earlier passes win):
  1. Reference + amount + entity (exact)
  2. Amount + entity, date within --date-window days (closest date wins)
  3. Amount within --amount-tol, description similarity >= --min-sim, date within 2x window

Bank-only breaks are classified (bank fee, interest, FX, unknown) and get a
proposed journal. Nothing is posted: proposals go to a review queue.

Usage:
  python3 reconcile.py --bank bank.csv --gl gl_cash.csv --out ./out [--date-window 3]

Required columns
  bank: date, amount, description[, reference][, entity]
  gl:   date, amount, description[, reference][, entity][, je_id][, account]
Amounts are signed: money in is positive.
"""
import argparse, json, re, sys
from difflib import SequenceMatcher
from pathlib import Path
import pandas as pd

CLASSIFY = [
    ("bank_fee", r"\b(fee|charge|commission|kosten|gebuehr|gebühr)\b", "6810 Bank charges"),
    ("interest", r"\b(interest|rente|zins)\b", "7900 Interest income/expense"),
    ("fx", r"\b(fx|revaluation|exchange|koers|kurs)\b", "7950 FX gains/losses"),
    ("card", r"\b(card|visa|mastercard|amex)\b", "2150 Card clearing"),
]

def norm_text(s):
    return re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).split()

def sim(a, b):
    return SequenceMatcher(None, " ".join(norm_text(a)), " ".join(norm_text(b))).ratio()

def load(path, kind):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in ("date", "amount", "description"):
        if c not in df.columns:
            sys.exit(f"{kind} file is missing required column '{c}'. Found: {list(df.columns)}")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        bad = df[df["date"].isna()].index.tolist()[:5]
        sys.exit(f"{kind} file has unreadable dates in rows {bad}")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").round(2)
    for c in ("reference", "entity"):
        if c not in df.columns:
            df[c] = ""
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["rowid"] = range(len(df))
    return df

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", required=True)
    ap.add_argument("--gl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--date-window", type=int, default=3)
    ap.add_argument("--amount-tol", type=float, default=0.01)
    ap.add_argument("--min-sim", type=float, default=0.55)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    bank, gl = load(a.bank, "bank"), load(a.gl, "GL")
    used_b, used_g, matches = set(), set(), []

    def take(bi, gi, rule):
        used_b.add(bi); used_g.add(gi)
        matches.append({"bank_row": bi, "gl_row": gi, "rule": rule})

    # pass 1
    gl_idx = {}
    for g in gl.itertuples():
        if g.reference:
            gl_idx.setdefault((g.reference.lower(), g.amount, g.entity), []).append(g.rowid)
    for b in bank.itertuples():
        if not b.reference:
            continue
        for gi in gl_idx.get((b.reference.lower(), b.amount, b.entity), []):
            if gi not in used_g:
                take(b.rowid, gi, "reference+amount"); break

    # pass 2
    by_amt = {}
    for g in gl.itertuples():
        by_amt.setdefault((g.amount, g.entity), []).append(g)
    for b in bank.itertuples():
        if b.rowid in used_b:
            continue
        cands = [g for g in by_amt.get((b.amount, b.entity), []) if g.rowid not in used_g
                 and abs((g.date - b.date).days) <= a.date_window]
        if cands:
            g = min(cands, key=lambda g: (abs((g.date - b.date).days), -sim(b.description, g.description)))
            take(b.rowid, g.rowid, f"amount+date±{a.date_window}d")

    # pass 3
    for b in bank.itertuples():
        if b.rowid in used_b:
            continue
        best, best_s = None, 0
        for g in gl.itertuples():
            if g.rowid in used_g or g.entity != b.entity:
                continue
            if abs(g.amount - b.amount) > a.amount_tol:
                continue
            if abs((g.date - b.date).days) > 2 * a.date_window:
                continue
            s = sim(b.description, g.description)
            if s > best_s:
                best, best_s = g, s
        if best is not None and best_s >= a.min_sim:
            take(b.rowid, best.rowid, f"fuzzy(sim={best_s:.2f})")

    m = pd.DataFrame(matches)
    if len(m):
        mb = bank.add_prefix("bank_").rename(columns={"bank_rowid": "bank_row"})
        mg = gl.add_prefix("gl_").rename(columns={"gl_rowid": "gl_row"})
        m = m.merge(mb, on="bank_row").merge(mg, on="gl_row")
        m["date_diff_days"] = (m["gl_date"] - m["bank_date"]).dt.days
    m.to_csv(out / "matched.csv", index=False)

    bank_breaks = bank[~bank["rowid"].isin(used_b)].copy()
    gl_breaks = gl[~gl["rowid"].isin(used_g)].copy()

    def classify(desc):
        t = str(desc).lower()
        for k, pat, acct in CLASSIFY:
            if re.search(pat, t):
                return k, acct
        return "unknown", "1999 Suspense (investigate)"

    bank_breaks[["break_type", "proposed_account"]] = bank_breaks["description"].apply(lambda d: pd.Series(classify(d)))
    bank_breaks["age_days"] = (bank["date"].max() - bank_breaks["date"]).dt.days
    gl_breaks["break_type"] = gl_breaks.apply(
        lambda r: "outstanding_payment" if r.amount < 0 else "deposit_in_transit", axis=1)
    gl_breaks["age_days"] = (gl["date"].max() - gl_breaks["date"]).dt.days

    # proposed journals for bank-only items
    props = []
    for i, r in enumerate(bank_breaks.itertuples(), 1):
        props.append({
            "proposal_id": f"PJ-{i:04d}", "entity": r.entity, "date": r.date.date(),
            "debit_account": r.proposed_account if r.amount < 0 else "1010 Bank",
            "credit_account": "1010 Bank" if r.amount < 0 else r.proposed_account,
            "amount": abs(r.amount), "evidence": f"bank row {r.rowid}: {r.description}",
            "confidence": "high" if r.break_type != "unknown" else "low",
            "status": "proposed (needs reviewer)",
        })
    pd.DataFrame(props).to_csv(out / "proposed_journals.csv", index=False)
    bank_breaks.drop(columns="rowid").assign(bank_row=bank_breaks["rowid"]).to_csv(out / "bank_breaks.csv", index=False)
    gl_breaks.drop(columns="rowid").assign(gl_row=gl_breaks["rowid"]).to_csv(out / "gl_breaks.csv", index=False)

    rules = m["rule"].str.replace(r"\(.*\)", "", regex=True).value_counts().to_dict() if len(m) else {}
    by_entity = {}
    for ent in sorted(set(bank["entity"]) | set(gl["entity"])):
        bb = bank[bank.entity == ent]; gg = gl[gl.entity == ent]
        by_entity[ent or "(none)"] = {
            "bank_lines": int(len(bb)), "gl_lines": int(len(gg)),
            "bank_total": round(float(bb.amount.sum()), 2), "gl_total": round(float(gg.amount.sum()), 2),
            "difference": round(float(bb.amount.sum() - gg.amount.sum()), 2),
            "unmatched_bank": int((~bb["rowid"].isin(used_b)).sum()),
            "unmatched_gl": int((~gg["rowid"].isin(used_g)).sum()),
            "explained_by_breaks": round(float(bb[~bb["rowid"].isin(used_b)].amount.sum() - gg[~gg["rowid"].isin(used_g)].amount.sum()), 2),
        }
        e = by_entity[ent or "(none)"]
        e["unexplained"] = round(e["difference"] - e["explained_by_breaks"], 2)
    summary = {
        "bank_lines": int(len(bank)), "gl_lines": int(len(gl)), "matched_pairs": int(len(m)),
        "auto_match_rate_bank": round(len(used_b) / max(1, len(bank)) * 100, 2),
        "match_rules": rules,
        "bank_breaks": int(len(bank_breaks)), "bank_breaks_total": round(float(bank_breaks.amount.sum()), 2),
        "gl_breaks": int(len(gl_breaks)), "gl_breaks_total": round(float(gl_breaks.amount.sum()), 2),
        "breaks_older_than_30d": int((bank_breaks.age_days > 30).sum() + (gl_breaks.age_days > 30).sum()),
        "proposed_journals": len(props),
        "by_entity": by_entity,
        "files": ["matched.csv", "bank_breaks.csv", "gl_breaks.csv", "proposed_journals.csv"],
    }
    (out / "recon_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str))

if __name__ == "__main__":
    main()
