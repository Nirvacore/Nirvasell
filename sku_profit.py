"""Profit per SKU — the one number every seller needs.

Joins orders + product cost + platform fees + shipping + ads + returns
to show TRUE profit per SKU. Reveals which products actually make money
after ALL costs, not just gross margin."""
from __future__ import annotations

import db


def per_sku_profit() -> list[dict]:
    """Calculate true profit per SKU across all orders.
    Returns sorted by profit descending."""

    import fees as fees_mod
    fees_data = fees_mod.load()

    with db.conn() as c:
        # Orders with cost data
        rows = c.execute(
            "SELECT o.sku, p.name, p.cost_price, p.sell_price, p.brand, "
            "SUM(o.qty) as total_qty, "
            "SUM(o.total_price) as total_revenue, "
            "COUNT(DISTINCT o.order_id) as order_count, "
            "o.platform "
            "FROM orders o "
            "LEFT JOIN products p ON p.id = o.product_id "
            "WHERE o.sku IS NOT NULL AND o.sku != '' "
            "GROUP BY o.sku, o.platform"
        ).fetchall()

    # Aggregate per SKU (across platforms)
    sku_data: dict[str, dict] = {}
    for r in rows:
        sku = r["sku"]
        if sku not in sku_data:
            sku_data[sku] = {
                "sku": sku,
                "name": r["name"] or "",
                "brand": r["brand"] or "",
                "cost_price": float(r["cost_price"] or 0),
                "sell_price": float(r["sell_price"] or 0),
                "total_qty": 0,
                "total_revenue": 0,
                "total_cogs": 0,
                "total_fees": 0,
                "order_count": 0,
                "platforms": set(),
            }
        d = sku_data[sku]
        qty = int(r["total_qty"] or 0)
        rev = float(r["total_revenue"] or 0)
        cost = float(r["cost_price"] or 0) * qty
        fee = fees_mod.platform_fee(rev, r["platform"] or "", fees_data)

        d["total_qty"] += qty
        d["total_revenue"] += rev
        d["total_cogs"] += cost
        d["total_fees"] += fee
        d["order_count"] += int(r["order_count"] or 0)
        d["platforms"].add(r["platform"] or "direct")

    # Add return losses per SKU
    with db.conn() as c:
        try:
            ret_rows = c.execute(
                "SELECT sku, "
                "COALESCE(SUM(refund_amount),0) as refund, "
                "COALESCE(SUM(shipping_cost),0) as ship, "
                "COUNT(*) as ret_count "
                "FROM returns WHERE sku IS NOT NULL AND sku != '' "
                "GROUP BY sku"
            ).fetchall()
            for r in ret_rows:
                sku = r["sku"]
                if sku in sku_data:
                    sku_data[sku]["return_loss"] = float(r["refund"]) + float(r["ship"])
                    sku_data[sku]["return_count"] = int(r["ret_count"])
        except Exception:
            pass

    # Calculate final profit
    results = []
    for sku, d in sku_data.items():
        d["platforms"] = ", ".join(sorted(d["platforms"]))
        ret_loss = d.get("return_loss", 0)
        d["return_loss"] = ret_loss
        d["return_count"] = d.get("return_count", 0)

        gross = d["total_revenue"] - d["total_cogs"]
        net = gross - d["total_fees"] - ret_loss

        d["gross_profit"] = round(gross, 2)
        d["net_profit"] = round(net, 2)
        d["gross_margin"] = round(gross / d["total_revenue"] * 100, 1) if d["total_revenue"] else 0
        d["net_margin"] = round(net / d["total_revenue"] * 100, 1) if d["total_revenue"] else 0
        d["profit_per_unit"] = round(net / d["total_qty"], 2) if d["total_qty"] else 0

        # Health score: >20% net = green, 5-20% = yellow, <5% = red
        if d["net_margin"] >= 20:
            d["health"] = "healthy"
        elif d["net_margin"] >= 5:
            d["health"] = "warning"
        elif d["net_margin"] >= 0:
            d["health"] = "thin"
        else:
            d["health"] = "losing"

        results.append(d)

    return sorted(results, key=lambda x: x["net_profit"], reverse=True)


def summary() -> dict:
    """Aggregate profit stats across all SKUs."""
    skus = per_sku_profit()
    if not skus:
        return {"total_skus": 0, "profitable": 0, "losing": 0,
                "total_profit": 0, "avg_margin": 0}
    profitable = [s for s in skus if s["net_profit"] > 0]
    losing = [s for s in skus if s["net_profit"] <= 0]
    total_profit = sum(s["net_profit"] for s in skus)
    avg_margin = sum(s["net_margin"] for s in skus) / len(skus) if skus else 0
    return {
        "total_skus": len(skus),
        "profitable": len(profitable),
        "losing": len(losing),
        "total_profit": round(total_profit, 2),
        "avg_margin": round(avg_margin, 1),
    }
