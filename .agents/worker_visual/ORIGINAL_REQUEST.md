## 2026-06-13T10:56:39Z
You are a teamwork_preview_worker assigned to execute Milestone 2: Visual Standardization.
Your working directory is c:\Users\PratikPandey\unified-scf-dashboard\.agents\worker_visual\.

Tasks:
1. Modify `.streamlit/config.toml` to set:
   `secondaryBackgroundColor = "#ffffff"` (to match the light theme background and strip alternating row colors from native Streamlit dataframes).
2. Modify `ui_helpers.py`:
   - In `_CSS_TEMPLATE` (around line 419), update the styling of `[data-testid="stDataFrame"]` to strip borders and shadow:
     ```css
     [data-testid="stDataFrame"] {
       border: none !important;
       box-shadow: none !important;
       border-radius: 0px !important;
     }
     ```
3. Modify `app.py`:
   - Replace the line `theme_mode = st.session_state.get("theme_mode", "Light")` with:
     ```python
     # Theme mode selectbox/radio defined in sidebar
     ```
     And inside `with st.sidebar:`, add:
     ```python
     theme_mode = st.radio("Theme Mode", ["Light", "Dark"], key="theme_mode")
     ```
     Before the sidebar is processed, make sure the `inject_visual_system(theme_mode)` is called with the chosen theme.
   - Inside `with st.sidebar:`, add the global Account Manager selectbox:
     ```python
     selected_am = st.selectbox("Account Manager", am_options, key=f"{team_name}_am")
     ```
     Make sure `selected_am` is defined for both teams.
   - Filter `accounts` and `invoices` globally by `selected_am` if it is not `"All"`:
     ```python
     if selected_am != "All":
         accounts = accounts[accounts["am"] == selected_am]
         invoices = invoices[invoices["account_id"].isin(set(accounts["id"]))]
     ```
4. Run `python _verify_metrics.py` and `python _verify_app.py` to see if the theme_mode key error is resolved and report any issues.
5. Document your edits and test verification results in c:\Users\PratikPandey\unified-scf-dashboard\.agents\worker_visual\handoff.md.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
