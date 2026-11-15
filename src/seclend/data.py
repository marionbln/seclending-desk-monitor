"""Synthetic data for a securities lending desk.

Everything here is randomly generated: no real client, counterparty or market data
is used, so the project can be shared publicly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SECTORS = ["Financials", "Industrials", "Health Care", "Tech", "Consumer", "Energy"]
COUNTERPARTIES = ["CPTY_A", "CPTY_B", "CPTY_C", "CPTY_D", "CPTY_E"]


def make_inventory(n_securities: int = 60, seed: int = 0) -> pd.DataFrame:
    """Lendable inventory: one row per security."""
    rng = np.random.default_rng(seed)
    isins = [f"CH{rng.integers(10**9, 10**10)}" for _ in range(n_securities)]
    price = rng.lognormal(mean=4.0, sigma=0.6, size=n_securities).round(2)
    lendable_qty = rng.integers(20_000, 500_000, size=n_securities)
    # Most names are "general collateral" (cheap to borrow); a few are "specials".
    market_fee_bps = np.where(
        rng.random(n_securities) < 0.15,
        rng.uniform(150, 900, n_securities),   # specials / hard-to-borrow
        rng.uniform(15, 60, n_securities),     # general collateral
    ).round(1)
    return pd.DataFrame(
        {
            "isin": isins,
            "sector": rng.choice(SECTORS, n_securities),
            "price": price,
            "lendable_qty": lendable_qty,
            "market_fee_bps": market_fee_bps,
        }
    )


def make_loans(inventory: pd.DataFrame, n_loans: int = 150, seed: int = 1) -> pd.DataFrame:
    """Open loans against the inventory, with a few deliberately planted breaks."""
    rng = np.random.default_rng(seed)
    rows = inventory.sample(n_loans, replace=True, random_state=seed).reset_index(drop=True)
    qty = (rows["lendable_qty"] * rng.uniform(0.02, 0.12, n_loans)).astype(int)
    fee = rows["market_fee_bps"] * rng.normal(1.0, 0.05, n_loans)
    collateral_pct = rng.normal(105, 0.8, n_loans)  # typical equity margin ~105%

    loans = pd.DataFrame(
        {
            "loan_id": [f"L{i:04d}" for i in range(n_loans)],
            "isin": rows["isin"],
            "counterparty": rng.choice(COUNTERPARTIES, n_loans),
            "qty": qty,
            "fee_bps": fee.round(1),
            "collateral_pct": collateral_pct.round(2),
            "days_open": rng.integers(1, 120, n_loans),
        }
    )

    # Planted exceptions so the monitor has something to find.
    loans.loc[3, "fee_bps"] = 5.0                       # stale / mispriced fee on a loan
    loans.loc[7, "collateral_pct"] = 99.1               # collateral shortfall
    loans.loc[11, "days_open"] = 400                    # very old open loan
    loans.loc[15, "qty"] = int(rows.loc[15, "lendable_qty"] * 1.4)  # lent more than lendable
    return loans
