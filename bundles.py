"""Product bundles — package multiple SKUs together at a bundle price."""
from __future__ import annotations
import db


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS bundles (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                description     TEXT,
                bundle_price    REAL DEFAULT 0,
                available_stock INTEGER DEFAULT 0,
                active          INTEGER DEFAULT 1,
                notes           TEXT,
                created_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS bundle_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                bundle_id   INTEGER NOT NULL,
                sku         TEXT NOT NULL,
                qty         INTEGER DEFAULT 1,
                FOREIGN KEY (bundle_id) REFERENCES bundles(id)
            )
        """)


def create(name: str, description: str = "", bundle_price: float = 0,
           skus_qtys: list[dict] = None, notes: str = "") -> int:
    if skus_qtys is None:
        skus_qtys = []
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO bundles (name,description,bundle_price,notes,active) "
            "VALUES (?,?,?,?,1)",
            (name, description, bundle_price, notes),
        )
        bundle_id = cur.lastrowid
        for item in skus_qtys:
            c.execute(
                "INSERT INTO bundle_items (bundle_id,sku,qty) VALUES (?,?,?)",
                (bundle_id, item["sku"], item.get("qty", 1)),
            )
    update_stock(bundle_id)
    return bundle_id


def update_stock(bundle_id: int) -> int:
    """Recalculate available bundle stock from component stocks."""
    with db.conn() as c:
        items = c.execute(
            "SELECT bi.sku, bi.qty, COALESCE(p.stock,0) stock "
            "FROM bundle_items bi "
            "LEFT JOIN products p ON bi.sku=p.sku "
            "WHERE bi.bundle_id=?",
            (bundle_id,),
        ).fetchall()
        if not items:
            return 0
        max_bundles = min(
            int(item["stock"] // item["qty"])
            for item in items
            if item["qty"] > 0
        )
        c.execute("UPDATE bundles SET available_stock=? WHERE id=?",
                  (max_bundles, bundle_id))
        return max_bundles


def get(bundle_id: int) -> dict | None:
    with db.conn() as c:
        row = c.execute("SELECT * FROM bundles WHERE id=?",
                        (bundle_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        items = c.execute(
            "SELECT bi.*, p.name product_name, p.sell_price, p.stock "
            "FROM bundle_items bi "
            "LEFT JOIN products p ON bi.sku=p.sku "
            "WHERE bi.bundle_id=?",
            (bundle_id,),
        ).fetchall()
        d["items"] = [dict(i) for i in items]
        component_value = sum(
            (i["sell_price"] or 0) * i["qty"] for i in items
        )
        d["component_value"] = component_value
        d["savings"] = round(component_value - d["bundle_price"], 2)
        d["savings_pct"] = (
            round(d["savings"] / component_value * 100, 1)
            if component_value > 0 else 0
        )
        return d


def all_bundles(active_only: bool = False) -> list[dict]:
    with db.conn() as c:
        if active_only:
            rows = c.execute(
                "SELECT * FROM bundles WHERE active=1 ORDER BY created_at DESC"
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM bundles ORDER BY active DESC, created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def activate(bundle_id: int) -> None:
    with db.conn() as c:
        c.execute("UPDATE bundles SET active=1 WHERE id=?", (bundle_id,))


def deactivate(bundle_id: int) -> None:
    with db.conn() as c:
        c.execute("UPDATE bundles SET active=0 WHERE id=?", (bundle_id,))


def refresh_all_stocks() -> None:
    with db.conn() as c:
        ids = [r[0] for r in c.execute("SELECT id FROM bundles WHERE active=1")]
    for bid in ids:
        update_stock(bid)


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM bundles").fetchone()[0]
        active = c.execute(
            "SELECT COUNT(*) FROM bundles WHERE active=1"
        ).fetchone()[0]
        total_stock = c.execute(
            "SELECT COALESCE(SUM(available_stock),0) FROM bundles WHERE active=1"
        ).fetchone()[0]
    return {
        "total": total,
        "active": active,
        "total_available_stock": total_stock,
    }
