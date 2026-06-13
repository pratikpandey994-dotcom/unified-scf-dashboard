## 2026-06-13T11:43:20Z

You are the Visual & Subtab Implementer. Your working directory is c:\Users\PratikPandey\unified-scf-dashboard\.agents\teamwork_preview_worker_visual_subtabbing\.
Your mission is to execute Milestones 3 and 4: Visual Metric Transformation and Leadership Sub-tabbing.

Specifically, implement the following changes in the codebase:

1. Modify `dashboard_metrics.py` inside the function `build_portfolio`:
   - After creating `ob_pivot` (around lines 135-143), map each account ID to its last 30 values of OB as a list of floats.
   - If `ob_pivot` is not empty:
     ```python
     if not ob_pivot.empty:
         accounts["ob_trend"] = accounts["id"].map(lambda uid: ob_pivot[uid].tail(30).tolist() if uid in ob_pivot.columns else [0.0]*30)
     else:
         accounts["ob_trend"] = accounts["id"].map(lambda _: [0.0]*30)
     ```
   - Ensure the column `ob_trend` is added to the returned `accounts` DataFrame.

2. Modify `ui_helpers.py` inside the function `data_config`:
   - Add the key `"ob_trend"` to the returned dictionary:
     ```python
     "ob_trend": st.column_config.LineChartColumn("OB Trend (30d)", y_min=0),
     ```

3. Modify `views_nikhil.py` to include `"ob_trend"` in the columns list for these tables:
   - Inside `render_portfolio` (around line 731):
     `["company", "am", "account_type", "quality", "util_denom", "ob", "ob_trend", "utilization_pct", "irr"]`
   - Inside `render_health` (around line 198):
     `["company", "am", "account_type", "util_denom", "ob", "ob_trend", "utilization_pct", "irr"]`
   - Inside `render_health` (around line 235):
     `["company", "am", "account_type", "util_denom", "ob", "ob_trend", "last_disbursed", "days_since_last"]`
   - Inside `render_actions` (around line 277):
     `["company", "am", "account_type", "util_denom", "ob", "ob_trend", "headroom", "due_in_window", "opportunity"]`
   - Inside `render_pulse` (around line 364):
     `["company", "am", "account_type", "util_denom", "ob", "ob_trend", "utilization_pct", "ob_change_30d", "last_disbursed", "days_since_last"]`
   - Inside `render_pulse` (around line 373):
     `["company", "am", "account_type", "util_denom", "ob", "ob_trend", "last_disbursed", "days_since_last"]`
   - Inside `render_pulse` (around line 381):
     `["company", "am", "util_denom", "ob", "ob_trend", "utilization_pct", "headroom", "peak_ob", "peak_gap"]`

4. Modify `views_pankit.py` to include `"ob_trend"` in the columns list for these tables:
   - Inside `render_inventory` (around line 99):
     `["company", "am", "facility", "ob", "ob_trend", "mtd_repayments", "net_ob", "utilization_pct", "raw_status"]`
   - Inside `render_utilization` (around line 130):
     `["company", "am", "facility", "ob", "ob_trend", "utilization_pct", "raw_status"]`
   - Inside `render_zero_ob` (around line 144):
     `["company", "am", "facility", "ob", "ob_trend", "last_disbursed", "days_since_last", "ob_30d", "raw_status"]`
   - Inside `render_workable_inactive` (around line 160):
     `["company", "am", "facility", "ob_trend", "last_disbursed", "months_since_last", "gap_to_75", "raw_status"]`
   - Inside `render_repayments` (around line 174):
     `["company", "am", "ob_30d", "ob_trend", "mtd_repayments", "ob", "net_ob"]`
   - Inside `render_ob_dent` (around line 199):
     `["company", "am", "ob_30d", "ob", "ob_trend", "ob_dent_30d", "ob_dent_30d_pct_display", "raw_status"]`
   - Inside `render_opportunity_views` (around line 241):
     `["company", "am", "facility", "ob", "ob_trend", "gap_to_75"]`
   - Inside `render_opportunity_views` (around line 252):
     `["company", "am", "facility", "ob", "ob_trend", "gap_to_75"]`
   - Inside `render_opportunity_views` (around line 259):
     `["company", "am", "facility", "ob_trend", "last_disbursed", "days_since_last"]`
   - Inside `render_opportunity_views` (around line 265):
     `["company", "am", "facility", "ob_trend", "utilization_pct"]`

5. Modify `app.py` to nest sub-tabs using `st.tabs` inside the main tabs to reduce vertical scrolling:
   - For **Team Nikhil**:
     - Inside `tabs[3]` (Risk & Collections), define sub-tabs:
       `sub_tabs = st.tabs(["Risk Exposure (Portfolio Quality)", "Utilization & Stuck Invoices", "Dormancy & Action Lists", "CP Partner Health"])`
       Assign each render call to its respective sub-tab context (i.e. `render_portfolio` under `sub_tabs[0]`, `render_health` under `sub_tabs[1]`, `render_actions` under `sub_tabs[2]`, `render_cp_health` under `sub_tabs[3]`).
     - Inside `tabs[4]` (Account Detail & Tracker), define sub-tabs:
       `sub_tabs = st.tabs(["Priority Tracker", "Account Pulse", "Shared Insights"])`
       Assign `render_tracker` to `sub_tabs[0]`, `render_pulse` to `sub_tabs[1]`, `render_insights` to `sub_tabs[2]`.
   - For **Team Pankit**:
     - Inside `tabs[1]` (Balance & Utilization), define sub-tabs:
       `sub_tabs = st.tabs(["Balance & Utilization", "75% Engine Opportunities", "Account Inventory", "Zero OB Accounts"])`
       Assign `render_utilization` to `sub_tabs[0]`, `render_75_engine` to `sub_tabs[1]`, `render_inventory` to `sub_tabs[2]`, `render_zero_ob` to `sub_tabs[3]`.
     - Inside `tabs[3]` (Risk & Collections), define sub-tabs:
       `sub_tabs = st.tabs(["Repayments", "OB Dent (30d Reductions)"])`
       Assign `render_repayments` to `sub_tabs[0]`, `render_ob_dent` to `sub_tabs[1]`.
     - Inside `tabs[4]` (Account Detail & Tracker), define sub-tabs:
       `sub_tabs = st.tabs(["High Opportunity Queue & Zero OB", "Workable Inactive", "Shared Insights"])`
       Assign `render_opportunity_views` to `sub_tabs[0]`, `render_workable_inactive` to `sub_tabs[1]`, `render_insights` to `sub_tabs[2]`.

6. Modify `_verify_app.py`:
   - Change assertions for tab counts from `5` to `12` (for Team Nikhil) and `14` (for Team Pankit).

7. Run `python _verify_metrics.py` and `python _verify_app.py` to ensure that all tests run and pass successfully in the new layout.
