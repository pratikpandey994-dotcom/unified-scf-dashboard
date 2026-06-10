from __future__ import annotations

from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import DEFAULT_FILES, load_data
from metrics import (
    TEAMS,
    am_summary,
    apply_filters,
    build_portfolio,
    filter_team,
    ob_trend,
    portfolio_kpis,
    utilization_buckets,
)


st.set_page_config(
    page_title="Unified SCF Portfolio",
    page_icon="SCF",
    layout="wide",
    initial_sidebar_state="expanded",
)


def fmt_money(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    value = float(value)
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def fmt_pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value) * 100:.1f}%"


def metric_row(kpis: dict[str, float | int | None]) -> None:
    cols = st.columns(5)
    cols[0].metric("Accounts", f"{int(kpis['accounts']):,}")
    cols[1].metric("Total Facility", fmt_money(kpis["total_facility"]))
    cols[2].metric("Total OB", fmt_money(kpis["total_ob"]))
    cols[3].metric("Utilization", fmt_pct(kpis["utilization"]))
    cols[4].metric("MTD Repayments", fmt_money(kpis["mtd_repayments"]))

    cols = st.columns(5)
    cols[0].metric("Net OB", fmt_money(kpis["net_ob"]))
    cols[1].metric("Gap to 75%", fmt_money(kpis["gap_to_75"]))
    cols[2].metric("Zero OB", f"{int(kpis['zero_ob']):,}")
    cols[3].metric("Overdue OB", fmt_money(kpis["overdue_ob"]))
    cols[4].metric("WIRR", "-" if kpis["wirr"] is None else f"{float(kpis['wirr']):.2f}%")


def data_config() -> dict:
    return {
        "facility": st.column_config.NumberColumn("Facility", format="$ %.0f"),
        "overdraft": st.column_config.NumberColumn("Overdraft", format="$ %.0f"),
        "total_facility": st.column_config.NumberColumn("Total Facility", format="$ %.0f"),
        "ob": st.column_config.NumberColumn("OB", format="$ %.0f"),
        "mtd_repayments": st.column_config.NumberColumn("MTD Repayments", format="$ %.0f"),
        "net_ob": st.column_config.NumberColumn("Net OB", format="$ %.0f"),
        "target_ob_75": st.column_config.NumberColumn("Target OB 75%", format="$ %.0f"),
        "gap_to_75": st.column_config.NumberColumn("Gap to 75%", format="$ %.0f"),
        "utilization_pct": st.column_config.NumberColumn("Utilization", format="%.1f%%"),
        "ob_dent_30d": st.column_config.NumberColumn("30d OB Dent", format="$ %.0f"),
        "ob_dent_30d_pct_display": st.column_config.NumberColumn("30d Dent %", format="%.1f%%"),
        "last_disbursed": st.column_config.DateColumn("Last Disbursed"),
    }


def show_source_defaults() -> None:
    with st.expander("Default file paths", expanded=False):
        for label, path in DEFAULT_FILES.items():
            st.caption(f"{label}: {path}")


st.title("Unified SCF Portfolio Dashboard")
st.caption("Select a team, then view the leader rollup or any individual AM.")

with st.sidebar:
    st.header("Data")
    use_uploads = st.toggle("Upload files manually", value=False)
    uploads = {}
    if use_uploads:
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
    raw = load_data(**uploads) if use_uploads else load_data()
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

team_name = st.radio(
    "Team",
    list(TEAMS.keys()),
    horizontal=True,
    key="team_name",
)

team_accounts = filter_team(accounts_all, team_name)
team_invoices = invoices_all[invoices_all["account_id"].isin(set(team_accounts["id"]))]
cfg = TEAMS[team_name]

if team_accounts.empty:
    st.warning("No accounts matched this team segment and AM list.")
    st.stop()

am_counts = team_accounts["am"].value_counts().to_dict()
am_options = ["All"] + [am for am in cfg.ams if am in am_counts]
selected_am = st.selectbox(
    "AM",
    am_options,
    format_func=lambda value: "All team AMs" if value == "All" else f"{value} ({am_counts.get(value, 0)})",
    key=f"{team_name}_am",
)

filter_cols = st.columns(2)
with filter_cols[0]:
    account_type_options = sorted(team_accounts["account_type"].dropna().unique().tolist())
    selected_account_types = st.multiselect(
        "Account type",
        account_type_options,
        default=[],
        key=f"{team_name}_account_types",
        help="Leave blank for all account types.",
    )
with filter_cols[1]:
    status_options = sorted(team_accounts["raw_status"].dropna().astype(str).unique().tolist())
    selected_statuses = st.multiselect(
        "Raw account status",
        status_options,
        default=[],
        key=f"{team_name}_raw_statuses",
        help="Leave blank for all raw statuses.",
    )

accounts = apply_filters(team_accounts, selected_am, selected_account_types, selected_statuses)
invoices = team_invoices[team_invoices["account_id"].isin(set(accounts["id"]))]
kpis = portfolio_kpis(accounts, invoices)

st.subheader(f"{team_name} - {'Leader View' if selected_am == 'All' else selected_am}")
st.caption(
    "Utilization and 75% targets use total facility = facility size + overdraft. "
    "Pankit Direct Team is non-partner/direct accounts for Pankit's AM list."
)
metric_row(kpis)

tabs = st.tabs(["Snapshot", "Accounts", "Utilization", "Repayments", "Opportunities", "OB Trend"])

with tabs[0]:
    left, right = st.columns([1.2, 1])
    with left:
        summary = am_summary(accounts if selected_am != "All" else team_accounts)
        if not summary.empty:
            fig = px.bar(
                summary,
                x="am",
                y=["ob", "facility"],
                barmode="group",
                labels={"value": "USD", "am": "AM", "variable": "Metric"},
                title="AM Portfolio Scale",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(summary, use_container_width=True, hide_index=True, column_config=data_config())
    with right:
        type_summary = (
            accounts.groupby("account_type", as_index=False)
            .agg(accounts=("id", "count"), ob=("ob", "sum"), facility=("total_facility", "sum"))
            .sort_values("ob", ascending=False)
        )
        if not type_summary.empty:
            fig = px.pie(type_summary, values="ob", names="account_type", hole=0.55, title="OB by Account Type")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(type_summary, use_container_width=True, hide_index=True, column_config=data_config())

with tabs[1]:
    st.dataframe(
        accounts[
            [
                "company",
                "am",
                "partner",
                "account_type",
                "raw_status",
                "total_facility",
                "ob",
                "mtd_repayments",
                "net_ob",
                "utilization_pct",
                "target_ob_75",
                "gap_to_75",
                "last_disbursed",
                "days_since_last",
            ]
        ].sort_values("total_facility", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config=data_config(),
    )

with tabs[2]:
    bucket_df = utilization_buckets(accounts)
    col1, col2 = st.columns([1, 1])
    with col1:
        fig = px.bar(bucket_df, x="Bucket", y="Accounts", text="Accounts", title="Utilization Buckets")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        high = int((accounts["utilization"] >= 0.75).sum())
        low = int(((accounts["utilization"] > 0) & (accounts["utilization"] < 0.50)).sum())
        st.metric("At or above 75%", f"{high:,}")
        st.metric("Below 50% but funded", f"{low:,}")
        st.metric("Average utilization", fmt_pct(accounts["utilization"].mean() if len(accounts) else 0))
    st.dataframe(
        accounts.sort_values("utilization", ascending=False)[
            ["company", "am", "account_type", "total_facility", "ob", "utilization_pct", "gap_to_75"]
        ],
        use_container_width=True,
        hide_index=True,
        column_config=data_config(),
    )

with tabs[3]:
    with_repay = accounts[accounts["mtd_repayments"] > 0].sort_values("mtd_repayments", ascending=False)
    cols = st.columns(3)
    cols[0].metric("Accounts with MTD repayments", f"{len(with_repay):,}")
    cols[1].metric("Total MTD repayments", fmt_money(with_repay["mtd_repayments"].sum()))
    cols[2].metric("Net OB after repayments", fmt_money(accounts["net_ob"].sum()))
    st.dataframe(
        with_repay[
            ["company", "am", "account_type", "ob_30d", "ob", "mtd_repayments", "net_ob", "utilization_pct"]
        ],
        use_container_width=True,
        hide_index=True,
        column_config=data_config(),
    )

with tabs[4]:
    opps = accounts[(accounts["gap_to_75"] > 0) & (accounts["total_facility"] > 0)].copy()
    dormant = accounts[(accounts["days_since_last"].fillna(9999) >= 90)].copy()
    zero_ob = accounts[accounts["ob"] < 1].copy()
    c1, c2, c3 = st.columns(3)
    c1.metric("Opportunity accounts", f"{len(opps):,}", fmt_money(opps["gap_to_75"].sum()))
    c2.metric("Not funded 90+ days", f"{len(dormant):,}")
    c3.metric("Zero OB accounts", f"{len(zero_ob):,}", fmt_money(zero_ob["total_facility"].sum()))

    view = st.radio(
        "Opportunity view",
        ["Gap to 75%", "Not Funded 90+ Days", "Zero OB", "30d OB Dent"],
        horizontal=True,
        key=f"{team_name}_opp_view",
    )
    if view == "Gap to 75%":
        frame = opps.sort_values("gap_to_75", ascending=False)
    elif view == "Not Funded 90+ Days":
        frame = dormant.sort_values("days_since_last", ascending=False)
    elif view == "Zero OB":
        frame = zero_ob.sort_values("total_facility", ascending=False)
    else:
        frame = accounts[(accounts["ob_dent_30d_pct"] > 0.25) | (accounts["ob_dent_30d"] > 100_000)].sort_values(
            "ob_dent_30d", ascending=False
        )

    st.dataframe(
        frame[
            [
                "company",
                "am",
                "account_type",
                "total_facility",
                "ob",
                "utilization_pct",
                "gap_to_75",
                "last_disbursed",
                "days_since_last",
                "ob_dent_30d",
                "ob_dent_30d_pct_display",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config=data_config(),
    )

with tabs[5]:
    trend = ob_trend(ob_pivot, set(accounts["id"]))
    if trend.empty:
        st.info("Upload historical/current OB files to enable the OB trend.")
    else:
        fig = px.line(trend, x="date", y="ob", title="Portfolio OB Trend", labels={"ob": "OB", "date": "Date"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(trend.tail(60), use_container_width=True, hide_index=True)
