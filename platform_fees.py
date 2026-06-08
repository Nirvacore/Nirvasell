"""Platform Fee Calculator — Shopee / Lazada / TikTok actual fee breakdown."""
from __future__ import annotations

PLATFORMS = {
    "shopee": {
        "label": "Shopee",
        "icon": "🟠",
        "color": "#f26222",
        "fees": {
            "commission": 3.0,       # GP %
            "payment": 2.0,          # payment processing fee %
            "transaction": 0.0,      # transaction fee %
            "vat_on_fees": 7.0,      # VAT on commission
        },
        "notes": "ค่า GP 3% + Payment 2% + VAT on commission",
    },
    "lazada": {
        "label": "Lazada",
        "icon": "🔵",
        "color": "#0d1a8b",
        "fees": {
            "commission": 4.0,
            "payment": 1.5,
            "transaction": 0.0,
            "vat_on_fees": 7.0,
        },
        "notes": "ค่า GP 4% + Payment 1.5% + VAT",
    },
    "tiktok_shop": {
        "label": "TikTok Shop",
        "icon": "⚫",
        "color": "#2d2d2d",
        "fees": {
            "commission": 2.0,
            "payment": 1.0,
            "transaction": 0.0,
            "vat_on_fees": 7.0,
        },
        "notes": "ค่า GP 2% + Payment 1% + VAT (โปรโมชั่นช่วงแรก)",
    },
    "facebook": {
        "label": "Facebook",
        "icon": "🔷",
        "color": "#1877f2",
        "fees": {
            "commission": 0.0,
            "payment": 0.0,
            "transaction": 0.0,
            "vat_on_fees": 0.0,
        },
        "notes": "ไม่มีค่า GP (ขายตรงผ่าน Live/DM)",
    },
    "line": {
        "label": "Line OA",
        "icon": "🟢",
        "color": "#06c755",
        "fees": {
            "commission": 0.0,
            "payment": 1.5,
            "transaction": 0.0,
            "vat_on_fees": 0.0,
        },
        "notes": "ค่า Payment Gateway ถ้าใช้ LINE Pay",
    },
}


def calculate(platform: str, sale_price: float,
              cost_price: float = 0, qty: int = 1) -> dict:
    p = PLATFORMS.get(platform, PLATFORMS["shopee"])
    fees_cfg = p["fees"]
    revenue = sale_price * qty
    commission = round(revenue * fees_cfg["commission"] / 100, 2)
    payment_fee = round(revenue * fees_cfg["payment"] / 100, 2)
    transaction_fee = round(revenue * fees_cfg["transaction"] / 100, 2)
    vat_on_comm = round(commission * fees_cfg["vat_on_fees"] / 100, 2)
    total_fees = commission + payment_fee + transaction_fee + vat_on_comm
    net_revenue = revenue - total_fees
    cogs = cost_price * qty
    gross_profit = net_revenue - cogs
    margin_pct = round(gross_profit / revenue * 100, 1) if revenue > 0 else 0
    fee_pct = round(total_fees / revenue * 100, 1) if revenue > 0 else 0

    return {
        "platform": platform,
        "label": p["label"],
        "revenue": round(revenue, 2),
        "commission": commission,
        "payment_fee": payment_fee,
        "transaction_fee": transaction_fee,
        "vat_on_fees": vat_on_comm,
        "total_fees": round(total_fees, 2),
        "fee_pct": fee_pct,
        "net_revenue": round(net_revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "margin_pct": margin_pct,
        "notes": p["notes"],
    }


def compare_all(sale_price: float, cost_price: float = 0,
                qty: int = 1) -> list[dict]:
    return [calculate(p, sale_price, cost_price, qty) for p in PLATFORMS]


def best_platform(sale_price: float, cost_price: float = 0) -> dict:
    results = compare_all(sale_price, cost_price)
    return max(results, key=lambda r: r["gross_profit"])


def fee_summary_from_orders(days: int = 30) -> list[dict]:
    import db
    with db.conn() as c:
        rows = c.execute(
            "SELECT COALESCE(platform,'direct') platform, "
            "  COALESCE(SUM(total_price),0) revenue, "
            "  COUNT(*) orders "
            "FROM orders "
            "WHERE date(order_date) >= date('now','-' || ? || ' days','localtime') "
            "  AND status NOT IN ('cancelled','returned') "
            "GROUP BY COALESCE(platform,'direct')",
            (days,),
        ).fetchall()
    result = []
    for r in rows:
        p = PLATFORMS.get(r["platform"], PLATFORMS.get("shopee"))
        fees_cfg = p["fees"]
        rev = r["revenue"]
        commission = round(rev * fees_cfg["commission"] / 100, 2)
        payment_fee = round(rev * fees_cfg["payment"] / 100, 2)
        vat_on_comm = round(commission * fees_cfg["vat_on_fees"] / 100, 2)
        total_fees = commission + payment_fee + vat_on_comm
        result.append({
            "platform": r["platform"],
            "label": p["label"],
            "revenue": round(rev, 2),
            "orders": r["orders"],
            "total_fees": round(total_fees, 2),
            "net_revenue": round(rev - total_fees, 2),
            "fee_pct": round(total_fees / rev * 100, 1) if rev > 0 else 0,
        })
    result.sort(key=lambda x: x["revenue"], reverse=True)
    return result
