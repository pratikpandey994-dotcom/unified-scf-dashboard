# Context — 2026-06-13T16:22:50+05:30

## Project Info
- Project: Unified SCF Dashboard
- Objective: Refactor 10 tabs into a minimal layout, strip visual noise (borders, alternate row colors), verify local functionality without git push.
- Directory: `c:\Users\PratikPandey\unified-scf-dashboard`

## Requirements
- **R1. Structural Refactor**: Autonomy to restructure/consolidate 10 tabs.
- **R2. Data-Dense Aesthetic**: Visual styling clean-up (sleek/clean tables, strip borders/alternating row styling). Keep dataframes visible by default.
- **R3. Local Testing Only**: No git pushes. Verify on localhost.

## Technical Context
- Streamlit application (`app.py`, `ui_helpers.py`, etc.)
- Verification scripts: `_verify_app.py`, `_verify_metrics.py`.
- Key specs in `docs/`: `docs/VISUAL_STANDARDIZATION_STUDY.md`, `docs/STREAMLIT_AUDIT.md`, etc.
