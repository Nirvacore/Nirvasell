"""Multi-tenant auth: per-user account + per-user DB isolation.

Implementation choices:
  • Password hash: PBKDF2-SHA256 with random salt (stdlib only — no extra deps)
  • Account store: shared SQLite at data/accounts.db (NOT a per-user file)
  • Sessions: token in st.session_state (lifetime = browser tab)
  • Data isolation: each user gets data/users/{user_id}/listo.db

Why per-user DB files instead of user_id columns?
  • Stronger isolation — no risk of leaky WHERE-clauses
  • Trivial backup / GDPR delete
  • Lets us reuse all existing db.py code unchanged"""
from __future__ import annotations
import hashlib
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).parent
DATA = ROOT / "data"
ACCOUNTS_PATH = DATA / "accounts.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    pw_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    display_name TEXT,
    role TEXT DEFAULT 'user',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_login TEXT
);
"""

# v29: additional columns added via ALTER TABLE for backwards compatibility.
#   • avatar_url       — profile pic from OAuth provider
#   • oauth_provider   — 'google' | 'apple' | 'microsoft' | 'line' | NULL
#   • oauth_sub        — provider's stable user ID (subject claim)
# Users may have BOTH a password and OAuth — login picks whichever succeeds.
_V29_COLUMNS = {
    "avatar_url":     "TEXT",
    "oauth_provider": "TEXT",
    "oauth_sub":      "TEXT",
}


# ---- DB --------------------------------------------------------------------

def _ensure_dir():
    DATA.mkdir(exist_ok=True)
    (DATA / "users").mkdir(exist_ok=True)


@contextmanager
def _accounts():
    _ensure_dir()
    c = sqlite3.connect(ACCOUNTS_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    _ensure_dir()
    with _accounts() as c:
        c.executescript(SCHEMA)
        # v29 migration: add OAuth columns to existing tables, idempotent.
        cols = {r[1] for r in c.execute("PRAGMA table_info(users)").fetchall()}
        for name, sql_type in _V29_COLUMNS.items():
            if name not in cols:
                c.execute(f"ALTER TABLE users ADD COLUMN {name} {sql_type}")
        c.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_oauth "
            "ON users(oauth_provider, oauth_sub)"
        )


# ---- Password ops ----------------------------------------------------------

ITERS = 200_000  # PBKDF2 rounds


def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERS).hex()


def _new_salt() -> bytes:
    return secrets.token_bytes(16)


# ---- Validators ------------------------------------------------------------

EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_email(s: str) -> bool:
    return bool(EMAIL_RX.match((s or "").strip()))


def valid_password(s: str) -> tuple[bool, str]:
    s = s or ""
    if len(s) < 8:
        return False, "Password ต้องยาว ≥ 8 ตัวอักษร"
    if s.lower() == s and s.upper() == s and not any(ch.isdigit() for ch in s):
        return False, "Password ต้องมีทั้งตัวอักษร + ตัวเลข"
    return True, ""


# ---- Public API ------------------------------------------------------------

def signup(email: str, password: str, display_name: str = "") -> tuple[bool, str]:
    email = (email or "").strip().lower()
    if not valid_email(email):
        return False, "อีเมลไม่ถูกต้อง"
    ok, msg = valid_password(password)
    if not ok:
        return False, msg

    init()
    salt = _new_salt()
    pw_hash = _hash(password, salt)
    try:
        with _accounts() as c:
            # First user becomes admin
            existing = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            role = "admin" if existing == 0 else "user"
            c.execute(
                "INSERT INTO users (email, pw_hash, salt, display_name, role) VALUES (?, ?, ?, ?, ?)",
                (email, pw_hash, salt.hex(), display_name or email.split("@")[0], role),
            )
        return True, "Signup ok"
    except sqlite3.IntegrityError:
        return False, "อีเมลนี้ใช้งานแล้ว"


# ---- Admin actions --------------------------------------------------------

def is_admin() -> bool:
    u = current_user()
    return bool(u and u.get("role") == "admin")


def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    """User-driven password change (requires old password)."""
    init()
    with _accounts() as c:
        row = c.execute(
            "SELECT pw_hash, salt FROM users WHERE id = ?", (user_id,),
        ).fetchone()
        if not row:
            return False, "User not found"
        salt = bytes.fromhex(row["salt"])
        if _hash(old_password, salt) != row["pw_hash"]:
            return False, "Password เดิมไม่ถูกต้อง"
    return reset_password(user_id, new_password)


def update_display_name(user_id: int, new_name: str) -> bool:
    init()
    new_name = (new_name or "").strip()
    if not new_name:
        return False
    with _accounts() as c:
        cur = c.execute(
            "UPDATE users SET display_name = ? WHERE id = ?",
            (new_name, user_id),
        )
    return cur.rowcount > 0


def reset_password(user_id: int, new_password: str) -> tuple[bool, str]:
    ok, msg = valid_password(new_password)
    if not ok:
        return False, msg
    init()
    salt = _new_salt()
    pw_hash = _hash(new_password, salt)
    with _accounts() as c:
        cur = c.execute(
            "UPDATE users SET pw_hash = ?, salt = ? WHERE id = ?",
            (pw_hash, salt.hex(), user_id),
        )
        if cur.rowcount == 0:
            return False, "User not found"
    return True, "Password reset"


def set_role(user_id: int, role: str) -> bool:
    if role not in ("admin", "user"):
        return False
    init()
    with _accounts() as c:
        cur = c.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    return cur.rowcount > 0


def delete_user(user_id: int) -> tuple[bool, str]:
    """Delete account + their per-user DB. Returns (ok, msg)."""
    init()
    with _accounts() as c:
        admins = c.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        target = c.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        if not target:
            return False, "User not found"
        if target["role"] == "admin" and admins <= 1:
            return False, "Cannot delete the last admin"
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # Drop per-user DB
    db_path = DATA / "users" / f"{user_id}.db"
    if db_path.exists():
        try:
            db_path.unlink()
        except Exception:
            pass
    return True, "User + data deleted"


def user_db_size(user_id: int) -> int:
    p = DATA / "users" / f"{user_id}.db"
    return p.stat().st_size if p.exists() else 0


def login(email: str, password: str) -> tuple[bool, str | dict]:
    email = (email or "").strip().lower()
    if not email or not password:
        return False, "กรอกอีเมลและ password"

    # Rate limit: stop brute-force before touching the password compare.
    import _rate_limit as rl
    allowed, retry = rl.check(email)
    if not allowed:
        mins = max(1, retry // 60)
        return False, f"ล็อกชั่วคราว — รออีก {mins} นาที (ลองผิดเกินกำหนด)"

    init()
    with _accounts() as c:
        row = c.execute(
            "SELECT id, email, pw_hash, salt, display_name, role FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if not row:
            rl.record_failure(email)
            return False, "อีเมล/password ไม่ถูกต้อง"

        salt = bytes.fromhex(row["salt"])
        if _hash(password, salt) != row["pw_hash"]:
            still_ok, wait = rl.record_failure(email)
            if not still_ok:
                mins = max(1, wait // 60)
                return False, f"ผิดเกินกำหนด — ล็อก {mins} นาที"
            stats = rl.stats(email)
            n_left = stats.get("remaining", 0)
            return False, f"อีเมล/password ไม่ถูกต้อง (เหลือลองได้อีก {n_left} ครั้ง)"

        # Success — clear the counter
        rl.clear(email)
        c.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],))

    return True, {
        "id":           row["id"],
        "email":        row["email"],
        "display_name": row["display_name"],
        "role":         row["role"],
    }


# ---- OAuth / passwordless ------------------------------------------------

def login_or_create_oauth(*, provider: str, sub: str, email: str,
                          name: str = "", avatar: str = "") -> dict:
    """Idempotent: returns the user dict either for an existing row or a
    freshly created one. Linking rules:
      1. Match by (provider, sub) — strongest, survives email change
      2. Else match by email — auto-link an existing password account
      3. Else create new (first-ever user gets admin)

    OAuth-only accounts get a random unguessable password they never use
    (so the schema's NOT NULL constraint stays satisfied)."""
    email = (email or "").strip().lower()
    provider = (provider or "").strip().lower()
    if not provider or not sub:
        raise ValueError("provider and sub required")
    if not valid_email(email):
        # Apple sometimes returns no email after first login; we'd need to
        # capture it differently. Reject for now — caller can prompt user.
        raise ValueError("oauth provider returned no usable email")

    init()
    with _accounts() as c:
        # 1. (provider, sub) match
        row = c.execute(
            "SELECT id, email, display_name, role, avatar_url FROM users "
            "WHERE oauth_provider = ? AND oauth_sub = ?",
            (provider, sub),
        ).fetchone()
        if row:
            c.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP, "
                "                 display_name = COALESCE(NULLIF(?, ''), display_name), "
                "                 avatar_url   = COALESCE(NULLIF(?, ''), avatar_url) "
                "WHERE id = ?",
                (name, avatar, row["id"]),
            )
            return _row_to_user(row)

        # 2. Email match — link OAuth to an existing password account
        row = c.execute(
            "SELECT id, email, display_name, role, avatar_url FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row:
            c.execute(
                "UPDATE users SET oauth_provider = ?, oauth_sub = ?, "
                "                 last_login = CURRENT_TIMESTAMP, "
                "                 avatar_url = COALESCE(NULLIF(?, ''), avatar_url) "
                "WHERE id = ?",
                (provider, sub, avatar, row["id"]),
            )
            return _row_to_user(row)

        # 3. Brand-new user
        existing = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        role = "admin" if existing == 0 else "user"
        salt = _new_salt()
        rand_pw = secrets.token_urlsafe(32)  # unusable, just satisfies NOT NULL
        pw_hash = _hash(rand_pw, salt)
        display = name or email.split("@")[0]
        cur = c.execute(
            """INSERT INTO users
               (email, pw_hash, salt, display_name, role,
                avatar_url, oauth_provider, oauth_sub, last_login)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (email, pw_hash, salt.hex(), display, role, avatar, provider, sub),
        )
        return {
            "id":           cur.lastrowid,
            "email":        email,
            "display_name": display,
            "role":         role,
            "avatar_url":   avatar,
        }


def _row_to_user(row) -> dict:
    return {
        "id":           row["id"],
        "email":        row["email"],
        "display_name": row["display_name"],
        "role":         row["role"],
        "avatar_url":   row["avatar_url"] if "avatar_url" in row.keys() else "",
    }


def login_or_create_email(email: str, name: str = "") -> dict:
    """Used by magic-link flow: caller has already verified the email via a
    signed token they clicked. We trust the email is real and create-or-find."""
    email = (email or "").strip().lower()
    if not valid_email(email):
        raise ValueError("invalid email")
    init()
    with _accounts() as c:
        row = c.execute(
            "SELECT id, email, display_name, role, avatar_url FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if row:
            c.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                      (row["id"],))
            return _row_to_user(row)

        existing = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        role = "admin" if existing == 0 else "user"
        salt = _new_salt()
        rand_pw = secrets.token_urlsafe(32)
        pw_hash = _hash(rand_pw, salt)
        display = name or email.split("@")[0]
        cur = c.execute(
            """INSERT INTO users (email, pw_hash, salt, display_name, role, last_login)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (email, pw_hash, salt.hex(), display, role),
        )
        return {"id": cur.lastrowid, "email": email,
                "display_name": display, "role": role, "avatar_url": ""}


def current_user() -> dict | None:
    return st.session_state.get("auth_user")


def is_authenticated() -> bool:
    return bool(current_user())


def login_user(user: dict):
    st.session_state["auth_user"] = user


def logout():
    for k in ("auth_user", "lang", "api_key"):
        st.session_state.pop(k, None)


def list_users() -> list[dict]:
    init()
    with _accounts() as c:
        rows = c.execute(
            "SELECT id, email, display_name, role, created_at, last_login FROM users "
            "ORDER BY created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


# ---- Per-user DB path ------------------------------------------------------

def user_db_path() -> Path:
    """Return the SQLite path for the active user. Falls back to a shared
    default for CLI scripts (no Streamlit session)."""
    _ensure_dir()
    u = current_user()
    if u:
        return DATA / "users" / f"{u['id']}.db"
    return DATA / "listo.db"
