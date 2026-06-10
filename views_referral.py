import json
import pandas as pd
import streamlit as st
from pathlib import Path

REFERRAL_TRACKER_PATH = Path(__file__).parent / "referral_tracker_state.json"
REFERRAL_STATUSES = ["New", "Contacted", "In Progress", "Converted", "Declined"]
OUTCOME_STATUSES = ["Pending", "Successful", "Unsuccessful"]

def _load_referral_tracker() -> list:
    if REFERRAL_TRACKER_PATH.exists():
        try:
            return json.loads(REFERRAL_TRACKER_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def _save_referral_tracker(state: list) -> None:
    REFERRAL_TRACKER_PATH.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")

def render_referral_tracker(cfg) -> None:
    st.markdown("#### Referral Tracker")
    st.caption("Track new account referrals from existing clients or partners.")

    state = _load_referral_tracker()
    
    # Initialize state in session to use with data_editor if not present
    if "referral_data" not in st.session_state:
        if not state:
            # Default empty row
            state = [{"Referrer AM": "", "Referred Account": "", "Date": "", "Status": "New", "Outcome": "Pending"}]
        st.session_state["referral_data"] = pd.DataFrame(state)

    edited_df = st.data_editor(
        st.session_state["referral_data"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Referrer AM": st.column_config.SelectboxColumn("Referrer AM", options=cfg.ams),
            "Referred Account": st.column_config.TextColumn("Referred Account"),
            "Date": st.column_config.DateColumn("Date (YYYY-MM-DD)"),
            "Status": st.column_config.SelectboxColumn("Status", options=REFERRAL_STATUSES),
            "Outcome": st.column_config.SelectboxColumn("Outcome", options=OUTCOME_STATUSES),
        },
        key="referral_tracker_editor"
    )

    if st.button("💾 Save Referrals", key="save_referrals_btn"):
        # Drop completely empty rows
        cleaned_df = edited_df.dropna(how="all")
        # Update session state and save to disk
        st.session_state["referral_data"] = cleaned_df
        records = cleaned_df.to_dict(orient="records")
        # Handle NAType or NaNs in records before saving
        for r in records:
            if pd.isna(r.get("Date")):
                r["Date"] = None
            else:
                r["Date"] = str(r["Date"])
        _save_referral_tracker(records)
        st.success("Referrals saved successfully!")
