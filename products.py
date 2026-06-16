"""Product catalog — thin wrapper over the products table in db.py."""
import db


def init():
    db.init()


def all_products() -> list[dict]:
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT id, sku, name, brand, category, cost_price, sell_price, stock, image_url "
        "FROM products ORDER BY name"
    ).fetchall()
    return [dict(r) for r in rows]


def get(product_id: int) -> dict | None:
    conn = db.get_conn()
    row = conn.execute(
        "SELECT id, sku, name, brand, category, cost_price, sell_price, stock, image_url "
        "FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    return dict(row) if row else None


def by_sku(sku: str) -> dict | None:
    conn = db.get_conn()
    row = conn.execute(
        "SELECT id, sku, name, brand, category, cost_price, sell_price, stock, image_url "
        "FROM products WHERE sku = ?",
        (sku,),
    ).fetchone()
    return dict(row) if row else None
