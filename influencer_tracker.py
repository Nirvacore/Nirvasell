"""Influencer / Affiliate Tracker — track creator partnerships and commissions."""
from __future__ import annotations
import db

PLATFORMS = ["tiktok", "facebook", "instagram", "youtube", "twitter", "other"]
STATUSES = {
    "active":   {"label": "กำลังร่วมงาน", "icon": "✅", "color": "#4d6c5c"},
    "pending":  {"label": "รอตอบรับ", "icon": "⏳", "color": "#c5963d"},
    "paused":   {"label": "หยุดชั่วคราว", "icon": "⏸", "color": "#9a9485"},
    "ended":    {"label": "สิ้นสุด", "icon": "⬛", "color": "#4a4a4a"},
}
COMMISSION_TYPES = {
    "percentage": "เปอร์เซ็นต์ต่อยอดขาย",
    "flat_per_sale": "บาทคงที่ต่อออเดอร์",
    "flat_monthly": "ค่าตอบแทนรายเดือน",
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS influencers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                handle          TEXT DEFAULT '',
                platform        TEXT DEFAULT 'tiktok',
                followers       INTEGER DEFAULT 0,
                niche           TEXT DEFAULT '',
                commission_type TEXT DEFAULT 'percentage',
                commission_rate REAL DEFAULT 10.0,
                status          TEXT DEFAULT 'pending',
                contact         TEXT DEFAULT '',
                promo_code      TEXT DEFAULT '',
                notes           TEXT DEFAULT '',
                created_at      TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS influencer_sales (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_id   INTEGER,
                order_id        TEXT DEFAULT '',
                sku             TEXT DEFAULT '',
                sale_amount     REAL DEFAULT 0,
                commission_amt  REAL DEFAULT 0,
                paid            INTEGER DEFAULT 0,
                sale_date       TEXT DEFAULT (date('now','localtime')),
                FOREIGN KEY (influencer_id) REFERENCES influencers(id)
            )
        """)


def add(name: str, handle: str = "", platform: str = "tiktok",
        followers: int = 0, niche: str = "", commission_type: str = "percentage",
        commission_rate: float = 10.0, contact: str = "", promo_code: str = "",
        notes: str = "") -> int:
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO influencers (name,handle,platform,followers,niche,"
            "commission_type,commission_rate,contact,promo_code,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (name, handle, platform, followers, niche,
             commission_type, commission_rate, contact, promo_code, notes),
        )
        return cur.lastrowid


def set_status(influencer_id: int, status: str) -> None:
    with db.conn() as c:
        c.execute("UPDATE influencers SET status=? WHERE id=?",
                  (status, influencer_id))


def record_sale(influencer_id: int, sale_amount: float,
                order_id: str = "", sku: str = "",
                sale_date: str = "") -> int:
    with db.conn() as c:
        row = c.execute(
            "SELECT commission_type, commission_rate FROM influencers WHERE id=?",
            (influencer_id,),
        ).fetchone()
        if not row:
            return 0
        ct = row["commission_type"]
        rate = row["commission_rate"]
        if ct == "percentage":
            commission = round(sale_amount * rate / 100, 2)
        elif ct == "flat_per_sale":
            commission = rate
        else:
            commission = 0
        from datetime import datetime
        date = sale_date or datetime.now().strftime("%Y-%m-%d")
        cur = c.execute(
            "INSERT INTO influencer_sales (influencer_id,order_id,sku,"
            "sale_amount,commission_amt,sale_date) VALUES (?,?,?,?,?,?)",
            (influencer_id, order_id, sku, sale_amount, commission, date),
        )
        return cur.lastrowid


def mark_paid(influencer_id: int) -> None:
    with db.conn() as c:
        c.execute(
            "UPDATE influencer_sales SET paid=1 "
            "WHERE influencer_id=? AND paid=0",
            (influencer_id,),
        )


def all_influencers(status: str = None) -> list[dict]:
    with db.conn() as c:
        if status:
            rows = c.execute(
                "SELECT * FROM influencers WHERE status=? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM influencers ORDER BY created_at DESC"
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["status_info"] = STATUSES.get(r["status"], STATUSES["pending"])
            sales = c.execute(
                "SELECT COALESCE(SUM(sale_amount),0) total_sales, "
                "COALESCE(SUM(commission_amt),0) total_commission, "
                "COALESCE(SUM(CASE WHEN paid=0 THEN commission_amt ELSE 0 END),0) unpaid "
                "FROM influencer_sales WHERE influencer_id=?",
                (r["id"],),
            ).fetchone()
            d["total_sales"] = sales["total_sales"]
            d["total_commission"] = sales["total_commission"]
            d["unpaid_commission"] = sales["unpaid"]
            result.append(d)
        return result


def stats() -> dict:
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM influencers").fetchone()[0]
        active = c.execute(
            "SELECT COUNT(*) FROM influencers WHERE status='active'"
        ).fetchone()[0]
        unpaid = c.execute(
            "SELECT COALESCE(SUM(commission_amt),0) FROM influencer_sales WHERE paid=0"
        ).fetchone()[0]
        total_sales = c.execute(
            "SELECT COALESCE(SUM(sale_amount),0) FROM influencer_sales"
        ).fetchone()[0]
    return {
        "total": total,
        "active": active,
        "unpaid_commission": round(unpaid, 2),
        "total_sales": round(total_sales, 2),
    }
