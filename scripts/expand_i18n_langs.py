#!/usr/bin/env python3
"""Expand i18n STRINGS to all LANGS via Google Translate.

Workflow (same pattern as auto_translate cache, but committed to git):
  1. translate  → scripts/i18n_lang_cache/{lang}.json  (resumable)
  2. merge        → patch i18n.py from cache

Usage:
  python3 scripts/expand_i18n_langs.py translate --all
  python3 scripts/expand_i18n_langs.py translate --all --lang vi
  python3 scripts/expand_i18n_langs.py merge
  python3 scripts/expand_i18n_langs.py status
"""
from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parent.parent
I18N_PATH = ROOT / "i18n.py"
CACHE_DIR = Path(__file__).resolve().parent / "i18n_lang_cache"

TARGET_LANGS = [
    "vi", "id", "ms", "tl", "my", "km", "lo", "zh", "ja", "ko",
    "es", "fr", "pt", "de", "ar", "hi", "ru",
]

TARGET_MAP: dict[str, str] = {
    "vi": "vi", "id": "id", "ms": "ms", "tl": "tl",
    "my": "my", "km": "km", "lo": "lo", "zh": "zh-CN",
    "ja": "ja", "ko": "ko", "es": "es", "fr": "fr",
    "pt": "pt", "de": "de", "ar": "ar", "hi": "hi", "ru": "ru",
}

_PRESERVE = re.compile(
    r"(\{[a-zA-Z_][a-zA-Z0-9_]*\}|"
    r"\{\{[a-zA-Z0-9_-]+\}\}|"
    r"nirva\.sell|Shopee|Lazada|TikTok|Facebook|LINE|PromptPay|"
    r"SMTP|Telegram|Webhook|Slack|Discord|Zapier|SQLite|SKU|PO|VAT|"
    r"COGS|DOH|MoM|CLV|API|DELETE|URL|HTTP|JSON|CSV|ZIP|"
    r"฿|≤|@BotFather|https?://[^\s]+|<[^>]+>)"
)

_KEY_LINE = re.compile(r'^(\s*)"([^"]+)":\s*\{')
_PAIR_RE = re.compile(r'"([a-z]{2})":\s*"((?:[^"\\]|\\.)*)"')


@dataclass
class Entry:
    key: str
    indent: str
    vals: dict[str, str] = field(default_factory=dict)


def _esc(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "")
    )


def _unesc(s: str) -> str:
    return s.replace("\\n", "\n").replace('\\"', '"').replace("\\\\", "\\")


def _mask_placeholders(text: str) -> tuple[str, list[str]]:
    tokens: list[str] = []

    def repl(m: re.Match) -> str:
        tokens.append(m.group(0))
        return f"__TOK{len(tokens) - 1}__"

    return _PRESERVE.sub(repl, text), tokens


def _unmask(text: str, tokens: list[str]) -> str:
    for i, tok in enumerate(tokens):
        text = text.replace(f"__TOK{i}__", tok)
    return text


def _translate_one(text: str, target: str) -> str:
    masked, toks = _mask_placeholders(text)
    tr = GoogleTranslator(source="en", target=TARGET_MAP[target])
    try:
        out = tr.translate(masked) or masked
    except Exception:
        out = masked
    return _unmask(out, toks)


def _translate_batch(texts: list[str], target: str, *, chunk: int = 20) -> list[str]:
    tr = GoogleTranslator(source="en", target=TARGET_MAP[target])
    out: list[str] = []
    for i in range(0, len(texts), chunk):
        batch = texts[i : i + chunk]
        masked, token_maps = [], []
        for t in batch:
            m, tok = _mask_placeholders(t)
            masked.append(m)
            token_maps.append(tok)
        try:
            translated = tr.translate_batch(masked)
        except Exception:
            translated = []
            for t in batch:
                try:
                    translated.append(_translate_one(t, target))
                except Exception:
                    translated.append(t)
        for orig, tr_text, toks in zip(batch, translated, token_maps):
            out.append(_unmask(tr_text, toks) if tr_text else orig)
        time.sleep(0.1)
    return out


def _parse_block(lines: list[str], start: int) -> tuple[Entry, int]:
    m = _KEY_LINE.match(lines[start])
    assert m
    indent, key = m.group(1), m.group(2)
    depth = lines[start].count("{") - lines[start].count("}")
    end = start
    block = [lines[start]]
    while depth > 0:
        end += 1
        block.append(lines[end])
        depth += lines[end].count("{") - lines[end].count("}")
    vals = {lang: _unesc(val) for lang, val in _PAIR_RE.findall("\n".join(block))}
    return Entry(key=key, indent=indent, vals=vals), end


def parse_entries(lines: list[str], *, marker: str | None) -> dict[str, Entry]:
    in_strings = False
    in_section = marker is None
    entries: dict[str, Entry] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("STRINGS"):
            in_strings = True
            i += 1
            continue
        if in_strings and line.startswith("def "):
            break
        if marker and marker in line:
            in_section = True
            i += 1
            continue
        if in_strings and in_section:
            if _KEY_LINE.match(line):
                entry, end = _parse_block(lines, i)
                entries[entry.key] = entry
                i = end + 1
                continue
        i += 1
    return entries


def _format_entry(entry: Entry) -> str:
    order: list[str] = []
    for k in ["th", "en"] + TARGET_LANGS:
        if k in entry.vals and k not in order:
            order.append(k)
    for k in entry.vals:
        if k not in order:
            order.append(k)
    single_parts = ", ".join(f'"{k}": "{_esc(entry.vals[k])}"' for k in order)
    multiline = any("\n" in entry.vals[k] for k in order)
    if not multiline and len(single_parts) < 220:
        pad = max(1, 40 - len(entry.key))
        return f'{entry.indent}"{entry.key}":{" " * pad}{{{single_parts}}},'
    inner = ",\n".join(
        f'{entry.indent}    "{k}": "{_esc(entry.vals[k])}"' for k in order
    )
    return f'{entry.indent}"{entry.key}": {{\n{inner},\n{entry.indent}}},'


def _apply_entries(lines: list[str], entries: dict[str, Entry]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = _KEY_LINE.match(lines[i])
        if m and m.group(2) in entries:
            key = m.group(2)
            _, end = _parse_block(lines, i)
            out.append(_format_entry(entries[key]))
            i = end + 1
        else:
            out.append(lines[i])
            i += 1
    return out


def _cache_path(lang: str) -> Path:
    return CACHE_DIR / f"{lang}.json"


def _load_cache(lang: str) -> dict[str, str]:
    p = _cache_path(lang)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_cache(lang: str, data: dict[str, str]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(lang).write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def translate(
    *,
    marker: str | None = None,
    langs: list[str] | None = None,
) -> dict:
    lines = I18N_PATH.read_text(encoding="utf-8").splitlines()
    entries = parse_entries(lines, marker=marker)
    target_langs = langs or TARGET_LANGS
    summary: dict[str, int] = {}

    for lang in target_langs:
        cache = _load_cache(lang)
        need = [
            e for e in entries.values()
            if e.key not in cache and lang not in e.vals and e.vals.get("en")
        ]
        if not need:
            print(f"  skip {lang} (cache complete)", flush=True)
            summary[lang] = 0
            continue
        print(f"  → {lang}: {len(need)} keys", flush=True)
        keys = [e.key for e in need]
        en_texts = [e.vals["en"] for e in need]
        # translate in sub-batches with incremental cache save
        batch_size = 50
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i : i + batch_size]
            batch_texts = en_texts[i : i + batch_size]
            translated = _translate_batch(batch_texts, lang, chunk=20)
            for k, v in zip(batch_keys, translated):
                cache[k] = v or entries[k].vals["en"]
            _save_cache(lang, cache)
            done = min(i + batch_size, len(keys))
            print(f"    {lang}: {done}/{len(keys)}", flush=True)
        summary[lang] = len(need)

    return {"translated": summary, "keys_in_scope": len(entries)}


def merge() -> dict:
    lines = I18N_PATH.read_text(encoding="utf-8").splitlines()
    entries = parse_entries(lines, marker=None)
    merged = 0
    for lang in TARGET_LANGS:
        cache = _load_cache(lang)
        if not cache:
            continue
        for key, val in cache.items():
            if key in entries and lang not in entries[key].vals and val:
                entries[key].vals[lang] = val
                merged += 1
    new_lines = _apply_entries(lines, entries)
    I18N_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return {"merged": merged, "keys": len(entries)}


def status() -> dict:
    lines = I18N_PATH.read_text(encoding="utf-8").splitlines()
    entries = parse_entries(lines, marker=None)
    out: dict[str, dict] = {}
    for lang in TARGET_LANGS:
        cache = _load_cache(lang)
        need = sum(
            1 for e in entries.values()
            if lang not in e.vals and e.vals.get("en")
        )
        out[lang] = {"cached": len(cache), "still_missing": need}
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Expand i18n keys to all LANGS")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("translate", help="Translate missing keys → lang cache")
    t.add_argument("--marker", default=None)
    t.add_argument("--all", action="store_true")
    t.add_argument("--lang", action="append", dest="langs")

    sub.add_parser("merge", help="Apply lang caches → i18n.py")
    sub.add_parser("status", help="Show cache / missing counts")

    args = p.parse_args()

    if args.cmd == "translate":
        marker = None if args.all or not args.marker else args.marker
        print(f"Translating (marker={marker!r})...")
        print(json.dumps(translate(marker=marker, langs=args.langs), indent=2))
    elif args.cmd == "merge":
        print(json.dumps(merge(), indent=2))
    elif args.cmd == "status":
        print(json.dumps(status(), indent=2))


if __name__ == "__main__":
    main()
