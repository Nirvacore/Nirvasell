"""Multi-channel notifications: Email (SMTP), Telegram, LINE Notify, Webhook.

Per-user config lives in the user's DB (table `notify_channels`). Each event
type (policy_change, batch_done, low_stock, generation_error) routes to all
enabled channels for that user.

No external deps — uses stdlib smtplib + httpx (already in requirements)."""
from __future__ import annotations
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Callable

import httpx

import db


SCHEMA = """
CREATE TABLE IF NOT EXISTS notify_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,          -- 'email' | 'telegram' | 'line' | 'webhook'
    name TEXT,                   -- label (optional)
    config TEXT,                 -- JSON: kind-specific settings
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_used TEXT
);
"""


def init():
    with db.conn() as c:
        c.executescript(SCHEMA)


# ---- CRUD ----------------------------------------------------------------

def list_channels() -> list[dict]:
    init()
    with db.conn() as c:
        rows = c.execute(
            "SELECT id, kind, name, config, enabled, created_at, last_used "
            "FROM notify_channels ORDER BY id"
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        try:
            d["config"] = json.loads(d["config"] or "{}")
        except Exception:
            d["config"] = {}
        out.append(d)
    return out


def add_channel(kind: str, name: str, config: dict) -> int:
    init()
    with db.conn() as c:
        cur = c.execute(
            "INSERT INTO notify_channels (kind, name, config) VALUES (?, ?, ?)",
            (kind, name, json.dumps(config, ensure_ascii=False)),
        )
        return cur.lastrowid


def update_channel(channel_id: int, name: str | None = None,
                   config: dict | None = None, enabled: bool | None = None):
    init()
    with db.conn() as c:
        if name is not None:
            c.execute("UPDATE notify_channels SET name = ? WHERE id = ?", (name, channel_id))
        if config is not None:
            c.execute(
                "UPDATE notify_channels SET config = ? WHERE id = ?",
                (json.dumps(config, ensure_ascii=False), channel_id),
            )
        if enabled is not None:
            c.execute(
                "UPDATE notify_channels SET enabled = ? WHERE id = ?",
                (1 if enabled else 0, channel_id),
            )


def delete_channel(channel_id: int):
    init()
    with db.conn() as c:
        c.execute("DELETE FROM notify_channels WHERE id = ?", (channel_id,))


# ---- Senders --------------------------------------------------------------

def send_email(config: dict, subject: str, body: str) -> tuple[bool, str]:
    """SMTP config keys: host, port (default 587), user, password, to, from (optional)."""
    host = config.get("host", "")
    port = int(config.get("port", 587))
    user = config.get("user", "")
    pwd  = config.get("password", "")
    to   = config.get("to", user)
    sender = config.get("from", user)
    if not (host and user and pwd):
        return False, "Missing SMTP host/user/password"

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        ctx = ssl.create_default_context()
        if port == 465:
            with smtplib.SMTP_SSL(host, port, timeout=20, context=ctx) as s:
                s.login(user, pwd)
                s.send_message(msg)
        else:
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls(context=ctx)
                s.login(user, pwd)
                s.send_message(msg)
        return True, "sent"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def send_telegram(config: dict, subject: str, body: str) -> tuple[bool, str]:
    """Telegram config: bot_token, chat_id."""
    token = config.get("bot_token", "")
    chat_id = config.get("chat_id", "")
    if not (token and chat_id):
        return False, "Missing bot_token/chat_id"
    text = f"*{subject}*\n\n{body}"
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
        if r.is_success:
            return True, "sent"
        return False, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return False, str(e)


def send_line(config: dict, subject: str, body: str) -> tuple[bool, str]:
    """LINE Notify config: token."""
    token = config.get("token", "")
    if not token:
        return False, "Missing LINE Notify token"
    message = f"\n{subject}\n\n{body}"
    try:
        r = httpx.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {token}"},
            data={"message": message[:1000]},
            timeout=10,
        )
        if r.is_success:
            return True, "sent"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def send_webhook(config: dict, subject: str, body: str) -> tuple[bool, str]:
    """Generic webhook (Slack/Discord/Zapier/Make compatible).
    Config: url, method (default POST), payload_template (optional Python format string)."""
    url = config.get("url", "")
    if not url:
        return False, "Missing webhook URL"
    method = config.get("method", "POST").upper()
    payload = {
        "subject": subject,
        "body": body,
        "text": f"{subject}\n{body}",   # Slack-compatible
        "content": f"**{subject}**\n{body}",  # Discord-compatible
    }
    try:
        r = httpx.request(method, url, json=payload, timeout=10)
        if r.is_success:
            return True, "sent"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


SENDERS: dict[str, Callable] = {
    "email":    send_email,
    "telegram": send_telegram,
    "line":     send_line,
    "webhook":  send_webhook,
}


# ---- Fan-out --------------------------------------------------------------

def notify(subject: str, body: str, only_kinds: list[str] | None = None) -> list[dict]:
    """Send to every enabled channel for the current user. Returns per-channel
    results: [{id, kind, name, ok, msg}, ...]"""
    init()
    results: list[dict] = []
    for ch in list_channels():
        if not ch.get("enabled"):
            continue
        if only_kinds and ch["kind"] not in only_kinds:
            continue
        sender = SENDERS.get(ch["kind"])
        if not sender:
            results.append({"id": ch["id"], "kind": ch["kind"], "name": ch.get("name", ""),
                            "ok": False, "msg": "Unknown kind"})
            continue
        ok, msg = sender(ch["config"], subject, body)
        # Audit
        with db.conn() as c:
            c.execute(
                "UPDATE notify_channels SET last_used = CURRENT_TIMESTAMP WHERE id = ?",
                (ch["id"],),
            )
        results.append({"id": ch["id"], "kind": ch["kind"],
                        "name": ch.get("name", ""), "ok": ok, "msg": msg})
    return results


def test_channel(channel_id: int) -> tuple[bool, str]:
    """Send a ping to one specific channel."""
    init()
    with db.conn() as c:
        row = c.execute(
            "SELECT kind, name, config FROM notify_channels WHERE id = ?",
            (channel_id,),
        ).fetchone()
    if not row:
        return False, "Channel not found"
    sender = SENDERS.get(row["kind"])
    if not sender:
        return False, f"Unknown kind: {row['kind']}"
    config = json.loads(row["config"] or "{}")
    return sender(
        config,
        "🧪 nirva.sell test ping",
        f"Hi from nirva.sell! This is a test of your {row['kind']} channel "
        f"'{row['name'] or '(unnamed)'}'.\n\nIf you see this, your config works.",
    )
