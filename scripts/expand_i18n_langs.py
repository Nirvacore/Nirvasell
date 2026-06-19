#!/usr/bin/env python3
"""Expand th+en-only i18n keys to all LANGS via Google Translate.

Patches i18n.py in place after each language (resumable). Preserves
{placeholders}, URLs, emoji, and brand tokens.

Usage:
  python3 scripts/expand_i18n_langs.py
  python3 scripts/expand_i18n_langs.py --marker "B/C pack inline"
  python3 scripts/expand_i18n_langs.py --lang ja
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from deep_translator import GoogleTranslator

ROOT = Path(__file__).resolve().parent.parent
I18N_PATH = ROOT / "i18n.py"

TARGET_MAP: dict[str, str] = {
    "vi": "vi", "id": "id", "ms": "ms", "tl": "tl",
    "my": "my", "km": "km", "lo": "lo", "zh": "zh-CN",
    "ja": "ja", "ko": "ko", "es": "es", "fr": "fr",
    "pt": "pt", "de": "de", "ar": "ar", "hi": "hi", "ru": "ru",
}

_PRESERVE = re.compile(
    r"(\{[a-zA-Z_][a-zA-Z0-9_]*\}|"
    r"nirva\.sell|Shopee|Lazada|TikTok|Facebook|LINE|PromptPay|"
    r"SMTP|Telegram|Webhook|Slack|Discord|Zapier|SQLite|SKU|PO|VAT|"
    r"COGS|DOH|MoM|CLV|API|DELETE|URL|HTTP|JSON|CSV|ZIP|"
    r"฿|≤|@BotFather|https?://[^\s]+|<[^>]+>)"
)

_TH_EN_RE = re.compile(
    r'^(\s*)"([^"]+)":\s*\{"th":\s*"((?:[^"\\]|\\.)*)",\s*"en":\s*"((?:[^"\\]|\\.)*)"\},?\s*$'
)
_MULTI_RE = re.compile(
    r'^(\s*)"([^"]+)":\s*\{(.*)\},?\s*$'
)
_PAIR_RE = re.compile(r'"([a-z]{2})":\s*"((?:[^"\\]|\\.)*)"')


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _unesc(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


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
    code = TARGET_MAP[target]
    tr = GoogleTranslator(source="en", target=code)
    out = tr.translate(masked) or masked
    return _unmask(out, toks)


def _translate_batch(texts: list[str], target: str, *, chunk: int = 12) -> list[str]:
    code = TARGET_MAP[target]
    tr = GoogleTranslator(source="en", target=code)
    out: list[str] = []
    for i in range(0, len(texts), chunk):
        chunk_texts = texts[i : i + chunk]
        masked, token_maps = [], []
        for t in chunk_texts:
            m, tok = _mask_placeholders(t)
            masked.append(m)
            token_maps.append(tok)
        try:
            translated = tr.translate_batch(masked)
        except Exception:
            translated = [_translate_one(t, target) for t in chunk_texts]
        for orig, tr_text, toks in zip(chunk_texts, translated, token_maps):
            out.append(_unmask(tr_text, toks) if tr_text else orig)
        time.sleep(0.15)
    return out


def _parse_line(line: str) -> tuple[str, str, dict[str, str]] | None:
    m = _TH_EN_RE.match(line)
    if m:
        key = m.group(2)
        return m.group(1), key, {"th": _unesc(m.group(3)), "en": _unesc(m.group(4))}
    m = _MULTI_RE.match(line)
    if not m:
        return None
    key = m.group(2)
    vals = {lang: _unesc(val) for lang, val in _PAIR_RE.findall(m.group(3))}
    if "th" in vals and "en" in vals:
        return m.group(1), key, vals
    return None


def _parse_entries(lines: list[str], marker: str | None) -> list[tuple[int, str, str, dict[str, str]]]:
    in_section = marker is None
    entries: list[tuple[int, str, str, dict[str, str]]] = []
    for i, line in enumerate(lines):
        if marker and marker in line:
            in_section = True
            continue
        if not in_section:
            continue
        parsed = _parse_line(line)
        if parsed:
            indent, key, vals = parsed
            entries.append((i, indent, key, vals))
    return entries


def _format_entry(indent: str, key: str, vals: dict[str, str]) -> str:
    order = ["th", "en"] + [c for c in TARGET_MAP if c in vals]
    parts = ", ".join(f'"{k}": "{_esc(vals[k])}"' for k in order)
    pad = max(1, 40 - len(key))
    return f'{indent}"{key}":{" " * pad}{{{parts}}},'


def _write_entries(lines: list[str], entries: list[tuple[int, str, str, dict[str, str]]]) -> None:
    for idx, indent, key, vals in entries:
        lines[idx] = _format_entry(indent, key, vals)


def expand(
    *,
    marker: str | None = "B/C pack inline",
    langs: list[str] | None = None,
    dry_run: bool = False,
) -> dict:
    lines = I18N_PATH.read_text(encoding="utf-8").splitlines()
    entries = _parse_entries(lines, marker)
    if not entries:
        return {"updated": 0, "keys": 0}

    target_langs = langs or list(TARGET_MAP)
    done_langs: list[str] = []

    for lang in target_langs:
        need = [e for e in entries if lang not in e[3]]
        if not need:
            print(f"  skip {lang} (already complete)", flush=True)
            done_langs.append(lang)
            continue
        print(f"  → {lang}: {len(need)} keys", flush=True)
        en_texts = [e[3]["en"] for e in need]
        translated = _translate_batch(en_texts, lang)
        for entry, val in zip(need, translated):
            entry[3][lang] = val
        done_langs.append(lang)
        if not dry_run:
            _write_entries(lines, entries)
            I18N_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"    saved ({lang})", flush=True)
        time.sleep(0.5)

    return {
        "updated": len(entries),
        "keys": len({e[2] for e in entries}),
        "langs_done": done_langs,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Expand th+en i18n keys to all LANGS")
    p.add_argument("--marker", default="B/C pack inline")
    p.add_argument("--all", action="store_true")
    p.add_argument("--lang", action="append", dest="langs")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    marker = None if args.all else args.marker
    print(f"Expanding i18n (marker={marker!r})...")
    summary = expand(marker=marker, langs=args.langs, dry_run=args.dry_run)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
