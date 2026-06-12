"""Shared Insights tab — analytics unlocked by the Jun-11 consolidated extracts.

These columns (booked revenue, exporter, industry, state, MAX_OPEN_DPD, Plaid/PG flags)
existed in neither original dashboard; the visuals follow each leader's framing:
revenue & mix for steering, aging & ops flags for action. Respects the sidebar AM filter.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard_metrics import OPEN_STAGES, get_window
from ui_helpers import (
    INDIGO,
    MUTED,
    NEGATIVE,
    POSITIVE,
    WARNING,
    base_layout,
    donut,
    fmt_money,
    metric_cards,
    section_header,
    show_table,
)

AGING_BANDS = [
    ("Current (0)", lambda d: d <= 0, POSITIVE),
    ("1-7", lambda d: (d > 0) & (d <= 7), INDIGO),
    ("8-30", lambda d: (d > 7) & (d <= 30), WARNING),
    ("31-90", lambda d: (d > 30) & (d <= 90), "#f97316"),
    (">90 (NPA)", lambda d: d > 90, NEGATIVE),
]


def _monthly_revenue(invoices: pd.DataFrame, months: int, today: pd.Timestamp) -> pd.DataFrame:
    rev = invoices[invoices["disbursed_date"].notna() & (invoices["booked_revenue"] > 0)].copy()
    if rev.empty:
        return pd.DataFrame(columns=["month", "booked_revenue"])
    rev["month"] = rev["disbursed_date"].dt.to_period("M").dt.to_timestamp()
    cutoff = (today - pd.DateOffset(months=months)).to_period("M").to_timestamp()
    rev = rev[rev["month"] >= cutoff]
    return rev.groupby("month", as_index=False)["booked_revenue"].sum()


def render_insights(accounts: pd.DataFrame, invoices: pd.DataFrame, today: pd.Timestamp, cfg) -> None:
    open_inv = invoices[invoices["Stage"].isin(OPEN_STAGES)]
    month_start, _ = get_window("mtd", today)

    # ---- Revenue ------------------------------------------------------------
    section_header("Revenue", "Booked revenue per invoice, attributed to its advance month")
    rev_12m = _monthly_revenue(invoices, 12, today)
    mtd_rev = invoices[
        invoices["disbursed_date"].notna() & invoices["disbursed_date"].between(month_start, today)
    ]["booked_revenue"].sum()
    expected_open = (open_inv["expected_interest"] + open_inv["expected_fees"]).sum()
    overdue_interest = invoices["overdue_interest"].sum()
    metric_cards(
        [
            ("Booked Revenue (12m)", fmt_money(rev_12m["booked_revenue"].sum()), "", POSITIVE),
            ("Booked Revenue (MTD)", fmt_money(mtd_rev), "advances this month", POSITIVE),
            ("Expected on Open Book", fmt_money(expected_open), "interest + factoring fees", INDIGO),
            ("Overdue Interest (all time)", fmt_money(overdue_interest), "", WARNING),
        ],
    )

    c1, c2 = st.columns(2)
    with c1:
        if not rev_12m.empty:
            fig = go.Figure(go.Bar(x=rev_12m["month"], y=rev_12m["booked_revenue"], marker_color=POSITIVE))
            fig.update_yaxes(tickprefix="$")
            st.plotly_chart(base_layout(fig, "Booked Revenue by Month (12m)"), use_container_width=True)
        else:
            st.info("No booked revenue in the last 12 months for this selection.")
    with c2:
        by_am = (
            invoices[invoices["booked_revenue"] > 0]
            .groupby("am")["booked_revenue"].sum()
            .reindex(cfg.ams).dropna()
        )
        if not by_am.empty:
            fig = go.Figure(go.Bar(
                x=[am.split()[0] for am in by_am.index], y=by_am.values, marker_color=INDIGO,
            ))
            fig.update_yaxes(tickprefix="$")
            st.plotly_chart(base_layout(fig, "Booked Revenue by AM (all time)"), use_container_width=True)
        else:
            st.info("No revenue by AM for this selection.")

    # ---- Portfolio mix ------------------------------------------------------
    section_header("Portfolio Mix", "Current OB by industry and state")
    c1, c2 = st.columns(2)
    with c1:
        mix = accounts.groupby("industry")["ob"].sum().sort_values(ascending=False).head(10)
        if mix.sum() > 0:
            fig = go.Figure(go.Bar(x=mix.values, y=mix.index, orientation="h", marker_color=INDIGO))
            fig.update_xaxes(tickprefix="$")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(base_layout(fig, "OB by Industry (top 10)", height=420), use_container_width=True)
        else:
            st.info("No OB to break down by industry.")
    with c2:
        geo = accounts.groupby("state")["ob"].sum().sort_values(ascending=False).head(10)
        if geo.sum() > 0:
            fig = go.Figure(go.Bar(x=geo.values, y=geo.index, orientation="h", marker_color=MUTED))
            fig.update_xaxes(tickprefix="$")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(base_layout(fig, "OB by State (top 10)", height=420), use_container_width=True)
        else:
            st.info("No OB to break down by state.")

    # ---- Supplier concentration ---------------------------------------------
    section_header("Supplier Concentration", "Open outstanding by exporter — single-supplier dependency risk")
    sup = (
        open_inv.groupby(["exporter", "exporter_country"])
        .agg(outstanding=("Outstanding", "sum"), invoices=("Invoice ID", "size"),
             buyers=("account_id", "nunique"))
        .sort_values("outstanding", ascending=False)
        .head(15)
        .reset_index()
    )
    if not sup.empty and sup["outstanding"].sum() > 0:
        total_open = open_inv["Outstanding"].sum()
        sup["share"] = sup["outstanding"] / total_open if total_open > 0 else 0
        show_table(sup, ["exporter", "exporter_country", "outstanding", "share", "invoices", "buyers"], height=380)
    else:
        st.caption("No open outstanding for this selection.")

    # ---- Account DPD aging ---------------------------------------------------
    section_header("Account Risk Aging", "Worst open DPD per account (master MAX_OPEN_DPD)")
    cols = st.columns(len(AGING_BANDS))
    for col, (label, predicate, color) in zip(cols, AGING_BANDS):
        subset = accounts[predicate(accounts["max_open_dpd"].fillna(0)) & (accounts["ob"] > 0)]
        with col:
            metric_cards([(label, f"{len(subset):,}", fmt_money(subset["ob"].sum()) + " OB", color)], columns=1)
    risky = accounts[(accounts["max_open_dpd"] > 7) & (accounts["ob"] > 0)].copy()
    if not risky.empty:
        show_table(
            risky.sort_values("max_open_dpd", ascending=False),
            ["company", "am", "ob", "max_open_dpd", "max_dpd", "raw_status", "industry"],
            height=320,
        )

    # ---- Ops flags -----------------------------------------------------------
    section_header("Operational Flags", "Connectivity and guarantee coverage")
    active = accounts[accounts["util_status"] == "active"]
    broken_plaid = active[active["plaid_status"].str.contains("Inactive|Broken", case=False, na=False)]
    not_integrated = active[active["plaid_status"] == "Not Integrated"]
    pg_yes = accounts[accounts["pg_status"] == "Yes"]
    c1, c2 = st.columns([1, 1.3])
    with c1:
        plaid_counts = accounts["plaid_status"].replace("", "Unknown").value_counts()
        st.plotly_chart(
            donut(plaid_counts.index.tolist(), plaid_counts.values.tolist(),
                  [POSITIVE, MUTED, NEGATIVE, WARNING][: len(plaid_counts)], "Plaid Status (all accounts)"),
            use_container_width=True,
        )
    with c2:
        metric_cards(
            [
                ("Active w/ Broken Plaid", f"{len(broken_plaid):,}", fmt_money(broken_plaid['ob'].sum()) + " OB at stake", NEGATIVE),
                ("Active, Not Integrated", f"{len(not_integrated):,}", "", WARNING),
                ("Personal Guarantee = Yes", f"{len(pg_yes):,}", f"of {len(accounts):,} accounts", INDIGO),
            ],
            columns=1,
        )
        if not broken_plaid.empty:
            with st.expander(f"Broken-Plaid active accounts — {len(broken_plaid)}"):
                show_table(broken_plaid.sort_values("ob", ascending=False),
                           ["company", "am", "ob", "plaid_status", "bdm"], height=260)
