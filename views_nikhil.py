"""Team Nikhil views, ported 1:1 from the original 'CP Pod · SCF Portfolio Dashboard' HTML.

Every section is traceable to docs/NIKHIL_DASHBOARD_SPEC.md (View F/A/B/C/D/H/P/G/T).
Charts keep the originals' series colors and groupings on the app's light theme.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard_metrics import (
    CURRENT_OB_CUTOFF,
    EXCLUDED_STAGES,
    IN_TARGET_TYPES,
    NIKHIL_AM_COLORS,
    OPEN_STAGES,
    REPAYMENT_STAGES,
    SETTLED,
    account_risk_category,
    due_by_account,
    get_window,
    in_target,
    ob_trend,
    ob_trend_by_am,
    originations_by_account,
    repayments_by_account,
    risk_kpis,
    utilization_buckets_nikhil,
    weighted_irr,
    cp_universe,
    health_scores,
)
from ui_helpers import (
    ACCENT_NIKHIL,
    INDIGO,
    MUTED,
    NEGATIVE,
    POSITIVE,
    WARNING,
    base_layout,
    donut,
    fmt_irr,
    fmt_money,
    fmt_pct,
    grouped_bar,
    metric_cards,
    section_header,
    show_table,
    export_portfolio_report,
)

TRACKER_PATH = Path(__file__).parent / "tracker_state.json"

WINDOW_LABELS = {"cw": "Current Week", "nw": "Next Week", "cm": "Current Month", "nm": "Next Month"}


def _company_map(accounts: pd.DataFrame) -> pd.DataFrame:
    return accounts[["id", "company", "am", "account_type"]].rename(columns={"id": "account_id"})


def _series_table(accounts: pd.DataFrame, series: pd.Series, value_name: str) -> pd.DataFrame:
    frame = accounts.copy()
    frame[value_name] = frame["id"].map(series).fillna(0)
    return frame


# ---------------------------------------------------------------- View F ----
def render_snapshot(accounts: pd.DataFrame, invoices: pd.DataFrame) -> None:
    target = in_target(accounts)
    total_ob = target["ob"].sum()
    total_fac = target["util_denom"].sum()

    st.markdown("##### Portfolio Scale — in-target (Active + Suspended Workable) only")
    c = st.columns(4)
    c[0].metric("Total OB", fmt_money(total_ob))
    c[1].metric("Total Facility", fmt_money(total_fac))
    c[2].metric("Portfolio Utilization", fmt_pct(total_ob / total_fac if total_fac > 0 else 0))
    wa_count = int((accounts["broad_status"] == "Workable").sum())
    c[3].metric("Total Accounts", f"{len(accounts):,}", f"{wa_count} Workable · {len(accounts) - wa_count} NWA", delta_color="off")

    st.markdown("##### Account Health")
    days = accounts["days_since_last"].fillna(99999)
    tiles = [
        ("Active Workable · IN TARGET", accounts["account_type"] == "Active Workable"),
        ("Suspended Workable · IN TARGET", accounts["account_type"] == "Suspended Workable"),
        ("Workable >365d · EXCL.", accounts["account_type"] == "Workable >365"),
        ("Non-Workable", accounts["account_type"] == "NWA"),
        ("NW >365d", (accounts["account_type"] == "NWA") & (days > 365)),
        ("NW ≤365d", (accounts["account_type"] == "NWA") & (days <= 365)),
    ]
    cols = st.columns(6)
    for col, (label, mask) in zip(cols, tiles):
        subset = accounts[mask]
        col.metric(label, f"{len(subset):,}", f"{fmt_money(subset['ob'].sum())} OB · {fmt_money(subset['util_denom'].sum())} Fac", delta_color="off")

    st.markdown("##### Yield (OB-weighted signed-up IRR)")
    c = st.columns(3)
    c[0].metric("Portfolio WIRR (in target)", fmt_irr(weighted_irr(target)))
    c[1].metric("Active WIRR", fmt_irr(weighted_irr(target[target["account_type"] == "Active Workable"])))
    c[2].metric("Suspended WIRR", fmt_irr(weighted_irr(target[target["account_type"] == "Suspended Workable"])))

    st.markdown("##### Risk")
    risk = risk_kpis(target, invoices)
    c = st.columns(4)
    c[0].metric("Overdue OB (DPD 8-90)", fmt_money(risk["overdue_ob"]), f"{risk['overdue_count']} invoices", delta_color="off")
    c[1].metric("NPA OB (DPD >90)", fmt_money(risk["npa_ob"]), f"{risk['npa_count']} invoices", delta_color="off")
    c[2].metric("Clean OB", fmt_money(risk["clean_ob"]))
    c[3].metric("Clean %", fmt_pct(risk["clean_pct"]))


# Polished light-theme replica of the original snapshot tile structure. This
# intentionally overrides the first direct port above while preserving formulas.
def render_snapshot(accounts: pd.DataFrame, invoices: pd.DataFrame) -> None:
    target = in_target(accounts)
    total_ob = target["ob"].sum()
    total_fac = target["util_denom"].sum()

    section_header("Portfolio Scale", "In-target Active + Suspended Workable accounts")
    wa_count = int((accounts["broad_status"] == "Workable").sum())
    metric_cards(
        [
            ("Total OB", fmt_money(total_ob), "", ACCENT_NIKHIL),
            ("Total Facility", fmt_money(total_fac), "Facility + overdraft", INDIGO),
            ("Portfolio Utilization", fmt_pct(total_ob / total_fac if total_fac > 0 else 0), "", POSITIVE),
            ("Total Accounts", f"{len(accounts):,}", f"{wa_count} Workable / {len(accounts) - wa_count} NWA", MUTED),
        ],
        columns=4,
    )

    section_header("Account Health", "Original six-tile CP pod split")
    days = accounts["days_since_last"].fillna(99999)
    tile_specs = [
        ("Active Workable / IN TARGET", accounts["account_type"] == "Active Workable", POSITIVE),
        ("Suspended Workable / IN TARGET", accounts["account_type"] == "Suspended Workable", WARNING),
        ("Workable >365d / EXCL.", accounts["account_type"] == "Workable >365", MUTED),
        ("Non-Workable", accounts["account_type"] == "NWA", MUTED),
        ("NW >365d", (accounts["account_type"] == "NWA") & (days > 365), MUTED),
        ("NW <=365d", (accounts["account_type"] == "NWA") & (days <= 365), MUTED),
    ]
    health_cards = []
    for label, mask, color in tile_specs:
        subset = accounts[mask]
        health_cards.append(
            (label, f"{len(subset):,}", f"{fmt_money(subset['ob'].sum())} OB / {fmt_money(subset['util_denom'].sum())} Fac", color)
        )
    metric_cards(health_cards, columns=3)

    section_header("Yield", "OB-weighted signed-up IRR")
    metric_cards(
        [
            ("Portfolio WIRR", fmt_irr(weighted_irr(target)), "In target", ACCENT_NIKHIL),
            ("Active WIRR", fmt_irr(weighted_irr(target[target["account_type"] == "Active Workable"])), "", POSITIVE),
            ("Suspended WIRR", fmt_irr(weighted_irr(target[target["account_type"] == "Suspended Workable"])), "", WARNING),
        ],
        columns=3,
    )

    section_header("Risk", "DPD 8-90 overdue and DPD >90 NPA")
    risk = risk_kpis(target, invoices)
    metric_cards(
        [
            ("Overdue OB (DPD 8-90)", fmt_money(risk["overdue_ob"]), f"{risk['overdue_count']} invoices", WARNING),
            ("NPA OB (DPD >90)", fmt_money(risk["npa_ob"]), f"{risk['npa_count']} invoices", NEGATIVE),
            ("Clean OB", fmt_money(risk["clean_ob"]), "", POSITIVE),
            ("Clean %", fmt_pct(risk["clean_pct"]), "", POSITIVE),
        ],
        columns=4,
    )


# ---------------------------------------------------------------- View A ----
def render_portfolio(accounts: pd.DataFrame, invoices: pd.DataFrame, invoices_team: pd.DataFrame,
                     ob_pivot: pd.DataFrame, today: pd.Timestamp, cfg) -> None:
    target = in_target(accounts)
    total_ob = target["ob"].sum()
    risk = risk_kpis(target, invoices)

    st.markdown("#### Portfolio Quality")
    excel_data = export_portfolio_report(target)
    st.download_button(label="📥 Export Portfolio Report (Excel)", data=excel_data, file_name="nikhil_portfolio_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.metric("Clean OB", fmt_money(risk["clean_ob"]), fmt_pct(risk["clean_pct"]) + " of portfolio", delta_color="off")
        st.metric("Overdue OB (DPD 8-90)", fmt_money(risk["overdue_ob"]), f"{risk['overdue_count']} invoices", delta_color="off")
        st.metric("NPA OB (DPD >90)", fmt_money(risk["npa_ob"]), f"{risk['npa_count']} invoices", delta_color="off")
        st.plotly_chart(
            donut(["Clean", "Overdue", "NPA"], [risk["clean_ob"], risk["overdue_ob"], risk["npa_ob"]],
                  [POSITIVE, WARNING, NEGATIVE], "Portfolio Quality ($)"),
            use_container_width=True,
        )
    with c2:
        pq = target.copy()
        pq["quality"] = account_risk_category(pq, invoices)
        pq_filter = st.selectbox("Quality filter", ["all", "clean", "overdue", "npa"], key="nik_pq_filter")
        if pq_filter != "all":
            pq = pq[pq["quality"] == pq_filter]
        show_table(pq.sort_values("ob", ascending=False),
                   ["company", "am", "account_type", "quality", "util_denom", "ob", "utilization_pct", "irr"], height=420)

    st.markdown("#### Weighted IRR")
    thresh = st.number_input("Only accounts with OB ≥", min_value=0, step=1000, value=0, key="nik_irr_thresh")
    c = st.columns(3)
    c[0].metric("Portfolio WIRR", fmt_irr(weighted_irr(target, thresh)))
    c[1].metric("Active", fmt_irr(weighted_irr(target[target["account_type"] == "Active Workable"], thresh)))
    c[2].metric("Suspended", fmt_irr(weighted_irr(target[target["account_type"] == "Suspended Workable"], thresh)))

    st.markdown("#### Targetable Portfolio")
    panels = [
        ("🟢 Active Workable — IN TARGET", "Active Workable"),
        ("🟠 Suspended Workable — IN TARGET", "Suspended Workable"),
        ("⏸ Workable >365d — NOT IN TARGET", "Workable >365"),
        ("⛔ Non-Workable — NWA", "NWA"),
    ]
    cols = st.columns(4)
    for col, (label, level) in zip(cols, panels):
        subset = accounts[accounts["account_type"] == level]
        fac = subset["util_denom"].sum()
        ob = subset["ob"].sum()
        col.markdown(f"**{label}**")
        col.metric("Accounts", f"{len(subset):,}")
        col.metric("Total Facility", fmt_money(fac))
        col.metric("OB", fmt_money(ob), fmt_pct(ob / fac if fac > 0 else 0) + " util", delta_color="off")

    st.markdown("#### OB Movement per AM (current OB file window)")
    if not ob_pivot.empty:
        current = ob_pivot[ob_pivot.index >= CURRENT_OB_CUTOFF]
        movers = accounts[~accounts["account_type"].isin({"NWA", "Workable >365"})]
        if not current.empty and not movers.empty:
            cols_present = [c_ for c_ in current.columns if c_ in set(movers["id"])]
            start = current[cols_present].iloc[0]
            end = current[cols_present].iloc[-1]
            move = movers[movers["id"].isin(cols_present)].copy()
            move["ob_start"] = move["id"].map(start)
            move["ob_end"] = move["id"].map(end)
            per_am = move.groupby("am")[["ob_start", "ob_end"]].sum().reindex(cfg.ams).dropna()
            fig = grouped_bar(
                list(per_am.index),
                {"OB Start": (per_am["ob_start"].tolist(), "rgba(148,163,184,.7)"),
                 "OB End": (per_am["ob_end"].tolist(), ACCENT_NIKHIL)},
                f"OB Start vs End ({current.index.min():%d %b} → {current.index.max():%d %b})",
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Upload OB files to enable OB movement.")

    st.markdown("#### Origination vs Repayment")
    win = st.radio("Window", ["MTD", "QTD", "Custom"], horizontal=True, key="nik_ovr_win")
    if win == "Custom":
        d1, d2 = st.columns(2)
        start = pd.Timestamp(d1.date_input("From", value=today.replace(day=1), key="nik_ovr_from"))
        end = pd.Timestamp(d2.date_input("To", value=today, key="nik_ovr_to"))
    else:
        start, end = get_window(win.lower(), today)
    orig = originations_by_account(invoices, start, end)
    repaid = repayments_by_account(invoices, start, end)
    rows = []
    for am in cfg.ams:
        ids = set(accounts.loc[accounts["am"] == am, "id"])
        o = orig[orig.index.isin(ids)].sum()
        r = repaid[repaid.index.isin(ids)].sum()
        rows.append({"am": am.split()[0], "Originated": o, "Repaid": r, "Net": o - r})
    rows.append({"am": "Team", "Originated": sum(r["Originated"] for r in rows), "Repaid": sum(r["Repaid"] for r in rows), "Net": sum(r["Net"] for r in rows)})
    ovr = pd.DataFrame(rows)
    fig = go.Figure()
    fig.add_bar(x=ovr["am"], y=ovr["Originated"], name="Originated", marker_color=INDIGO)
    fig.add_bar(x=ovr["am"], y=ovr["Repaid"], name="Repaid", marker_color=POSITIVE)
    fig.add_bar(x=ovr["am"], y=ovr["Net"], name="Net", marker_color=[ACCENT_NIKHIL if v >= 0 else NEGATIVE for v in ovr["Net"]])
    fig.update_layout(barmode="group")
    fig.update_yaxes(tickprefix="$")
    st.plotly_chart(base_layout(fig, f"Origination vs Repayment ({start:%d %b} – {end:%d %b})"), use_container_width=True)

    st.markdown("#### Collections Tracker (independent of the AM filter above)")
    chip = st.radio("Scope", ["Portfolio"] + cfg.ams, horizontal=True, key="nik_coll_am")
    inv = invoices_team if chip == "Portfolio" else invoices_team[invoices_team["am"] == chip]
    month_start, _ = get_window("mtd", today)
    received = inv[
        inv["Stage"].isin(SETTLED) & inv["settlement_date"].notna() & inv["settlement_date"].between(month_start, today)
    ]
    received_amt = (received["Origination"] - received["Outstanding"]).clip(lower=0).sum()
    recovery = inv[inv["Stage"].isin({"overdue", "npa"})]
    recovery_amt = (recovery["Origination"] - recovery["Outstanding"]).clip(lower=0).sum()

    to_win = st.radio("To-receive window", list(WINDOW_LABELS), format_func=WINDOW_LABELS.get, horizontal=True, key="nik_coll_win")
    w_start, w_end = get_window(to_win, today)
    due = inv[inv["Stage"].isin({"advanced", "partial"}) & inv["due_date_of_invoice"].notna() & inv["due_date_of_invoice"].between(w_start, w_end)]
    c = st.columns(3)
    c[0].metric("✅ Received MTD (principal repaid)", fmt_money(received_amt), f"{len(received)} invoices", delta_color="off")
    c[1].metric(f"⏳ To Receive — {WINDOW_LABELS[to_win]}", fmt_money(due["Outstanding"].sum()), f"{len(due)} invoices", delta_color="off")
    c[2].metric("⚠ Recovery Collections (overdue/NPA repaid)", fmt_money(recovery_amt))
    if not due.empty:
        detail = (
            due.groupby("Buyer")
            .agg(invoices=("Outstanding", "size"), total_due=("Outstanding", "sum"),
                 first_due=("due_date_of_invoice", "min"), last_due=("due_date_of_invoice", "max"))
            .sort_values("total_due", ascending=False)
            .reset_index()
        )
        with st.expander(f"To-receive detail — {len(detail)} companies"):
            st.dataframe(detail, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------- View B ----
def render_team(accounts: pd.DataFrame, invoices: pd.DataFrame, today: pd.Timestamp, cfg) -> None:
    month_start, _ = get_window("mtd", today)
    visible_ams = [am for am in cfg.ams if am in set(accounts["am"])]
    st.markdown("#### AM Scorecards")
    cols = st.columns(max(len(visible_ams), 1))
    for col, am in zip(cols, visible_ams):
        sub = accounts[accounts["am"] == am]
        sub_target = in_target(sub)
        inv = invoices[invoices["am"] == am]
        aw = sub[sub["account_type"] == "Active Workable"]
        sw = sub[sub["account_type"] == "Suspended Workable"]
        mtd_orig = originations_by_account(inv, month_start, today).sum()
        mtd_rep = repayments_by_account(inv, month_start, today).sum()
        early = inv[
            inv["Stage"].isin(SETTLED)
            & inv["settlement_date"].notna() & inv["due_date_of_invoice"].notna()
            & (inv["settlement_date"] < inv["due_date_of_invoice"])
        ]
        early_mtd = early[early["settlement_date"].between(month_start, today)]["Origination"].sum()
        with col:
            st.markdown(f"**{am}**")
            st.metric("Active WA", f"{len(aw)}", f"{fmt_money(aw['ob'].sum())} OB", delta_color="off")
            st.metric("Suspended WA", f"{len(sw)}", f"{fmt_money(sw['ob'].sum())} OB", delta_color="off")
            st.metric("MTD Originated", fmt_money(mtd_orig))
            st.metric("MTD Repaid", fmt_money(mtd_rep))
            st.metric("Early Repayment MTD", fmt_money(early_mtd))
            st.metric("WIRR", fmt_irr(weighted_irr(sub_target)))

    st.markdown("#### AM Status Distribution")
    levels = [("Active Workable", POSITIVE), ("Suspended Workable", WARNING), ("Workable >365", "rgba(71,85,105,.55)"), ("NWA", "rgba(71,85,105,.3)")]
    fig = go.Figure()
    first_names = [am.split()[0] for am in visible_ams]
    for level, color in levels:
        counts = [int(((accounts["am"] == am) & (accounts["account_type"] == level)).sum()) for am in visible_ams]
        fig.add_bar(x=first_names, y=counts, name=level, marker_color=color)
    fig.update_layout(barmode="stack")
    st.plotly_chart(base_layout(fig, "Accounts by status per AM"), use_container_width=True)


# ---------------------------------------------------------------- View C ----
def render_health(accounts: pd.DataFrame, invoices: pd.DataFrame) -> None:
    target = in_target(accounts)
    buckets = utilization_buckets_nikhil(target)

    st.markdown("#### Utilization Buckets (in-target accounts)")
    c1, c2 = st.columns([1, 1])
    with c1:
        colors = [MUTED, ACCENT_NIKHIL, INDIGO, POSITIVE]
        st.plotly_chart(donut(buckets["Bucket"].tolist(), buckets["OB"].tolist(), colors, "OB by utilization bucket"), use_container_width=True)
    with c2:
        fig = go.Figure(go.Bar(
            y=buckets["Bucket"], x=[v if v is not None else 0 for v in buckets["WIRR"]],
            orientation="h", marker_color=colors,
            text=[fmt_irr(v) for v in buckets["WIRR"]], textposition="outside",
        ))
        fig.update_xaxes(ticksuffix="%")
        st.plotly_chart(base_layout(fig, "Weighted IRR by bucket (OB > 0)"), use_container_width=True)
    show_table(buckets.assign(WIRR=buckets["WIRR"].map(fmt_irr)))

    pick = st.selectbox("Bucket detail", ["All"] + buckets["Bucket"].tolist(), key="nik_bucket_pick")
    detail = target.copy()
    util = np.where(detail["util_denom"] > 0, (detail["ob"] / detail["util_denom"]).clip(0, 1), 0)
    detail["bucket"] = pd.cut(pd.Series(util, index=detail.index), [-1, 0, 0.40, 0.74, 1.01],
                              labels=buckets["Bucket"].tolist())
    if pick != "All":
        detail = detail[detail["bucket"] == pick]
    show_table(detail.sort_values("ob", ascending=False),
               ["company", "am", "account_type", "util_denom", "ob", "utilization_pct", "irr"], height=360)

    open_inv = invoices[invoices["Stage"].isin(OPEN_STAGES)] if not invoices.empty else invoices
    for title, mask_fn in [
        ("Overdue (DPD 8-90)", lambda f: (f["dpd"] > 7) & (f["dpd"] <= 90)),
        ("NPA (DPD >90)", lambda f: f["dpd"] > 90),
    ]:
        st.markdown(f"#### {title}")
        section = open_inv[mask_fn(open_inv)].copy() if not open_inv.empty else open_inv
        if section.empty:
            st.caption("No invoices in this band.")
            continue
        section["recovered"] = (section["Origination"] - section["Outstanding"]).clip(lower=0)
        no_pay = section[section["recovered"] <= 0]
        partial = section[section["recovered"] > 0]
        c = st.columns(3)
        c[0].metric("Total Stuck", fmt_money(section["Outstanding"].sum()), f"{len(section)} invoices", delta_color="off")
        c[1].metric("No Payment Received", fmt_money(no_pay["Outstanding"].sum()))
        c[2].metric("Partially Paid — Still Owed", fmt_money(partial["Outstanding"].sum()),
                    f"{fmt_money(partial['recovered'].sum())} recovered", delta_color="off")
        ordered = pd.concat([partial.sort_values("dpd", ascending=False), no_pay.sort_values("dpd", ascending=False)])
        with st.expander(f"{title} detail — {len(ordered)} invoices"):
            st.dataframe(
                ordered[["Buyer", "am", "Invoice ID", "Stage", "Origination", "Outstanding", "recovered", "dpd"]],
                use_container_width=True, hide_index=True,
            )

    st.markdown("#### Days Since Last Disbursement")
    universe = accounts[accounts["account_type"].isin(IN_TARGET_TYPES | {"Workable >365"})].copy()
    bucket = st.selectbox("Days bucket", ["all", "0-30", "31-60", "61-90", "91-120", "121-150", "151-180", "180+"], key="nik_dsld")
    days = universe["days_since_last"].fillna(-1)
    if bucket == "180+":
        universe = universe[days >= 180]
    elif bucket != "all":
        lo, hi = bucket.split("-")
        universe = universe[days.between(int(lo), int(hi))]
    show_table(universe.sort_values("days_since_last", ascending=False),
               ["company", "am", "account_type", "util_denom", "ob", "last_disbursed", "days_since_last"], height=360)


# ---------------------------------------------------------------- View D ----
def render_actions(accounts: pd.DataFrame, invoices: pd.DataFrame, master_raw: pd.DataFrame, today: pd.Timestamp) -> None:
    st.markdown("#### Declining Accounts (repaid > originated in window)")
    win = st.radio("Window", ["MTD", "QTD", "Custom"], horizontal=True, key="nik_dec_win")
    if win == "Custom":
        d1, d2 = st.columns(2)
        start = pd.Timestamp(d1.date_input("From", value=today.replace(day=1), key="nik_dec_from"))
        end = pd.Timestamp(d2.date_input("To", value=today, key="nik_dec_to"))
    else:
        start, end = get_window(win.lower(), today)
    movers = accounts[~accounts["account_type"].isin({"NWA", "Workable >365"})]
    inv = invoices[invoices["account_id"].isin(set(movers["id"]))]
    orig = originations_by_account(inv, start, end)
    repaid = repayments_by_account(inv, start, end)
    flows = pd.DataFrame({"orig": orig, "repaid": repaid}).fillna(0)
    flows["net"] = flows["orig"] - flows["repaid"]
    declining = flows[flows["repaid"] > flows["orig"]].sort_values("net")
    if declining.empty:
        st.caption("No declining accounts in this window.")
    else:
        decl = declining.join(movers.set_index("id")[["company", "am"]])
        top = decl.head(15)
        fig = go.Figure(go.Bar(y=top["company"], x=top["net"], orientation="h",
                               marker_color=[NEGATIVE if v < 0 else POSITIVE for v in top["net"]]))
        fig.update_xaxes(tickprefix="$")
        st.plotly_chart(base_layout(fig, f"Top declining ({start:%d %b} – {end:%d %b})", height=420), use_container_width=True)
        with st.expander(f"Declining detail — {len(decl)} accounts"):
            st.dataframe(decl.reset_index(names="account_id"), use_container_width=True, hide_index=True)

    st.markdown("#### High Opportunity (headroom + upcoming due)")
    opp_win = st.radio("Due window", list(WINDOW_LABELS), format_func=WINDOW_LABELS.get, horizontal=True, key="nik_opp_win")
    w_start, w_end = get_window(opp_win, today)
    due = due_by_account(invoices, w_start, w_end)
    target = in_target(accounts).copy()
    target["headroom"] = (target["util_denom"] - target["ob"]).clip(lower=0)
    target["due_in_window"] = target["id"].map(due).fillna(0)
    target["opportunity"] = target["headroom"] + target["due_in_window"]
    opp = target[target["opportunity"] > 0].sort_values("opportunity", ascending=False)
    show_table(opp, ["company", "am", "account_type", "util_denom", "ob", "headroom", "due_in_window", "opportunity"], height=360)

    st.markdown("#### Early Repayment Tracking")
    early = invoices[
        invoices["Stage"].isin(SETTLED)
        & invoices["settlement_date"].notna() & invoices["due_date_of_invoice"].notna()
        & (invoices["settlement_date"] < invoices["due_date_of_invoice"])
    ].copy()
    if early.empty:
        st.caption("No early repayments found.")
    else:
        early["days_early"] = (early["due_date_of_invoice"] - early["settlement_date"]).dt.days
        early = early.sort_values("days_early", ascending=False).head(300)
        with st.expander(f"Early repayments — showing {len(early)} (cap 300)"):
            st.dataframe(early[["Buyer", "am", "Invoice ID", "Origination", "settlement_date", "due_date_of_invoice", "days_early"]],
                         use_container_width=True, hide_index=True)

    st.markdown("#### Recovery Collections Detail")
    recovery = invoices[invoices["Stage"].isin(OPEN_STAGES) & (invoices["dpd"] > 7)].copy()
    recovery["recovered"] = (recovery["Origination"] - recovery["Outstanding"]).clip(lower=0)
    recovery = recovery[recovery["recovered"] > 0]
    if recovery.empty:
        st.caption("No recovery collections.")
    else:
        agg = (
            recovery.groupby("Buyer")
            .agg(invoices=("recovered", "size"), origination=("Origination", "sum"),
                 outstanding=("Outstanding", "sum"), recovered=("recovered", "sum"), max_dpd=("dpd", "max"))
            .sort_values("recovered", ascending=False)
            .reset_index()
        )
        st.dataframe(agg, use_container_width=True, hide_index=True)
        st.caption(f"Total recovered: {fmt_money(agg['recovered'].sum())} across {int(agg['invoices'].sum())} invoices")

    st.markdown("#### Reactivation Focus (workable, suspended, dormant ≥180d — sorted by Peak OB)")
    react = accounts[
        (accounts["broad_status"] == "Workable")
        & (accounts["util_status"] == "suspended")
        & (accounts["days_since_last"].fillna(0) >= 180)
    ]
    show_table(react.sort_values("peak_ob", ascending=False),
               ["company", "am", "util_denom", "ob", "peak_ob", "peak_ob_date", "days_since_last"], height=320)

    st.markdown("#### Alerts — Unassigned CP Accounts")
    if not master_raw.empty:
        unassigned = master_raw[
            (master_raw["Team"].astype(str).str.strip() == "CP")
            & (master_raw["utilization_status"].astype(str).str.strip() == "active")
            & master_raw["First_Disbursed_Date"].notna()
            & (master_raw["AM"].isna() | (master_raw["AM"].astype(str).str.strip().isin(["", "nan"])))
        ]
        if unassigned.empty:
            st.caption("No unassigned active CP accounts. ✅")
        else:
            st.warning(f"{len(unassigned)} active CP account(s) without an AM")
            st.dataframe(unassigned[["Buyer", "Partner", "First_Disbursed_Date", "OB"]],
                         use_container_width=True, hide_index=True)


# ---------------------------------------------------------------- View H ----
def render_pulse(accounts: pd.DataFrame, invoices: pd.DataFrame, today: pd.Timestamp) -> None:
    target = in_target(accounts).copy()

    st.markdown("#### Repayments Due")
    cols = st.columns(3)
    dues = {}
    for col, win in zip(cols, ["cw", "cm", "nm"]):
        w_start, w_end = get_window(win, today)
        series = due_by_account(invoices, w_start, w_end)
        dues[win] = series
        col.metric(f"Due — {WINDOW_LABELS[win]}", fmt_money(series.sum()), f"{int((series > 0).sum())} accounts", delta_color="off")
    due_win = st.radio("Show due column for", list(WINDOW_LABELS)[:1] + ["cm", "nm"],
                       format_func=lambda k: WINDOW_LABELS[k], horizontal=True, key="nik_pulse_due")
    target["due_window"] = target["id"].map(dues.get(due_win, pd.Series(dtype=float))).fillna(0)

    st.markdown("#### Workable Accounts")
    s1, s2 = st.columns(2)
    sort_by = s1.radio("Sort by", ["Facility", "OB", "Utilization"], horizontal=True, key="nik_pulse_sort")
    slice_pick = s2.radio("Slice", ["Top 10", "Top 25", "Top 50", "All", "Bottom 25"], horizontal=True, index=2, key="nik_pulse_slice")
    sort_col = {"Facility": "util_denom", "OB": "ob", "Utilization": "utilization"}[sort_by]
    ordered = target.sort_values(sort_col, ascending=False)
    if slice_pick.startswith("Top"):
        ordered = ordered.head(int(slice_pick.split()[1]))
    elif slice_pick.startswith("Bottom"):
        ordered = ordered.tail(int(slice_pick.split()[1])).iloc[::-1]
    ordered = ordered.copy()
    ordered["ob_chg_30d"] = ordered["ob"] - ordered["ob_30d"]
    show_table(ordered, ["company", "am", "account_type", "util_denom", "ob", "utilization_pct",
                         "ob_chg_30d", "due_window", "last_disbursed", "peak_ob", "peak_ob_date", "avg_ob"], height=480)

    st.markdown("#### About to Go Inactive (Active WA, ≥120 days since disbursement)")
    inactive_soon = accounts[(accounts["account_type"] == "Active Workable") & (accounts["days_since_last"].fillna(0) >= 120)]
    c = st.columns(3)
    c[0].metric("Accounts", f"{len(inactive_soon):,}")
    c[1].metric("OB at risk", fmt_money(inactive_soon["ob"].sum()))
    c[2].metric("Facility at risk", fmt_money(inactive_soon["util_denom"].sum()))
    show_table(inactive_soon.sort_values("days_since_last", ascending=False),
               ["company", "am", "util_denom", "ob", "utilization_pct", "last_disbursed", "days_since_last"], height=280)

    st.markdown("#### Headroom Opportunity (recently active, <120 days)")
    headroom = target[(target["days_since_last"].isna()) | (target["days_since_last"] < 120)].copy()
    headroom["headroom"] = (headroom["util_denom"] - headroom["ob"]).clip(lower=0)
    headroom["peak_gap"] = (headroom["peak_ob"] - headroom["ob"]).clip(lower=0)
    headroom = headroom[headroom["headroom"] > 0].sort_values("headroom", ascending=False)
    show_table(headroom, ["company", "am", "util_denom", "ob", "utilization_pct", "headroom", "peak_ob", "peak_gap"], height=320)

    st.markdown("#### Repayment Tracker")
    rep_win = st.radio("Window", ["WTD", "MTD"], horizontal=True, key="nik_pulse_rep")
    w_start, _ = get_window("cw" if rep_win == "WTD" else "mtd", today)
    repaid = repayments_by_account(invoices, w_start, today)
    rep_table = _series_table(target, repaid, "repaid")
    rep_table = rep_table[rep_table["repaid"] > 0].sort_values("repaid", ascending=False)
    c = st.columns(3)
    c[0].metric(f"Total Repaid {rep_win}", fmt_money(rep_table["repaid"].sum()))
    c[1].metric("Accounts with repayment", f"{len(rep_table):,}")
    c[2].metric("Avg per account", fmt_money(rep_table["repaid"].mean() if len(rep_table) else 0))
    st.dataframe(rep_table[["company", "am", "repaid", "ob"]], use_container_width=True, hide_index=True)

    st.markdown("#### Origination — Month to Date")
    m_start, _ = get_window("mtd", today)
    orig = originations_by_account(invoices, m_start, today)
    orig_table = _series_table(target, orig, "originated")
    orig_table = orig_table[orig_table["originated"] > 0].sort_values("originated", ascending=False)
    c = st.columns(3)
    c[0].metric("Total Originated MTD", fmt_money(orig_table["originated"].sum()))
    c[1].metric("Accounts with origination", f"{len(orig_table):,}")
    c[2].metric("Avg per account", fmt_money(orig_table["originated"].mean() if len(orig_table) else 0))
    st.dataframe(orig_table[["company", "am", "originated", "ob"]], use_container_width=True, hide_index=True)

    st.markdown("#### OB Drop")
    d30, d90 = st.columns(2)
    for col, col_name, label in [(d30, "ob_30d", "30 days"), (d90, "ob_90d", "90 days")]:
        drop = target[target[col_name] > target["ob"]].copy()
        drop["drop"] = drop[col_name] - drop["ob"]
        drop["drop_pct"] = drop["drop"] / drop[col_name] * 100
        with col:
            st.markdown(f"**Drop vs {label} ago** — {fmt_money(drop['drop'].sum())}")
            st.dataframe(drop.sort_values("drop", ascending=False)[["company", "am", col_name, "ob", "drop", "drop_pct"]],
                         use_container_width=True, hide_index=True, height=300)


# ---------------------------------------------------------------- View P ----
def render_peak(accounts: pd.DataFrame, invoices: pd.DataFrame, ob_pivot: pd.DataFrame, today: pd.Timestamp) -> None:
    if ob_pivot.empty:
        st.info("Upload historical/current OB files to enable peak analysis.")
        return
    ids = set(accounts["id"])
    trend = ob_trend(ob_pivot, ids)

    st.markdown("#### OB Trend")
    t1, t2 = st.columns(2)
    mode = t1.radio("Mode", ["Portfolio Total", "Per AM"], horizontal=True, key="nik_peak_mode")
    window = t2.radio("Window", ["3M", "6M", "12M", "All history"], horizontal=True, index=2, key="nik_peak_window")
    months = {"3M": 3, "6M": 6, "12M": 12}.get(window)
    start_date = today - pd.DateOffset(months=months) if months else trend["date"].min()
    fig = go.Figure()
    if mode == "Portfolio Total":
        view = trend[trend["date"] >= start_date]
        fig.add_scatter(x=view["date"], y=view["ob"], mode="lines", name="Portfolio OB",
                        line=dict(color=ACCENT_NIKHIL, width=2), fill="tozeroy", fillcolor="rgba(245,158,11,.10)")
    else:
        per_am = ob_trend_by_am(ob_pivot, accounts)
        per_am = per_am[per_am["date"] >= start_date]
        for am, group in per_am.groupby("am"):
            fig.add_scatter(x=group["date"], y=group["ob"], mode="lines", name=am,
                            line=dict(color=NIKHIL_AM_COLORS.get(am, MUTED), width=2))
    fig.update_yaxes(tickprefix="$")
    st.plotly_chart(base_layout(fig, "Daily OB"), use_container_width=True)
    st.caption("Historic OB coverage starts 2023-01-01; current file covers May 2026 onward.")

    st.markdown("#### Peak vs Today")
    peak_mode = st.radio("Peak date", ["Auto (max)", "Custom"], horizontal=True, key="nik_peak_pick")
    daily_totals = ob_pivot[[c for c in ob_pivot.columns if c in ids]].sum(axis=1)
    if peak_mode == "Custom":
        chosen = pd.Timestamp(st.date_input("Pick date", value=daily_totals.idxmax().date(), key="nik_peak_date"))
        eligible = daily_totals.index[daily_totals.index <= chosen]
        peak_date = eligible.max() if len(eligible) else daily_totals.idxmax()
    else:
        peak_date = daily_totals.idxmax()
    peak_ob = daily_totals.loc[peak_date]
    today_ob = accounts["ob"].sum()  # ALL pod accounts (WA + NWA), per the HTML
    net = today_ob - peak_ob
    c = st.columns(3)
    c[0].metric(f"Peak Portfolio OB ({peak_date:%d %b %Y})", fmt_money(peak_ob))
    c[1].metric("Today's Portfolio OB", fmt_money(today_ob))
    c[2].metric("Net Movement", fmt_money(net), f"{net / peak_ob * 100:+.1f}%" if peak_ob else "-")

    snap = ob_pivot.loc[peak_date]
    change = accounts.copy()
    change["ob_peak"] = change["id"].map(snap).fillna(0)
    change["change"] = change["ob"] - change["ob_peak"]
    change = change[(change["ob_peak"] > 0) | (change["ob"] > 0)]
    is_wa = change["account_type"].isin(IN_TARGET_TYPES)

    open_inv = invoices[invoices["Stage"].isin(OPEN_STAGES)] if not invoices.empty else invoices
    npa_ids = set(open_inv.loc[open_inv["dpd"] > 90, "account_id"]) if not open_inv.empty else set()
    over_ids = set(open_inv.loc[(open_inv["dpd"] > 7) & (open_inv["dpd"] <= 90), "account_id"]) if not open_inv.empty else set()

    def zero_category(row) -> str:
        if row["id"] in npa_ids:
            return "npa"
        if row["id"] in over_ids:
            return "overdue"
        if row["account_type"] in {"NWA", "Workable >365"}:
            return "nwa"
        if row["util_status"] == "active":
            return "active0"
        return "suspended"

    change["status"] = np.select(
        [(change["ob_peak"] > 0) & (change["ob"] == 0), change["change"] < 0, change["change"] > 0],
        ["zero", "declined", "grew"], default="unchanged",
    )
    change["category"] = change.apply(zero_category, axis=1)

    wa = change[is_wa]
    nwa = change[~is_wa]
    c = st.columns(4)
    c[0].metric("WA Net (peak → today)", fmt_money(wa["change"].sum()),
                f"{int((wa['status'] == 'grew').sum())} grew · {int(wa['status'].isin(['declined', 'zero']).sum())} declined", delta_color="off")
    c[1].metric("NWA Residual OB", fmt_money(nwa.loc[nwa["ob"] > 0, "ob"].sum()), f"{int((nwa['ob'] > 0).sum())} accounts", delta_color="off")
    c[2].metric("NWA Structural Loss", fmt_money(nwa.loc[(nwa["ob_peak"] > 0) & (nwa["ob"] == 0), "ob_peak"].sum()),
                f"{int(((nwa['ob_peak'] > 0) & (nwa['ob'] == 0)).sum())} accounts went to $0", delta_color="off")
    c[3].metric("Gross Growth / Decline",
                f"+{fmt_money(wa.loc[wa['change'] > 0, 'change'].sum())}",
                f"-{fmt_money(abs(wa.loc[wa['status'].isin(['declined', 'zero']), 'change'].sum()))}", delta_color="off")

    st.markdown("#### Contribution Waterfall (top 40 by |change|)")
    moves = change[(change["change"] != 0) & ~((~is_wa) & (change["ob"] > 0))]
    top = moves.reindex(moves["change"].abs().sort_values(ascending=False).index).head(40).sort_values("change")
    bar_colors = ["rgba(71,85,105,.45)" if t not in IN_TARGET_TYPES else (NEGATIVE if v < 0 else POSITIVE)
                  for t, v in zip(top["account_type"], top["change"])]
    fig = go.Figure(go.Bar(y=top["company"], x=top["change"], orientation="h", marker_color=bar_colors))
    fig.update_xaxes(tickprefix="$")
    st.plotly_chart(base_layout(fig, "Peak → Today change per account", height=720), use_container_width=True)

    st.markdown("#### Account Detail")
    cat = st.selectbox("Filter", ["all", "wa", "nwa", "declined", "grew", "zero", "active0", "npa", "overdue", "suspended"], key="nik_peak_cat")
    detail = change
    if cat == "wa":
        detail = change[is_wa]
    elif cat == "nwa":
        detail = change[~is_wa]
    elif cat in {"declined", "grew", "zero"}:
        detail = change[change["status"] == cat]
    elif cat in {"active0", "npa", "overdue", "suspended"}:
        detail = change[(change["status"] == "zero") & (change["category"] == cat)]
    show_table(detail.sort_values("change"),
               ["company", "am", "account_type", "status", "category", "ob_peak", "ob", "change"], height=420)


# ---------------------------------------------------------------- View G ----
def render_cp_health(accounts_all: pd.DataFrame, invoices_all: pd.DataFrame, today: pd.Timestamp) -> None:
    st.caption("CP Health covers ALL CP-partner accounts (Team = CP, Partner ≠ Direct) across every AM — it intentionally ignores the team/AM filters, exactly like the original View G.")
    cp = cp_universe(accounts_all)
    if cp.empty:
        st.info("No CP accounts available.")
        return
    cp_invoices = invoices_all[invoices_all["account_id"].isin(set(cp["id"]))]
    cp["health_score"] = health_scores(cp, cp_invoices, today)

    fac = cp["total_facility"].sum()
    ob = cp["ob"].sum()
    c = st.columns(4)
    c[0].metric("Total CP Accounts", f"{len(cp):,}")
    c[1].metric("Total CP OB", fmt_money(ob))
    c[2].metric("Total CP Facility", fmt_money(fac))
    c[3].metric("CP Utilization", fmt_pct(ob / fac if fac else 0))

    by_partner = (
        cp.groupby("partner")
        .agg(accounts=("id", "count"), ob=("ob", "sum"), facility=("total_facility", "sum"),
             score=("health_score", "mean"))
        .sort_values("ob", ascending=False)
    )
    wirrs = {p: weighted_irr(g[g["ob"] > 0]) for p, g in cp.groupby("partner")}
    by_partner["wirr"] = by_partner.index.map(wirrs)
    labels = [p.replace("_", " ") for p in by_partner.head(20).index]

    fig = go.Figure()
    fig.add_bar(y=labels, x=by_partner.head(20)["facility"].tolist(), name="Total Facility", marker_color="rgba(148,163,184,.55)", orientation="h")
    fig.add_bar(y=labels, x=by_partner.head(20)["ob"].tolist(), name="OB", marker_color=ACCENT_NIKHIL, marker_opacity=0.85, orientation="h")
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(tickprefix="$")
    st.plotly_chart(base_layout(fig, "OB & Facility by Partner (top 20)", height=560), use_container_width=True)

    open_inv = cp_invoices[cp_invoices["Stage"].isin(OPEN_STAGES)].copy()
    if not open_inv.empty:
        partner_map = cp.set_index("id")["partner"]
        open_inv["partner"] = open_inv["account_id"].map(partner_map)
        risk = pd.DataFrame({
            "overdue": open_inv[(open_inv["dpd"] > 7) & (open_inv["dpd"] <= 90)].groupby("partner")["Outstanding"].sum(),
            "npa": open_inv[open_inv["dpd"] > 90].groupby("partner")["Outstanding"].sum(),
        }).fillna(0)
        risk = risk[(risk["overdue"] + risk["npa"]) > 0].sort_values(by=["npa", "overdue"], ascending=False)
        if not risk.empty:
            fig = go.Figure()
            fig.add_bar(y=[p.replace("_", " ") for p in risk.index], x=risk["overdue"], name="Overdue (DPD 8-90)", orientation="h", marker_color=WARNING)
            fig.add_bar(y=[p.replace("_", " ") for p in risk.index], x=risk["npa"], name="NPA (DPD >90)", orientation="h", marker_color=NEGATIVE)
            fig.update_layout(barmode="stack")
            fig.update_xaxes(tickprefix="$")
            st.plotly_chart(base_layout(fig, "Risk by Partner"), use_container_width=True)

    wirr_data = by_partner[by_partner["wirr"].notna() & (by_partner["wirr"] > 0)].sort_values("wirr", ascending=False)
    if not wirr_data.empty:
        colors = [POSITIVE if v >= 20 else (ACCENT_NIKHIL if v >= 18 else NEGATIVE) for v in wirr_data["wirr"]]
        fig = go.Figure(go.Bar(y=[p.replace("_", " ") for p in wirr_data.index], x=wirr_data["wirr"], orientation="h", marker_color=colors))
        fig.update_xaxes(ticksuffix="%")
        st.plotly_chart(base_layout(fig, "Weighted IRR by Partner (green ≥20, amber ≥18)", height=520), use_container_width=True)

    st.markdown("#### Partner Health Scorecard")
    partner_pick = st.selectbox("Partner", ["All"] + by_partner.index.tolist(), key="nik_cp_partner",
                                format_func=lambda p: p.replace("_", " "))
    detail = cp if partner_pick == "All" else cp[cp["partner"] == partner_pick]
    show_table(detail.sort_values("health_score", ascending=False),
               ["partner", "company", "am", "total_facility", "ob", "utilization_pct", "irr", "health_score"], height=480)


# ---------------------------------------------------------------- View T ----
def _load_tracker() -> dict:
    if TRACKER_PATH.exists():
        try:
            return json.loads(TRACKER_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_tracker(state: dict) -> None:
    TRACKER_PATH.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


TRACKER_STATUSES = ["No Update", "In Progress", "Escalated", "Done", "Waiting"]


def render_tracker(accounts: pd.DataFrame, invoices: pd.DataFrame, today: pd.Timestamp, cfg) -> None:
    mode = st.radio("Tracker view", ["Focus View", "Manager Overview"], horizontal=True, key="nik_tracker_mode")
    month_start, _ = get_window("mtd", today)

    open_inv = invoices[invoices["Stage"].isin(OPEN_STAGES)] if not invoices.empty else invoices
    risk_ids = set(open_inv.loc[open_inv["dpd"] > 7, "account_id"]) if not open_inv.empty else set()
    mtd_orig = originations_by_account(invoices, month_start, today)
    mtd_rep = repayments_by_account(invoices, month_start, today)

    def buckets_for(sub: pd.DataFrame) -> dict[str, pd.DataFrame]:
        sub_inv = invoices[invoices["account_id"].isin(set(sub["id"]))]
        wa = in_target(sub)
        out: dict[str, pd.DataFrame] = {}
        out["🔴 Overdue / NPA"] = wa[wa["id"].isin(risk_ids)]
        for win, label in [("cw", "🟡 Repayment Due — This Week"), ("nw", "🟡 Repayment Due — Next Week"), ("nm", "🟡 Repayment Due — Next Month")]:
            w_start, w_end = get_window(win, today)
            due = due_by_account(sub_inv, w_start, w_end)
            out[label] = wa[wa["id"].isin(due[due > 0].index)]
        orig_s = wa["id"].map(mtd_orig).fillna(0)
        rep_s = wa["id"].map(mtd_rep).fillna(0)
        out["🟠 Net Negative MTD"] = wa[(wa["account_type"] == "Active Workable") & (rep_s > orig_s) & (rep_s > 0)]
        out["🟣 Suspended — Still Repaying"] = wa[(wa["account_type"] == "Suspended Workable") & (rep_s > 0)]
        out["⚠ Approaching Inactive (90-119d)"] = wa[wa["days_since_last"].fillna(0).between(90, 119)]
        return out

    if mode == "Manager Overview":
        rows = []
        for am in cfg.ams:
            sub = accounts[accounts["am"] == am]
            b = buckets_for(sub)
            rows.append({
                "AM": am,
                "Overdue/NPA": len(b["🔴 Overdue / NPA"]),
                "Due this week": len(b["🟡 Repayment Due — This Week"]),
                "Net negative MTD": len(b["🟠 Net Negative MTD"]),
                "Suspended still repaying": len(b["🟣 Suspended — Still Repaying"]),
                "Approaching inactive": len(b["⚠ Approaching Inactive (90-119d)"]),
                "OB": fmt_money(sub["ob"].sum()),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        return

    am_options = [am for am in cfg.ams if am in set(accounts["am"])]
    if not am_options:
        st.info("No account managers available.")
        return
    selected_am = st.selectbox("Account Manager", am_options, key="nik_tracker_am")
    sub = accounts[accounts["am"] == selected_am]
    state = _load_tracker()

    for label, frame in buckets_for(sub).items():
        if frame.empty:
            continue
        with st.expander(f"{label} — {len(frame)} accounts", expanded=False):
            editable = frame[["company", "ob", "util_denom", "days_since_last"]].copy()
            keys = [f"{selected_am}|{cid}" for cid in frame["id"]]
            editable["Status"] = [state.get(k, {}).get("status", "No Update") for k in keys]
            editable["Comment"] = [state.get(k, {}).get("comment", "") for k in keys]
            editable["Next follow-up"] = [state.get(k, {}).get("nextfu", "") for k in keys]
            edited = st.data_editor(
                editable,
                use_container_width=True,
                hide_index=True,
                disabled=["company", "ob", "util_denom", "days_since_last"],
                column_config={
                    "Status": st.column_config.SelectboxColumn("Status", options=TRACKER_STATUSES),
                    "Comment": st.column_config.TextColumn("Comment"),
                    "Next follow-up": st.column_config.TextColumn("Next follow-up (YYYY-MM-DD)"),
                    "ob": st.column_config.NumberColumn("OB", format="$ %.0f"),
                    "util_denom": st.column_config.NumberColumn("Facility", format="$ %.0f"),
                },
                key=f"nik_tracker_{selected_am}_{label}",
            )
            for k, (_, row) in zip(keys, edited.iterrows()):
                state[k] = {"status": row["Status"], "comment": row["Comment"], "nextfu": row["Next follow-up"]}

    if st.button("💾 Save tracker", key="nik_tracker_save"):
        _save_tracker(state)
        st.success("Tracker saved to tracker_state.json")
