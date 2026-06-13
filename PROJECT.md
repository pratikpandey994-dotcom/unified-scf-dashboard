# Project: Unified SCF Dashboard Minimalist Refactor

## Architecture
- `app.py`: Main Streamlit app containing sidebar inputs, theme handling, and tab dispatching.
- `ui_helpers.py`: Common formatting, table column config, chart styles, visual systems, and Excel exports.
- `views_nikhil.py`: Views for Team Nikhil.
- `views_pankit.py`: Views for Team Pankit.
- `views_referral.py`: Views for Referral program (if separate).
- `views_common.py`: Shared Insights tab.
- `data_loader.py`: Ingests and processes master & invoice data.
- `dashboard_metrics.py`: Computes KPI metrics, risk lists, origination metrics, etc.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Baseline Verification | Run `_verify_app.py` and `_verify_metrics.py` to confirm baseline test suite passes. | None | DONE |
| 2 | Visual Standardization | Edit `ui_helpers.py` and views to remove dataframe borders, alternating row colors, and other styling noise. | M1 | DONE |
| 3 | Tab Consolidation | Restructure and consolidate the existing 10 tabs into a clean, minimal set of views in `app.py` and views files. | M2 | DONE |
| 4 | Regression Fixing | Adjust tests in `_verify_app.py` and verify all metrics check out after the structural change. | M3 | DONE |
| 5 | Forensic Audit & Signoff | Run the Forensic Auditor to check compliance and ensure no git pushes were done. | M4 | DONE |

## Code Layout
- `app.py`: Streamlit entrypoint
- `ui_helpers.py`: Layout & formatting helper functions
- `views_*.py`: Component render files for different tabs
- `_verify_*.py`: Testing & validation scripts
