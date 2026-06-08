"""Staff Commission Tracker — track sales commissions per staff member.

Each staff member gets a % of orders they processed.
Tracks earned, paid, and pending commissions."""
from __future__ import annotations
from datetime import datetime
import db


def init():
    with db.conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                commission_pct REAL DEFAULT 5.0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS commission_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                staff_id INTEGER REFERENCES staff(id),
                order_id TEXT,
                sku TEXT,
                sale_amount REAL,
                commission_amt REAL,
                commission_pct REAL,
                period TEXT,
                paid INTEGER DEFAULT 0,
                paid_at TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_cr_staff
                ON commission_records(staff_id);
            CREATE INDEX IF NOT EXISTS idx_cr_period
                ON commission_records(period);
            CREATE INDEX IF NOT EXISTS idx_cr_paid
                ON commission_records(paid);
        """)


def add_staff(name: str, commission_pct: float = 5.0) -> int:
    with db.conn() as c:
        c.execute("""
            INSERT INTO staff (name, commission_pct)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET
                commission_pct = excluded.commission_pct,
                is_active = 1
        """, (name, commission_pct))
        return c.execute(
            "SELECT id FROM staff WHERE name = ?", (name,)
        ).fetchone()["id"]


def all_staff() -> list:
    with db.conn() as c:
        return [dict(r) for r in c.execute("""
            SELECT s.*,
                   COALESCE(SUM(CASE WHEN cr.paid = 0 THEN cr.commission_amt ELSE 0 END), 0) AS pending,
                   COALESCE(SUM(CASE WHEN cr.paid = 1 THEN cr.commission_amt ELSE 0 END), 0) AS paid_total
            FROM staff s
            LEFT JOIN commission_records cr ON s.id = cr.staff_id
            WHERE s.is_active = 1
            GROUP BY s.id ORDER BY s.name
        """).fetchall()]


def record(staff_id: int, order_id: str, sale_amount: float,
           sku: str = "", commission_pct: float = None,
           notes: str = "") -> int:
    with db.conn() as c:
        if commission_pct is None:
            row = c.execute(
                "SELECT commission_pct FROM staff WHERE id = ?",
                (staff_id,)
            ).fetchone()
            commission_pct = row["commission_pct"] if row else 5.0

        commission_amt = round(sale_amount * commission_pct / 100, 2)
        period = datetime.now().strftime("%Y-%m")

        c.execute("""
            INSERT INTO commission_records
                (staff_id, order_id, sku, sale_amount, commission_amt,
                 commission_pct, period, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (staff_id, order_id, sku, sale_amount, commission_amt,
              commission_pct, period, notes))
        return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def mark_paid(staff_id: int, period: str = None) -> float:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db.conn() as c:
        if period:
            rows = c.execute("""
                SELECT COALESCE(SUM(commission_amt), 0) AS total
                FROM commission_records
                WHERE staff_id = ? AND period = ? AND paid = 0
            """, (staff_id, period)).fetchone()
            c.execute("""
                UPDATE commission_records
                SET paid = 1, paid_at = ?
                WHERE staff_id = ? AND period = ? AND paid = 0
            """, (now, staff_id, period))
        else:
            rows = c.execute("""
                SELECT COALESCE(SUM(commission_amt), 0) AS total
                FROM commission_records
                WHERE staff_id = ? AND paid = 0
            """, (staff_id,)).fetchone()
            c.execute("""
                UPDATE commission_records
                SET paid = 1, paid_at = ?
                WHERE staff_id = ? AND paid = 0
            """, (now, staff_id))
    return float(rows["total"])


def staff_summary(staff_id: int, period: str = None) -> dict:
    with db.conn() as c:
        params = [staff_id]
        period_filter = ""
        if period:
            period_filter = " AND period = ?"
            params.append(period)

        row = c.execute("""
            SELECT COALESCE(SUM(commission_amt), 0) AS total_earned,
                   COALESCE(SUM(CASE WHEN paid = 0 THEN commission_amt ELSE 0 END), 0) AS pending,
                   COALESCE(SUM(CASE WHEN paid = 1 THEN commission_amt ELSE 0 END), 0) AS paid,
                   COUNT(*) AS transactions,
                   COALESCE(SUM(sale_amount), 0) AS total_sales
            FROM commission_records
            WHERE staff_id = ?""" + period_filter,
            params
        ).fetchone()

        records = c.execute("""
            SELECT * FROM commission_records
            WHERE staff_id = ?""" + period_filter +
            " ORDER BY created_at DESC LIMIT 20",
            params
        ).fetchall()

        staff_row = c.execute(
            "SELECT * FROM staff WHERE id = ?", (staff_id,)
        ).fetchone()

    return {
        "staff": dict(staff_row) if staff_row else {},
        "total_earned": round(row["total_earned"], 2),
        "pending": round(row["pending"], 2),
        "paid": round(row["paid"], 2),
        "transactions": row["transactions"],
        "total_sales": round(row["total_sales"], 2),
        "records": [dict(r) for r in records],
    }


def period_summary(period: str = None) -> list:
    if not period:
        period = datetime.now().strftime("%Y-%m")
    with db.conn() as c:
        rows = c.execute("""
            SELECT s.name, s.commission_pct,
                   COALESCE(SUM(cr.sale_amount), 0) AS total_sales,
                   COALESCE(SUM(cr.commission_amt), 0) AS total_commission,
                   COALESCE(SUM(CASE WHEN cr.paid = 0 THEN cr.commission_amt ELSE 0 END), 0) AS pending,
                   COUNT(cr.id) AS orders
            FROM staff s
            LEFT JOIN commission_records cr
                ON s.id = cr.staff_id AND cr.period = ?
            WHERE s.is_active = 1
            GROUP BY s.id ORDER BY total_commission DESC
        """, (period,)).fetchall()
    return [dict(r) for r in rows]


def stats() -> dict:
    with db.conn() as c:
        staff_count = c.execute(
            "SELECT COUNT(*) FROM staff WHERE is_active = 1"
        ).fetchone()[0]
        total_pending = c.execute(
            "SELECT COALESCE(SUM(commission_amt), 0) FROM commission_records WHERE paid = 0"
        ).fetchone()[0]
        this_month = c.execute("""
            SELECT COALESCE(SUM(commission_amt), 0)
            FROM commission_records
            WHERE period = strftime('%Y-%m', 'now')
        """).fetchone()[0]
    return {
        "staff_count": staff_count,
        "total_pending": round(total_pending, 2),
        "this_month": round(this_month, 2),
    }
