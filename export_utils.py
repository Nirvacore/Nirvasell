"""Format generated content as Markdown / plain-text / Notion-ready blocks."""
from __future__ import annotations
import json
from typing import Iterable


def listing_to_markdown(payload: dict, sku: str = "", sell_price: int = 0) -> str:
    parts: list[str] = []
    if sku:
        parts.append(f"`{sku}`")
    title = payload.get("title") or ""
    if title:
        parts.append(f"# {title}")
    if sell_price:
        parts.append(f"**฿{sell_price:,}**")
    desc = payload.get("description") or ""
    if desc:
        parts.append(desc)
    tags = payload.get("tags") or ""
    if tags:
        parts.append("**Tags:** " + " ".join(f"`{t.strip()}`" for t in tags.split(",") if t.strip()))
    return "\n\n".join(parts)


def line_to_markdown(payload: dict) -> str:
    hook = payload.get("hook", "")
    msg = payload.get("message", "")
    cta = payload.get("cta", "")
    parts: list[str] = []
    if hook:
        parts.append(f"## {hook}")
    if msg:
        parts.append(msg)
    if cta:
        parts.append(f"**▶ {cta}**")
    return "\n\n".join(parts)


def fb_to_markdown(payload: dict) -> str:
    post = payload.get("post", "")
    tags = payload.get("hashtags", "")
    out = post.strip()
    if tags:
        out += "\n\n" + tags
    return out


def tiktok_to_markdown(payload: dict) -> str:
    hook = payload.get("hook", "")
    script = payload.get("script", "")
    tags = payload.get("hashtags", "")
    out = []
    if hook:
        out.append(f"**Hook:** {hook}")
    if script:
        out.append("```\n" + script + "\n```")
    if tags:
        out.append(tags)
    return "\n\n".join(out)


def email_to_markdown(payload: dict) -> str:
    subj = payload.get("subject", "")
    pre = payload.get("preheader", "")
    body = payload.get("body_text", "")
    out = []
    if subj:
        out.append(f"**Subject:** {subj}")
    if pre:
        out.append(f"_{pre}_")
    if body:
        out.append(body)
    return "\n\n".join(out)


def qa_to_markdown(payload: dict) -> str:
    return payload.get("qa_text", "")


def promo_to_markdown(payload: dict) -> str:
    headline = payload.get("headline", "")
    body = payload.get("body", "")
    pct = payload.get("discount_pct", "")
    price = payload.get("promo_price", "")
    cta = payload.get("cta", "")
    countdown = payload.get("countdown_line", "")
    out = []
    if headline:
        out.append(f"## {headline}")
    if body:
        out.append(body)
    if price:
        out.append(f"**~~ปกติ~~ ฿{price}** · ลด {pct}%")
    if countdown:
        out.append(f"⏰ {countdown}")
    if cta:
        out.append(f"**▶ {cta}**")
    return "\n\n".join(out)


def bundle_to_markdown(payload: dict) -> str:
    name = payload.get("bundle_name", "")
    pitch = payload.get("pitch", "")
    pct = payload.get("suggested_discount_pct", "")
    price = payload.get("bundle_price", "")
    out = []
    if name:
        out.append(f"# {name}")
    if pitch:
        out.append(pitch)
    if price:
        out.append(f"**฿{price}** · ลด {pct}%")
    return "\n\n".join(out)


TASK_FORMATTERS = {
    "listing":        listing_to_markdown,
    "line_post":      line_to_markdown,
    "fb_post":        fb_to_markdown,
    "tiktok_script":  tiktok_to_markdown,
    "email_blast":    email_to_markdown,
    "customer_qa":    qa_to_markdown,
    "promotion":      promo_to_markdown,
    "bundle":         bundle_to_markdown,
}


def to_markdown(task_key: str, payload: dict, sku: str = "", sell_price: int = 0) -> str:
    fn = TASK_FORMATTERS.get(task_key)
    if not fn:
        return json.dumps(payload, indent=2, ensure_ascii=False)
    if task_key == "listing":
        return listing_to_markdown(payload, sku=sku, sell_price=sell_price)
    return fn(payload)


def product_to_full_markdown(product: dict, contents: dict[str, dict]) -> str:
    """All content for one product in a single Markdown doc — ready for Notion paste."""
    sku = product.get("sku") or ""
    name = product.get("name") or sku
    sell = int(product.get("sell_price") or 0)
    cost = int(product.get("cost_price") or 0)

    parts: list[str] = [f"# {name}", f"`{sku}` · ฿{sell:,} (cost ฿{cost:,})"]
    icons = {
        "listing": "🛒", "line_post": "💚", "fb_post": "📘",
        "tiktok_script": "🎵", "email_blast": "✉️",
        "customer_qa": "💬", "promotion": "🔥", "bundle": "📦",
    }
    for task_key, payload in contents.items():
        if not payload:
            continue
        icon = icons.get(task_key, "•")
        parts.append(f"\n---\n\n## {icon} {task_key.replace('_', ' ').title()}\n")
        parts.append(to_markdown(task_key, payload, sku=sku, sell_price=sell))
    return "\n".join(parts)
