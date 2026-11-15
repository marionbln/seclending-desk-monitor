# Securities Lending Desk Monitor

A small Python tool that produces the morning report for a securities lending desk:
book size, utilisation, fee revenue, specials, and a list of **exceptions to review**,
plus a short desk note **drafted by an LLM under guardrails**.

All data is synthetic (randomly generated), so the project can be shared publicly.

```
python run.py            # writes desk_report.html
python -m pytest -q      # 5 tests
```

## What it does

| Step | Module | Details |
|---|---|---|
| Data | `data.py` | Lendable inventory (60 securities, general collateral vs specials) and 150 open loans, with a few planted breaks |
| Analytics | `analytics.py` | Utilisation, on-loan notional, daily fee revenue, specials and their revenue share |
| Exceptions | `exceptions.py` | **Rules:** collateral below 102%, fee more than 30% away from market, loans open over a year, quantity lent above lendable. **Model:** Isolation Forest flags unusual loans that no rule explains |
| AI note | `ai_summary.py` | 3-sentence desk note written by Claude, with guardrails (below) |
| Report | `report.py` | One HTML page: headline cards, top-10 revenue chart, exception table |

## Responsible use of AI

The LLM only writes the commentary; every number comes from the Python analytics.

- **Data minimisation:** only rounded, aggregated figures are sent to the model, never loan IDs, ISINs or counterparties (checked by a test).
- **Grounding check:** every number in the AI draft must match a figure supplied to the model; otherwise the draft is discarded.
- **Human in the loop:** the note is labelled "AI draft – to be reviewed by the desk".
- **Fallback:** without an API key, or if the call fails, a deterministic template summary is used, so the report always runs.

To enable the AI note: `pip install anthropic` and set `ANTHROPIC_API_KEY`.

## Ideas for next steps

- Recall risk: flag loans on securities with upcoming corporate actions or dividend dates
- Fee optimisation: suggest re-rates for loans priced below the market fee
- Schedule the report daily and email it to the desk
