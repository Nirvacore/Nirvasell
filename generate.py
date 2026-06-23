"""Generic batch generator that delegates prompt/parse to task modules.

A "task" is any plugin under tasks/ that exports TASK dict + build_prompt() + parse()."""
from __future__ import annotations
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from anthropic import Anthropic


DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _client(api_key: str | None = None) -> Anthropic:
    return Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))


LANG_NAMES = {
    "th": "ภาษาไทย",
    "en": "English",
    "zh": "中文 (Simplified Chinese)",
    "ja": "日本語",
    "ko": "한국어",
    "vi": "Tiếng Việt",
    "id": "Bahasa Indonesia",
    "ms": "Bahasa Melayu",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
    "pt": "Português",
    "ar": "العربية",
}


def _with_target_lang(prompt: str, target_lang: str | None) -> str:
    """If target_lang is set and not Thai (default in prompts), prefix an
    instruction so Claude writes content in the requested language."""
    if not target_lang or target_lang == "th":
        return prompt
    name = LANG_NAMES.get(target_lang, target_lang)
    return f"IMPORTANT: Write all generated content in {name}. Do not translate the JSON keys — only the string values.\n\n" + prompt


def _with_context(prompt: str,
                  campaign: dict | None = None,
                  trending_kws: list[str] | None = None) -> str:
    """Inject real-time market context into a prompt. Both args are optional."""
    extras: list[str] = []
    if campaign:
        from i18n_inline import live_promo_label
        label = live_promo_label(campaign.get("slug", "")) or "upcoming sale"
        days = campaign.get("days_until")
        date_str = campaign.get("date")
        extras.append(
            f"REAL-TIME CONTEXT — UPCOMING SALE EVENT:\n"
            f"  • {label} on {date_str} (in {days} days, region: {campaign.get('region','')})\n"
            f"  • Use this in copy: add subtle urgency, hint at the event without lying,\n"
            f"    and mention countdown phrasing where natural."
        )
    if trending_kws:
        kws = ", ".join(trending_kws[:8])
        extras.append(
            f"TRENDING KEYWORDS THIS MONTH (use 2-3 naturally — don't keyword-stuff):\n"
            f"  {kws}"
        )
    if not extras:
        return prompt
    return "\n\n".join(extras) + "\n\n---\n\n" + prompt


def _call(client: Anthropic, prompt: str, max_tokens: int = 2000) -> str:
    msg = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _stream(client: Anthropic, prompt: str, on_chunk, max_tokens: int = 4000) -> str:
    """Streaming version: each text chunk hits on_chunk(text, accumulated).
    Returns the final accumulated text."""
    acc = ""
    with client.messages.stream(
        model=DEFAULT_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            acc += text
            on_chunk(text, acc)
    return acc


def run_per_product(
    rows: list[dict],
    task_module,
    api_key: str | None = None,
    workers: int = 8,
    on_progress: Callable[[int, int], None] | None = None,
    target_lang: str | None = None,
) -> list[dict]:
    """Run a per-product task over many rows in parallel.

    Returns parallel list of {**input_row, **output_payload} dicts. Errors
    surface as a single 'error' key so a bad row doesn't break the batch."""
    client = _client(api_key)
    out: list[dict] = [dict(r) for r in rows]
    total = len(rows)
    done = 0

    def work(i: int):
        try:
            prompt = _with_target_lang(task_module.build_prompt(rows[i]), target_lang)
            text = _call(client, prompt)
            payload = task_module.parse(text)
            out[i].update(payload)
        except Exception as e:
            out[i]["error"] = f"{type(e).__name__}: {e}"

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(work, i) for i in range(total)]
        for _ in as_completed(futures):
            done += 1
            if on_progress:
                on_progress(done, total)
    return out


def run_multi_product(
    rows: list[dict],
    task_module,
    api_key: str | None = None,
) -> dict:
    """Run a task that consumes a SET of products and returns a single result.
    Used by Bundle Proposal."""
    client = _client(api_key)
    prompt = task_module.build_prompt(rows)
    text = _call(client, prompt)
    return task_module.parse(text)


def run_all_in_one_streaming(
    row: dict,
    on_chunk: Callable[[str, str], None],
    api_key: str | None = None,
) -> dict:
    """Stream a single all-in-one generation. on_chunk(delta, accumulated) fires
    on each text chunk so the UI can show live typing.

    Returns the parsed payload dict (or {"error": ...}).
    """
    from tasks import all_in_one as aio
    client = _client(api_key)
    try:
        prompt = aio.build_prompt(row)
        full = _stream(client, prompt, on_chunk, max_tokens=4000)
        return {"all_payloads": aio.parse_all(full)}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def run_all_in_one(
    rows: list[dict],
    api_key: str | None = None,
    workers: int = 8,
    on_progress: Callable[[int, int], None] | None = None,
    target_lang: str | None = None,
    campaign: dict | None = None,
    trending_kws: list[str] | None = None,
) -> list[dict]:
    """One Claude call per product → all 5 single-product content types.

    Returns list of dicts: {**row, "all_payloads": {task_key: payload}, "error": ...?}
    """
    from tasks import all_in_one as aio
    client = _client(api_key)
    out: list[dict] = [dict(r) for r in rows]
    total = len(rows)

    def work(i: int):
        try:
            base = aio.build_prompt(rows[i])
            base = _with_context(base, campaign=campaign, trending_kws=trending_kws)
            prompt = _with_target_lang(base, target_lang)
            text = _call(client, prompt, max_tokens=4000)
            out[i]["all_payloads"] = aio.parse_all(text)
        except Exception as e:
            out[i]["error"] = f"{type(e).__name__}: {e}"

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(work, i) for i in range(total)]
        for _ in as_completed(futures):
            done += 1
            if on_progress:
                on_progress(done, total)
    return out
