# Demo close dataset

A fictional three-entity group (NL-BV, DE-GmbH, UK-Ltd), October 2026, EUR. Generate it with a short numpy and pandas script written to `./orrery-demo/make_demo.py`, using random seed 42 for everything, and write the CSVs to `./orrery-demo/`. Planted issues give every agent something real to find. All companies, people and figures are fictional; say so when presenting.

## bank.csv and gl_cash.csv

Columns: bank `date, amount, description, reference, entity`; GL `date, amount, description, reference, entity, account, je_id`.

- Lines per entity: NL-BV 260, DE-GmbH 310, UK-Ltd 180. For each line: GL date = a random day from 1 to 28 October; 45% receipts (positive) from a customer list, otherwise payments (negative) to a supplier list.
- Amount = e^N(8.6, 1.3), rounded to 2 dp.
- Reference `RC` or `PY` + first two letters of the entity + a 5-digit counter. GL `je_id` numbered from JE-30001, account 1010.
- Bank line: same amount; date = GL date + 0 to 3 days; description = counterparty in capitals + reference. 18% of bank lines have the reference left empty, so passes 2 and 3 have work to do.
- Customers: Rabo Agri BV, Siemens Mobility, Tesco Stores, Bosch Rexroth, Philips Lighting, Zalando SE, Ahold Delhaize, Vodafone UK, Lufthansa Technik, ASML Holding, BMW Group, Ocado Retail.
- Suppliers: Hamburg Logistik AG, DHL Freight, Randstad, Microsoft Ireland, AWS EMEA, KPMG Accountants, Eneco, WeWork NL, Iberdrola, Sage UK, Atlassian, Booking.com Travel.

Bank-only items, all dated 2026-10-30 with no reference:

| entity | description | amount |
|---|---|---|
| NL-BV | BANK FEE OCT PACKAGE | -184.50 |
| NL-BV | INTEREST CREDIT Q3 | 1,243.18 |
| DE-GmbH | KONTOFUEHRUNG GEBUEHR | -96.00 |
| DE-GmbH | FX REVALUATION USD ACCOUNT | -3,118.40 |
| UK-Ltd | CARD MERCHANT FEE VISA | -412.77 |
| UK-Ltd | UNKNOWN CREDIT REF 88231 | 7,750.00 |
| DE-GmbH | ZINS GUTSCHRIFT | 512.40 |
| NL-BV | TRANSFER 4471-XX | -2,200.00 |

GL-only items (account 1010, no reference):

| entity | description | amount | date |
|---|---|---|---|
| NL-BV | Payment Eneco Q4 advance | -18,400.00 | 2026-10-30 |
| DE-GmbH | Payment Randstad wk44 | -26,150.00 | 2026-10-31 |
| UK-Ltd | Receipt Tesco Stores | 41,820.55 | 2026-10-31 |
| DE-GmbH | Receipt BMW Group | 63,210.00 | 2026-10-31 |
| NL-BV | Payment KPMG interim audit | -12,500.00 | 2026-09-18 (stale) |

## journals.csv and vendors.csv

Columns: `je_id, posted_at, entity, account, amount, vendor, description, preparer, approver, invoice_ref`.

- 1,400 journals `JE-20000` to `JE-21399`, posted on random October days between 08:00 and 18:59. Move any weekend posting back 2 days. Random entity; account from 5100, 5200, 6100, 6200, 6300, 6400, 6500, 2100, 2400; amount = e^N(7.4, 1.6) to 2 dp; vendor from the supplier list plus Ricoh, Coolblue Zakelijk, Deutsche Bahn and Thames Water; description "Accrual / invoice posting"; preparer from a.jansen, m.devries, k.schulz, j.smith, l.bakker, t.meyer; approver from m.devries, c.fischer, r.patel but never the preparer; invoice_ref `INV-{5000+k}`.
- `vendors.csv` (column `vendor`) holds that vendor list.

Overwrite these positions with planted entries:

| je_id | posted_at | entity | account | amount | vendor | description | preparer | approver | invoice_ref |
|---|---|---|---|---|---|---|---|---|---|
| JE-20931 | 2026-10-25 23:41 (Sunday) | DE-GmbH | 6400 | 48,200.00 | Nordlicht Beratung GmbH (not in master) | Consulting services Oct | k.schulz | c.fischer | NB-2026-001 |
| JE-20512 | 2026-10-14 10:12 | DE-GmbH | 5200 | 12,640.00 | Hamburg Logistik AG | Freight Sep | t.meyer | c.fischer | INV-7781 |
| JE-21288 | 2026-10-29 16:40 | DE-GmbH | 5200 | 12,640.00 | Hamburg Logistik AG | Freight Sep | t.meyer | c.fischer | INV-7781A |
| JE-20777 | 2026-10-30 18:55 | UK-Ltd | 4100 | 75,000.00 | (none) | Manual revenue adjustment | j.smith | j.smith | (none) |
| JE-20640 | 2026-10-31 21:05 | NL-BV | 1999 | 9,150.00 | (none) | Clearing to suspense | a.jansen | m.devries | (none) |

## sales.csv

Columns `period, entity, product, scenario, units, revenue`, period 2026-10. Budget rows: units × budget price.

| entity | product | budget units | budget price |
|---|---|---|---|
| NL-BV | Edge Sensor S2 | 640 | 410 |
| NL-BV | Gateway G5 | 210 | 1,850 |
| DE-GmbH | Edge Sensor S2 | 1,900 | 405 |
| DE-GmbH | Gateway G5 | 520 | 1,820 |
| DE-GmbH | Fleet Suite | 300 | 2,400 |
| UK-Ltd | Edge Sensor S2 | 380 | 395 |
| UK-Ltd | Fleet Suite | 140 | 2,350 |

Actual units = round(budget units × entity factor × product factor), with entity factors DE-GmbH 1.22, NL-BV 1.04, UK-Ltd 0.97, and product factor 1.08 for Fleet Suite, otherwise 1. Actual revenue = actual units × budget price × price factor, where the price factor is 0.955 for DE-GmbH Gateway G5 and Fleet Suite (price concessions), otherwise 0.99.

## actuals.csv, budget.csv and prior.csv

Columns `period, entity, account, line, type, amount`. Per entity, with s = 1 for October and s = 0.95 for the prior file (period 2026-09, built like actuals):

| account | line | type | budget | actual |
|---|---|---|---|---|
| 4100 | Product sales | revenue | sales.csv budget revenue | sales.csv actual revenue |
| 4200 | Services | revenue | NL 420k, DE 610k, UK 380k | budget × 1.03 |
| 4300 | Subscriptions | revenue | NL 900k, DE 1,450k, UK 760k | budget × 1.01 |
| 5100 | Materials | cogs | 36% of product sales | 36% of product sales |
| 5200 | Freight | cogs | 5% of product sales | 5% × 1.06 |
| 5300 | FX on purchases | cogs | DE 210k, others 95k | budget × 2.9 |
| 6100 | Salaries and wages | opex | NL 610k, DE 880k, UK 520k | budget × 0.88 |
| 6200 | Marketing | opex | NL 140k, DE 160k, UK 120k | UK × 1.4, others as budget |
| 6300 | Rent and facilities | opex | NL 90k, DE 110k, UK 85k | as budget |
| 6400 | Professional fees | opex | NL 60k, DE 70k, UK 45k | DE × 1.25, others as budget |
| 6500 | IT and software | opex | NL 75k, DE 95k, UK 60k | as budget |
| 8100 | Depreciation | other | NL 120k, DE 150k, UK 90k | as budget |

Fixed amounts are multiplied by s. Actuals for NL-BV in 2026-10 also get account 6900 "Restructuring (one-off)", opex, 300,000. Round amounts to 2 dp.

## history.csv

Columns `period, metric, value`, metrics revenue, cogs and opex, January 2024 to October 2026 (34 months). Seasonal factors by month: Jan 0.90, Feb 0.92, Mar 1.02, Apr 0.98, May 1.00, Jun 1.04, Jul 0.93, Aug 0.88, Sep 1.03, Oct 1.07, Nov 1.08, Dec 1.15. Growth g runs linearly from 0.72 in the first month to 1.00 in the last. Base = October 2026 actual total for the metric ÷ 1.07 for revenue and cogs, and the October total itself for opex. Value = base × g × seasonal × (1 + noise), with seasonality damped to 1 + (factor − 1) × 0.2 for opex, and noise N(0, 0.035) for revenue, 0.04 for cogs and 0.025 for opex. October 2026 equals the actual total exactly.

## Checks after generating

Bank has 758 lines and GL 755. Journals has 1,400 rows including the 5 planted ones. The planted rows are present exactly as listed. History has 102 rows. Then report the files written.
