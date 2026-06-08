"""Monthly P&L Report — one page that shows THE TRUTH.

Revenue (from orders)
- Cost of goods (from products.cost_price × qty)
- Platform fees (from fees.py)
- Expenses (from expenses.py)
- Return losses (from returns.py)
= TRUE NET PROFIT

Exportable as CSV for accountant / tax filing."""
from __future__ import annotations

from datetime import datetime, timedelta

import db


def monthly_pnl(month: str) -> dict:
    """Generate P&L for a given month (format: '2026-06').
    Returns revenue, cost, fees, expenses, returns, net profit."""

    with db.conn() as c:
        # Revenue + cost
        orders = c.execute(
            "SELECT o.qty, o.unit_price, o.total_price, o.platform, "
            "p.cost_price "
            "FROM orders o LEFT JOIN products p ON p.id = o.product_id "
            "WHERE o.order_date LIKE ?",
            (month + "%",),
        ).fetchall()

    revenue = sum(float(r["total_price"] or 0) for r in orders)
    cogs = sum(float(r["cost_price"] or 0) * int(r["qty"] or 1) for r in orders)
    order_count = len(orders)

    # Platform fees
    import fees as fees_mod
    fees_data = fees_mod.load()
    total_fees = sum(
        fees_mod.platform_fee(float(r["total_price"] or 0), r["platform"] or "", fees_data)
        for r in orders
    )

    # Expenses
    total_expenses = 0
    exp_breakdown = {}
    try:
        import expenses as exp
        exp.init()
        summary = exp.monthly_summary(month)
        total_expenses = summary["total"]
        exp_breakdown = summary["breakdown"]
    except Exception:
        pass

    # Returns
    total_returns = 0
    return_count = 0
    try:
        import returns as ret
        ret.init()
        with db.conn() as c:
            r = c.execute(
                "SELECT COUNT(*) as cnt, "
                "COALESCE(SUM(refund_amount),0) as refund, "
                "COALESCE(SUM(shipping_cost),0) as ship "
                "FROM returns WHERE return_date LIKE ?",
                (month + "%",),
            ).fetchone()
            total_returns = (r["refund"] or 0) + (r["ship"] or 0)
            return_count = r["cnt"] or 0
    except Exception:
        pass

    gross_profit = revenue - cogs
    net_profit = gross_profit - total_fees - total_expenses - total_returns
    net_margin = (net_profit / revenue * 100) if revenue > 0 else 0

    return {
        "month": month,
        "order_count": order_count,
        "revenue": round(revenue, 2),
        "cogs": round(cogs, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin": round((gross_profit / revenue * 100) if revenue else 0, 1),
        "platform_fees": round(total_fees, 2),
        "expenses": round(total_expenses, 2),
        "expense_breakdown": exp_breakdown,
        "returns_loss": round(total_returns, 2),
        "return_count": return_count,
        "net_profit": round(net_profit, 2),
        "net_margin": round(net_margin, 1),
    }


def multi_month_pnl(months: int = 6) -> list[dict]:
    now = datetime.now()
    results = []
    for i in range(months):
        d = now - timedelta(days=30 * i)
        m = d.strftime("%Y-%m")
        results.append(monthly_pnl(m))
    return list(reversed(results))


def to_csv(pnl: dict) -> str:
    lines = [
        "รายการ,จำนวน (฿)",
        f"รายได้ (Revenue),{pnl['revenue']:.0f}",
        f"ต้นทุนสินค้า (COGS),-{pnl['cogs']:.0f}",
        f"กำไรขั้นต้น (Gross Profit),{pnl['gross_profit']:.0f}",
        f"ค่าธรรมเนียม Platform,-{pnl['platform_fees']:.0f}",
        f"ค่าใช้จ่ายอื่น (Expenses),-{pnl['expenses']:.0f}",
    ]
    for cat, amt in pnl.get("expense_breakdown", {}).items():
        lines.append(f"  - {cat},-{amt:.0f}")
    lines.extend([
        f"ค่าคืนสินค้า (Returns),-{pnl['returns_loss']:.0f}",
        f"กำไรสุทธิ (Net Profit),{pnl['net_profit']:.0f}",
        f"Net Margin,{pnl['net_margin']:.1f}%",
        "",
        f"ออเดอร์ทั้งหมด,{pnl['order_count']}",
        f"สินค้าคืน,{pnl['return_count']}",
    ])
    return "\n".join(lines)
