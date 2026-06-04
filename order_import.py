"""Multi-marketplace order CSV importer.

Each marketplace exports orders in a different shape. We auto-detect the
shape by looking at column names, then map to our canonical order schema.

Canonical fields: order_id, sku, qty, unit_price, total_price, currency,
                  order_date, status, platform"""
from __future__ import annotations
import io
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

import db


# Per-marketplace column aliases (lowercase substring match)
SCHEMAS: dict[str, dict[str, list[str]]] = {
    "shopee": {
        "order_id":    ["order id", "หมายเลขคำสั่งซื้อ", "เลขที่คำสั่งซื้อ"],
        "sku":         ["sku", "รหัส sku", "parent sku"],
        "qty":         ["quantity", "จำนวน", "qty"],
        "unit_price":  ["original price", "ราคาสินค้า"],
        "total_price": ["total amount", "ยอดรวม", "subtotal"],
        "order_date":  ["order creation date", "วันที่สั่งซื้อ", "create time"],
        "status":      ["order status", "สถานะ"],
    },
    "lazada": {
        "order_id":    ["orderitemid", "order number", "เลขออเดอร์", "order id"],
        "sku":         ["sellersku", "seller sku", "sku"],
        "qty":         ["quantity"],
        "unit_price":  ["paid price", "unit price"],
        "total_price": ["paid price", "order total", "total"],
        "order_date":  ["created at", "create time", "order date"],
        "status":      ["status", "order status"],
    },
    "tiktok": {
        "order_id":    ["order id", "order number"],
        "sku":         ["sku id", "seller sku", "sku"],
        "qty":         ["quantity"],
        "unit_price":  ["sku unit original price", "price"],
        "total_price": ["order amount", "sub total"],
        "order_date":  ["created time", "order created time"],
        "status":      ["order status"],
    },
    "shopify": {
        "order_id":    ["name", "order id"],
        "sku":         ["lineitem sku", "sku"],
        "qty":         ["lineitem quantity", "quantity"],
        "unit_price":  ["lineitem price"],
        "total_price": ["total", "subtotal"],
        "order_date":  ["created at", "processed at"],
        "status":      ["financial status", "fulfillment status"],
    },
    "amazon": {
        "order_id":    ["amazon-order-id", "order-id"],
        "sku":         ["sku"],
        "qty":         ["quantity-purchased", "quantity"],
        "unit_price":  ["item-price"],
        "total_price": ["item-price"],
        "order_date":  ["purchase-date"],
        "status":      ["order-status"],
    },
}


def _norm(s: str) -> str:
    return str(s).strip().lower()


def detect_platform(columns: list[str]) -> str | None:
    """Guess which marketplace this CSV is from based on column names."""
    cols_l = [_norm(c) for c in columns]
    best, best_score = None, 0
    for platform, alias_map in SCHEMAS.items():
        score = 0
        for canonical, aliases in alias_map.items():
            for alias in aliases:
                if any(alias in c for c in cols_l):
                    score += 1
                    break
        if score > best_score:
            best, best_score = platform, score
    return best if best_score >= 3 else None


def map_columns(columns: list[str], platform: str) -> dict[str, str | None]:
    """Return {canonical: actual_column_name | None}."""
    cols_l = [(c, _norm(c)) for c in columns]
    alias_map = SCHEMAS.get(platform, {})
    out: dict[str, str | None] = {}
    for canonical, aliases in alias_map.items():
        match = None
        for alias in aliases:
            for orig, lc in cols_l:
                if alias in lc:
                    match = orig
                    break
            if match:
                break
        out[canonical] = match
    return out


def read_orders_csv(raw: bytes, filename: str = "") -> pd.DataFrame:
    """Read any marketplace order export. Tries multiple encodings."""
    for enc in ("utf-8-sig", "utf-8", "cp874"):
        try:
            if filename.endswith((".xlsx", ".xls")):
                return pd.read_excel(io.BytesIO(raw), dtype=str)
            return pd.read_csv(io.BytesIO(raw), dtype=str, encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception:
            try:
                return pd.read_csv(io.BytesIO(raw), dtype=str, sep="\t", encoding=enc)
            except Exception:
                continue
    raise ValueError("Could not parse order CSV")


def normalize(df: pd.DataFrame, platform: str,
              mapping: dict[str, str | None] | None = None) -> pd.DataFrame:
    """Project the raw DataFrame onto canonical fields."""
    mapping = mapping or map_columns(list(df.columns), platform)
    out = pd.DataFrame()
    for canonical, src in mapping.items():
        out[canonical] = df[src] if src and src in df.columns else None

    # Clean numeric fields
    for col in ("qty", "unit_price", "total_price"):
        if col in out.columns:
            out[col] = (
                out[col].astype(str)
                .str.replace(r"[฿$,\s]", "", regex=True)
                .pipe(pd.to_numeric, errors="coerce")
            )

    # Parse date — best-effort
    if "order_date" in out.columns:
        out["order_date"] = pd.to_datetime(out["order_date"], errors="coerce")

    out["platform"] = platform
    out["currency"] = "THB" if platform in ("shopee", "lazada", "tiktok") else "USD"

    # Required: order_id + sku
    out = out[out["order_id"].notna() & out["sku"].notna()].reset_index(drop=True)
    return out


def save_orders(df: pd.DataFrame) -> int:
    """Insert normalized orders into DB. Idempotent via UNIQUE constraint."""
    if df.empty:
        return 0

    # Map sku → product_id where it exists
    with db.conn() as c:
        sku_to_id = {
            r["sku"]: r["id"]
            for r in c.execute("SELECT id, sku FROM products").fetchall()
        }

    n_inserted = 0
    with db.conn() as c:
        for _, r in df.iterrows():
            product_id = sku_to_id.get(r["sku"])
            try:
                qty = int(r.get("qty") or 1)
            except (TypeError, ValueError):
                qty = 1
            try:
                unit = float(r.get("unit_price") or 0)
            except (TypeError, ValueError):
                unit = 0
            try:
                total = float(r.get("total_price") or unit * qty)
            except (TypeError, ValueError):
                total = unit * qty

            date_val = r.get("order_date")
            order_date = ""
            if pd.notna(date_val):
                try:
                    order_date = pd.Timestamp(date_val).isoformat()
                except Exception:
                    order_date = str(date_val)

            try:
                # Track total_changes before/after to know if this row was new
                before = c.total_changes
                c.execute(
                    """
                    INSERT OR IGNORE INTO orders
                    (order_id, sku, product_id, platform, qty, unit_price, total_price,
                     currency, order_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(r["order_id"]), str(r["sku"]), product_id,
                        r["platform"], qty, unit, total,
                        r.get("currency", "THB"),
                        order_date,
                        str(r.get("status") or "paid"),
                    ),
                )
                if c.total_changes > before:
                    n_inserted += 1
                    # Decrement stock on the matched product (only on NEW
                    # rows, so re-importing the same CSV doesn't double-deduct).
                    if product_id:
                        _decrement_stock(c, product_id, qty)
            except Exception:
                continue

    # v50: Emit a single event for the batch — not one per order (would spam)
    if n_inserted:
        try:
            import events
            events.log(
                category="order",
                severity="success",
                title=f"📦 {n_inserted} ออเดอร์ใหม่",
                body=f"Import เรียบร้อย · stock ลดอัตโนมัติแล้ว",
                target_page="pages/F_📈_Dashboard.py",
                meta={"n_inserted": n_inserted},
            )
        except Exception:
            pass

    return n_inserted


def _decrement_stock(c, product_id: int, qty: int) -> None:
    """Best-effort stock decrement. products.stock is a free-text label like
    '12 ชิ้น' or 'In stock' — we strip out the first integer, subtract qty,
    and write it back. Non-numeric stock is left alone."""
    import re
    row = c.execute("SELECT stock FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row or not row["stock"]:
        return
    s = str(row["stock"])
    m = re.search(r"\d+", s)
    if not m:
        return
    new_n = max(0, int(m.group(0)) - int(qty or 1))
    new_stock = re.sub(r"\d+", str(new_n), s, count=1)
    c.execute("UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id))
