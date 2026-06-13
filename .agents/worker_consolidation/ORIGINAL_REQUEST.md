## 2026-06-13T11:00:50Z

You are a teamwork_preview_worker assigned to execute Milestone 3: Tab Restructuring & Consolidation.
Your working directory is c:\Users\PratikPandey\unified-scf-dashboard\.agents\worker_consolidation\.

Tasks:
1. Modify `app.py` to consolidate the tabs for BOTH Team Nikhil and Team Pankit into a single, clean structure of 5 identical tabs:
   `["Portfolio Snapshot", "Balance & Utilization", "Account Managers", "Risk & Collections", "Account Detail & Tracker"]`
   
   Ensure that inside each tab, the rendering functions from views files are sequentially called as follows:
   
   For **Team Nikhil**:
   - Tab 0: "Portfolio Snapshot"
     -> `render_snapshot(accounts, invoices)`
   - Tab 1: "Balance & Utilization"
     -> Render header `### Peak Movement`
     -> `render_peak(accounts, invoices, ob_pivot, today)`
   - Tab 2: "Account Managers"
     -> `render_team(accounts, invoices, today, cfg)`
   - Tab 3: "Risk & Collections"
     -> Render header `### Portfolio Quality`
     -> `render_portfolio(accounts, invoices, team_invoices, ob_pivot, today, cfg)`
     -> Render header `### Risk & Health`
     -> `render_health(accounts, invoices)`
     -> Render header `### Collections & Action Lists`
     -> `render_actions(accounts, invoices, raw["master"], today)`
     -> Render header `### CP Partner Health`
     -> `render_cp_health(accounts_all, invoices_all, today)`
   - Tab 4: "Account Detail & Tracker"
     -> Render header `### Priority Tracker`
     -> `render_tracker(accounts, invoices, today, cfg)`
     -> Render header `### Account Pulse`
     -> `render_pulse(accounts, invoices, today)`
     -> Render header `### Shared Insights`
     -> `render_insights(accounts, invoices, today, cfg)`

   For **Team Pankit**:
   - Tab 0: "Portfolio Snapshot"
     -> `render_executive(accounts, team_accounts, team_invoices, ob_pivot, cfg)`
   - Tab 1: "Balance & Utilization"
     -> Render header `### Balance & Utilization`
     -> `render_utilization(accounts, cfg)`
     -> Render header `### 75% Engine Opportunities`
     -> `render_75_engine(accounts)`
     -> Render header `### Account Inventory`
     -> `render_inventory(accounts)`
     -> Render header `### Zero OB Accounts`
     -> `render_zero_ob(accounts)`
   - Tab 2: "Account Managers"
     -> `render_am_performance(team_accounts, team_invoices, cfg)`
   - Tab 3: "Risk & Collections"
     -> Render header `### Repayments`
     -> `render_repayments(accounts, cfg, selected_am)`
     -> Render header `### OB Dent (30d Reductions)`
     -> `render_ob_dent(accounts, ob_pivot, team_accounts)`
   - Tab 4: "Account Detail & Tracker"
     -> Render header `### High Opportunity Queue & Zero OB`
     -> `render_opportunity_views(team_accounts, selected_am, cfg)`
     -> Render header `### Workable Inactive`
     -> `render_workable_inactive(team_accounts, selected_am)`
     -> Render header `### Shared Insights`
     -> `render_insights(accounts, invoices, today, cfg)`

2. Modify `_verify_app.py` to update the tab count assertions:
   - Line 27: Change `assert len(at.tabs) == 10` to `assert len(at.tabs) == 5`.
   - Line 75: Change `assert len(at.tabs) == 11` to `assert len(at.tabs) == 5`.

3. Run `python _verify_metrics.py` and `python _verify_app.py` from the project root to ensure everything passes with the new structure.
4. Document the exact command outputs and your files modifications in c:\Users\PratikPandey\unified-scf-dashboard\.agents\worker_consolidation\handoff.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
