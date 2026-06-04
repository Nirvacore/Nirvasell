"""Smart intake — accept anything dealer-shaped, return a normalized DataFrame.

Sources supported:
  • .xlsx / .xls / .xlsm  — pandas
  • .csv / .tsv           — pandas
  • .pdf                  — pypdf text extraction → Claude product extractor
  • raw text (paste)      → Claude product extractor
"""
from __future__ import annotations
import io
import json
import re
from typing import Any

import pandas as pd
from anthropic import Anthropic

import parser as parser_mod


def detect_format(filename: str) -> str:
    name = filename.lower()
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        return "excel"
    if name.endswith(".pdf"):
        return "pdf"
    if name.endswith((".csv", ".tsv")):
        return "csv"
    return "unknown"


def pdf_to_text(raw: bytes) -> str:
    """Extract text from a PDF. Returns one string, page-separated by \\n\\n."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    out = []
    for page in reader.pages:
        try:
            out.append(page.extract_text() or "")
        except Exception:
            out.append("")
    return "\n\n".join(out)


EXTRACT_PROMPT = """ข้อความด้านล่างมาจาก pricelist ของ dealer (อาจเป็น PDF, paste, หรือ scrape).
สกัดรายการสินค้าออกมา ส่งกลับเป็น JSON array ห้ามใส่ ``` หรือคำอธิบายเพิ่ม

ตัวอย่าง output:
[
  {{"sku":"ABC-001","name":"Zyxel GS1920","brand":"Zyxel","category":"Networking","cost_price":15200,"stock":25,"specs":"48 ports PoE"}},
  ...
]

กฎ:
- ต้องมี sku และ cost_price (เลขล้วน ตัด ฿ และ ,)
- name = ชื่อเต็มสินค้า
- brand / category / stock / specs ถ้าไม่มีให้เว้นว่าง ""
- ข้าม header / footer / หน้าว่าง / ขอบเขตที่ไม่ใช่สินค้า

ข้อความ:
{text}"""


def claude_extract(text: str, api_key: str | None = None) -> pd.DataFrame:
    """Use Claude to pull product rows out of free-form text. Returns DataFrame
    in nirva's normalized shape (same columns as parser.normalize)."""
    import os
    client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

    # If the text is very long, chunk it (~12k chars per chunk = ~3-4k tokens).
    chunks = _chunk(text, 12000)
    all_rows: list[dict] = []
    for chunk in chunks:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{"role": "user", "content": EXTRACT_PROMPT.format(text=chunk)}],
        )
        out = msg.content[0].text.strip()
        if out.startswith("```"):
            out = out.split("```")[1]
            if out.startswith("json"):
                out = out[4:]
            out = out.strip().rstrip("`")
        try:
            rows = json.loads(out)
            if isinstance(rows, list):
                all_rows.extend(rows)
        except json.JSONDecodeError:
            continue

    if not all_rows:
        return pd.DataFrame(columns=["sku", "name", "brand", "category", "cost_price", "stock", "image_url", "specs"])

    df = pd.DataFrame(all_rows)
    # Coerce types + ensure all columns exist.
    for col in ["sku", "name", "brand", "category", "stock", "specs"]:
        if col not in df:
            df[col] = ""
    if "cost_price" not in df:
        df["cost_price"] = None
    df["cost_price"] = pd.to_numeric(df["cost_price"], errors="coerce")
    if "image_url" not in df:
        df["image_url"] = None
    df = df[df["sku"].notna() & df["cost_price"].notna() & (df["cost_price"] > 0)].reset_index(drop=True)
    return df


def _chunk(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    parts = []
    for i in range(0, len(text), size):
        parts.append(text[i:i + size])
    return parts


def read_anything(filename: str, raw: bytes | None, paste_text: str = "",
                  api_key: str | None = None) -> tuple[pd.DataFrame, str]:
    """Universal entry: returns (DataFrame, source-description)."""
    if paste_text and not raw:
        df = claude_extract(paste_text, api_key=api_key)
        return df, "pasted text"

    fmt = detect_format(filename)
    if fmt == "excel":
        raw_df = parser_mod.read_any(filename, raw)
        return raw_df, f"Excel ({filename})"
    if fmt == "csv":
        raw_df = parser_mod.read_any(filename, raw)
        return raw_df, f"CSV ({filename})"
    if fmt == "pdf":
        text = pdf_to_text(raw)
        if not text.strip():
            raise ValueError("PDF มีแต่รูป — ไม่มี text. ลองคัดลอกข้อความวางในช่อง paste แทน")
        df = claude_extract(text, api_key=api_key)
        return df, f"PDF ({filename})"
    raise ValueError(f"ไม่รู้จักไฟล์: {filename}")
