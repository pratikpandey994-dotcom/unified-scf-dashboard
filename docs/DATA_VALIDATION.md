# Phase 3 — Data Validation Report (2026-06-10)

All five Excel files in `C:\Users\PratikPandey\Downloads` inspected. Every file has exactly one sheet named `Query result`, headers on row 1, no fully-duplicated rows, no mixed-type columns.

## File schemas (key facts)

### 1. View 1 (`scf_am_team___view_1_with_suspension_reasons_...xlsx`) — 645 rows × 22 cols
- Key: `importer_user_id` (unique). Columns include `company`, `utilization_status` (active 231 / suspended 414), `Facility_Size` (int64), `Outstanding_Balance` (int64 — whole dollars), `max_balance`, `Signed-up IRR`, `interest_rate`, `flat_discounting_fee`, `overdue_rate`, `Realised Revenue` (16 nulls), `Total Orginations` (sic — typo in source), `First/Last_Disbursed_Date` (datetime), `overdraft_limit`, `AM_ID/AM_Name/AM_Email` (45 nulls), `user_id`, `latest_suspension_Date` (85 nulls), `suspension_reason` (84 nulls), `manual_suspension_reason` (627 nulls).
- AM counts: Nikhil Shetty 88, Pejush Hal 71, Kaustav Das 67, Ashitha Nair 54, Sonal Mishra 48, Deepsayan Dam 46, Darshan Hublikar 38, Pankit Shah 29, Asif Ali 25, … (21 AMs total + 45 unassigned).
- `suspension_reason` fragmented: `DPD` 228 / `dpd` 63, `dormat account` 30 (sic) / `Dormancy` 3, `manual_monitoring` 222, `grade_drop` 13, etc. Needs normalization before grouping.
- Dup company name: `JAYMIN ENTERPRISES CORP` under IDs 347583 and 170974 → join on ID, never name.

### 2. View 2 (`view_2_...xlsx`) — 36,800 rows × 25 cols (invoice level)
- Key: `Invoice ID` (unique). **No account ID — only `Buyer` name** (645 uniques, matches View 1). Name-join will mis-attribute the JAYMIN dup.
- `Stage` (15): closed 28532, paid 4646, advanced 3024, npa 263, overdue 179, partial 72, deposit_pending 37, processing 23, received 5, data_entry 5, uploaded 4, pending_advance 4, verify_bank_details 3, partadvanced 2, hold 1.
- ⚠ Columns the Nikhil HTML references that DON'T exist: `invoice_id` (file has `Invoice ID`), `name` (file has `AM_Email`). The HTML silently fell back to its company→AM map; the port must map AM from the account join.
- Data hazards: `irr` max **39,810,000** (outliers — never average raw); 18 negative `Origination` (min −19,230); `dpd` negative for 18,094 rows (days until due — filter `dpd > 7` handles it); nulls in settlement/fee columns correspond to non-settled invoices (expected); 449 invoices lack AM_Email; `Invoice Date` min 2013-03-28 (entry error).

### 3. Master (`us_scf___master_data___handover_date_...xlsx`) — 643 rows × 32 cols
- Key: `Buyer_ID` (unique). Includes `Partner` (46 values; `Direct` 330), `Type` (Direct 330/CP 313), `Team` (Direct 362/CP 281 — **Team ≠ Type for ~32 accounts**), `Account_Status` (Workable - Active 232, Non-Workable 215, Workable - Inactive (BDM) 127, Workable - Temporarily suspended 41, Workable - Inactive (AM) 28), `Broad_Account_Status` (Workable 428 / Non-Workable 215), `Pod_Manager` (Shreyanshu_D 236, Nikhil_Shetty 212, Others 195), `Facility_Size`, `Overdraft_Limit`, `OB` (float; 4 tiny negative residues — clamp), `Signed_up_IRR`, `AM` (44 nulls), `BDM`, `Annual_Maintenance_Fee` (248 nulls), `PG_Status`.
- ⚠ `First_Disbursed_Date` and `Handover_Date` are **strings** (parse cleanly; must cast). `Handover_Date` max is 2026-08-15 (future).
- `state` badly fragmented (NY/New York/"New York ", typos) — normalize before any geo grouping.

### 4. Historic OB (`Historic OB.xlsx`) — 779,456 rows × 3 cols
- `importer_user_id`, `ob_date`, `ob`. Dense daily panel: 641 accounts × 1,216 days, **2023-01-01 → 2026-04-30**, zero gaps, zero dup (id,date) pairs. 9,788 tiny negative `ob` values (min −1.74, float residue — clamp to 0).
- Note: Nikhil's HTML says "Jun 2020" but this file starts 2023-01-01.

### 5. Current OB (`us_scf___daily_ob_by_accounts_...xlsx`) — 21,252 rows × 3 cols
- Same schema. 644 accounts × 33 days, **2026-05-01 → 2026-06-02**, no gaps. 238 negative values ~−5.8e-11 (clamp).
- **Seam with Historic OB is clean** (ends 04-30 / starts 05-01, no overlap). Account sets differ (641 vs 644).

(Also in Downloads but unused by any dashboard: `ctrypremApr26.xlsx`.)

## Cross-file facts
- Join key: `importer_user_id` = `Buyer_ID`. View 2 joins only by Buyer name (case-insensitive).
- Row drift: 645 (V1) vs 643 (master) vs 644 (current OB) vs 641 (historic OB); suspended 414 vs 412. Extracts snapshotted at slightly different times — outer-join + null handling required.

## Segmentation validation (run 2026-06-10 against live files)

With AM resolved as V1 `AM_Name` primary, master `AM` fallback (the rule both the HTML and the Streamlit app use):

| Universe definition | Count |
|---|---|
| Nikhil team: AM ∈ 5-list (HTML pod rule, **no partner filter**) | **250** |
| Nikhil team: AM ∈ 5-list AND Partner ≠ Direct (current Streamlit rule) | **226** (drops 24 Direct-partner accounts) |
| Pankit team: AM ∈ 4-list (no partner filter) | **215** — matches the "215 Accounts" header of Pankit's original |
| Pankit team: AM ∈ 4-list AND Partner = Direct (current Streamlit rule) | **194** (Kaustav 66, Pejush 62, Sonal 48, Pankit 18) |
| Pankit team: AM ∈ 4-list AND Team = Direct | 195 |
| Pankit's embedded RAW.accounts | **128** (Kaustav 50, Sonal 38, Pejush 35, Pankit 5) — reproducible by **no** filter combination on the current extracts; RAW also has OB values that differ from the Jun-5 master (e.g. DAXX 2,245,527.8 vs 1,996,446.02), so it came from a different snapshot/filter. Live derivation is the agreed approach. |

## Utilization formula check
- Nikhil HTML: `totalFac = Facility_Size + overdraft_limit`; util = ob / totalFac.
- Pankit RAW: `utilization = ob / facility` and `target_ob = facility × 0.75` — **facility only**. (Spot-checks Style Source 480585, Nova Eye 479766, DAXX 204587 all have overdraft 0 so both formulas agree on them; the formula difference only bites on overdraft accounts — 43 accounts portfolio-wide have overdraft > 0.)

## Open items resolved with the user — 2026-06-10
1. Team universes → **Nikhil = AM-list only (250)**; **Pankit = AM-list + Partner='Direct' (194)**.
2. Utilization denominator → **per-team**: Nikhil = Facility + Overdraft; Pankit = Facility only.
3. Theme → **keep the current light theme**; replicate chart groupings/series colors/conditional rules only.
4. Reactivation List file (Nikhil View H/T) — no such file in Downloads → reactivation views derive from
   the live data (Workable + suspended + dormant ≥180d, sorted by peak OB); the list-file upload can be
   added later if the file resurfaces.
