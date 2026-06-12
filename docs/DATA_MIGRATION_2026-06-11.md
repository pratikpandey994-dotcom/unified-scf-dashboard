# Data Migration — Jun-11 Consolidated Extracts (2026-06-12)

The five Jun-5 extracts (View 1, View 2, Master Handover, Historic OB, Current OB) were removed from
Downloads and replaced by **two** consolidated extracts:

| File | Shape | Replaces |
|---|---|---|
| `us_scf___master_data___client_level_*.xlsx` | 647 × 37 | Master Handover + View 1 (merged) |
| `us_scf___invoice_level_data_*.xlsx` | 36,975 × 35 | View 2 (and partially the OB files, via reconstruction) |

Both have a single `Query result` sheet, headers on row 1. The loader now **auto-discovers the newest
file matching each pattern** in Downloads, so future timestamped re-extracts need no code change.

## Structural wins over the old extracts

1. **Clean ID join.** The invoice file carries `IMPORTER_USER_ID`; all 647 account IDs round-trip with
   zero orphans. The old View 2 only had buyer *names* (the JAYMIN duplicate-name hazard). The
   name-join is retired.
2. **One source per account fact.** AM, facility, OB, status all live in the master — the old
   V1-primary/master-fallback coalescing is gone.
3. **New analytics that neither original dashboard could show:** `BOOKED_REVENUE` per invoice
   (real revenue), exporter/supplier concentration, industry & state mix, per-account
   `MAX_OPEN_DPD`/`MAX_DPD`, ops flags (`PLAID_STATUS`, `PG_STATUS`), plan terms
   (tenor/margin/advance rates).

## What is LOST and how it is handled

The daily OB panel files (Historic OB 2023-01→2026-04, Current OB 2026-05+) no longer exist anywhere
on disk. Everything OB-history-driven (OB trend, peak analysis, OB 30/90d ago, OB dent, peak/avg OB
per account) is now computed from an **invoice-derived reconstruction**:

> An invoice contributes its `ORIGINATION` (amount actually advanced) from `FIRST_ADVANCE_DATE`
> until `SETTLEMENT_DATE` (open invoices: until today). Daily cumulative sum per account.

Validation on 2026-06-11 data: reconstruction "today" = **$94.1M** vs open-invoice outstanding
**$89.9M** (gap = $4.1M of partial repayments not yet settled — the method books partial paydowns
only at settlement) vs master OB **$81.1M** (master OB is a different, net measure). The live-window
mask agrees with open-stage membership on all but 2 of 36,975 rows. The reconstruction is therefore
faithful for **shape, peaks, and movement**, and overstates levels by ~5-15% vs master OB; every
OB-history chart is labeled "invoice-derived (advance basis)".

## Decision log

| Topic | Old rule | New rule | Why |
|---|---|---|---|
| Team Nikhil | AM ∈ 5-list, no partner filter → 250 | unchanged → **255** | same agreed rule, fresher book |
| Team Pankit | AM ∈ 4-list AND `Partner == 'Direct'` → 194 | AM ∈ 4-list AND `TYPE == 'DIRECT'` → **193** | `Partner` column gone; `TYPE ∈ {DIRECT, CP}` is the direct/CP split (uppercase!). One account genuinely left the book. |
| CP universe (View G) | `Team=='CP' & Partner!='Direct'` | `TYPE == 'CP'`, partner = `CP_COMPANY` → **313** accts / 43 partners | `Team` column gone; `CP_COMPANY` is the partner name |
| Account OB vs risk OB | account OB from V1, invoice risk from V2 outstanding | account OB from master `OB`, invoice risk from `OUTSTANDING_ADVANCE_BALANCE_USD` | preserves the originals' duality (master 81.1M ≠ invoice 89.9M on 60 accounts; both are correct measures) |
| DPD | V2 `dpd` negative = days-until-due | `DAYS_PAST_DUE` null when not past due, positive otherwise → `fillna(0)` | thresholds `>7 & ≤90` overdue, `>90` NPA unchanged |
| Invoice AM | invoice `name` column (broken) → company map | from the account join (master AM) | single source of truth; invoice `AM` column kept as `am_on_invoice` for audit |
| Stages | 15 stages incl. 7 EXCLUDED | only 8 appear (`closed, paid, advanced, npa, overdue, partial, received, partadvanced`) | stage sets unchanged; EXCLUDED now only ever matches `partadvanced` |

## Column coverage — master (37/37 mapped)

| New column | Canonical field | Used by |
|---|---|---|
| USER_ID | `id` | join key everywhere |
| IMPORTER_NAME | `company` | all tables |
| CP_ID / CP_COMPANY | `cp_id` / `partner` | CP Health partner rollup |
| TYPE | `type` (DIRECT/CP) | team + CP universe rules |
| AIRTABLE_INDUSTRY | `industry` | Insights: industry mix |
| AIRTABLE_GOODS_SHIPPED | `goods_shipped` | account detail table |
| USER_UTILIZATION_STATUS | `util_status` | level-2 classification |
| FIRST/LAST_DISBURSED_DATE | `first/last_disbursed` | dormancy, DSLD, reactivation |
| FACILITY_SIZE / OVERDRAFT_LIMIT / TOTAL_LIMIT | `facility` / `overdraft` / `total_facility` | utilization denominators (TOTAL_LIMIT verified == facility+overdraft) |
| OB | `ob` (clip ≥0; 18 nulls → 0) | headline OB |
| MAX_DPD / MAX_OPEN_DPD | `max_dpd` / `max_open_dpd` | Insights: account DPD aging; risk tables |
| SIGNED_UP_IRR | `irr` | WIRR everywhere |
| INTEREST_RATE / FLAT_DISCOUNTING_FEE | `interest_rate` / `flat_fee` | CP Health scorecard |
| PLANS_PAYMENT_TENOR / OVERDUE_RATE | `tenor` / `overdue_rate` | account detail |
| USER_ADDRESS/CITY/STATE/COUNTRY | `state`, `country` (addr/city in detail) | Insights: geography |
| AM / BDM / POD_MANAGER | `am` / `bdm` / `pod_manager` | team rules, Insights |
| ACCOUNT_STATUS / BROAD_ACCOUNT_STATUS | `raw_status` / `broad_status` | Pankit statuses / Nikhil level-2 |
| PLANS_MARGIN_RATE / PLANS_ADVANCE_RATE / PROCESSING_FEE / ANNUAL_MAINTENANCE_FEE | `margin_rate`/`advance_rate`/`processing_fee`/`amf` | CP scorecard, account detail |
| PG_STATUS / CG_STATUS / PLAID_STATUS | `pg_status`/`cg_status`/`plaid_status` | Insights: ops flags (CG_STATUS is constant 'No' — carried, not charted) |

## Column coverage — invoices (35/35 mapped)

| New column | Canonical field | Used by |
|---|---|---|
| INVOICE_ID | `Invoice ID` | risk/early-repayment tables |
| IMPORTER_USER_ID / IMPORTER_COMPANY | `account_id` / `Buyer` | join, groupings |
| BUYER_COUNTRY | `buyer_country` | detail |
| EXPORTER_USER_ID/COMPANY/COUNTRY | `exporter*` | Insights: supplier concentration |
| CP_COMPANY / TYPE | `cp_company` / `type` | CP risk charts |
| ACCOUNT_STATUS / USER_UTILIZATION_STATUS | snapshot copies — account-level canonical comes from master | audit only |
| AM | `am_on_invoice` (canonical `am` comes from account join) | audit |
| STAGE | `Stage` (lowercased) | stage sets unchanged |
| INVOICE_DATE / MARGIN_RECEIVED_DATE | `invoice_date` / `margin_received_date` | detail |
| FIRST_ADVANCE_DATE | `disbursed_date` | originations, windows, OB reconstruction |
| DUE_DATE | `due_date_of_invoice` | due windows, early repayment |
| SETTLEMENT_DATE | `settlement_date` | repayments, OB reconstruction |
| INVOICE_TERM / CURRENCY | `term` / `currency` | detail, Insights |
| INVOICE_VALUE_USD / TOTAL_ADVANCED | `invoice_value` / `total_advanced` | Insights |
| MARGIN_RECEIVED_USD | `margin_received` | detail |
| ORIGINATION | `Origination` | origination/repayment math, OB reconstruction |
| INTEREST_RATE / DISCOUNTING_RATE | `int_rate` / `disc_rate` | detail |
| BOOKED_REVENUE | `booked_revenue` | Insights: revenue trend/by-AM |
| EXPECTED_REGULAR_INTEREST_USD / EXPECTED_FACTORING_FEES_USD | `expected_interest` / `expected_fees` | Insights: expected vs booked |
| REGULAR_INTEREST_NATIVE / FACTORING_FEES_NATIVE / OVERDUE_INTEREST_NATIVE | `interest_native`/`fees_native`/`overdue_interest` | revenue split detail |
| TOTAL_LIMIT | dropped at invoice level (duplicate of master) | — |
| OUTSTANDING_ADVANCE_BALANCE_USD | `Outstanding` | risk OB, collections |
| DAYS_PAST_DUE | `dpd` (fillna 0) | overdue/NPA thresholds |

## Knock-on effects in the app

- `CURRENT_OB_CUTOFF` (the old hist/current file seam) is obsolete; "OB Movement" windows are now
  date-relative (last 30 days of the reconstruction).
- Demo mode generates the new canonical schema directly.
- `_verify_metrics.py` expectations: Nikhil 255, Pankit 193, CP 313.
- A shared **Insights** tab (both teams) charts the newly available columns: booked revenue trend &
  by-AM, industry/state mix, exporter concentration, account DPD aging, Plaid/PG ops flags.
