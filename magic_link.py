"""Passwordless email login. The flow:

  1. User enters their email on the login page.
  2. We mint a short-lived signed token (15 min) tied to that email.
  3. SMTP delivers a clickable link: https://nirva.example.com/?ml=<token>
  4. User clicks; app.py / _auth_gate.py reads the query param, verifies
     the signature + expiry, then logs them in (creating the account on
     first visit).

Why HMAC + ttl instead of a DB table?
  • No server-side state to clean up
  • Tokens can't be reused after expiry — no replay risk
  • If our SECRET ever rotates, all outstanding links instantly invalidate"""
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from pathlib import Path

import db
import auth


_TTL_SECONDS = 15 * 60   # 15 min — long enough to read the email, short enough to fail closed
_SECRET_FILE = Path(__file__).parent / "data" / "magic_link.secret"


def _get_secret() -> bytes:
    """Long-lived HMAC key. Generated once on first use and stashed in the
    data dir so it survives restarts. NOT in env — that'd require operator
    setup; we want this to "just work"."""
    if _SECRET_FILE.exists():
        return _SECRET_FILE.read_bytes()
    _SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    s = secrets.token_bytes(32)
    _SECRET_FILE.write_bytes(s)
    try:
        os.chmod(_SECRET_FILE, 0o600)
    except Exception:
        pass
    return s


# ---- Token mint + verify ------------------------------------------------

def _sign(payload: bytes) -> str:
    sig = hmac.new(_get_secret(), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode() + "." \
         + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()


def _verify(token: str) -> dict | None:
    try:
        p_b64, s_b64 = token.split(".")
        # Restore padding chopped by `.rstrip("=")`
        payload = base64.urlsafe_b64decode(p_b64 + "=" * (-len(p_b64) % 4))
        sig = base64.urlsafe_b64decode(s_b64 + "=" * (-len(s_b64) % 4))
    except Exception:
        return None
    expected = hmac.new(_get_secret(), payload, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        data = json.loads(payload.decode())
    except Exception:
        return None
    if int(data.get("exp", 0)) < int(time.time()):
        return None
    return data


def mint(email: str, name: str = "") -> str:
    """Build a self-contained token for this email. Caller embeds it in a URL."""
    payload = json.dumps({
        "email": (email or "").strip().lower(),
        "name":  (name or "").strip(),
        "exp":   int(time.time()) + _TTL_SECONDS,
        "nonce": secrets.token_hex(8),
    }, separators=(",", ":")).encode()
    return _sign(payload)


def consume(token: str) -> dict | None:
    """Returns the {email, name} dict if valid; else None."""
    data = _verify(token)
    if not data:
        return None
    if not auth.valid_email(data.get("email", "")):
        return None
    return {"email": data["email"], "name": data.get("name", "")}


# ---- Email sender -------------------------------------------------------

def _smtp_config() -> dict:
    """Pull SMTP creds from env. Operator sets these once in `.env`."""
    return {
        "host": os.getenv("SMTP_HOST", ""),
        "port": int(os.getenv("SMTP_PORT", "587") or 587),
        "user": os.getenv("SMTP_USER", ""),
        "pass": os.getenv("SMTP_PASS", ""),
        "from": os.getenv("SMTP_FROM", os.getenv("SMTP_USER", "")),
    }


def smtp_configured() -> bool:
    cfg = _smtp_config()
    return bool(cfg["host"] and cfg["user"] and cfg["pass"])


def send(email: str, app_url: str, lang: str = "th",
         name: str = "") -> tuple[bool, str]:
    """Generate token + email it. Returns (ok, message-or-token).
    If SMTP isn't configured we still return the token so dev users can
    paste it manually — useful for first-run / self-host."""
    token = mint(email, name=name)
    link = f"{app_url.rstrip('/')}/?ml={token}"

    cfg = _smtp_config()
    if not smtp_configured():
        # Dev fallback: tell caller to surface the link directly in the UI
        return False, link

    subject_by_lang = {
        "th": "ลิงก์เข้าสู่ระบบ nirva.sell",
        "en": "Your nirva.sell sign-in link",
        "zh": "nirva.sell 登录链接",
        "ja": "nirva.sell サインインリンク",
        "ko": "nirva.sell 로그인 링크",
        "vi": "Liên kết đăng nhập nirva.sell",
        "id": "Tautan masuk nirva.sell",
    }
    body_by_lang = {
        "th": (f"คลิกลิงก์ด้านล่างเพื่อเข้าสู่ระบบ (อายุ 15 นาที):\n\n{link}\n\n"
               "ถ้าไม่ใช่คุณเป็นคนขอ — ไม่ต้องทำอะไร"),
        "en": (f"Click the link below to sign in (valid for 15 minutes):\n\n{link}\n\n"
               "If this wasn't you, you can safely ignore this email."),
        "zh": (f"点击下方链接登录(有效期 15 分钟):\n\n{link}\n\n如非您本人操作,请忽略此邮件。"),
        "ja": (f"次のリンクをクリックしてサインインしてください(15 分間有効):\n\n{link}\n\n"
               "心当たりがない場合は無視してください。"),
        "ko": (f"아래 링크를 클릭하여 로그인하세요 (15분간 유효):\n\n{link}\n\n"
               "본인이 요청하지 않은 경우 무시하셔도 됩니다."),
        "vi": (f"Nhấn vào liên kết bên dưới để đăng nhập (hiệu lực 15 phút):\n\n{link}\n\n"
               "Nếu bạn không yêu cầu, hãy bỏ qua email này."),
        "id": (f"Klik tautan di bawah untuk masuk (berlaku 15 menit):\n\n{link}\n\n"
               "Jika ini bukan Anda, abaikan saja email ini."),
    }
    subject = subject_by_lang.get(lang, subject_by_lang["en"])
    body = body_by_lang.get(lang, body_by_lang["en"])

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


# ---- Throttle (prevents abuse) -----------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS magic_link_throttle (
    email TEXT PRIMARY KEY,
    last_sent_at REAL
);
"""

_THROTTLE_SECONDS = 60  # don't send another link to the same email within 60s


def init():
    """Idempotent — creates throttle table in the shared accounts DB."""
    import sqlite3
    auth.init()
    p = auth.DATA / "accounts.db"
    c = sqlite3.connect(str(p))
    try:
        c.executescript(_SCHEMA)
        c.commit()
    finally:
        c.close()


def throttle_check(email: str) -> tuple[bool, int]:
    """Returns (allowed, retry_in_seconds)."""
    import sqlite3
    init()
    p = auth.DATA / "accounts.db"
    c = sqlite3.connect(str(p))
    c.row_factory = sqlite3.Row
    try:
        row = c.execute(
            "SELECT last_sent_at FROM magic_link_throttle WHERE email = ?",
            (email.lower(),),
        ).fetchone()
        now = time.time()
        if row and (now - float(row["last_sent_at"] or 0)) < _THROTTLE_SECONDS:
            wait = int(_THROTTLE_SECONDS - (now - float(row["last_sent_at"])))
            return False, max(1, wait)
        c.execute(
            """INSERT INTO magic_link_throttle (email, last_sent_at) VALUES (?, ?)
               ON CONFLICT(email) DO UPDATE SET last_sent_at = excluded.last_sent_at""",
            (email.lower(), now),
        )
        c.commit()
        return True, 0
    finally:
        c.close()
