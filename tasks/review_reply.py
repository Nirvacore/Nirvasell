"""Auto review reply — generate context-aware Thai responses to customer
reviews across rating tiers (1★-5★). Where BigSeller has template replies,
nirva uses Claude to read the actual review text + product context, then
write a reply that addresses the specific point the customer made.

Input columns we use beyond the standard product fields:
  • review_text — the customer's review (required for context)
  • review_rating — 1..5 stars (defaults to 5 if missing)

Output JSON:
  {
    "reply":        "Polite Thai reply, ~50-80 words, addresses specific points",
    "tone":         "grateful | apologetic | clarifying | recovery",
    "follow_up":    "Optional: what action the seller should take offline
                     (refund, replacement, check QC, none)"
  }"""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "review_reply",
    "icon": "💬",
    "output_fields": ["reply", "tone", "follow_up"],
}


PROMPT = """คุณคือ customer success rep ของร้านขายของออนไลน์ไทย เก่งเรื่อง
ตอบรีวิวลูกค้าให้ดูจริงใจ ไม่ใช้คำสำเร็จรูป

ข้อมูลสินค้า:
{ctx}

รีวิวลูกค้า (rating: {rating}/5):
"{review_text}"

ภารกิจ:
- อ่านรีวิวให้เข้าใจว่าลูกค้าพูดถึง point อะไรเป็นพิเศษ
- ตอบให้ตรงจุดนั้นๆ ไม่ตอบลอยๆ ("ขอบคุณค่ะ") ที่ดูเหมือนใช้ template
- ถ้า rating 1-2★ → tone: ขอโทษจริงใจ + offer recovery action
- ถ้า 3★ → tone: ขอบคุณ + ขอ feedback เพิ่ม + รับว่าจะปรับปรุง
- ถ้า 4-5★ → tone: ขอบคุณ + reference ส่วนที่ลูกค้าชม + invite ซื้อซ้ำ
- ใช้ภาษาไทย กึ่งทางการ ลงท้าย "ค่ะ" หรือ "ครับ" ตามเหมาะสม
- ห้ามใช้ template เด็ดขาด — ต้องอ้างอิงเนื้อหารีวิวจริง

ส่ง JSON เท่านั้น:

{{
  "reply": "Reply ตามจริง ~50-80 คำ พูดถึง point ที่ลูกค้ายกมา",
  "tone": "grateful | apologetic | clarifying | recovery",
  "follow_up": "ถ้ามี action offline ที่ seller ต้องทำ (refund / replace / check QC / contact customer / none)"
}}

ห้ามใส่ ``` หรือคำอธิบาย"""


def build_prompt(row: dict) -> str:
    review = (row.get("review_text") or "").strip()
    if not review:
        # No review text → can't generate context-aware reply. Surface a clear
        # marker so caller can skip or prompt user to add the review.
        review = "(ลูกค้ายังไม่ได้ใส่ข้อความ — ตอบขอบคุณทั่วไปสำหรับ rating ที่ให้)"
    try:
        rating = int(row.get("review_rating") or 5)
    except (TypeError, ValueError):
        rating = 5
    rating = max(1, min(5, rating))
    return PROMPT.format(
        ctx=common_context(row),
        rating=rating,
        review_text=review.replace('"', "'"),  # avoid breaking the JSON template
    )


def parse(text: str) -> dict:
    data = parse_json(text)
    return {
        "reply":     (data.get("reply") or "").strip(),
        "tone":      (data.get("tone") or "").strip().lower(),
        "follow_up": (data.get("follow_up") or "").strip(),
    }
