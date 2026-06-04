"""AI Review — Claude reads a generated listing and flags subjective issues
that rule-based compliance can't catch:
  • Over-promising / dishonest claims ("ดีที่สุดในโลก", "100% guaranteed cure")
  • Aggressive / pushy tone (too many emoji, ALL CAPS, scare tactics)
  • Brand-safe? (sensitive comparisons, copycat positioning)
  • Cultural fit (right register for Thai/EN audience)
  • Clarity (jargon, walls of text, missing benefit)

Output: list of {issue, severity, fix} per checked content."""
from __future__ import annotations
import json
from ._base import parse_json


TASK = {
    "key": "ai_review",
    "label": "🤖 AI Review",
    "icon": "🤖",
    "blurb": "Claude อ่าน listing แล้วบอกประเด็นที่ rule check ไม่เจอ (โทน, ความซื่อสัตย์, brand-safe)",
    "output_fields": ["score", "issues_text", "n_blockers", "n_warnings"],
    "is_review": True,
}


PROMPT = """คุณคือ marketplace QA reviewer ที่เข้มแต่ยุติธรรม ตรวจดู listing นี้แล้วประเมิน

ข้อมูลสินค้า:
- SKU: {sku}
- Brand: {brand}
- ราคา: ฿{price}

Listing ที่จะตรวจ:
- Title: {title}
- Description:
{description}
- Tags: {tags}

ประเมิน 5 ด้าน:
1. ความซื่อสัตย์ — ไม่ over-promise / ไม่อ้างเกินจริง
2. โทน — ไม่ pushy ไม่ใช้ scare tactic ไม่ ALL CAPS
3. Brand-safe — ไม่เปรียบทับคู่แข่ง / ไม่ก๊อปคนอื่น
4. Clarity — เข้าใจง่าย ไม่ jargon / มี benefit ชัด
5. Cultural fit (TH) — ภาษาเหมาะ ไม่ฝรั่งจัด ไม่หยาบ

ส่งกลับ JSON object เท่านั้น (ห้ามใส่ ``` หรือคำอธิบาย):

{{
  "score": <0-100 — คุณภาพรวม>,
  "blockers": [
    {{"issue": "...", "fix": "..."}}, ...
  ],
  "warnings": [
    {{"issue": "...", "fix": "..."}}, ...
  ],
  "praise": "1-2 ประโยคชมจุดดีของ listing นี้",
  "overall": "verdict สั้น เช่น 'พร้อม publish' / 'แก้ blockers ก่อน' / 'ปรับโทน + publish ได้'"
}}"""


def build_prompt(row: dict) -> str:
    return PROMPT.format(
        sku=row.get("sku") or "",
        brand=row.get("brand") or "—",
        price=int(row.get("sell_price") or row.get("cost_price") or 0),
        title=(row.get("title") or "")[:300],
        description=(row.get("description") or "")[:2000],
        tags=row.get("tags") or "",
    )


def parse(text: str) -> dict:
    data = parse_json(text)
    blockers = data.get("blockers", []) or []
    warnings = data.get("warnings", []) or []
    # Flatten into a copy-friendly text block.
    lines: list[str] = []
    if data.get("overall"):
        lines.append(f"📋 {data['overall']}")
    if data.get("praise"):
        lines.append(f"✓ {data['praise']}")
    for b in blockers:
        lines.append(f"🔴 {b.get('issue','')} → {b.get('fix','')}")
    for w in warnings:
        lines.append(f"🟡 {w.get('issue','')} → {w.get('fix','')}")
    return {
        "score": int(data.get("score") or 0),
        "issues_text": "\n".join(lines),
        "n_blockers": str(len(blockers)),
        "n_warnings": str(len(warnings)),
    }
