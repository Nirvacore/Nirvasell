"""Running cost meter — radical transparency about what running nirva.sell
actually costs the operator, so "pay what you can" feels like community
funding instead of begging.

Sources:
  • Server cost: admin-set, defaults to ~$5/mo (Hetzner CX11 tier)
  • Domain cost: admin-set, defaults to ~$15/yr amortized = ~$1.25/mo
  • This month's donations: sum from payments.donations
  • This month's AI calls: usage_log entries (rough estimate)

Returns the rendering chunk used by the Support page tip jar and any
"Help fund the server" prompts elsewhere."""
from __future__ import annotations
import datetime
import os

import db


DEFAULT_SERVER_MONTHLY_USD = 5.0
DEFAULT_DOMAIN_YEARLY_USD = 15.0


def _settings():
    try:
        import user_settings as us
        return us
    except Exception:
        return None


def get_monthly_target_thb(usd_to_thb: float = 35.0) -> float:
    """Total monthly cost the operator needs to cover (in THB)."""
    us = _settings()
    if us:
        s_usd = float(us.get("cost.server_monthly_usd", DEFAULT_SERVER_MONTHLY_USD) or DEFAULT_SERVER_MONTHLY_USD)
        d_usd = float(us.get("cost.domain_yearly_usd", DEFAULT_DOMAIN_YEARLY_USD) or DEFAULT_DOMAIN_YEARLY_USD)
    else:
        s_usd = DEFAULT_SERVER_MONTHLY_USD
        d_usd = DEFAULT_DOMAIN_YEARLY_USD
    return (s_usd + d_usd / 12.0) * usd_to_thb


def get_this_month_donations() -> dict[str, float]:
    """Per-currency total of confirmed donations this calendar month."""
    try:
        import payments
        payments.init()
    except Exception:
        return {}
    today = datetime.date.today()
    first_of_month = today.replace(day=1).isoformat()
    with db.conn() as c:
        rows = c.execute(
            """SELECT currency, SUM(amount) AS total
               FROM donations
               WHERE created_at >= ?
                 AND confirmed = 1
               GROUP BY currency""",
            (first_of_month,),
        ).fetchall()
    return {r["currency"]: float(r["total"] or 0) for r in rows}


def set_costs(*, server_monthly_usd: float | None = None,
              domain_yearly_usd: float | None = None) -> None:
    us = _settings()
    if not us:
        return
    if server_monthly_usd is not None:
        us.set("cost.server_monthly_usd", float(server_monthly_usd))
    if domain_yearly_usd is not None:
        us.set("cost.domain_yearly_usd", float(domain_yearly_usd))


# ---- UI helper ----------------------------------------------------------

def render(st, t, *, currency: str = "THB", usd_to_thb: float = 35.0) -> None:
    """Render a horizontal "cost vs raised" meter on a Streamlit page."""
    target = get_monthly_target_thb(usd_to_thb=usd_to_thb)
    raised = get_this_month_donations().get("THB", 0.0)
    pct = min(100, int((raised / target) * 100)) if target > 0 else 0

    # Header line
    month_name = datetime.date.today().strftime("%B %Y")
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;"
        f"align-items:baseline;margin-bottom:6px'>"
        f"<div style='font-size:13px;color:#7a7569;font-weight:500'>"
        f"{t('cost.this_month')} · {month_name}</div>"
        f"<div style='font-size:13px;color:#1f1f1f'>"
        f"<strong>฿{raised:,.0f}</strong> "
        f"<span style='color:#9a9485'>/ ฿{target:,.0f}</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Progress bar — sage when partial, gold-ish when overfunded
    bar_color = "#4d6c5c" if pct < 100 else "#c5963d"
    track_color = "rgba(40,30,20,0.08)"
    st.markdown(
        f"<div style='height:8px;border-radius:4px;background:{track_color};"
        f"overflow:hidden;margin-bottom:6px'>"
        f"<div style='height:100%;width:{min(100,pct)}%;background:{bar_color};"
        f"transition:width .3s ease'></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Subtitle: where the money goes
    st.markdown(
        f"<div style='font-size:11px;color:#9a9485;line-height:1.6'>"
        f"💡 {t('cost.where_money_goes')}"
        f"</div>",
        unsafe_allow_html=True,
    )
