"""Regression coverage for global search against the canonical orders schema."""
from __future__ import annotations

import ast
import sys
import tempfile
import types
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        fake_pandas.notna = lambda value: value is not None
        sys.modules["pandas"] = fake_pandas

import db
import fulfillment
import global_search


def _render_order_amount(order: dict) -> str:
    """Evaluate the page's actual amount formatter without running its UI/auth."""
    page = Path(__file__).parent / "pages" / "A2_🔎_Search.py"
    tree = ast.parse(page.read_text(), filename=str(page))
    formatters = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "format"
        and any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and isinstance(child.func.value, ast.Name)
            and child.func.value.id == "o"
            and child.func.attr == "get"
            and child.args
            and isinstance(child.args[0], ast.Constant)
            and child.args[0].value in ("total_price", "total_amount")
            for child in ast.walk(node)
        )
    ]
    assert len(formatters) == 1, "expected exactly one order amount formatter"
    return eval(compile(ast.Expression(formatters[0]), str(page), "eval"),
                {"__builtins__": {}}, {"o": order})


def test_search_reads_order_total_price() -> None:
    with tempfile.TemporaryDirectory(prefix="nirvasell-global-search-") as temp:
        original_resolver = db._resolve_path
        db._resolve_path = lambda: Path(temp) / "fixture.db"
        try:
            fulfillment.init()
            with db.conn() as connection:
                connection.execute(
                    "INSERT INTO orders (order_id, sku, platform, qty, total_price, order_date, status, buyer_name, buyer_phone) VALUES (?,?,?,?,?,?,?,?,?)",
                    ("order-1", "SKU-1", "fixture", 2, 240.0, "2026-09-07", "paid", "Nirva buyer", "0812345678"),
                )

            result = global_search.search("order-1")
            assert result["orders"] == [
                {
                    "order_id": "order-1",
                    "sku": "SKU-1",
                    "platform": "fixture",
                    "qty": 2,
                    "total_price": 240.0,
                    "order_date": "2026-09-07",
                    "status": "paid",
                    "buyer_name": "Nirva buyer",
                    "buyer_phone": "0812345678",
                }
            ]
            assert _render_order_amount(result["orders"][0]) == "240"
            assert _render_order_amount({"total_price": 0}) == "0"
        finally:
            db._resolve_path = original_resolver


if __name__ == "__main__":
    test_search_reads_order_total_price()
    print("global search order schema: 1 passed")
