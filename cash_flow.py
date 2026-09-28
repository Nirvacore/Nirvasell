"""Cash Flow — net cash by day/week/month: revenue in, expenses out."""
from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
import math

import db
from order_dates import order_business_date


def _ensure_tables() -> None:
    import expenses

    expenses.init()


def _nonblank(value) -> bool:
    return value is not None and str(value).strip() != ""


def _number(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _business_today() -> date:
    today = order_business_date(datetime.now(timezone.utc))
    assert today is not None
    return today


def _flow_summary(*, start: date, end: date, period: str) -> dict:
    _ensure_tables()
    with db.conn() as c:
        orders = [dict(row) for row in c.execute(
            "SELECT total_price,order_date,status FROM orders"
        )]
        expense_rows = [dict(row) for row in c.execute(
            "SELECT amount,date FROM expenses"
        )]

    income: dict[str, float] = {}
    outflow: dict[str, float] = {}
    missing_orders = 0
    missing_expenses = 0

    for order in orders:
        order_date = order_business_date(order["order_date"])
        if order_date is None:
            # Window membership cannot be determined safely.
            missing_orders += 1
            continue
        if order_date < start or order_date > end:
            continue

        status = str(order["status"]).strip().lower() if _nonblank(order["status"]) else ""
        if not status:
            missing_orders += 1
            continue
        if status in {"cancelled", "returned"}:
            continue

        amount = _number(order["total_price"])
        if amount is None or amount < 0:
            missing_orders += 1
            continue
        key = order_date.isoformat() if period == "day" else order_date.strftime("%Y-%m")
        income[key] = income.get(key, 0.0) + amount

    for expense in expense_rows:
        expense_date = order_business_date(expense["date"])
        if expense_date is None:
            missing_expenses += 1
            continue
        if expense_date < start or expense_date > end:
            continue

        amount = _number(expense["amount"])
        if amount is None or amount < 0:
            missing_expenses += 1
            continue
        key = expense_date.isoformat() if period == "day" else expense_date.strftime("%Y-%m")
        outflow[key] = outflow.get(key, 0.0) + amount

    collection = "days" if period == "day" else "months"
    if missing_orders or missing_expenses:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": missing_orders,
            "missing_expense_evidence_rows": missing_expenses,
            collection: [],
        }

    rows = []
    cumulative = 0.0
    for key in sorted(set(income) | set(outflow)):
        incoming = income.get(key, 0.0)
        outgoing = outflow.get(key, 0.0)
        net = incoming - outgoing
        if period == "day":
            cumulative += net
            rows.append({
                "day": key,
                "income": round(incoming, 2),
                "expenses": round(outgoing, 2),
                "net": round(net, 2),
                "cumulative": round(cumulative, 2),
            })
        else:
            rows.append({
                "month": key,
                "income": round(incoming, 2),
                "expenses": round(outgoing, 2),
                "net": round(net, 2),
                "margin_pct": round(net / incoming * 100, 1) if incoming > 0 else None,
            })

    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_expense_evidence_rows": 0,
        collection: rows,
    }


def daily_summary(days: int = 30) -> dict:
    """Return daily cash flow only when every in-window row is complete."""
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise ValueError("days must be a positive integer")
    end = _business_today()
    start = end - timedelta(days=days - 1)
    return _flow_summary(start=start, end=end, period="day")


def daily(days: int = 30) -> list[dict]:
    """Net cash per day for the last N calendar days."""
    return daily_summary(days)["days"]


def monthly_summary(months: int = 6) -> dict:
    """Return the current and prior calendar months with evidence status."""
    if isinstance(months, bool) or not isinstance(months, int) or months < 1:
        raise ValueError("months must be a positive integer")
    end = _business_today()
    month_index = end.year * 12 + end.month - 1 - (months - 1)
    start = date(month_index // 12, month_index % 12 + 1, 1)
    return _flow_summary(start=start, end=end, period="month")


def monthly(months: int = 6) -> list[dict]:
    """Net cash for the current and prior calendar months."""
    return monthly_summary(months)["months"]


def current_month_forecast() -> dict:
    """Compare current month pace vs last month."""
    evidence = monthly_summary(2)
    if not evidence["evidence_complete"]:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": evidence["missing_order_evidence_rows"],
            "missing_expense_evidence_rows": evidence["missing_expense_evidence_rows"],
            "this_month_so_far": None,
            "days_elapsed": None,
            "projected_month": None,
            "last_month": None,
            "growth_pct": None,
            "this_month_expenses": None,
            "projected_net": None,
        }

    today = _business_today()
    this_key = today.strftime("%Y-%m")
    prior_index = today.year * 12 + today.month - 2
    last_key = f"{prior_index // 12:04d}-{prior_index % 12 + 1:02d}"
    by_month = {row["month"]: row for row in evidence["months"]}
    this_month = by_month.get(this_key, {"income": 0.0, "expenses": 0.0})
    last_month = by_month.get(last_key, {"income": 0.0})

    days_elapsed = today.day
    days_in_month = monthrange(today.year, today.month)[1]
    daily_pace = this_month["income"] / days_elapsed
    projected = round(daily_pace * days_in_month, 2)
    last_rev = last_month["income"]
    growth_pct = round((projected - last_rev) / last_rev * 100, 1) if last_rev > 0 else 0

    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_expense_evidence_rows": 0,
        "this_month_so_far": round(this_month["income"], 2),
        "days_elapsed": days_elapsed,
        "projected_month": projected,
        "last_month": round(last_rev, 2),
        "growth_pct": growth_pct,
        "this_month_expenses": round(this_month["expenses"], 2),
        "projected_net": round(
            projected - this_month["expenses"] * days_in_month / days_elapsed, 2
        ),
    }


def summary() -> dict:
    """Return three-month net trend only when its evidence is complete."""
    evidence = monthly_summary(3)
    if not evidence["evidence_complete"]:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": evidence["missing_order_evidence_rows"],
            "missing_expense_evidence_rows": evidence["missing_expense_evidence_rows"],
            "avg_monthly_net": None,
            "last_month_net": None,
            "trend": None,
            "months": 0,
        }
    monthly_data = evidence["months"]
    if not monthly_data:
        return {
            "evidence_complete": True,
            "missing_order_evidence_rows": 0,
            "missing_expense_evidence_rows": 0,
            "avg_monthly_net": 0,
            "last_month_net": 0,
            "trend": "stable",
            "months": 0,
        }
    avg_net = sum(m["net"] for m in monthly_data) / len(monthly_data)
    last_net = monthly_data[-1]["net"] if monthly_data else 0
    trend = "rising" if last_net > avg_net * 1.1 else (
        "declining" if last_net < avg_net * 0.9 else "stable"
    )
    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_expense_evidence_rows": 0,
        "avg_monthly_net": round(avg_net, 2),
        "last_month_net": round(last_net, 2),
        "trend": trend,
        "months": len(monthly_data),
    }
