"""Stock Turnover Analysis — how fast does inventory move?

Key metrics:
  - Turnover Rate = COGS / Average Inventory (higher = better)
  - Days of Inventory (DOI) = 365 / Turnover Rate
  - Reorder Point = Daily Sales × Lead Days + Safety Stock

Thai resellers with thin margins can't afford slow-moving stock.
Fast turnover = more cash cycles per year = more profit."""
from __future__ import annotations

from datetime import date, datetime
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


def _nonnegative_number(value) -> bool:
    number = _number(value)
    return number is not None and number >= 0


def _canonical_date(value) -> date | None:
    if not _nonblank(value):
        return None
    raw = str(value).strip()
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None
    return parsed if parsed.isoformat() == raw else None


def _analysis() -> dict:
    """Build turnover only from complete canonical product/order evidence."""
    with db.conn() as c:
        products = [dict(row) for row in c.execute(
            "SELECT sku,name,stock,cost_price,sell_price FROM products"
        )]
        orders = [dict(row) for row in c.execute(
            "SELECT order_id,sku,platform,qty,order_date,status FROM orders"
        )]

    missing_products = sum(
        1 for product in products
        if (not _nonblank(product["sku"])
            or not _nonnegative_number(product["stock"])
            or not _nonnegative_number(product["cost_price"]))
    )
    product_by_sku = {
        str(product["sku"]).strip(): product
        for product in products
        if _nonblank(product["sku"])
    }

    valid_orders = []
    missing_orders = 0
    today = date.today()
    for order in orders:
        status = str(order["status"]).strip().lower() if _nonblank(order["status"]) else ""
        if not status:
            missing_orders += 1
            continue
        if status in {"cancelled", "returned"}:
            continue

        order_date = _canonical_date(order["order_date"])
        qty = _number(order["qty"])
        sku = str(order["sku"]).strip() if _nonblank(order["sku"]) else ""
        if (
            not all(_nonblank(order[key]) for key in ("order_id", "platform", "sku"))
            or qty is None
            or qty < 0
            or order_date is None
            or order_date > today
            or sku not in product_by_sku
        ):
            missing_orders += 1
            continue

        order["_date"] = order_date
        order["_qty"] = qty
        order["_sku"] = sku
        valid_orders.append(order)

    if missing_products or missing_orders:
        return {
            "evidence_complete": False,
            "missing_order_evidence_rows": missing_orders,
            "missing_product_evidence_rows": missing_products,
            "items": [],
        }

    aggregates = {
        sku: {"total_sold": 0.0, "orders": set(), "dates": []}
        for sku in product_by_sku
    }
    for order in valid_orders:
        aggregate = aggregates[order["_sku"]]
        aggregate["total_sold"] += order["_qty"]
        aggregate["orders"].add((str(order["platform"]).strip(),
                                 str(order["order_id"]).strip()))
        aggregate["dates"].append(order["_date"])

    items = []
    for sku, product in product_by_sku.items():
        aggregate = aggregates[sku]
        stock = _number(product["stock"])
        cost = _number(product["cost_price"])
        sold = aggregate["total_sold"]

        # Trading period
        first_sale = min(aggregate["dates"]) if aggregate["dates"] else None
        if first_sale:
            trading_days = max((today - first_sale).days, 1)
        else:
            trading_days = 0

        # Daily sales velocity
        daily_sales = sold / trading_days if trading_days > 0 else 0

        # Stock value
        stock_value = stock * cost

        # COGS for period
        cogs_total = sold * cost

        # Average inventory (simple: current stock as proxy)
        avg_inventory_value = stock_value

        # Turnover rate (annualized)
        if sold == 0:
            turnover_rate = 0.0
        elif trading_days > 0 and avg_inventory_value > 0:
            turnover_rate = (cogs_total / avg_inventory_value) * (365 / trading_days)
        else:
            turnover_rate = None

        # Days of inventory
        doi = round(stock / daily_sales, 0) if daily_sales > 0 else 999

        # Reorder point (assume 7-day lead time + 3 days safety)
        lead_days = 7
        safety_days = 3
        reorder_point = round(daily_sales * (lead_days + safety_days), 0)

        # Health status
        if doi <= 14:
            health = "fast"
        elif doi <= 30:
            health = "good"
        elif doi <= 60:
            health = "slow"
        else:
            health = "stuck"

        d = dict(product)
        d["sku"] = sku
        d["total_sold"] = sold
        d["order_count"] = len(aggregate["orders"])
        d["first_sale"] = first_sale.isoformat() if first_sale else None
        d["last_sale"] = max(aggregate["dates"]).isoformat() if aggregate["dates"] else None
        d["daily_sales"] = round(daily_sales, 2)
        d["stock_value"] = round(stock_value, 0)
        d["turnover_rate"] = round(turnover_rate, 1) if turnover_rate is not None else None
        d["turnover_available"] = turnover_rate is not None
        d["doi"] = int(min(doi, 999))
        d["reorder_point"] = int(reorder_point)
        d["needs_reorder"] = stock <= reorder_point and daily_sales > 0
        d["health"] = health
        d["trading_days"] = trading_days

        items.append(d)

    items.sort(key=lambda item: item["total_sold"], reverse=True)
    return {
        "evidence_complete": True,
        "missing_order_evidence_rows": 0,
        "missing_product_evidence_rows": 0,
        "items": items,
    }


def calculate() -> list[dict]:
    """Calculate stock turnover for each SKU when evidence is complete."""
    return _analysis()["items"]


def summary() -> dict:
    """Overall stock turnover summary."""
    analysis = _analysis()
    items = analysis["items"]
    evidence = {
        "evidence_complete": analysis["evidence_complete"],
        "missing_order_evidence_rows": analysis["missing_order_evidence_rows"],
        "missing_product_evidence_rows": analysis["missing_product_evidence_rows"],
        "items": items,
    }
    if not analysis["evidence_complete"]:
        return {
            **evidence,
            "total_skus": None,
            "avg_turnover": None,
            "avg_doi": None,
            "total_stock_value": None,
            "need_reorder": None,
            "health": None,
        }
    if not items:
        return {
            **evidence,
            "total_skus": 0,
            "avg_turnover": 0,
            "avg_doi": 0,
            "total_stock_value": 0,
            "need_reorder": 0,
            "health": {"fast": 0, "good": 0, "slow": 0, "stuck": 0},
        }

    health = {"fast": 0, "good": 0, "slow": 0, "stuck": 0}
    for i in items:
        health[i["health"]] = health.get(i["health"], 0) + 1

    selling = [i for i in items if i["daily_sales"] > 0]
    turnover_values = [i["turnover_rate"] for i in selling if i["turnover_rate"] is not None]
    avg_turnover = (
        sum(turnover_values) / len(turnover_values)
        if len(turnover_values) == len(selling) and selling else
        (0 if not selling else None)
    )
    avg_doi = (sum(i["doi"] for i in selling) / len(selling)) if selling else 0

    return {
        **evidence,
        "total_skus": len(items),
        "avg_turnover": round(avg_turnover, 1) if avg_turnover is not None else None,
        "avg_doi": int(avg_doi),
        "total_stock_value": sum(i["stock_value"] for i in items),
        "need_reorder": sum(1 for i in items if i["needs_reorder"]),
        "health": health,
    }


def reorder_list() -> list[dict]:
    """Products that need reordering."""
    return [i for i in calculate() if i["needs_reorder"]]
