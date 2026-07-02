"""All-in-one task: one Claude call → 7 single-product content types.

Saves 7× API calls + cost vs running each task separately. Used by
Workspace for one-click "ทำให้หมด".

Output keys map directly to existing task plugins so History page sees them
normally."""
from __future__ import annotations
from ._base import common_context, parse_json


TASK = {
    "key": "all_in_one",
    "icon": "✨",
    "output_fields": [],
    "is_mega": True,
}


PROMPT = """คุณคือ AI sales assistant สำหรับ reseller ไทย เก่ง copywriting หลายแพลตฟอร์ม

ข้อมูลสินค้า:
{ctx}

สร้างเนื้อหาขาย 7 รูปแบบในรอบเดียว ส่งกลับ JSON object เดียว ห้ามใส่ ``` หรือคำอธิบาย:

{{
  "listing": {{
    "title": "≤100 chars: keyword + brand + model + จุดเด่น",
    "description": "200-400 คำ bullet (•) จุดเด่น+สเปค+ประกัน+จัดส่ง",
    "tags": ["8-12 keyword SEO"]
  }},
  "line_post": {{
    "hook": "บรรทัดเปิด emoji 1-2",
    "message": "4-6 บรรทัด ใช้ emoji แบ่งย่อหน้า จุดเด่น+ราคา",
    "cta": "ปุ่ม CTA"
  }},
  "fb_post": {{
    "post": "80-150 คำ hook→story→solution→CTA+ราคา",
    "hashtags": ["5-8 hashtag"]
  }},
  "tiktok_script": {{
    "hook": "0-3 วินาทีเปิด",
    "script": "30 วินาที [SHOT 1]...[SHOT 2]... พร้อม timing",
    "hashtags": ["6-10 hashtag"]
  }},
  "email_blast": {{
    "subject": "≤60 chars",
    "preheader": "≤90 chars",
    "body_text": "100-200 คำ ทักทาย+ปัญหา+จุดเด่น(bullet)+CTA",
    "body_html": "HTML body ใช้ <p><ul><li><strong><a> เท่านั้น"
  }},
  "customer_qa": {{
    "qa": [
      {{"q": "...", "a": "..."}},
      {{"q": "...", "a": "..."}},
      {{"q": "...", "a": "..."}},
      {{"q": "...", "a": "..."}},
      {{"q": "...", "a": "..."}},
      {{"q": "...", "a": "..."}}
    ]
  }},
  "promotion": {{
    "headline": "≤60 chars พลังลด+ตัวเลข",
    "body": "50-80 คำ ใช้ emoji เน้นเหตุผลลด+benefit",
    "discount_pct": <10-30>,
    "promo_price": <ราคาหลังลดปัดสวย จบ 9 หรือ 0>,
    "cta": "ปุ่ม CTA",
    "countdown_line": "บรรทัด urgency"
  }},
  "ad_creative": {{
    "headline": "≤30 chars scroll-stopper",
    "subhead": "≤60 chars benefit",
    "body": "40-80 คำ story+benefit+CTA",
    "primary_cta": "≤14 chars",
    "image_direction": "คำสั่งภาพ (พื้นหลัง+มุม+prop)",
    "overlay_text": "ข้อความทับภาพ ≤2 บรรทัด",
    "best_aspect": "1:1 หรือ 9:16 หรือ 1.91:1"
  }}
}}"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(ctx=common_context(row))


def parse_all(text: str) -> dict[str, dict]:
    """Returns {task_key: payload_dict} for each of the 7 single-product tasks."""
    data = parse_json(text)
    result: dict[str, dict] = {}

    if "listing" in data:
        l = data["listing"]
        result["listing"] = {
            "title": (l.get("title") or "")[:200],
            "description": l.get("description") or "",
            "tags": ",".join(l.get("tags") or []),
        }
    if "line_post" in data:
        lp = data["line_post"]
        result["line_post"] = {
            "hook": lp.get("hook", ""),
            "message": lp.get("message", ""),
            "cta": lp.get("cta") or "สั่งเลย",
        }
    if "fb_post" in data:
        fb = data["fb_post"]
        result["fb_post"] = {
            "post": fb.get("post", ""),
            "hashtags": " ".join(f"#{h.lstrip('#')}" for h in (fb.get("hashtags") or [])),
        }
    if "tiktok_script" in data:
        tk = data["tiktok_script"]
        result["tiktok_script"] = {
            "hook": tk.get("hook", ""),
            "script": tk.get("script", ""),
            "hashtags": " ".join(f"#{h.lstrip('#')}" for h in (tk.get("hashtags") or [])),
        }
    if "email_blast" in data:
        em = data["email_blast"]
        result["email_blast"] = {
            "subject": (em.get("subject") or "")[:120],
            "preheader": (em.get("preheader") or "")[:120],
            "body_text": em.get("body_text", ""),
            "body_html": em.get("body_html", ""),
        }
    if "customer_qa" in data:
        qa_list = data["customer_qa"].get("qa", [])
        lines = []
        for i, item in enumerate(qa_list, 1):
            q = (item.get("q") or "").strip()
            a = (item.get("a") or "").strip()
            if q and a:
                lines.append(f"Q{i}: {q}\nA{i}: {a}")
        result["customer_qa"] = {
            "qa_text": "\n\n".join(lines),
            "qa_count": str(len(qa_list)),
        }
    if "promotion" in data:
        pr = data["promotion"]
        result["promotion"] = {
            "headline": (pr.get("headline") or "")[:120],
            "body": pr.get("body") or "",
            "discount_pct": str(pr.get("discount_pct") or 15),
            "promo_price": str(pr.get("promo_price") or 0),
            "cta": pr.get("cta") or "ซื้อเลย",
            "countdown_line": pr.get("countdown_line") or "",
        }
    if "ad_creative" in data:
        ac = data["ad_creative"]
        result["ad_creative"] = {
            "headline": (ac.get("headline") or "")[:120],
            "subhead": (ac.get("subhead") or "")[:160],
            "body": ac.get("body") or "",
            "primary_cta": (ac.get("primary_cta") or "ช้อปเลย")[:30],
            "image_direction": ac.get("image_direction") or "",
            "overlay_text": ac.get("overlay_text") or "",
            "best_aspect": ac.get("best_aspect") or "1:1",
        }
    return result
