"""Bank-slip verifier — Thai home sellers get fake transfer slips daily.
Upload a slip image → Claude Vision reads amount, date, bank, sender,
reference number → flags suspicious elements (photoshopped numbers, font
mismatches, wrong date format).

Output for the UI:
  {
    "amount":     float | None,       # e.g. 1500.00
    "currency":   str,                # 'THB'
    "date":       str,                # 'YYYY-MM-DD HH:MM'
    "bank":       str,                # 'SCB', 'KTB', 'BBL', ...
    "sender":     str,                # account name / phone
    "recipient":  str,                # account name / phone
    "ref":        str,                # transaction reference
    "suspicious": [list of red flags],
    "confidence": 'high' | 'medium' | 'low',
    "raw_notes":  str,                # Claude's free-text observations
  }

NOT a guarantee — Claude can be fooled by sophisticated forgeries. Treat
"high confidence" as "likely real, still verify in bank app for big sums."
"""
from __future__ import annotations
import base64
import json
import os
import re


_MODEL = "claude-haiku-4-5-20251001"


_PROMPT = """You are verifying a Thai bank transfer slip. Read the image and
extract the structured fields below. Be especially attentive to common forgery
markers in screenshot edits.

Return ONLY valid JSON with these keys:
{
  "amount":     <number or null>,
  "currency":   "THB",
  "date":       "<YYYY-MM-DD HH:MM or empty>",
  "bank":       "<bank name e.g. SCB, KBANK, BBL, KTB, TTB, BAY, GSB or unknown>",
  "sender":     "<name / partial account / phone visible on slip>",
  "recipient":  "<name / partial account / phone visible on slip>",
  "ref":        "<transaction ID / reference number>",
  "suspicious": ["<each red flag in plain Thai or English>"],
  "confidence": "high" | "medium" | "low",
  "raw_notes":  "<observations about layout, fonts, anything unusual>"
}

Suspicious markers to look for:
  • Font inconsistency between amount digits and surrounding text
  • Pixelation around amount or date (signals editing)
  • Wrong date format for the claimed bank (each Thai bank has a signature layout)
  • Missing reference number where the bank normally shows one
  • Amount stylized differently than the bank's actual app screenshot
  • "Successful" stamp present but no recipient information
  • Timezone / time inconsistencies (Thai banks are GMT+7)

Confidence rules:
  • "high"   = layout, fonts, fields all match a known Thai bank app + no markers
  • "medium" = some fields readable, no clear forgery markers, but unsure of bank
  • "low"    = clear forgery markers OR unable to read most fields

Return ONLY the JSON. No ``` fences, no commentary."""


def verify(image_bytes: bytes, *, api_key: str | None = None,
           mime: str = "image/jpeg") -> dict:
    """Run Claude Vision on a slip image. Always returns a dict (never raises)
    — wraps errors as suspicious markers."""
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _err("missing API key")
    if not image_bytes:
        return _err("empty image")

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        b64 = base64.standard_b64encode(image_bytes).decode()
        msg = client.messages.create(
            model=_MODEL,
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image",
                     "source": {"type": "base64", "media_type": mime, "data": b64}},
                    {"type": "text", "text": _PROMPT},
                ],
            }],
        )
        text = msg.content[0].text.strip()
        # Strip ```json fences if Claude added them
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return _err(f"AI did not return valid JSON: {e}")
    except Exception as e:
        return _err(f"{type(e).__name__}: {e}")

    # Sanitize / normalize
    return {
        "amount":     _num(data.get("amount")),
        "currency":   (data.get("currency") or "THB").upper(),
        "date":       str(data.get("date") or "").strip(),
        "bank":       str(data.get("bank") or "").strip(),
        "sender":     str(data.get("sender") or "").strip(),
        "recipient":  str(data.get("recipient") or "").strip(),
        "ref":        str(data.get("ref") or "").strip(),
        "suspicious": [s for s in (data.get("suspicious") or []) if s],
        "confidence": _conf(data.get("confidence")),
        "raw_notes":  str(data.get("raw_notes") or "").strip(),
    }


def _err(msg: str) -> dict:
    return {
        "amount": None, "currency": "THB", "date": "", "bank": "",
        "sender": "", "recipient": "", "ref": "",
        "suspicious": [msg], "confidence": "low", "raw_notes": msg,
    }


def _num(v):
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _conf(v):
    v = (v or "low").lower()
    return v if v in ("high", "medium", "low") else "low"


# ---- Compare against expected amount -----------------------------------

def check_against_expected(report: dict, expected_amount: float | None,
                           tolerance: float = 0.01) -> dict:
    """Add a `matches_expected` boolean + reason to the report."""
    if expected_amount is None or report.get("amount") is None:
        report["matches_expected"] = None
        return report
    diff = abs(report["amount"] - expected_amount)
    if diff <= tolerance:
        report["matches_expected"] = True
        report["match_reason"] = f"exact match: ฿{report['amount']:,.2f}"
    else:
        report["matches_expected"] = False
        report["match_reason"] = (
            f"slip shows ฿{report['amount']:,.2f}, "
            f"expected ฿{expected_amount:,.2f} (off by ฿{diff:,.2f})"
        )
    return report
