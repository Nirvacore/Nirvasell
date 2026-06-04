"""LINE OA broadcast — สั้น กระชับ ใส่ emoji + CTA."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "line_post",
    "label": "LINE OA Broadcast",
    "icon": "💚",
    "blurb": "ข้อความสั้นๆ สำหรับ broadcast ทาง LINE Official Account",
    "output_fields": ["message", "hook", "cta"],
}


PROMPT = """คุณคือ marketer สำหรับ LINE Official Account ในไทย

ข้อมูลสินค้า:
{ctx}

เขียน broadcast message สั้นๆ ให้ค้นเจอใน LINE feed:

{{
  "hook": "บรรทัดเปิด 1 บรรทัด ดึงดูด สะดุดตา (มี emoji 1-2 ตัว)",
  "message": "เนื้อหา 4-6 บรรทัด สั้น กระชับ ใช้ emoji แบ่งย่อหน้า เน้นจุดเด่น + ราคา",
  "cta": "ข้อความปุ่ม CTA สั้นๆ เช่น 'สั่งเลย', 'ดูเพิ่ม'"
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "hook": data.get("hook", ""),
        "message": data.get("message", ""),
        "cta": data.get("cta", "สั่งเลย"),
    }
