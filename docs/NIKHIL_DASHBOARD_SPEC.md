# Phase 1 Spec — Nikhil's Original Dashboard ("CP Pod · SCF Portfolio Dashboard")

**Source:** `C:\Users\PratikPandey\Downloads\Nikhil Dashboard Code` (single self-contained HTML file, 4,170 lines)
**Libraries:** SheetJS `xlsx 0.18.5`, `Chart.js 4.4.1` (CDN), Google Fonts IBM Plex Sans / IBM Plex Mono.
**Architecture:** Upload screen → `processData()` builds in-memory model `G` → 9 tab views rendered client-side. Persistence: IndexedDB (`scf_pod_cache` / store `files`) for large OB files; `localStorage` for Master Handover, Reactivation List, and all Team-Tracker fields.

---

## 0. GLOBAL CONSTANTS & HARDCODED VALUES (lines 1267–1276)

```js
const POD_AMS = ['Nikhil Shetty','Darshan Hublikar','Deepsayan Dam','Ashitha Nair','Asif Ali'];
const AM_COLORS = ['#f59e0b','#10b981','#6366f1','#f97316','#94a3b8'];   // index-paired to POD_AMS
const AM_INITIALS = {'Nikhil Shetty':'NS','Darshan Hublikar':'DH','Deepsayan Dam':'DD','Ashitha Nair':'AN','Asif Ali':'AA'};
const SETTLED  = new Set(['closed','paid','received']);
const PARTIAL  = new Set(['partial']);
const OPEN     = new Set(['advanced','overdue','npa','partial']);
const EXCLUDED = new Set(['partadvanced','processing','deposit_pending','pending_advance','data_entry','verify_bank_details','hold']);
```

Other hardcoded values used throughout:
- **OB-file date cutoff:** `new Date('2026-05-01T00:00:00')` — Historical OB rows are used only when `ob_date < cutoff`; Current OB rows only when `ob_date >= cutoff` (lines 1560–1576).
- **Trend "since inception" start:** `'2020-07-01'` (lines 2148, 3334).
- **DPD thresholds:** Overdue = `dpd > 7 && dpd <= 90` ("DPD 8–90"); NPA = `dpd > 90`. Used everywhere.
- **Utilization thresholds:** buckets at 0 / 0.40 / 0.74; table cell highlight at `util > 0.74` (i.e. ≥75%) green, `util === 0` warn.
- **Dormancy thresholds:** 90–119 (approaching inactive), ≥120 (about to go inactive / headroom exclusion), ≥180 (reactivation), >365 (Workable_Over365 / out of target), >730 (deep dormant red in reactivation table).
- **IRR color thresholds (View G):** `wirr >= 20` green, `>= 18` amber, else red (line 2927).
- **Health-score thresholds:** ≥75 green, ≥50 amber, else red.
- **Week definition:** Monday→Sunday. `getWindow` (lines 1474–1485):
  - `mtd` → `[1st of month, today]`
  - `qtd` → `[1st of quarter, today]` (quarter = `Math.floor(m/3)*3`)
  - `cw` → Monday of this week → Sunday (`d-(dow===0?6:dow-1)`)
  - `nw` → next Monday → next Sunday
  - `cm` → `[1st of month, last day of month]`
  - `nm` → `[1st of next month, last day of next month]`
- **Currency formatting** `fmtCcy` (lines 1451–1460): `abs>=1e6` → `'$'+(v/1e6).toFixed(2)+'M'` (e.g. `$1.23M`); `abs>=1e3` → `'$'+(v/1e3).toFixed(1)+'K'`; else `'$'+v.toFixed(0)`. Long form: `$` + locale string, 0 decimals.
- **`fmtIRR`**: `v.toFixed(2)+'%'`, returns `'—'` for null/NaN/**0**.
- **`fmtPct`**: `(v*100).toFixed(1)+'%'` (input is fraction).
- **`fmtDate`**: `toLocaleDateString('en-US',{day:'2-digit',month:'short',year:'numeric'})` → e.g. "10 Jun 2026".
- **ID normalization** `normID` (line 1449): `String(v).replace(/,/g,'').replace(/\.0+$/,'').trim()` — strips commas and trailing `.0`.
- **Company matching between files is case-insensitive** on trimmed `toLowerCase()` of company name; account-ID matching uses `normID`.

---

## 1. DATA LAYER

### 1.1 Upload zones (6 files; all `.xlsx/.xls`; only the FIRST sheet is read, parsed with `XLSX.utils.sheet_to_json(ws,{defval:null})` and `cellDates:true`)

| Key | Zone label | Cadence | Required to launch? | Cache |
|---|---|---|---|---|
| `v1` | "View 1 — Accounts" (facility, OB, utilization, AM) | Weekly | **Yes** | none |
| `v2` | "View 2 — Invoices" (stages, DPD, origination, settlement) | Weekly | **Yes** | none |
| `mh` | "Master Handover" (Buyer_ID, AM, Account_Status, Broad) | Occasional | **Yes** (or cached) | localStorage `scf_mh` |
| `obhist` | "Historical OB (File 5)" — Jun 2020 – Apr 2026 | Cached | No | IndexedDB `scf_obhist` |
| `obcurr` | "Current OB File" — May 2026 onwards | Cached | No | IndexedDB `scf_obcurr` |
| `reactlist` | "Reactivation List" | Cached | No | localStorage `scf_reactlist` |

Launch gating: `disabled = !(loaded.v1 && loaded.v2 && (loaded.mh || !!G.mh))`. A date input "Today" sets `G.today` (defaults to system date); all windows/day-counts derive from it.

### 1.2 Columns referenced per file (exact strings)

**V1 (Accounts):** `importer_user_id`, `AM_Name`, `utilization_status`, `Last_Disbursed_Date`, `First_Disbursed_Date`, `Facility_Size`, `overdraft_limit`, `Outstanding_Balance`, `Signed-up IRR` (hyphen + space), `interest_rate`, `flat_discounting_fee`, `company`.

**Master Handover (MH):** `Buyer_ID`, `Buyer`, `AM`, `Broad_Account_Status`, `Account_Status`, `Team`, `Partner`, `Facility_Size`, `Overdraft_Limit`, `OB`, `Signed_up_IRR` (underscores), `Last_Disbursed_Date`, `First_Disbursed_Date`, `interest_rate`, `flat_discounting_fee`, `Annual_Maintenance_Fee`, `utilization_status` (used only in Unassigned-CP alert).

**V2 (Invoices):** `invoice_id`, `Buyer`, `name` (AM on the invoice), `Stage`, `Origination`, `Outstanding`, `dpd`, `disbursed_date`, `settlement_date`, `due_date_of_invoice`.
> ⚠ The actual V2 export has `Invoice ID` (not `invoice_id`) and `AM_Email` (no `name` column) — in the HTML both resolve to `undefined` and the AM falls back to the company→AM map. A port should map AM from the account join.

**OB files (obhist & obcurr, same schema):** `importer_user_id`, `ob_date`, `ob`.

**Reactivation list (fallback chains, first non-empty wins):**
- Company: `Company` → `company`
- Owner: `Assign To (Owner)` → `Assign_To` → `assign_to`
- Partner: `Partner` → `partner`
- Days dormant: `Days Dormant` → `Days_Since_Last_Disbursement` → `days`
- Facility: `Facility Size` → `Facility_Size` → `facility`

### 1.3 `processData()` — core entity build (lines 1492–1635)

**`G.podAccounts`** — iterate MH rows, join V1 by `normID(Buyer_ID) == normID(importer_user_id)`:
- `am = (v1['AM_Name']||'').trim() || (mh['AM']||'').trim()` — **V1 AM is primary, MH fallback**; row kept only if `POD_AMS.includes(am)`. **No partner/team filter — the pod is defined purely by the AM list.**
- `broad = (mh['Broad_Account_Status']||'').trim()`; `v1util = (v1['utilization_status']||'').trim()`.
- `lastDisb = toDate(v1.Last_Disbursed_Date || mh.Last_Disbursed_Date)` (same fallback for first disb); `daysSince = floor((today − lastDisb)/86400000)`.
- **Level-2 classification:**
  ```js
  if (broad !== 'Workable')                       level2 = 'NWA';
  else if (daysSince == null || daysSince > 365)  level2 = 'Workable_Over365';
  else level2 = v1util === 'active' ? 'Active Workable' : 'Suspended Workable';
  ```
- `facility = parseFloat(v1.Facility_Size || mh.Facility_Size || 0)`; `overdraft = parseFloat(v1.overdraft_limit || mh.Overdraft_Limit || 0)`; **`totalFac = facility + overdraft`**.
- `ob = v1.Outstanding_Balance != null ? parseFloat(v1.Outstanding_Balance) : parseFloat(mh.OB || 0)`.
- `irr = parseFloat(v1['Signed-up IRR'] || mh['Signed_up_IRR'] || 0)`.
- Also carries: `company = (mh.Buyer || v1.company).trim()`, `acctStatus = mh.Account_Status`, `team = mh.Team`.

**`G.v2pod`** — V2 invoices kept only if `(r['Buyer']||'').trim().toLowerCase()` is in the pod-company set. Fields: `stage = (r.Stage||'').trim().toLowerCase()`, `origination`, `outstanding`, `dpd` (parseFloat), `disbursed/settled/due` dates; `am = (r['name']||'').trim() || coToAM[buyer]`; `level2` copied from the matched pod account.

**`G.obDaily`** — `{ 'YYYY-MM-DD': { acctId: ob } }`, restricted to pod account IDs, hist rows `< 2026-05-01`, current rows `>= 2026-05-01`.

**`G.allCPAccounts`** (View G universe) — MH rows where `Team === 'CP'` **and** `Partner !== 'Direct'` (exact trimmed strings, all AMs). Adds `interest`, `txnFee` (`flat_discounting_fee`), `amf` (`Annual_Maintenance_Fee`), `utilPct = totalFac>0 ? Math.min(ob/totalFac,1) : 0`, `daysLastDisb`, `daysFirstDisb`.

**Peak/Avg OB** (both pod and CP universes): `peakOB = max(ob over all G.obDaily dates)`; `avgOB = mean(ob over days where ob > 0)`.

---

## 2. KPI & METRIC DEFINITIONS (per view, with formulas)

Throughout: `accts = filteredPodAccounts()` (global AM filter applied), `inTarget = accts where level2 ∈ {'Active Workable','Suspended Workable'}` (a.k.a. "WA" in most views).

### VIEW F — Executive Snapshot
- **Total OB** = `inTarget.reduce((s,a)=>s+a.ob,0)` — *only in-target WA accounts*.
- **Total Facility Size** = `inTarget.reduce((s,a)=>s+a.totalFac,0)` (facility + overdraft).
- **Portfolio Utilization %** = `totalFac>0 ? totalOB/totalFac : 0` (fmtPct).
- **Total Accounts** = `accts.length`; sub = `wa.length + ' Workable · ' + (NWA count) + ' NWA'` where `wa = broad==='Workable'`.
- **Account Health — 6 tiles** (count + OB + Facility each): `Active Workable`, `Suspended Workable`, `Workable >365d` (`level2==='Workable_Over365'`), `Non-Workable` (`level2==='NWA'`), `NW >365d` (NWA with `daysSince>365`), `NW ≤365d` (NWA with `daysSince<=365`). Tags: first two `IN TARGET` (green tag), Workable>365d `EXCL.`, NWA tiles `NWA`. Value colors: green / orange / grey×4; muted opacity for the last four tiles.
- **Weighted IRR**: `wirr(arr) = Σ(irr·ob)/Σ(ob)` (null if Σob ≤ 0). Three tiles: inTarget, Active-only, Suspended-only.
- **Risk**: `openInvs = v2pod where OPEN.has(stage)`; **Overdue OB** = Σ outstanding where `dpd>7 && dpd<=90`; **NPA OB** = Σ outstanding where `dpd>90`; sub = invoice counts; **Clean OB** = `max(0, totalWAOB − overdueOB − npaOB)`; **Clean %** = `cleanOB/totalWAOB`.

### VIEW A — Portfolio
- Hidden spans replicate F's Total OB / Facility / Util / counts.
- **Portfolio Quality summary tiles**: Clean OB / Overdue OB (DPD 8–90) / NPA OB (DPD >90), each with `% of portfolio` (`val/totalOB`) and invoice count. Donut: data in **$M** (`/1e6`), colors `rgba(16,185,129,.75)` / `rgba(249,115,22,.75)` / `rgba(239,68,68,.75)`, border `#16213e` width 3, tooltip `label: $X.XXM`, legend bottom.
- **PQ detail table**: rows = inTarget accounts, account category: `npa` if company appears in any open invoice with dpd>90, else `overdue` if dpd 8–90, else `clean`. Filter dropdown `all/clean/overdue/npa`. Sorted `b.ob - a.ob`. Util cell class: `util>0.74 → 'pos'`, `util===0 → 'warn'`, else `'acc'`. Badge classes: `badge-clean/badge-overdue/badge-npa`.
- **Weighted IRR tile** (`recomputeIRR_A`): user threshold input (default 0, step 1000): `wirr = Σ(irr·ob | ob>=thresh) / Σ(ob | ob>=thresh)` over inTarget; splits for Active and Suspended.
- **Targetable Portfolio — 4 panels**: 🟢 Active Workable / 🟠 Suspended Workable / ⏸ Workable >365d (muted, `NOT IN TARGET`) / ⛔ Non-Workable (muted, `NWA`). Each shows Accounts, Total Facility, OB, Utilization % (`ob/fac`).
- **OB Movement per AM**: uses **raw `G.obcurr`** (current OB file only). Per account: sort its rows by date; `start = first ob`, `end = last ob`. Excludes `level2==='NWA'` and `'Workable_Over365'`. Sums per AM. Bar chart: "OB Start" `rgba(148,163,184,.5)` vs "OB End" `rgba(245,158,11,.75)`, y-axis `$XM`.
- **Origination vs Repayment**: window MTD/QTD/Custom. Skips invoices where `EXCLUDED.has(stage)` or AM ∉ POD_AMS. **Originated** = Σ `origination` where `disbursed` in window. **Repaid** = Σ `max(0, origination − outstanding)` where `stage ∈ SETTLED ∪ PARTIAL` and `settled` in window. **Net** = Orig − Repaid. Grouped bar per AM + "Team Total": Originated `rgba(99,102,241,.75)`, Repaid `rgba(16,185,129,.65)`, Net colored per-bar `net>=0 ? 'rgba(245,158,11,.8)' : 'rgba(239,68,68,.8)'`; $M axis.
- **Collections Tracker**: AM chips (Portfolio + 5 AMs) filter independent of global filter.
  - **✅ Received (Principal Repaid)** = Σ `max(0, origination − outstanding)` over invoices with `SETTLED.has(stage)` and `settled ∈ [monthStart, today]`.
  - **⏳ To Receive** = Σ `outstanding` over invoices with `stage ∈ ['advanced','partial']` and `due` in selected window (Curr Wk/Next Wk/Curr Mo/Next Mo). Detail table groups by company: invoice count, total due, due-date range (min → max), sorted by total desc.
  - **⚠ Recovery Collections** = Σ `max(0, origination − outstanding)` where `stage ∈ ['overdue','npa']`.

### VIEW B — Team
- **AM Scorecards** (one card per AM; respects global filter). Per AM:
  - Active Workable: OB, Facility, Util% (`awOB/awFac`); same for Suspended Workable.
  - **MTD Activity:** Originated = Σ origination where `disbursed` in [monthStart, today]; Repaid = Σ `max(0, orig − outstanding)` where stage ∈ SETTLED∪PARTIAL and settled in month.
  - **Early Repayment Value** WTD/MTD/QTD = Σ **`origination`** (full origination, not principal repaid) over invoices with `SETTLED.has(stage) && settled && due && settled < due` and `settled` in the window. Week starts Monday.
  - **Weighted IRR with per-card threshold input**: inTarget accounts of the AM with `ob >= thresh`; `Σ(irr·ob)/Σ(ob)`.
- **AM Status Distribution** stacked bar: counts of Active Workable `rgba(16,185,129,.75)`, Suspended Workable `rgba(249,115,22,.65)`, Workable >365d `rgba(71,85,105,.5)`, Non-Workable `rgba(71,85,105,.3)` per AM (first names as labels).

### VIEW C — Health
- **Utilization Buckets** over inTarget WA: `util = totalFac>0 ? min(ob/totalFac, 1) : 0`. Buckets:
  - `Zero` (util ≤ 0, "0%", color `#475569`)
  - `Low` (≤ 0.4, "1% – 40%", `rgba(245,158,11,.8)`)
  - `Medium` (≤ 0.74, "41% – 74%", `rgba(99,102,241,.8)`)
  - `High` (else, "75% – 100%", `rgba(16,185,129,.8)`)
  4 clickable cards (count + Σob); donut of bucket OB in $M; clicking a card fills the detail table (sorted ob desc), default "All".
- **Weighted IRR by Utilization Bucket**: same buckets but only accounts with `ob > 0`; `wirr = Σ(irr·ob)/Σ(ob)` per bucket; horizontal bar; x-axis `%`.
- **Overdue (DPD 8–90) & NPA (DPD>90) sections**: for each set of open invoices:
  - **Total Stuck** = Σ outstanding (red), n invoices.
  - **No Payment Received** = Σ outstanding where `(origination − outstanding) <= 0` (orange).
  - **Partially Paid — Still Owed** = Σ outstanding where `(origination − outstanding) > 0` (accent), sub shows `$X.XK recovered`.
  - Detail table sorted: partial-paid first (row tint `rgba(99,102,241,.05)`), then DPD desc. Columns Company/AM/Invoice ID/Stage badge/Origination/Outstanding/Recovered (`max(0, orig−outstanding)`, green if >0 else `—`)/DPD (`>90` red else orange)/Payment badge (`Partial` indigo / `None` red).
- **Days Since Last Disbursement**: universe = `level2 ∈ {Active Workable, Suspended Workable, Workable_Over365}`. Bucket dropdown: `all, 0-30, 31-60, 61-90, 91-120, 121-150, 151-180, 180+`. Sorted days desc. Days cell: `>90` red, `>60` orange. Status badge shows `>365d` for Workable_Over365.

### VIEW D — Actions
- **Declining Accounts**: window MTD/QTD/Custom. Per company over v2pod (skip invoices whose `level2 ∈ {NWA, Workable_Over365}`): `orig` = Σ origination disbursed-in-window; `rep` = Σ `max(0, orig−outstanding)` settled-in-window (stage SETTLED∪PARTIAL). **Declining = rep > orig**; `net = orig − rep` (negative); sorted net asc. Chart: top 15, horizontal, values $K, bar color `net<0 ? red : green`.
- **High Opportunity**: window cw/nw/cm/nm. `due[company] = Σ outstanding` of `advanced/partial` invoices with due in window. Rows = inTarget WA: `headroom = max(0, totalFac − ob)`; **`opp = headroom + due`**; keep `opp > 0`, sort desc.
- **Early Repayment Tracking**: invoices `SETTLED.has(stage) && settled < due`, sorted by `(due−settled)` desc, capped at 300 rows.
- **Recovery Collections Detail**: open invoices with `dpd > 7` and `(origination − outstanding) > 0`, aggregated per company (count, Σorig, Σoutstanding, Σrecovered, maxDPD), sorted recovered desc; footer Total row; maxDPD `>90` red else orange.
- **Reactivation Focus**: pod accounts with `broad==='Workable' && v1util==='suspended' && daysSince>=180`, **sorted by `peakOB` desc**. Days cell: `>365` red, `>180` orange.
- **Unassigned CP Accounts**: raw MH rows with `Team==='CP' && utilization_status==='active' && First_Disbursed_Date truthy && !AM`. Columns Company/Partner/First Disbursed/OB (from MH `OB`).

### VIEW H — Account Pulse
Snapshot helpers: `key30/key90` = latest obDaily date key ≤ (today − 30/90 days); `peakOBDate[id]` = date of per-account max ob.
- **Due tiles (clickable)**: `dueByAcct[win][buyer_lower] += outstanding` for `advanced/partial` invoices with due in cw/cm/nm windows. Tile value = Σ; sub = distinct account count. Clicking toggles a row-highlight filter on the table.
- **Workable Accounts table**: universe = inTarget WA. Sort toggle: `fac` (totalFac desc, default) / `ob` / `util`. Slice toggle: Top 10/25/50 (default 50)/All/Bottom 10/25/50. Columns: # / Company / AM / Status badge / Total Facility / OB / Util % / **OB Chg 30d** (`ob − ob30ago`, green/red) / Due (Selected Window) / Last Disb / Peak OB / Peak OB Date / Avg OB.
- **About to Go Inactive**: `level2==='Active Workable' && daysSince>=120`, sorted daysSince desc. Tiles: count (orange), Σ OB at risk, Σ Facility at risk. Days cell `>180` red else orange.
- **Headroom Opportunity**: WA with `daysSince == null || daysSince < 120`; `headroom = max(0, totalFac − ob)` filtered `> 0`, sorted desc; `peakGap = max(0, peakOB − ob)` (orange if >0 else `—`).
- **Reactivation**: from `reactlist` rows, enriched with peakOB/avgOB/peakDate by case-insensitive company match. Global AM filter applies to **owner**. Sorted days dormant desc. Tiles (always unfiltered): Total Accounts; per-owner counts hardcoded to `'Ashitha Nair'`, `'Darshan Hublikar'`, `'Deepsayan Dam'`; **Avg Days Dormant**; Total Facility. Days cell: `>730` red, `>365` orange.
- **Repayment Tracker** (WTD/MTD toggle, default WTD): `repaid[company] = Σ max(0, orig − outstanding)` for SETTLED∪PARTIAL invoices settled in [start, today]. Rows = WA accounts having repayment, sorted desc. Tiles: Total Repaid; Accounts with Repayment; Avg.
- **Origination — Month to Date**: `orig[company] = Σ origination` of invoices disbursed in [monthStart, today]; rows = WA accounts with origination, sorted desc; tiles Total / count / Avg.
- **OB Drop** (30d & 90d side-by-side): WA where `obXago > ob`; `drop = obXago − ob`; `dropPct = drop/obXago`; sorted drop desc.

### VIEW P — Peak Analysis
- **OB Trend chart**: mode Portfolio Total / Per AM; window 3M/6M/12M/"Jul 2020". Data = Σ obDaily per date for filtered pod IDs (all pod accounts, WA+NWA), `/1e6`. >180 dates → downsampled to ~150 points. Portfolio line `#f59e0b` fill `rgba(245,158,11,.1)`; per-AM lines AM_COLORS. **Clicking a point sets peak mode to custom with that date.**
- **Peak date selection**: Auto = obDaily date with max Σ-total; Custom = latest obDaily date ≤ chosen date.
- **Peak Portfolio OB** = `dailyTotals[peakDate]`; **Today's** = Σ `a.ob` over **all** pod accounts (WA + NWA); **Net Movement** = today − peak (`▲/▼ pct`).
- **Per-account changes**: `change = obToday − obPeak`; `changePct = obPeak>0 ? change/obPeak : 1`; `status` = `'zero'` (obPeak>0 && obToday===0), `'declined'`, `'grew'`, `'unchanged'`.
- **zeroCategory** (priority): open NPA invoices → `'npa'`; open overdue → `'overdue'`; `level2 ∈ {NWA, Workable_Over365}` → `'nwa'`; `v1util==='active'` → `'active0'`; else `'suspended'`.
- **Tiles**: WA Peak/Today/Net; NWA Residual (clickable); NWA Structural Loss (clickable); Gross Growth; Gross Decline; 5 went-to-zero tiles (clickable filters).
- **Waterfall chart**: changes ≠ 0 and not NWA-residual, sorted |change| desc, **top 40** (header says "Top 30"). Horizontal bars $K: NWA grey ` ⊘`; WA red/green. Tooltip Change/Peak/Today/AM/Status.
- **Detail table** with 11 filter buttons (`all/wa/nwa_residual/nwa_structural/declined/grew/active0/npa/overdue/suspended/nwa`), sorted change asc.

### VIEW T — Team Tracker (all inputs persisted to localStorage)
- Key format: `tracker_{AM}_{acctId}_{field}`, field ∈ `status|comment|lastfu|nextfu`; referrals at `tracker_refs_{AM}`.
- **AM tabs** (5, default Nikhil Shetty) + Focus View / Manager Overview toggle.
- **Status enums**: Accounts `['No Update','In Progress','Escalated','Done','Waiting']`; Reactivation `['Not Started','Contacted','Interested','In Progress','Converted','Dead']`; Referrals `['Not Contacted','Meeting Scheduled','Meeting Done','In Pipeline','Converted','Dead']`.
- **7 Focus buckets** (collapsible; rows = account + status select + comment + last/next follow-up dates with overdue warning):
  1. 🔴 Overdue/NPA (open invoices dpd>7; NPA if any dpd>90)
  2. 🟡 Repayment Due — This Week (advanced/partial due in cw)
  3. 🟡 Repayment Due — Next Week (nw)
  4. 🟡 Repayment Due — Next Month (nm)
  5. 🟠 Net Negative MTD — Active WA where MTD `repaid > orig && repaid > 0`
  6. 🟣 Suspended — Still Repaying — Suspended WA with MTD repaid > 0
  7. ⚠ Approaching Inactive — WA with `daysSince ∈ [90,120)`
- **Reactivation Tracker**: reactlist rows where owner === selected AM.
- **Referral Tracker**: add/edit/delete rows; "Referring Client" dropdown = the AM's pod companies.
- **Manager Overview**: 3 summary tiles + per-AM cards (Overdue/NPA count, Net Negative MTD, Reactivation count, Referrals, Overdue follow-ups, Last update staleness flag >7d).

### VIEW G — CP Health — **NOT affected by global AM filter**
Universe = `G.allCPAccounts` (Team='CP', Partner≠'Direct', all AMs). Invoice risk uses **raw full `G.v2`** matched to all CP companies.
- **Summary tiles**: Total CP Accounts; Total CP OB; Total CP Facility; CP Utilization %.
- **Chart 1 OB & Utilization**: partners sorted by OB desc, **top 20**; horizontal bars Total Facility `rgba(148,163,184,.3)` + OB `rgba(245,158,11,.75)`, $M; partner labels `replace(/_/g,' ')`.
- **Chart 2 Risk**: per partner Σ outstanding of OPEN-stage invoices: NPA (dpd>90) red stacked on Overdue (7<dpd≤90) orange; only partners with risk >0, sorted desc; $K axis.
- **Chart 3 Weighted IRR**: partners with wirr>0 sorted desc; bar color `wirr>=20 → green`, `>=18 → amber`, else red; x-axis `%`.
- **Health Score /100** per account:
  ```js
  sUtil   = utilPct*25;                                   // 0–25 (utilPct = min(ob/totalFac,1))
  sClean  = overdueAccts.has(co) ? 0 : 25;                // any open invoice dpd>7 → 0
  sRecent = (daysLastDisb!=null && daysLastDisb<=30) ? 25 : 0;
  sActive = active90d.has(co) ? 25 : 0;                   // any invoice disbursed in last 90 days
  ```
- **Partner Health Scorecard**: expandable card per partner — header: account count, Avg score pill (≥75 green / ≥50 amber / red), NPA $ red, OVR $ orange, Σob OB · util% · IRR. Body table per account sorted healthScore desc.

### Portfolio Report ("↓ Portfolio Report" header button)
Printable light-theme page (unfiltered, full pod): headline Peak OB / Today OB (all pod, WA+NWA) / Change from Peak / Workable OB Today; OB Movement table (vs-30d/90d/MTD/QTD/Peak × Total Prev/Today/Change/WA Change/NWA Change); "Where Did the OB Go?" top 10 by 30-day drop; Team Breakdown (WA only) per the 5 AMs. Colors: pos `#059669`, neg `#dc2626`, accent `#f59e0b` on white.

---

## 3. VISUAL COMPONENT INVENTORY — see §2 per view; render order

Header (sticky): brand "CP POD · SCF", date pill, 9 nav buttons (F/A/B/C/D/H/T/P/G), global AM filter (All + 5 AMs), "↓ Portfolio Report", "↑ Re-upload".

| View | Components |
|---|---|
| F | 4 xl KPI tiles · 6 health tiles · 3 WIRR tiles · 3 risk tiles |
| A | PQ tiles + donut + filterable table · IRR threshold tile · 4 targetable panels · OB movement grouped bar · OVR grouped bar + window toggle · Collections (chips + tiles + window toggle + collapsible table) |
| B | AM scorecard grid · stacked status bar |
| C | 4 clickable util bucket cards + donut + drill table · WIRR-by-bucket hbar · Overdue section (3 tiles + table) · NPA section · DSLD dropdown + table |
| D | Declining (toggle + hbar top 15 + table) · High Opportunity (toggle + table) · Early Repayment table · Recovery detail table + totals · Reactivation Focus table · Unassigned CP alert table |
| H | due tiles (clickable) + sort/slice toggles + 13-col workable table · about-to-go-inactive · headroom · reactivation · repayment tracker (WTD/MTD) · origination MTD · OB drop 30/90 |
| P | trend line (click-to-peak) + toggles · peak tiles (clickable) · waterfall hbar · 11-filter detail table |
| T | AM tabs · 7 editable buckets · reactivation tracker · referral tracker · manager overview |
| G | 4 KPI tiles · OB/util by partner hbar · risk by partner stacked hbar · WIRR by partner hbar · partner health scorecards |

**Chart defaults**: legend labels `#94a3b8` IBM Plex Sans 11; tooltip bg `#16213e`, border `#1e3a5f`; axis ticks `#94a3b8` (y Mono); grid `rgba(30,58,95,.3)`. Donut borders `#16213e` w3. Currency axes `$XM`/`$XK`.

**Recurring conditional formatting:** Util% cell → `>0.74` green, `===0` orange, else amber. DPD → `>90` red else orange. Status badges: active green, suspended orange, nwa/excluded grey, npa red, overdue orange, clean green, partial indigo `#818cf8`, early green.

---

## 4. FILTER & INTERACTION LOGIC

1. **Global AM filter** (header): options `all` + 5 POD_AMS. Re-renders **F, A, B, C, D, H, P** (NOT G, NOT T). In View H Reactivation it filters the **owner** column.
2. **Tab navigation**: H, P, T re-render on every show; F/A/B/C/D/G render at launch and on global-AM change.
3. View-specific: PQ filter select; IRR threshold inputs (A + per-AM in B); OVR/Declining window toggles (MTD/QTD/Custom + date inputs); Collections AM chips + window toggle; util bucket card clicks; DSLD bucket dropdown; H sort/slice toggles + due-tile click-to-highlight; repayment WTD/MTD; P trend mode/window toggles + chart-click-to-peak + auto/custom peak + 11 filter buttons + 7 clickable tiles; T AM tabs + focus/overview + autosaving inputs.
4. Table sorting is fixed (not click-to-sort).
5. No search functionality exists.

---

## 5. THEME

```css
--bg-base:#1a1a2e;   --bg-card:#16213e;  --bg-card-hover:#1e2d4a;  --bg-input:#0f1729;
--accent:#f59e0b;    --accent-dim:#b45309;
--text-primary:#f1f5f9; --text-secondary:#94a3b8; --text-muted:#475569;
--positive:#10b981;  --negative:#ef4444;  --warning:#f97316;
--border:#1e3a5f;    --border-subtle:#162032;
--font-sans:'IBM Plex Sans',sans-serif;  --font-mono:'IBM Plex Mono',monospace;
```
`html{font-size:14px}`; numbers always mono; section titles 0.68rem uppercase letterspaced; sticky header; `.view` max-width 1440px; card grids cols-2..6 responsive; tables sticky uppercase headers, max-height 420/560px scroll.

---

## Porting gotchas
- "Total OB / Facility / Util" on F and A are **in-target only** (Active + Suspended Workable); View P "Today's OB" and the Portfolio Report use **all** pod accounts.
- Repaid is always `max(0, Origination − Outstanding)`, except Early Repayment Value (View B) which sums full **Origination**.
- `fmtIRR` hides exact-zero IRRs as `—`.
- View B early-repayment uses only `SETTLED` stages; OVR/Declining/Repayment Tracker include `PARTIAL` too.
- The `EXCLUDED` stage set is enforced only in `renderOVR`.
- View P waterfall header says "Top 30" but slices **40**.
- View G ignores the global AM filter and re-scans raw `G.v2`.
- OB Movement (A4) reads raw `G.obcurr` without the May-2026 cutoff.
