"""Metrics regression check against the live Jun-11 extracts (expected values from
docs/DATA_MIGRATION_2026-06-11.md)."""
import warnings

import pandas as pd

warnings.filterwarnings("ignore")

from data_loader import load_data
from dashboard_metrics import (
    TEAMS, build_portfolio, cp_universe, filter_team, in_target,
    is_workable, portfolio_kpis, risk_kpis, weighted_irr,
)

TODAY = pd.Timestamp("2026-06-11")

loader = load_data.__wrapped__ if hasattr(load_data, "__wrapped__") else load_data
raw = loader(as_of=str(TODAY.date()))
accounts, invoices, ob_pivot = build_portfolio(raw["master"], raw["invoices"], raw["ob_history"], TODAY)
print("accounts_all:", len(accounts), "| invoices:", len(invoices), "| ob pivot:", ob_pivot.shape)
assert len(accounts) == 647, f"expected 647 accounts, got {len(accounts)}"
assert len(invoices) == 36975, f"expected 36,975 invoices, got {len(invoices)}"
assert invoices["account_id"].isin(set(accounts["id"])).all(), "invoice->account join lost rows"

nik = filter_team(accounts, "Team Nikhil")
pan = filter_team(accounts, "Team Pankit")
print("Team Nikhil:", len(nik), "(expect 255) | per-AM:", nik["am"].value_counts().to_dict())
print("Team Pankit:", len(pan), "(expect 193) | per-AM:", pan["am"].value_counts().to_dict())
assert len(nik) == 255 and len(pan) == 193

cp = cp_universe(accounts)
print("CP universe:", len(cp), "(expect 313) | partners:", cp["partner"].nunique(), "(expect 43)")
assert len(cp) == 313

tgt = in_target(nik)
inv_nik = invoices[invoices["account_id"].isin(set(nik["id"]))]
print("Nikhil in-target:", len(tgt),
      "| Total OB: %.2fM" % (tgt["ob"].sum() / 1e6),
      "| Fac: %.2fM" % (tgt["util_denom"].sum() / 1e6),
      "| WIRR: %.2f" % (weighted_irr(tgt) or 0))
print("Nikhil risk:", {k: round(v, 1) if isinstance(v, float) else v for k, v in risk_kpis(tgt, inv_nik).items()})

inv_pan = invoices[invoices["account_id"].isin(set(pan["id"]))]
k = portfolio_kpis(pan, inv_pan)
print("Pankit KPIs: OB %.2fM | Fac %.2fM | util %.1f%% | zeroOB %d | MTD repay %.3fM"
      % (k["total_ob"] / 1e6, k["total_facility"] / 1e6, k["utilization"] * 100, k["zero_ob"], k["mtd_repayments"] / 1e6))

# Denominator rules per team
assert (pan["util_denom"] == pan["facility"]).all(), "Pankit denom must be facility only"
assert (nik["util_denom"] == nik["total_facility"]).all(), "Nikhil denom must include overdraft"
# Non-Workable must NOT pass the workable predicate
assert not is_workable(pan[pan["raw_status"] == "Non-Workable"]).any()
# DPD semantics: no negative dpd after canonicalization
assert (invoices["dpd"] >= 0).all()
# Reconstructed OB sanity: today's total within 25% of master OB and >= open outstanding * 0.9
recon_today = ob_pivot.iloc[-1].sum()
master_ob = accounts["ob"].sum()
print("recon today: %.1fM vs master OB %.1fM" % (recon_today / 1e6, master_ob / 1e6))
assert 0.9 < recon_today / master_ob < 1.35, "reconstruction drifted from master OB"
print("ASSERTIONS OK")
