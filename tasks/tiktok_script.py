"""TikTok video script — 30 วินาที format hook → demo → CTA."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "tiktok_script",
    "icon": "🎵",
    "output_fields": ["hook", "script", "hashtags"],
}


PROMPT = """คุณคือ TikTok creator ที่ทำ short-form review ขายของในไทย

ข้อมูลสินค้า:
{ctx}

เขียน script วิดีโอ 30 วินาที (~80-100 คำ พูดได้พอดี):

{{
  "hook": "ประโยคเปิด 0-3 วินาที สร้าง curiosity / pattern interrupt",
  "script": "Full script แบ่งเป็น shot ด้วย [SHOT 1] [SHOT 2] … ใส่ timing โดยประมาณ บอกสิ่งที่พูด + สิ่งที่ถ่าย",
  "hashtags": ["6-10 hashtag เน้น niche keyword + trend"]
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "hook": data.get("hook", ""),
        "script": data.get("script", ""),
        "hashtags": " ".join(f"#{h.lstrip('#')}" for h in (data.get("hashtags") or [])),
    }
