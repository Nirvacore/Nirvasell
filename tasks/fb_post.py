"""Facebook Page post — story-driven, engagement-friendly."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "fb_post",
    "label": "Facebook Page Post",
    "icon": "📘",
    "blurb": "Post ยาวพอประมาณ มี story + engagement hook สำหรับ FB Page",
    "output_fields": ["post", "hashtags"],
}


PROMPT = """คุณคือ content creator สำหรับ Facebook Page ในไทย ใช้โทนสนุก เป็นมิตร เข้าถึงง่าย

ข้อมูลสินค้า:
{ctx}

เขียน FB post 80-150 คำ:

{{
  "post": "เริ่มด้วย hook 1 บรรทัด, ตามด้วยเนื้อหาเล่าเรื่อง / ปัญหา → solution, ใช้ emoji ประปราย, ปิดด้วย CTA + ราคา",
  "hashtags": ["5-8 hashtag ภาษาไทย/อังกฤษ ที่คนค้นจริง"]
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "post": data.get("post", ""),
        "hashtags": " ".join(f"#{h.lstrip('#')}" for h in (data.get("hashtags") or [])),
    }
