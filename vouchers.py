"""Voucher / promo code studio — design once, export per-platform CSV.

Thai home sellers create 10+ vouchers per month: 11.11 sale, Songkran flash,
new-follower welcome, Christmas, Chinese New Year, etc. Each marketplace's
voucher upload format is different — this module designs the voucher once
then exports the right CSV shape for Shopee / Lazada / TikTok.

Storage: per-user `vouchers` table.
Use-counter: 0 (uses tracked externally — marketplaces don't push back to us).
"""
from __future__ import annotations
import csv
import io
import secrets
import string
from datetime import datetime, date, timedelta

import db


SCHEMA = """
CREATE TABLE IF NOT EXISTS vouchers (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT NOT NULL UNIQUE,
    label        TEXT NOT NULL,
    discount_type TEXT NOT NULL,        -- 'percent' | 'fixed' | 'shipping'
    discount_value REAL NOT NULL,        -- 20 (= 20% if percent, ฿20 if fixed)
    min_spend    REAL DEFAULT 0,
    max_uses     INTEGER DEFAULT 0,      -- 0 = unlimited
    starts_at    TEXT,
    expires_at   TEXT,
    platforms    TEXT,                   -- CSV: 'shopee,lazada,tiktok'
    status       TEXT DEFAULT 'active',  -- 'active' | 'paused' | 'expired'
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vouchers_status ON vouchers(status);
"""


# ---- Preset templates (Thai festival calendar) -------------------------

TEMPLATES = {
    "songkran": {
        "label": "Songkran (สงกรานต์)",
        "icon":  "💦",
        "code_prefix": "SONGKRAN",
        "month": 4, "day": 13,
        "suggested": {"discount_type": "percent", "discount_value": 15,
                      "min_spend": 200, "duration_days": 7},
    },
    "double_11": {
        "label": "11.11 Mega Sale",
        "icon":  "🛒",
        "code_prefix": "ELEVEN11",
        "month": 11, "day": 11,
        "suggested": {"discount_type": "percent", "discount_value": 25,
                      "min_spend": 0, "duration_days": 3},
    },
    "double_12": {
        "label": "12.12 Year-End",
        "icon":  "🎄",
        "code_prefix": "TWELVE12",
        "month": 12, "day": 12,
        "suggested": {"discount_type": "percent", "discount_value": 20,
                      "min_spend": 0, "duration_days": 3},
    },
    "black_friday": {
        "label": "Black Friday",
        "icon":  "🛍",
        "code_prefix": "BLACKFRI",
        "month": 11, "day": 28,   # last Fri of Nov — approximate
        "suggested": {"discount_type": "percent", "discount_value": 30,
                      "min_spend": 500, "duration_days": 4},
    },
    "lunar_new_year": {
        "label": "ตรุษจีน · Lunar New Year",
        "icon":  "🧧",
        "code_prefix": "CNYHAPPY",
        "month": 2, "day": 1,     # approximation
        "suggested": {"discount_type": "fixed", "discount_value": 88,
                      "min_spend": 388, "duration_days": 5},
    },
    "welcome": {
        "label": "New customer welcome",
        "icon":  "👋",
        "code_prefix": "WELCOME",
        "month": None, "day": None,
        "suggested": {"discount_type": "fixed", "discount_value": 50,
                      "min_spend": 300, "duration_days": 30},
    },
    "free_ship": {
        "label": "Free shipping promo",
        "icon":  "🚚",
        "code_prefix": "FREESHIP",
        "month": None, "day": None,
        "suggested": {"discount_type": "shipping", "discount_value": 0,
                      "min_spend": 500, "duration_days": 7},
    },
    "flash_24h": {
        "label": "Flash 24-hour deal",
        "icon":  "⚡",
        "code_prefix": "FLASH24",
        "month": None, "day": None,
        "suggested": {"discount_type": "percent", "discount_value": 15,
                      "min_spend": 0, "duration_days": 1},
    },
}


# ---- Code helpers ------------------------------------------------------

def random_suffix(n: int = 4) -> str:
    """Short random suffix to make codes unique."""
    pool = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(pool) for _ in range(n))


def suggest_code(template_key: str) -> str:
    """Generate a unique-looking code from a template key."""
    tpl = TEMPLATES.get(template_key)
    if not tpl:
        return "PROMO" + random_suffix()
    return f"{tpl['code_prefix']}{random_suffix(3)}"


# ---- CRUD --------------------------------------------------------------

def init():
    with db.conn() as c:
        c.executescript(SCHEMA)


def add(*, code: str, label: str, discount_type: str, discount_value: float,
        min_spend: float = 0, max_uses: int = 0,
        starts_at: str = "", expires_at: str = "",
        platforms: list[str] | None = None) -> tuple[bool, str]:
    init()
    code = (code or "").strip().upper()
    if not code:
        return False, "code required"
    if discount_type not in ("percent", "fixed", "shipping"):
        return False, "bad discount_type"
    try:
        with db.conn() as c:
            c.execute(
                "INSERT INTO vouchers (code, label, discount_type, discount_value, "
                "min_spend, max_uses, starts_at, expires_at, platforms) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (code, label.strip() or code,
                 discount_type, float(discount_value),
                 float(min_spend or 0), int(max_uses or 0),
                 starts_at.strip(), expires_at.strip(),
                 ",".join(platforms or [])),
            )
    except Exception as e:
        return False, str(e)
    return True, "ok"


def all_active() -> list[dict]:
    init()
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM vouchers WHERE status = 'active' "
            "ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def all_vouchers() -> list[dict]:
    init()
    with db.conn() as c:
        rows = c.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def delete(voucher_id: int) -> bool:
    init()
    with db.conn() as c:
        cur = c.execute("DELETE FROM vouchers WHERE id = ?", (voucher_id,))
    return cur.rowcount > 0


def pause(voucher_id: int) -> bool:
    init()
    with db.conn() as c:
        cur = c.execute(
            "UPDATE vouchers SET status = 'paused' WHERE id = ?", (voucher_id,)
        )
    return cur.rowcount > 0


def resume(voucher_id: int) -> bool:
    init()
    with db.conn() as c:
        cur = c.execute(
            "UPDATE vouchers SET status = 'active' WHERE id = ?", (voucher_id,)
        )
    return cur.rowcount > 0


# ---- Per-platform CSV exporters ----------------------------------------
# Each marketplace's voucher CSV column shape differs. Sellers download the
# CSV here then upload into the seller-centre voucher creator.

def export_shopee(vouchers: list[dict]) -> bytes:
    """Shopee TH voucher mass-upload format."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Voucher Code", "Voucher Name", "Discount Type",
                "Discount Amount", "Min. Spend", "Total Vouchers",
                "Start Date", "End Date"])
    for v in vouchers:
        dt = {"percent": "%", "fixed": "THB", "shipping": "FREE_SHIPPING"}[v["discount_type"]]
        w.writerow([
            v["code"], v["label"], dt, v["discount_value"],
            v.get("min_spend", 0), v.get("max_uses", 0) or "unlimited",
            v.get("starts_at", ""), v.get("expires_at", ""),
        ])
    return buf.getvalue().encode("utf-8-sig")


def export_lazada(vouchers: list[dict]) -> bytes:
    """Lazada voucher format."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["VoucherCode", "Title", "VoucherType", "Value",
                "MinSpend", "Quota", "StartTime", "EndTime"])
    for v in vouchers:
        vt = {"percent": "PERCENTAGE", "fixed": "AMOUNT", "shipping": "SHIPPING"}[v["discount_type"]]
        w.writerow([
            v["code"], v["label"], vt, v["discount_value"],
            v.get("min_spend", 0), v.get("max_uses", 0) or 999999,
            v.get("starts_at", ""), v.get("expires_at", ""),
        ])
    return buf.getvalue().encode("utf-8-sig")


def export_tiktok(vouchers: list[dict]) -> bytes:
    """TikTok Shop voucher format."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Code", "Name", "Type", "Discount", "MinPurchase",
                "TotalQty", "Start", "End"])
    for v in vouchers:
        t = {"percent": "percent", "fixed": "amount", "shipping": "free_shipping"}[v["discount_type"]]
        w.writerow([
            v["code"], v["label"], t, v["discount_value"],
            v.get("min_spend", 0), v.get("max_uses", 0),
            v.get("starts_at", ""), v.get("expires_at", ""),
        ])
    return buf.getvalue().encode("utf-8-sig")


PLATFORM_EXPORTERS = {
    "shopee": (export_shopee, "shopee_vouchers"),
    "lazada": (export_lazada, "lazada_vouchers"),
    "tiktok": (export_tiktok, "tiktok_vouchers"),
}


# ---- Pretty display ----------------------------------------------------

def format_discount(v: dict) -> str:
    dt = v["discount_type"]
    val = v["discount_value"]
    if dt == "percent":
        return f"-{int(val)}%"
    if dt == "fixed":
        return f"-฿{int(val):,}"
    return "ส่งฟรี"


def status_for(v: dict) -> str:
    """Compute live status considering expiry/start."""
    today = date.today().isoformat()
    if v.get("status") == "paused":
        return "paused"
    if v.get("expires_at") and v["expires_at"] < today:
        return "expired"
    if v.get("starts_at") and v["starts_at"] > today:
        return "scheduled"
    return "active"
