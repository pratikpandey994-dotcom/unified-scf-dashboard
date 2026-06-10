# Portfolio Dashboard

Consolidates Team Nikhil's CP-pod view and Team Pankit's direct-sales view into one Streamlit dashboard,
replicating each leader's original dashboard (specs in `docs/`).

## Run

```powershell
cd C:\Users\PratikPandey\unified-scf-dashboard
streamlit run app.py
```

## Files

- `app.py` — shell: sidebar data source, division/AM/status filters, session-state navigation, view dispatch.
- `metrics.py` — segmentation, classification, KPI/risk/repayment/origination/window logic.
- `views_nikhil.py` — Team Nikhil views (Snapshot, Portfolio, Team, Health, Actions, Account Pulse, Peak, CP Health, Tracker), ported from the CP Pod HTML.
- `views_pankit.py` — Team Pankit views (Executive, Inventory, Utilization, Zero OB, Workable Inactive, Repayments, OB Dent, AM Performance, 75% Engine, Opportunity Views), ported from the 75% Utilization Engine.
- `ui_helpers.py` — formatters, table column config, chart helpers.
- `data_loader.py` — single cached `load_data()` for Excel ingestion + deterministic demo data.
- `docs/` — Phase 1 specs of both originals, data validation report, Streamlit audit.
- `_verify_metrics.py`, `_verify_app.py` — regression checks (metric numbers + headless click-through of every view).
- `tracker_state.json` — persisted Team Tracker statuses/comments (created on first save).

## Default Data Paths

When manual upload is off, the app loads these from `C:\Users\PratikPandey\Downloads`:

- `scf_am_team___view_1_with_suspension_reasons_2026-06-05T13_49_41.37721429Z.xlsx`
- `view_2_2026-06-05T13_49_21.379501371Z.xlsx`
- `us_scf___master_data___handover_date_2026-06-05T14_10_07.092355226Z.xlsx`
- `Historic OB.xlsx`
- `us_scf___daily_ob_by_accounts_2026-06-03T15_05_48.33250036Z.xlsx`

Manual uploads are available from the sidebar. For UI testing, switch `Source` to `Dummy data`.

## Team Logic (agreed 2026-06-10)

- **Team Nikhil** = every account whose AM (View 1 primary, master fallback) is in
  {Nikhil Shetty, Darshan Hublikar, Deepsayan Dam, Ashitha Nair, Asif Ali}. No partner filter (matches the HTML pod). 250 accounts on the Jun-5 extracts.
- **Team Pankit** = accounts of {Pankit Shah, Sonal Mishra, Pejush Hal, Kaustav Das} with Partner = `Direct`. 194 accounts on the Jun-5 extracts.
- CP Health (under Team Nikhil) intentionally covers ALL CP accounts (Team='CP', Partner≠'Direct', every AM) and ignores filters, like the original View G.

## Metric Rules

- **Team Nikhil**: total facility = `Facility_Size + Overdraft_Limit`; headline OB/Facility/Utilization/WIRR computed over **in-target** accounts (Active + Suspended Workable) only.
- **Team Pankit**: utilization/75% target use **facility only** (no overdraft), per the 75% Engine.
- 75% target = denominator × 0.75; gap to 75% = `max(target − OB, 0)`.
- Repaid (always) = `max(Origination − Outstanding, 0)` for `closed/paid/received/partial` invoices settled in window.
- Overdue OB = open-stage outstanding with `7 < dpd ≤ 90`; NPA OB = `dpd > 90`; Clean OB = in-target OB − overdue − NPA.
- WIRR = OB-weighted signed-up IRR (zero shown as `—`).
- Account classification: Non-Workable → NWA; Workable with no disbursement ≤365d → `Workable >365`; else Active/Suspended Workable by View-1 utilization status.
- Weeks run Monday→Sunday; MTD/QTD/CW/NW/CM/NM windows match the HTML's `getWindow`.

## Theme

Light theme (`.streamlit/config.toml`) kept deliberately; charts reuse the originals' series colors,
groupings, and threshold-based color rules (e.g., WIRR green ≥20 / amber ≥18 / red).
