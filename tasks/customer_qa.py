"""Customer Q&A — 8 ready-to-use question/answer pairs per product.

Saves resellers a ton of time on chat support: paste these into the product
page Q&A section so customers find answers before asking."""
from __future__ import annotations
import json
from ._base import common_context, parse_json


TASK = {
    "key": "customer_qa",
    "label": "💬 Q&A สำหรับลูกค้า",
    "icon": "💬",
    "blurb": "8 คำถาม-คำตอบสำเร็จรูป ลดเวลาตอบแชต",
    "output_fields": ["qa_text", "qa_count"],
}


PROMPT = """คุณคือผู้เชี่ยวชาญ customer service สำหรับ marketplace ไทย

ข้อมูลสินค้า:
{ctx}

สร้างคำถาม + คำตอบที่ลูกค้าไทยถามบ่อย 8 ข้อ ส่งกลับ JSON object เท่านั้น:

{{
  "qa": [
    {{"q": "คำถามที่ลูกค้ามักถาม", "a": "คำตอบ 1-3 ประโยค สุภาพ ตรงประเด็น"}},
    ...
  ]
}}

ครอบคลุม: ของแท้/ประกัน, การจัดส่ง, การคืนสินค้า, การใช้งาน/สเปคสำคัญ, ค่าจัดส่ง/COD, ของในกล่อง, ใช้กับรุ่นไหน/รองรับอะไร, มีโปรไหม

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    qa_list = data.get("qa") or []
    # Flatten to copy-paste-able text block.
    lines = []
    for i, item in enumerate(qa_list, 1):
        q = (item.get("q") or "").strip()
        a = (item.get("a") or "").strip()
        if q and a:
            lines.append(f"Q{i}: {q}\nA{i}: {a}")
    return {
        "qa_text": "\n\n".join(lines),
        "qa_count": str(len(qa_list)),
    }
