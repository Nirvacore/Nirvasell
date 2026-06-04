"""Ad Creative — display/banner ad copy + image direction.

What this generates is *not* a marketplace listing — it's the punchy,
visual-first creative used in Facebook/Instagram/TikTok ad campaigns,
Google Display Network, and shop-front banners."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "ad_creative",
    "label": "🎨 Ad Creative",
    "icon": "🎨",
    "blurb": "คำขายแบบโฆษณา + คำสั่งภาพ (พื้นหลัง, overlay, สัดส่วน) สำหรับ ads",
    "output_fields": [
        "headline", "subhead", "body", "primary_cta",
        "image_direction", "overlay_text", "best_aspect",
    ],
}


PROMPT = """คุณคือ creative director สำหรับ paid ads (Facebook, Instagram, TikTok, Google Display) ในไทย เก่งทำ scroll-stopper

ข้อมูลสินค้า:
{ctx}

สร้าง ad creative spec — ห้ามใส่ ``` หรือคำอธิบายเพิ่ม ส่ง JSON เท่านั้น:

{{
  "headline": "บรรทัดเปิด ≤30 ตัวอักษร แรง สะดุดตา ไม่ใช่ชื่อสินค้า",
  "subhead": "บรรทัดรอง ≤60 ตัวอักษร — benefit หรือเหตุผลซื้อ",
  "body": "เนื้อหา 40-80 คำ — story สั้นๆ + benefit + CTA",
  "primary_cta": "ปุ่ม CTA ≤14 ตัวอักษร เช่น 'ช้อปเลย', 'ดูเพิ่ม'",
  "image_direction": "คำสั่งสำหรับภาพ — บอกพื้นหลัง (สีอะไร / lifestyle), มุม, prop ที่ใส่, ขนาดสินค้าในเฟรม. ตัวอย่าง: 'สินค้าวางบนพื้นหลังสีพีช matte, มุม 45° จากบน, มีเงา soft, prop: ใบไม้เขียวเล็กๆ ด้านขวา'",
  "overlay_text": "ข้อความสั้นๆ ที่จะวางทับภาพ — สูงสุด 2 บรรทัด เช่น 'ลด 30%\\nวันนี้เท่านั้น'",
  "best_aspect": "อัตราส่วนภาพดีสุดสำหรับสินค้านี้ — '1:1' (FB/IG feed) หรือ '9:16' (Reels/TikTok/Story) หรือ '1.91:1' (FB link ad)"
}}"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "headline": (data.get("headline") or "")[:120],
        "subhead": (data.get("subhead") or "")[:160],
        "body": data.get("body") or "",
        "primary_cta": (data.get("primary_cta") or "ช้อปเลย")[:30],
        "image_direction": data.get("image_direction") or "",
        "overlay_text": data.get("overlay_text") or "",
        "best_aspect": data.get("best_aspect") or "1:1",
    }
