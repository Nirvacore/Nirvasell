"""Multi-supplier sourcing — cluster "same product, different suppliers" and
pick the best offer at order time.

How matching works:
  • Auto-group by (normalized brand) + (model_code regex)
  • model_code = an alphanumeric token in the product name with at least 1
    digit and 1 letter, e.g. "RV340", "GS1920-48HPV2", "EAP245", "T5-1TB"
  • Manually link / unlink via Sourcing page

How "best offer" works:
  • Default: lowest cost_price (cheapest wins)
  • Or: highest stock if you need it now
  • Or: weighted (price 60% + stock 40%)
"""
from __future__ import annotations
import re
import sqlite3
from typing import Iterable

import pandas as pd

import db


# ---- Normalization helpers -----------------------------------------------

def _norm(s: str | None) -> str:
    return (s or "").strip().lower()


# Model-code candidate: 3+ chars, mixed letters and digits, optional dashes
MODEL_RX = re.compile(r"\b([A-Z0-9][A-Z0-9\-/]{2,}[A-Z0-9])\b", re.I)


def extract_model_code(name: str) -> str:
    """Find the most-specific-looking model code in a product name.
    Returns "" if nothing useful found."""
    if not name:
        return ""
    candidates = MODEL_RX.findall(name.upper())
    if not candidates:
        return ""
    # Prefer tokens with both letters AND digits.
    scored = [
        (c, sum(c.lower() != c for c in c) + sum(ch.isdigit() for ch in c))
        for c in candidates
    ]
    # Filter out tokens that are all letters or all digits.
    mixed = [c for c, _ in scored if any(ch.isdigit() for ch in c) and any(ch.isalpha() for ch in c)]
    if not mixed:
        return ""
    # Longest wins (usually most specific, e.g. "GS1920-48HPV2" over "GS1920").
    return max(mixed, key=len)


def match_key(brand: str | None, name: str | None) -> str:
    brand_n = _norm(brand)
    model = extract_model_code(name or "")
    if not model:
        return ""
    return f"{brand_n}|{model.lower()}"


# ---- Group management ----------------------------------------------------

def get_or_create_group(c: sqlite3.Connection, brand: str | None, name: str | None) -> int | None:
    """Return group_id for this brand+name pair. Creates the group if missing.
    Returns None if we can't extract a model code (un-groupable)."""
    key = match_key(brand, name)
    if not key:
        return None

    row = c.execute("SELECT id FROM product_groups WHERE match_key = ?", (key,)).fetchone()
    if row:
        return row["id"]

    model = extract_model_code(name or "")
    canonical = f"{(brand or '').strip()} {model}".strip()
    c.execute(
        "INSERT INTO product_groups (canonical_name, brand, model_code, match_key) "
        "VALUES (?, ?, ?, ?)",
        (canonical, (brand or "").strip(), model, key),
    )
    return c.execute("SELECT last_insert_rowid()").fetchone()[0]


def auto_group_all() -> dict:
    """Run match-and-link across every product. Idempotent.

    Returns stats: {linked, ungroupable, groups_created}."""
    linked = 0
    ungrp = 0
    created_before = None
    with db.conn() as c:
        before = c.execute("SELECT COUNT(*) FROM product_groups").fetchone()[0]
        products = c.execute("SELECT id, brand, name, group_id FROM products").fetchall()
        for p in products:
            gid = get_or_create_group(c, p["brand"], p["name"])
            if gid is None:
                ungrp += 1
                continue
            if p["group_id"] != gid:
                c.execute("UPDATE products SET group_id = ? WHERE id = ?", (gid, p["id"]))
            linked += 1
        after = c.execute("SELECT COUNT(*) FROM product_groups").fetchone()[0]
    return {"linked": linked, "ungroupable": ungrp, "groups_created": after - before, "total_groups": after}


# ---- Query offers --------------------------------------------------------

def offers_for_group(group_id: int) -> pd.DataFrame:
    """Every supplier offer for one group, with derived 'supplier' col."""
    with db.conn() as c:
        rows = c.execute(
            """
            SELECT id, sku, name, brand, category, cost_price, sell_price,
                   stock, image_url, specs, created_at
            FROM products
            WHERE group_id = ?
            ORDER BY cost_price ASC
            """,
            (group_id,),
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if not df.empty:
        # Bridge_reseller prefixes SKU with source: "SYNNEX-..." / "SOLAR-..."
        df["supplier"] = df["sku"].astype(str).str.split("-", n=1).str[0]
        # Friendly display name via supplier registry (falls back gracefully)
        try:
            from suppliers import display as _sup_display
            df["supplier_name"] = df["supplier"].str.lower().map(_sup_display)
        except Exception:
            df["supplier_name"] = df["supplier"]
    return df


def best_offer(group_id: int, criterion: str = "price",
               in_stock_only: bool = False) -> dict | None:
    """Return the winning offer dict. criterion in {price, stock, weighted}."""
    df = offers_for_group(group_id)
    if df.empty:
        return None

    if in_stock_only and "stock" in df.columns:
        in_stock = df[df["stock"].notna() & (df["stock"].astype(str).str.contains(r"\d", na=False))]
        if not in_stock.empty:
            df = in_stock

    if criterion == "price":
        winner = df.nsmallest(1, "cost_price").iloc[0]
    elif criterion == "stock":
        # Try numeric stock; rows with parseable stock win.
        df["stock_num"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0)
        winner = df.nlargest(1, "stock_num").iloc[0]
    else:  # weighted: cheapest with reasonable stock
        df["stock_num"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0)
        price_min = df["cost_price"].min()
        price_max = df["cost_price"].max() or price_min
        # Lower price is better → invert
        df["price_score"] = 1 - ((df["cost_price"] - price_min) / max(price_max - price_min, 1))
        stock_max = df["stock_num"].max() or 1
        df["stock_score"] = df["stock_num"] / stock_max
        df["total"] = df["price_score"] * 0.6 + df["stock_score"] * 0.4
        winner = df.nlargest(1, "total").iloc[0]

    return winner.to_dict()


# ---- Group browsing helpers ----------------------------------------------

def list_groups(min_offers: int = 1) -> pd.DataFrame:
    """All groups with offer count, cheapest offer, savings vs. most expensive."""
    with db.conn() as c:
        rows = c.execute(
            """
            SELECT g.id, g.canonical_name, g.brand, g.model_code,
                   COUNT(p.id) AS offer_count,
                   MIN(p.cost_price) AS min_cost,
                   MAX(p.cost_price) AS max_cost,
                   AVG(p.cost_price) AS avg_cost
            FROM product_groups g
            LEFT JOIN products p ON p.group_id = g.id
            GROUP BY g.id
            HAVING offer_count >= ?
            ORDER BY offer_count DESC, g.canonical_name ASC
            """,
            (min_offers,),
        ).fetchall()
    df = pd.DataFrame([dict(r) for r in rows])
    if not df.empty:
        df["savings"] = df["max_cost"] - df["min_cost"]
        df["savings_pct"] = df.apply(
            lambda r: ((r["max_cost"] - r["min_cost"]) / r["max_cost"] * 100)
            if r["max_cost"] else 0,
            axis=1,
        )
    return df


def ungrouped_products() -> pd.DataFrame:
    """Products that couldn't auto-group — user can manually assign."""
    with db.conn() as c:
        rows = c.execute(
            "SELECT id, sku, brand, name, cost_price FROM products "
            "WHERE group_id IS NULL ORDER BY name"
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])
