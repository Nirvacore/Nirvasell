"""Bundle proposal — รวมหลายชิ้นเป็นชุด พร้อมส่วนลด.

Unlike single-product tasks, this one runs once over a SET of products."""
from __future__ import annotations
import json
from ._base import parse_json


TASK = {
    "key": "bundle",
    "icon": "📦",
    "output_fields": ["bundle_name", "pitch", "suggested_discount_pct", "bundle_price"],
    "multi_product": True,
}


PROMPT = """คุณคือผู้เชี่ยวชาญด้าน bundle pricing สำหรับ resellers ในไทย

สินค้าในชุด:
{items}

ราคารวมปกติ: {total:,} บาท

สร้าง bundle proposal:

{{
  "bundle_name": "ชื่อชุดที่ดึงดูด ≤60 ตัวอักษร",
  "pitch": "คำขาย 100-150 คำ อธิบายว่าสินค้าใน bundle ใช้คู่กันยังไง สร้างประโยชน์อะไรเพิ่ม (synergy)",
  "suggested_discount_pct": <ตัวเลข 5-15>,
  "bundle_price": <ราคาหลังลดเป็นเลขปัดสวยๆ>
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(rows: list[dict]) -> str:
    items = "\n".join(
        f"  • {r.get('name') or r.get('sku')} — ฿{int(r.get('sell_price') or 0):,}"
        for r in rows
    )
    total = sum(int(r.get("sell_price") or 0) for r in rows)
    return PROMPT.format(items=items, total=total)


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "bundle_name": data.get("bundle_name", ""),
        "pitch": data.get("pitch", ""),
        "suggested_discount_pct": int(data.get("suggested_discount_pct") or 10),
        "bundle_price": int(data.get("bundle_price") or 0),
    }
