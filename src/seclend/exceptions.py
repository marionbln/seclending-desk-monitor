"""Exception handling: rule-based checks plus an ML anomaly score.

Rules catch the breaks we know about; the anomaly model flags unusual loans that no
rule describes. Every flag carries a plain-English reason so a person can review it.
"""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

MIN_COLLATERAL_PCT = 102.0
FEE_DEVIATION_LIMIT = 0.30   # loan fee more than 30% away from market fee
MAX_DAYS_OPEN = 365


def rule_exceptions(inventory: pd.DataFrame, loans: pd.DataFrame) -> pd.DataFrame:
    inv = inventory.set_index("isin")
    df = loans.join(inv[["market_fee_bps", "lendable_qty"]], on="isin")
    lent_per_isin = df.groupby("isin")["qty"].transform("sum")

    checks = {
        "Collateral below 102%": df["collateral_pct"] < MIN_COLLATERAL_PCT,
        "Fee far from market": (df["fee_bps"] / df["market_fee_bps"] - 1).abs() > FEE_DEVIATION_LIMIT,
        "Loan open > 1 year": df["days_open"] > MAX_DAYS_OPEN,
        "Lent more than lendable": lent_per_isin > df["lendable_qty"],
    }
    out = []
    for reason, mask in checks.items():
        hits = df.loc[mask, ["loan_id", "isin", "counterparty"]].assign(reason=reason, source="rule")
        out.append(hits)
    return pd.concat(out, ignore_index=True)


def anomaly_exceptions(
    inventory: pd.DataFrame, loans: pd.DataFrame, contamination: float = 0.03, seed: int = 0
) -> pd.DataFrame:
    """Isolation Forest on loan features; returns the most unusual loans."""
    df = loans.join(inventory.set_index("isin")[["market_fee_bps"]], on="isin")
    features = pd.DataFrame(
        {
            "fee_vs_market": df["fee_bps"] / df["market_fee_bps"],
            "collateral_pct": df["collateral_pct"],
            "days_open": df["days_open"],
        }
    )
    model = IsolationForest(contamination=contamination, random_state=seed).fit(features)
    flagged = model.predict(features) == -1
    return df.loc[flagged, ["loan_id", "isin", "counterparty"]].assign(
        reason="Unusual loan profile (anomaly model)", source="model"
    )


def all_exceptions(inventory: pd.DataFrame, loans: pd.DataFrame) -> pd.DataFrame:
    rules = rule_exceptions(inventory, loans)
    model = anomaly_exceptions(inventory, loans)
    # Keep model flags only for loans that no rule already explains.
    model = model[~model["loan_id"].isin(rules["loan_id"])]
    return pd.concat([rules, model], ignore_index=True).sort_values(["source", "loan_id"])
