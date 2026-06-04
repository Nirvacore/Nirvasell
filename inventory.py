"""Inventory + overselling protection — the #1 pain Thai resellers complain
about ("ขายเกินสต็อก ถูกหักคะแนนร้าน").

Two problems we solve here:

1. **Stock is stored as free-text** in products.stock (e.g. "5 ชิ้น",
   "in stock", "3 left"). Raw int() blows up. We parse the leading integer
   so exporters can write a clean number, and recognize sentinel phrases
   ("out of stock" / "sold out" / "หมด") as zero.

2. **Pre-flight before export** — surface a summary so the seller sees
   "3 SKUs are out of stock" BEFORE pushing to Shopee/Lazada. Optionally
   exclude OOS items entirely from the CSV.

Used by every exporter + the History/Listing download flow."""
from __future__ import annotations
import re
from typing import Iterable

import pandas as pd


# Sentinel phrases that mean "zero stock" even when no number is present.
# Keep them lowercase for case-insensitive matching.
_OOS_PHRASES = (
    "out of stock", "sold out", "no stock", "unavailable",
    "หมด", "ของหมด", "สินค้าหมด", "ยังไม่มีของ",
    "无库存", "缺货", "売り切れ", "在庫切れ",
    "품절", "재고없음", "hết hàng", "habis",
)

# Default fallback stock when the value is missing entirely (not OOS — just
# unknown). 0 is too conservative (rejects every untagged product); 100 is
# too aggressive. We pick a sane middle and surface it as "assumed".
_FALLBACK_STOCK = 99


def parse_stock(value) -> int:
    """Extract integer stock from free-text. Examples:
       "5 ชิ้น"   → 5
       "0"         → 0
       "หมด"       → 0
       "In stock"  → 99 (assumed)
       None / ""   → 99 (assumed)
       "100+"      → 100
    """
    if value is None:
        return _FALLBACK_STOCK
    s = str(value).strip().lower()
    if not s:
        return _FALLBACK_STOCK
    # Sentinel OOS phrases first
    if any(p in s for p in _OOS_PHRASES):
        return 0
    # First run of digits
    m = re.search(r"\d+", s)
    if m:
        try:
            return max(0, int(m.group(0)))
        except ValueError:
            return _FALLBACK_STOCK
    # Non-empty but no number and no OOS phrase — assume in stock
    return _FALLBACK_STOCK


def is_in_stock(value, low_threshold: int = 0) -> bool:
    """True if stock is strictly above the low threshold."""
    return parse_stock(value) > low_threshold


def is_assumed(value) -> bool:
    """True if we fell back to the default — i.e. the seller never set stock.
    Useful for surfacing "did you mean to leave this blank?" warnings."""
    if value is None:
        return True
    s = str(value).strip()
    return not s or (not any(c.isdigit() for c in s) and
                     not any(p in s.lower() for p in _OOS_PHRASES))


# ---- Audit / pre-flight summary -----------------------------------------

def audit(df: pd.DataFrame, low_threshold: int = 5) -> dict:
    """Bucket products by stock state. Returns a dict the UI can render."""
    if df.empty or "stock" not in df.columns:
        return {"total": len(df), "ok": len(df), "low": 0, "out": 0, "assumed": 0,
                "out_skus": [], "low_skus": [], "ok_skus": list(df.get("sku", []))}
    ok, low, out, assumed = [], [], [], []
    for _, r in df.iterrows():
        s = r.get("stock")
        n = parse_stock(s)
        sku = r.get("sku", "?")
        if is_assumed(s):
            assumed.append(sku)
        if n == 0:
            out.append(sku)
        elif n <= low_threshold:
            low.append(sku)
        else:
            ok.append(sku)
    return {
        "total":    len(df),
        "ok":       len(ok),
        "low":      len(low),
        "out":      len(out),
        "assumed":  len(assumed),
        "out_skus": out,
        "low_skus": low,
        "ok_skus":  ok,
    }


def filter_in_stock(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows whose stock parses to 0. Useful for "exclude OOS" toggle."""
    if df.empty or "stock" not in df.columns:
        return df
    mask = df["stock"].apply(lambda s: parse_stock(s) > 0)
    return df[mask].copy()


def normalize_stock_column(df: pd.DataFrame) -> pd.DataFrame:
    """Replace the free-text stock column with parsed integers in-place.
    Exporters call this before writing CSVs so they don't need to know the
    parsing rules — they just trust `row["stock"]` is an int."""
    if df.empty or "stock" not in df.columns:
        return df
    out = df.copy()
    out["stock"] = out["stock"].apply(parse_stock)
    return out


def decrement(value, n: int = 1) -> str:
    """Manually decrement a stock value by `n`. Returns a string in the same
    shape as the input (preserving "ชิ้น" suffix etc.). Used after a fulfilled
    order or sourcing adjustment."""
    if value is None:
        return str(max(0, _FALLBACK_STOCK - n))
    s = str(value)
    m = re.search(r"\d+", s)
    if not m:
        return s
    new = max(0, int(m.group(0)) - int(n or 1))
    return re.sub(r"\d+", str(new), s, count=1)
