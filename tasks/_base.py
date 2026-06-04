"""Shared helpers for task plugins."""
from __future__ import annotations
import json


def strip_codefence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3]
    return text


def parse_json(text: str) -> dict:
    return json.loads(strip_codefence(text))


def common_context(row: dict) -> str:
    """Format the product info block used by most prompts."""
    return (
        f"- ชื่อ: {row.get('name') or row.get('sku')}\n"
        f"- แบรนด์: {row.get('brand') or '—'}\n"
        f"- หมวด: {row.get('category') or '—'}\n"
        f"- ราคา: {int(row.get('sell_price') or row.get('cost_price') or 0):,} บาท\n"
        f"- สเปค: {(row.get('specs') or '')[:1200]}"
    )
