"""Product Score — evidence-bounded performance rank per SKU.

Score = weighted composite of revenue, margin, velocity, stock health.
Used to identify stars, cash cows, dogs, and question marks.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math

import db
from order_dates import order_business_date


WEIGHTS = {
    "revenue": 0.35,
    "margin": 0.30,
    "velocity": 0.25,
    "stock": 0.10,
}

_REVENUE_STATUSES = {"paid", "confirmed", "shipped", "delivered", "completed"}


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


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    max_v = max(values)
    if max_v == 0:
        return [0.0] * len(values)
    return [value / max_v for value in values]


def _analysis(days: int = 30) -> dict:
    if isinstance(days, bool) or not isinstance(days, int) or days < 1:
        raise ValueError("days must be a positive integer")

    today = order_business_date(datetime.now(timezone.utc))
    cutoff = today - timedelta(days=days - 1)
    with db.conn() as connection:
        products = [dict(row) for row in connection.execute(
            "SELECT sku,name,cost_price,sell_price,stock FROM products ORDER BY sku"
        )]
        orders = [dict(row) for row in connection.execute(
            """SELECT order_id,sku,platform,qty,total_price,order_date,status
               FROM orders"""
        )]

    product_by_sku: dict[str, dict] = {}
    duplicate_skus: set[str] = set()
    missing_products = 0
    for product in products:
        sku = str(product["sku"]).strip() if _nonblank(product["sku"]) else ""
        cost = _number(product["cost_price"])
        sell = _number(product["sell_price"])
        stock = _number(product["stock"])
        margin_pct = (
            (sell - cost) / sell * 100
            if sell is not None and sell > 0 and cost is not None else None
        )
        if (
            not sku
            or cost is None or cost < 0
            or sell is None or sell <= 0
            or stock is None or stock < 0
            or margin_pct is None or not math.isfinite(margin_pct) or margin_pct < 0
        ):
            missing_products += 1
            continue
        if sku in product_by_sku:
            if sku not in duplicate_skus:
                missing_products += 1
            duplicate_skus.add(sku)
            missing_products += 1
            product_by_sku.pop(sku, None)
            continue
        if sku in duplicate_skus:
            missing_products += 1
            continue
        product_by_sku[sku] = {
            **product,
            "sku": sku,
            "_cost": cost,
            "_sell": sell,
            "_stock": stock,
            "_margin_pct": margin_pct,
        }

    aggregates = {
        sku: {"qty": 0.0, "revenue": 0.0}
        for sku in product_by_sku
    }
    missing_orders = 0
    for order in orders:
        status = str(order["status"]).strip().lower() if _nonblank(order["status"]) else ""
        if status not in _REVENUE_STATUSES:
            continue

        business_date = order_business_date(order["order_date"])
        if business_date is None or business_date > today:
            missing_orders += 1
            continue
        if business_date < cutoff:
            continue

        sku = str(order["sku"]).strip() if _nonblank(order["sku"]) else ""
        qty = _number(order["qty"])
        revenue = _number(order["total_price"])
        if (
            not all(_nonblank(order[key]) for key in ("order_id", "sku"))
            or sku not in product_by_sku
            or qty is None or qty < 0
            or revenue is None or revenue < 0
        ):
            missing_orders += 1
            continue
        next_qty = aggregates[sku]["qty"] + qty
        next_revenue = aggregates[sku]["revenue"] + revenue
        if not math.isfinite(next_qty) or not math.isfinite(next_revenue):
            missing_orders += 1
            continue
        aggregates[sku]["qty"] = next_qty
        aggregates[sku]["revenue"] = next_revenue

    if missing_products or missing_orders:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": missing_orders,
            "missing_product_evidence_rows": missing_products,
            "items": [],
        }

    raw = []
    for sku, product in product_by_sku.items():
        revenue = aggregates[sku]["revenue"]
        qty = aggregates[sku]["qty"]
        stock = product["_stock"]
        margin_pct = product["_margin_pct"]
        velocity = qty / days
        stock_score = (
            min(stock / max(velocity * 30, 1), 2)
            if velocity > 0 else (1 if stock > 0 else 0)
        )
        raw.append({
            "sku": sku,
            "name": product["name"],
            "revenue": revenue,
            "margin_pct": round(margin_pct, 1),
            "velocity": round(velocity, 2),
            "stock": stock,
            "stock_score": stock_score,
        })

    rev_norm = _normalize([item["revenue"] for item in raw])
    mar_norm = _normalize([item["margin_pct"] for item in raw])
    vel_norm = _normalize([item["velocity"] for item in raw])
    stk_norm = _normalize([item["stock_score"] for item in raw])

    result = []
    for index, item in enumerate(raw):
        score = (
            rev_norm[index] * WEIGHTS["revenue"]
            + mar_norm[index] * WEIGHTS["margin"]
            + vel_norm[index] * WEIGHTS["velocity"]
            + stk_norm[index] * WEIGHTS["stock"]
        ) * 100
        quadrant = _quadrant(item["revenue"], item["margin_pct"])
        result.append({
            **item,
            "score": round(score, 1),
            "quadrant": quadrant,
            "quadrant_icon": {
                "star": "⭐", "cash_cow": "🐄", "question": "❓", "dog": "🐕",
            }.get(quadrant, "?"),
        })

    result.sort(key=lambda item: item["score"], reverse=True)
    for index, item in enumerate(result):
        item["rank"] = index + 1

    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": result,
    }


def calculate(days: int = 30) -> list[dict]:
    """Return scores only when the selected window's evidence is complete."""
    return _analysis(days)["items"]


def _quadrant(revenue: float, margin_pct: float) -> str:
    high_rev = revenue > 0
    high_mar = margin_pct >= 25
    if high_rev and high_mar:
        return "star"
    if high_rev and not high_mar:
        return "cash_cow"
    if not high_rev and high_mar:
        return "question"
    return "dog"


def top_performers(n: int = 10) -> list:
    return calculate()[:n]


def bottom_performers(n: int = 10) -> list:
    return list(reversed(calculate()))[:n]


def by_quadrant(quadrant: str) -> list:
    return [product for product in calculate() if product["quadrant"] == quadrant]


def summary(days: int = 30) -> dict:
    analysis = _analysis(days)
    evidence = {
        "evidence_complete": analysis["evidence_complete"],
        "missing_order_evidence_rows": analysis["missing_order_evidence_rows"],
        "missing_product_evidence_rows": analysis["missing_product_evidence_rows"],
        "items": analysis["items"],
    }
    if not analysis["evidence_complete"]:
        return {
            **evidence,
            "total_skus": None,
            "avg_score": None,
            "quadrants": None,
        }

    scored = analysis["items"]
    quadrants = {"star": 0, "cash_cow": 0, "question": 0, "dog": 0}
    for product in scored:
        quadrants[product["quadrant"]] += 1
    avg_score = sum(product["score"] for product in scored) / len(scored) if scored else 0
    return {
        **evidence,
        "total_skus": len(scored),
        "avg_score": round(avg_score, 1),
        "quadrants": quadrants,
    }
