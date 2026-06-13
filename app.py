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
    initial_sidebar_state="collapsed",
)

theme_mode = st.session_state.get("theme_mode", "Light")
inject_visual_system(theme_mode)


# ---------------------------------------------------------------- Sidebar ----
with st.sidebar:

    if "use_sample" not in st.session_state:
        st.session_state["use_sample"] = False

    st.header("Data Upload")
    if st.button("Load Sample Data", use_container_width=True):
        st.session_state["use_sample"] = True

    master_file = st.file_uploader("Masterdata file", type=["xlsx", "xls"], key="master_file")
    invoice_file = st.file_uploader("Invoice Data file", type=["xlsx", "xls"], key="invoice_file")

    if master_file or invoice_file:
        st.session_state["use_sample"] = False

    today_value = date.today()


# ---------------------------------------------------------------- Data load ----
try:
    if st.session_state["use_sample"]:
        raw = load_demo_data()
    else:
        raw = load_data(master_file=master_file, invoice_file=invoice_file, as_of=str(today_value))
    if not {"master", "invoices", "ob_history"} <= set(raw):
        # Cached result from a pre-migration loader (old five-file schema) — heal and rerun.
        st.cache_data.clear()
        st.rerun()
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
st.title("Unified SCF Dashboard")

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
    st.divider()
    st.markdown("""
        <h3 style='margin-top: -10px !important; margin-bottom: 0 !important;'>Custom Filters</h3>
        <p style='margin-top: -5px !important; margin-bottom: 0 !important;'><b>Masterdata</b></p>
    """, unsafe_allow_html=True)
    account_filter_cols = [c for c in team_accounts.columns]
    selected_account_filters = st.multiselect("Add filter", account_filter_cols, default=[], key=f"{team_name}_ms_master")
    account_filter_values = {}
    if selected_account_filters:
        for col_name in selected_account_filters:
            options = sorted(team_accounts[col_name].dropna().astype(str).unique().tolist())
            account_filter_values[col_name] = st.multiselect(col_name, options, default=[], key=f"{team_name}_{col_name}_master")

    st.markdown("<p style='margin-top: 5px !important; margin-bottom: 0 !important;'><b>Invoice Data</b></p>", unsafe_allow_html=True)
    view2_filter_cols = [c for c in team_invoices.columns if c not in account_filter_cols]
    selected_view2_filters = st.multiselect("Add filter", view2_filter_cols, default=[], key=f"{team_name}_ms_invoice")
    view2_filter_values = {}
    if selected_view2_filters:
        for col_name in selected_view2_filters:
            options = sorted(team_invoices[col_name].dropna().astype(str).unique().tolist())
            view2_filter_values[col_name] = st.multiselect(col_name, options, default=[], key=f"{team_name}_{col_name}_invoice")

accounts = team_accounts.copy()

for col_name, selected_values in account_filter_values.items():
    if selected_values:
        accounts = accounts[accounts[col_name].astype(str).isin(selected_values)]

invoices = team_invoices[team_invoices["account_id"].isin(set(accounts["id"]))]

for col_name, selected_values in view2_filter_values.items():
    if selected_values:
        invoices = invoices[invoices[col_name].astype(str).isin(selected_values)]

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
