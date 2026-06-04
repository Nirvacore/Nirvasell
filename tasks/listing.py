"""Marketplace listing — Shopee / Lazada / TikTok bulk-upload."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "listing",
    "label": "Marketplace Listing",
    "icon": "🛒",
    "blurb": "Title + Description + Tags สำหรับ Shopee / Lazada / TikTok bulk upload",
    "output_fields": ["title", "description", "tags"],
}


PROMPT = """คุณคือ copywriter มืออาชีพสำหรับ Shopee / Lazada / TikTok Shop ไทย

ข้อมูลสินค้า:
{ctx}

สร้าง listing ภาษาไทยขายดี ส่งกลับ JSON object ห้ามใส่ ``` หรือคำอธิบาย:

{{
  "title": "≤100 ตัวอักษร — keyword + brand + รุ่น + จุดเด่นอันดับ 1",
  "description": "200-400 คำ ใช้ bullet (•) เน้นจุดเด่น, สเปค, การรับประกัน, การจัดส่ง",
  "tags": ["8-12 keyword สำหรับ SEO"]
}}"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "title": (data.get("title") or "")[:200],
        "description": data.get("description") or "",
        "tags": ",".join(data.get("tags") or []),
    }
