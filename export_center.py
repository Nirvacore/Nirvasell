"""Export Center — CSV export for orders, products, customers, expenses.

Thai sellers need Excel-compatible exports for accounting, tax filing,
and sharing with suppliers. CSV with BOM for Thai character support."""
from __future__ import annotations
import csv
import io
from datetime import datetime
import db


def export_products() -> str:
    with db.conn() as c:
        rows = c.execute("""
            SELECT sku, name, brand, category, cost_price, sell_price,
                   stock, created_at
            FROM products ORDER BY sku
        """).fetchall()

    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf)
    w.writerow(["SKU", "ชื่อสินค้า", "แบรนด์", "หมวดหมู่",
                "ราคาทุน", "ราคาขาย", "สต็อก", "วันที่เพิ่ม"])
    for r in rows:
        w.writerow([r["sku"], r["name"], r["brand"], r["category"],
                    r["cost_price"], r["sell_price"], r["stock"],
                    (r["created_at"] or "")[:10]])
    return buf.getvalue()


def export_orders(days: int = 90) -> str:
    with db.conn() as c:
        rows = c.execute("""
            SELECT o.order_id, o.sku, p.name AS product_name,
                   o.platform, o.qty, o.unit_price, o.total_price,
                   o.order_date, o.status,
                   COALESCE(o.buyer_name, '') AS buyer_name,
                   COALESCE(o.buyer_phone, '') AS buyer_phone,
                   COALESCE(o.total_amount, o.total_price) AS total_amount
            FROM orders o
            LEFT JOIN products p ON o.sku = p.sku
            WHERE o.order_date >= date('now', ? || ' days')
            ORDER BY o.order_date DESC
        """, (str(-days),)).fetchall()

    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf)
    w.writerow(["เลขออเดอร์", "SKU", "ชื่อสินค้า", "แพลตฟอร์ม",
                "จำนวน", "ราคาต่อชิ้น", "ราคารวม", "ยอดรวม",
                "วันที่", "สถานะ", "ชื่อลูกค้า", "เบอร์โทร"])
    for r in rows:
        w.writerow([r["order_id"], r["sku"], r["product_name"],
                    r["platform"], r["qty"], r["unit_price"],
                    r["total_price"], r["total_amount"],
                    (r["order_date"] or "")[:10], r["status"],
                    r["buyer_name"], r["buyer_phone"]])
    return buf.getvalue()


def export_customers(days: int = 180) -> str:
    with db.conn() as c:
        rows = c.execute("""
            SELECT COALESCE(buyer_phone, buyer_name) AS customer_key,
                   buyer_name, buyer_phone,
                   COUNT(*) AS order_count,
                   SUM(total_amount) AS total_spent,
                   MAX(order_date) AS last_order,
                   MIN(order_date) AS first_order,
                   GROUP_CONCAT(DISTINCT platform) AS platforms
            FROM orders
            WHERE buyer_name IS NOT NULL AND buyer_name != ''
              AND order_date >= date('now', ? || ' days')
            GROUP BY customer_key
            ORDER BY total_spent DESC
        """, (str(-days),)).fetchall()

    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf)
    w.writerow(["ลูกค้า", "ชื่อ", "เบอร์โทร", "จำนวนออเดอร์",
                "ยอดซื้อรวม", "ซื้อครั้งแรก", "ซื้อล่าสุด", "แพลตฟอร์ม"])
    for r in rows:
        w.writerow([r["customer_key"], r["buyer_name"], r["buyer_phone"],
                    r["order_count"], r["total_spent"],
                    (r["first_order"] or "")[:10],
                    (r["last_order"] or "")[:10], r["platforms"]])
    return buf.getvalue()


def export_expenses(months: int = 3) -> str:
    with db.conn() as c:
        rows = c.execute("""
            SELECT date, category, amount, description, created_at
            FROM expenses
            WHERE date >= date('now', ? || ' months')
            ORDER BY date DESC
        """, (str(-months),)).fetchall()

    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf)
    w.writerow(["วันที่", "หมวดหมู่", "จำนวนเงิน", "รายละเอียด"])
    for r in rows:
        w.writerow([(r["date"] or "")[:10], r["category"],
                    r["amount"], r["description"]])
    return buf.getvalue()


def export_inventory_snapshot() -> str:
    with db.conn() as c:
        rows = c.execute("""
            SELECT p.sku, p.name, p.brand, p.category,
                   p.stock, p.cost_price, p.sell_price,
                   (p.stock * COALESCE(p.cost_price, 0)) AS stock_value,
                   (p.sell_price - COALESCE(p.cost_price, 0)) AS margin_per_unit,
                   COALESCE(sales.qty_30d, 0) AS sold_30d
            FROM products p
            LEFT JOIN (
                SELECT sku, SUM(qty) AS qty_30d
                FROM orders
                WHERE order_date >= date('now', '-30 days')
                GROUP BY sku
            ) sales ON p.sku = sales.sku
            ORDER BY stock_value DESC
        """).fetchall()

    buf = io.StringIO()
    buf.write("﻿")
    w = csv.writer(buf)
    w.writerow(["SKU", "ชื่อสินค้า", "แบรนด์", "หมวดหมู่", "สต็อก",
                "ราคาทุน", "ราคาขาย", "มูลค่าสต็อก", "กำไร/ชิ้น",
                "ขายได้ 30 วัน"])
    for r in rows:
        w.writerow([r["sku"], r["name"], r["brand"], r["category"],
                    r["stock"], r["cost_price"], r["sell_price"],
                    r["stock_value"], r["margin_per_unit"], r["sold_30d"]])
    return buf.getvalue()


def stats() -> dict:
    with db.conn() as c:
        products = c.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        try:
            expenses = c.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
        except Exception:
            expenses = 0
    return {
        "products": products,
        "orders": orders,
        "expenses": expenses,
        "export_types": 5,
    }
