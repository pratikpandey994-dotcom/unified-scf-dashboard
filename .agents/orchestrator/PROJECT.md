# Project: Unified SCF Dashboard Data-Science Visual Sub-tabbing

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
| 1 | Raw Excel Analysis | Study raw Excel files (`us_scf___master_data___client_level_*.xlsx` and `us_scf___invoice_level_data_*.xlsx` in Downloads), understand their schema, distributions, and relationships. Save analysis to a report. | None | PLANNED |
| 2 | Baseline Verification | Run `_verify_app.py` and `_verify_metrics.py` to confirm current code passes baseline. | M1 | PLANNED |
| 3 | Visual Metric Transformation | Transform plain numbers in views (Nikhil & Pankit) into clean visual insights (sparklines, trendlines, micro-charts) without removing data. | M2 | PLANNED |
| 4 | Leadership Sub-tabbing | Organize long views into focused, clickable sub-tabs to eliminate vertical scroll fatigue. | M3 | PLANNED |
| 5 | Verification & Forensic Audit | Run testing suite and Forensic Auditor to verify functionality and ensure no git pushes. | M4 | PLANNED |

## Code Layout
- `app.py`: Streamlit entrypoint
- `ui_helpers.py`: Layout & formatting helper functions
- `views_*.py`: Component render files for different tabs
- `_verify_*.py`: Testing & validation scripts
