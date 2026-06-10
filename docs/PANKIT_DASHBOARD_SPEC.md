# Phase 1 Spec — Pankit's Original Dashboard ("75% Utilization Engine")

**Source:** `C:\Users\PratikPandey\Downloads\Pankit Dashboard code` (741 lines; single-file React component, default export `Dashboard`)
**Stack:** React (`useState`, `useMemo`) + Recharts. No network calls — all data embedded in a `const RAW = {...};` literal (54k chars). `ScatterChart/Scatter` imported but never used.

---

## 1. KPI & METRIC DEFINITIONS

### 1.1 Per-account fields — ALL PRECOMPUTED (embedded literals, not computed in JS)

128 `RAW.accounts` objects. Implied upstream formulas (verified against data):

| Field | Meaning / implied formula | Example (Style Source LLC, id 480585) |
|---|---|---|
| `id` | Account ID (int) | `480585` |
| `name` | Account name | `"Style Source LLC"` |
| `am` | Account Manager | `"Sonal Mishra"` |
| `facility` | Facility/limit ($, int) | `250000` |
| `ob` | Current outstanding balance | `156168.89` |
| `ob_30d` | OB 30 days ago | `227077.46` |
| `ob_60d` | OB 60 days ago | `0.0` |
| `ob_90d` | OB 90 days ago — **0.0 for every row** | `0.0` |
| `repayments` | June repayments ($) | `0.0` |
| `net_ob` | `ob - repayments` | `156168.89` |
| `utilization` | `ob / facility * 100` (2dp) — **facility only, NO overdraft** | `62.47` |
| `target_ob` | `facility * 0.75` | `187500.0` |
| `gap_to_75` | `max(0, target_ob - ob)` | `31331.11` |
| `status` | Workability status (see §2.4) | `"Workable - Active"` |
| `last_disbursed` | `YYYY-MM-DD` | `"2026-06-01"` |
| `days_since_last` | Days since last_disbursed (vs 2026-06-05) | `4` |
| `months_since_last` | `days_since_last / ~30.4` (1dp) | `0.1` |
| `ob_dent_30d` | `ob_30d - ob` (positive = OB shrank) | `70908.57` |
| `ob_dent_90d` | `ob_90d - ob` → always `≤ 0` since ob_90d=0 | `-156168.89` |
| `ob_dent_30d_pct` | `ob_dent_30d / ob_30d * 100`, **clamped to ±100**; inconsistent when `ob_30d == 0` | `31.23` |

### 1.2 JS-computed portfolio KPIs — `kpi` useMemo (over **unfiltered** ACCOUNTS)

```js
const workable = ACCOUNTS.filter(a => a.status?.startsWith("Workable"));
const active = ACCOUNTS.filter(a => a.status === "Workable - Active");
const inactive = ACCOUNTS.filter(a => a.status?.includes("Inactive"));
const zeroOB = ACCOUNTS.filter(a => (a.ob || 0) < 1);
const totalFacility = Σ facility; const totalOB = Σ ob;
const totalRepay = REPAYMENTS_AM.reduce(...); // from repayments_by_am, NOT account rows
const utilPct = totalOB / totalFacility * 100;
const activeIn12m = inactive.filter(a => (a.days_since_last || 999) <= 365);
```
Verification values: workable=126, active=103, inactive=6, zeroOB=15, totalFacility=$53.17M, totalOB=$43.65M, totalRepay=$2.54M, utilPct≈82.1%, activeIn12m=5, Net OB = totalOB − totalRepay = $41.11M.

### 1.3 AM performance — `amPerf` useMemo (unfiltered)

AM order hardcoded: `["Sonal Mishra", "Pejush Hal", "Kaustav Das", "Pankit Shah"]`.
Per AM: accounts count, Σ facility, Σ ob, **avgUtil = simple mean of per-account utilization (facility>0 only, NOT OB-weighted)**, zeroOB count (`ob<1`), inactive count (`status.includes("Inactive")`), repay from `REPAYMENTS_AM`, orig from `ORIG_AM`.
Verification: Sonal 38 accts / fac 9,750,049 / OB 7,239,812.94 / repay 560,888.69 / orig 141,726,939; Pejush 35 / 18,375,000 / 15,855,838.66 / 1,286,793.80 / 177,229,815; Kaustav 50 / 14,445,001 / 11,162,240.22 / 695,421.56 / 119,921,864; Pankit Shah 5 / 10,600,000 / 9,394,158.45 / repay 0 (absent) / 49,837,757.

### 1.4 Per-tab computed metrics

- **Tab 1:** counts/sums over `filtered` (Showing, Active, Inactive, Total Facility, Total OB).
- **Tab 2:** `d = filtered.filter(facility > 0)`; `above75` (`util >= 75`), `below50` (`<50 && >0`), `below25` (`<25 && >0`), avgUtil (simple mean); histogram buckets: `===0`, `>0&&<25`, `>=25&&<50`, `>=50&&<75`, `>=75&&<=100`, `>100`.
- **Tab 3:** `zeroRows = filtered.filter(ob < 1)`; `highFacilityZero` (`facility >= 500000`); `recentlyActive` (`ob_30d > 0 || days_since_last <= 90`); dormant facility = Σ facility.
- **Tab 4:** `inact12 = ACCOUNTS.filter((status includes "Inactive" OR "Temporarily suspended") && days_since_last <= 365 && amFilter match)`. **Ignores statusFilter.**
- **Tab 5:** `withRepay = filtered.filter(repayments > 0)`; totalRepay = Σ over that set.
- **Tab 6:** `valid = filtered.filter(ob>0 || ob_30d>0)`; `reduced30 = ob_dent_30d > 0`; `reduced90 = ob_dent_90d > 0` (always 0); `flagged = pct > 25 || dent > 100000`.
- **Tab 8:** `opps = filtered.filter(gap_to_75 > 0 && facility > 0 && status.startsWith("Workable"))`; totalGap; avg utilization (simple mean over opps).
- **Tab 9 table 4:** per hardcoded AM: count of `gap_to_75>0 && status.startsWith("Workable")`, Σ gap, avgUtil over facility>0 accounts.

### 1.5 Number formatter

```js
const fmt = (n, type="$") => {
  if (n == null || isNaN(n)) return "-";
  if (type === "$") {
    if (Math.abs(n) >= 1e6) return `$${(n/1e6).toFixed(2)}M`;
    if (Math.abs(n) >= 1e3) return `$${(n/1e3).toFixed(0)}K`;
    return `$${n.toFixed(0)}`;
  }
  if (type === "%") return `${n.toFixed(1)}%`;
  return n.toFixed(2);
};
```

---

## 2. DATA LAYER

### 2.1 `RAW.accounts` — 128 objects (header claims 215 — hardcoded string)

Distribution: Kaustav Das 50, Sonal Mishra 38, Pejush Hal 35, Pankit Shah 5. Status counts: Workable - Active 103, Workable - Temporarily suspended 17, Workable - Inactive (AM) 5, Workable - Inactive (BDM) 1, Non-Workable 2.

### 2.2 `RAW.portfolio_ob_trend` — 24 points, raw dollars, irregular dates 2026-04-01 → 2026-06-05
First: `{"date":"2026-04-01","ob":39347471.8}`; last: `{"date":"2026-06-05","ob":44307771.5}`. Transformed: `date → "MM-DD"`, `ob → $M 3dp`.

### 2.3 `repayments_by_am` (3 rows — **no Pankit Shah**) / `originations_by_am` (4 rows)
```json
"repayments_by_am":[{"am":"Kaustav Das","repayments":695421.56},{"am":"Pejush Hal","repayments":1286793.8},{"am":"Sonal Mishra","repayments":560888.69}]
"originations_by_am":[{"am":"Kaustav Das","originations":119921864},{"am":"Pankit Shah","originations":49837757},{"am":"Pejush Hal","originations":177229815},{"am":"Sonal Mishra","originations":141726939}]
"generated_at":"2026-06-05"
```

### 2.4 Hardcoded lookups & thresholds

```js
const AM_COLORS = { "Kaustav Das": "#3b82f6", "Pejush Hal": "#8b5cf6", "Sonal Mishra": "#f59e0b", "Pankit Shah": "#10b981" };
const STATUS_MAP = {
  "Workable - Active":                 { label: "Active",         color: "#10b981", bg: "#d1fae5" },
  "Workable - Temporarily suspended":  { label: "Suspended",      color: "#f59e0b", bg: "#fef3c7" },
  "Workable - Inactive (AM)":          { label: "Inactive (AM)",  color: "#ef4444", bg: "#fee2e2" },
  "Workable - Inactive (BDM)":         { label: "Inactive (BDM)", color: "#f97316", bg: "#ffedd5" },
  "Non-Workable":                      { label: "Non-Workable",   color: "#6b7280", bg: "#f3f4f6" },
};
const ALL_AMS = ["All", "Sonal Mishra", "Pejush Hal", "Kaustav Das", "Pankit Shah"];
```
Thresholds: 75% target; util badge bands 75/50/0; histogram edges 0/25/50/75/100; zero-OB `ob < 1`; high facility ≥ $500K; recently-active ≤ 90 days or `ob_30d > 0`; reactivation ≤ 365 days; dent flags `pct > 25` or `> $100K`; low-util screen `< 30%`; not-funded `>= 90 days` (>90 amber, >180 red); ReferenceLines `y=42` "Current" (tab 0; stale), `y=44.31` "Today $44.3M" (tab 6), `y=75` "75% Target"; Y-domains `[35,46]` (tab 0), `[35,47]` (tab 6). Header text: `"Data as of Jun 5, 2026 · 215 Accounts"`.

---

## 3. VISUAL COMPONENTS INVENTORY (render order)

### 3.0 Chrome
1. **Header** — gradient `linear-gradient(90deg, #0f172a 0%, #1e293b 100%)`, border-bottom `#334155`. Eyebrow `"Drip Capital · BD Pod"` (11px `#3b82f6` 700 uppercase) over title `"75% Utilization Engine"` (22px 800 `#f8fafc`). Right: `"Data as of Jun 5, 2026 · 215 Accounts"` (12px `#64748b`).
2. **Tab bar** — 10 buttons: `🏠 Executive, 📋 Account Inventory, 📊 Utilization, ⭕ Zero OB, 💤 Workable Inactive, 💳 Repayments, 📉 OB Dent Tracker, 👤 AM Performance, 🎯 75% Engine, 🔥 Opportunity Views`. Active: `#38bdf8` + 2px bottom border; inactive `#64748b`.
3. **Persistent filter bar** — `AM:` + 5 pills (selected bg = AM color, or `#334155` for All); `Status:` + 5 pills (`All` + 4 statuses via STATUS_MAP labels; **"Workable - Inactive (BDM)" not selectable**).

### 3.1 Shared primitives
- **KpiCard**(label, value, sub, color=#38bdf8) — gradient bg `135deg #0f172a→#1e293b`, border `#334155`, radius 12, minWidth 160; label 11px `#64748b` uppercase; value 24px/700 'DM Mono'; sub 12px `#94a3b8`.
- **SortableTable**(cols, rows, maxRows=999, defaultSort, defaultDir="desc") — every header clickable; same key toggles asc/desc, new key sets desc; numeric vs localeCompare; active header `#38bdf8` with ↑/↓.
- **UtilBadge**(u) — `u>=75` green `#d1fae5/#065f46`; `>=50` amber `#fef3c7/#92400e`; `>0` red `#fee2e2/#991b1b`; `0` gray `#f3f4f6/#374151`.
- **StatusBadge** — from STATUS_MAP.
- **AmDot** — 8px dot AM_COLORS + name.
- **CustomTooltip** — dark panel `#0f172a`/`#334155`; `$X.XXXM` when series is "ob"/contains "OB".

### 3.2 Tab 0 — 🏠 Executive (**unfiltered**; ignores both filters)
1. **10 KpiCards**: Total Workable (#38bdf8), Active (#10b981), Inactive (#f59e0b), Zero-OB (#ef4444), Total Facility (#a78bfa), Total OB (#38bdf8), Portfolio Utilization (green ≥75 else amber), Net OB (#64748b), June Repayments (#10b981, sub "Sonal not in data" — stale), Inactive w/ Last 12 Mo (#fb923c, sub "Reactivation targets").
2. **LineChart "Portfolio OB Trend (Apr–Jun 2026)"** — trendData; Y domain [35,46] ticks `$XM`; grid dash 3 3 `#1e293b`; ReferenceLine y=42 dashed "Current"; line `#38bdf8` w2 no dots.
3. **BarChart "June Repayments & Total Originations by AM"** — X first names; dual Y axes; single Bar `repay` (per-Cell AM colors). **No originations bar despite title.**
4. **SortableTable "AM Portfolio Snapshot"** — amPerf, defaultSort "ob": AM (AmDot), Accounts, Total Facility, Total OB, Avg Util % (UtilBadge), Zero OB, Inactive, June Repayments.

### 3.3 Tab 1 — 📋 Account Inventory (`filtered`)
5 KpiCards (Showing/Active/Inactive/Total Facility/Total OB) + SortableTable defaultSort "facility": Account Name, AM, Facility, OB, June Repayments, Net OB, Utilization (UtilBadge), Status (StatusBadge).

### 3.4 Tab 2 — 📊 Utilization (`filtered`, facility>0)
4 KpiCards (Avg Util; ≥75%; <50%; <25%) · **BarChart "Utilization Distribution"** 6 buckets, Cell colors `["#ef4444","#f97316","#f59e0b","#3b82f6","#10b981","#8b5cf6"]` · **BarChart "AM-wise Avg Utilization"** (first names, AM colors, ReferenceLine y=75 green dashed "75% Target") · SortableTable defaultSort "utilization".

### 3.5 Tab 3 — ⭕ Zero OB (`filtered`, ob<1)
4 KpiCards (Zero-OB; High Facility ≥$500K "Priority reactivation"; Recently Active <90d; Total Dormant Facility) · 2 legend chips (red `#fef2f2/#991b1b`, amber `#fffbeb/#92400e`) · SortableTable defaultSort "facility": OB renders literal red `$0`; Days Since amber if ≤90; OB 30d Ago amber if >0 else "-".

### 3.6 Tab 4 — 💤 Workable Inactive (`inact12`; amFilter only)
3 KpiCards (count "Primary reactivation pipeline"; Σ facility; Σ gap_to_75) · SortableTable defaultSort "facility": Account, AM, Facility, Last Disbursed, Months Since (`X mo`), Gap to 75% (blue), Status.

### 3.7 Tab 5 — 💳 Repayments (`filtered`, repayments>0)
KpiCards: Total June Repayments (green), Accounts with Repayments (blue), + one card per repayments_by_am row (filtered by amFilter) "{FirstName} Repayments" in AM color · SortableTable defaultSort "repayments": Account, AM, Beginning OB (30d), Repayments (green 600), Current OB, Net OB.

### 3.8 Tab 6 — 📉 OB Dent Tracker (`valid` = filtered with ob>0 or ob_30d>0)
5 KpiCards (Total Facility shown; OB Reduced in 30d; OB Reduced in 90d (always 0); Total 30d OB Reduction; Recovery Candidates ">25% dent or >$100K") · LineChart "Portfolio OB Movement — 180 Day Window ($M)" Y [35,47], ReferenceLine y=44.31 green "Today $44.3M", activeDot r5 · flag chip · SortableTable defaultSort "ob_dent_30d": **30d Dent** render `v>0` green `+{fmt} ▼`, `v<0` red `{fmt} ▲`, 0 gray; **Dent %** amber+700 when |v|>25.

### 3.9 Tab 7 — 👤 AM Performance (unfiltered amPerf)
2×2 grid of AM cards (border = AM color at 25% alpha; 8 mini-tiles: Accounts/Facility/OB/Avg Util/Zero OB/Inactive/June Repay/Total Orig.) · SortableTable "AM Comparison Table" defaultSort "ob".

### 3.10 Tab 8 — 🎯 75% Engine (`opps`)
3 KpiCards (Opportunity Accounts "Below 75% utilization"; Total Gap "Potential incremental OB"; Avg Current Utilization) · formula chip `💡 Formula: Gap to 75% = (Facility × 75%) - Current OB` (bg `#dbeafe` text `#1e40af`) · SortableTable defaultSort "gap_to_75": Account, AM, Facility, Current OB, Target OB (75%), Utilization, Gap to 75% (blue 700), Last Funded, Status.

### 3.11 Tab 9 — 🔥 Opportunity Views (4 stacked panels)
1. **🏆 Top 20 Utilization Opportunities** — `ACCOUNTS.filter(gap>0 && status.startsWith("Workable"))` — **ignores all filters**; maxRows 20.
2. **⚠️ Accounts Not Funded in 90+ Days** — `days_since_last >= 90`, amFilter only; Days render >180 red / >90 amber + " days".
3. **🎯 High Facility / Low Utilization** — `facility >= 500000 && utilization < 30`, amFilter only.
4. **📊 AM Opportunity Ranking** — per hardcoded AM (ignores all filters); defaultSort "totalGap".

**Clickability:** only tab buttons, filter pills, and table headers (sort). Rows/cards/charts not clickable.

---

## 4. FILTER & INTERACTION LOGIC

| State | Default | Options | Affects |
|---|---|---|---|
| `tab` | 0 | 0–9 | content area |
| `amFilter` | "All" | All + 4 AMs | tabs 1,2,3,5,6,8; tab 4; tab 9 tables 2&3; tab 5 AM cards. NOT tabs 0, 7, tab 9 tables 1&4 |
| `statusFilter` | "All" | All + 4 statuses (BDM missing) | `filtered` only → tabs 1,2,3,5,6,8. NOT tabs 0,4,7,9 |

Leader vs AM view: "All" = leader; AM pill narrows account-level tabs. Executive & AM Performance always leader-level. Filter state persists across tab switches. No search, no pagination (only Top-20 cap).

---

## 5. THEME

Fonts: body `'DM Sans', system-ui`; KPI values `'DM Mono', monospace`. Page bg `#020817`; panels `#0f172a` border `#1e293b` radius 12; surfaces `#1e293b`; borders `#334155`; text `#e2e8f0`/`#f8fafc`/muted `#94a3b8`/`#64748b`; accent `#38bdf8`; semantic green `#10b981`, amber `#f59e0b`, red `#ef4444`, orange `#f97316`/`#fb923c`, purple `#a78bfa`/`#8b5cf6`, blue `#3b82f6`. Charts: grid dash 3 3 `#1e293b`; ticks `#64748b`; bar radius 4.

---

## ANOMALIES / PORT-FIDELITY NOTES

1. Header "215 Accounts" hardcoded; RAW has 128. (215 = all accounts of the 4 AMs in View 1 with no partner filter — verified against the Excel.)
2. "Sonal not in data" sub-text is stale — Pankit Shah is the one missing from repayments_by_am.
3. "OB Reduced in 90d" KPI structurally always 0.
4. Tab 0 bar chart title promises Originations but only plots Repayments.
5. `ob_dent_30d_pct` upstream-clamped ±100, inconsistent at ob_30d=0.
6. Status filter cannot select "Workable - Inactive (BDM)" (1 account: Sri Riya Exports, id 368797).
7. Tab 0 ReferenceLine y=42 stale vs latest trend 44.308.
8. `kpi`/`amPerf` memos intentionally static (deps `[]`).
9. **Embedded OB values differ from the Jun-5 master extract** (e.g. DAXX: embedded 2,245,527.8 vs master 1,996,446.02) — RAW came from a different snapshot. The unified app derives live from the Excel files instead (agreed approach, see README).
