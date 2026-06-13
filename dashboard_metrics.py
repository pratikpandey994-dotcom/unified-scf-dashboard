from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import numpy as np
import pandas as pd


NIKHIL_AMS = ["Nikhil Shetty", "Darshan Hublikar", "Deepsayan Dam", "Ashitha Nair", "Asif Ali"]
PANKIT_AMS = ["Pankit Shah", "Sonal Mishra", "Pejush Hal", "Kaustav Das"]

# AM colors from the original dashboards (index-paired for Nikhil, named for Pankit).
NIKHIL_AM_COLORS = dict(zip(NIKHIL_AMS, ["#f59e0b", "#10b981", "#6366f1", "#f97316", "#94a3b8"]))
PANKIT_AM_COLORS = {
    "Kaustav Das": "#3b82f6",
    "Pejush Hal": "#8b5cf6",
    "Sonal Mishra": "#f59e0b",
    "Pankit Shah": "#10b981",
}

SETTLED = {"closed", "paid", "received"}
REPAYMENT_STAGES = SETTLED | {"partial"}
OPEN_STAGES = {"advanced", "overdue", "npa", "partial"}
EXCLUDED_STAGES = {"partadvanced", "processing", "deposit_pending", "pending_advance", "data_entry", "verify_bank_details", "hold"}

IN_TARGET_TYPES = {"Active Workable", "Suspended Workable"}

# Window (days) for "OB movement" style start-vs-end comparisons on the reconstructed history.
MOVEMENT_WINDOW_DAYS = 30


@dataclass(frozen=True)
class TeamConfig:
    label: str
    leader: str
    ams: list[str]
    scope: str  # "am_only" (Nikhil pod rule) or "direct" (AM list + TYPE == DIRECT)
    include_overdraft: bool  # utilization / 75% denominator includes overdraft?


TEAMS = {
    "Team Nikhil": TeamConfig(
        label="Team Nikhil",
        leader="Nikhil Shetty",
        ams=NIKHIL_AMS,
        scope="am_only",
        include_overdraft=True,
    ),
    "Team Pankit": TeamConfig(
        label="Team Pankit",
        leader="Pankit Shah",
        ams=PANKIT_AMS,
        scope="direct",
        include_overdraft=False,
    ),
}


def _classify_level(broad_status: str, utilization_status: str, days_since: float | None) -> str:
    if str(broad_status).strip() != "Workable":
        return "NWA"
    if days_since is None or pd.isna(days_since) or days_since > 365:
        return "Workable >365"
    if str(utilization_status).strip().casefold() == "active":
        return "Active Workable"
    return "Suspended Workable"


def get_window(kind: str, today: pd.Timestamp) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Date windows as defined in the original HTML (weeks run Monday-Sunday)."""
    today = pd.Timestamp(today).normalize()
    if kind == "mtd":
        return today.replace(day=1), today
    if kind == "qtd":
        quarter_month = (today.month - 1) // 3 * 3 + 1
        return today.replace(month=quarter_month, day=1), today
    if kind == "cw":
        monday = today - timedelta(days=today.dayofweek)
        return monday, monday + timedelta(days=6)
    if kind == "nw":
        monday = today - timedelta(days=today.dayofweek) + timedelta(days=7)
        return monday, monday + timedelta(days=6)
    if kind == "cm":
        start = today.replace(day=1)
        return start, start + pd.offsets.MonthEnd(0)
    if kind == "nm":
        start = today.replace(day=1) + pd.offsets.MonthBegin(1)
        return start, start + pd.offsets.MonthEnd(0)
    raise ValueError(f"Unknown window: {kind}")


def _snapshot_on_or_before(ob_pivot: pd.DataFrame, target: pd.Timestamp) -> pd.Series:
    """OB per account on the latest pivot date <= target (empty Series when none)."""
    if ob_pivot.empty:
        return pd.Series(dtype=float)
    idx = ob_pivot.index
    pos = idx.searchsorted(pd.Timestamp(target), side="right") - 1
    if pos < 0:
        return pd.Series(dtype=float)
    return ob_pivot.iloc[pos]


import streamlit as st

@st.cache_data(show_spinner=False)
def build_portfolio(
    master: pd.DataFrame,
    invoices_raw: pd.DataFrame,
    ob_history: pd.DataFrame,
    today: pd.Timestamp,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Account + invoice frames from the canonical loader output (Jun-11 two-file schema)."""
    today = pd.Timestamp(today)
    accounts = master.copy()
    if accounts.empty:
        return accounts, invoices_raw.iloc[0:0].copy(), pd.DataFrame()

    days = (today - accounts["last_disbursed"]).dt.days
    accounts["days_since_last"] = days.astype("Float64")
    accounts["account_type"] = [
        _classify_level(broad, util, d)
        for broad, util, d in zip(accounts["broad_status"], accounts["util_status"], days)
    ]
    accounts["buyer_lower"] = accounts["company"].astype(str).str.casefold()

    account_ids = set(accounts["id"])
    ob_pivot = pd.DataFrame()
    if not ob_history.empty:
        ob_subset = ob_history[ob_history["importer_user_id"].isin(account_ids)].copy()
        if not ob_subset.empty:
            ob_subset["ob"] = ob_subset["ob"].clip(lower=0)
            ob_subset["date_key"] = ob_subset["ob_date"].dt.normalize()
            ob_pivot = ob_subset.groupby(["date_key", "importer_user_id"])["ob"].last().unstack(fill_value=0)
            ob_pivot = ob_pivot.sort_index()
            accounts["peak_ob"] = accounts["id"].map(ob_pivot.max(axis=0)).fillna(0)
            accounts["peak_ob_date"] = accounts["id"].map(ob_pivot.idxmax(axis=0))
            accounts["avg_ob"] = accounts["id"].map(ob_pivot.replace(0, np.nan).mean(axis=0)).fillna(0)
            snap_30 = _snapshot_on_or_before(ob_pivot, today - timedelta(days=30))
            snap_90 = _snapshot_on_or_before(ob_pivot, today - timedelta(days=90))
            accounts["ob_30d"] = accounts["id"].map(snap_30).fillna(0)
            accounts["ob_90d"] = accounts["id"].map(snap_90).fillna(0)
        else:
            accounts[["peak_ob", "avg_ob", "ob_30d", "ob_90d"]] = 0.0
            accounts["peak_ob_date"] = pd.NaT
    else:
        accounts[["peak_ob", "avg_ob", "ob_30d", "ob_90d"]] = 0.0
        accounts["peak_ob_date"] = pd.NaT

    accounts["ob_dent_30d"] = accounts["ob_30d"] - accounts["ob"]
    accounts["ob_dent_90d"] = accounts["ob_90d"] - accounts["ob"]
    accounts["ob_dent_30d_pct"] = np.where(accounts["ob_30d"] > 0, accounts["ob_dent_30d"] / accounts["ob_30d"], 0)
    accounts["ob_dent_30d_pct_display"] = accounts["ob_dent_30d_pct"] * 100

    # Invoices join by account ID (the Jun-11 extract carries IMPORTER_USER_ID — the old
    # name-based join and its duplicate-company hazard are retired). AM comes from the account.
    acct_index = accounts.set_index("id")
    invoices = invoices_raw[invoices_raw["account_id"].isin(acct_index.index)].copy()
    invoices["am"] = invoices["account_id"].map(acct_index["am"])
    invoices["account_type"] = invoices["account_id"].map(acct_index["account_type"])

    month_start, _ = get_window("mtd", today)
    accounts["mtd_repayments"] = accounts["id"].map(repayments_by_account(invoices, month_start, today)).fillna(0)
    accounts["net_ob"] = accounts["ob"] - accounts["mtd_repayments"]

    return accounts, invoices, ob_pivot


def repayments_by_account(invoices: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Principal repaid per account: max(0, Origination - Outstanding) on settled/partial invoices settled in window."""
    if invoices.empty:
        return pd.Series(dtype=float)
    settled = invoices[
        invoices["Stage"].isin(REPAYMENT_STAGES)
        & invoices["settlement_date"].notna()
        & invoices["settlement_date"].between(start, end)
    ].copy()
    if settled.empty:
        return pd.Series(dtype=float)
    settled["repayment_amount"] = (settled["Origination"] - settled["Outstanding"]).clip(lower=0)
    return settled.groupby("account_id")["repayment_amount"].sum()


def originations_by_account(invoices: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Origination per account for invoices disbursed in window (EXCLUDED stages skipped, per the HTML OVR rule)."""
    if invoices.empty:
        return pd.Series(dtype=float)
    window = invoices[
        ~invoices["Stage"].isin(EXCLUDED_STAGES)
        & invoices["disbursed_date"].notna()
        & invoices["disbursed_date"].between(start, end)
    ]
    if window.empty:
        return pd.Series(dtype=float)
    return window.groupby("account_id")["Origination"].sum()


def due_by_account(invoices: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.Series:
    """Outstanding due per account: advanced/partial invoices with due date in window."""
    if invoices.empty:
        return pd.Series(dtype=float)
    due = invoices[
        invoices["Stage"].isin({"advanced", "partial"})
        & invoices["due_date_of_invoice"].notna()
        & invoices["due_date_of_invoice"].between(start, end)
    ]
    if due.empty:
        return pd.Series(dtype=float)
    return due.groupby("account_id")["Outstanding"].sum()


def filter_team(accounts: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Team segmentation (decisions 2026-06-10, re-mapped to the Jun-11 schema):
    - Team Nikhil: account's AM in the pod AM list. No type filter (HTML pod rule).
    - Team Pankit: account's AM in the team AM list AND TYPE == 'DIRECT'
      (the old Partner=='Direct' rule; the consolidated master carries TYPE instead).
    Then recompute utilization/75% columns with the team's denominator
    (Nikhil: facility + overdraft, Pankit: facility only)."""
    cfg = TEAMS[team_name]
    filtered = accounts[accounts["am"].isin(cfg.ams)]
    if cfg.scope == "direct":
        filtered = filtered[filtered["type"].astype(str).str.upper() == "DIRECT"]
    filtered = filtered.copy()

    denom = filtered["total_facility"] if cfg.include_overdraft else filtered["facility"]
    filtered["util_denom"] = denom
    filtered["utilization"] = np.where(denom > 0, filtered["ob"] / denom, 0.0)
    filtered["utilization_pct"] = filtered["utilization"] * 100
    filtered["target_ob_75"] = denom * 0.75
    filtered["gap_to_75"] = (filtered["target_ob_75"] - filtered["ob"]).clip(lower=0)
    return filtered


def apply_filters(
    accounts: pd.DataFrame,
    am: str,
    account_types: list[str],
    raw_statuses: list[str],
) -> pd.DataFrame:
    filtered = accounts.copy()
    if am != "All":
        filtered = filtered[filtered["am"] == am]
    if account_types:
        filtered = filtered[filtered["account_type"].isin(account_types)]
    if raw_statuses:
        filtered = filtered[filtered["raw_status"].isin(raw_statuses)]
    return filtered


def in_target(accounts: pd.DataFrame) -> pd.DataFrame:
    """Nikhil's 'in target' universe: Active Workable + Suspended Workable."""
    return accounts[accounts["account_type"].isin(IN_TARGET_TYPES)]


def is_workable(accounts: pd.DataFrame) -> pd.Series:
    """Pankit's workable predicate: status starts with 'Workable' (excludes 'Non-Workable')."""
    return accounts["raw_status"].astype(str).str.startswith("Workable")


def weighted_irr(accounts: pd.DataFrame, min_ob: float = 0) -> float | None:
    """OB-weighted signed-up IRR over accounts with ob >= min_ob; None when no OB."""
    eligible = accounts[accounts["ob"] >= min_ob] if min_ob > 0 else accounts
    total_ob = eligible["ob"].sum()
    if total_ob <= 0:
        return None
    return float((eligible["irr"] * eligible["ob"]).sum() / total_ob)


def risk_kpis(target_accounts: pd.DataFrame, invoices: pd.DataFrame) -> dict:
    """Overdue (DPD 8-90), NPA (DPD>90) outstanding over OPEN-stage invoices, and Clean OB."""
    if invoices.empty:
        overdue = npa = invoices
    else:
        open_inv = invoices[invoices["Stage"].isin(OPEN_STAGES)]
        overdue = open_inv[(open_inv["dpd"] > 7) & (open_inv["dpd"] <= 90)]
        npa = open_inv[open_inv["dpd"] > 90]
    total_ob = target_accounts["ob"].sum()
    overdue_ob = overdue["Outstanding"].sum() if not overdue.empty else 0.0
    npa_ob = npa["Outstanding"].sum() if not npa.empty else 0.0
    clean_ob = max(0.0, total_ob - overdue_ob - npa_ob)
    return {
        "overdue_ob": overdue_ob,
        "overdue_count": len(overdue),
        "npa_ob": npa_ob,
        "npa_count": len(npa),
        "clean_ob": clean_ob,
        "clean_pct": clean_ob / total_ob if total_ob > 0 else 0.0,
    }


def account_risk_category(accounts: pd.DataFrame, invoices: pd.DataFrame) -> pd.Series:
    """Per-account quality category: npa > overdue > clean (by worst open invoice DPD)."""
    npa_ids: set = set()
    overdue_ids: set = set()
    if not invoices.empty:
        open_inv = invoices[invoices["Stage"].isin(OPEN_STAGES)]
        npa_ids = set(open_inv.loc[open_inv["dpd"] > 90, "account_id"])
        overdue_ids = set(open_inv.loc[(open_inv["dpd"] > 7) & (open_inv["dpd"] <= 90), "account_id"])
    return accounts["id"].map(lambda i: "npa" if i in npa_ids else ("overdue" if i in overdue_ids else "clean"))


def portfolio_kpis(accounts: pd.DataFrame, invoices: pd.DataFrame) -> dict[str, float | int | None]:
    risk = risk_kpis(accounts, invoices)
    total_facility = accounts["util_denom"].sum() if "util_denom" in accounts else accounts["total_facility"].sum()
    total_ob = accounts["ob"].sum()
    return {
        "accounts": len(accounts),
        "total_facility": total_facility,
        "total_ob": total_ob,
        "utilization": total_ob / total_facility if total_facility > 0 else 0,
        "mtd_repayments": accounts["mtd_repayments"].sum() if "mtd_repayments" in accounts else 0,
        "net_ob": accounts["net_ob"].sum() if "net_ob" in accounts else total_ob,
        "gap_to_75": accounts["gap_to_75"].sum() if "gap_to_75" in accounts else 0,
        "zero_ob": int((accounts["ob"] < 1).sum()),
        "inactive_12m": int(
            (
                accounts["raw_status"].astype(str).str.contains("Inactive", case=False, na=False)
                & (accounts["days_since_last"].fillna(9999) <= 365)
            ).sum()
        ),
        "overdue_ob": risk["overdue_ob"],
        "npa_ob": risk["npa_ob"],
        "clean_ob": risk["clean_ob"],
        "wirr": weighted_irr(accounts),
    }


def am_summary(accounts: pd.DataFrame) -> pd.DataFrame:
    if accounts.empty:
        return pd.DataFrame()
    grouped = (
        accounts.groupby("am", as_index=False)
        .agg(
            accounts=("id", "count"),
            facility=("util_denom", "sum") if "util_denom" in accounts else ("total_facility", "sum"),
            ob=("ob", "sum"),
            repayments=("mtd_repayments", "sum"),
            gap_to_75=("gap_to_75", "sum"),
            zero_ob=("ob", lambda s: int((s < 1).sum())),
        )
        .sort_values("ob", ascending=False)
    )
    grouped["utilization"] = np.where(grouped["facility"] > 0, grouped["ob"] / grouped["facility"], 0)
    return grouped


def utilization_buckets_pankit(accounts: pd.DataFrame) -> pd.DataFrame:
    """Pankit's 6 histogram buckets (utilization in %)."""
    util = accounts["utilization"] * 100
    bins = [
        ("0%", util == 0),
        ("0-25%", (util > 0) & (util < 25)),
        ("25-50%", (util >= 25) & (util < 50)),
        ("50-75%", (util >= 50) & (util < 75)),
        ("75-100%", (util >= 75) & (util <= 100)),
        (">100%", util > 100),
    ]
    return pd.DataFrame(
        {"Bucket": label, "Accounts": int(mask.sum()), "OB": accounts.loc[mask, "ob"].sum()}
        for label, mask in bins
    )


def utilization_buckets_nikhil(accounts: pd.DataFrame) -> pd.DataFrame:
    """Nikhil's View C buckets over in-target accounts (util capped at 1): Zero / 1-40 / 41-74 / 75-100."""
    util = np.where(accounts["util_denom"] > 0, (accounts["ob"] / accounts["util_denom"]).clip(0, 1), 0)
    util = pd.Series(util, index=accounts.index)
    bins = [
        ("Zero (0%)", util <= 0),
        ("Low (1-40%)", (util > 0) & (util <= 0.40)),
        ("Medium (41-74%)", (util > 0.40) & (util <= 0.74)),
        ("High (75-100%)", util > 0.74),
    ]
    return pd.DataFrame(
        {
            "Bucket": label,
            "Accounts": int(mask.sum()),
            "OB": accounts.loc[mask, "ob"].sum(),
            "WIRR": weighted_irr(accounts.loc[mask & (accounts["ob"] > 0)]),
        }
        for label, mask in bins
    )


# Backward-compatible alias (older code imported `utilization_buckets`).
utilization_buckets = utilization_buckets_pankit


def ob_trend(ob_pivot: pd.DataFrame, account_ids: set) -> pd.DataFrame:
    if ob_pivot.empty or not account_ids:
        return pd.DataFrame(columns=["date", "ob"])
    cols = [col for col in ob_pivot.columns if col in account_ids]
    if not cols:
        return pd.DataFrame(columns=["date", "ob"])
    trend = ob_pivot[cols].sum(axis=1).reset_index()
    trend.columns = ["date", "ob"]
    trend["date"] = pd.to_datetime(trend["date"])
    return trend.sort_values("date")


def ob_trend_by_am(ob_pivot: pd.DataFrame, accounts: pd.DataFrame) -> pd.DataFrame:
    """Long-form per-AM daily OB totals (date, am, ob)."""
    if ob_pivot.empty or accounts.empty:
        return pd.DataFrame(columns=["date", "am", "ob"])
    frames = []
    for am, group in accounts.groupby("am"):
        cols = [c for c in ob_pivot.columns if c in set(group["id"])]
        if not cols:
            continue
        series = ob_pivot[cols].sum(axis=1)
        frames.append(pd.DataFrame({"date": series.index, "am": am, "ob": series.values}))
    if not frames:
        return pd.DataFrame(columns=["date", "am", "ob"])
    return pd.concat(frames, ignore_index=True)


def cp_universe(accounts: pd.DataFrame) -> pd.DataFrame:
    """View G universe: TYPE == 'CP', ALL AMs (ignores team/AM filters).
    `partner` is the CP_COMPANY name from the consolidated master."""
    cp = accounts[accounts["type"].astype(str).str.upper() == "CP"].copy()
    cp["util_denom"] = cp["total_facility"]
    cp["utilization"] = np.where(cp["total_facility"] > 0, (cp["ob"] / cp["total_facility"]).clip(0, 1), 0.0)
    cp["utilization_pct"] = cp["utilization"] * 100
    return cp


def health_scores(cp_accounts: pd.DataFrame, invoices: pd.DataFrame, today: pd.Timestamp) -> pd.Series:
    """Nikhil View G health score /100: 25*util + 25 clean + 25 recent-disb(<=30d) + 25 active-90d."""
    overdue_ids: set = set()
    active_90_ids: set = set()
    if not invoices.empty:
        open_inv = invoices[invoices["Stage"].isin(OPEN_STAGES)]
        overdue_ids = set(open_inv.loc[open_inv["dpd"] > 7, "account_id"])
        cutoff = pd.Timestamp(today) - pd.Timedelta(days=90)
        active_90_ids = set(invoices.loc[invoices["disbursed_date"].notna() & (invoices["disbursed_date"] >= cutoff), "account_id"])
    return (
        cp_accounts["utilization"].clip(0, 1) * 25
        + cp_accounts["id"].map(lambda i: 0 if i in overdue_ids else 25)
        + cp_accounts["days_since_last"].map(lambda d: 25 if pd.notna(d) and d <= 30 else 0)
        + cp_accounts["id"].map(lambda i: 25 if i in active_90_ids else 0)
    ).round()
