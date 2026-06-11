# Visual Standardization Study

Scope:
- `Downloads/Nikhil Dashboard Code`
- `Downloads/Pankit Dashboard code`
- unified Streamlit app in this repo

Goal:
- preserve the useful business signals from both source dashboards
- remove duplicate or noisy presentation
- standardize the unified SCF dashboard into one consistent visual language

## 1. What each source dashboard is really doing

### Nikhil dashboard
- Leader-grade portfolio control room.
- Stronger on risk, collections, targetability, and drill-down behavior.
- Uses many interactive controls: filters, bucket clicks, table highlights, window toggles, and view-specific actions.
- Visual hierarchy is dense but structured: top summary, then focused analytical sections.

### Pankit dashboard
- Utilization engine and AM performance board.
- Stronger on utilization bands, 75% target logic, account-level inventory, and AM comparison.
- Uses a compact KPI row plus stacked operational tabs.
- More explicit about target gap, inactive accounts, repayments, and 75% opportunity.

## 2. Component inventory to standardize

| Area | Nikhil source | Pankit source | Unified standard |
|---|---|---|---|
| Header | branded control room, many tabs | branded engine header, fixed tabs | one simple title, one team selector, one theme toggle |
| KPI row | portfolio quality, targetable, collections | utilization, inactive, repayments, opportunity | 6 cards max, same card size and order |
| Portfolio quality | donut + table + clickable filters | not central | keep as one primary risk block |
| Utilization | targetable and bucketed analysis | 75% engine is core | keep as one core utilization block |
| AM performance | scorecards + status | AM comparison + utilization | one AM performance chart and one summary table |
| Collections | due windows, overdue/NPA, recovery | repayments and workability emphasis | keep one collections section with due and overdue tables |
| Drill-down | many click paths | mostly table sort/filter | preserve only the useful clicks that change the table |

## 3. What to keep from each source

### Keep from Nikhil
- portfolio quality donut
- overdue and NPA split
- targetable portfolio view
- due window logic
- collections and recovery focus
- account-level drill-down tables

### Keep from Pankit
- 75% utilization framing
- utilization distribution
- AM comparison
- account inventory table
- inactive / zero-OB focus
- opportunity gap framing

## 4. What to remove or compress

- duplicate “smart path” style navigation
- overlapping KPI cards that repeat the same math in different words
- secondary charts that do not change decisions
- dense explanatory text inside the main canvas
- repeated filters that appear in both sidebar and content area

## 5. Recommended unified IA

1. Portfolio snapshot
2. Balance and utilization
3. Account managers
4. Risk and collections
5. Account detail

## 6. Unified visual rules

- one theme toggle in the sidebar
- one team toggle in the sidebar
- light/dark must share the same layout and naming
- keep the main page under 8 to 10 visible components
- use one chart language for balances and one for risk
- use concise business labels, not internal labels
- keep tables scannable and avoid full-width noise blocks

## 7. Naming standard

| Old style | Unified style |
|---|---|
| Overview | Portfolio snapshot |
| Performance | Account manager performance |
| Utilization Engine | Balance and utilization |
| Opportunity Views | Collections and opportunity |
| Portfolio Quality | Risk exposure |
| Smart path | Quick access |

## 8. Working conclusion

The unified dashboard should not try to reproduce every original screen.
It should preserve the business logic from both sources, then show it through one calmer, more readable layout:
- Nikhil for risk and collections depth
- Pankit for utilization and target gap clarity
- unified SCF for a single director-level view with theme toggle support

## 9. Implementation mapping

Implemented in the unified Streamlit dashboard:

| Recommendation | Current implementation |
|---|---|
| Light/dark support | Sidebar Theme toggle; both modes use the same layout and labels |
| Nikhil/Pankit source-specific utilization rules | Nikhil uses facility + overdraft; Pankit uses facility only |
| Nikhil headline balance nuance | Nikhil's balance/utilization summary uses in-target accounts |
| Portfolio quality | Donut with Clean / Overdue / NPA plus buttons routing to account detail |
| Due windows | This week / this month / next month cards route to account detail |
| 75% engine | Targetable portfolio, 75% gap value, high-opportunity queue, top gap chart |
| Pankit opportunity logic | Gap-to-75 and zero-OB queues added to a unified action tab |
| Nikhil collections/action logic | Overdue/NPA, due windows, dormant, and OB-reduction queues added |
| Common drill-down | Account detail has a focus selector shared by all section buttons |
| Peak movement and OB dent | Peak vs current trend, per-AM mode, window controls, peak-decline queue, and 30d OB reduction chart added |
| CP partner health | CP-only partner rollup with health score, WIRR, and risk split added |
| Recovery collections | Open overdue/NPA invoices with recovered principal are aggregated by company |
| Unassigned CP accounts | CP partner accounts without an owner are highlighted under partner health |
| Manager tracker | Priority account queues are editable in-session with status, owner, comments, follow-up dates, and CSV export |

Still missing or intentionally deferred:

| Source item | Recommended next action |
|---|---|
| Nikhil Peak Analysis | Implemented as a compact peak-vs-current movement tab with per-AM mode and peak-decline drill-down |
| Nikhil CP Health | Implemented as a CP partner health section using the CP-only universe |
| Nikhil editable tracker | Implemented as an in-session Streamlit tracker; durable persistence remains deferred until storage requirements are clear |
| Pankit sortable React table behavior | Streamlit dataframe sorting is sufficient for now |
| Pankit OB dent deep tracker | Current action queue includes 30d reductions; add a dedicated dent chart only if used operationally |
| Full clickable chart bars | Current implementation uses section buttons and table focus; chart-click drilldown can be added later if needed |
