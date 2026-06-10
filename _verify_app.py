import warnings; warnings.filterwarnings("ignore")
from streamlit.testing.v1 import AppTest

NIKHIL_VIEWS = ["Snapshot", "Portfolio", "Team", "Health", "Actions", "Account Pulse", "Peak", "CP Health", "Tracker"]
PANKIT_VIEWS = ["Executive", "Account Inventory", "Utilization", "Zero OB", "Workable Inactive",
                "Repayments", "OB Dent", "AM Performance", "75% Engine", "Opportunity Views"]

at = AppTest.from_file("app.py", default_timeout=600)
at.run()
failures = []

def check(team, label):
    if at.exception:
        failures.append((team, label, str(at.exception[0].value)))
        print(f"FAIL {team} / {label}: {at.exception[0].value}")
    else:
        print(f"OK   {team} / {label}")

for team, views in [("Team Nikhil", NIKHIL_VIEWS), ("Team Pankit", PANKIT_VIEWS)]:
    at.radio(key="team_name").set_value(team)
    at.run(); check(team, "team-switch")
    for view in views:
        at.radio(key=f"{team}_nav").set_value(view)
        at.run(); check(team, view)

# exercise in-view interactive widgets (window toggles, custom peak, bucket drill)
at.radio(key="team_name").set_value("Team Nikhil"); at.run()
at.radio(key="Team Nikhil_nav").set_value("Portfolio"); at.run()
at.radio(key="nik_ovr_win").set_value("QTD"); at.run(); check("Nikhil", "OVR window=QTD")
at.radio(key="nik_coll_win").set_value("nm"); at.run(); check("Nikhil", "Collections window=Next Month")
at.radio(key="Team Nikhil_nav").set_value("Health"); at.run()
at.selectbox(key="nik_dsld").set_value("91-120"); at.run(); check("Nikhil", "DSLD bucket=91-120")
at.radio(key="Team Nikhil_nav").set_value("Peak"); at.run()
at.radio(key="nik_peak_pick").set_value("Custom"); at.run(); check("Nikhil", "Peak custom date")
at.radio(key="nik_peak_mode").set_value("Per AM"); at.run(); check("Nikhil", "Trend per-AM")
at.radio(key="Team Nikhil_nav").set_value("Account Pulse"); at.run()
at.radio(key="nik_pulse_slice").set_value("Bottom 25"); at.run(); check("Nikhil", "Pulse slice=Bottom 25")
# nav persistence: after widget interaction we must still be on Account Pulse
assert at.radio(key="Team Nikhil_nav").value == "Account Pulse", "nav state lost!"
print("OK   Nikhil / nav persists across widget interactions")

print("\nRESULT:", "ALL PASS" if not failures else f"{len(failures)} FAILURES")
for f in failures: print(" -", f)
