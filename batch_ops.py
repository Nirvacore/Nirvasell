"""Batch operations — update stock/price for many SKUs at once.

Thai resellers get stock updates from distributors (Synnex, VSTECS) and
need to update 50+ SKUs in one go. This module handles CSV-based batch
updates and bulk price adjustments."""
from __future__ import annotations

import csv
import io

import db


def parse_batch_csv(raw: bytes, filename: str = "") -> list[dict]:
    """Parse a CSV with columns: sku, stock, cost_price, sell_price.
    Any column except sku is optional — only present fields get updated."""
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for r in reader:
        sku = (r.get("sku") or r.get("SKU") or r.get("รหัสสินค้า") or "").strip()
        if not sku:
            continue
        item = {"sku": sku}
        for key, aliases in [
            ("stock", ["stock", "qty", "จำนวน", "สต็อก"]),
            ("cost_price", ["cost_price", "cost", "ต้นทุน", "ราคาทุน"]),
            ("sell_price", ["sell_price", "price", "ราคาขาย"]),
        ]:
            for a in aliases:
                val = r.get(a)
                if val is not None and val.strip():
                    try:
                        item[key] = float(val.strip().replace(",", ""))
                    except ValueError:
                        pass
                    break
        rows.append(item)
    return rows


def apply_batch_update(rows: list[dict]) -> dict:
    """Apply parsed batch to products table.
    Returns {updated: n, not_found: [skus], skipped: n}."""
    updated = 0
    not_found = []
    skipped = 0

    with db.conn() as c:
        for r in rows:
            sku = r["sku"]
            existing = c.execute(
                "SELECT id FROM products WHERE sku = ?", (sku,)
            ).fetchone()
            if not existing:
                not_found.append(sku)
                continue

            sets = []
            vals = []
            for col in ["stock", "cost_price", "sell_price"]:
                if col in r:
                    sets.append(f"{col} = ?")
                    vals.append(r[col])
            if not sets:
                skipped += 1
                continue

            vals.append(existing["id"])
            c.execute(
                "UPDATE products SET " + ", ".join(sets) + " WHERE id = ?",
                vals,
            )
            updated += 1

    return {"updated": updated, "not_found": not_found, "skipped": skipped}


def bulk_price_adjust(percent: float, skus: list[str] | None = None) -> int:
    """Adjust sell_price by a percentage. +10 = raise 10%, -5 = drop 5%.
    If skus is None, applies to all products."""
    multiplier = 1 + percent / 100
    with db.conn() as c:
        if skus:
            placeholders = ",".join("?" * len(skus))
            c.execute(
                f"UPDATE products SET sell_price = ROUND(sell_price * ?, 0) "
                f"WHERE sku IN ({placeholders})",
                [multiplier] + skus,
            )
            return c.execute("SELECT changes()").fetchone()[0]
        else:
            c.execute(
                "UPDATE products SET sell_price = ROUND(sell_price * ?, 0) "
                "WHERE sell_price > 0",
                (multiplier,),
            )
            return c.execute("SELECT changes()").fetchone()[0]


def bulk_stock_set(value: int, skus: list[str] | None = None) -> int:
    """Set stock to a fixed value for selected or all products."""
    with db.conn() as c:
        if skus:
            placeholders = ",".join("?" * len(skus))
            c.execute(
                f"UPDATE products SET stock = ? WHERE sku IN ({placeholders})",
                [value] + skus,
            )
        else:
            c.execute("UPDATE products SET stock = ?", (value,))
        return c.execute("SELECT changes()").fetchone()[0]
