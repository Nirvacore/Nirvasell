"""Fire-and-forget welcome email when a new account signs up. Uses the same
SMTP env vars as magic_link.py — SMTP_HOST / SMTP_USER / SMTP_PASS /
SMTP_FROM / APP_URL.

If SMTP isn't configured, this no-ops silently (signup still succeeds —
welcome email is "nice to have", not "must-send")."""
from __future__ import annotations
import os
import smtplib
import ssl
from email.message import EmailMessage


def _smtp_config() -> dict:
    return {
        "host": os.getenv("SMTP_HOST", ""),
        "port": int(os.getenv("SMTP_PORT", "587") or 587),
        "user": os.getenv("SMTP_USER", ""),
        "pass": os.getenv("SMTP_PASS", ""),
        "from": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "")),
    }


def smtp_configured() -> bool:
    c = _smtp_config()
    return bool(c["host"] and c["user"] and c["pass"])


_SUBJECTS = {
    "th": "ยินดีต้อนรับสู่ nirva.sell",
    "en": "Welcome to nirva.sell",
    "zh": "欢迎使用 nirva.sell",
    "ja": "nirva.sell へようこそ",
    "ko": "nirva.sell에 오신 것을 환영합니다",
    "vi": "Chào mừng đến với nirva.sell",
    "id": "Selamat datang di nirva.sell",
}


def _body(name: str, app_url: str, lang: str) -> str:
    """Plain-text body. Plain beats HTML — better deliverability + readable
    in any client."""
    greet = name or "เพื่อน"
    bodies = {
        "th": f"""สวัสดีคุณ {greet},

ยินดีต้อนรับสู่ nirva.sell — AI ช่วยรวมของขายของ reseller ไทย

เริ่มต้นได้ที่:
{app_url}

3 อย่างแรกที่แนะนำให้ลอง:
  1. หน้า "🚀 Start" — wizard 4 ขั้นตอน
  2. หน้า "📸 Vision" — drop ภาพสินค้า → AI อ่านสเปคให้
  3. หน้า "🤖 Generate" — สร้าง listing/LINE/FB/TikTok ในคลิกเดียว

ข้อมูลของคุณอยู่บนเครื่องเรา — ไม่แชร์ที่ไหน, ลบเองได้ทุกเมื่อ
ผ่านหน้า Account

ถ้ามีปัญหาอะไร reply เมลนี้ได้เลย — เราอ่านจริงๆ

— nirva.sell""",

        "en": f"""Hi {greet},

Welcome to nirva.sell — AI tooling for resellers who want to consolidate
products + sell across marketplaces.

Get started:
{app_url}

Three things to try first:
  1. "🚀 Start" page — 4-step wizard
  2. "📸 Vision" page — drop product photos, AI reads specs
  3. "🤖 Generate" — listings/social posts in one click

Your data stays in your own per-user database — never shared, deletable
anytime from the Account page.

Questions? Just reply to this email.

— nirva.sell""",
    }
    return bodies.get(lang, bodies["en"])


def send(email: str, name: str = "", lang: str = "th") -> tuple[bool, str]:
    """Best-effort welcome email. Returns (sent, message-or-reason)."""
    if not smtp_configured():
        return False, "smtp_not_configured"
    if not email or "@" not in email:
        return False, "bad_email"
    cfg = _smtp_config()
    app_url = (os.getenv("APP_URL", "") or "http://localhost:8501").rstrip("/")
    subject = _SUBJECTS.get(lang, _SUBJECTS["en"])
    body = _body(name, app_url, lang)

    msg = EmailMessage()
    msg["From"] = cfg["from"]
    msg["To"] = email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        ctx = ssl.create_default_context()
        if cfg["port"] == 465:
            with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20, context=ctx) as s:
                s.login(cfg["user"], cfg["pass"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as s:
                s.starttls(context=ctx)
                s.login(cfg["user"], cfg["pass"])
                s.send_message(msg)
        return True, "sent"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
