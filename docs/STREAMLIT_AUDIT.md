# Phase 2 — Audit of the Current Streamlit App (2026-06-10)

Files audited: `app.py` (714 lines), `metrics.py` (284), `data_loader.py` (359), `.streamlit/config.toml`.

## 2.1 What is correctly implemented

**Data layer (`data_loader.py`)**
- ✅ All 5 default file paths correct and existing; manual upload + demo mode work.
- ✅ `@st.cache_data` on `load_data` and `load_demo_data`.
- ✅ `norm_id` matches the HTML's `normID` (strips commas + trailing `.0`).
- ✅ Stage lowercased/trimmed; dates coerced; numerics coerced with fillna(0).
- ✅ Historic + Current OB concatenated (clean seam given file date ranges).

**Metrics (`metrics.py`)**
- ✅ AM lists match both originals exactly (NIKHIL_AMS = POD_AMS; PANKIT_AMS = Pankit's 4).
- ✅ Stage sets match the HTML (`SETTLED`, `REPAYMENT_STAGES` = settled+partial, `OPEN_STAGES`).
- ✅ Level-2 classification (`_classify_level`) matches the HTML exactly (NWA / >365 / Active / Suspended Workable).
- ✅ AM resolution: V1 `AM_Name` primary, master `AM` fallback — matches HTML.
- ✅ Facility/overdraft/OB/IRR V1-primary-master-fallback coalescing matches HTML.
- ✅ MTD repayments = `max(0, Origination − Outstanding)` for settled+partial invoices settled in [month start, today] — matches both originals' repayment logic.
- ✅ Overdue OB (`dpd>7 & ≤90`) and NPA OB (`dpd>90`) over OPEN stages — matches HTML.
- ✅ `gap_to_75 = max(0.75·fac − ob, 0)`, `net_ob = ob − mtd_repayments` — match Pankit (modulo the denominator question).
- ✅ Invoice→account mapping by lowercased Buyer name (same behavior as HTML, same JAYMIN caveat).
- ✅ Utilization buckets (0 / 0–25 / 25–50 / 50–75 / 75–100 / >100) match Pankit's tab 2.

**App (`app.py`)**
- ✅ Division → AM → account-type/status filter cascade exists, with per-team widget keys.
- ✅ `fmt_money` matches both originals' `$X.XXM` formatter (minor: K-form uses 1dp like Nikhil; Pankit uses 0dp).
- ✅ Pankit tabs Zero OB / Workable Inactive / OB Dent / 75% Engine / Opportunity Views replicate most of the original's KPIs, filters, and table columns.
- ✅ CP health-score formula (4 × 25-pt components) matches Nikhil's View G.

## 2.2 Broken or wrong (vs the source-of-truth originals)

| # | Issue | Should be (source) | Currently | Root cause |
|---|---|---|---|---|
| B1 | **Team Nikhil universe too small (226 vs 250)** | Pod = AM ∈ 5-list, no partner filter (HTML `processData`) | `filter_team` also requires `partner_segment == 'cp_partner'`, silently dropping 24 Direct-partner accounts of Nikhil's AMs | Segment filter invented during consolidation; README documents it but it contradicts the HTML |
| B2 | **Team Pankit universe unverified (194)** | Original embeds 128 accounts but headers claim 215 (= AM-list-only count) | AM-list + Partner==Direct → 194 | RAW.accounts not reproducible from current extracts; needs a user decision |
| B3 | **Headline KPIs use wrong universe for Nikhil** | Total OB/Facility/Util = **in-target only** (Active+Suspended Workable) (HTML View F/A) | Sums over all filtered accounts incl. NWA and >365 | `portfolio_kpis` has no level-2 filter |
| B4 | **WIRR includes NWA accounts and shows 0 IRRs** | WIRR over in-target accounts; `fmtIRR` renders 0 as `—` (HTML) | `weighted_irr(accounts)` over everything | same as B3 |
| B5 | **One generic KPI row for both teams** | Nikhil: OB/Fac/Util/Accounts + 6 health tiles + 3 WIRR + Risk(Clean) tiles. Pankit: 10 specific cards (Workable, Active, Inactive, Zero-OB, Facility, OB, Util%, Net OB, June Repay, Inactive ≤12 mo) | 10 mixed metrics (e.g. Gap-to-75 shown for Nikhil, who never had it; no Clean OB; no NPA card) | KPI row designed as lowest common denominator |
| B6 | **`st.tabs` resets to the first tab on every widget interaction** — the main "not interactive" complaint. Any radio/selectbox inside a later tab (Opportunities view radio, Tracker selectbox/radio) reruns the script and jumps back to tab 1, so those controls appear dead | Views persist (original is an SPA) | Streamlit-native tabs hold no state | Navigation not bound to `st.session_state` |
| B7 | **Non-Workable leaks into 75% Engine / Opportunity views** | Pankit: `status.startsWith("Workable")` | regex `contains("Workable\|Active\|Suspended\|Inactive")` — `"Non-Workable"` contains `"Workable"` → matches | wrong string predicate |
| B8 | **Utilization buckets: Pankit's bands applied to Nikhil** | Nikhil View C: Zero / 1–40 / 41–74 / 75–100 over in-target WA, clickable cards + donut + WIRR-by-bucket | one shared 6-bucket bar for both teams | shared tab not team-specialized |
| B9 | **CP Health runs on the wrong universe** | View G = ALL CP accounts (Team='CP' & Partner≠'Direct', every AM, ignores the AM filter) | receives AM-filtered Team-Nikhil pod accounts | filtered frame passed in |
| B10 | CP Health partner chart stacked + missing charts | Grouped horizontal Facility vs OB (top 20); Risk-by-partner stacked bar; WIRR-by-partner bar; expandable partner scorecards | one `px.bar` (defaults to stacked); no risk/WIRR charts; flat table | partial port |
| B11 | **Declining Accounts uses OB-dent proxy** | HTML View D: invoice-based MTD/QTD window — declining = repaid > originated in window | `ob_dent_30d > 0` on accounts | different formula |
| B12 | Reactivation Focus wrong filter | `broad=='Workable' && v1util=='suspended' && daysSince>=180`, sorted peak OB | status regex `Suspended\|Inactive` OR `days>=180` (no Workable requirement, OR instead of AND) | loose predicate |
| B13 | Early Repayment table unscoped/unsorted | `settled < due`, sorted days-early desc, cap 300, Days Early column | sorted by Origination, no day count, no cap | partial port |
| B14 | Tracker is a different feature | 7 specific buckets (Overdue/NPA, due cw/nw/nm, Net-negative MTD, Suspended-still-repaying, Approaching inactive) + editable status/comments/follow-ups (persisted) + referral tracker | 4 generic read-only buckets (NPA/Overdue/Suspended/Active) | not ported |
| B15 | Peak view incomplete | Auto/Custom peak date, WA vs NWA split, zero-categories, clickable tiles, waterfall top 40, 11-filter table, per-AM trend mode, window toggles | single auto peak, one bar chart, one table | partial port |
| B16 | Missing Nikhil views entirely | View A (PQ donut+table, IRR threshold, targetable panels, OB movement/AM, Orig-vs-Repay, Collections), View B (AM scorecards, status distribution), View C (overdue/NPA sections, DSLD), View H (everything), Portfolio Report, Unassigned CP alert, High Opportunity (headroom+due), Recovery detail | absent | not ported |
| B17 | Missing Pankit Executive tab layout | 10 KPI cards + OB trend line (with reference lines) + repayments-by-AM bar + AM snapshot table | generic Snapshot tab (AM bar + **OB-by-account-type donut that exists in neither original**) | invented layout |
| B18 | AM Performance details off | Pankit: avgUtil = mean over facility>0 accounts only; repay/orig from dedicated tables; 2×2 AM cards with 8 tiles | mean over all accounts; originations = Σ invoice Origination all-time (≈ right concept); no cards | partial port |
| B19 | **Theme matches neither original** | Nikhil: dark navy `#1a1a2e`/amber `#f59e0b`, IBM Plex. Pankit: dark slate `#020817`/sky `#38bdf8`, DM Sans | light theme, teal `#0d9488`; default Plotly palette everywhere | config.toml + no chart styling |
| B20 | Workable-Inactive months formula | Pankit: `days/30.4` 1dp | `days/30` | minor |
| B21 | OB-dent flag threshold display | Pankit flags `pct > 25` (%) | metrics stores fraction and app compares `> 0.25` ✅ but the Opportunities tab "30d OB Dent" view reuses it with no `valid` (ob>0 or ob_30d>0) guard | minor |
| B22 | `inactive_12m` KPI computed but never displayed; `npa_ob` computed, never displayed | Pankit card 10 / Nikhil risk tile | dead code | omission |

## 2.3 Not interactive but should be

- Tab/view persistence (B6) — the single biggest UX breakage.
- Nikhil: global AM filter exists ✅, but missing: MTD/QTD/Custom window toggles (Orig-vs-Repay, Declining), cw/nw/cm/nm window toggles (Collections, High Opportunity, due tiles), IRR threshold inputs, PQ category dropdown, utilization-bucket click-to-drill, DSLD bucket dropdown, H sort/slice toggles, P auto/custom peak + trend mode/window + tile filters, T editable tracker fields.
- Pankit: status filter exists as multiselect ✅ (richer than original pills); missing: per-tab default sorts are fixed by code ✅ (st.dataframe column sort covers click-sort), Executive reference lines/tooltips.
- Sidebar "As of date" exists ✅ (matches HTML "Today" input).

## Performance / robustness notes
- `_closest_ob` does a Python list-comprehension over the full date index **per account × 2** (~645 × 1,249) — slow; vectorize with `ob_pivot.index searchsorted`.
- `build_portfolio` iterates master rows with `.iterrows()` — acceptable at 643 rows but vectorizable.
- 780k-row Historic OB load is cached ✅.
- OB clamping (negative residues) not applied — sums can be microscopically off; harmless but easy to clamp.
- `metric_row` divides by zero nowhere ✅; `ob_trend` handles empty pivots ✅.
