"""Stock Reconciliation — compare physical count vs system, log variances.

แม่ค้านับของจริง → ระบบเปรียบเทียบ → รู้ว่าหายไปไหน / เกินจริงมาจากไหน"""
from __future__ import annotations
from datetime import datetime
import db


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS stock_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_date TEXT DEFAULT CURRENT_DATE,
                notes TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS stock_count_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_id INTEGER REFERENCES stock_counts(id) ON DELETE CASCADE,
                sku TEXT NOT NULL,
                system_qty INTEGER,
                physical_qty INTEGER,
                variance INTEGER,
                notes TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_sci_count
                ON stock_count_items(count_id);
            CREATE INDEX IF NOT EXISTS idx_sci_sku
                ON stock_count_items(sku);
        """)


def new_count(notes: str = "") -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    with db.conn() as c:
        c.execute("""
            INSERT INTO stock_counts (count_date, notes)
            VALUES (?, ?)
        """, (today, notes))
        count_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

        products = c.execute(
            "SELECT sku, stock FROM products ORDER BY sku"
        ).fetchall()
        for p in products:
            c.execute("""
                INSERT INTO stock_count_items (count_id, sku, system_qty, physical_qty, variance)
                VALUES (?, ?, ?, ?, 0)
            """, (count_id, p["sku"], p["stock"] or 0, p["stock"] or 0))
    return count_id


def update_physical(count_id: int, sku: str, physical_qty: int,
                    notes: str = "") -> None:
    with db.conn() as c:
        system_qty = c.execute("""
            SELECT system_qty FROM stock_count_items
            WHERE count_id = ? AND sku = ?
        """, (count_id, sku)).fetchone()

        if not system_qty:
            return

        variance = physical_qty - system_qty["system_qty"]
        c.execute("""
            UPDATE stock_count_items
            SET physical_qty = ?, variance = ?, notes = ?
            WHERE count_id = ? AND sku = ?
        """, (physical_qty, variance, notes, count_id, sku))


def get_count(count_id: int) -> dict:
    with db.conn() as c:
        header = c.execute(
            "SELECT * FROM stock_counts WHERE id = ?", (count_id,)
        ).fetchone()
        if not header:
            return {}

        items = c.execute("""
            SELECT sci.*, p.name, p.cost_price
            FROM stock_count_items sci
            LEFT JOIN products p ON sci.sku = p.sku
            WHERE sci.count_id = ?
            ORDER BY ABS(sci.variance) DESC, sci.sku
        """, (count_id,)).fetchall()

    item_list = [dict(i) for i in items]
    total_var = sum(i["variance"] for i in item_list)
    discrepancies = [i for i in item_list if i["variance"] != 0]
    loss_value = sum(
        abs(i["variance"]) * (i["cost_price"] or 0)
        for i in discrepancies if i["variance"] < 0
    )

    return {
        "id": header["id"],
        "date": header["count_date"],
        "notes": header["notes"],
        "status": header["status"],
        "items": item_list,
        "total_skus": len(item_list),
        "discrepancies": len(discrepancies),
        "total_variance": total_var,
        "estimated_loss": round(loss_value, 2),
    }


def finalize(count_id: int, apply_adjustments: bool = True) -> dict:
    with db.conn() as c:
        c.execute(
            "UPDATE stock_counts SET status = 'finalized' WHERE id = ?",
            (count_id,)
        )

        if apply_adjustments:
            items = c.execute("""
                SELECT sku, physical_qty FROM stock_count_items
                WHERE count_id = ? AND variance != 0
            """, (count_id,)).fetchall()

            for item in items:
                c.execute(
                    "UPDATE products SET stock = ? WHERE sku = ?",
                    (item["physical_qty"], item["sku"])
                )

    return get_count(count_id)


def history(limit: int = 10) -> list:
    with db.conn() as c:
        rows = c.execute("""
            SELECT sc.*,
                   COUNT(sci.id) AS total_skus,
                   SUM(ABS(sci.variance)) AS total_abs_variance
            FROM stock_counts sc
            LEFT JOIN stock_count_items sci ON sc.id = sci.count_id
            GROUP BY sc.id
            ORDER BY sc.created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def summary() -> dict:
    with db.conn() as c:
        total_counts = c.execute("SELECT COUNT(*) FROM stock_counts").fetchone()[0]
        last = c.execute("""
            SELECT count_date FROM stock_counts
            ORDER BY created_at DESC LIMIT 1
        """).fetchone()
        discrepancies = c.execute("""
            SELECT COUNT(*) FROM stock_count_items
            WHERE variance != 0
        """).fetchone()[0]
    return {
        "total_counts": total_counts,
        "last_count_date": last["count_date"] if last else None,
        "total_discrepancies_ever": discrepancies,
    }
