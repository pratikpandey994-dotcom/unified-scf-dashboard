from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import numpy as np


DOWNLOADS = Path.home() / "Downloads"

DEFAULT_FILES = {
    "view1": DOWNLOADS / "scf_am_team___view_1_with_suspension_reasons_2026-06-05T13_49_41.37721429Z.xlsx",
    "view2": DOWNLOADS / "view_2_2026-06-05T13_49_21.379501371Z.xlsx",
    "master": DOWNLOADS / "us_scf___master_data___handover_date_2026-06-05T14_10_07.092355226Z.xlsx",
    "historic_ob": DOWNLOADS / "Historic OB.xlsx",
    "current_ob": DOWNLOADS / "us_scf___daily_ob_by_accounts_2026-06-03T15_05_48.33250036Z.xlsx",
}

DEMO_DATE = pd.Timestamp("2026-06-05")
DEMO_CP_AMS = ["Nikhil Shetty", "Darshan Hublikar", "Deepsayan Dam", "Ashitha Nair", "Asif Ali"]
DEMO_DIRECT_AMS = ["Pankit Shah", "Sonal Mishra", "Pejush Hal", "Kaustav Das"]


def norm_id(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace(",", "").strip()
    return text[:-2] if text.endswith(".0") else text


def _read_excel(source: Any) -> pd.DataFrame:
    if source is None:
        return pd.DataFrame()
    if hasattr(source, "seek"):
        source.seek(0)
    return pd.read_excel(source)


def _resolve_source(uploaded: Any, default_path: Path) -> Any:
    if uploaded is not None:
        return uploaded
    return default_path if default_path.exists() else None


def _to_number(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)
    return df


def _to_datetime(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NaT
        df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def _load_view1(source: Any) -> pd.DataFrame:
    df = _read_excel(source)
    required = {"importer_user_id", "AM_Name"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"View 1 is missing required column(s): {', '.join(missing)}")

    df["importer_user_id"] = df["importer_user_id"].apply(norm_id)
    df["AM_Name"] = df["AM_Name"].astype(str).str.strip()
    if "utilization_status" not in df.columns:
        df["utilization_status"] = ""
    df["utilization_status"] = df["utilization_status"].astype(str).str.strip().str.lower()
    _to_number(df, ["Facility_Size", "Outstanding_Balance", "overdraft_limit", "Signed-up IRR"])
    _to_datetime(df, ["First_Disbursed_Date", "Last_Disbursed_Date"])
    return df.set_index("importer_user_id", drop=False)


def _load_view2(source: Any) -> pd.DataFrame:
    df = _read_excel(source)
    required = {"Buyer", "Stage", "Origination", "Outstanding"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"View 2 is missing required column(s): {', '.join(missing)}")

    df["Buyer"] = df["Buyer"].astype(str).str.strip()
    df["buyer_lower"] = df["Buyer"].str.casefold()
    df["Stage"] = df["Stage"].astype(str).str.strip().str.lower()
    _to_number(df, ["Origination", "Outstanding", "dpd", "payment_total_usd"])
    _to_datetime(df, ["disbursed_date", "settlement_date", "due_date_of_invoice"])
    return df


def _load_master(source: Any) -> pd.DataFrame:
    df = _read_excel(source)
    required = {"Buyer_ID", "Buyer", "AM", "Partner", "Team", "Broad_Account_Status", "Account_Status"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Master data is missing required column(s): {', '.join(missing)}")

    df["Buyer_ID"] = df["Buyer_ID"].apply(norm_id)
    df["Buyer"] = df["Buyer"].astype(str).str.strip()
    df["buyer_lower"] = df["Buyer"].str.casefold()
    df["AM"] = df["AM"].astype(str).str.strip()
    for column in ["Partner", "Team", "Broad_Account_Status", "Account_Status"]:
        df[column] = df[column].astype(str).str.strip()
    _to_number(df, ["Facility_Size", "Overdraft_Limit", "OB", "Signed_up_IRR"])
    _to_datetime(df, ["First_Disbursed_Date", "Last_Disbursed_Date"])
    return df


def _load_ob(source: Any) -> pd.DataFrame:
    if source is None:
        return pd.DataFrame(columns=["importer_user_id", "ob_date", "ob"])
    df = _read_excel(source)
    required = {"importer_user_id", "ob_date", "ob"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"OB history is missing required column(s): {', '.join(missing)}")
    df["importer_user_id"] = df["importer_user_id"].apply(norm_id)
    df["ob_date"] = pd.to_datetime(df["ob_date"], errors="coerce")
    df["ob"] = pd.to_numeric(df["ob"], errors="coerce").fillna(0)
    return df.dropna(subset=["ob_date"])


def _make_demo_data(today: pd.Timestamp = DEMO_DATE) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(42)
    cp_companies = [
        "Atlas Foods LLC",
        "Blue Ridge Trading",
        "Coastal Supply Co",
        "Delta Imports Inc",
        "Eagle Distributors",
        "Frontier Goods Corp",
        "Global Harvest Ltd",
        "Harbor Freight Solutions",
        "Inland Fresh Co",
        "Junction Foods",
        "Keystone Provisions",
        "Liberty Commodities",
    ]
    direct_companies = [
        "Nova Eye Inc",
        "Worldwide Snacks Inc.",
        "Q4 Designs LLC",
        "Style Source LLC",
        "AGRO FRESH USA, LLC",
        "Packaging Matters LLC",
        "Trendly Inc",
        "Harry Supply Inc",
        "Sanael LLC DBA Central Trading",
        "Certor Sports LLC",
        "GDB International Inc.",
        "UNIMACTS GLOBAL LLC",
    ]
    teams = [
        ("CP", cp_companies, DEMO_CP_AMS, ["IGA_Trade_Credit", "Funding_Nexus", "C2FO"]),
        ("Direct", direct_companies, DEMO_DIRECT_AMS, ["Direct"]),
    ]

    master_rows: list[dict] = []
    view1_rows: list[dict] = []
    view2_rows: list[dict] = []
    ob_rows: list[dict] = []

    acc_counter = 100000
    inv_counter = 1
    for team_name, companies, ams, partners in teams:
        for company in companies:
            buyer_id = str(acc_counter)
            acc_counter += 1
            am = rng.choice(ams)
            partner = rng.choice(partners)
            if team_name == "CP":
                broad_status = "Workable"
                account_status = rng.choice(["Active", "Suspended"])
                util_status = "active" if account_status == "Active" else "suspended"
                overdraft = float(rng.choice([0, 50000, 100000]))
            else:
                broad_status = rng.choice(["Workable", "Non-Workable"], p=[0.8, 0.2])
                account_status = rng.choice(["Workable - Active", "Workable - Temporarily suspended", "Workable - Inactive (AM)", "Non-Workable"])
                util_status = "active" if "Active" in account_status else "suspended"
                overdraft = float(rng.choice([0, 0, 25000, 50000]))

            facility = float(rng.choice([50000, 100000, 150000, 250000, 500000, 750000, 1000000, 1500000]))
            ob = float(round(facility * float(rng.uniform(0.05, 1.15)), 2))
            irr = float(round(rng.uniform(14, 28), 2))
            first_disb = today - pd.Timedelta(days=int(rng.integers(60, 500)))
            last_disb = today - pd.Timedelta(days=int(rng.integers(2, 380)))

            master_rows.append(
                {
                    "Buyer_ID": buyer_id,
                    "Buyer": company,
                    "Partner": partner,
                    "Type": "Demo",
                    "First_Disbursed_Date": first_disb,
                    "Last_Disbursed_Date": last_disb,
                    "Handover_Date": today - pd.Timedelta(days=10),
                    "Facility_Size": facility,
                    "Overdraft_Limit": overdraft,
                    "OB": ob,
                    "utilization_status": util_status,
                    "Signed_up_IRR": irr,
                    "interest_rate": 0,
                    "flat_discounting_fee": 0,
                    "Tenor": 180,
                    "overdue_rate": 0,
                    "address": "",
                    "city": "",
                    "state": "",
                    "country": "US",
                    "AM": am,
                    "BDM": "",
                    "Team": team_name,
                    "email": "",
                    "Account_Status": account_status,
                    "Broad_Account_Status": broad_status,
                    "Pod_Manager": "",
                    "margin_rate": 0,
                    "advance_rate": 0,
                    "processing_fee": 0,
                    "Annual_Maintenance_Fee": 0,
                    "PG_Status": "",
                }
            )

            view1_rows.append(
                {
                    "importer_user_id": buyer_id,
                    "company": company,
                    "utilization_status": util_status,
                    "Facility_Size": facility,
                    "Outstanding_Balance": ob,
                    "max_balance": facility,
                    "Signed-up IRR": irr,
                    "interest_rate": 0,
                    "flat_discounting_fee": 0,
                    "overdue_rate": 0,
                    "Realised Revenue": 0,
                    "Total Orginations": 0,
                    "First_Disbursed_Date": first_disb,
                    "Last_Disbursed_Date": last_disb,
                    "overdraft_limit": overdraft,
                    "AM_ID": "",
                    "AM_Name": am,
                    "AM_Email": f"{am.split()[0].lower()}@example.com",
                    "user_id": buyer_id,
                    "latest_suspension_Date": last_disb if util_status != "active" else pd.NaT,
                    "suspension_reason": "" if util_status == "active" else "Demo suspension",
                    "manual_suspension_reason": "",
                }
            )

            for _ in range(int(rng.integers(2, 6))):
                stage = rng.choice(["advanced", "closed", "paid", "received", "overdue", "npa", "partial"])
                orig = float(round(rng.uniform(5000, 50000), 2))
                if stage in {"closed", "paid", "received"}:
                    outstanding = 0.0
                    settlement_date = today - pd.Timedelta(days=int(rng.integers(1, 30)))
                elif stage == "partial":
                    outstanding = float(round(orig * rng.uniform(0.1, 0.6), 2))
                    settlement_date = today - pd.Timedelta(days=int(rng.integers(1, 45)))
                else:
                    outstanding = float(round(orig * rng.uniform(0.4, 1.0), 2))
                    settlement_date = pd.NaT
                due_date = today - pd.Timedelta(days=int(rng.integers(0, 120)))
                disbursed_date = due_date - pd.Timedelta(days=int(rng.integers(30, 60)))
                dpd = max(0, int((today - due_date).days)) if stage in {"overdue", "npa"} else 0
                view2_rows.append(
                    {
                        "Invoice ID": f"DEMO-{inv_counter:05d}",
                        "AM_Email": f"{am.split()[0].lower()}@example.com",
                        "Buyer": company,
                        "Seller": "Demo Seller",
                        "Payment_terms": "Net 30",
                        "Stage": stage,
                        "booked_revenue": 0,
                        "total_fees": 0,
                        "total_interest_paid": 0,
                        "total_disc_fees_paid": 0,
                        "total_overdue_paid": 0,
                        "irr": irr,
                        "disbursed_date": disbursed_date,
                        "settlement_date": settlement_date,
                        "Created Date": disbursed_date,
                        "Updated Date": today,
                        "Invoice Date": disbursed_date,
                        "Deposit Received Date": settlement_date,
                        "Origination": orig,
                        "Outstanding": outstanding,
                        "Total Advanced": orig,
                        "advice_collection_amount": 0,
                        "payment_total_usd": max(0, orig - outstanding),
                        "due_date_of_invoice": due_date,
                        "dpd": dpd,
                    }
                )
                inv_counter += 1

            for offset in range(0, 180, 7):
                ob_rows.append(
                    {
                        "importer_user_id": buyer_id,
                        "ob_date": today - pd.Timedelta(days=offset),
                        "ob": max(0, ob * float(rng.uniform(0.85, 1.10))),
                    }
                )

    master = pd.DataFrame(master_rows)
    view1 = pd.DataFrame(view1_rows)
    view2 = pd.DataFrame(view2_rows)
    ob_history = pd.DataFrame(ob_rows)
    return {"master": master, "view1": view1, "view2": view2, "ob_history": ob_history}


@st.cache_data(show_spinner=False)
def load_data(
    view1_file: Any = None,
    view2_file: Any = None,
    master_file: Any = None,
    historic_ob_file: Any = None,
    current_ob_file: Any = None,
) -> dict[str, pd.DataFrame]:
    """Load every Excel input through a single cached entry point."""
    view1_source = _resolve_source(view1_file, DEFAULT_FILES["view1"])
    view2_source = _resolve_source(view2_file, DEFAULT_FILES["view2"])
    master_source = _resolve_source(master_file, DEFAULT_FILES["master"])
    hist_source = _resolve_source(historic_ob_file, DEFAULT_FILES["historic_ob"])
    curr_source = _resolve_source(current_ob_file, DEFAULT_FILES["current_ob"])

    missing = [
        name
        for name, source in {
            "View 1": view1_source,
            "View 2": view2_source,
            "Master": master_source,
        }.items()
        if source is None
    ]
    if missing:
        raise FileNotFoundError(f"Missing required file(s): {', '.join(missing)}")

    historic_ob = _load_ob(hist_source)
    current_ob = _load_ob(curr_source)
    return {
        "view1": _load_view1(view1_source),
        "view2": _load_view2(view2_source),
        "master": _load_master(master_source),
        "ob_history": pd.concat([historic_ob, current_ob], ignore_index=True),
    }


@st.cache_data(show_spinner=False)
def load_demo_data() -> dict[str, pd.DataFrame]:
    """Return a deterministic synthetic dataset for UI and logic testing."""
    return _make_demo_data()
