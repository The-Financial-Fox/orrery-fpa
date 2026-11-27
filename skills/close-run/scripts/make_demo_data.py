#!/usr/bin/env python3
"""Generate a realistic demo close dataset for a three-entity group (NL-BV, DE-GmbH, UK-Ltd),
October 2026, EUR. Planted issues let every agent find something real:
  * bank fees, interest and an unknown receipt with no GL entry; outstanding payments and deposits in transit
  * JE-20931: EUR 48,200.00 to a new vendor, posted Sunday 25 Oct 23:41 (just under the 50k approval limit)
  * INV-7781 / INV-7781A: possible duplicate invoice from Hamburg Logistik AG
  * a self-approved journal and a suspense posting
  * DACH volume up, price concessions, FX hit on purchases, salary underspend, one-off restructuring

Usage: python3 make_demo_data.py --out ./orrery-demo
"""
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    ents = ["NL-BV", "DE-GmbH", "UK-Ltd"]
    days = pd.date_range("2026-10-01", "2026-10-31")

    # ---------- bank vs GL ----------
    bank, gl = [], []
    customers = ["Rabo Agri BV", "Siemens Mobility", "Tesco Stores", "Bosch Rexroth", "Philips Lighting", "Zalando SE",
                 "Ahold Delhaize", "Vodafone UK", "Lufthansa Technik", "ASML Holding", "BMW Group", "Ocado Retail"]
    suppliers = ["Hamburg Logistik AG", "DHL Freight", "Randstad", "Microsoft Ireland", "AWS EMEA", "KPMG Accountants",
                 "Eneco", "WeWork NL", "Iberdrola", "Sage UK", "Atlassian", "Booking.com Travel"]
    je = 30000
    for ent in ents:
        n = {"NL-BV": 260, "DE-GmbH": 310, "UK-Ltd": 180}[ent]
        for k in range(n):
            d = days[rng.integers(0, 28)]
            receipt = rng.random() < 0.45
            cp = rng.choice(customers if receipt else suppliers)
            amt = round(float(np.exp(rng.normal(8.6, 1.3))), 2) * (1 if receipt else -1)
            ref = f"{'RC' if receipt else 'PY'}{ent[:2]}{k:05d}"
            has_ref = rng.random() > 0.18
            lag = int(rng.integers(0, 4))
            je += 1
            gl.append({"date": d.date(), "amount": amt, "description": f"{'Receipt' if receipt else 'Payment'} {cp}",
                       "reference": ref, "entity": ent, "account": "1010", "je_id": f"JE-{je}"})
            bank.append({"date": (d + pd.Timedelta(days=lag)).date(), "amount": amt,
                         "description": f"{cp.upper()} {ref if has_ref else ''}".strip(),
                         "reference": ref if has_ref else "", "entity": ent})
    # planted bank-only items
    for ent, desc, amt in [("NL-BV", "BANK FEE OCT PACKAGE", -184.50), ("NL-BV", "INTEREST CREDIT Q3", 1243.18),
                           ("DE-GmbH", "KONTOFUEHRUNG GEBUEHR", -96.00), ("DE-GmbH", "FX REVALUATION USD ACCOUNT", -3118.40),
                           ("UK-Ltd", "CARD MERCHANT FEE VISA", -412.77), ("UK-Ltd", "UNKNOWN CREDIT REF 88231", 7750.00),
                           ("DE-GmbH", "ZINS GUTSCHRIFT", 512.40), ("NL-BV", "TRANSFER 4471-XX", -2200.00)]:
        bank.append({"date": "2026-10-30", "amount": amt, "description": desc, "reference": "", "entity": ent})
    # planted GL-only items (outstanding payments / deposits in transit)
    for ent, desc, amt, d in [("NL-BV", "Payment Eneco Q4 advance", -18400.00, "2026-10-30"),
                              ("DE-GmbH", "Payment Randstad wk44", -26150.00, "2026-10-31"),
                              ("UK-Ltd", "Receipt Tesco Stores", 41820.55, "2026-10-31"),
                              ("DE-GmbH", "Receipt BMW Group", 63210.00, "2026-10-31"),
                              ("NL-BV", "Payment KPMG interim audit", -12500.00, "2026-09-18")]:
        je += 1
        gl.append({"date": d, "amount": amt, "description": desc, "reference": "", "entity": ent, "account": "1010", "je_id": f"JE-{je}"})
    pd.DataFrame(bank).to_csv(out / "bank.csv", index=False)
    pd.DataFrame(gl).to_csv(out / "gl_cash.csv", index=False)

    # ---------- journals ----------
    preparers = ["a.jansen", "m.devries", "k.schulz", "j.smith", "l.bakker", "t.meyer"]
    approvers = ["m.devries", "c.fischer", "r.patel"]
    accts = ["5100", "5200", "6100", "6200", "6300", "6400", "6500", "2100", "2400"]
    J = []
    vendors_master = suppliers + ["Ricoh", "Coolblue Zakelijk", "Deutsche Bahn", "Thames Water"]
    for k in range(1400):
        t = days[rng.integers(0, 31)] + pd.Timedelta(hours=int(rng.integers(8, 19)), minutes=int(rng.integers(0, 60)))
        if t.weekday() >= 5: t = t - pd.Timedelta(days=2)
        p = rng.choice(preparers); ap_ = rng.choice([x for x in approvers if x != p])
        J.append({"je_id": f"JE-{20000+k}", "posted_at": t, "entity": rng.choice(ents), "account": rng.choice(accts),
                  "amount": round(float(np.exp(rng.normal(7.4, 1.6))), 2), "vendor": rng.choice(vendors_master),
                  "description": "Accrual / invoice posting", "preparer": p, "approver": ap_, "invoice_ref": f"INV-{5000+k}"})
    J[931] = {"je_id": "JE-20931", "posted_at": pd.Timestamp("2026-10-25 23:41"), "entity": "DE-GmbH", "account": "6400",
              "amount": 48200.00, "vendor": "Nordlicht Beratung GmbH", "description": "Consulting services Oct",
              "preparer": "k.schulz", "approver": "c.fischer", "invoice_ref": "NB-2026-001"}
    J[512] = {"je_id": "JE-20512", "posted_at": pd.Timestamp("2026-10-14 10:12"), "entity": "DE-GmbH", "account": "5200",
              "amount": 12640.00, "vendor": "Hamburg Logistik AG", "description": "Freight Sep", "preparer": "t.meyer",
              "approver": "c.fischer", "invoice_ref": "INV-7781"}
    J[1288] = {"je_id": "JE-21288", "posted_at": pd.Timestamp("2026-10-29 16:40"), "entity": "DE-GmbH", "account": "5200",
               "amount": 12640.00, "vendor": "Hamburg Logistik AG", "description": "Freight Sep", "preparer": "t.meyer",
               "approver": "c.fischer", "invoice_ref": "INV-7781A"}
    J[777] = {"je_id": "JE-20777", "posted_at": pd.Timestamp("2026-10-30 18:55"), "entity": "UK-Ltd", "account": "4100",
              "amount": 75000.00, "vendor": "", "description": "Manual revenue adjustment", "preparer": "j.smith",
              "approver": "j.smith", "invoice_ref": ""}
    J[640] = {"je_id": "JE-20640", "posted_at": pd.Timestamp("2026-10-31 21:05"), "entity": "NL-BV", "account": "1999",
              "amount": 9150.00, "vendor": "", "description": "Clearing to suspense", "preparer": "a.jansen",
              "approver": "m.devries", "invoice_ref": ""}
    pd.DataFrame(J).to_csv(out / "journals.csv", index=False)
    pd.DataFrame({"vendor": vendors_master}).to_csv(out / "vendors.csv", index=False)

    # ---------- sales (price / volume / mix) ----------
    prods = {"NL-BV": [("Edge Sensor S2", 640, 410.0), ("Gateway G5", 210, 1850.0)],
             "DE-GmbH": [("Edge Sensor S2", 1900, 405.0), ("Gateway G5", 520, 1820.0), ("Fleet Suite", 300, 2400.0)],
             "UK-Ltd": [("Edge Sensor S2", 380, 395.0), ("Fleet Suite", 140, 2350.0)]}
    S = []
    for ent, ps in prods.items():
        for name, u, pr in ps:
            S.append({"period": "2026-10", "entity": ent, "product": name, "scenario": "budget", "units": u, "revenue": round(u * pr, 2)})
            uf = {"DE-GmbH": 1.22, "NL-BV": 1.04, "UK-Ltd": 0.97}[ent] * (1.08 if name == "Fleet Suite" else 1)
            pf = 0.955 if (ent == "DE-GmbH" and name in ("Gateway G5", "Fleet Suite")) else 0.99
            ua = int(round(u * uf)); S.append({"period": "2026-10", "entity": ent, "product": name, "scenario": "actual",
                                                "units": ua, "revenue": round(ua * pr * pf, 2)})
    sales = pd.DataFrame(S); sales.to_csv(out / "sales.csv", index=False)

    # ---------- P&L ----------
    def pl(scn, period, scale=1.0):
        rows = []
        for ent in ents:
            sr = sales[(sales.entity == ent) & (sales.scenario == scn)].revenue.sum() * scale
            svc = {"NL-BV": 420000, "DE-GmbH": 610000, "UK-Ltd": 380000}[ent] * scale
            sub = {"NL-BV": 900000, "DE-GmbH": 1450000, "UK-Ltd": 760000}[ent] * scale
            act = scn == "actual"
            rows += [(ent, "4100", "Product sales", "revenue", sr),
                     (ent, "4200", "Services", "revenue", svc * (1.03 if act else 1)),
                     (ent, "4300", "Subscriptions", "revenue", sub * (1.01 if act else 1)),
                     (ent, "5100", "Materials", "cogs", sr * 0.36),
                     (ent, "5200", "Freight", "cogs", sr * 0.05 * (1.06 if act else 1)),
                     (ent, "5300", "FX on purchases", "cogs", (210000 if ent == "DE-GmbH" else 95000) * (1 if not act else 2.9) * scale),
                     (ent, "6100", "Salaries and wages", "opex", {"NL-BV": 610000, "DE-GmbH": 880000, "UK-Ltd": 520000}[ent] * (0.88 if act else 1) * scale),
                     (ent, "6200", "Marketing", "opex", {"NL-BV": 140000, "DE-GmbH": 160000, "UK-Ltd": 120000}[ent] * (1.4 if act and ent == "UK-Ltd" else 1) * scale),
                     (ent, "6300", "Rent and facilities", "opex", {"NL-BV": 90000, "DE-GmbH": 110000, "UK-Ltd": 85000}[ent] * scale),
                     (ent, "6400", "Professional fees", "opex", {"NL-BV": 60000, "DE-GmbH": 70000, "UK-Ltd": 45000}[ent] * (1.25 if act and ent == "DE-GmbH" else 1) * scale),
                     (ent, "6500", "IT and software", "opex", {"NL-BV": 75000, "DE-GmbH": 95000, "UK-Ltd": 60000}[ent] * scale),
                     (ent, "8100", "Depreciation", "other", {"NL-BV": 120000, "DE-GmbH": 150000, "UK-Ltd": 90000}[ent] * scale)]
            if act and ent == "NL-BV" and period == "2026-10":
                rows.append((ent, "6900", "Restructuring (one-off)", "opex", 300000))
        return pd.DataFrame([{"period": period, "entity": e, "account": ac, "line": l, "type": t, "amount": round(v, 2)}
                             for e, ac, l, t, v in rows])
    pl("actual", "2026-10").to_csv(out / "actuals.csv", index=False)
    pl("budget", "2026-10").to_csv(out / "budget.csv", index=False)
    pl("actual", "2026-09", 0.95).to_csv(out / "prior.csv", index=False)

    # ---------- history for forecast ----------
    act_oct = pl("actual", "2026-10")
    tot = act_oct.groupby("type").amount.sum()
    H = []
    periods = pd.period_range("2024-01", "2026-10", freq="M")
    season = {1: .90, 2: .92, 3: 1.02, 4: .98, 5: 1.0, 6: 1.04, 7: .93, 8: .88, 9: 1.03, 10: 1.07, 11: 1.08, 12: 1.15}
    n = len(periods)
    for i, p in enumerate(periods):
        g = 0.72 + 0.28 * i / (n - 1)
        for met, base, noise in [("revenue", tot["revenue"] / season[10], .035), ("cogs", tot["cogs"] / season[10], .04),
                                 ("opex", tot["opex"] / 1.0, .025)]:
            s = season[p.month] if met != "opex" else 1 + (season[p.month] - 1) * .2
            v = base * g * s * (1 + rng.normal(0, noise))
            if p == periods[-1]: v = tot[met]
            H.append({"period": str(p), "metric": met, "value": round(float(v), 2)})
    pd.DataFrame(H).to_csv(out / "history.csv", index=False)

    (out / "README.txt").write_text(
        "Orrery demo close: October 2026, three entities (NL-BV, DE-GmbH, UK-Ltd), EUR.\n"
        "Files: bank.csv, gl_cash.csv, journals.csv, vendors.csv, actuals.csv, budget.csv, prior.csv, sales.csv, history.csv\n"
        "All companies, people and figures are fictional.\n")
    print(json.dumps({"out": str(out), "files": sorted(p.name for p in out.iterdir())}, indent=2))

if __name__ == "__main__":
    main()
