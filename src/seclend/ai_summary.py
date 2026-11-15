"""Desk commentary drafted by an LLM, with guardrails.

Responsible-use choices:
- Only aggregated desk figures are sent to the model: no loan IDs, ISINs or counterparties.
- Every number in the AI draft is checked against the figures we supplied; a draft that
  cites an unknown number is rejected and the deterministic summary is used instead.
- The output is labelled as a draft for human review, never sent automatically.
- Without an API key, the tool falls back to a template summary, so it always runs.
"""
from __future__ import annotations

import os
import re

MODEL = "claude-haiku-5-5"


def facts_from(summary: dict, exceptions_count: dict) -> dict:
    """Rounded, aggregated facts: the only data the model ever sees."""
    return {
        "on_loan_notional_m": round(summary["on_loan_notional"] / 1e6, 1),
        "utilisation_pct": round(100 * summary["utilisation_value"], 1),
        "daily_fee_revenue_k": round(summary["daily_fee_revenue"] / 1e3, 1),
        "specials": summary["specials"],
        "specials_revenue_share_pct": round(100 * summary["specials_revenue_share"], 1),
        **{f"exceptions_{k}": v for k, v in exceptions_count.items()},
    }


def template_summary(facts: dict) -> str:
    n_exc = sum(v for k, v in facts.items() if k.startswith("exceptions_"))
    return (
        f"Book on loan: {facts['on_loan_notional_m']}m, utilisation {facts['utilisation_pct']}%. "
        f"Daily fee revenue {facts['daily_fee_revenue_k']}k, of which "
        f"{facts['specials_revenue_share_pct']}% from {facts['specials']} specials. "
        f"{n_exc} exceptions to review today."
    )


def numbers_are_grounded(text: str, facts: dict) -> bool:
    """True if every number in the text is one of the supplied facts."""
    allowed = {float(v) for v in facts.values()}
    allowed |= {float(sum(v for k, v in facts.items() if k.startswith("exceptions_")))}
    found = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    return all(x in allowed for x in found)


def ai_summary(facts: dict) -> tuple[str, str]:
    """Return (text, source) where source is 'ai' or 'template'."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return template_summary(facts), "template"
    try:
        import anthropic

        prompt = (
            "You write the morning note for a securities lending desk. Using ONLY these figures, "
            "write 3 short sentences for traders: book size and utilisation, where revenue comes "
            "from, and what needs review. Do not invent or compute new numbers.\n"
            f"Figures: {facts}"
        )
        msg = anthropic.Anthropic().messages.create(
            model=MODEL, max_tokens=200, messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text.strip()
    except Exception:
        return template_summary(facts), "template"

    if not numbers_are_grounded(text, facts):
        return template_summary(facts), "template"
    return text, "ai"
