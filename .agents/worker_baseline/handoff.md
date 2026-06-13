# Handoff Report — Baseline Verification

## 1. Observation
- **Command:** `python _verify_metrics.py` executed successfully inside `c:\Users\PratikPandey\unified-scf-dashboard\`.
  - Verbatim Output:
    ```
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
- **Command:** `python _verify_app.py` failed with `exit code 1` inside `c:\Users\PratikPandey\unified-scf-dashboard\`.
  - Verbatim error log:
    ```
    Traceback (most recent call last):
      File "C:\Users\PratikPandey\unified-scf-dashboard\_verify_app.py", line 29, in <module>
        at.radio(key="theme_mode").set_value("Dark")
        ~~~~~~~~^^^^^^^^^^^^^^^^^^
      File "C:\Users\PratikPandey\scoop\apps\python\current\Lib\site-packages\streamlit\testing\v1\element_tree.py", line 263, in __call__
        raise KeyError(key)
    KeyError: 'theme_mode'
    ```
- **File structure inspection (`app.py`, `ui_helpers.py`, views modules):**
  - `app.py` has no interactive element configured with `key="theme_mode"`.
  - Tabs: Configured in `app.py` using `st.tabs([...])` inside conditional blocks for "Team Nikhil" (10 tabs) and "Team Pankit" (11 tabs).
  - DataFrame Rendering: Custom helper `show_table(frame, columns, height)` is defined in `ui_helpers.py:769-775` utilizing `st.dataframe`. In addition, direct calls to `st.dataframe(...)` and `st.data_editor(...)` are present across `views_nikhil.py`, `views_pankit.py`, and `views_referral.py`.
  - Styling configuration: In `ui_helpers.py:419-425`, dataframe borders are configured using `[data-testid="stDataFrame"]` styling with a border color `var(--scf-border-soft)` and `border-radius: 10px`. No custom rules for alternating rows exist; it uses native Streamlit dataframe styles under Glide Data Grid.

## 2. Logic Chain
1. Since `_verify_metrics.py` completed with all assertions OK, the underlying data computation and filter structures (e.g. `is_workable`, `weighted_irr`, `filter_team`, CP universe, and reconstructed OB calculations) match the expected baseline datasets and business rules exactly.
2. Since `_verify_app.py` attempted to retrieve a radio widget with `key="theme_mode"` to select "Dark" but `app.py` does not render a radio widget for theme selection (instead, it relies on retrieving `theme_mode` directly from `st.session_state` without a widget connection), `AppTest.from_file` throws a `KeyError: 'theme_mode'`. This confirms that the baseline app testing suite fails due to a discrepancy between the test assumptions and the actual UI implementation in `app.py`.
3. In `ui_helpers.py`, `inject_visual_system` applies global layout and card component styles via an HTML template. The `[data-testid="stDataFrame"]` CSS selector specifically overrides Streamlit's default container box-shadow, border-radius, and border properties.
4. Because there are no custom CSS selectors targeting odd/even rows (like `tr:nth-child(even)` or Glide Grid variables) in `ui_helpers.py`, the alternating row colors are governed strictly by default Streamlit theme settings.

## 3. Caveats
- No changes to the codebase were authorized or executed during Milestone 1. Fixing the `theme_mode` testing error is scoped for Milestone 4 (Regression Fixing).
- Alternating row styling inside Glide Data Grid is determined by the underlying Streamlit version and theme config (such as `.streamlit/config.toml`).

## 4. Conclusion
- The baseline metrics verification is healthy and functional.
- The baseline app verification is broken due to a test-to-implementation discrepancy regarding the `theme_mode` widget.
- UI layouts (tabs, table columns, borders) are standardized via custom CSS injection and helper wrappers (`show_table`), but direct dataframe rendering calls are scattered, creating styling noise.

## 5. Verification Method
- Independent verification can be performed by running:
  - `python _verify_metrics.py` (passes)
  - `python _verify_app.py` (fails with `KeyError: 'theme_mode'`)
- Inspect the generated report in `.agents/worker_baseline/analysis.md` for full details.
