"""Bulk auto-translation of UI strings — uses Claude (via translate.py)
to fill in missing translations for any language, then writes them to a
per-language JSON cache that i18n.py reads at startup.

Why this exists:
  We support 19 languages but manually translating ~750 strings × 12 new
  languages = 9,000+ entries is impractical. This module lets a user
  (or admin) click "Translate UI to Bahasa Melayu" once, and every string
  gets translated by Claude in a single batch + cached to disk.

Cache file layout:
  data/i18n_auto/{lang}.json  →  {"key1": "translation", "key2": ..., ...}

These files are merged into STRINGS at import time, so subsequent UI loads
are instant — no API calls per page render.
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import Callable

import i18n


_AUTO_DIR = Path(__file__).parent / "data" / "i18n_auto"


# ---- Disk cache ---------------------------------------------------------

def cache_path(lang: str) -> Path:
    return _AUTO_DIR / f"{lang}.json"


def load_cache(lang: str) -> dict[str, str]:
    p = cache_path(lang)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_cache(lang: str, data: dict[str, str]) -> None:
    _AUTO_DIR.mkdir(parents=True, exist_ok=True)
    p = cache_path(lang)
    p.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


# ---- Merge into i18n.STRINGS at startup --------------------------------

def merge_caches_into_strings() -> int:
    """Read every {lang}.json under data/i18n_auto and merge translations
    back into i18n.STRINGS. Returns the count of entries merged.
    Called once from i18n.py at module import."""
    if not _AUTO_DIR.exists():
        return 0
    n = 0
    for path in _AUTO_DIR.glob("*.json"):
        lang = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for key, val in data.items():
            entry = i18n.STRINGS.setdefault(key, {})
            # Only fill if the manually-curated source doesn't already have it
            if lang not in entry and val:
                entry[lang] = val
                n += 1
    return n


# ---- Bulk translate one language ---------------------------------------

def missing_keys(lang: str, source_lang: str = "en") -> list[str]:
    """Keys that have a source but no translation yet for `lang`."""
    out = []
    for key, entry in i18n.STRINGS.items():
        if lang in entry and entry[lang]:
            continue
        if not entry.get(source_lang) and not entry.get("th"):
            # Nothing to translate from
            continue
        out.append(key)
    return out


# Claude prompt — translate a batch of UI strings in one call. Returns a
# JSON object keyed by the same keys we sent, so each line can be matched.
_BATCH_PROMPT = """You are translating UI labels for a SaaS web app called
nirva.sell — a tool that helps online sellers list products on marketplaces
like Shopee, Lazada, and TikTok Shop. Keep the tone friendly, casual,
modern. NEVER translate code-like tokens (variable names in {curly braces},
HTML tags, emoji). Keep brand names (nirva.sell, Shopee, Lazada, TikTok,
Google, LINE, etc.) untranslated.

Target language: {lang_name}

Translate the JSON below. Return ONLY a valid JSON object with the same
keys, where each value is the translation. No commentary, no ``` fences.

{source_json}
"""


def _claude_translate_batch(items: dict[str, str], lang: str,
                            api_key: str) -> dict[str, str]:
    """Single Claude call for a batch. Returns {key: translation}."""
    from anthropic import Anthropic
    from translate import LANG_NAMES
    lang_name = LANG_NAMES.get(lang, lang)

    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8000,
        messages=[{
            "role": "user",
            "content": _BATCH_PROMPT.format(
                lang_name=lang_name,
                source_json=json.dumps(items, ensure_ascii=False, indent=2),
            ),
        }],
    )
    out_text = msg.content[0].text.strip()
    # Strip any accidental code fence
    if out_text.startswith("```"):
        out_text = "\n".join(out_text.split("\n")[1:-1])
    try:
        result = json.loads(out_text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(result, dict):
        return {}
    # Keep only keys we asked for + non-empty values
    return {k: v.strip() for k, v in result.items()
            if k in items and isinstance(v, str) and v.strip()}


def translate_language(lang: str, *, api_key: str,
                       batch_size: int = 25,
                       progress: Callable[[int, int], None] | None = None,
                       source_lang: str = "en") -> dict:
    """Translate every missing string for `lang`, write to disk cache, and
    merge back into i18n.STRINGS. Returns a summary dict."""
    keys = missing_keys(lang, source_lang=source_lang)
    if not keys:
        return {"translated": 0, "total": 0, "from_cache": 0}

    # Start with anything already cached on disk
    cache = load_cache(lang)
    already_cached = sum(1 for k in keys if k in cache)
    to_translate = [k for k in keys if k not in cache]

    n_done = already_cached
    total = len(keys)
    if progress:
        progress(n_done, total)

    # Batch the missing ones
    for i in range(0, len(to_translate), batch_size):
        batch_keys = to_translate[i:i + batch_size]
        items = {}
        for k in batch_keys:
            entry = i18n.STRINGS.get(k, {})
            src = entry.get(source_lang) or entry.get("en") or entry.get("th") or k
            items[k] = src
        try:
            translations = _claude_translate_batch(items, lang, api_key)
        except Exception:
            translations = {}
        # Merge into cache
        for k, v in translations.items():
            cache[k] = v
        # Save incrementally (so we don't lose progress on crash)
        save_cache(lang, cache)
        n_done += len(batch_keys)
        if progress:
            progress(n_done, total)

    # Merge final into STRINGS
    for k, v in cache.items():
        entry = i18n.STRINGS.setdefault(k, {})
        if lang not in entry and v:
            entry[lang] = v

    return {
        "translated":  len(cache) - already_cached,
        "total":       total,
        "from_cache":  already_cached,
        "lang":        lang,
    }


def coverage(lang: str) -> dict:
    """Return how complete `lang` is — total keys, how many translated."""
    total = sum(1 for k, e in i18n.STRINGS.items() if e)
    done = sum(1 for k, e in i18n.STRINGS.items() if e.get(lang))
    return {
        "total":   total,
        "done":    done,
        "percent": (100 * done // max(1, total)),
    }
