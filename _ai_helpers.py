"""AI text transformations — small Claude calls that let users polish any
text in-place. Powers the Notion-style "/" chip row that appears above
text inputs.

Each helper is a single-call transformation with a tight prompt — no JSON
parsing, no caching needed (these are rare interactive actions, not bulk
operations). Returns the transformed string (or original on error).
"""
from __future__ import annotations
import os


_MODEL = "claude-haiku-4-5-20251001"


def _call(prompt: str, api_key: str | None = None,
          max_tokens: int = 1500) -> str:
    """Single Claude call returning a plain string."""
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("API key missing")
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    out = msg.content[0].text.strip()
    # Strip wrapping quotes if Claude added them
    if (out.startswith(('"', "'")) and out.endswith(('"', "'"))
            and len(out) > 1):
        out = out[1:-1]
    return out


# ---- Transformations ---------------------------------------------------

def improve(text: str, api_key: str | None = None) -> str:
    """Rewrite for clarity, flow, and punch. Keep meaning + language."""
    return _call(
        "Rewrite the text below for clarity and impact. Keep the SAME "
        "language, same length (±10%), same meaning. Don't add new claims. "
        "Return ONLY the rewritten text, no commentary.\n\n"
        f"Text:\n{text}",
        api_key=api_key,
    )


def shorten(text: str, max_chars: int = 60,
            api_key: str | None = None) -> str:
    """Compress to fit ≤ max_chars (Shopee title limit etc)."""
    return _call(
        f"Shorten the text below to no more than {max_chars} characters. "
        f"Keep the same language. Preserve the most important keywords for "
        f"marketplace search. Return ONLY the shortened text, no commentary.\n\n"
        f"Text:\n{text}",
        api_key=api_key,
    )


def add_emojis(text: str, api_key: str | None = None) -> str:
    """Add 1-2 relevant emojis. Don't go overboard."""
    return _call(
        "Add 1-2 relevant emojis to the text below to make it more engaging. "
        "Place them at natural points (start, end, or after a verb). Don't "
        "add more than 2. Keep the same language. Return ONLY the text with "
        "emojis, no commentary.\n\n"
        f"Text:\n{text}",
        api_key=api_key,
    )


def to_casual(text: str, api_key: str | None = None) -> str:
    """Make it sound friendlier / more conversational. Keep language."""
    return _call(
        "Rewrite the text below in a friendlier, more casual tone — like "
        "you're chatting with a friend. Keep the SAME language and same "
        "meaning. Return ONLY the rewritten text, no commentary.\n\n"
        f"Text:\n{text}",
        api_key=api_key,
    )


def to_professional(text: str, api_key: str | None = None) -> str:
    """Make it more formal / B2B-appropriate. Keep language."""
    return _call(
        "Rewrite the text below in a more professional, polished tone "
        "suitable for B2B / corporate communication. Keep the SAME language "
        "and same meaning. Return ONLY the rewritten text, no commentary.\n\n"
        f"Text:\n{text}",
        api_key=api_key,
    )


def translate_to(text: str, target_lang: str,
                 api_key: str | None = None) -> str:
    """Translate to target language. Keep tone + structure."""
    from translate import LANG_NAMES
    lang_name = LANG_NAMES.get(target_lang, target_lang)
    return _call(
        f"Translate the text below into {lang_name}. Preserve tone, formatting, "
        f"and any product/brand names. Return ONLY the translation, no "
        f"commentary or quotes.\n\n"
        f"Text:\n{text}",
        api_key=api_key,
    )


# ---- Registry for the UI chip row --------------------------------------

HELPERS = {
    "improve":      {"icon": "✨", "fn": improve,        "label_key": "ai_help.improve"},
    "shorten":      {"icon": "✂",  "fn": shorten,        "label_key": "ai_help.shorten"},
    "emojis":       {"icon": "🎉", "fn": add_emojis,     "label_key": "ai_help.emojis"},
    "casual":       {"icon": "😊", "fn": to_casual,      "label_key": "ai_help.casual"},
    "professional": {"icon": "👔", "fn": to_professional,"label_key": "ai_help.professional"},
}


def apply(helper_key: str, text: str, api_key: str,
          **kwargs) -> tuple[bool, str]:
    """Run a helper by name. Returns (ok, new_text-or-error-message)."""
    helper = HELPERS.get(helper_key)
    if not helper:
        return False, f"unknown helper: {helper_key}"
    fn = helper["fn"]
    try:
        out = fn(text, api_key=api_key, **kwargs)
        return True, out
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
