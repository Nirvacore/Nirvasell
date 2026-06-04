"""User-defined AI tasks. Each task is a per-user record in SQLite that
exposes the same interface as built-in tasks/*.py modules.

Stored fields:
  • key            unique per user (e.g. "reorder_email")
  • label          display name
  • icon           emoji
  • blurb          one-line description
  • prompt         template — placeholders {ctx} (filled with product info)
                    plus {name}, {brand}, {category}, {price}, {specs} if used directly
  • output_fields  comma-separated list (becomes the JSON keys we extract)
  • format_hint    optional extra JSON shape guidance to bolt onto the prompt

The CustomTask wrapper class quacks like built-in tasks (TASK dict +
build_prompt + parse) so generate.py treats it identically."""
from __future__ import annotations
import json
import re
from typing import Any

import db
from tasks._base import common_context, parse_json


SCHEMA = """
CREATE TABLE IF NOT EXISTS custom_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    icon TEXT DEFAULT '✨',
    blurb TEXT,
    prompt TEXT,
    output_fields TEXT,       -- comma-separated
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def init():
    with db.conn() as c:
        c.executescript(SCHEMA)


# ---- CRUD ---------------------------------------------------------------

def list_custom() -> list[dict]:
    init()
    with db.conn() as c:
        rows = c.execute(
            "SELECT * FROM custom_tasks ORDER BY label"
        ).fetchall()
    return [dict(r) for r in rows]


def get(key: str) -> dict | None:
    init()
    with db.conn() as c:
        row = c.execute("SELECT * FROM custom_tasks WHERE key = ?", (key,)).fetchone()
    return dict(row) if row else None


def save(*, key: str, label: str, icon: str, blurb: str,
         prompt: str, output_fields: list[str]) -> tuple[bool, str]:
    init()
    key = (key or "").strip().lower()
    # Validate key
    if not re.match(r"^[a-z][a-z0-9_]*$", key):
        return False, "key ต้องเป็นตัวอักษรเล็ก/ตัวเลข/_ และเริ่มด้วยตัวอักษร"
    if not label.strip():
        return False, "label ห้ามว่าง"
    if not prompt.strip():
        return False, "prompt ห้ามว่าง"
    if not output_fields:
        return False, "output_fields ต้องมีอย่างน้อย 1 ฟิลด์"

    fields_csv = ",".join(f.strip() for f in output_fields if f.strip())
    with db.conn() as c:
        c.execute(
            """
            INSERT INTO custom_tasks (key, label, icon, blurb, prompt, output_fields)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
              label=excluded.label,
              icon=excluded.icon,
              blurb=excluded.blurb,
              prompt=excluded.prompt,
              output_fields=excluded.output_fields,
              updated_at=CURRENT_TIMESTAMP
            """,
            (key, label.strip(), (icon or "✨").strip(), (blurb or "").strip(),
             prompt.strip(), fields_csv),
        )
    return True, "saved"


def delete(key: str) -> bool:
    init()
    with db.conn() as c:
        cur = c.execute("DELETE FROM custom_tasks WHERE key = ?", (key,))
    return cur.rowcount > 0


# ---- Wrapper that quacks like a built-in task module -------------------

class CustomTask:
    """Lightweight object exposing TASK dict + build_prompt + parse, matching
    the built-in task plugin interface so generate.py can run it unchanged."""

    def __init__(self, row: dict):
        self.row = row
        fields = [f.strip() for f in (row.get("output_fields") or "").split(",") if f.strip()]
        self.TASK = {
            "key":           row["key"],
            "label":         row["label"],
            "icon":          row.get("icon") or "✨",
            "blurb":         row.get("blurb") or "",
            "output_fields": fields,
            "custom":        True,
        }

    def build_prompt(self, p: dict) -> str:
        # Substitute well-known fields into the template
        prompt = self.row.get("prompt") or ""
        ctx = common_context(p)
        try:
            text = prompt.format(
                ctx=ctx,
                name=p.get("name") or "",
                brand=p.get("brand") or "",
                category=p.get("category") or "",
                price=int(p.get("sell_price") or p.get("cost_price") or 0),
                specs=(p.get("specs") or "")[:1200],
            )
        except (KeyError, ValueError):
            # Template has unknown placeholder — pass through as-is + append ctx
            text = prompt + "\n\nProduct context:\n" + ctx

        # Append output-shape instructions if not already there
        fields = self.TASK["output_fields"]
        if "JSON" not in text.upper() and fields:
            shape = "{\n" + ",\n".join(f'  "{f}": "..."' for f in fields) + "\n}"
            text += (
                f"\n\nReturn ONLY a JSON object with these keys, no ``` or commentary:\n{shape}"
            )
        return text

    def parse(self, text: str) -> dict:
        fields = self.TASK["output_fields"]
        try:
            data = parse_json(text)
            if isinstance(data, dict):
                return {f: data.get(f, "") for f in fields}
        except Exception:
            pass
        # Fallback: put everything in the first field
        if fields:
            return {fields[0]: text.strip()}
        return {}


def load_for_current_user() -> dict[str, CustomTask]:
    """Return {key: CustomTask} for all custom tasks of the active user."""
    try:
        return {row["key"]: CustomTask(row) for row in list_custom()}
    except Exception:
        return {}
