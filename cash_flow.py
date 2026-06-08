"""Cash Flow — net cash by day/week/month: revenue in, expenses out."""
from __future__ import annotations
import db


def daily(days: int = 30) -> list[dict]:
    """Net cash per day for last N days."""
    with db.conn() as c:
        income = c.execute(
            "SELECT date(order_date) day, "
            "  COALESCE(SUM(total_price),0) amount "
            "FROM orders "
            "WHERE date(order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND status NOT IN ('cancelled','returned') "
            "GROUP BY day",
            (days,),
        ).fetchall()
        expenses = c.execute(
            "SELECT date(expense_date) day, "
            "  COALESCE(SUM(amount),0) amount "
            "FROM expenses "
            "WHERE date(expense_date) >= date('now','-' || ? || ' days','localtime') "
            "GROUP BY day",
            (days,),
        ).fetchall()

    inc_map = {r["day"]: r["amount"] for r in income}
    exp_map = {r["day"]: r["amount"] for r in expenses}
    all_days = sorted(set(list(inc_map.keys()) + list(exp_map.keys())))

    result = []
    cumulative = 0.0
    for day in all_days:
        inc = inc_map.get(day, 0)
        exp = exp_map.get(day, 0)
        net = inc - exp
        cumulative += net
        result.append({
            "day": day,
            "income": round(inc, 2),
            "expenses": round(exp, 2),
            "net": round(net, 2),
            "cumulative": round(cumulative, 2),
        })
    return result


def monthly(months: int = 6) -> list[dict]:
    with db.conn() as c:
        income = c.execute(
            "SELECT strftime('%Y-%m', order_date) month, "
            "  COALESCE(SUM(total_price),0) amount "
            "FROM orders "
            "WHERE date(order_date) >= date('now','-' || ? || ' months','localtime') "
            "  AND status NOT IN ('cancelled','returned') "
            "GROUP BY month",
            (months,),
        ).fetchall()
        expenses = c.execute(
            "SELECT strftime('%Y-%m', expense_date) month, "
            "  COALESCE(SUM(amount),0) amount "
            "FROM expenses "
            "WHERE date(expense_date) >= date('now','-' || ? || ' months','localtime') "
            "GROUP BY month",
            (months,),
        ).fetchall()

    inc_map = {r["month"]: r["amount"] for r in income}
    exp_map = {r["month"]: r["amount"] for r in expenses}
    all_months = sorted(set(list(inc_map.keys()) + list(exp_map.keys())))

    result = []
    for month in all_months:
        inc = inc_map.get(month, 0)
        exp = exp_map.get(month, 0)
        result.append({
            "month": month,
            "income": round(inc, 2),
            "expenses": round(exp, 2),
            "net": round(inc - exp, 2),
            "margin_pct": round((inc - exp) / inc * 100, 1) if inc > 0 else 0,
        })
    return result


def current_month_forecast() -> dict:
    """Compare current month pace vs last month."""
    with db.conn() as c:
        this_m = c.execute(
            "SELECT COALESCE(SUM(total_price),0) rev, "
            "  CAST(strftime('%d','now','localtime') AS INTEGER) days_elapsed "
            "FROM orders "
            "WHERE strftime('%Y-%m',order_date)=strftime('%Y-%m','now','localtime') "
            "  AND status NOT IN ('cancelled','returned')"
        ).fetchone()
        last_m = c.execute(
            "SELECT COALESCE(SUM(total_price),0) rev "
            "FROM orders "
            "WHERE strftime('%Y-%m',order_date)=strftime('%Y-%m','now','-1 month','localtime') "
            "  AND status NOT IN ('cancelled','returned')"
        ).fetchone()
        this_exp = c.execute(
            "SELECT COALESCE(SUM(amount),0) amt "
            "FROM expenses "
            "WHERE strftime('%Y-%m',expense_date)=strftime('%Y-%m','now','localtime')"
        ).fetchone()

    days_elapsed = this_m["days_elapsed"] or 1
    days_in_month = 30
    daily_pace = this_m["rev"] / days_elapsed
    projected = round(daily_pace * days_in_month, 2)
    last_rev = last_m["rev"] or 0
    growth_pct = round((projected - last_rev) / last_rev * 100, 1) if last_rev > 0 else 0

    return {
        "this_month_so_far": round(this_m["rev"], 2),
        "days_elapsed": days_elapsed,
        "projected_month": projected,
        "last_month": round(last_rev, 2),
        "growth_pct": growth_pct,
        "this_month_expenses": round(this_exp["amt"], 2),
        "projected_net": round(projected - this_exp["amt"] * days_in_month / days_elapsed, 2),
    }


def summary() -> dict:
    monthly_data = monthly(3)
    if not monthly_data:
        return {"avg_monthly_net": 0, "trend": "stable", "months": 0}
    avg_net = sum(m["net"] for m in monthly_data) / len(monthly_data)
    last_net = monthly_data[-1]["net"] if monthly_data else 0
    trend = "rising" if last_net > avg_net * 1.1 else (
        "declining" if last_net < avg_net * 0.9 else "stable"
    )
    return {
        "avg_monthly_net": round(avg_net, 2),
        "last_month_net": round(last_net, 2),
        "trend": trend,
        "months": len(monthly_data),
    }
