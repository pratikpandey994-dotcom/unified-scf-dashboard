from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from data_loader import FILE_PATTERNS, default_files_found, load_data, load_demo_data
from dashboard_metrics import (
    TEAMS,
    apply_filters,
    build_portfolio,
    filter_team,
    get_window,
)
from ui_helpers import inject_visual_system
from views_nikhil import (
    render_snapshot,
    render_portfolio,
    render_team,
    render_health,
    render_actions,
    render_pulse,
    render_peak,
    render_cp_health,
    render_tracker,
)
from views_pankit import (
    render_executive,
    render_inventory,
    render_utilization,
    render_zero_ob,
    render_workable_inactive,
    render_repayments,
    render_ob_dent,
    render_am_performance,
    render_75_engine,
    render_opportunity_views,
)
from views_common import render_insights


st.set_page_config(
    page_title="Drip SCF Leader",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

theme_mode = st.session_state.get("theme_mode", "Light")
inject_visual_system(theme_mode)


# ---------------------------------------------------------------- Sidebar ----
with st.sidebar:
    st.header("Appearance")
    st.radio("Theme", ["Light", "Dark"], index=0 if theme_mode == "Light" else 1, key="theme_mode", horizontal=True)

    # Default to Demo data when local extracts aren't present (e.g. Streamlit Cloud).
    _found = default_files_found()
    _default_src = 0 if all(_found.values()) else 1
    st.header("Data Source")
    data_mode = st.radio("Source", ["Real files", "Demo data"], index=_default_src, key="data_mode")
    uploads: dict[str, object] = {}
    if data_mode == "Demo data":
        st.info("Demo mode uses synthetic data for UI review.")
    else:
        use_uploads = st.toggle("Upload files manually", value=False)
        if use_uploads:
            uploads["master_file"] = st.file_uploader("Master data — client level", type=["xlsx", "xls"], key="master_file")
            uploads["invoice_file"] = st.file_uploader("Invoice level data", type=["xlsx", "xls"], key="invoice_file")
        with st.expander("Auto-detected files (newest match in Downloads)"):
            for kind, pattern in FILE_PATTERNS.items():
                found = _found.get(kind)
                st.caption(f"{pattern}: {found.name if found else '— not found —'}")

    today_value = st.date_input("As of date", value=date(2026, 6, 11), key="as_of_date")


# ---------------------------------------------------------------- Data load ----
try:
    raw = (
        load_demo_data()
        if data_mode == "Demo data"
        else load_data(as_of=str(today_value), **{k: v for k, v in uploads.items() if v is not None})
    )
    accounts_all, invoices_all, ob_pivot = build_portfolio(
        raw["master"],
        raw["invoices"],
        raw["ob_history"],
        pd.Timestamp(today_value),
    )
except Exception as exc:
    st.error(str(exc))
    st.stop()

today = pd.Timestamp(today_value)
st.session_state["_window_map"] = {
    "cw": get_window("cw", today),
    "cm": get_window("cm", today),
    "nm": get_window("nm", today),
}


# ---------------------------------------------------------------- Header ----
_date_str = f"{today_value.strftime('%b')} {today_value.day}, {today_value.year}"
st.markdown(
    f'<div class="scf-page-header">'
    f'<div><span class="scf-page-title">Drip SCF</span>'
    f'<span class="scf-page-tag">Leader Intelligence</span></div>'
    f'<span class="scf-page-date">{_date_str}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

team_name = st.radio("View", list(TEAMS.keys()), horizontal=True, key="team_name")
cfg = TEAMS[team_name]

team_accounts = filter_team(accounts_all, team_name)
team_invoices = invoices_all[invoices_all["account_id"].isin(set(team_accounts["id"]))]

if team_accounts.empty:
    st.warning("No accounts match this team.")
    st.stop()

am_options = ["All"] + [am for am in cfg.ams if am in set(team_accounts["am"])]
account_type_options = sorted(team_accounts["account_type"].dropna().unique().tolist())
raw_status_options = sorted(team_accounts["raw_status"].dropna().astype(str).unique().tolist())

with st.sidebar:
    st.header("Filters")
    selected_am = st.selectbox(
        "Account manager",
        am_options,
        format_func=lambda value: "All account managers" if value == "All" else value,
        key=f"{team_name}_am",
    )
    selected_account_types = st.multiselect(
        "Account type", account_type_options, default=[], key=f"{team_name}_account_types"
    )
    selected_raw_statuses = st.multiselect(
        "Raw status", raw_status_options, default=[], key=f"{team_name}_raw_statuses"
    )

accounts = apply_filters(team_accounts, selected_am, selected_account_types, selected_raw_statuses)
invoices = team_invoices[team_invoices["account_id"].isin(set(accounts["id"]))]

if accounts.empty:
    st.warning("No accounts match the current filter set.")
    st.stop()


# ---------------------------------------------------------------- Routing ----
if team_name == "Team Nikhil":
    st.caption("CP pod · Utilization = Facility + Overdraft")
    tabs = st.tabs([
        "Overview", "Portfolio Quality", "Team", "Risk & Health",
        "Collections", "Account Pulse", "Peak Movement", "CP Health", "Tracker", "Insights",
    ])
    with tabs[0]:
        render_snapshot(accounts, invoices)
    with tabs[1]:
        render_portfolio(accounts, invoices, team_invoices, ob_pivot, today, cfg)
    with tabs[2]:
        render_team(accounts, invoices, today, cfg)
    with tabs[3]:
        render_health(accounts, invoices)
    with tabs[4]:
        render_actions(accounts, invoices, raw["master"], today)
    with tabs[5]:
        render_pulse(accounts, invoices, today)
    with tabs[6]:
        render_peak(accounts, invoices, ob_pivot, today)
    with tabs[7]:
        render_cp_health(accounts_all, invoices_all, today)
    with tabs[8]:
        render_tracker(accounts, invoices, today, cfg)
    with tabs[9]:
        render_insights(accounts, invoices, today, cfg)

else:
    st.caption("Direct sales · Utilization = Facility only")
    tabs = st.tabs([
        "Overview", "Inventory", "Utilization", "Zero OB",
        "Workable Inactive", "Repayments", "OB Dent",
        "AM Performance", "75% Engine", "Opportunity", "Insights",
    ])
    with tabs[0]:
        render_executive(accounts, team_accounts, team_invoices, ob_pivot, cfg)
    with tabs[1]:
        render_inventory(accounts)
    with tabs[2]:
        render_utilization(accounts, cfg)
    with tabs[3]:
        render_zero_ob(accounts)
    with tabs[4]:
        render_workable_inactive(team_accounts, selected_am)
    with tabs[5]:
        render_repayments(accounts, cfg, selected_am)
    with tabs[6]:
        render_ob_dent(accounts, ob_pivot, team_accounts)
    with tabs[7]:
        render_am_performance(team_accounts, team_invoices, cfg)
    with tabs[8]:
        render_75_engine(accounts)
    with tabs[9]:
        render_opportunity_views(team_accounts, selected_am, cfg)
    with tabs[10]:
        render_insights(accounts, invoices, today, cfg)
