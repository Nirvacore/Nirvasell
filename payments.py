"""Payment helpers — PromptPay QR (Thai) + Stripe Payment Link (global).

Philosophy: no recurring billing, no paywall. This is a pay-what-you-can
donation flow. Two paths:

1. **PromptPay QR** — generated locally per amount. User scans with their bank
   app and pays directly to the operator's phone/national-ID. No fees, no
   middleman, no API account needed. Configure once via env or admin UI.

2. **Stripe Payment Link** — a single URL the operator created in the Stripe
   dashboard. The link itself does the checkout; we just hand it over. No
   server-side Stripe API calls, no webhook handling — keeps the codebase
   simple and deploy-friendly.

Optional: a `donations` table records what users SAY they sent (honor system).
Admin can later reconcile with bank statements.

To configure:
  env vars:    PROMPTPAY_ID=0812345678  STRIPE_PAYMENT_LINK=https://buy.stripe.com/xxx
  or admin UI: see Account or Admin pages → "Payment settings"
"""
from __future__ import annotations
import io
import os
import re
from datetime import datetime

import db


# ---- Config -------------------------------------------------------------

def get_settings() -> dict:
    """Read payment config from user_settings (per-admin) or env vars."""
    try:
        import user_settings as us
        return {
            "promptpay_id": us.get("payments.promptpay_id", "")
                            or os.getenv("PROMPTPAY_ID", ""),
            "promptpay_name": us.get("payments.promptpay_name", "")
                              or os.getenv("PROMPTPAY_NAME", ""),
            "stripe_link": us.get("payments.stripe_link", "")
                           or os.getenv("STRIPE_PAYMENT_LINK", ""),
            "bmac_url": us.get("payments.bmac_url", "")
                        or os.getenv("BUYMEACOFFEE_URL", ""),
            "github_sponsors": us.get("payments.github_sponsors", "")
                               or os.getenv("GITHUB_SPONSORS_URL", ""),
        }
    except Exception:
        return {
            "promptpay_id": os.getenv("PROMPTPAY_ID", ""),
            "promptpay_name": os.getenv("PROMPTPAY_NAME", ""),
            "stripe_link": os.getenv("STRIPE_PAYMENT_LINK", ""),
            "bmac_url": os.getenv("BUYMEACOFFEE_URL", ""),
            "github_sponsors": os.getenv("GITHUB_SPONSORS_URL", ""),
        }


def set_settings(**kwargs) -> None:
    """Persist payment config in user_settings."""
    import user_settings as us
    for k, v in kwargs.items():
        if v is not None:
            us.set(f"payments.{k}", v.strip() if isinstance(v, str) else v)


# ---- PromptPay payload generator ---------------------------------------
# Spec: EMVCo QR + Thai PromptPay extension (AID A000000677010111)

def _tlv(tag: str, value: str) -> str:
    """Tag-Length-Value: TT LL VV (length zero-padded to 2 digits)."""
    return f"{tag}{len(value):02d}{value}"


def _crc16(data: str) -> str:
    """CRC-16/CCITT-FALSE — standard EMVCo checksum."""
    crc = 0xFFFF
    for ch in data.encode("ascii"):
        crc ^= ch << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def _normalize_promptpay_id(id_: str) -> tuple[str, str] | None:
    """Return (tag, padded_id) where tag is '01' for phone or '02' for NID.
    Returns None if id_ is malformed."""
    digits = re.sub(r"\D", "", id_ or "")
    if len(digits) == 10 and digits.startswith("0"):
        # Phone: drop leading 0, prepend 0066 → 13 digits
        return ("01", "0066" + digits[1:])
    if len(digits) == 13:
        # National ID: pass through
        return ("02", digits)
    if len(digits) == 15:
        # e-Wallet ID
        return ("03", digits)
    return None


def promptpay_payload(id_: str, amount: float | None = None) -> str | None:
    """Build the EMVCo QR string. Returns None if id_ is invalid."""
    norm = _normalize_promptpay_id(id_)
    if not norm:
        return None
    inner_tag, value = norm

    # Merchant Account Information (tag 29)
    mai = _tlv("00", "A000000677010111") + _tlv(inner_tag, value)
    mai_field = _tlv("29", mai)

    payload = (
        _tlv("00", "01") +              # Payload Format Indicator
        _tlv("01", "12" if amount else "11") +  # 11=static, 12=dynamic
        mai_field +
        _tlv("53", "764") +             # Currency: THB
    ((_tlv("54", f"{amount:.2f}")) if amount else "") +
        _tlv("58", "TH")                # Country
    )
    payload += "6304"                   # CRC tag+length placeholder
    return payload + _crc16(payload)


def promptpay_qr_png(id_: str, amount: float | None = None) -> bytes | None:
    """Render the QR as PNG bytes. Returns None on invalid id."""
    payload = promptpay_payload(id_, amount)
    if not payload:
        return None
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_M
    except ImportError:
        return None
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---- Donation log -------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amount REAL,
    currency TEXT DEFAULT 'THB',
    method TEXT,                 -- 'promptpay' | 'stripe' | 'bmac' | 'github' | 'other'
    note TEXT,
    confirmed INTEGER DEFAULT 0, -- admin marks as reconciled
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init():
    with db.conn() as c:
        c.executescript(SCHEMA)


def log_donation(*, amount: float, method: str, currency: str = "THB",
                 note: str = "") -> int:
    """Honor-system log: user says they donated X via Y. Admin reconciles."""
    init()
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO donations (amount, currency, method, note) VALUES (?, ?, ?, ?)",
            (amount, currency, method.strip().lower(), note.strip()),
        )
        donation_id = cur.lastrowid

    # v50: surface in the unified events feed so admin sees the love come in
    try:
        import events
        events.log(
            category="payment",
            severity="success",
            title=f"💝 ได้รับการสนับสนุน {currency} {amount:,.0f}",
            body=f"ผ่าน {method}" + (f" · {note}" if note else ""),
            target_page="pages/A_💝_Support.py",
            meta={"id": donation_id, "amount": amount, "method": method},
        )
    except Exception:
        pass

    return donation_id


def list_donations(limit: int = 200) -> list[dict]:
    init()
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM donations ORDER BY created_at DESC LIMIT ?", (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def confirm(donation_id: int) -> bool:
    init()
    with db.conn() as c:
        cur = c.execute(
            "UPDATE donations SET confirmed = 1 WHERE id = ?", (donation_id,),
        )
    return cur.rowcount > 0


def total_received(confirmed_only: bool = True) -> dict[str, float]:
    """Per-currency totals."""
    init()
    where = "WHERE confirmed = 1" if confirmed_only else ""
    with db.conn() as c:
        rows = c.execute(
            f"SELECT currency, SUM(amount) AS total FROM donations {where} GROUP BY currency"
        ).fetchall()
    return {r["currency"]: float(r["total"] or 0) for r in rows}
