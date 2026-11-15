"""Daily desk report: one HTML page with headline numbers, a chart and the exception list."""
from __future__ import annotations

import base64
import io
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _chart(view: pd.DataFrame) -> str:
    top = view.sort_values("daily_fee", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(7, 3.2))
    colors = ["#c0392b" if s else "#2c6fbb" for s in top["is_special"]]
    ax.barh(top["isin"][::-1], top["daily_fee"][::-1], color=colors[::-1])
    ax.set_xlabel("Daily fee revenue")
    ax.set_title("Top 10 securities by revenue (red = special)")
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def build_report(summary: dict, view: pd.DataFrame, exceptions: pd.DataFrame,
                 note: str, note_source: str) -> str:
    label = "AI draft – to be reviewed by the desk" if note_source == "ai" else "Template summary"
    cards = "".join(
        f"<div class='card'><b>{v}</b><span>{k}</span></div>"
        for k, v in {
            "On loan": f"{summary['on_loan_notional']/1e6:,.1f}m",
            "Utilisation": f"{summary['utilisation_value']:.1%}",
            "Daily revenue": f"{summary['daily_fee_revenue']/1e3:,.1f}k",
            "Specials": summary["specials"],
            "Exceptions": len(exceptions),
        }.items()
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Securities Lending Desk Monitor – {date.today()}</title>
<style>
body{{font-family:Arial,sans-serif;max-width:900px;margin:30px auto;color:#222}}
.cards{{display:flex;gap:12px;margin:16px 0}}
.card{{flex:1;border:1px solid #ddd;border-radius:8px;padding:12px;text-align:center}}
.card b{{display:block;font-size:22px}} .card span{{color:#666;font-size:13px}}
.note{{background:#f5f7fb;border-left:4px solid #2c6fbb;padding:10px 14px}}
.note small{{color:#888}} table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{border-bottom:1px solid #eee;padding:6px;text-align:left}}
</style></head><body>
<h1>Securities Lending Desk Monitor</h1><p>{date.today():%d %B %Y} · synthetic data</p>
<div class="cards">{cards}</div>
<div class="note"><small>{label}</small><p>{note}</p></div>
<h2>Revenue</h2><img src="data:image/png;base64,{_chart(view)}" width="100%">
<h2>Exceptions to review</h2>{exceptions.to_html(index=False, border=0)}
</body></html>"""
