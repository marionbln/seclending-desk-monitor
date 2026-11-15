import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from seclend.ai_summary import facts_from, numbers_are_grounded, template_summary
from seclend.analytics import desk_summary, position_view
from seclend.data import make_inventory, make_loans
from seclend.exceptions import all_exceptions, rule_exceptions

INV = make_inventory(seed=0)
LOANS = make_loans(INV, seed=1)


def test_positions_and_revenue():
    view = position_view(INV, LOANS)
    assert (view["utilisation"] >= 0).all()
    assert view["daily_fee"].sum() > 0
    assert view["on_loan_qty"].sum() == LOANS["qty"].sum()


def test_planted_breaks_are_caught():
    exc = rule_exceptions(INV, LOANS)
    assert "L0003" in set(exc.loc[exc["reason"] == "Fee far from market", "loan_id"])
    assert "L0007" in set(exc.loc[exc["reason"] == "Collateral below 102%", "loan_id"])
    assert "L0011" in set(exc.loc[exc["reason"] == "Loan open > 1 year", "loan_id"])
    assert "L0015" in set(exc.loc[exc["reason"] == "Lent more than lendable", "loan_id"])


def test_model_flags_do_not_duplicate_rule_flags():
    exc = all_exceptions(INV, LOANS)
    rule_ids = set(exc.loc[exc["source"] == "rule", "loan_id"])
    model_ids = set(exc.loc[exc["source"] == "model", "loan_id"])
    assert not rule_ids & model_ids


def test_only_aggregated_facts_go_to_the_model():
    facts = facts_from(desk_summary(position_view(INV, LOANS)), {"rule": 4, "model": 2})
    text = str(facts)
    assert "L0" not in text and "CPTY" not in text and "CH" not in text


def test_grounding_check_accepts_real_numbers_and_rejects_invented_ones():
    facts = facts_from(desk_summary(position_view(INV, LOANS)), {"rule": 4, "model": 2})
    assert numbers_are_grounded(template_summary(facts), facts)
    assert not numbers_are_grounded("Utilisation rose to 97.3% today.", facts)
