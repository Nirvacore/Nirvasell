"""Channel Performance — compare revenue/orders/margin across selling platforms."""
from __future__ import annotations
import db
from i18n_inline import channel_fee_label, platform_name

CHANNELS = {
    "shopee":      {"icon": "🟠", "color": "#f26222"},
    "lazada":      {"icon": "🔵", "color": "#0d1a8b"},
    "tiktok_shop": {"icon": "⚫", "color": "#2d2d2d"},
    "facebook":    {"icon": "🔷", "color": "#1877f2"},
    "line":        {"icon": "🟢", "color": "#06c755"},
    "instagram":   {"icon": "🌸", "color": "#e1306c"},
    "website":     {"icon": "🌐", "color": "#4d6c5c"},
    "direct":      {"icon": "📞", "color": "#9a7569"},
    "other":       {"icon": "📌", "color": "#9a9485"},
}

PLATFORM_FEES = {
    "shopee":      {"pct": 3.5},
    "lazada":      {"pct": 4.0},
    "tiktok_shop": {"pct": 2.0},
    "facebook":    {"pct": 0.0},
    "line":        {"pct": 0.0},
    "instagram":   {"pct": 0.0},
    "website":     {"pct": 0.0},
    "direct":      {"pct": 0.0},
    "other":       {"pct": 0.0},
}


def channel_stats(days: int = 30) -> list[dict]:
    """Revenue, orders, avg order value per channel for last N days."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT "
            "  COALESCE(platform,'direct') platform, "
            "  COUNT(*) orders, "
            "  COALESCE(SUM(total_price),0) revenue, "
            "  COALESCE(AVG(total_price),0) avg_order "
            "FROM orders "
            "WHERE date(order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND status NOT IN ('cancelled','returned') "
            "GROUP BY COALESCE(platform,'direct') "
            "ORDER BY revenue DESC",
            (days,),
        ).fetchall()
        total_rev = sum(r["revenue"] for r in rows) or 1
        result = []
        for r in rows:
            ch = CHANNELS.get(r["platform"], CHANNELS["other"])
            fee_pct = PLATFORM_FEES.get(r["platform"], {}).get("pct", 0)
            revenue = r["revenue"]
            fees = round(revenue * fee_pct / 100, 2)
            share = round(revenue / total_rev * 100, 1)
            result.append({
                "platform": r["platform"],
                "label": platform_name(r["platform"]),
                "fee_label": channel_fee_label(r["platform"]),
                "icon": ch["icon"],
                "color": ch["color"],
                "orders": r["orders"],
                "revenue": round(revenue, 2),
                "avg_order": round(r["avg_order"], 2),
                "platform_fees": fees,
                "net_revenue": round(revenue - fees, 2),
                "share_pct": share,
            })
        return result


def channel_trend(channel: str, weeks: int = 8) -> list[dict]:
    """Weekly revenue trend for a specific channel."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT strftime('%Y-W%W', order_date) week, "
            "  COUNT(*) orders, COALESCE(SUM(total_price),0) revenue "
            "FROM orders "
            "WHERE COALESCE(platform,'direct')=? "
            "  AND date(order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND status NOT IN ('cancelled','returned') "
            "GROUP BY week ORDER BY week",
            (channel, weeks * 7),
        ).fetchall()
        return [dict(r) for r in rows]


def top_skus_by_channel(channel: str, days: int = 30,
                         limit: int = 5) -> list[dict] | None:
    """Return ranked SKUs, or None when eligible line evidence is incomplete."""
    with db.conn() as c:
        rows = c.execute(
            "WITH eligible AS ("
            "  SELECT o.sku, o.qty, o.total_price FROM orders o "
            "  WHERE COALESCE(o.platform,'direct')=? "
            "    AND date(o.order_date) >= date('now','-' || ? || ' days','localtime') "
            "    AND LOWER(o.status) NOT IN ('cancelled','returned')"
            "), evidence AS ("
            "  SELECT COUNT(*) source_rows, "
            "    COALESCE(SUM(CASE WHEN sku IS NULL OR TRIM(sku)='' THEN 1 ELSE 0 END),0) missing_sku_rows, "
            "    COALESCE(SUM(CASE WHEN qty IS NULL THEN 1 ELSE 0 END),0) missing_qty_rows, "
            "    COALESCE(SUM(CASE WHEN total_price IS NULL THEN 1 ELSE 0 END),0) missing_total_rows "
            "  FROM eligible"
            "), ranked AS ("
            "  SELECT sku, SUM(qty) total_qty, SUM(total_price) revenue "
            "  FROM eligible WHERE sku IS NOT NULL AND TRIM(sku)<>'' "
            "  GROUP BY sku ORDER BY revenue DESC, sku ASC LIMIT ?"
            ") SELECT e.source_rows, e.missing_sku_rows, e.missing_qty_rows, "
            "  e.missing_total_rows, r.sku, r.total_qty, r.revenue "
            "FROM evidence e LEFT JOIN ranked r ON 1=1 "
            "ORDER BY r.revenue DESC, r.sku ASC",
            (channel, days, limit),
        ).fetchall()
    evidence = dict(rows[0])
    if evidence["source_rows"] == 0:
        return []
    if any(
        evidence[field] > 0
        for field in ("missing_sku_rows", "missing_qty_rows", "missing_total_rows")
    ):
        return None
    return [
        {
            "sku": row["sku"],
            "total_qty": row["total_qty"],
            "revenue": row["revenue"],
        }
        for row in rows
        if row["sku"] is not None
    ]


def summary(days: int = 30) -> dict:
    stats = channel_stats(days)
    if not stats:
        return {"total_channels": 0, "top_channel": "—",
                "total_revenue": 0, "channel_count": 0}
    return {
        "total_channels": len(stats),
        "top_channel": stats[0]["label"] if stats else "—",
        "top_revenue": stats[0]["revenue"] if stats else 0,
        "total_revenue": sum(s["revenue"] for s in stats),
        "channel_count": len(stats),
    }
