"""Product Variants — color/size/material combos with individual stock.

ผลิตภัณฑ์ที่มีหลายแบบ เช่น เสื้อสีแดง/ฟ้า ไซซ์ S/M/L
แต่ละ combination มีสต็อกและราคาแยกกัน"""
from __future__ import annotations
import json
import db


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS variant_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_sku TEXT NOT NULL UNIQUE,
                variant_axes TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS product_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER REFERENCES variant_groups(id) ON DELETE CASCADE,
                variant_sku TEXT NOT NULL UNIQUE,
                variant_label TEXT,
                attributes TEXT,
                stock INTEGER DEFAULT 0,
                cost_price REAL,
                sell_price REAL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_pv_group
                ON product_variants(group_id);
            CREATE INDEX IF NOT EXISTS idx_pv_sku
                ON product_variants(variant_sku);
        """)


def create_group(parent_sku: str, axes: list, notes: str = "") -> int:
    with db.conn() as c:
        c.execute("""
            INSERT INTO variant_groups (parent_sku, variant_axes, notes)
            VALUES (?, ?, ?)
            ON CONFLICT(parent_sku) DO UPDATE SET
                variant_axes = excluded.variant_axes,
                notes = excluded.notes
        """, (parent_sku, json.dumps(axes, ensure_ascii=False), notes))
        row = c.execute(
            "SELECT id FROM variant_groups WHERE parent_sku = ?", (parent_sku,)
        ).fetchone()
        return row["id"]


def add_variant(parent_sku: str, attributes: dict,
                stock: int = 0, cost_price: float = None,
                sell_price: float = None) -> str:
    parts = [str(v) for v in attributes.values()]
    variant_sku = parent_sku + "-" + "-".join(parts)
    label = " / ".join(parts)

    with db.conn() as c:
        group = c.execute(
            "SELECT id FROM variant_groups WHERE parent_sku = ?", (parent_sku,)
        ).fetchone()
        if not group:
            create_group(parent_sku, list(attributes.keys()))
            group = c.execute(
                "SELECT id FROM variant_groups WHERE parent_sku = ?", (parent_sku,)
            ).fetchone()

        c.execute("""
            INSERT INTO product_variants
                (group_id, variant_sku, variant_label, attributes, stock, cost_price, sell_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(variant_sku) DO UPDATE SET
                attributes = excluded.attributes,
                stock = excluded.stock,
                cost_price = excluded.cost_price,
                sell_price = excluded.sell_price
        """, (group["id"], variant_sku, label,
              json.dumps(attributes, ensure_ascii=False),
              stock, cost_price, sell_price))
    return variant_sku


def get_variants(parent_sku: str) -> dict:
    with db.conn() as c:
        group = c.execute(
            "SELECT * FROM variant_groups WHERE parent_sku = ?", (parent_sku,)
        ).fetchone()
        if not group:
            return {"parent_sku": parent_sku, "variants": [], "axes": []}

        variants = c.execute("""
            SELECT * FROM product_variants
            WHERE group_id = ?
            ORDER BY variant_label
        """, (group["id"],)).fetchall()

    var_list = []
    for v in variants:
        try:
            attrs = json.loads(v["attributes"] or "{}")
        except Exception:
            attrs = {}
        var_list.append({
            "id": v["id"],
            "variant_sku": v["variant_sku"],
            "label": v["variant_label"],
            "attributes": attrs,
            "stock": v["stock"],
            "cost_price": v["cost_price"],
            "sell_price": v["sell_price"],
            "is_active": v["is_active"],
        })

    total_stock = sum(v["stock"] or 0 for v in var_list)
    try:
        axes = json.loads(group["variant_axes"] or "[]")
    except Exception:
        axes = []

    return {
        "parent_sku": parent_sku,
        "group_id": group["id"],
        "axes": axes,
        "variants": var_list,
        "total_stock": total_stock,
        "active_count": sum(1 for v in var_list if v["is_active"]),
    }


def update_stock(variant_sku: str, stock: int) -> None:
    with db.conn() as c:
        c.execute(
            "UPDATE product_variants SET stock = ? WHERE variant_sku = ?",
            (stock, variant_sku)
        )


def all_groups(limit: int = 100) -> list:
    with db.conn() as c:
        groups = c.execute("""
            SELECT vg.parent_sku,
                   p.name AS product_name,
                   COUNT(pv.id) AS variant_count,
                   SUM(pv.stock) AS total_stock
            FROM variant_groups vg
            LEFT JOIN products p ON vg.parent_sku = p.sku
            LEFT JOIN product_variants pv ON vg.id = pv.group_id
            GROUP BY vg.parent_sku
            ORDER BY variant_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(g) for g in groups]


def stats() -> dict:
    with db.conn() as c:
        groups = c.execute("SELECT COUNT(*) FROM variant_groups").fetchone()[0]
        variants = c.execute("SELECT COUNT(*) FROM product_variants").fetchone()[0]
        total_stock = c.execute(
            "SELECT COALESCE(SUM(stock), 0) FROM product_variants"
        ).fetchone()[0]
        out_of_stock = c.execute(
            "SELECT COUNT(*) FROM product_variants WHERE stock = 0 AND is_active = 1"
        ).fetchone()[0]
    return {
        "groups": groups,
        "variants": variants,
        "total_stock": total_stock,
        "out_of_stock": out_of_stock,
    }
