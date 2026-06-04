"""Claude Vision integration — send a product photo, get structured product
data back. Powers the 📸 Vision page."""
from __future__ import annotations
import base64
import json
import os
import re

from anthropic import Anthropic


MODEL = "claude-opus-4-7"   # Vision-capable; falls back to Sonnet if needed
FALLBACK = "claude-sonnet-4-6"


PROMPT = """ดูภาพสินค้านี้ แล้วสกัดข้อมูลออกเป็น JSON object ห้ามใส่ ``` หรือคำอธิบายเพิ่ม

ส่งกลับเป็น:
{
  "name": "ชื่อสินค้า + รุ่น (เต็ม)",
  "brand": "ยี่ห้อ ถ้ามองออกจากภาพ ไม่อย่างนั้น \\\"\\\"",
  "category": "หมวด เช่น Networking · Switch / Laptop · Business / Accessories · Mouse",
  "color": "สีหลัก",
  "specs": "สเปคเด่น 3-5 จุดที่มองเห็นได้จากภาพ — เป็น text บรรทัดเดียว",
  "estimated_thb": <ราคาประมาณการเป็นเลขถ้าพอจะเดาได้จากภาพ/รุ่น/ตลาดไทย, ไม่อย่างนั้นใส่ 0>,
  "confidence": <0.0-1.0 ความมั่นใจในการสกัด>,
  "notes": "สิ่งที่มองเห็นแต่ไม่แน่ใจ"
}"""


def encode_image(raw: bytes, media_type: str = "image/jpeg") -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(raw).decode(),
        },
    }


def guess_media_type(filename: str) -> str:
    f = filename.lower()
    if f.endswith(".png"):
        return "image/png"
    if f.endswith(".webp"):
        return "image/webp"
    if f.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`")
    return text


def extract_one(raw: bytes, filename: str = "image.jpg", api_key: str | None = None) -> dict:
    """Send one image to Claude, return parsed product dict."""
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    media_type = guess_media_type(filename)

    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1200,
            messages=[{
                "role": "user",
                "content": [
                    encode_image(raw, media_type),
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )
    except Exception:
        # Vision-capable Opus may not be available; try Sonnet
        msg = client.messages.create(
            model=FALLBACK,
            max_tokens=1200,
            messages=[{
                "role": "user",
                "content": [
                    encode_image(raw, media_type),
                    {"type": "text", "text": PROMPT},
                ],
            }],
        )

    text = _strip_code_fence(msg.content[0].text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object inside the response.
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        data = json.loads(match.group(0))

    return {
        "name": (data.get("name") or "").strip(),
        "brand": (data.get("brand") or "").strip(),
        "category": (data.get("category") or "").strip(),
        "color": (data.get("color") or "").strip(),
        "specs": (data.get("specs") or "").strip(),
        "estimated_thb": float(data.get("estimated_thb") or 0),
        "confidence": float(data.get("confidence") or 0),
        "notes": (data.get("notes") or "").strip(),
    }
