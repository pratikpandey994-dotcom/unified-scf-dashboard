"""Team Pankit views, ported 1:1 from the original '75% Utilization Engine' React dashboard.

Every tab is traceable to docs/PANKIT_DASHBOARD_SPEC.md. Account metrics are derived live
from the Excel files (the original embedded a precomputed snapshot); utilization here uses
facility only (no overdraft), per the original and the 2026-06-10 decision.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard_metrics import (
    PANKIT_AM_COLORS,
    get_window,
    is_workable,
    ob_trend,
    utilization_buckets_pankit,
    weighted_irr,
)
from ui_helpers import (
    ACCENT_PANKIT,
    MUTED,
    NEGATIVE,
    POSITIVE,
    WARNING,
    base_layout,
    fmt_irr,
    fmt_money,
    fmt_pct,
    metric_cards,
    section_header,
    show_table,
    export_portfolio_report,
)

BUCKET_COLORS = ["#ef4444", "#f97316", "#f59e0b", "#3b82f6", "#10b981", "#8b5cf6"]


def _am_perf(accounts: pd.DataFrame, invoices: pd.DataFrame, cfg) -> pd.DataFrame:
    rows = []
    for am in cfg.ams:
        sub = accounts[accounts["am"] == am]
        inv = invoices[invoices["am"] == am] if not invoices.empty else invoices
        funded = sub[sub["facility"] > 0]
        rows.append({
            "am": am,
            "accounts": len(sub),
            "facility": sub["facility"].sum(),
            "ob": sub["ob"].sum(),
            # Original: simple mean of per-account utilization over facility>0 accounts (NOT OB-weighted).
            "avg_utilization": funded["utilization_pct"].mean() if len(funded) else 0,
            "zero_ob": int((sub["ob"] < 1).sum()),
            "inactive": int(sub["raw_status"].astype(str).str.contains("Inactive", case=False, na=False).sum()),
            "repayments": sub["mtd_repayments"].sum(),
            "originations": inv["Origination"].sum() if not inv.empty and "Origination" in inv else 0,
            "wirr": weighted_irr(sub),
        })
    return pd.DataFrame(rows)


def kpi_header(accounts: pd.DataFrame) -> None:
    """Light-theme replica of the original 10-card Pankit KPI grid."""
    workable = accounts[is_workable(accounts)]
    active = accounts[accounts["raw_status"] == "Workable - Active"]
    inactive = accounts[accounts["raw_status"].astype(str).str.contains("Inactive", case=False, na=False)]
    zero_ob = accounts[accounts["ob"] < 1]
    total_fac = accounts["facility"].sum()
    total_ob = accounts["ob"].sum()
    total_rep = accounts["mtd_repayments"].sum()
    util = total_ob / total_fac * 100 if total_fac > 0 else 0
    inact_12m = inactive[inactive["days_since_last"].fillna(999) <= 365]
    metric_cards(
        [
            ("Total Workable Accounts", f"{len(workable):,}", "", ACCENT_PANKIT),
            ("Active Accounts", f"{len(active):,}", "", POSITIVE),
            ("Inactive Accounts", f"{len(inactive):,}", "", "#f59e0b"),
            ("Zero-OB Accounts", f"{len(zero_ob):,}", "", NEGATIVE),
            ("Total Facility Size", fmt_money(total_fac), "", "#8b5cf6"),
            ("Total Outstanding OB", fmt_money(total_ob), "", ACCENT_PANKIT),
            ("Portfolio Utilization", f"{util:.1f}%", "", POSITIVE if util >= 75 else "#f59e0b"),
            ("Net OB (OB - Repayments)", fmt_money(total_ob - total_rep), "", MUTED),
            ("MTD Repayments", fmt_money(total_rep), "", POSITIVE),
            ("Inactive w/ Last 12 Mo", f"{len(inact_12m):,}", "Reactivation targets", "#fb923c"),
        ],
        columns=5,
    )


def render_inventory(accounts: pd.DataFrame) -> None:
    active = accounts[accounts["raw_status"] == "Workable - Active"]
    inactive = accounts[accounts["raw_status"].astype(str).str.contains("Inactive", case=False, na=False)]
    c = st.columns(5)
    c[0].metric("Showing Accounts", f"{len(accounts):,}")
    c[1].metric("Active", f"{len(active):,}")
    c[2].metric("Inactive", f"{len(inactive):,}")
    c[3].metric("Total Facility", fmt_money(accounts["facility"].sum()))
    c[4].metric("Total OB", fmt_money(accounts["ob"].sum()))
    show_table(accounts.sort_values("facility", ascending=False),
               ["company", "am", "facility", "ob", "mtd_repayments", "net_ob", "utilization_pct", "raw_status"], height=520)


def render_utilization(accounts: pd.DataFrame, cfg) -> None:
    funded = accounts[accounts["facility"] > 0]
    util = funded["utilization"] * 100
    c = st.columns(4)
    c[0].metric("Avg Utilization", f"{util.mean():.1f}%" if len(funded) else "-")
    c[1].metric("≥ 75% Utilized", f"{int((util >= 75).sum()):,}")
    c[2].metric("< 50% Utilized", f"{int(((util < 50) & (util > 0)).sum()):,}")
    c[3].metric("< 25% Utilized", f"{int(((util < 25) & (util > 0)).sum()):,}")

    c1, c2 = st.columns(2)
    with c1:
        buckets = utilization_buckets_pankit(funded)
        fig = go.Figure(go.Bar(x=buckets["Bucket"], y=buckets["Accounts"], marker_color=BUCKET_COLORS,
                               text=buckets["Accounts"], textposition="outside"))
        st.plotly_chart(base_layout(fig, "Utilization Distribution"), use_container_width=True)
    with c2:
        rows = []
        for am in cfg.ams:
            sub = funded[funded["am"] == am]
            rows.append({"am": am.split()[0], "avg": sub["utilization_pct"].mean() if len(sub) else 0,
                         "color": PANKIT_AM_COLORS.get(am, MUTED)})
        by_am = pd.DataFrame(rows)
        fig = go.Figure(go.Bar(x=by_am["am"], y=by_am["avg"], marker_color=by_am["color"]))
        fig.add_hline(y=75, line_dash="dash", line_color=POSITIVE, annotation_text="75% Target")
        fig.update_yaxes(ticksuffix="%")
        st.plotly_chart(base_layout(fig, "AM-wise Avg Utilization"), use_container_width=True)

    show_table(funded.sort_values("utilization", ascending=False),
               ["company", "am", "facility", "ob", "utilization_pct", "raw_status"], height=420)


def render_zero_ob(accounts: pd.DataFrame) -> None:
    zero_rows = accounts[accounts["ob"] < 1].copy()
    high_facility = zero_rows[zero_rows["facility"] >= 500_000]
    recently_active = zero_rows[(zero_rows["ob_30d"] > 0) | (zero_rows["days_since_last"].fillna(9999) <= 90)]
    c = st.columns(4)
    c[0].metric("Zero-OB Accounts", f"{len(zero_rows):,}")
    c[1].metric("High Facility (≥$500K)", f"{len(high_facility):,}", "Priority reactivation", delta_color="off")
    c[2].metric("Recently Active (<90d)", f"{len(recently_active):,}")
    c[3].metric("Total Dormant Facility", fmt_money(zero_rows["facility"].sum()))
    st.caption("🔴 High Facility + Zero OB = priority flag · 🟡 Recently active but now dormant")
    show_table(zero_rows.sort_values("facility", ascending=False),
               ["company", "am", "facility", "ob", "last_disbursed", "days_since_last", "ob_30d", "raw_status"], height=460)


def render_workable_inactive(accounts_team: pd.DataFrame, selected_am: str) -> None:
    # Original tab 4 ignores the status filter and applies only the AM filter.
    base = accounts_team if selected_am == "All" else accounts_team[accounts_team["am"] == selected_am]
    inactive = base[
        base["raw_status"].astype(str).str.contains("Inactive|Temporarily suspended", case=False, na=False)
        & (base["days_since_last"].fillna(9999) <= 365)
    ].copy()
    inactive["months_since_last"] = (inactive["days_since_last"].fillna(0) / 30.4).round(1)
    c = st.columns(3)
    c[0].metric("Workable Inactive (≤12 mo)", f"{len(inactive):,}", "Primary reactivation pipeline", delta_color="off")
    c[1].metric("Total Facility Available", fmt_money(inactive["facility"].sum()))
    c[2].metric("Total Gap to 75%", fmt_money(inactive["gap_to_75"].sum()))
    show_table(inactive.sort_values("facility", ascending=False),
               ["company", "am", "facility", "last_disbursed", "months_since_last", "gap_to_75", "raw_status"], height=440)


def render_repayments(accounts: pd.DataFrame, cfg, selected_am: str) -> None:
    with_repay = accounts[accounts["mtd_repayments"] > 0].sort_values("mtd_repayments", ascending=False)
    cards = st.columns(2 + len(cfg.ams))
    cards[0].metric("Total MTD Repayments", fmt_money(with_repay["mtd_repayments"].sum()))
    cards[1].metric("Accounts with Repayments", f"{len(with_repay):,}")
    for idx, am in enumerate(cfg.ams):
        if selected_am not in ("All", am):
            continue
        amt = accounts.loc[accounts["am"] == am, "mtd_repayments"].sum()
        cards[2 + idx].metric(f"{am.split()[0]} Repayments", fmt_money(amt))
    show_table(with_repay, ["company", "am", "ob_30d", "mtd_repayments", "ob", "net_ob"], height=440)


def render_ob_dent(accounts: pd.DataFrame, ob_pivot: pd.DataFrame, accounts_team: pd.DataFrame) -> None:
    valid = accounts[(accounts["ob"] > 0) | (accounts["ob_30d"] > 0)].copy()
    reduced_30 = valid[valid["ob_dent_30d"] > 0]
    reduced_90 = valid[valid["ob_dent_90d"] > 0]
    flagged = valid[(valid["ob_dent_30d_pct"] > 0.25) | (valid["ob_dent_30d"] > 100_000)]
    c = st.columns(5)
    c[0].metric("Total Facility (shown)", fmt_money(valid["facility"].sum()))
    c[1].metric("OB Reduced in 30d", f"{len(reduced_30):,}")
    c[2].metric("OB Reduced in 90d", f"{len(reduced_90):,}")
    c[3].metric("Total 30d OB Reduction", fmt_money(reduced_30["ob_dent_30d"].sum()))
    c[4].metric("Recovery Candidates", f"{len(flagged):,}", ">25% dent or >$100K", delta_color="off")

    trend = ob_trend(ob_pivot, set(accounts_team["id"]))
    if not trend.empty:
        recent = trend.tail(180)
        fig = go.Figure(go.Scatter(x=recent["date"], y=recent["ob"], mode="lines",
                                   line=dict(color=ACCENT_PANKIT, width=2.5)))
        fig.add_hline(y=recent["ob"].iloc[-1], line_dash="dash", line_color=POSITIVE,
                      annotation_text=f"Today {fmt_money(recent['ob'].iloc[-1])}")
        fig.update_yaxes(tickprefix="$")
        st.plotly_chart(base_layout(fig, "Portfolio OB Movement — 180 Day Window"), use_container_width=True)
    st.caption("🎯 Opportunity flag: OB dent >25% or >$100K = recovery conversation")
    show_table(valid.sort_values("ob_dent_30d", ascending=False),
               ["company", "am", "ob_30d", "ob", "ob_dent_30d", "ob_dent_30d_pct_display", "raw_status"], height=420)


def render_am_performance(accounts_team: pd.DataFrame, invoices_team: pd.DataFrame, cfg) -> None:
    st.caption("AM Performance is leader-level: it ignores the AM/status filters (matches the original).")
    perf = _am_perf(accounts_team, invoices_team, cfg)
    grid = st.columns(2)
    for idx, row in perf.iterrows():
        with grid[int(idx) % 2]:
            with st.container(border=True):
                st.markdown(f"**● {row['am']}**")
                t = st.columns(4)
                t[0].metric("Accounts", f"{row['accounts']:,}")
                t[1].metric("Facility", fmt_money(row["facility"]))
                t[2].metric("OB", fmt_money(row["ob"]))
                t[3].metric("Avg Util", f"{row['avg_utilization']:.1f}%")
                t = st.columns(4)
                t[0].metric("Zero OB", f"{row['zero_ob']:,}")
                t[1].metric("Inactive", f"{row['inactive']:,}")
                t[2].metric("MTD Repay", fmt_money(row["repayments"]))
                t[3].metric("Total Orig.", fmt_money(row["originations"]))
    section_header("AM Comparison Table")
    display = perf.sort_values("ob", ascending=False).copy()
    display["wirr"] = display["wirr"].map(fmt_irr)
    st.dataframe(display, use_container_width=True, hide_index=True,
                 column_config={
                     "facility": st.column_config.NumberColumn("Facility", format="$ %.0f"),
                     "ob": st.column_config.NumberColumn("OB", format="$ %.0f"),
                     "avg_utilization": st.column_config.NumberColumn("Avg Util %", format="%.1f%%"),
                     "repayments": st.column_config.NumberColumn("Repayments", format="$ %.0f"),
                     "originations": st.column_config.NumberColumn("Total Originations", format="$ %.0f"),
                 })


def render_75_engine(accounts: pd.DataFrame) -> None:
    opps = accounts[(accounts["gap_to_75"] > 0) & (accounts["facility"] > 0) & is_workable(accounts)].copy()
    c = st.columns(3)
    c[0].metric("Opportunity Accounts", f"{len(opps):,}", "Below 75% utilization", delta_color="off")
    c[1].metric("Total Gap to 75%", fmt_money(opps["gap_to_75"].sum()), "Potential incremental OB", delta_color="off")
    c[2].metric("Avg Current Utilization", fmt_pct(opps["utilization"].mean() if len(opps) else 0))
    st.info("💡 Formula: Gap to 75% = (Facility × 75%) − Current OB")
    show_table(opps.sort_values("gap_to_75", ascending=False),
               ["company", "am", "facility", "ob", "target_ob_75", "utilization_pct", "gap_to_75", "last_disbursed", "raw_status"],
               height=460)


def render_opportunity_views(accounts_team: pd.DataFrame, selected_am: str, cfg) -> None:
    by_am = accounts_team if selected_am == "All" else accounts_team[accounts_team["am"] == selected_am]

    st.markdown("#### 🏆 Top 20 Utilization Opportunities")
    st.caption("Largest dollar gap to 75% across the whole division (ignores filters, like the original).")
    top_gap = accounts_team[(accounts_team["gap_to_75"] > 0) & is_workable(accounts_team)]
    show_table(top_gap.sort_values("gap_to_75", ascending=False).head(20),
               ["company", "am", "facility", "ob", "utilization_pct", "gap_to_75"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ⚠️ Not Funded in 90+ Days")
        dormant = by_am[by_am["days_since_last"].fillna(0) >= 90]
        show_table(dormant.sort_values("days_since_last", ascending=False),
                   ["company", "am", "facility", "ob", "days_since_last", "raw_status"], height=380)
    with c2:
        st.markdown("#### 🎯 High Facility / Low Utilization")
        st.caption("Facility ≥ $500K with utilization < 30%")
        big_low = by_am[(by_am["facility"] >= 500_000) & (by_am["utilization"] < 0.30)]
        show_table(big_low.sort_values("facility", ascending=False),
                   ["company", "am", "facility", "ob", "utilization_pct", "gap_to_75"], height=380)

    st.markdown("#### 📊 AM Opportunity Ranking")
    ranking = []
    for am in cfg.ams:
        sub = accounts_team[accounts_team["am"] == am]
        am_opps = sub[(sub["gap_to_75"] > 0) & is_workable(sub)]
        funded = sub[sub["facility"] > 0]
        ranking.append({
            "am": am,
            "opportunity_accounts": len(am_opps),
            "total_gap": am_opps["gap_to_75"].sum(),
            "avg_utilization": funded["utilization_pct"].mean() if len(funded) else 0,
        })
    st.dataframe(pd.DataFrame(ranking).sort_values("total_gap", ascending=False),
                 use_container_width=True, hide_index=True,
                 column_config={
                     "total_gap": st.column_config.NumberColumn("Total Gap to 75%", format="$ %.0f"),
                     "avg_utilization": st.column_config.NumberColumn("Avg Util %", format="%.1f%%"),
                 })


# ---------------------------------------------------------------- View Executive ----
def render_executive(accounts: pd.DataFrame, accounts_team: pd.DataFrame, invoices_team: pd.DataFrame,
                     ob_pivot: pd.DataFrame, cfg) -> None:
    st.caption("Executive view is leader-level: it uses the whole division regardless of the AM/status filters (matches the original).")

    st.download_button(
        label="📥 Export Portfolio Report (Excel)",
        data=export_portfolio_report(accounts_team),
        file_name="pankit_portfolio_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="pan_portfolio_export",
    )

    kpi_header(accounts_team)

    c1, c2 = st.columns(2)
    with c1:
        trend = ob_trend(ob_pivot, set(accounts_team["id"]))
        if not trend.empty:
            recent = trend.tail(90)
            fig = go.Figure(go.Scatter(x=recent["date"], y=recent["ob"], mode="lines", name="OB",
                                       line=dict(color=ACCENT_PANKIT, width=2)))
            fig.add_hline(y=recent["ob"].iloc[-1], line_dash="dash", line_color=POSITIVE,
                          annotation_text=f"Today {fmt_money(recent['ob'].iloc[-1])}")
            fig.update_yaxes(tickprefix="$")
            st.plotly_chart(base_layout(fig, "Portfolio OB Trend (last 90 days, invoice-derived)"), use_container_width=True)
            st.caption("Invoice-derived OB (advance basis): origination held from advance to settlement.")
        else:
            st.info("No invoice history available to derive the trend.")
    with c2:
        perf = _am_perf(accounts_team, invoices_team, cfg)
        fig = go.Figure(go.Bar(
            x=[am.split()[0] for am in perf["am"]], y=perf["repayments"], name="Repayments",
            marker_color=[PANKIT_AM_COLORS.get(am, MUTED) for am in perf["am"]],
        ))
        fig.update_yaxes(tickprefix="$")
        st.plotly_chart(base_layout(fig, "MTD Repayments by AM"), use_container_width=True)

    section_header("AM Portfolio Snapshot")
    perf = _am_perf(accounts_team, invoices_team, cfg).sort_values("ob", ascending=False)
    display = perf.copy()
    display["wirr"] = display["wirr"].map(fmt_irr)
    st.dataframe(
        display,
        use_container_width=True, hide_index=True,
        column_config={
            "facility": st.column_config.NumberColumn("Total Facility", format="$ %.0f"),
            "ob": st.column_config.NumberColumn("Total OB", format="$ %.0f"),
            "avg_utilization": st.column_config.NumberColumn("Avg Util %", format="%.1f%%"),
            "repayments": st.column_config.NumberColumn("MTD Repayments", format="$ %.0f"),
            "originations": st.column_config.NumberColumn("Total Originations", format="$ %.0f"),
        },
    )
