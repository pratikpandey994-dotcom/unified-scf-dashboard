"""Excel ingestion for the Jun-11 consolidated extracts (see docs/DATA_MIGRATION_2026-06-11.md).

Two inputs replace the old five:
- master client-level  (647 x 37)  -> canonical `master` frame (one row per account)
- invoice level        (37k x 35)  -> canonical `invoices` frame

Daily OB history is reconstructed from invoices (ORIGINATION held from FIRST_ADVANCE_DATE to
SETTLEMENT_DATE) because the daily-OB extract files no longer exist. Advance-basis: faithful for
shape/peaks/movement, overstates levels ~5-15% vs master OB.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

DOWNLOADS = Path.home() / "Downloads"

FILE_PATTERNS = {
    "master": "us_scf___master_data___client_level_*.xlsx",
    "invoices": "us_scf___invoice_level_data_*.xlsx",
}

DEMO_DATE = pd.Timestamp("2026-06-11")
DEMO_CP_AMS = ["Nikhil Shetty", "Darshan Hublikar", "Deepsayan Dam", "Ashitha Nair", "Asif Ali"]
DEMO_DIRECT_AMS = ["Pankit Shah", "Sonal Mishra", "Pejush Hal", "Kaustav Das"]

MASTER_REQUIRED = {"USER_ID", "IMPORTER_NAME", "TYPE", "AM", "ACCOUNT_STATUS", "BROAD_ACCOUNT_STATUS",
                   "FACILITY_SIZE", "OVERDRAFT_LIMIT", "OB", "USER_UTILIZATION_STATUS"}
INVOICE_REQUIRED = {"INVOICE_ID", "IMPORTER_USER_ID", "STAGE", "ORIGINATION",
                    "OUTSTANDING_ADVANCE_BALANCE_USD", "FIRST_ADVANCE_DATE", "DUE_DATE"}


def norm_id(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace(",", "").strip()
    return text[:-2] if text.endswith(".0") else text


def latest_default_file(kind: str) -> Path | None:
    """Newest Downloads file matching the extract pattern — future re-extracts need no code change."""
    matches = sorted(DOWNLOADS.glob(FILE_PATTERNS[kind]), key=lambda p: p.stat().st_mtime)
    return matches[-1] if matches else None


def _read_excel(source: Any) -> pd.DataFrame:
    if hasattr(source, "seek"):
        source.seek(0)
    return pd.read_excel(source)


def _to_number(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column not in df.columns:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)


def _to_datetime(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column not in df.columns:
            df[column] = pd.NaT
        df[column] = pd.to_datetime(df[column], errors="coerce")


def _clean_str(series: pd.Series) -> pd.Series:
    out = series.astype(str).str.strip()
    return out.mask(out.isin(["", "nan", "None", "NaT"]), "")


def load_master_file(source: Any) -> pd.DataFrame:
    """Canonicalize the client-level master extract. Every source column is carried (see migration doc)."""
    raw = _read_excel(source)
    missing = sorted(MASTER_REQUIRED - set(raw.columns))
    if missing:
        raise ValueError(f"Master (client-level) is missing required column(s): {', '.join(missing)}")

    df = pd.DataFrame()
    df["id"] = raw["USER_ID"].apply(norm_id)
    df["company"] = _clean_str(raw["IMPORTER_NAME"])
    df["cp_id"] = raw.get("CP_ID")
    df["partner"] = _clean_str(raw.get("CP_COMPANY", pd.Series(index=raw.index, dtype=object)))
    df["type"] = _clean_str(raw["TYPE"]).str.upper()  # DIRECT / CP
    df["industry"] = _clean_str(raw.get("AIRTABLE_INDUSTRY", pd.Series(index=raw.index, dtype=object))).replace("", "Unknown")
    df["goods_shipped"] = _clean_str(raw.get("AIRTABLE_GOODS_SHIPPED", pd.Series(index=raw.index, dtype=object)))
    df["util_status"] = _clean_str(raw["USER_UTILIZATION_STATUS"]).str.casefold()
    df["raw_status"] = _clean_str(raw["ACCOUNT_STATUS"])
    df["broad_status"] = _clean_str(raw["BROAD_ACCOUNT_STATUS"])
    df["am"] = _clean_str(raw["AM"]).replace("", "Unassigned")
    df["bdm"] = _clean_str(raw.get("BDM", pd.Series(index=raw.index, dtype=object)))
    df["pod_manager"] = _clean_str(raw.get("POD_MANAGER", pd.Series(index=raw.index, dtype=object)))
    df["address"] = _clean_str(raw.get("USER_ADDRESS", pd.Series(index=raw.index, dtype=object)))
    df["city"] = _clean_str(raw.get("USER_CITY", pd.Series(index=raw.index, dtype=object)))
    df["state"] = _clean_str(raw.get("USER_STATE", pd.Series(index=raw.index, dtype=object))).replace("", "Unknown")
    df["country"] = _clean_str(raw.get("USER_COUNTRY", pd.Series(index=raw.index, dtype=object)))
    df["pg_status"] = _clean_str(raw.get("PG_STATUS", pd.Series(index=raw.index, dtype=object)))
    df["cg_status"] = _clean_str(raw.get("CG_STATUS", pd.Series(index=raw.index, dtype=object)))
    df["plaid_status"] = _clean_str(raw.get("PLAID_STATUS", pd.Series(index=raw.index, dtype=object)))

    for canonical, source_col in [
        ("facility", "FACILITY_SIZE"), ("overdraft", "OVERDRAFT_LIMIT"), ("total_facility", "TOTAL_LIMIT"),
        ("ob", "OB"), ("irr", "SIGNED_UP_IRR"), ("interest_rate", "INTEREST_RATE"),
        ("flat_fee", "FLAT_DISCOUNTING_FEE"), ("tenor", "PLANS_PAYMENT_TENOR"),
        ("overdue_rate", "OVERDUE_RATE"), ("margin_rate", "PLANS_MARGIN_RATE"),
        ("advance_rate", "PLANS_ADVANCE_RATE"), ("processing_fee", "PROCESSING_FEE"),
        ("amf", "ANNUAL_MAINTENANCE_FEE"), ("max_dpd", "MAX_DPD"), ("max_open_dpd", "MAX_OPEN_DPD"),
    ]:
        df[canonical] = pd.to_numeric(raw.get(source_col), errors="coerce").fillna(0)
    df["ob"] = df["ob"].clip(lower=0)
    if "TOTAL_LIMIT" not in raw.columns:
        df["total_facility"] = df["facility"] + df["overdraft"]

    for canonical, source_col in [("first_disbursed", "FIRST_DISBURSED_DATE"), ("last_disbursed", "LAST_DISBURSED_DATE")]:
        df[canonical] = pd.to_datetime(raw.get(source_col), errors="coerce")
    return df


def load_invoice_file(source: Any) -> pd.DataFrame:
    """Canonicalize the invoice-level extract. Account-fact columns come from the master join, not here."""
    raw = _read_excel(source)
    missing = sorted(INVOICE_REQUIRED - set(raw.columns))
    if missing:
        raise ValueError(f"Invoice extract is missing required column(s): {', '.join(missing)}")

    df = pd.DataFrame()
    df["Invoice ID"] = raw["INVOICE_ID"]
    df["account_id"] = raw["IMPORTER_USER_ID"].apply(norm_id)
    df["Buyer"] = _clean_str(raw.get("IMPORTER_COMPANY", pd.Series(index=raw.index, dtype=object)))
    df["buyer_country"] = _clean_str(raw.get("BUYER_COUNTRY", pd.Series(index=raw.index, dtype=object)))
    df["exporter"] = _clean_str(raw.get("EXPORTER_COMPANY", pd.Series(index=raw.index, dtype=object)))
    df["exporter_country"] = _clean_str(raw.get("EXPORTER_COUNTRY", pd.Series(index=raw.index, dtype=object)))
    df["cp_company"] = _clean_str(raw.get("CP_COMPANY", pd.Series(index=raw.index, dtype=object)))
    df["type"] = _clean_str(raw.get("TYPE", pd.Series(index=raw.index, dtype=object))).str.upper()
    df["am_on_invoice"] = _clean_str(raw.get("AM", pd.Series(index=raw.index, dtype=object)))
    df["Stage"] = _clean_str(raw["STAGE"]).str.casefold()
    df["currency"] = _clean_str(raw.get("CURRENCY", pd.Series(index=raw.index, dtype=object)))

    _to_datetime(raw, ["INVOICE_DATE", "MARGIN_RECEIVED_DATE", "FIRST_ADVANCE_DATE", "DUE_DATE", "SETTLEMENT_DATE"])
    df["invoice_date"] = raw["INVOICE_DATE"]
    df["margin_received_date"] = raw["MARGIN_RECEIVED_DATE"]
    df["disbursed_date"] = raw["FIRST_ADVANCE_DATE"]
    df["due_date_of_invoice"] = raw["DUE_DATE"]
    df["settlement_date"] = raw["SETTLEMENT_DATE"]

    for canonical, source_col in [
        ("Origination", "ORIGINATION"), ("Outstanding", "OUTSTANDING_ADVANCE_BALANCE_USD"),
        ("invoice_value", "INVOICE_VALUE_USD"), ("total_advanced", "TOTAL_ADVANCED"),
        ("margin_received", "MARGIN_RECEIVED_USD"), ("booked_revenue", "BOOKED_REVENUE"),
        ("expected_interest", "EXPECTED_REGULAR_INTEREST_USD"), ("expected_fees", "EXPECTED_FACTORING_FEES_USD"),
        ("interest_native", "REGULAR_INTEREST_NATIVE"), ("fees_native", "FACTORING_FEES_NATIVE"),
        ("overdue_interest", "OVERDUE_INTEREST_NATIVE"), ("int_rate", "INTEREST_RATE"),
        ("disc_rate", "DISCOUNTING_RATE"), ("term", "INVOICE_TERM"),
    ]:
        df[canonical] = pd.to_numeric(raw.get(source_col), errors="coerce").fillna(0)
    # DAYS_PAST_DUE is null when an invoice is not past due (no more negative days-until-due).
    df["dpd"] = pd.to_numeric(raw["DAYS_PAST_DUE"], errors="coerce").fillna(0)
    df["Origination"] = df["Origination"].clip(lower=0)
    df["Outstanding"] = df["Outstanding"].clip(lower=0)
    return df


def reconstruct_ob_history(invoices: pd.DataFrame, today: pd.Timestamp) -> pd.DataFrame:
    """Daily OB per account from invoice flow events (advance-basis, see module docstring).

    Returns the long form the metrics layer expects: importer_user_id / ob_date / ob.
    """
    if invoices.empty:
        return pd.DataFrame(columns=["importer_user_id", "ob_date", "ob"])
    today = pd.Timestamp(today).normalize()
    inv = invoices[invoices["disbursed_date"].notna() & (invoices["Origination"] > 0)]

    plus = pd.DataFrame({
        "importer_user_id": inv["account_id"],
        "date": inv["disbursed_date"].dt.normalize(),
        "delta": inv["Origination"],
    })
    settled = inv[inv["settlement_date"].notna() & (inv["settlement_date"].dt.normalize() <= today)]
    minus = pd.DataFrame({
        "importer_user_id": settled["account_id"],
        "date": settled["settlement_date"].dt.normalize(),
        "delta": -settled["Origination"],
    })
    events = pd.concat([plus, minus], ignore_index=True)
    events = events[events["date"] <= today]
    if events.empty:
        return pd.DataFrame(columns=["importer_user_id", "ob_date", "ob"])

    deltas = events.pivot_table(index="date", columns="importer_user_id", values="delta", aggfunc="sum")
    daily = deltas.reindex(pd.date_range(deltas.index.min(), today, freq="D")).fillna(0).cumsum()
    daily = daily.clip(lower=0)

    long = daily.stack().reset_index()
    long.columns = ["ob_date", "importer_user_id", "ob"]
    return long[["importer_user_id", "ob_date", "ob"]]


def _make_demo_data(today: pd.Timestamp = DEMO_DATE) -> dict[str, pd.DataFrame]:
    """Deterministic synthetic dataset in the canonical (post-load) schema."""
    rng = np.random.default_rng(42)
    cp_companies = [
        "Atlas Foods LLC", "Blue Ridge Trading", "Coastal Supply Co", "Delta Imports Inc",
        "Eagle Distributors", "Frontier Goods Corp", "Global Harvest Ltd", "Harbor Freight Solutions",
        "Inland Fresh Co", "Junction Foods", "Keystone Provisions", "Liberty Commodities",
    ]
    direct_companies = [
        "Nova Eye Inc", "Worldwide Snacks Inc.", "Q4 Designs LLC", "Style Source LLC",
        "AGRO FRESH USA, LLC", "Packaging Matters LLC", "Trendly Inc", "Harry Supply Inc",
        "Sanael LLC DBA Central Trading", "Certor Sports LLC", "GDB International Inc.", "UNIMACTS GLOBAL LLC",
    ]
    industries = ["Consumer - Others", "Textiles & Apparel", "Electronics", "Industrial Goods", "Food - Plant Products"]
    states = ["CA", "NY", "TX", "NJ", "FL", "IL"]
    cp_partners = ["IGA_Trade_Credit", "Funding_Nexus", "C2FO"]
    statuses = ["Workable - Active", "Workable - Temporarily suspended", "Workable - Inactive (AM)",
                "Workable - Inactive (BDM)", "Non-Workable"]

    master_rows: list[dict] = []
    invoice_rows: list[dict] = []
    acc_counter = 100000
    inv_counter = 1
    for type_, companies, ams in [("CP", cp_companies, DEMO_CP_AMS), ("DIRECT", direct_companies, DEMO_DIRECT_AMS)]:
        for company in companies:
            account_id = str(acc_counter)
            acc_counter += 1
            am = str(rng.choice(ams))
            raw_status = str(rng.choice(statuses, p=[0.45, 0.2, 0.1, 0.1, 0.15]))
            broad = "Non-Workable" if raw_status == "Non-Workable" else "Workable"
            util_status = "active" if raw_status == "Workable - Active" else "suspended"
            facility = float(rng.choice([50000, 100000, 250000, 500000, 750000, 1000000]))
            overdraft = float(rng.choice([0, 0, 0, 50000, 100000])) if type_ == "CP" else 0.0
            ob = float(round(facility * float(rng.uniform(0.0, 1.05)), 2))
            irr = float(round(rng.uniform(14, 28), 2))
            last_disb = today - pd.Timedelta(days=int(rng.integers(2, 380)))
            master_rows.append({
                "id": account_id, "company": company, "cp_id": None,
                "partner": str(rng.choice(cp_partners)) if type_ == "CP" else "",
                "type": type_, "industry": str(rng.choice(industries)),
                "goods_shipped": "", "util_status": util_status, "raw_status": raw_status,
                "broad_status": broad, "am": am, "bdm": "Demo BDM", "pod_manager": "",
                "address": "", "city": "", "state": str(rng.choice(states)), "country": "United States Of America",
                "pg_status": str(rng.choice(["Yes", "No"], p=[0.1, 0.9])), "cg_status": "No",
                "plaid_status": str(rng.choice(["Active", "Not Integrated", "Inactive / Broken Connection"])),
                "facility": facility, "overdraft": overdraft, "total_facility": facility + overdraft,
                "ob": ob, "irr": irr, "interest_rate": 12.0, "flat_fee": 1.0, "tenor": 90,
                "overdue_rate": 24, "margin_rate": 20, "advance_rate": 80, "processing_fee": 0.0,
                "amf": 0.5, "max_dpd": float(rng.integers(0, 120)), "max_open_dpd": float(rng.integers(0, 60)),
                "first_disbursed": today - pd.Timedelta(days=int(rng.integers(120, 900))),
                "last_disbursed": last_disb,
            })
            for _ in range(int(rng.integers(4, 10))):
                stage = str(rng.choice(["advanced", "closed", "paid", "overdue", "npa", "partial"], p=[0.2, 0.45, 0.15, 0.08, 0.05, 0.07]))
                orig = float(round(rng.uniform(5000, 80000), 2))
                disbursed = today - pd.Timedelta(days=int(rng.integers(5, 400)))
                due = disbursed + pd.Timedelta(days=90)
                if stage in {"closed", "paid"}:
                    outstanding, settlement = 0.0, disbursed + pd.Timedelta(days=int(rng.integers(30, 120)))
                elif stage == "partial":
                    outstanding, settlement = float(round(orig * rng.uniform(0.1, 0.6), 2)), pd.NaT
                else:
                    outstanding, settlement = orig, pd.NaT
                dpd = max(0, int((today - due).days)) if stage in {"overdue", "npa", "advanced", "partial"} else 0
                if stage == "npa":
                    dpd = max(dpd, 95)
                invoice_rows.append({
                    "Invoice ID": inv_counter, "account_id": account_id, "Buyer": company,
                    "buyer_country": "United States Of America", "exporter": f"Exporter {inv_counter % 17}",
                    "exporter_country": str(rng.choice(["India", "China", "Vietnam", "Mexico"])),
                    "cp_company": "", "type": type_, "am_on_invoice": am, "Stage": stage, "currency": "USD",
                    "invoice_date": disbursed, "margin_received_date": disbursed,
                    "disbursed_date": disbursed, "due_date_of_invoice": due,
                    "settlement_date": settlement if pd.notna(settlement) and settlement <= today else pd.NaT,
                    "Origination": orig, "Outstanding": outstanding, "invoice_value": orig * 1.25,
                    "total_advanced": orig, "margin_received": orig * 0.25,
                    "booked_revenue": float(round(orig * rng.uniform(0.005, 0.03), 2)),
                    "expected_interest": orig * 0.02, "expected_fees": orig * 0.005,
                    "interest_native": orig * 0.02, "fees_native": orig * 0.005, "overdue_interest": 0.0,
                    "int_rate": 12.0, "disc_rate": 1.0, "term": 90, "dpd": float(dpd),
                })
                inv_counter += 1

    master = pd.DataFrame(master_rows)
    invoices = pd.DataFrame(invoice_rows)
    ob_history = reconstruct_ob_history(invoices, today)
    return {"master": master, "invoices": invoices, "ob_history": ob_history}


@st.cache_data(show_spinner=False)
def load_data(master_file: Any = None, invoice_file: Any = None, as_of: str = "") -> dict[str, pd.DataFrame]:
    """Load the two consolidated extracts (uploads first, else newest Downloads match)."""
    master_source = master_file if master_file is not None else latest_default_file("master")
    invoice_source = invoice_file if invoice_file is not None else latest_default_file("invoices")

    missing = [label for label, source in
               [("Master (client level)", master_source), ("Invoice level", invoice_source)] if source is None]
    if missing:
        raise FileNotFoundError(
            f"Missing required file(s): {', '.join(missing)}. "
            f"Expected in Downloads: {FILE_PATTERNS['master']} and {FILE_PATTERNS['invoices']}"
        )

    master = load_master_file(master_source)
    invoices = load_invoice_file(invoice_source)
    today = pd.Timestamp(as_of) if as_of else pd.Timestamp.today().normalize()
    ob_history = reconstruct_ob_history(invoices, today)
    return {"master": master, "invoices": invoices, "ob_history": ob_history}


@st.cache_data(show_spinner=False)
def load_demo_data() -> dict[str, pd.DataFrame]:
    """Return a deterministic synthetic dataset for UI and logic testing."""
    return _make_demo_data()


# Default-path discovery used by the sidebar display.
def default_files_found() -> dict[str, Path | None]:
    return {kind: latest_default_file(kind) for kind in FILE_PATTERNS}
