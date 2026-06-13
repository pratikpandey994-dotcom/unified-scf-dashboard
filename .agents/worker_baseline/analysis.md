# Baseline Verification and Codebase Analysis

## 1. Verification Outputs

### python _verify_metrics.py
Running `python _verify_metrics.py` succeeds with all assertions passing.
**Output:**
```
2026-06-13 16:24:07.598 WARNING streamlit.runtime.caching.cache_data_api: No runtime found, using MemoryCacheStorageManager
2026-06-13 16:24:07.600 WARNING streamlit.runtime.caching.cache_data_api: No runtime found, using MemoryCacheStorageManager
2026-06-13 16:24:07.611 WARNING streamlit.runtime.caching.cache_data_api: No runtime found, using MemoryCacheStorageManager
2026-06-13 16:24:19.381 WARNING streamlit.runtime.caching.cache_data_api: No runtime found, using MemoryCacheStorageManager
accounts_all: 647 | invoices: 36975 | ob pivot: (2163, 647)
Team Nikhil: 255 (expect 255) | per-AM: {'Nikhil Shetty': 87, 'Ashitha Nair': 54, 'Deepsayan Dam': 48, 'Darshan Hublikar': 41, 'Asif Ali': 25}
Team Pankit: 193 (expect 193) | per-AM: {'Kaustav Das': 66, 'Pejush Hal': 62, 'Sonal Mishra': 47, 'Pankit Shah': 18}
CP universe: 313 (expect 313) | partners: 43 (expect 43)
Nikhil in-target: 154 | Total OB: 34.17M | Fac: 56.10M | WIRR: 18.76
Nikhil risk: {'overdue_ob': np.float64(2994547.3), 'overdue_count': 141, 'npa_ob': np.float64(4124143.3), 'npa_count': 183, 'clean_ob': np.float64(27052316.4), 'clean_pct': np.float64(0.8)}
Pankit KPIs: OB 43.25M | Fac 71.42M | util 60.6% | zeroOB 76 | MTD repay 5.529M
recon today: 94.1M vs master OB 81.1M
ASSERTIONS OK
```

### python _verify_app.py
Running `python _verify_app.py` fails on the theme toggling step.
**Output:**
```
OK   default-load (Team Nikhil, all 10 tabs render)
Traceback (most recent call last):
  File "C:\Users\PratikPandey\unified-scf-dashboard\_verify_app.py", line 29, in <module>
    at.radio(key="theme_mode").set_value("Dark")
    ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "C:\Users\PratikPandey\scoop\apps\python\current\Lib\site-packages\streamlit\testing\v1\element_tree.py", line 263, in __call__
    raise KeyError(key)
KeyError: 'theme_mode'
```
**Reason for Failure:**
The test script `_verify_app.py` assumes a sidebar/main-page radio widget exists with the key `"theme_mode"` to test theme switching. However, `app.py` only references `theme_mode` by retrieving it from session state:
```python
theme_mode = st.session_state.get("theme_mode", "Light")
inject_visual_system(theme_mode)
```
There is no widget defined in `app.py` with `key="theme_mode"`, causing the `AppTest` to throw a `KeyError`.

---

## 2. Analysis of Tab Setup

Tabs are dynamically set up based on the active team selection radio button (`team_name = st.radio("View", list(TEAMS.keys()), ...)`).

* **Team Nikhil** renders 10 tabs (defined in `app.py` lines 161–164):
  - Overview
  - Portfolio Quality
  - Team
  - Risk & Health
  - Collections
  - Account Pulse
  - Peak Movement
  - CP Health
  - Tracker
  - Insights
* **Team Pankit (Direct sales)** renders 11 tabs (defined in `app.py` lines 188–192):
  - Overview
  - Inventory
  - Utilization
  - Zero OB
  - Workable Inactive
  - Repayments
  - OB Dent
  - AM Performance
  - 75% Engine
  - Opportunity
  - Insights

### Tab Styling Configuration
Tab styling is configured via injected CSS within `ui_helpers.py` (`_CSS_TEMPLATE` / `inject_visual_system`):
* **Tab Layout & Wrapping**: Since the number of tabs is large (10 to 11 tabs), custom styling is applied to `.stTabs [data-baseweb="tab-list"]` with `flex-wrap: wrap` and `overflow-x: visible !important`. The scroll buttons are hidden with `button[data-testid="stTabScrollButton"] { display: none !important; }`. This prevents tabs from getting cut off or hidden behind scroll arrows.
* **Tab Styling**: Tabs are styled with custom spacing (`padding: 0.55rem 1.1rem !important`), font sizes (`font-size: 0.82rem !important`), and colors mapping to CSS variables (e.g. `var(--scf-muted)`).
* **Selected Tab**: The active/selected tab has `font-weight: 700 !important`, changes to heading color, and shows a bottom border `2px solid var(--scf-accent) !important`.
* **Highlights/Borders**: The default baseweb tab highlight and border are disabled with `display: none !important`.

---

## 3. Analysis of DataFrame Rendering

Dataframes are rendered in the application using two methods:

### Method A: `show_table` Helper Function
The primary method is the custom `show_table` helper in `ui_helpers.py`:
```python
def show_table(frame: pd.DataFrame, columns: list[str] | None = None, height: int | None = None) -> None:
    if columns is not None:
        columns = [c for c in columns if c in frame.columns]
        frame = frame[columns]
    kwargs = {"height": height} if height is not None else {}
    st.dataframe(frame, width="stretch", hide_index=True, column_config=data_config(), **kwargs)
```
This function standardizes rendering by:
* Selecting specific columns if specified.
* Applying standard formats via `data_config()`, such as:
  - Currency column formatting (`$ %.0f`) for `facility`, `overdraft`, `ob`, `peak_ob`, etc.
  - Percentage formatting (`%.1f%%`) for `utilization_pct`, `ob_dent_30d_pct_display`, etc.
  - Date formatters for `last_disbursed`, `first_disbursed`, etc.
  - Visual progress bar representation (`ProgressColumn` formatted as `%d`, min=0, max=100) for `health_score`.
* Automatically setting `width="stretch"` and `hide_index=True`.

### Method B: Direct `st.dataframe` or `st.data_editor` Calls
Some views directly invoke Streamlit dataframe components instead of using `show_table`:

* **`views_nikhil.py`**:
  - `st.dataframe(decl.reset_index(names="account_id"), use_container_width=True, hide_index=True)`
  - `st.dataframe(early[["Buyer", "am", "Invoice ID", ...]], height=380, use_container_width=True, hide_index=True)`
  - `st.dataframe(agg, use_container_width=True, hide_index=True)`
  - `st.dataframe(unassigned[["company", "partner", ...]], height=240, use_container_width=True, hide_index=True)`
  - `st.dataframe(rep_table[["company", "am", "repaid", "ob"]], use_container_width=True, hide_index=True)`
  - `st.dataframe(orig_table[["company", "am", ...]], use_container_width=True, hide_index=True)`
  - `st.dataframe(drop.sort_values(...)[["company", "am", ...]], height=280, use_container_width=True, hide_index=True)`
  - `st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)`
  - `st.dataframe(detail, use_container_width=True, hide_index=True)`
  - `st.data_editor(st.session_state["tracker_df"], num_rows="dynamic", use_container_width=True, ...)`
* **`views_pankit.py`**:
  - `st.dataframe(display, use_container_width=True, hide_index=True, column_config={...})`
  - `st.dataframe(pd.DataFrame(ranking).sort_values("total_gap", ...), use_container_width=True, hide_index=True, ...)`
  - `st.dataframe(pd.DataFrame(pivoted.to_records()), use_container_width=True, hide_index=True, ...)`
* **`views_referral.py`**:
  - `st.data_editor(st.session_state["referral_data"], num_rows="dynamic", use_container_width=True, hide_index=True, ...)`

---

## 4. Analysis of Styling Configuration

### Border Configurations
Dataframe borders are configured inside `_CSS_TEMPLATE` in `ui_helpers.py` targeting `[data-testid="stDataFrame"]`:
```css
/* ── DataFrame ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--scf-border-soft) !important;
  border-radius: 10px !important;
  overflow: hidden !important;
  box-shadow: 0 1px 3px rgba(15,31,61,0.04) !important;
}
```
This applies a subtle border (`var(--scf-border-soft)`) and wraps the dataframe inside a rounded-corner container (`border-radius: 10px`) with a soft drop shadow.

### Alternating Rows
No custom CSS rule for alternating rows (such as styling odd/even rows or custom background colors for specific row indexes) is defined in `ui_helpers.py` or the view files. The alternating row color scheme comes from the default Glide Data Grid styling embedded in Streamlit's native `st.dataframe` or `st.data_editor` components, adapting automatically to the Streamlit theme defined in `.streamlit/config.toml` (which sets text and background colors).

### Theme Styling Setup
* **Global Configuration**: `.streamlit/config.toml` specifies a default light theme:
  - `primaryColor = "#0d9488"`
  - `backgroundColor = "#ffffff"`
  - `secondaryBackgroundColor = "#f0f2f6"`
  - `textColor = "#1f2937"`
* **Programmatic Theme Injection**: `ui_helpers.py` defines `LIGHT_THEME` and `DARK_THEME` dictionaries mapping colors to variables (like `bg`, `card`, `border`, `border_soft`, `sidebar_bg`, etc.).
* **CSS Variable Setup**: `inject_visual_system(theme_mode)` reads the active theme settings and replaces token placeholders (e.g. `TK_BG`, `TK_CARD`, `TK_BORDER_SOFT`) in the CSS template, injecting the resulting `<style>` element into the page via `st.markdown(..., unsafe_allow_html=True)`.
