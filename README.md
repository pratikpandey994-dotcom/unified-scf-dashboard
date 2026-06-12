# Portfolio Dashboard

Consolidates Team Nikhil's CP-pod view and Team Pankit's direct-sales view into one Streamlit dashboard,
replicating each leader's original dashboard (specs in `docs/`).

## Run

```powershell
cd C:\Users\PratikPandey\unified-scf-dashboard
streamlit run app.py
```

## Files

- `app.py` — shell: sidebar data source, theme, division/AM/status filters, tab dispatch.
- `dashboard_metrics.py` — segmentation, classification, KPI/risk/repayment/origination/window logic.
- `views_nikhil.py` — Team Nikhil views (Overview, Portfolio Quality, Team, Risk & Health, Collections, Account Pulse, Peak Movement, CP Health, Tracker), ported from the CP Pod HTML.
- `views_pankit.py` — Team Pankit views (Overview, Inventory, Utilization, Zero OB, Workable Inactive, Repayments, OB Dent, AM Performance, 75% Engine, Opportunity), ported from the 75% Utilization Engine.
- `views_common.py` — shared **Insights** tab (booked revenue, industry/state mix, supplier concentration, DPD aging, ops flags) — analytics unlocked by the Jun-11 extracts.
- `ui_helpers.py` — formatters, table column config, chart helpers, visual system, Excel export.
- `data_loader.py` — cached two-file ingestion + invoice-derived OB reconstruction + deterministic demo data.
- `docs/` — Phase 1 specs of both originals, data validation, Streamlit audit, design studies, **DATA_MIGRATION_2026-06-11.md** (current data contract).
- `_verify_metrics.py`, `_verify_app.py` — regression checks (metric numbers + headless render of every view/widget).
- `tracker_state.json` — persisted Team Tracker statuses/comments (created on first save).

## Data Inputs (since 2026-06-11)

Two consolidated extracts replace the old five files. The loader auto-discovers the **newest** match
in `Downloads`, so re-extracted files with new timestamps work without code changes:

- `us_scf___master_data___client_level_*.xlsx` — one row per account (647 × 37)
- `us_scf___invoice_level_data_*.xlsx` — one row per invoice (36,975 × 35), carries `IMPORTER_USER_ID`
  so invoices join accounts by ID (the old name-join is retired)

There are no daily-OB files anymore. OB history (trend, peak, OB 30/90d ago, dent) is **reconstructed
from invoices**: origination held from advance date to settlement date. Validated within ~5% of
open-invoice outstanding; charts are labeled "invoice-derived (advance basis)". See
`docs/DATA_MIGRATION_2026-06-11.md` for the full mapping and decision log.

Manual uploads are available from the sidebar. For UI testing, switch `Source` to `Demo data`.

## Team Logic (agreed 2026-06-10, re-mapped 2026-06-12)

- **Team Nikhil** = every account whose AM is in
  {Nikhil Shetty, Darshan Hublikar, Deepsayan Dam, Ashitha Nair, Asif Ali}. No type filter
  (matches the HTML pod). **255 accounts** on the Jun-11 extracts.
- **Team Pankit** = accounts of {Pankit Shah, Sonal Mishra, Pejush Hal, Kaustav Das} with
  `TYPE = 'DIRECT'` (the old `Partner = 'Direct'` rule). **193 accounts** on the Jun-11 extracts.
- CP Health (under Team Nikhil) covers ALL CP accounts (`TYPE = 'CP'`, partner = `CP_COMPANY`,
  every AM) and ignores filters, like the original View G. **313 accounts / 43 partners.**

## Metric Rules

- **Team Nikhil**: total facility = `FACILITY_SIZE + OVERDRAFT_LIMIT` (= `TOTAL_LIMIT`); headline
  OB/Facility/Utilization/WIRR computed over **in-target** accounts (Active + Suspended Workable) only.
- **Team Pankit**: utilization/75% target use **facility only** (no overdraft), per the 75% Engine.
- 75% target = denominator × 0.75; gap to 75% = `max(target − OB, 0)`.
- Repaid (always) = `max(Origination − Outstanding, 0)` for `closed/paid/received/partial` invoices settled in window.
- Overdue OB = open-stage outstanding with `7 < dpd ≤ 90`; NPA OB = `dpd > 90`; Clean OB = in-target OB − overdue − NPA.
  (`DAYS_PAST_DUE` is null when not past due → treated as 0.)
- WIRR = OB-weighted signed-up IRR (zero shown as `—`).
- Account classification: Non-Workable → NWA; Workable with no disbursement ≤365d → `Workable >365`; else Active/Suspended Workable by `USER_UTILIZATION_STATUS`.
- Weeks run Monday→Sunday; MTD/QTD/CW/NW/CM/NM windows match the HTML's `getWindow`.
- Account-level OB comes from master `OB`; invoice-level risk uses `OUTSTANDING_ADVANCE_BALANCE_USD`
  (the two intentionally differ — both originals had the same duality).

## Theme

Light theme by default with a Dark toggle (`ui_helpers.inject_visual_system`); charts reuse the
originals' series colors, groupings, and threshold-based color rules (e.g., WIRR green ≥20 / amber ≥18 / red).
