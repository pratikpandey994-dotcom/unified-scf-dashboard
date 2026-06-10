import pandas as pd
from data_loader import load_data
from dashboard_metrics import TEAMS, build_portfolio, filter_team, in_target, weighted_irr, risk_kpis, portfolio_kpis

raw = load_data.__wrapped__() if hasattr(load_data, "__wrapped__") else load_data()
today = pd.Timestamp("2026-06-05")
accounts, invoices, ob_pivot = build_portfolio(raw["master"], raw["view1"], raw["view2"], raw["ob_history"], today)
print("accounts_all:", len(accounts), "| invoices:", len(invoices), "| pivot:", ob_pivot.shape)

nik = filter_team(accounts, "Team Nikhil")
pan = filter_team(accounts, "Team Pankit")
print("Team Nikhil:", len(nik), "(expect 250) | per-AM:", nik["am"].value_counts().to_dict())
print("Team Pankit:", len(pan), "(expect 194) | per-AM:", pan["am"].value_counts().to_dict())

tgt = in_target(nik)
inv_nik = invoices[invoices["account_id"].isin(set(nik["id"]))]
print("Nikhil in-target:", len(tgt), "| Total OB:", round(tgt["ob"].sum()/1e6,2), "M | Fac:", round(tgt["util_denom"].sum()/1e6,2), "M | WIRR:", round(weighted_irr(tgt) or 0,2))
print("Nikhil risk:", {k: round(v,1) if isinstance(v,float) else v for k,v in risk_kpis(tgt, inv_nik).items()})

inv_pan = invoices[invoices["account_id"].isin(set(pan["id"]))]
k = portfolio_kpis(pan, inv_pan)
print("Pankit KPIs: OB", round(k["total_ob"]/1e6,2), "M | Fac", round(k["total_facility"]/1e6,2), "M | util", round(k["utilization"]*100,1), "% | zeroOB", k["zero_ob"], "| MTD repay", round(k["mtd_repayments"]/1e6,3), "M")
# Pankit util must use facility only:
assert (pan["util_denom"] == pan["facility"]).all(), "Pankit denom wrong"
assert (nik["util_denom"] == nik["total_facility"]).all(), "Nikhil denom wrong"
# Non-Workable must NOT pass the workable predicate
from dashboard_metrics import is_workable
assert not is_workable(pan[pan["raw_status"]=="Non-Workable"]).any()
print("ASSERTIONS OK")
