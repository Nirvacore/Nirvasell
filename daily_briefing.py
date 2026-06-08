"""Daily Briefing — morning summary of what to do today.

Auto-generated: yesterday's results, today's tasks, alerts.
The seller opens this page once and knows everything."""
from __future__ import annotations

from datetime import datetime, timedelta, date

import db


def generate() -> dict:
    """Generate today's briefing."""
    today = date.today().strftime("%Y-%m-%d")
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    briefing = {
        "date": today,
        "yesterday": _yesterday_summary(yesterday),
        "today_tasks": _today_tasks(today),
        "alerts": _alerts(),
        "quick_stats": _quick_stats(),
    }

    return briefing


def _yesterday_summary(yesterday: str) -> dict:
    with db.conn() as c:
        orders = c.execute(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(total_amount), 0) AS rev "
            "FROM orders WHERE order_date = ?", (yesterday,)
        ).fetchone()

        new_customers = c.execute("""
            SELECT COUNT(DISTINCT COALESCE(buyer_phone, buyer_name)) AS cnt
            FROM orders WHERE order_date = ?
        """, (yesterday,)).fetchone()

    return {
        "orders": orders["cnt"] if orders else 0,
        "revenue": orders["rev"] if orders else 0,
        "new_customers": new_customers["cnt"] if new_customers else 0,
    }


def _today_tasks(today: str) -> list[dict]:
    tasks = []

    # 1. Pending orders to ship
    with db.conn() as c:
        pending = c.execute(
            "SELECT COUNT(*) AS cnt FROM orders WHERE status IN ('pending','confirmed')"
        ).fetchone()
    if pending and pending["cnt"] > 0:
        tasks.append({
            "icon": "📦",
            "task": "Ship " + str(pending["cnt"]) + " pending orders",
            "task_th": "จัดส่ง " + str(pending["cnt"]) + " ออเดอร์ค้าง",
            "priority": "high",
            "page": "PickPack",
        })

    # 2. Low stock items
    with db.conn() as c:
        low = c.execute(
            "SELECT COUNT(*) AS cnt FROM products WHERE stock > 0 AND stock <= 5"
        ).fetchone()
    if low and low["cnt"] > 0:
        tasks.append({
            "icon": "⚠️",
            "task": str(low["cnt"]) + " items low stock",
            "task_th": str(low["cnt"]) + " สินค้าสต็อกต่ำ",
            "priority": "high",
            "page": "Turnover",
        })

    # 3. COD to collect
    try:
        with db.conn() as c:
            cod = c.execute(
                "SELECT COUNT(*) AS cnt FROM cod_orders WHERE status='delivered'"
            ).fetchone()
        if cod and cod["cnt"] > 0:
            tasks.append({
                "icon": "💰",
                "task": "Collect " + str(cod["cnt"]) + " COD payments",
                "task_th": "เก็บเงิน COD " + str(cod["cnt"]) + " รายการ",
                "priority": "medium",
                "page": "COD",
            })
    except Exception:
        pass

    # 4. Follow-ups due
    try:
        import customer_crm as crm
        crm.init()
        followups = crm.pending_followups()
        today_followups = [f for f in followups if f["followup_date"] <= today]
        if today_followups:
            tasks.append({
                "icon": "💬",
                "task": str(len(today_followups)) + " customer follow-ups due",
                "task_th": str(len(today_followups)) + " ลูกค้าต้องติดตาม",
                "priority": "medium",
                "page": "CRM",
            })
    except Exception:
        pass

    # 5. Content to post
    try:
        import content_calendar as cal
        cal.init()
        today_posts = cal.today_posts()
        if today_posts:
            tasks.append({
                "icon": "📱",
                "task": str(len(today_posts)) + " posts scheduled for today",
                "task_th": str(len(today_posts)) + " โพสต์ที่นัดไว้วันนี้",
                "priority": "medium",
                "page": "Calendar",
            })
    except Exception:
        pass

    # 6. Out of stock
    with db.conn() as c:
        oos = c.execute(
            "SELECT COUNT(*) AS cnt FROM products WHERE stock <= 0"
        ).fetchone()
    if oos and oos["cnt"] > 0:
        tasks.append({
            "icon": "🔴",
            "task": str(oos["cnt"]) + " items out of stock",
            "task_th": str(oos["cnt"]) + " สินค้าหมด",
            "priority": "high",
            "page": "Products",
        })

    return sorted(tasks, key=lambda t: {"high": 0, "medium": 1, "low": 2}[t["priority"]])


def _alerts() -> list[dict]:
    alerts = []

    # High return rate
    try:
        import returns as ret
        ret.init()
        s = ret.stats()
        if s.get("return_rate", 0) > 5:
            alerts.append({
                "icon": "↩️",
                "level": "danger",
                "msg": "Return rate " + str(round(s["return_rate"], 1)) + "% — above 5% threshold",
                "msg_th": "อัตราคืนสินค้า " + str(round(s["return_rate"], 1)) + "% — เกิน 5%",
            })
    except Exception:
        pass

    # Negative cash flow
    try:
        import cashflow as cf
        f = cf.forecast(30)
        if f.get("health") == "danger":
            alerts.append({
                "icon": "💧",
                "level": "danger",
                "msg": "Cash flow negative for next 30 days!",
                "msg_th": "กระแสเงินสดติดลบ 30 วันข้างหน้า!",
            })
    except Exception:
        pass

    return alerts


def _quick_stats() -> dict:
    """MTD quick stats."""
    month_start = date.today().replace(day=1).strftime("%Y-%m-%d")
    with db.conn() as c:
        mtd = c.execute("""
            SELECT COUNT(*) AS orders, COALESCE(SUM(total_amount), 0) AS revenue
            FROM orders WHERE order_date >= ?
        """, (month_start,)).fetchone()

        products = c.execute("SELECT COUNT(*) AS cnt FROM products").fetchone()

    return {
        "mtd_orders": mtd["orders"] if mtd else 0,
        "mtd_revenue": mtd["revenue"] if mtd else 0,
        "total_products": products["cnt"] if products else 0,
    }
