"""Regression coverage for low-stock alerts on the canonical product schema."""
from __future__ import annotations

import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        fake_pandas = types.ModuleType("pandas")
        fake_pandas.DataFrame = type("DataFrame", (), {})
        sys.modules["pandas"] = fake_pandas

if "streamlit" not in sys.modules:
    fake_streamlit = types.ModuleType("streamlit")
    fake_streamlit.session_state = {}
    sys.modules["streamlit"] = fake_streamlit

import alerts
import db


@contextmanager
def isolated_db():
    temp_dir = Path(tempfile.mkdtemp(prefix="nirvasell_alerts_"))
    db_path = temp_dir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        db.init()
        alerts.init()
        yield
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_low_stock_alert_uses_canonical_product_schema():
    with isolated_db():
        with db.conn() as connection:
            connection.executemany(
                "INSERT INTO products (sku, name, stock) VALUES (?, ?, ?)",
                [
                    ("LOW-1", "Low stock", 5),
                    ("OK-1", "Enough stock", 6),
                ],
            )

        low_stock = [
            alert for alert in alerts.check_all()
            if alert["type"] == "low_stock"
        ]

        assert len(low_stock) == 1
        assert low_stock[0]["key"] == "low_stock_daily"
        assert low_stock[0]["count"] == 1


if __name__ == "__main__":
    test_low_stock_alert_uses_canonical_product_schema()
    print("alerts product schema tests: 1 passed")
