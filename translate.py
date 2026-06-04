"""Claude-powered translator with persistent cache.

Why cache: translating 100 listings × 5 langs = 500 Claude calls. Cache keyed
by (content_hash, lang) so re-exports cost zero API calls."""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable

import db


LANG_NAMES = {
    "th": "Thai (ภาษาไทย)",
    "en": "English",
    "zh": "Simplified Chinese (简体中文)",
    "ja": "Japanese (日本語)",
    "ko": "Korean (한국어)",
    "vi": "Vietnamese (Tiếng Việt)",
    "id": "Bahasa Indonesia",
    "ms": "Bahasa Melayu",
    "fr": "French (Français)",
    "es": "Spanish (Español)",
    "de": "German (Deutsch)",
    "pt": "Portuguese (Português)",
    "ar": "Arabic (العربية)",
}


CACHE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL,
    target_lang TEXT NOT NULL,
    field TEXT NOT NULL,
    source_text TEXT,
    translated_text TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(content_hash, target_lang, field)
);

CREATE INDEX IF NOT EXISTS idx_translations_lookup
    ON translations(content_hash, target_lang, field);
"""


def init_cache():
    with db.conn() as c:
        c.executescript(CACHE_TABLE_SQL)


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()[:16]


def _get_cached(c: sqlite3.Connection, content_hash: str, target_lang: str, field: str) -> str | None:
    row = c.execute(
        "SELECT translated_text FROM translations "
        "WHERE content_hash = ? AND target_lang = ? AND field = ?",
        (content_hash, target_lang, field),
    ).fetchone()
    return row["translated_text"] if row else None


def _put_cache(c: sqlite3.Connection, content_hash: str, target_lang: str,
               field: str, source: str, translated: str):
    c.execute(
        "INSERT OR REPLACE INTO translations "
        "(content_hash, target_lang, field, source_text, translated_text) "
        "VALUES (?, ?, ?, ?, ?)",
        (content_hash, target_lang, field, source, translated),
    )


PROMPT = """Translate the following marketplace listing text to {lang_name}.

Rules:
- Preserve the meaning exactly — do NOT add or remove information
- Keep the marketplace tone (commercial, persuasive)
- Keep numbers, model codes, brand names AS-IS (no translation)
- Keep formatting (bullets, line breaks) as-is
- If the source is already in the target language, return it unchanged
- Return ONLY the translated text — no commentary, no quotes

Source:
{source}"""


def translate_text(text: str, target_lang: str, api_key: str | None = None) -> str:
    """Translate a single string. Uses cache."""
    if not text or not text.strip():
        return text
    init_cache()
    content_hash = _hash(text)

    with db.conn() as c:
        cached = _get_cached(c, content_hash, target_lang, "_text")
        if cached is not None:
            return cached

    # Cache miss → call Claude
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
    lang_name = LANG_NAMES.get(target_lang, target_lang)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2500,
        messages=[{
            "role": "user",
            "content": PROMPT.format(lang_name=lang_name, source=text),
        }],
    )
    out = msg.content[0].text.strip()
    # Strip accidental quotes
    if out.startswith(("'", '"')) and out.endswith(("'", '"')):
        out = out[1:-1]

    with db.conn() as c:
        _put_cache(c, content_hash, target_lang, "_text", text, out)
    return out


def translate_row(row: dict, target_lang: str, api_key: str | None = None,
                  fields: list[str] | None = None) -> dict:
    """Translate selected fields of a listing dict. Returns new dict with
    translated fields (other fields untouched)."""
    fields = fields or ["title", "description"]
    out = dict(row)
    for f in fields:
        val = row.get(f)
        if isinstance(val, str) and val.strip():
            out[f] = translate_text(val, target_lang, api_key=api_key)
    return out


def translate_batch(rows: list[dict], target_lang: str,
                    api_key: str | None = None,
                    fields: list[str] | None = None,
                    workers: int = 6,
                    on_progress: Callable[[int, int], None] | None = None) -> list[dict]:
    """Parallel translate. Cache hits run instantly so most calls are fast."""
    if target_lang == "th" or not rows:
        return [dict(r) for r in rows]

    out = [None] * len(rows)
    total = len(rows)
    done = 0

    def work(i: int):
        out[i] = translate_row(rows[i], target_lang, api_key=api_key, fields=fields)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(work, i) for i in range(total)]
        for _ in as_completed(futures):
            done += 1
            if on_progress:
                on_progress(done, total)
    return out


def cache_stats() -> dict:
    init_cache()
    with db.conn() as c:
        total = c.execute("SELECT COUNT(*) FROM translations").fetchone()[0]
        by_lang = c.execute(
            "SELECT target_lang, COUNT(*) AS n FROM translations GROUP BY target_lang"
        ).fetchall()
    return {"total": total, "by_lang": {r["target_lang"]: r["n"] for r in by_lang}}
