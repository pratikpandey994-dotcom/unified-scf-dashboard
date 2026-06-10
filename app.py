from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from data_loader import DEFAULT_FILES, load_data, load_demo_data
from dashboard_metrics import TEAMS, apply_filters, build_portfolio, filter_team
import views_nikhil
import views_pankit
import views_referral
from ui_helpers import inject_visual_system


st.set_page_config(
    page_title="Portfolio Dashboard",
    page_icon="SCF",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_visual_system()

query_team = st.query_params.get("team_name")
if isinstance(query_team, list):
    query_team = query_team[0] if query_team else None
if query_team in ("Team Nikhil", "Team Pankit") and "team_name" not in st.session_state:
    st.session_state["team_name"] = query_team


def show_source_defaults() -> None:
    with st.expander("Default file paths", expanded=False):
        for label, path in DEFAULT_FILES.items():
            st.caption(f"{label}: {path}")


def route_buttons(team_name: str) -> None:
    """Reference-style quick paths into the views that hold the detailed data."""
    if team_name == "Team Nikhil":
        routes = [
            ("Snapshot", "Snapshot"),
            ("Portfolio Quality", "Portfolio"),
            ("Team Scorecards", "Team"),
            ("Risk Health", "Health"),
            ("Action Queue", "Actions"),
            ("Account Pulse", "Account Pulse"),
            ("CP Health", "CP Health"),
            ("Tracker", "Tracker"),
        ]
    else:
        routes = [
            ("Executive", "Executive"),
            ("Inventory", "Account Inventory"),
            ("Utilization", "Utilization"),
            ("Zero OB", "Zero OB"),
            ("Inactive", "Workable Inactive"),
            ("Repayments", "Repayments"),
            ("OB Dent", "OB Dent"),
            ("AM Performance", "AM Performance"),
            ("75% Engine", "75% Engine"),
        ]

    st.markdown(
        '<div class="scf-path-row"><span class="scf-path-label">Smart paths</span></div>',
        unsafe_allow_html=True,
    )
    cols = st.columns(min(len(routes), 5))
    for idx, (label, target) in enumerate(routes):
        with cols[idx % len(cols)]:
            if st.button(label, key=f"{team_name}_route_{target}", use_container_width=True):
                st.session_state[f"{team_name}_nav"] = target
                st.rerun()


st.title("Portfolio Dashboard")
st.caption("Team Nikhil (CP pod) and Team Pankit (direct sales) in one place — each replicating its original dashboard's metrics and views.")

with st.sidebar:
    st.header("Data")
    data_mode = st.radio("Source", ["Real files", "Dummy data"], horizontal=False, key="data_mode")
    use_demo_data = data_mode == "Dummy data"
    use_uploads = (not use_demo_data) and st.toggle("Upload files manually", value=False)
    uploads = {}
    if use_demo_data:
        st.info("Demo mode uses synthetic data for testing and UI changes.")
    elif use_uploads:
        uploads["master_file"] = st.file_uploader("Master data", type=["xlsx", "xls"], key="master_file")
        uploads["view1_file"] = st.file_uploader("View 1", type=["xlsx", "xls"], key="view1_file")
        uploads["view2_file"] = st.file_uploader("View 2", type=["xlsx", "xls"], key="view2_file")
        uploads["historic_ob_file"] = st.file_uploader("Historic OB", type=["xlsx", "xls"], key="historic_ob_file")
        uploads["current_ob_file"] = st.file_uploader("Current OB", type=["xlsx", "xls"], key="current_ob_file")
    else:
        show_source_defaults()

    st.header("View")
    today_value = st.date_input("As of date", value=date(2026, 6, 5), key="as_of_date")

try:
    raw = load_demo_data() if use_demo_data else (load_data(**uploads) if use_uploads else load_data())
    accounts_all, invoices_all, ob_pivot = build_portfolio(
        raw["master"],
        raw["view1"],
        raw["view2"],
        raw["ob_history"],
        pd.Timestamp(today_value),
    )
except Exception as exc:
    st.error(str(exc))
    st.stop()

today = pd.Timestamp(today_value)

team_name = st.radio("Division", list(TEAMS.keys()), horizontal=True, key="team_name")
cfg = TEAMS[team_name]

query_view = st.query_params.get("view")
if isinstance(query_view, list):
    query_view = query_view[0] if query_view else None

team_accounts = filter_team(accounts_all, team_name)
team_invoices = invoices_all[invoices_all["account_id"].isin(set(team_accounts["id"]))]

if team_accounts.empty:
    st.warning("No accounts matched this team segment and AM list.")
    st.stop()

# ---- Filters (persisted per-team in session_state via stable keys) ----
am_counts = team_accounts["am"].value_counts().to_dict()
am_options = ["All"] + [am for am in cfg.ams if am in am_counts]
f1, f2, f3 = st.columns([1, 1, 1])
with f1:
    selected_am = st.selectbox(
        "Account Manager",
        am_options,
        format_func=lambda value: "All Account Managers" if value == "All" else f"{value} ({am_counts.get(value, 0)})",
        key=f"{team_name}_am",
    )
with f2:
    account_type_options = sorted(team_accounts["account_type"].dropna().unique().tolist())
    selected_account_types = st.multiselect(
        "Account type", account_type_options, default=[],
        key=f"{team_name}_account_types", help="Leave blank for all account types.",
    )
with f3:
    status_options = sorted(team_accounts["raw_status"].dropna().astype(str).unique().tolist())
    selected_statuses = st.multiselect(
        "Raw status", status_options, default=[],
        key=f"{team_name}_raw_statuses", help="Leave blank for all raw statuses in this division.",
    )

accounts = apply_filters(team_accounts, selected_am, selected_account_types, selected_statuses)
invoices = team_invoices[team_invoices["account_id"].isin(set(accounts["id"]))]

st.subheader(f"{team_name} — {'All Account Managers' if selected_am == 'All' else selected_am}")
if team_name == "Team Nikhil":
    st.caption("Utilization and 75% targets use total facility = facility size + overdraft (per the CP Pod dashboard).")
else:
    st.caption("Utilization and 75% targets use facility size only (per the 75% Utilization Engine).")

# ---- Navigation: a keyed radio instead of st.tabs so the active view ----
# ---- survives every rerun (st.tabs resets to the first tab whenever  ----
# ---- a widget inside a later tab fires).                              ----
NIKHIL_VIEWS = ["Snapshot", "Portfolio", "Team", "Health", "Actions", "Account Pulse", "Peak", "CP Health", "Tracker", "Referral Tracker"]
PANKIT_VIEWS = ["Executive", "Account Inventory", "Utilization", "Zero OB", "Workable Inactive",
                "Repayments", "OB Dent", "AM Performance", "75% Engine", "Opportunity Views", "Referral Tracker"]

view_options = NIKHIL_VIEWS if team_name == "Team Nikhil" else PANKIT_VIEWS
if query_view in view_options:
    st.session_state[f"{team_name}_nav"] = query_view
route_buttons(team_name)
view = st.radio("View", view_options, horizontal=True, key=f"{team_name}_nav", label_visibility="collapsed")
st.divider()

if team_name == "Team Nikhil":
    if view == "Snapshot":
        views_nikhil.render_snapshot(accounts, invoices)
    elif view == "Portfolio":
        views_nikhil.render_portfolio(accounts, invoices, team_invoices, ob_pivot, today, cfg)
    elif view == "Team":
        views_nikhil.render_team(accounts, invoices, today, cfg)
    elif view == "Health":
        views_nikhil.render_health(accounts, invoices)
    elif view == "Actions":
        views_nikhil.render_actions(accounts, invoices, raw["master"], today)
    elif view == "Account Pulse":
        views_nikhil.render_pulse(accounts, invoices, today)
    elif view == "Peak":
        views_nikhil.render_peak(accounts, invoices, ob_pivot, today)
    elif view == "CP Health":
        views_nikhil.render_cp_health(accounts_all, invoices_all, today)
    elif view == "Tracker":
        views_nikhil.render_tracker(team_accounts, team_invoices, today, cfg)
    elif view == "Referral Tracker":
        views_referral.render_referral_tracker(cfg)
else:
    if view == "Executive":
        views_pankit.render_executive(accounts, team_accounts, team_invoices, ob_pivot, cfg)
    elif view == "Account Inventory":
        views_pankit.render_inventory(accounts)
    elif view == "Utilization":
        views_pankit.render_utilization(accounts, cfg)
    elif view == "Zero OB":
        views_pankit.render_zero_ob(accounts)
    elif view == "Workable Inactive":
        views_pankit.render_workable_inactive(team_accounts, selected_am)
    elif view == "Repayments":
        views_pankit.render_repayments(accounts, cfg, selected_am)
    elif view == "OB Dent":
        views_pankit.render_ob_dent(accounts, ob_pivot, team_accounts)
    elif view == "AM Performance":
        views_pankit.render_am_performance(team_accounts, team_invoices, cfg)
    elif view == "75% Engine":
        views_pankit.render_75_engine(accounts)
    elif view == "Opportunity Views":
        views_pankit.render_opportunity_views(team_accounts, selected_am, cfg)
    elif view == "Referral Tracker":
        views_referral.render_referral_tracker(cfg)
