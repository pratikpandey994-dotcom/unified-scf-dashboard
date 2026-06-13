"""Headless regression check of the live app.

The app renders each team's views inside st.tabs, so every tab body executes on
every run — one run per team covers all views. Widget interactions below hit the
in-view controls (window toggles, bucket picks, custom peak, tracker mode).
"""
import warnings

warnings.filterwarnings("ignore")

from streamlit.testing.v1 import AppTest

failures: list[tuple[str, str]] = []


def check(at: AppTest, label: str) -> None:
    if at.exception:
        failures.append((label, str(at.exception[0].value)))
        print(f"FAIL {label}: {at.exception[0].value}")
    else:
        print(f"OK   {label}")


at = AppTest.from_file("app.py", default_timeout=600)
at.run()
check(at, "default-load (Team Nikhil, all 12 tabs render)")
assert len(at.tabs) == 12, f"expected 12 Nikhil tabs, got {len(at.tabs)}"

at.radio(key="theme_mode").set_value("Dark")
at.run()
check(at, "theme=Dark")
at.radio(key="theme_mode").set_value("Light")
at.run()
check(at, "theme=Light")

# ---- Team Nikhil in-view widgets --------------------------------------------
for label, kind, key, value in [
    ("PQ filter=npa", "radio", "nik_pq_filter", "npa"),
    ("OVR window=QTD", "radio", "nik_ovr_win", "QTD"),
    ("Collections window=Next Month", "radio", "nik_coll_win", "nm"),
    ("DSLD bucket=91-120", "selectbox", "nik_dsld", "91-120"),
    ("Declining window=QTD", "radio", "nik_dec_win", "QTD"),
    ("Peak trend=Per AM", "radio", "nik_peak_mode", "Per AM"),
    ("Peak date=Custom", "radio", "nik_peak_pick", "Custom"),
    ("Peak detail=declined", "selectbox", "nik_peak_cat", "declined"),
    ("Pulse slice=Bottom 25", "radio", "nik_pulse_slice", "Bottom 25"),
    ("Repayment window=MTD", "radio", "nik_pulse_rep", "MTD"),
    ("Tracker=Manager Overview", "radio", "nik_tracker_mode", "Manager Overview"),
]:
    getattr(at, kind)(key=key).set_value(value)
    at.run()
    check(at, f"Nikhil / {label}")

def exercise_am_filter(at: AppTest, team: str) -> None:
    box = at.selectbox(key=f"{team}_am")
    # options surface as formatted labels: "All" renders as "All account managers"
    single_am = next((o for o in box.options if o not in ("All", "All account managers")), None)
    if single_am is None:
        print(f"SKIP {team} / AM filter (no AMs in data)")
        return
    box.set_value(single_am)
    at.run()
    check(at, f"{team} / AM filter={single_am}")
    at.selectbox(key=f"{team}_am").set_value("All")
    at.run()
    check(at, f"{team} / AM filter=All")


exercise_am_filter(at, "Team Nikhil")

# ---- Team Pankit -------------------------------------------------------------
at.radio(key="team_name").set_value("Team Pankit")
at.run()
check(at, "team-switch (Team Pankit, all 14 tabs render)")
assert len(at.tabs) == 14, f"expected 14 Pankit tabs, got {len(at.tabs)}"

exercise_am_filter(at, "Team Pankit")

print("\nRESULT:", "ALL PASS" if not failures else f"{len(failures)} FAILURES")
for failure in failures:
    print(" -", failure)
raise SystemExit(1 if failures else 0)
