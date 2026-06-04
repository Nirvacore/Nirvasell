"""Email blast — สำหรับ B2B / repeat customer."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "email_blast",
    "label": "Email Blast",
    "icon": "✉️",
    "blurb": "Subject + Preheader + Body HTML สำหรับ email campaign",
    "output_fields": ["subject", "preheader", "body_text", "body_html"],
}


PROMPT = """คุณคือ email marketer สำหรับลูกค้า B2B / reseller ในไทย ใช้ภาษาสุภาพ ตรงประเด็น

ข้อมูลสินค้า:
{ctx}

เขียน email campaign:

{{
  "subject": "หัวข้อ ≤60 ตัวอักษร ดึงให้เปิด ไม่หลอกลวง",
  "preheader": "preview text ≤90 ตัวอักษร เสริม subject",
  "body_text": "Plain text body 100-200 คำ มี: ทักทาย → ปัญหา/โอกาส → จุดเด่นสินค้า (bullet 3-4 จุด) → ราคา + CTA",
  "body_html": "HTML version ของ body_text ใช้ <p>, <ul>, <li>, <strong>, <a href='#'> เท่านั้น สไตล์เรียบง่าย"
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "subject": (data.get("subject") or "")[:120],
        "preheader": (data.get("preheader") or "")[:120],
        "body_text": data.get("body_text", ""),
        "body_html": data.get("body_html", ""),
    }
