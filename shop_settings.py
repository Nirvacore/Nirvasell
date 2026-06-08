"""Shop Settings — store profile, business info, default values."""
from __future__ import annotations
import json
import db

SETTING_KEYS = {
    "shop_name":       {"label": "ชื่อร้าน", "default": ""},
    "shop_phone":      {"label": "เบอร์โทร", "default": ""},
    "shop_address":    {"label": "ที่อยู่ผู้ส่ง", "default": ""},
    "shop_line":       {"label": "Line ID", "default": ""},
    "shop_facebook":   {"label": "Facebook Page", "default": ""},
    "shop_tax_id":     {"label": "เลขผู้เสียภาษี", "default": ""},
    "default_carrier": {"label": "ขนส่งหลัก", "default": "kerry"},
    "default_platform":{"label": "แพลตฟอร์มหลัก", "default": "shopee"},
    "low_stock_threshold": {"label": "เตือนสต็อกต่ำเมื่อ (ชิ้น)", "default": "5"},
    "default_vat":     {"label": "แสดง VAT ในใบกำกับ", "default": "false"},
    "currency_symbol": {"label": "สกุลเงิน", "default": "฿"},
    "order_prefix":    {"label": "Prefix เลขออเดอร์", "default": "ORD"},
}


def init() -> None:
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT DEFAULT ''
            )
        """)
        for key, info in SETTING_KEYS.items():
            c.execute(
                "INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)",
                (key, info["default"]),
            )


def get(key: str) -> str:
    with db.conn() as c:
        row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        if row:
            return row["value"] or ""
        return SETTING_KEYS.get(key, {}).get("default", "")


def set(key: str, value: str) -> None:
    with db.conn() as c:
        c.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",
                  (key, value))


def get_all() -> dict:
    with db.conn() as c:
        rows = c.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}


def set_many(updates: dict) -> None:
    with db.conn() as c:
        for key, value in updates.items():
            c.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)",
                      (key, str(value)))


def shop_profile() -> dict:
    all_s = get_all()
    return {
        "name": all_s.get("shop_name", ""),
        "phone": all_s.get("shop_phone", ""),
        "address": all_s.get("shop_address", ""),
        "line": all_s.get("shop_line", ""),
        "facebook": all_s.get("shop_facebook", ""),
        "tax_id": all_s.get("shop_tax_id", ""),
    }
