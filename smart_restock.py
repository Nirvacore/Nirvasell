"""Smart Restock — predict when each SKU runs out + suggest reorder qty.

Thai resellers lose sales every day from stockouts they didn't see coming.
This module uses actual order history to calculate:
  - Average daily sales per SKU
  - Days until stockout at current velocity
  - Recommended reorder quantity (lead time × daily rate × safety buffer)

Wired into LINE Notify: alert when any SKU is predicted to run out in < 7 days."""
from __future__ import annotations

from datetime import datetime, timedelta

import db
import inventory as inv


def _sales_velocity(sku: str, lookback_days: int = 30) -> float:
    cutoff = (datetime.now() - timedelta(days=lookback_days)).isoformat()
    with db.conn() as c:
        row = c.execute(
            "SELECT COALESCE(SUM(qty), 0) as total_qty, "
            "COUNT(DISTINCT DATE(order_date)) as active_days "
            "FROM orders WHERE sku = ? AND order_date >= ?",
            (sku, cutoff),
        ).fetchone()
    total = row["total_qty"] if row else 0
    days = row["active_days"] if row else 0
    if days == 0:
        return 0.0
    return total / lookback_days


def predict_stockout(sku: str, current_stock: int,
                     lookback_days: int = 30) -> dict:
    velocity = _sales_velocity(sku, lookback_days)
    if velocity <= 0:
        return {
            "sku": sku,
            "stock": current_stock,
            "daily_sales": 0,
            "days_until_out": 999,
            "stockout_date": "",
            "status": "no_sales",
        }
    days = current_stock / velocity
    stockout_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
    if days <= 3:
        status = "critical"
    elif days <= 7:
        status = "warning"
    elif days <= 14:
        status = "watch"
    else:
        status = "ok"
    return {
        "sku": sku,
        "stock": current_stock,
        "daily_sales": round(velocity, 1),
        "days_until_out": round(days, 0),
        "stockout_date": stockout_date,
        "status": status,
    }


def reorder_qty(sku: str, current_stock: int, lead_days: int = 7,
                safety_buffer: float = 1.5, lookback_days: int = 30) -> dict:
    velocity = _sales_velocity(sku, lookback_days)
    if velocity <= 0:
        return {"sku": sku, "recommended": 0, "reason": "no_sales"}
    needed_during_lead = velocity * lead_days
    buffer = velocity * lead_days * (safety_buffer - 1)
    total = max(0, needed_during_lead + buffer - current_stock)
    return {
        "sku": sku,
        "recommended": int(round(total)),
        "daily_sales": round(velocity, 1),
        "lead_days": lead_days,
        "needed_during_lead": round(needed_during_lead),
        "buffer": round(buffer),
        "reason": "calculated",
    }


def all_predictions(low_threshold: int = 7) -> list[dict]:
    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name, stock, cost_price, sell_price FROM products"
        ).fetchall()
    results = []
    for p in products:
        stock_n = inv.parse_stock(p["stock"])
        pred = predict_stockout(p["sku"], stock_n)
        pred["name"] = p["name"]
        pred["cost_price"] = p["cost_price"]
        pred["sell_price"] = p["sell_price"]
        if pred["daily_sales"] > 0:
            ro = reorder_qty(p["sku"], stock_n)
            pred["reorder_qty"] = ro["recommended"]
        else:
            pred["reorder_qty"] = 0
        results.append(pred)
    results.sort(key=lambda r: r["days_until_out"])
    return results


def critical_skus(days_threshold: int = 7) -> list[dict]:
    preds = all_predictions()
    return [p for p in preds if p["days_until_out"] <= days_threshold
            and p["status"] != "no_sales"]


def send_low_stock_alerts():
    try:
        import user_settings as us
        us.init()
        token = us.get("line_notify_token", "")
        if not token or not us.get("line_alert_stock", True):
            return
        crits = critical_skus(days_threshold=7)
        if not crits:
            return
        import line_notify
        for p in crits[:5]:
            line_notify.notify_low_stock(
                token,
                sku=p["sku"],
                name=p.get("name", ""),
                remaining=p["stock"],
            )
    except Exception:
        pass
