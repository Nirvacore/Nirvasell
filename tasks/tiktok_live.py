"""TikTok Live caption pack — 10 short Thai captions per SKU optimized for
LIVE COMMERCE moments. Each caption has:
  • A CF trigger (e.g. "CF1", "CF X") viewers type in chat to order
  • A scarcity / urgency hook
  • Short enough for TikTok's overlay system (~60 chars)

This is the wedge feature no Thai competitor has. Page365 has live-selling
automation but no AI script generation; Zaapi has AI chat but not live
commerce captions.

Output JSON shape:
  {
    "captions":  ["🔥 CF1 ลด 30% มี 5 ชิ้น", "💥 CF2 ฟรีค่าส่ง 2 ชม.นี้", ...],
    "go_live_hook": "first 10 seconds — hook for viewers to stay",
    "closer":  "60-second closing pitch when sale ends"
  }
"""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "tiktok_live",
    "label": "TikTok Live Captions",
    "icon": "🔴",
    "blurb": "10 captions สั้นสำหรับ Live + hook เปิด + closing pitch — CF trigger ทุกชิ้น",
    "output_fields": ["go_live_hook", "captions", "closer"],
}


PROMPT = """คุณคือ TikTok Live commerce host มืออาชีพในตลาดไทย

ข้อมูลสินค้า:
{ctx}

ภารกิจ: สร้าง content pack สำหรับ Live commerce บน TikTok Shop ไทย

ออกแบบให้:
- ผู้ชมเห็น caption แล้วพิมพ์ CF + เลข ในแชทเพื่อกดสั่ง
- ทุก caption สั้น พูดออกเสียงได้พอดี อ่านง่ายเวลาเลื่อนผ่าน
- ใช้ความ scarcity / urgency จริง (จำนวนชิ้น, นาทีที่เหลือ) แทน clickbait
- เลี่ยงคำต้องห้าม Shopee/Lazada ที่เอามาใช้ใน TikTok Live ไม่ได้

ส่งกลับ JSON เท่านั้น:

{{
  "go_live_hook": "Hook 10 วินาทีแรกของ Live: ทำไมผู้ชมต้องอยู่ฟัง พูดประมาณ 30-40 คำ ใส่ความเป็นเอกลักษณ์ของสินค้านี้",
  "captions": [
    "🔥 CF1 — caption สั้น ๆ ~50 ตัวอักษร พร้อม CF code",
    "💥 CF2 — เวอร์ชั่นที่ 2 มี hook ต่าง",
    "⚡ CF3 — เน้น scarcity",
    "🎁 CF4 — เน้น bundle / ฟรีของแถม",
    "💸 CF5 — เน้นราคาเทียบกับท้องตลาด",
    "✨ CF6 — เน้น lifestyle / outcome ของลูกค้า",
    "📦 CF7 — เน้นความเร็วในการส่ง",
    "🎯 CF8 — เน้นรีวิวจริง / ใช้แล้วชอบ",
    "🔁 CF9 — เน้น repeat customer / ของขายดี",
    "⏰ CF10 — เน้นเวลาที่เหลือก่อน Live ปิดราคา"
  ],
  "closer": "Closing pitch 60 วินาทีสุดท้ายของ Live: ปิด deal กับคนที่ยังลังเล รวบ pain point + scarcity"
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    captions = data.get("captions") or []
    # Join captions with line breaks so they fit in a single output field.
    captions_text = "\n".join(c.strip() for c in captions if c and c.strip())
    return {
        "go_live_hook": data.get("go_live_hook", ""),
        "captions":     captions_text,
        "closer":       data.get("closer", ""),
    }
