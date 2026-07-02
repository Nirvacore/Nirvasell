"""Watch marketplace fee/policy pages → detect changes → propose fee updates.

How it works:
  1. For each platform, store the source URL (Shopee help center, Lazada
     Seller Center, etc.) in data/policy_sources.json — user-editable.
  2. fetch_policy_text(url) → returns the readable text portion.
  3. Claude extracts structured fee data from the text (commission %, payment %,
     transaction %, VAT). Falls back to manual paste if scraping blocked.
  4. compare_fees() vs current → returns a diff.
  5. apply_update() writes to fees.OVERRIDES_PATH.

Why we use Claude instead of regex:
  • Each marketplace formats their fee page differently
  • Rules change wording often (Thai/EN/policy structure)
  • Claude reads natural language reliably
"""
from __future__ import annotations
import hashlib
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

import httpx
from anthropic import Anthropic

import fees as fees_mod


ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
SOURCES_PATH = DATA / "policy_sources.json"
HISTORY_PATH = DATA / "policy_history.jsonl"


DEFAULT_SOURCES: list[dict] = [
    {
        "platform": "shopee",
        "url": "https://help.shopee.co.th/portal/4/article/77254-นโยบายค่าธรรมเนียม",
        "language": "th",
    },
    {
        "platform": "lazada",
        "url": "https://sellercenter.lazada.co.th/seller/helpcenter/article/360001236693",
        "language": "th",
    },
    {
        "platform": "tiktok",
        "url": "https://seller-th.tiktok.com/university/article/10005775",
        "fallback_urls": [
            "https://seller.tiktokglobalshop.com/university/essay?knowledge_id=10005775",
        ],
        "language": "th",
    },
    {
        "platform": "amazon_us",
        "url": "https://sell.amazon.com/pricing",
        "fallback_urls": [
            "https://sellercentral.amazon.com/help/hub/reference/G200336920",
        ],
        "language": "en",
    },
    {
        "platform": "ebay_us",
        "url": "https://www.ebay.com/sellercenter/run-your-store/fees",
        "language": "en",
    },
]


# ---- Sources registry ----------------------------------------------------

def load_sources() -> list[dict]:
    if SOURCES_PATH.exists():
        try:
            return json.loads(SOURCES_PATH.read_text())
        except Exception:
            pass
    return [dict(s) for s in DEFAULT_SOURCES]


def save_sources(sources: list[dict]):
    SOURCES_PATH.write_text(json.dumps(sources, indent=2, ensure_ascii=False))


# ---- Fetch + extract -----------------------------------------------------

_TAG_RX = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_HTML_RX = re.compile(r"<[^>]+>")
_FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
}
_SPA_MARKERS = (
    "react app doesn't work properly without javascript",
    "please enable javascript",
    "please enable cookies to continue",
)
_MIN_USEFUL_LEN = 200


def _clean_html(html: str) -> str:
    clean = _TAG_RX.sub(" ", html)
    clean = _HTML_RX.sub(" ", clean)
    return re.sub(r"\s+", " ", clean).strip()


def _is_usable_policy_text(text: str) -> bool:
    if len(text) < _MIN_USEFUL_LEN:
        return False
    low = text.lower()
    return not any(marker in low for marker in _SPA_MARKERS)


def fetch_policy_text(url: str, *, retries: int = 2) -> dict:
    """GET a URL and strip to readable text. Returns {ok, text, hash, status}."""
    last: dict = {"ok": False, "status": -1, "text": "", "hash": ""}
    for attempt in range(retries + 1):
        try:
            r = httpx.get(
                url,
                timeout=20.0,
                follow_redirects=True,
                headers=_FETCH_HEADERS,
            )
            if not r.is_success:
                last = {"ok": False, "status": r.status_code, "text": "", "hash": ""}
                if r.status_code >= 500 and attempt < retries:
                    continue
                return last

            clean = _clean_html(r.text)
            h = hashlib.sha256(clean.encode()).hexdigest()[:16]
            if not _is_usable_policy_text(clean):
                return {
                    "ok": False,
                    "status": r.status_code,
                    "text": clean,
                    "hash": h,
                    "reason": "spa_or_empty",
                }

            return {"ok": True, "status": r.status_code, "text": clean, "hash": h}
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            last = {"ok": False, "status": -1, "text": "", "hash": "", "error": str(e)}
            if attempt < retries:
                continue
            return last
        except Exception as e:
            return {"ok": False, "status": -1, "text": "", "hash": "", "error": str(e)}
    return last


def fetch_source(source: dict) -> dict:
    """Try a source URL plus optional fallbacks. Returns the first usable result."""
    urls: list[str] = []
    primary = source.get("url")
    if primary:
        urls.append(primary)
    urls.extend(source.get("fallback_urls") or [])

    last: dict = {"ok": False, "status": -1, "text": "", "hash": ""}
    for url in urls:
        result = fetch_policy_text(url)
        result["url_used"] = url
        if result.get("ok"):
            return result
        last = result
    return last


# ---- Claude-powered fee extraction --------------------------------------

EXTRACTION_PROMPT = """ข้อความด้านล่างมาจากหน้านโยบายของ marketplace ({platform}).
สกัดค่าธรรมเนียมและกฎสำคัญ ส่งกลับเป็น JSON เท่านั้น ห้ามใส่ ``` หรือคำอธิบาย:

{{
  "commission_pct": <ตัวเลข ค่า commission/transaction ทั่วไป (non-Mall)>,
  "payment_pct": <ตัวเลข ค่าธรรมเนียมชำระเงิน>,
  "transaction_pct": <ตัวเลข ค่าธุรกรรมอื่นถ้ามี ไม่งั้น 0>,
  "vat_on_fees": <ตัวเลข VAT บนค่า fee ปกติ 7 ในไทย>,
  "notes": "สรุปกฎสำคัญ 3-5 ข้อ เช่น ของต้องห้าม, ขนาดรูป, deadline จัดส่ง",
  "effective_date": "วันที่นโยบายมีผล ถ้าเจอในข้อความ (YYYY-MM-DD ไม่งั้น \\\"\\\")"
}}

ข้อความ:
{text}"""


def extract_fees_with_claude(text: str, platform: str, api_key: str | None = None) -> dict:
    """Use Claude to pull structured fee data from policy page text."""
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    # Limit text to keep prompt manageable
    snippet = text[:20000]
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": EXTRACTION_PROMPT.format(platform=platform, text=snippet),
        }],
    )
    out = msg.content[0].text.strip()
    if out.startswith("```"):
        out = out.split("```")[1]
        if out.startswith("json"):
            out = out[4:]
        out = out.strip().rstrip("`")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", out)
        if m:
            return json.loads(m.group(0))
        raise


# ---- Diff vs current -----------------------------------------------------

def compare(platform: str, new_data: dict) -> list[dict]:
    """Return list of {field, old, new, delta} for changed numeric fields."""
    current = fees_mod.load().get(platform, {})
    diffs = []
    for field in ("commission_pct", "payment_pct", "transaction_pct", "vat_on_fees"):
        old = current.get(field, 0)
        new = new_data.get(field, 0)
        try:
            old_f = float(old)
            new_f = float(new)
        except (TypeError, ValueError):
            continue
        if abs(new_f - old_f) > 0.01:
            diffs.append({
                "field": field,
                "old": old_f,
                "new": new_f,
                "delta": new_f - old_f,
            })
    return diffs


def apply_update(platform: str, new_data: dict):
    """Persist accepted fee changes by writing into fee_overrides.json."""
    current = fees_mod.load()
    if platform not in current:
        return
    for field in ("commission_pct", "payment_pct", "transaction_pct", "vat_on_fees"):
        if field in new_data:
            try:
                current[platform][field] = float(new_data[field])
            except (TypeError, ValueError):
                continue
    fees_mod.save(current)
    # Audit log entry
    HISTORY_PATH.parent.mkdir(exist_ok=True)
    with HISTORY_PATH.open("a") as f:
        f.write(json.dumps({
            "at": datetime.now().isoformat(),
            "platform": platform,
            "applied": {k: new_data.get(k) for k in (
                "commission_pct", "payment_pct", "transaction_pct", "vat_on_fees"
            )},
            "notes": new_data.get("notes", ""),
            "effective_date": new_data.get("effective_date", ""),
        }) + "\n")


def history() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    out = []
    for line in HISTORY_PATH.read_text().splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out[::-1]  # newest first
