"""Run the daily desk monitor: python run.py  ->  writes desk_report.html"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from seclend.ai_summary import ai_summary, facts_from
from seclend.analytics import desk_summary, position_view
from seclend.data import make_inventory, make_loans
from seclend.exceptions import all_exceptions
from seclend.report import build_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Securities lending desk monitor")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="desk_report.html")
    args = parser.parse_args()

    inventory = make_inventory(seed=args.seed)
    loans = make_loans(inventory, seed=args.seed + 1)
    view = position_view(inventory, loans)
    summary = desk_summary(view)
    exceptions = all_exceptions(inventory, loans)

    facts = facts_from(summary, exceptions["source"].value_counts().to_dict())
    note, source = ai_summary(facts)

    Path(args.out).write_text(build_report(summary, view, exceptions, note, source), encoding="utf-8")
    print(note)
    print(f"{len(exceptions)} exceptions -> report written to {args.out} ({source} summary)")


if __name__ == "__main__":
    main()
