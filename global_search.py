"""Global Search — search across products, orders, and customers in one query.

One search box to find anything in the shop."""
from __future__ import annotations
import db


def search(query: str, limit: int = 50) -> dict:
    if not query or len(query.strip()) < 2:
        return {"products": [], "orders": [], "customers": [], "knowledge": []}

    q = "%" + query.strip() + "%"

    # Knowledge Hub — the ecosystem Source of Truth reads OUT through here.
    # Guarded: the table only exists once a user has opened the Hub.
    knowledge = []
    try:
        import knowledge_hub as kh
        knowledge = kh.search(query.strip(), limit=limit)
    except Exception:
        knowledge = []

    with db.conn() as c:
        products = c.execute("""
            SELECT sku, name, brand, category, cost_price, sell_price, stock
            FROM products
            WHERE sku LIKE ? OR name LIKE ? OR brand LIKE ? OR category LIKE ?
            ORDER BY sell_price DESC
            LIMIT ?
        """, (q, q, q, q, limit)).fetchall()

        orders = c.execute("""
            SELECT order_id, sku, platform, qty, total_amount,
                   order_date, status, buyer_name, buyer_phone
            FROM orders
            WHERE order_id LIKE ? OR sku LIKE ? OR buyer_name LIKE ?
                  OR buyer_phone LIKE ? OR platform LIKE ?
            ORDER BY order_date DESC
            LIMIT ?
        """, (q, q, q, q, q, limit)).fetchall()

        customers = c.execute("""
            SELECT COALESCE(buyer_phone, buyer_name) AS customer_key,
                   buyer_name, buyer_phone,
                   COUNT(*) AS order_count,
                   SUM(total_amount) AS total_spent,
                   MAX(order_date) AS last_order
            FROM orders
            WHERE buyer_name LIKE ? OR buyer_phone LIKE ?
            GROUP BY customer_key
            ORDER BY total_spent DESC
            LIMIT ?
        """, (q, q, limit)).fetchall()

    return {
        "products": [dict(r) for r in products],
        "orders": [dict(r) for r in orders],
        "customers": [dict(r) for r in customers],
        "knowledge": knowledge,
    }


def quick_stats() -> dict:
    with db.conn() as c:
        products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        try:
            custs = c.execute("""
                SELECT COUNT(DISTINCT COALESCE(buyer_phone, buyer_name))
                FROM orders WHERE buyer_name IS NOT NULL AND buyer_name != ''
            """).fetchone()[0]
        except Exception:
            custs = 0
    return {"products": products, "orders": orders, "customers": custs}
