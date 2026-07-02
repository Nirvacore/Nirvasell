"""Cash Flow Forecast — see your money BEFORE it arrives.

Combines: pending COD collection + expected platform payouts +
upcoming expenses + supplier orders = cash position forecast.

Thai platforms hold seller money 7-14 days. Knowing when cash
actually arrives prevents the #1 reseller killer: running out
of cash to buy more stock."""
from __future__ import annotations

from datetime import datetime, date, timedelta

import db
from i18n_inline import cf_week_label


def forecast(days_ahead: int = 30) -> dict:
    """Forecast cash flow for the next N days."""
    today = date.today()

    # ---- INCOMING ----

    # 1. Pending COD collection (delivered, not yet paid)
    pending_cod = 0
    try:
        with db.conn() as c:
            r = c.execute(
                "SELECT COALESCE(SUM(amount),0) FROM cod_orders "
                "WHERE payment_type='cod' AND status IN ('delivered','shipped')"
            ).fetchone()
            pending_cod = float(r[0] or 0)
    except Exception:
        pass

    # 2. Recent orders not yet settled (platform holds 7-14 days)
    pending_orders = 0
    try:
        cutoff = (today - timedelta(days=14)).isoformat()
        with db.conn() as c:
            r = c.execute(
                "SELECT COALESCE(SUM(total_price),0) FROM orders "
                "WHERE order_date >= ?",
                (cutoff,),
            ).fetchone()
            pending_orders = float(r[0] or 0) * 0.5  # estimate ~50% not yet settled
    except Exception:
        pass

    total_incoming = pending_cod + pending_orders

    # ---- OUTGOING ----

    # 3. Recent monthly expenses (annualize to estimate next period)
    monthly_expenses = 0
    try:
        import expenses as exp
        exp.init()
        month_str = today.strftime("%Y-%m")
        s = exp.monthly_summary(month_str)
        monthly_expenses = s.get("total", 0)
    except Exception:
        pass

    projected_expenses = monthly_expenses * (days_ahead / 30)

    # 4. Pending supplier orders
    pending_po = 0
    try:
        with db.conn() as c:
            r = c.execute(
                "SELECT COALESCE(SUM(total_amount),0) FROM purchase_orders "
                "WHERE status='ordered'"
            ).fetchone()
            pending_po = float(r[0] or 0)
    except Exception:
        pass

    # 5. Expected return losses
    return_reserve = 0
    try:
        with db.conn() as c:
            r = c.execute(
                "SELECT COALESCE(SUM(refund_amount + shipping_cost),0) / 3 "
                "FROM returns WHERE return_date >= ?",
                ((today - timedelta(days=90)).isoformat(),),
            ).fetchone()
            return_reserve = float(r[0] or 0)  # monthly avg from last 90 days
    except Exception:
        pass

    total_outgoing = projected_expenses + pending_po + return_reserve

    # ---- SUMMARY ----
    net_flow = total_incoming - total_outgoing

    return {
        "days_ahead": days_ahead,
        "pending_cod": round(pending_cod, 0),
        "pending_orders": round(pending_orders, 0),
        "total_incoming": round(total_incoming, 0),
        "projected_expenses": round(projected_expenses, 0),
        "pending_po": round(pending_po, 0),
        "return_reserve": round(return_reserve, 0),
        "total_outgoing": round(total_outgoing, 0),
        "net_flow": round(net_flow, 0),
        "health": "positive" if net_flow > 0 else ("tight" if net_flow > -5000 else "danger"),
    }


def weekly_projection(weeks: int = 4) -> list[dict]:
    """Week-by-week cash flow projection."""
    results = []
    for w in range(weeks):
        days = (w + 1) * 7
        f = forecast(days)
        results.append({
            "week": w + 1,
            "label": cf_week_label(w + 1),
            "incoming": f["total_incoming"],
            "outgoing": f["total_outgoing"],
            "net": f["net_flow"],
            "health": f["health"],
        })
    return results


def runway_days() -> int:
    """Estimate how many days of cash runway based on current burn rate."""
    f30 = forecast(30)
    daily_burn = f30["total_outgoing"] / 30 if f30["total_outgoing"] > 0 else 1
    available = f30["total_incoming"]
    return int(available / daily_burn) if daily_burn > 0 else 999
