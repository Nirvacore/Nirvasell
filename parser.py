"""Smart parser for dealer pricelists. Accepts xlsx/csv with any column names —
auto-detects which column is SKU/name/price/brand/etc using keyword matching.

The user can override the mapping in the UI if auto-detect picks wrong.
"""
from __future__ import annotations
import io
import re
import pandas as pd


# Canonical fields → aliases that might appear in dealer files.
# Match is case-insensitive, substring-anywhere. Order matters — first hit wins.
FIELD_ALIASES = {
    "sku": ["sku", "รหัสสินค้า", "รหัส", "product code", "part no", "part number", "model", "item code"],
    "name": ["product name", "ชื่อสินค้า", "ชื่อ", "description", "name", "product", "รายการ"],
    "brand": ["brand", "ยี่ห้อ", "แบรนด์", "manufacturer"],
    "category": ["category", "หมวด", "หมวดหมู่", "type", "ประเภท"],
    "cost_price": ["dealer price", "cost", "ราคาดีลเลอร์", "ราคา dealer", "ราคา", "price", "unit price", "net price", "wholesale"],
    "stock": ["stock", "qty", "quantity", "คงเหลือ", "available", "จำนวน"],
    "image_url": ["image", "รูป", "photo", "picture", "image url"],
    "specs": ["spec", "specification", "สเปค", "feature", "detail", "รายละเอียด"],
}


def read_any(name: str, raw: bytes) -> pd.DataFrame:
    """Read either Excel or CSV/TSV from raw bytes. Tries multiple sheets/encodings."""
    name = name.lower()
    if name.endswith((".xlsx", ".xls", ".xlsm")):
        # Pandas reads all sheets; pick the one with the most non-null cells.
        sheets = pd.read_excel(io.BytesIO(raw), sheet_name=None, dtype=str)
        if not sheets:
            raise ValueError("Empty workbook")
        best = max(sheets.values(), key=lambda d: d.notna().sum().sum())
        return _normalize_headers(best)
    if name.endswith(".tsv"):
        return _normalize_headers(pd.read_csv(io.BytesIO(raw), sep="\t", dtype=str))
    # CSV — try utf-8 then cp874 (Thai Windows).
    for enc in ("utf-8-sig", "utf-8", "cp874"):
        try:
            return _normalize_headers(pd.read_csv(io.BytesIO(raw), dtype=str, encoding=enc))
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode CSV")


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    # Drop fully-empty columns (common in Excel exports with trailing blanks).
    df = df.dropna(axis=1, how="all")
    return df


def auto_map(columns: list[str]) -> dict[str, str | None]:
    """Return {canonical_field: original_column_name | None}."""
    out: dict[str, str | None] = {}
    used: set[str] = set()
    lowered = [(c, c.lower()) for c in columns]
    for field, aliases in FIELD_ALIASES.items():
        match = None
        for alias in aliases:
            for orig, lc in lowered:
                if orig in used:
                    continue
                if alias in lc:
                    match = orig
                    break
            if match:
                break
        out[field] = match
        if match:
            used.add(match)
    return out


def normalize(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    """Project the raw DataFrame onto canonical columns. Drops rows missing
    required fields (sku + cost_price)."""
    out = pd.DataFrame()
    for field, src in mapping.items():
        out[field] = df[src] if src and src in df.columns else None

    # Clean price: strip currency symbols, commas, whitespace.
    if "cost_price" in out:
        out["cost_price"] = (
            out["cost_price"]
            .astype(str)
            .str.replace(r"[฿$,\s]", "", regex=True)
            .str.replace(",", "")
            .pipe(pd.to_numeric, errors="coerce")
        )

    # Trim text columns.
    for col in ("sku", "name", "brand", "category", "specs"):
        if col in out:
            out[col] = out[col].astype(str).str.strip().replace({"nan": None, "None": None})

    # Required: sku + cost_price > 0
    out = out[out["sku"].notna() & out["cost_price"].notna() & (out["cost_price"] > 0)]
    out = out.reset_index(drop=True)
    return out


def markup_price(cost: float, markup_percent: float, round_to: int = 10) -> int:
    raw = cost * (1 + markup_percent / 100)
    return int(((raw + round_to - 1) // round_to) * round_to)
