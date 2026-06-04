"""SQLite store for Listo. Persists products and every piece of generated
content so the user can re-download / re-use without re-uploading.

Each upload becomes a "batch" so we can filter by source/date later."""
from __future__ import annotations
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "listo.db"   # fallback for CLI scripts (no Streamlit session)


def _resolve_path() -> Path:
    """Multi-tenant: route to data/users/{user_id}.db when logged in."""
    try:
        from auth import user_db_path
        return user_db_path()
    except Exception:
        return DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER REFERENCES batches(id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    name TEXT,
    brand TEXT,
    category TEXT,
    cost_price REAL,
    sell_price INTEGER,
    stock INTEGER,
    image_url TEXT,
    specs TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sku)
);

CREATE INDEX IF NOT EXISTS idx_products_brand    ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    task TEXT NOT NULL,                 -- 'listing' | 'line_post' | 'fb_post' | …
    payload TEXT,                       -- JSON: {title, description, tags, …}
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, task)
);

CREATE INDEX IF NOT EXISTS idx_content_task ON content(task);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    cost_price REAL,
    seen_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Product groups cluster "same item from different suppliers" so we can pick
-- the best supplier at order time. Members live in products via group_id.
CREATE TABLE IF NOT EXISTS product_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT,
    brand TEXT,
    model_code TEXT,
    match_key TEXT UNIQUE,
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_groups_brand ON product_groups(brand);
CREATE INDEX IF NOT EXISTS idx_groups_model ON product_groups(model_code);

-- Orders imported from marketplace exports (Shopee/Lazada/TikTok/etc.).
-- Lets us close the loop: which generated listings actually sold + at what margin.
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    sku TEXT,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    platform TEXT,
    qty INTEGER DEFAULT 1,
    unit_price REAL,
    total_price REAL,
    currency TEXT DEFAULT 'THB',
    order_date TEXT,
    status TEXT DEFAULT 'paid',
    imported_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform, order_id, sku)
);

CREATE INDEX IF NOT EXISTS idx_orders_sku      ON orders(sku);
CREATE INDEX IF NOT EXISTS idx_orders_platform ON orders(platform);
CREATE INDEX IF NOT EXISTS idx_orders_date     ON orders(order_date);
"""


# Idempotent post-release column additions. Re-applied on every init().
PRODUCTS_MIGRATIONS = [
    ("group_id", "INTEGER REFERENCES product_groups(id)"),
]


@contextmanager
def conn():
    c = sqlite3.connect(_resolve_path())
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(SCHEMA)
        existing_cols = {r["name"] for r in c.execute("PRAGMA table_info(products)")}
        for col, coltype in PRODUCTS_MIGRATIONS:
            if col not in existing_cols:
                c.execute(f"ALTER TABLE products ADD COLUMN {col} {coltype}")


# ---- Batches ---------------------------------------------------------------

def create_batch(filename: str, row_count: int) -> int:
    with conn() as c:
        cur = c.execute(
            "INSERT INTO batches (filename, row_count) VALUES (?, ?)",
            (filename, row_count),
        )
        return cur.lastrowid


def list_batches() -> list[sqlite3.Row]:
    with conn() as c:
        return c.execute(
            "SELECT * FROM batches ORDER BY uploaded_at DESC"
        ).fetchall()


# ---- Products --------------------------------------------------------------

def upsert_products(df: pd.DataFrame, batch_id: int) -> int:
    """Save normalized DataFrame. Returns count inserted/updated."""
    n = 0
    with conn() as c:
        for _, r in df.iterrows():
            c.execute(
                """
                INSERT INTO products
                  (batch_id, sku, name, brand, category, cost_price, sell_price,
                   stock, image_url, specs)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(sku) DO UPDATE SET
                  batch_id=excluded.batch_id,
                  name=excluded.name,
                  brand=COALESCE(excluded.brand, products.brand),
                  category=COALESCE(excluded.category, products.category),
                  cost_price=excluded.cost_price,
                  sell_price=excluded.sell_price,
                  stock=COALESCE(excluded.stock, products.stock),
                  image_url=COALESCE(excluded.image_url, products.image_url),
                  specs=COALESCE(excluded.specs, products.specs)
                """,
                (
                    batch_id, r["sku"], r.get("name"), r.get("brand"), r.get("category"),
                    float(r["cost_price"]) if pd.notna(r["cost_price"]) else None,
                    int(r["sell_price"]) if pd.notna(r.get("sell_price")) else None,
                    int(r["stock"]) if pd.notna(r.get("stock")) else None,
                    r.get("image_url"), r.get("specs"),
                ),
            )
            n += 1
    return n


def fetch_products(
    brand: str | None = None,
    category: str | None = None,
    search: str | None = None,
    with_content_task: str | None = None,
    only_missing_task: bool = False,
    limit: int | None = None,
) -> pd.DataFrame:
    sql = "SELECT p.* FROM products p"
    params: list = []
    if with_content_task:
        join = "LEFT JOIN content c ON c.product_id = p.id AND c.task = ?"
        sql += f" {join}"
        params.append(with_content_task)
    where = []
    if brand:
        where.append("p.brand = ?")
        params.append(brand)
    if category:
        where.append("p.category = ?")
        params.append(category)
    if search:
        where.append("(p.sku LIKE ? OR p.name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if only_missing_task and with_content_task:
        where.append("c.id IS NULL")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY p.created_at DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"

    with conn() as c:
        rows = c.execute(sql, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def distinct_values(column: str) -> list[str]:
    assert column in ("brand", "category")
    with conn() as c:
        rows = c.execute(
            f"SELECT DISTINCT {column} FROM products WHERE {column} IS NOT NULL AND {column} != '' ORDER BY 1"
        ).fetchall()
    return [r[0] for r in rows]


# ---- Generated content -----------------------------------------------------

def save_content(product_id: int, task: str, payload: dict):
    with conn() as c:
        c.execute(
            """
            INSERT INTO content (product_id, task, payload)
            VALUES (?, ?, ?)
            ON CONFLICT(product_id, task) DO UPDATE SET
              payload=excluded.payload,
              generated_at=CURRENT_TIMESTAMP
            """,
            (product_id, task, json.dumps(payload, ensure_ascii=False)),
        )


def fetch_content(task: str, product_ids: list[int] | None = None) -> pd.DataFrame:
    """Return product rows + parsed payload columns for one task."""
    sql = """
        SELECT p.*, c.payload, c.generated_at
        FROM content c
        JOIN products p ON p.id = c.product_id
        WHERE c.task = ?
    """
    params: list = [task]
    if product_ids:
        qs = ",".join("?" * len(product_ids))
        sql += f" AND p.id IN ({qs})"
        params.extend(product_ids)
    sql += " ORDER BY c.generated_at DESC"

    with conn() as c:
        rows = c.execute(sql, params).fetchall()

    out = []
    for r in rows:
        d = dict(r)
        payload = json.loads(d.pop("payload") or "{}")
        d.update(payload)
        out.append(d)
    return pd.DataFrame(out)


def content_counts() -> dict[str, int]:
    with conn() as c:
        rows = c.execute(
            "SELECT task, COUNT(*) AS n FROM content GROUP BY task"
        ).fetchall()
    return {r["task"]: r["n"] for r in rows}


def stats() -> dict:
    with conn() as c:
        s = {
            "products": c.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "batches": c.execute("SELECT COUNT(*) FROM batches").fetchone()[0],
            "content_total": c.execute("SELECT COUNT(*) FROM content").fetchone()[0],
        }
    s["by_task"] = content_counts()
    return s
