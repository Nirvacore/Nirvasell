"""Tests for products.py — product catalog CRUD over the products table."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

import products


# ---------------------------------------------------------------------------
# Helpers — in-memory SQLite that mirrors the real schema
# ---------------------------------------------------------------------------

def _make_db():
    """Return (mock_db, raw_connection) with products table."""
    mem = sqlite3.connect(":memory:")
    mem.row_factory = sqlite3.Row
    mem.execute("PRAGMA foreign_keys = ON")
    mem.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL UNIQUE,
            name TEXT,
            brand TEXT,
            category TEXT,
            cost_price REAL,
            sell_price INTEGER,
            stock INTEGER,
            image_url TEXT,
            specs TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    mem.commit()
    return mem


def _seed_products(mem, rows):
    """Insert multiple product rows from a list of tuples
    (sku, name, brand, category, cost_price, sell_price, stock, image_url)."""
    for r in rows:
        mem.execute(
            "INSERT INTO products (sku, name, brand, category, cost_price, sell_price, stock, image_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            r,
        )
    mem.commit()


@pytest.fixture()
def prod_db():
    """Provide a patched in-memory DB for products module."""
    mem = _make_db()
    mock_db = MagicMock()
    mock_db.get_conn.return_value = mem
    mock_db.init.return_value = None

    @contextmanager
    def _conn():
        yield mem
        mem.commit()

    mock_db.conn = _conn
    with patch.object(products, "db", mock_db):
        yield mock_db, mem


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

class TestInit:
    def test_init_calls_db_init(self, prod_db):
        mock_db, _ = prod_db
        products.init()
        mock_db.init.assert_called_once()


# ---------------------------------------------------------------------------
# all_products — empty
# ---------------------------------------------------------------------------

class TestAllProductsEmpty:
    def test_returns_empty_list_when_no_products(self, prod_db):
        result = products.all_products()
        assert result == []

    def test_returns_list_type(self, prod_db):
        result = products.all_products()
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# all_products — with data
# ---------------------------------------------------------------------------

class TestAllProductsWithData:
    def test_returns_all_products(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Widget A", "BrandX", "Electronics", 100.0, 150, 50, ""),
            ("SKU-002", "Widget B", "BrandY", "Clothing", 200.0, 300, 30, ""),
        ])
        result = products.all_products()
        assert len(result) == 2

    def test_returns_dicts(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Widget A", "BrandX", "Electronics", 100.0, 150, 50, ""),
        ])
        result = products.all_products()
        assert isinstance(result[0], dict)

    def test_dict_keys(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Widget A", "BrandX", "Electronics", 100.0, 150, 50, "http://img.jpg"),
        ])
        result = products.all_products()
        expected_keys = {"id", "sku", "name", "brand", "category", "cost_price", "sell_price", "stock", "image_url"}
        assert expected_keys == set(result[0].keys())

    def test_ordered_by_name(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-002", "Zebra Item", "B", "C", 10, 20, 5, ""),
            ("SKU-001", "Alpha Item", "B", "C", 10, 20, 5, ""),
            ("SKU-003", "Middle Item", "B", "C", 10, 20, 5, ""),
        ])
        result = products.all_products()
        names = [p["name"] for p in result]
        assert names == ["Alpha Item", "Middle Item", "Zebra Item"]

    def test_correct_values(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Test Product", "TestBrand", "TestCat", 99.50, 199, 42, "http://example.com/img.jpg"),
        ])
        result = products.all_products()
        p = result[0]
        assert p["sku"] == "SKU-001"
        assert p["name"] == "Test Product"
        assert p["brand"] == "TestBrand"
        assert p["category"] == "TestCat"
        assert p["cost_price"] == 99.50
        assert p["sell_price"] == 199
        assert p["stock"] == 42
        assert p["image_url"] == "http://example.com/img.jpg"


# ---------------------------------------------------------------------------
# get — by id
# ---------------------------------------------------------------------------

class TestGet:
    def test_returns_product_by_id(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Widget A", "BrandX", "Electronics", 100.0, 150, 50, ""),
        ])
        # Get the ID that was auto-assigned
        row_id = mem.execute("SELECT id FROM products WHERE sku='SKU-001'").fetchone()[0]
        result = products.get(row_id)
        assert result is not None
        assert result["sku"] == "SKU-001"
        assert result["name"] == "Widget A"

    def test_returns_none_for_nonexistent_id(self, prod_db):
        result = products.get(99999)
        assert result is None

    def test_returns_dict(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Widget A", "BrandX", "Electronics", 100.0, 150, 50, ""),
        ])
        row_id = mem.execute("SELECT id FROM products WHERE sku='SKU-001'").fetchone()[0]
        result = products.get(row_id)
        assert isinstance(result, dict)

    def test_returns_correct_fields(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-100", "Gadget", "BrandZ", "Toys", 50.0, 80, 10, "http://img.png"),
        ])
        row_id = mem.execute("SELECT id FROM products WHERE sku='SKU-100'").fetchone()[0]
        result = products.get(row_id)
        assert result["sku"] == "SKU-100"
        assert result["brand"] == "BrandZ"
        assert result["category"] == "Toys"
        assert result["cost_price"] == 50.0
        assert result["sell_price"] == 80
        assert result["stock"] == 10

    def test_get_with_null_fields(self, prod_db):
        _, mem = prod_db
        mem.execute(
            "INSERT INTO products (sku, name) VALUES (?, ?)",
            ("SKU-NULL", "Bare Product"),
        )
        mem.commit()
        row_id = mem.execute("SELECT id FROM products WHERE sku='SKU-NULL'").fetchone()[0]
        result = products.get(row_id)
        assert result is not None
        assert result["name"] == "Bare Product"
        assert result["brand"] is None
        assert result["category"] is None

    def test_get_returns_id_field(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-ID", "ID Test", "B", "C", 10, 20, 5, ""),
        ])
        row_id = mem.execute("SELECT id FROM products WHERE sku='SKU-ID'").fetchone()[0]
        result = products.get(row_id)
        assert result["id"] == row_id


# ---------------------------------------------------------------------------
# by_sku
# ---------------------------------------------------------------------------

class TestBySku:
    def test_returns_product_by_sku(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Widget A", "BrandX", "Electronics", 100.0, 150, 50, ""),
            ("SKU-002", "Widget B", "BrandY", "Clothing", 200.0, 300, 30, ""),
        ])
        result = products.by_sku("SKU-002")
        assert result is not None
        assert result["sku"] == "SKU-002"
        assert result["name"] == "Widget B"

    def test_returns_none_for_nonexistent_sku(self, prod_db):
        result = products.by_sku("NO-SUCH-SKU")
        assert result is None

    def test_returns_dict(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001", "Widget A", "BrandX", "Electronics", 100.0, 150, 50, ""),
        ])
        result = products.by_sku("SKU-001")
        assert isinstance(result, dict)

    def test_sku_is_case_sensitive(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("sku-lower", "Lower Case", "B", "C", 10, 20, 5, ""),
        ])
        # Exact match should work
        assert products.by_sku("sku-lower") is not None
        # Different case should not match
        assert products.by_sku("SKU-LOWER") is None

    def test_returns_correct_product_among_many(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-A", "Product A", "Brand1", "Cat1", 10, 20, 5, ""),
            ("SKU-B", "Product B", "Brand2", "Cat2", 30, 40, 15, ""),
            ("SKU-C", "Product C", "Brand3", "Cat3", 50, 60, 25, ""),
        ])
        result = products.by_sku("SKU-B")
        assert result["name"] == "Product B"
        assert result["brand"] == "Brand2"
        assert result["cost_price"] == 30

    def test_by_sku_with_special_characters(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-001/A", "Special SKU", "B", "C", 10, 20, 5, ""),
        ])
        result = products.by_sku("SKU-001/A")
        assert result is not None
        assert result["name"] == "Special SKU"

    def test_by_sku_empty_string(self, prod_db):
        result = products.by_sku("")
        assert result is None

    def test_by_sku_returns_all_fields(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-FULL", "Full Product", "FullBrand", "FullCat", 123.45, 200, 99, "http://img.png"),
        ])
        result = products.by_sku("SKU-FULL")
        expected_keys = {"id", "sku", "name", "brand", "category", "cost_price", "sell_price", "stock", "image_url"}
        assert expected_keys == set(result.keys())
        assert result["cost_price"] == 123.45
        assert result["sell_price"] == 200
        assert result["stock"] == 99
        assert result["image_url"] == "http://img.png"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_multiple_products_all_returned(self, prod_db):
        _, mem = prod_db
        for i in range(20):
            mem.execute(
                "INSERT INTO products (sku, name, brand, category, cost_price, sell_price, stock, image_url) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (f"SKU-{i:03d}", f"Product {i}", "Brand", "Cat", i * 10, i * 15, i, ""),
            )
        mem.commit()
        result = products.all_products()
        assert len(result) == 20

    def test_get_and_by_sku_agree(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-AGREE", "Agree Test", "B", "C", 100, 200, 50, "http://img.png"),
        ])
        row_id = mem.execute("SELECT id FROM products WHERE sku='SKU-AGREE'").fetchone()[0]
        by_id = products.get(row_id)
        by_sku = products.by_sku("SKU-AGREE")
        assert by_id == by_sku

    def test_product_with_zero_stock(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-ZERO", "Zero Stock", "B", "C", 10, 20, 0, ""),
        ])
        result = products.by_sku("SKU-ZERO")
        assert result["stock"] == 0

    def test_product_with_zero_price(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-FREE", "Free Item", "B", "C", 0, 0, 10, ""),
        ])
        result = products.by_sku("SKU-FREE")
        assert result["cost_price"] == 0
        assert result["sell_price"] == 0

    def test_product_with_unicode_name(self, prod_db):
        _, mem = prod_db
        _seed_products(mem, [
            ("SKU-TH", "สินค้าทดสอบ", "แบรนด์", "หมวดหมู่", 100, 200, 10, ""),
        ])
        result = products.by_sku("SKU-TH")
        assert result["name"] == "สินค้าทดสอบ"
        assert result["brand"] == "แบรนด์"

    def test_product_with_long_image_url(self, prod_db):
        _, mem = prod_db
        long_url = "http://example.com/" + "a" * 500
        _seed_products(mem, [
            ("SKU-URL", "URL Test", "B", "C", 10, 20, 5, long_url),
        ])
        result = products.by_sku("SKU-URL")
        assert result["image_url"] == long_url
