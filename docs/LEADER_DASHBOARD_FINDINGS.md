# Leader Dashboard Findings

Scope:
- `Downloads/Nikhil Dashboard Code`
- `Downloads/Pankit Dashboard code`
- existing study docs in `docs/`
- unified Streamlit repo README and audit notes

Goal:
- document what each dashboard is doing today
- identify shared patterns, assumptions, and data dependencies
- recommend a unified two-view structure before any redesign work starts

## Executive Summary

The two leader dashboards solve related but different management problems.

Team Nikhil is a portfolio control room. It is built around risk, collections, reactivation, peak movement, and deeper account drill-down. It is data-pipeline heavy and stateful: it ingests multiple Excel files, joins them, classifies accounts, persists tracker state, and drives several drill-down views.

Team Pankit is a utilization engine. It is built around the 75% target, low-utilization opportunity, zero-OB inventory, AM comparison, and OB dent. It is much simpler technically: one embedded snapshot, no external joins, mostly client-side filtering and sorting.

The best unified direction is not to merge everything into one generic screen. It is to keep one shared shell and provide two leader-specific views:
- Portfolio Risk and Collections for Team Nikhil
- Utilization and Opportunity for Team Pankit

## 1. Team Nikhil Dashboard

### Purpose and business questions

This dashboard answers the questions a portfolio leader needs every day:
- How much of the portfolio is clean, overdue, or NPA?
- Which accounts are active, suspended, non-workable, or aged out?
- Which accounts are targetable today and which are excluded?
- What collections are due this week, next week, this month, or next month?
- Which accounts are declining, dormant, or approaching inactivity?
- Which AMs are strongest or weakest by book quality?
- Where did OB peak, where is it now, and what changed?
- Which CP accounts need partner-level attention?

### Visual hierarchy and layout logic

The HTML is structured as a dense but ordered control room:
1. Upload and launch gate.
2. Sticky header with brand, date, tabs, and upload-again action.
3. Executive snapshot with KPI cards.
4. Portfolio, team, health, actions, pulse, peak, tracker, and CP health tabs.

The visual language is functional:
- KPI cards for quick scanning.
- Donut charts for mix/composition.
- Horizontal bars for ranking and comparison.
- Detailed tables for operational follow-up.
- Expand/collapse panels to keep detail available without forcing constant scroll.
- Window toggles for MTD, QTD, current week, next week, current month, and next month actions.

Why these visuals were chosen:
- Cards summarize the answer to one management question.
- Donuts show portfolio mix at a glance.
- Bar charts compare AMs, partners, or utilization buckets cleanly.
- Tables are used whenever the user needs account-level action.

### Data model and flow implied by the code

The dashboard is truly data-driven, not hardcoded.

It ingests five Excel inputs:
- View 1 accounts
- View 2 invoices
- Master handover
- Historical OB
- Current OB

The code then builds a layered in-memory model:
- account universe is defined by a fixed AM list, not by team label alone
- V1 AM is primary, master AM is fallback
- buyer ID joins account tables
- buyer name joins invoice tables
- historical and current OB are stitched with a cutoff date around 2026-05-01
- a reactivation list and tracker state are persisted locally

Key assumptions:
- team membership is defined by the AM list
- invoice risk is driven by DPD thresholds
- utilization uses facility plus overdraft
- WIRR is OB-weighted signed-up IRR
- weeks run Monday through Sunday
- company matching is case-insensitive, which is a deliberate simplification

### Reusable patterns and inconsistencies

Reusable patterns:
- KPI tiles
- status badges
- account tables
- window toggle controls
- chart cards
- drill-down rows and expanders

Inconsistencies:
- several concepts appear in more than one view under different names
- some views duplicate the same account universe with slightly different filters
- the dashboard mixes portfolio-level and account-level questions in adjacent sections
- the CP health view deliberately ignores the AM filter, which makes it structurally different from the rest of the app

### Improvement opportunities

- reduce repeated risk sections by consolidating related views
- shorten section titles and use more consistent language
- simplify the number of visible controls per screen
- make the tables less dense and more scannable
- keep only the charts that change decisions, not every chart that can be derived

## 2. Team Pankit Dashboard

### Purpose and business questions

This dashboard answers a narrower set of operational questions:
- how much of the book is at or above 75% utilization?
- which accounts are below target and how large is the gap?
- which accounts are zero OB or very low utilization?
- which accounts have not been funded recently?
- which accounts are losing OB over time?
- how do AMs compare on book size, OB, utilization, repayments, and originations?
- where is the next opportunity to push utilization upward?

### Visual hierarchy and layout logic

The dashboard is more compact and more opinionated:
1. Executive tab with summary KPIs, trend, AM repayment/origination bar, and portfolio table.
2. Inventory and utilization tabs for account-level inspection.
3. Zero OB and Workable Inactive tabs for reactivation work.
4. Repayments, OB dent, AM performance, 75% engine, and opportunity tabs for action.

The chosen visuals are consistent with a sales/utilization workflow:
- KPI cards for headline health.
- Bar charts for AM comparison and utilization buckets.
- Tables for account inventory and opportunity ranking.
- Reference lines to show the 75% target.

Why these visuals were chosen:
- the 75% threshold is the central business rule, so it is repeated in charts and table columns
- zero-OB and low-utilization accounts are easiest to work from a table
- AM performance is better read as a comparison grid than as narrative text

### Data model and flow implied by the code

This dashboard does not compute from live files.

It uses a single embedded `RAW` object with:
- precomputed account rows
- precomputed trend points
- precomputed repayments by AM
- precomputed originations by AM

Implications:
- there is no file loading, joining, or persistence layer
- the snapshot is fixed to the embedded data date
- the dashboard depends on upstream preprocessing that is not visible in the code
- some labels and numbers are stale or inconsistent with the current live extracts

Key assumptions:
- utilization uses facility only, not overdraft
- target OB is exactly 75% of facility
- account status labels are fixed and enumerated
- the data snapshot is authoritative even when it is not reproducible from current files

### Reusable patterns and inconsistencies

Reusable patterns:
- KPI cards
- sortable tables
- AM color dots
- utilization badges
- status badges
- chart cards

Inconsistencies:
- some tab titles do not match the chart contents exactly
- some sections ignore the active filters
- the embedded data does not match the current live extract set
- the UI is visually coherent, but the data contract is not portable

### Improvement opportunities

- align titles with the actual metrics shown
- make the opportunity views more explicit about what is filtered and what is not
- reduce repeated threshold language
- replace stale embedded data with the same live pipeline used by the unified repo
- keep the strong AM comparison and 75% framing, but put it in a cleaner shell

## 3. Shared Patterns Across Both Dashboards

Common patterns:
- both are leader dashboards, not generic BI pages
- both are built for action, not passive reporting
- both rely on account-level tables and status badges
- both use AM filtering as a primary control
- both use charts mainly for comparison and ranking
- both rely on a small number of business concepts: AM, facility, OB, utilization, repayments, origination, risk, and date windows

Common reusable primitives:
- KPI card
- sortable table
- chart card
- status badge
- AM color token
- threshold-based coloring
- account-level drilldown

Main differences:
- Nikhil is broader and deeper, with risk, collections, peak analysis, tracker, and CP health
- Pankit is narrower and more focused on utilization and opportunity
- Nikhil is file-driven and stateful
- Pankit is embedded and static
- Nikhil uses facility plus overdraft
- Pankit uses facility only

## 4. Unified Two-View Recommendation

The best unified structure is one shared shell with two leader-specific views.

### Shared shell

Standardize these once for both views:
- light theme
- one header with title, date, and source/team selector
- one AM filter control
- one KPI card pattern
- one chart color system
- one table style system
- one badge language system
- one window-control component

### View 1: Portfolio Risk and Collections

This view should preserve the strongest parts of Team Nikhil's dashboard:
- portfolio quality split
- overdue and NPA logic
- targetable portfolio
- collections due windows
- recovery collections
- reactivation and inactivity tracking
- account pulse and peak movement
- CP health if the user is in a CP-facing role

This view should answer:
- what is clean versus at-risk
- what cash is due soon
- what accounts are fading or reactivatable
- where are the biggest risk movements

### View 2: Utilization and Opportunity

This view should preserve the strongest parts of Team Pankit's dashboard:
- 75% utilization engine
- utilization distribution
- zero OB and low-utilization inventory
- Workable Inactive inventory
- OB dent tracking
- AM performance comparison
- top opportunity ranking

This view should answer:
- where is the gap to target
- which accounts need immediate funding or reactivation
- which AMs are creating or losing OB
- what opportunity is most actionable this week

## 5. Keep / Merge / Redesign / Standardize

### Keep
- Nikhil's risk, collections, peak, and CP health logic
- Pankit's 75% engine, AM comparison, and opportunity framing
- account-level sortable tables
- threshold-based badges and color rules
- AM-level comparison

### Merge
- executive summary cards into one top KPI band per view
- targetable and opportunity views into one utilization-opportunity section
- collections, overdue, and recovery logic into one collections section
- AM scorecards into one normalized AM comparison block
- zero OB, inactive, and dent reporting into one actionable inventory section

### Redesign
- crowded header navigation
- duplicated metrics presented under different names
- overly dense table sections
- inconsistent chart titles
- dark legacy styling if the target is a light-theme dashboard
- any section that shows the same answer in two places

### Standardize
- typography
- spacing
- card dimensions
- table column ordering
- number formatting
- date formats
- status colors
- utilization thresholds
- chart palette
- window selector placement
- naming conventions for portfolio, opportunity, risk, and collections

## 6. Assumptions and Dependencies to Preserve

Do not lose these during implementation:
- Nikhil team membership is AM-list driven
- Pankit source is a pre-curated direct-sales snapshot; the unified repo later applies an explicit Direct-partner rule to live files
- Nikhil utilization includes overdraft
- Pankit utilization does not
- overdue means DPD 8-90
- NPA means DPD greater than 90
- weeks are Monday through Sunday
- company matching is case-insensitive
- historical OB and current OB are separate files that need a seam
- reactivation and tracker state need persistence

## 7. Source References

- [Nikhil Dashboard Code](<C:/Users/PratikPandey/Downloads/Nikhil Dashboard Code>)
- [Pankit Dashboard code](<C:/Users/PratikPandey/Downloads/Pankit Dashboard code>)
- [VISUAL_STANDARDIZATION_STUDY.md](<C:/Users/PratikPandey/unified-scf-dashboard/docs/VISUAL_STANDARDIZATION_STUDY.md>)
- [NIKHIL_DASHBOARD_SPEC.md](<C:/Users/PratikPandey/unified-scf-dashboard/docs/NIKHIL_DASHBOARD_SPEC.md>)
- [PANKIT_DASHBOARD_SPEC.md](<C:/Users/PratikPandey/unified-scf-dashboard/docs/PANKIT_DASHBOARD_SPEC.md>)
- [README.md](<C:/Users/PratikPandey/unified-scf-dashboard/README.md>)

## 8. Bottom Line

The two dashboards are not duplicates. They are two views of the same operating problem.

The unified product should preserve both perspectives, but it should stop presenting them as two unrelated interfaces. The right design is a clean light-theme shell with two leader-specific views, a shared vocabulary, and a single set of visual rules.

That gives the business one consistent dashboard without flattening the differences that make each leader's view useful.
