"""Desk-level analytics: utilisation, revenue and specials."""
from __future__ import annotations

import pandas as pd

SPECIAL_THRESHOLD_BPS = 100.0


def position_view(inventory: pd.DataFrame, loans: pd.DataFrame) -> pd.DataFrame:
    """One row per security: lendable, on loan, utilisation and daily fee revenue."""
    lent = loans.assign(
        notional=lambda d: d["qty"] * d["isin"].map(inventory.set_index("isin")["price"]),
        daily_fee=lambda d: d["notional"] * d["fee_bps"] / 1e4 / 360,
    )
    agg = lent.groupby("isin").agg(
        on_loan_qty=("qty", "sum"),
        on_loan_notional=("notional", "sum"),
        daily_fee=("daily_fee", "sum"),
        n_loans=("loan_id", "count"),
    )
    view = inventory.set_index("isin").join(agg).fillna(
        {"on_loan_qty": 0, "on_loan_notional": 0.0, "daily_fee": 0.0, "n_loans": 0}
    )
    view["utilisation"] = view["on_loan_qty"] / view["lendable_qty"]
    view["is_special"] = view["market_fee_bps"] >= SPECIAL_THRESHOLD_BPS
    return view.reset_index()


def desk_summary(view: pd.DataFrame) -> dict:
    """Headline numbers for the daily report."""
    lendable_value = (view["lendable_qty"] * view["price"]).sum()
    return {
        "securities": int(len(view)),
        "on_loan_notional": float(view["on_loan_notional"].sum()),
        "utilisation_value": float(view["on_loan_notional"].sum() / lendable_value),
        "daily_fee_revenue": float(view["daily_fee"].sum()),
        "specials": int(view["is_special"].sum()),
        "specials_revenue_share": float(
            view.loc[view["is_special"], "daily_fee"].sum() / max(view["daily_fee"].sum(), 1e-9)
        ),
    }


def revenue_by(view: pd.DataFrame, loans: pd.DataFrame, key: str) -> pd.Series:
    """Daily fee revenue by sector or counterparty."""
    if key == "sector":
        return view.groupby("sector")["daily_fee"].sum().sort_values(ascending=False)
    price = view.set_index("isin")["price"]
    fee = loans["qty"] * loans["isin"].map(price) * loans["fee_bps"] / 1e4 / 360
    return fee.groupby(loans[key]).sum().sort_values(ascending=False)
