"""Profit Calendar — daily profit heatmap like GitHub contributions.

See at a glance which days made money, which days lost money.
Spot patterns: weekend vs weekday, campaign days, seasonal trends."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import math

import db


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


def _canonical_date(value) -> date | None:
    if not _nonblank(value):
        return None
    raw = str(value).strip()
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None
    return parsed if parsed.isoformat() == raw else None


def daily_summary(days: int = 90) -> dict:
    """Return daily profit only when every in-window row is complete.

    An unparseable date has unknown window membership and therefore fails the
    result closed. Once a canonical date proves a row is outside the requested
    window, unrelated defects on that row do not suppress current evidence.
    """
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise ValueError("days must be a non-negative integer")

    end = date.today()
    start = end - timedelta(days=days)
    with db.conn() as c:
        orders = [dict(row) for row in c.execute(
            "SELECT order_id,sku,platform,qty,total_price,order_date,status FROM orders"
        )]
        products = [dict(row) for row in c.execute(
            "SELECT sku,cost_price FROM products"
        )]

    products_by_sku: dict[str, list[dict]] = {}
    for product in products:
        if _nonblank(product["sku"]):
            products_by_sku.setdefault(str(product["sku"]).strip(), []).append(product)

    included = []
    missing_orders = 0
    missing_products = 0
    for order in orders:
        order_date = _canonical_date(order["order_date"])
        if order_date is None:
            # Membership cannot be determined safely.
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

        sku = str(order["sku"]).strip() if _nonblank(order["sku"]) else ""
        qty = _number(order["qty"])
        total = _number(order["total_price"])
        if (
            not all(_nonblank(order[key]) for key in ("order_id", "platform", "sku"))
            or qty is None
            or qty < 0
            or total is None
            or total < 0
        ):
            missing_orders += 1
            continue

        matches = products_by_sku.get(sku, [])
        cost = _number(matches[0]["cost_price"]) if len(matches) == 1 else None
        if len(matches) != 1 or cost is None or cost < 0:
            missing_products += 1
            continue

        included.append({
            "date": order_date,
            "sku": sku,
            "qty": qty,
            "total": total,
            "cost": cost,
            "order_key": (
                str(order["platform"]).strip(),
                str(order["order_id"]).strip(),
            ),
        })

    if missing_orders or missing_products:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": missing_orders,
            "missing_product_evidence_rows": missing_products,
            "days": [],
        }

    day_map: dict[str, dict] = {}
    for order in included:
        key = order["date"].isoformat()
        aggregate = day_map.setdefault(
            key, {"revenue": 0.0, "cogs": 0.0, "orders": set()}
        )
        aggregate["revenue"] += order["total"]
        aggregate["cogs"] += order["qty"] * order["cost"]
        aggregate["orders"].add(order["order_key"])

    result = []
    current = start
    for _ in range(days + 1):
        ds = current.isoformat()
        data = day_map.get(ds)
        revenue = data["revenue"] if data else 0.0
        cogs = data["cogs"] if data else 0.0
        result.append({
            "date": ds,
            "weekday": current.strftime("%a"),
            "weekday_num": current.weekday(),
            "revenue": revenue,
            "cogs": cogs,
            "profit": revenue - cogs,
            "orders": len(data["orders"]) if data else 0,
            "has_data": data is not None,
        })
        current += timedelta(days=1)

    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "days": result,
    }


def daily_profits(days: int = 90) -> list[dict]:
    """Calculate daily profit only when evidence is complete."""
    return daily_summary(days)["days"]


def weekly_summary(days: int = 90) -> list[dict]:
    """Aggregate daily profits into weeks."""
    daily = daily_profits(days)
    weeks = []
    current_week = []

    for d in daily:
        current_week.append(d)
        if d["weekday_num"] == 6 or d == daily[-1]:  # Sunday or last day
            revenue = sum(x["revenue"] for x in current_week)
            cogs = sum(x["cogs"] for x in current_week)
            profit = revenue - cogs
            weeks.append({
                "start": current_week[0]["date"],
                "end": current_week[-1]["date"],
                "revenue": revenue,
                "cogs": cogs,
                "profit": profit,
                "days_with_sales": sum(1 for x in current_week if x["has_data"]),
                "orders": sum(x["orders"] for x in current_week),
                "best_day": max(current_week, key=lambda x: x["profit"])["date"] if current_week else "",
            })
            current_week = []

    return weeks


def monthly_summary(months: int = 6) -> list[dict]:
    """Monthly profit summary."""
    daily = daily_profits(months * 31)
    monthly = {}

    for d in daily:
        month_key = d["date"][:7]  # YYYY-MM
        if month_key not in monthly:
            monthly[month_key] = {"revenue": 0, "cogs": 0, "days": 0}
        monthly[month_key]["revenue"] += d["revenue"]
        monthly[month_key]["cogs"] += d["cogs"]
        if d["has_data"]:
            monthly[month_key]["days"] += 1

    result = []
    for k in sorted(monthly.keys()):
        m = monthly[k]
        result.append({
            "month": k,
            "revenue": m["revenue"],
            "cogs": m["cogs"],
            "profit": m["revenue"] - m["cogs"],
            "days_with_sales": m["days"],
        })

    return result


def best_worst_days(days: int = 90, top: int = 5) -> dict:
    """Find the best and worst profit days."""
    daily = [d for d in daily_profits(days) if d["has_data"]]
    if not daily:
        return {"best": [], "worst": []}

    by_profit = sorted(daily, key=lambda x: x["profit"], reverse=True)
    return {
        "best": by_profit[:top],
        "worst": by_profit[-top:],
    }
