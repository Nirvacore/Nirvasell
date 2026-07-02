"""Promotion / Flash Sale copy — urgency-driven copy with discount math."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "promotion",
    "icon": "🔥",
    "output_fields": ["headline", "body", "discount_pct", "promo_price", "cta", "countdown_line"],
}


PROMPT = """คุณคือนักการตลาด flash sale ใน marketplace ไทย เก่งสร้างความเร่งด่วน (urgency) แบบไม่ปลอม

ข้อมูลสินค้า:
{ctx}

ราคาขายปกติคือราคาในข้อมูลข้างต้น สร้าง promotion copy ใหม่ที่กระตุ้นให้กดซื้อทันที ส่งกลับ JSON:

{{
  "headline": "หัวข้อ ≤60 ตัวอักษร พลังลด + ตัวเลข",
  "body": "เนื้อหา 50-80 คำ ใช้ emoji ประปราย เน้น: เหตุผลที่ลด + benefit + ของจำกัด",
  "discount_pct": <ตัวเลข 10-40 ที่สมเหตุสมผลสำหรับสินค้านี้>,
  "promo_price": <ราคาขายปกติ × (1 - discount_pct/100) แล้วปัดให้สวย เลขจบที่ 9 หรือ 0>,
  "cta": "ปุ่ม CTA สั้นๆ เช่น 'ซื้อเลย', 'รีบช้อป'",
  "countdown_line": "บรรทัด urgency เช่น 'เหลือ 3 ชม.', 'พรุ่งนี้กลับเป็นราคาเต็ม'"
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "headline": (data.get("headline") or "")[:120],
        "body": data.get("body") or "",
        "discount_pct": str(data.get("discount_pct") or 15),
        "promo_price": str(data.get("promo_price") or 0),
        "cta": data.get("cta") or "ซื้อเลย",
        "countdown_line": data.get("countdown_line") or "",
    }
