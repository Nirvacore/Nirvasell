"""Pre-flight compliance check — verify every listing meets the rules of
the marketplace it's headed to.

Rule types:
  • length     — text field must fit within N chars
  • forbidden  — must not contain certain words/phrases
  • required   — field must be non-empty
  • regex      — must match a pattern
  • numeric    — must be in a numeric range

Severity:
  • error  — marketplace will reject — block export
  • warn   — likely to hurt conversion / get flagged — show clearly
  • info   — suggestion / best practice

Each rule's check returns Issue objects which the UI groups per product."""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Callable


@dataclass
class Issue:
    platform: str
    sku: str
    field: str
    severity: str   # error | warn | info
    message: str
    suggestion: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


# ---- Forbidden word lists (Thai marketplaces are strict) -----------------

FORBIDDEN_TH = [
    # Replica / counterfeit language — instant ban
    "ของก๊อป", "ก๊อป", "ของเลียนแบบ", "เลียนแบบ", "replica", "fake",
    "AAA", "copy", "ก๊อปปี้",
    # Misleading claims
    "ดีที่สุดในโลก", "the best", "ของแท้100%", "100% original",
    # Banned categories
    "อาวุธ", "ยาเสพติด", "บุหรี่ไฟฟ้า", "vape",
]

# Per-marketplace overrides (extend as needed)
FORBIDDEN_BY_PLATFORM: dict[str, list[str]] = {
    "shopee": FORBIDDEN_TH,
    "lazada": FORBIDDEN_TH,
    "tiktok": FORBIDDEN_TH + ["ลด 100%", "ฟรี ฟรี ฟรี"],
}


# ---- Rule definitions ----------------------------------------------------

PLATFORM_RULES: dict[str, list[dict]] = {
    "shopee": [
        {"type": "length",    "field": "title",       "max": 100,   "severity": "error",
         "message": "Shopee: title ห้ามเกิน 100 ตัวอักษร"},
        {"type": "length",    "field": "title",       "min": 25,    "severity": "warn",
         "message": "Title สั้นไป — SEO Shopee แนะนำ ≥ 25 chars"},
        {"type": "length",    "field": "description", "max": 3000,  "severity": "error",
         "message": "Shopee: description ห้ามเกิน 3000 ตัวอักษร"},
        {"type": "required",  "field": "title",       "severity": "error",
         "message": "Title ห้ามว่าง"},
        {"type": "forbidden", "field": "title",       "severity": "error",
         "message": "พบคำต้องห้ามใน title"},
        {"type": "forbidden", "field": "description", "severity": "warn",
         "message": "พบคำต้องห้ามใน description"},
        {"type": "required",  "field": "image_url",   "severity": "warn",
         "message": "Shopee ต้องมีรูปอย่างน้อย 1 รูป"},
    ],
    "lazada": [
        {"type": "length",    "field": "title",       "max": 80,    "severity": "error",
         "message": "Lazada: title ห้ามเกิน 80 ตัวอักษร"},
        {"type": "length",    "field": "title",       "min": 20,    "severity": "warn",
         "message": "Title สั้นไป — แนะนำ ≥ 20 chars"},
        {"type": "length",    "field": "description", "max": 25000, "severity": "error",
         "message": "Lazada: description ห้ามเกิน 25,000 ตัวอักษร"},
        {"type": "required",  "field": "title",       "severity": "error",
         "message": "Title ห้ามว่าง"},
        {"type": "forbidden", "field": "title",       "severity": "error",
         "message": "พบคำต้องห้ามใน title"},
        {"type": "required",  "field": "image_url",   "severity": "warn",
         "message": "Lazada ต้องมีรูปอย่างน้อย 1 รูป"},
    ],
    "tiktok": [
        {"type": "length",    "field": "title",       "max": 60,    "severity": "error",
         "message": "TikTok Shop: title ห้ามเกิน 60 ตัวอักษร"},
        {"type": "length",    "field": "description", "max": 10000, "severity": "error",
         "message": "TikTok Shop: description ห้ามเกิน 10,000 ตัวอักษร"},
        {"type": "required",  "field": "title",       "severity": "error",
         "message": "Title ห้ามว่าง"},
        {"type": "forbidden", "field": "title",       "severity": "error",
         "message": "พบคำต้องห้ามใน title"},
        {"type": "required",  "field": "image_url",   "severity": "error",
         "message": "TikTok Shop จำเป็นต้องมีรูป"},
    ],
    "shopify": [
        {"type": "length",    "field": "title",       "max": 255,   "severity": "error",
         "message": "Shopify: title ห้ามเกิน 255 ตัวอักษร"},
        {"type": "required",  "field": "title",       "severity": "error",
         "message": "Title ห้ามว่าง"},
    ],
    "amazon_us": [
        {"type": "length",    "field": "title",       "max": 200,   "severity": "error",
         "message": "Amazon: title ห้ามเกิน 200 ตัวอักษร"},
        {"type": "length",    "field": "title",       "min": 80,    "severity": "warn",
         "message": "Amazon: title แนะนำ ≥ 80 chars (more SEO)"},
        {"type": "required",  "field": "image_url",   "severity": "error",
         "message": "Amazon: ต้องมี product image"},
    ],
    "ebay_us": [
        {"type": "length",    "field": "title",       "max": 80,    "severity": "error",
         "message": "eBay: title ห้ามเกิน 80 ตัวอักษร"},
        {"type": "required",  "field": "title",       "severity": "error",
         "message": "Title ห้ามว่าง"},
    ],
    "etsy": [
        {"type": "length",    "field": "title",       "max": 140,   "severity": "error",
         "message": "Etsy: title ห้ามเกิน 140 ตัวอักษร"},
        {"type": "required",  "field": "title",       "severity": "error",
         "message": "Title ห้ามว่าง"},
        {"type": "length",    "field": "tags",        "max": 200,   "severity": "warn",
         "message": "Etsy: 13 tags max recommended"},
    ],
}


# ---- Rule evaluators -----------------------------------------------------

def _val(row, field: str) -> str:
    """Pull a field as a string, even for non-string types."""
    v = row.get(field) if hasattr(row, "get") else (row[field] if field in row else None)
    return "" if v is None else str(v)


def _check_length(row, rule, platform) -> Issue | None:
    val = _val(row, rule["field"])
    n = len(val)
    mx = rule.get("max")
    mn = rule.get("min")
    if mx and n > mx:
        return Issue(
            platform=platform, sku=_val(row, "sku"),
            field=rule["field"], severity=rule.get("severity", "error"),
            message=rule["message"] + f" (มี {n} chars)",
            suggestion=f"ตัดเหลือ ≤ {mx} (เกินอยู่ {n - mx})",
        )
    if mn and n < mn:
        return Issue(
            platform=platform, sku=_val(row, "sku"),
            field=rule["field"], severity=rule.get("severity", "warn"),
            message=rule["message"] + f" (มี {n} chars)",
            suggestion=f"เพิ่มอีก ≥ {mn - n}",
        )
    return None


def _check_required(row, rule, platform) -> Issue | None:
    val = _val(row, rule["field"]).strip()
    if not val:
        return Issue(
            platform=platform, sku=_val(row, "sku"),
            field=rule["field"], severity=rule.get("severity", "error"),
            message=rule["message"],
            suggestion=f"กรอก {rule['field']}",
        )
    return None


def _check_forbidden(row, rule, platform) -> Issue | None:
    text = _val(row, rule["field"]).lower()
    if not text:
        return None
    forbidden = FORBIDDEN_BY_PLATFORM.get(platform, FORBIDDEN_TH)
    hits = [w for w in forbidden if w.lower() in text]
    if hits:
        return Issue(
            platform=platform, sku=_val(row, "sku"),
            field=rule["field"], severity=rule.get("severity", "warn"),
            message=rule["message"] + f": {', '.join(hits[:3])}",
            suggestion=f"ลบ/เปลี่ยน: {', '.join(hits[:3])}",
        )
    return None


CHECKERS: dict[str, Callable] = {
    "length":    _check_length,
    "required":  _check_required,
    "forbidden": _check_forbidden,
}


# ---- Public API ----------------------------------------------------------

def check_one(row: dict, platform: str) -> list[Issue]:
    """Run all rules for a platform against a single product/listing dict."""
    rules = PLATFORM_RULES.get(platform, [])
    out: list[Issue] = []
    for rule in rules:
        fn = CHECKERS.get(rule["type"])
        if not fn:
            continue
        issue = fn(row, rule, platform)
        if issue:
            out.append(issue)
    return out


def check_batch(rows: list[dict], platform: str) -> list[Issue]:
    out: list[Issue] = []
    for r in rows:
        out.extend(check_one(r, platform))
    return out


def summarize(issues: list[Issue]) -> dict:
    """Counts per severity, blocking total."""
    by_sev: dict[str, int] = {"error": 0, "warn": 0, "info": 0}
    for i in issues:
        by_sev[i.severity] = by_sev.get(i.severity, 0) + 1
    blocking = by_sev["error"]
    return {
        **by_sev,
        "total": sum(by_sev.values()),
        "blocking": blocking,
        "passing": blocking == 0,
    }


# ---- Image compliance ----------------------------------------------------

# Per-platform image specs. (min_side_px, recommended aspect, allowed_aspects)
IMAGE_SPECS: dict[str, dict] = {
    "shopee":    {"min_px": 500,  "rec_aspect": (1, 1),    "max_mb": 2.0},
    "lazada":    {"min_px": 500,  "rec_aspect": (1, 1),    "max_mb": 5.0},
    "tiktok":    {"min_px": 600,  "rec_aspect": (1, 1),    "max_mb": 5.0},
    "shopify":   {"min_px": 2048, "rec_aspect": (1, 1),    "max_mb": 20.0},
    "amazon_us": {"min_px": 1000, "rec_aspect": (1, 1),    "max_mb": 10.0},
    "ebay_us":   {"min_px": 500,  "rec_aspect": (1, 1),    "max_mb": 7.0},
    "etsy":      {"min_px": 2000, "rec_aspect": (4, 3),    "max_mb": 20.0},
}


def _open_image(src: str) -> "tuple | None":
    """Return (width, height, mode, size_bytes) — None on failure.

    Accepts HTTPS URL or local file path."""
    try:
        from PIL import Image
        import io as _io
        from pathlib import Path
        if src.startswith("http"):
            import httpx
            r = httpx.get(src, timeout=8.0, follow_redirects=True)
            if not r.is_success:
                return None
            data = r.content
            img = Image.open(_io.BytesIO(data))
            return (img.width, img.height, img.mode, len(data))
        else:
            p = Path(src)
            if not p.exists():
                return None
            img = Image.open(p)
            return (img.width, img.height, img.mode, p.stat().st_size)
    except Exception:
        return None


def check_image(image_url: str, sku: str, platform: str) -> list[Issue]:
    """Validate a product image against marketplace spec."""
    if not image_url:
        return []
    spec = IMAGE_SPECS.get(platform)
    if not spec:
        return []

    # First image only (pipe-separated list)
    src = image_url.split("|")[0].strip()
    info = _open_image(src)
    if not info:
        return [Issue(
            platform=platform, sku=sku, field="image_url", severity="warn",
            message=f"โหลดรูปไม่ได้: {src[:80]}",
            suggestion="ตรวจ URL หรืออัปรูปใหม่",
        )]
    w, h, mode, size = info

    out: list[Issue] = []
    if min(w, h) < spec["min_px"]:
        out.append(Issue(
            platform=platform, sku=sku, field="image_url", severity="error",
            message=f"{platform.title()}: รูปเล็กไป {w}×{h} (ต้อง ≥ {spec['min_px']}px)",
            suggestion=f"อัปรูปใหม่ขนาด ≥ {spec['min_px']}×{spec['min_px']}",
        ))
    # Aspect check
    rec_w, rec_h = spec["rec_aspect"]
    actual = w / h if h else 0
    target = rec_w / rec_h
    if abs(actual - target) / target > 0.10:  # >10% off
        out.append(Issue(
            platform=platform, sku=sku, field="image_url", severity="warn",
            message=f"{platform.title()}: อัตราส่วนไม่ตรง {w}:{h} (แนะนำ {rec_w}:{rec_h})",
            suggestion=f"ใช้ image_utils.resize_for() crop ให้ {rec_w}:{rec_h}",
        ))
    if size > spec["max_mb"] * 1024 * 1024:
        out.append(Issue(
            platform=platform, sku=sku, field="image_url", severity="error",
            message=f"{platform.title()}: ไฟล์ใหญ่ไป {size//1024//1024}MB (max {spec['max_mb']}MB)",
            suggestion="ลด quality หรือ resize",
        ))
    return out


def check_one_with_images(row: dict, platform: str, check_imgs: bool = True) -> list[Issue]:
    """check_one + optional image validation."""
    issues = check_one(row, platform)
    if check_imgs and row.get("image_url"):
        issues.extend(check_image(row["image_url"], row.get("sku", ""), platform))
    return issues


def check_batch_with_images(rows: list[dict], platform: str, check_imgs: bool = True) -> list[Issue]:
    out: list[Issue] = []
    for r in rows:
        out.extend(check_one_with_images(r, platform, check_imgs=check_imgs))
    return out


# Convenience: auto-truncate a title to the platform max (preserve word boundary).
def truncate_title(title: str, platform: str) -> str:
    rules = PLATFORM_RULES.get(platform, [])
    mx = next(
        (r["max"] for r in rules if r["type"] == "length" and r["field"] == "title" and "max" in r),
        None,
    )
    if not mx or len(title) <= mx:
        return title
    cut = title[:mx]
    # Try not to cut mid-word
    if " " in cut[-20:]:
        cut = cut.rsplit(" ", 1)[0]
    return cut
