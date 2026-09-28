"""SKU performance trends backed by canonical order evidence."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import math

import db
from order_dates import order_business_date



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


_canonical_date = order_business_date


def _created_date(value) -> date | None:
    """Accept the canonical SQLite timestamp as well as an ISO date."""
    if not _nonblank(value):
        return None
    raw = str(value).strip()
    try:
        parsed = (
            date.fromisoformat(raw)
            if len(raw) == 10 else datetime.fromisoformat(raw).date()
        )
    except ValueError:
        return None
    return parsed


def trend_summary(weeks: int = 4) -> dict:
    """Return rolling seven-day SKU trends when in-window evidence is complete."""
    if isinstance(weeks, bool) or not isinstance(weeks, int) or weeks < 1:
        raise ValueError("weeks must be a positive integer")

    today = date.today()
    end_exclusive = today + timedelta(days=1)
    oldest = end_exclusive - timedelta(days=weeks * 7)
    with db.conn() as c:
        orders = [dict(row) for row in c.execute(
            "SELECT order_id,sku,platform,qty,total_price,order_date,status FROM orders"
        )]
        products = [dict(row) for row in c.execute("SELECT sku,name FROM products")]

    product_names = {
        str(product["sku"]).strip(): product["name"] or ""
        for product in products
        if _nonblank(product["sku"])
    }
    included = []
    missing_orders = 0
    for order in orders:
        order_date = _canonical_date(order["order_date"])
        if order_date is None:
            # A malformed date has unknown window membership.
            missing_orders += 1
            continue
        if order_date < oldest or order_date >= end_exclusive:
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

        week_index = (end_exclusive - order_date - timedelta(days=1)).days // 7
        included.append({
            "sku": sku,
            "qty": qty,
            "total": total,
            "week_index": week_index,
        })

    if missing_orders:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": missing_orders,
            "missing_product_evidence_rows": 0,
            "items": [],
        }

    results: dict[str, dict] = {}
    for order in included:
        sku = order["sku"]
        result = results.setdefault(sku, {
            "sku": sku,
            "name": product_names.get(sku, ""),
            "weeks": {},
        })
        label = "This Week" if order["week_index"] == 0 else f"W-{order['week_index']}"
        values = result["weeks"].setdefault(label, {"qty": 0.0, "revenue": 0.0})
        values["qty"] += order["qty"]
        values["revenue"] += order["total"]

    items = []
    for sku, data in results.items():
        this_week = data["weeks"].get("This Week", {})
        last_week = data["weeks"].get("W-1", {})
        qty_now = this_week.get("qty", 0.0)
        qty_prev = last_week.get("qty", 0.0)
        rev_now = this_week.get("revenue", 0.0)
        rev_prev = last_week.get("revenue", 0.0)
        qty_change = (
            (qty_now - qty_prev) / qty_prev * 100
            if qty_prev > 0 else (100 if qty_now > 0 else 0)
        )
        rev_change = (
            (rev_now - rev_prev) / rev_prev * 100
            if rev_prev > 0 else (100 if rev_now > 0 else 0)
        )
        trend = "rising" if qty_change > 20 else (
            "declining" if qty_change < -20 else "stable"
        )
        items.append({
            "sku": sku,
            "name": data["name"],
            "qty_this_week": qty_now,
            "qty_last_week": qty_prev,
            "qty_change_pct": round(qty_change, 1),
            "rev_this_week": rev_now,
            "rev_last_week": rev_prev,
            "rev_change_pct": round(rev_change, 1),
            "trend": trend,
            "weeks": data["weeks"],
        })

    items.sort(key=lambda item: item["rev_change_pct"], reverse=True)
    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": items,
    }


def weekly_trend(weeks: int = 4) -> list[dict]:
    """Per-SKU sales trend across rolling seven-day windows."""
    return trend_summary(weeks)["items"]


def rising_stars(min_change: float = 20) -> list[dict]:
    """Products with significant unit growth."""
    return [
        item for item in weekly_trend()
        if item["qty_change_pct"] > min_change and item["qty_this_week"] >= 3
    ]


def declining(min_change: float = -20) -> list[dict]:
    """Products losing unit momentum."""
    return [item for item in weekly_trend() if item["qty_change_pct"] < min_change]


def new_products_summary(days: int = 14) -> dict:
    """Return early performance for products provably created in the period."""
    if isinstance(days, bool) or not isinstance(days, int) or days < 0:
        raise ValueError("days must be a non-negative integer")

    today = date.today()
    cutoff = today - timedelta(days=days)
    with db.conn() as c:
        products = [dict(row) for row in c.execute(
            "SELECT sku,name,stock,sell_price,created_at FROM products"
        )]
        orders = [dict(row) for row in c.execute(
            "SELECT order_id,sku,platform,qty,total_price,order_date,status FROM orders"
        )]

    selected: dict[str, dict] = {}
    missing_products = 0
    duplicate_skus: set[str] = set()
    for product in products:
        created = _created_date(product["created_at"])
        if created is None:
            missing_products += 1
            continue
        if created < cutoff or created > today:
            continue
        if not _nonblank(product["sku"]):
            missing_products += 1
            continue
        sku = str(product["sku"]).strip()
        if sku in selected:
            first_collision = sku not in duplicate_skus
            duplicate_skus.add(sku)
            missing_products += 2 if first_collision else 1
            continue
        selected[sku] = {**product, "_created_date": created}

    for sku in duplicate_skus:
        selected.pop(sku, None)

    if not selected and not missing_products:
        return {
            "evidence_complete": True,
            "missing_order_evidence_rows": 0,
            "missing_product_evidence_rows": 0,
            "items": [],
        }

    aggregates = {
        sku: {"total_sold": 0.0, "total_revenue": 0.0}
        for sku in selected
    }
    missing_orders = 0
    for order in orders:
        status = str(order["status"]).strip().lower() if _nonblank(order["status"]) else ""
        if status in {"cancelled", "returned"}:
            continue
        if not _nonblank(order["sku"]):
            order_date = _canonical_date(order["order_date"])
            if order_date is not None and (order_date < cutoff or order_date > today):
                continue
            # Neither SKU nor an in-scope date can exclude the row.
            missing_orders += 1
            continue
        sku = str(order["sku"]).strip()
        if sku not in selected:
            continue

        if not status:
            missing_orders += 1
            continue
        order_date = _canonical_date(order["order_date"])
        if order_date is None:
            missing_orders += 1
            continue
        if order_date < selected[sku]["_created_date"] or order_date > today:
            continue
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
        aggregates[sku]["total_sold"] += qty
        aggregates[sku]["total_revenue"] += total

    if missing_orders or missing_products:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": missing_orders,
            "missing_product_evidence_rows": missing_products,
            "items": [],
        }

    items = []
    for sku, product in selected.items():
        items.append({
            "sku": sku,
            "name": product["name"],
            "stock": product["stock"],
            "sell_price": product["sell_price"],
            **aggregates[sku],
        })
    items.sort(key=lambda item: item["total_sold"], reverse=True)
    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": items,
    }


def new_products(days: int = 14) -> list[dict]:
    """Recently added products and their early performance."""
    return new_products_summary(days)["items"]


def summary() -> dict:
    analysis = trend_summary()
    if not analysis["evidence_complete"]:
        return {
            **analysis,
            "total_skus": None,
            "rising": None,
            "declining": None,
            "stable": None,
            "top_gainer": None,
            "top_gainer_pct": None,
            "top_loser": None,
            "top_loser_pct": None,
        }

    trends = analysis["items"]
    rising = [item for item in trends if item["trend"] == "rising"]
    declining_ = [item for item in trends if item["trend"] == "declining"]
    stable = [item for item in trends if item["trend"] == "stable"]
    return {
        **analysis,
        "total_skus": len(trends),
        "rising": len(rising),
        "declining": len(declining_),
        "stable": len(stable),
        "top_gainer": rising[0]["sku"] if rising else "—",
        "top_gainer_pct": rising[0]["rev_change_pct"] if rising else 0,
        "top_loser": declining_[-1]["sku"] if declining_ else "—",
        "top_loser_pct": declining_[-1]["rev_change_pct"] if declining_ else 0,
    }
