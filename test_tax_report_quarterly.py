"""Characterization tests for tax_report — VALID-quarter behavior only.

Scope (ME-02 / IMP-A-P1-004): this harness locks in current behavior of
quarterly(), annual() and vat_check() for valid quarters (1-4) and valid
years, against a temporary, isolated SQLite database — never the shared
data/listo.db or any per-user database.

It does NOT decide or implement the invalid-quarter policy tracked in
Nirvasell issue #22 ("DRAFT: tax_report quarterly invalid-quarter policy").
That issue is explicitly non-binding pending an owner decision (A/B/C) and
is out of scope here.

A follow-up slice fixed one narrow, orthogonal defect this harness first
discovered: tax_report.py's expense query referenced a column
(`expense_date`) that has never existed on the `expenses` table (the real
column is `date`, per expenses.py). That mismatch was unrelated to #22 (it
fired for every valid quarter regardless of data) and did not touch tax
rates, filing rules, or invalid-quarter behavior, so it was corrected here
and the corresponding tests below now assert correct computed totals
instead of the OperationalError they originally locked in. Missing-table
scenarios (returns/expenses tables not yet created) remain characterized
as-is and untouched — see test_quarterly_fresh_db_raises_missing_returns_
table and test_quarterly_without_expenses_table_raises_missing_expenses_
table below.

Runs with the plain interpreter (no pytest required)::

    python3 test_tax_report_quarterly.py

...and is also pytest-discoverable (def test_*).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import types
from contextlib import contextmanager
from pathlib import Path

# db.py hard-imports pandas for CSV/dataframe helpers (upsert_products,
# fetch_products, fetch_content) that this harness never touches. Stub it
# only when pandas isn't installed, so the harness adds no new hard
# dependency beyond what the module under test already needs to import.
if "pandas" not in sys.modules:
    try:
        import pandas  # noqa: F401
    except ImportError:
        _fake_pandas = types.ModuleType("pandas")
        _fake_pandas.DataFrame = type("DataFrame", (), {})
        _fake_pandas.notna = lambda x: x is not None
        sys.modules["pandas"] = _fake_pandas

sys.path.insert(0, str(Path(__file__).parent))

import db  # noqa: E402
import tax_report as tr  # noqa: E402


@contextmanager
def isolated_db():
    """Point db.conn() at a throw-away SQLite file for the duration of the
    block, then restore the original resolver — even if the block raises.
    Never touches real user data. Yields the temp directory Path.

    Patches db._resolve_path directly — the function db.conn() actually
    calls — rather than db.DATA/db.DB_PATH. db._resolve_path() tries
    `from auth import user_db_path` first and only falls back to
    db.DB_PATH if that import or call raises (db.py:20-26). Patching only
    DATA/DB_PATH is isolated by accident, on any environment where `auth`
    (which hard-imports streamlit) fails to import; the moment auth is
    importable and user_db_path() returns cleanly, db.conn() would route
    to auth.py's own DATA/"listo.db" — a real, shared, per-user path —
    ignoring the patched DATA/DB_PATH entirely. See
    test_isolated_db_never_calls_available_auth_resolver below."""
    tmpdir = Path(tempfile.mkdtemp(prefix="nirvasell_tax_report_test_"))
    db_path = tmpdir / "test.db"
    original_resolve_path = db._resolve_path
    db._resolve_path = lambda: db_path
    try:
        db.init()
        yield tmpdir
    finally:
        db._resolve_path = original_resolve_path
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---- isolated_db() harness self-check --------------------------------------
# These protect the test HARNESS itself, not tax_report.py. db.conn() does
# not read db.DATA/db.DB_PATH directly — it calls db._resolve_path(), which
# tries `from auth import user_db_path` first and only falls back to
# db.DB_PATH if that import or call raises (see db.py:20-26, auth.py:426-433).
# A DATA/DB_PATH-only patch is isolated only by the accident of `auth`
# (which hard-imports streamlit) failing to import in whatever environment
# runs this file — it silently stops isolating the moment auth becomes
# importable and user_db_path() returns cleanly, which can route db.conn()
# to auth.py's own DATA/"listo.db" (a real, shared, per-user path).
#
# Each check below installs a synthetic stand-in `auth` module — never the
# real one, never real data — so the guarantee holds regardless of whether
# streamlit happens to be installed here. If anything below did reach the
# fake resolver, it would only ever touch a sentinel file inside a temp
# directory this call uniquely owns (own mkdtemp, not a fixed/shared name),
# so concurrent test runs can't collide and restore() can never delete a
# preexisting file — the whole owned directory is removed, nothing else.

def _install_fake_auth_resolver():
    """Install a spying stand-in for the `auth` module. Returns (calls,
    restore): `calls` records every invocation of the fake user_db_path();
    restore() puts sys.modules['auth'] back exactly as found and removes
    only the uniquely-owned sentinel directory this call created."""
    calls = []
    sentinel_dir = Path(tempfile.mkdtemp(prefix="nirvasell_test_fake_auth_"))
    sentinel = sentinel_dir / "SHOULD_NEVER_BE_USED.db"

    def _fake_user_db_path():
        calls.append(1)
        return sentinel

    fake_auth = types.ModuleType("auth")
    fake_auth.user_db_path = _fake_user_db_path
    had_auth = "auth" in sys.modules
    orig_auth = sys.modules.get("auth")
    sys.modules["auth"] = fake_auth

    def _restore():
        if had_auth:
            sys.modules["auth"] = orig_auth
        else:
            sys.modules.pop("auth", None)
        shutil.rmtree(sentinel_dir, ignore_errors=True)

    return calls, _restore


def test_isolated_db_never_calls_available_auth_resolver():
    calls, restore = _install_fake_auth_resolver()
    try:
        with isolated_db():
            with db.conn():
                pass
        assert calls == [], (
            "db.conn() reached auth.user_db_path() while isolated_db() was "
            "active — the fixture must patch db._resolve_path itself, not "
            "just db.DATA/db.DB_PATH"
        )
    finally:
        restore()


def test_isolated_db_sqlite_main_file_is_inside_tempdir():
    calls, restore = _install_fake_auth_resolver()
    try:
        with isolated_db() as tmpdir:
            with db.conn() as c:
                main_file = Path(c.execute("PRAGMA database_list").fetchone()["file"]).resolve()
            assert main_file.parent == Path(tmpdir).resolve(), (
                f"sqlite main file {main_file} is not inside the isolated "
                f"temp dir {tmpdir}"
            )
    finally:
        restore()


def test_isolated_db_restores_resolver_after_normal_exit():
    original = db._resolve_path
    with isolated_db():
        assert db._resolve_path is not original
    assert db._resolve_path is original


def test_isolated_db_restores_resolver_after_exceptional_exit():
    original = db._resolve_path

    class _SyntheticFailure(Exception):
        pass

    try:
        with isolated_db():
            raise _SyntheticFailure("synthetic failure inside isolated_db() block")
    except _SyntheticFailure:
        pass
    assert db._resolve_path is original


# ---- synthetic fixtures ----------------------------------------------------
# Table DDL below is copied verbatim from returns.py/expenses.py (not from
# tax_report.py's assumptions) so the harness proves what the REAL schema
# looks like, not what tax_report.py hopes it looks like. Rows are inserted
# with raw SQL rather than expenses.add()/returns.add() because those helpers
# have their own unrelated bug (`Connection.lastrowid` does not exist in
# Python's sqlite3 module) — out of scope for this slice.

def _init_returns_table():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id    TEXT DEFAULT '',
                sku         TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                reason      TEXT DEFAULT 'other',
                refund_amount REAL DEFAULT 0,
                shipping_cost REAL DEFAULT 0,
                note        TEXT DEFAULT '',
                return_date TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)


def _init_expenses_table():
    with db.conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                category    TEXT NOT NULL DEFAULT 'other',
                amount      REAL NOT NULL DEFAULT 0,
                note        TEXT DEFAULT '',
                platform    TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)


def _insert_order(order_id, sku, platform, unit_price, qty, total, order_date, status="paid"):
    with db.conn() as c:
        c.execute(
            "INSERT INTO orders (order_id, sku, platform, qty, unit_price, total_price, "
            "order_date, status) VALUES (?,?,?,?,?,?,?,?)",
            (order_id, sku, platform, qty, unit_price, total, order_date, status),
        )


def _insert_return(order_id, sku, platform, refund_amount, created_at, return_date=None):
    # tax_report.py buckets returns by `created_at`, not `return_date` (a
    # separate, out-of-scope semantic question — see module docstring), so
    # tests that need deterministic quarter placement must set created_at
    # explicitly rather than rely on its `datetime('now')` default.
    if return_date is None:
        return_date = created_at[:10]
    with db.conn() as c:
        c.execute(
            "INSERT INTO returns (order_id, sku, platform, reason, refund_amount, "
            "shipping_cost, note, return_date, created_at) VALUES (?,?,?,?,?,0,'',?,?)",
            (order_id, sku, platform, "other", refund_amount, return_date, created_at),
        )


def _insert_expense(date, category, amount):
    with db.conn() as c:
        c.execute(
            "INSERT INTO expenses (date, category, amount) VALUES (?,?,?)",
            (date, category, amount),
        )


# ---- vat_check() / stats(): the entry points that currently work ----------
# quarterly()/annual() never reach a `return` in any reachable DB state (see
# below) — vat_check() only touches `orders`, whose real columns match its
# query, so it is characterized here as correct, working current behavior.

def test_vat_check_sums_only_non_cancelled_non_returned_orders():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 500, 2, 1000, "2026-01-05", "paid")
        _insert_order("O2", "SKU2", "lazada", 300, 1, 300, "2026-02-10", "shipped")
        _insert_order("O3", "SKU3", "shopee", 999, 1, 999, "2026-03-01", "cancelled")
        _insert_order("O4", "SKU4", "tiktok", 100, 1, 100, "2026-03-02", "returned")
        result = tr.vat_check(2026)
        assert result["revenue"] == 1300.0, result


def test_vat_check_requires_vat_at_threshold():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 1_800_000, 1, 1_800_000, "2026-05-01")
        result = tr.vat_check(2026)
        assert result["requires_vat"] is True, result
        assert result["remaining_headroom"] == 0.0, result
        assert result["pct_of_threshold"] == 100.0, result


def test_vat_check_headroom_below_threshold():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 900_000, 1, 900_000, "2026-05-01")
        result = tr.vat_check(2026)
        assert result["requires_vat"] is False, result
        assert result["remaining_headroom"] == 900_000.0, result
        assert result["pct_of_threshold"] == 50.0, result


def test_vat_check_ignores_other_years():
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 500, 1, 500, "2025-12-31")
        _insert_order("O2", "SKU2", "shopee", 700, 1, 700, "2027-01-01")
        result = tr.vat_check(2026)
        assert result["revenue"] == 0.0, result


def test_stats_wraps_vat_check_for_current_year():
    from datetime import datetime
    with isolated_db():
        _insert_order("O1", "SKU1", "shopee", 400, 1, 400, f"{datetime.now().year}-01-01")
        result = tr.stats()
        assert result["ytd_revenue"] == 400.0, result
        assert result["vat_required"] is False, result


# ---- quarterly() / annual(): DB-state coverage -----------------------------
# The two missing-table cases below remain deterministic, data-independent
# failures — the table simply doesn't exist yet, regardless of quarter or
# row contents — and are intentionally left untouched (out of ME-02 scope).
# The real-schema case further down now asserts correct computed totals,
# since the expense_date -> date column fix landed in tax_report.py.

VALID_QUARTERS = (1, 2, 3, 4)


def test_quarterly_fresh_db_raises_missing_returns_table():
    # Realistic state: only db.init() has ever run — a brand-new workspace
    # that opens Tax Report before ever visiting Expenses/Returns pages.
    with isolated_db():
        for q in VALID_QUARTERS:
            try:
                tr.quarterly(2026, q)
                raise AssertionError(f"quarter {q}: expected OperationalError, got a result")
            except AssertionError:
                raise
            except Exception as e:
                assert type(e).__name__ == "OperationalError", (q, e)
                assert "no such table: returns" in str(e), (q, e)


def test_quarterly_without_expenses_table_raises_missing_expenses_table():
    # Realistic state: seller has recorded returns but never opened the
    # Expenses page, so expenses.init() has never run.
    with isolated_db():
        _init_returns_table()
        for q in VALID_QUARTERS:
            try:
                tr.quarterly(2026, q)
                raise AssertionError(f"quarter {q}: expected OperationalError, got a result")
            except AssertionError:
                raise
            except Exception as e:
                assert type(e).__name__ == "OperationalError", (q, e)
                assert "no such table: expenses" in str(e), (q, e)


def _seed_full_year(year=2026):
    """One synthetic order/return/expense per quarter, chosen so every
    quarter has a distinct, hand-computed expected result (see comments in
    the two tests below for the arithmetic)."""
    _init_returns_table()
    _init_expenses_table()

    # Q1 (Jan-Mar): two counted orders + one cancelled (excluded)
    _insert_order("O1", "SKU1", "shopee", 1000, 1, 1000, f"{year}-01-15", "paid")
    _insert_order("O2", "SKU2", "lazada", 500, 1, 500, f"{year}-02-10", "shipped")
    _insert_order("O3", "SKU3", "shopee", 300, 1, 300, f"{year}-03-05", "cancelled")
    _insert_return("O1", "SKU1", "shopee", 50, f"{year}-01-20 10:00:00")
    _insert_expense(f"{year}-01-05", "shipping", 30)
    _insert_expense(f"{year}-01-25", "packaging", 20)

    # Q2 (Apr-Jun): one counted order, no returns
    _insert_order("O4", "SKU4", "tiktok", 800, 1, 800, f"{year}-04-20", "paid")
    _insert_expense(f"{year}-04-10", "advertising", 50)

    # Q3 (Jul-Sep): one counted order + one returned-status order (excluded)
    _insert_order("O5", "SKU5", "shopee", 1200, 1, 1200, f"{year}-07-01", "paid")
    _insert_order("O6", "SKU6", "lazada", 400, 1, 400, f"{year}-08-15", "returned")
    _insert_return("O5", "SKU5", "shopee", 100, f"{year}-07-15 10:00:00")
    _insert_expense(f"{year}-07-20", "shipping", 40)

    # Q4 (Oct-Dec): two counted orders, no returns, two expense categories
    _insert_order("O7", "SKU7", "shopee", 2000, 1, 2000, f"{year}-10-10", "paid")
    _insert_order("O8", "SKU8", "tiktok", 300, 1, 300, f"{year}-11-11", "paid")
    _insert_expense(f"{year}-10-05", "platform_fee", 60)
    _insert_expense(f"{year}-10-15", "shipping", 25)


# Hand-computed from _seed_full_year(): revenue/returns/expenses per quarter,
# then net_revenue = revenue - returns, total_expenses = sum(expenses),
# gross_profit = net_revenue - total_expenses,
# std_deduction = round(net_revenue * 0.6, 2),
# taxable_income_std/actual = max(0, net_revenue - std_deduction/total_expenses).
EXPECTED_QUARTERS = {
    1: dict(revenue=1500.0, returns=50.0, net_revenue=1450.0,
            expenses={"shipping": 30.0, "packaging": 20.0}, total_expenses=50.0,
            gross_profit=1400.0, standard_deduction=870.0,
            taxable_income_std=580.0, taxable_income_actual=1400.0, orders=2),
    2: dict(revenue=800.0, returns=0.0, net_revenue=800.0,
            expenses={"advertising": 50.0}, total_expenses=50.0,
            gross_profit=750.0, standard_deduction=480.0,
            taxable_income_std=320.0, taxable_income_actual=750.0, orders=1),
    3: dict(revenue=1200.0, returns=100.0, net_revenue=1100.0,
            expenses={"shipping": 40.0}, total_expenses=40.0,
            gross_profit=1060.0, standard_deduction=660.0,
            taxable_income_std=440.0, taxable_income_actual=1060.0, orders=1),
    4: dict(revenue=2300.0, returns=0.0, net_revenue=2300.0,
            expenses={"platform_fee": 60.0, "shipping": 25.0}, total_expenses=85.0,
            gross_profit=2215.0, standard_deduction=1380.0,
            taxable_income_std=920.0, taxable_income_actual=2215.0, orders=2),
}


def test_quarterly_computes_correct_totals_for_each_valid_quarter_with_real_schema():
    # Realistic steady state: returns AND expenses tables both exist with the
    # actual production schema (expenses.py's `expenses.date` column — see
    # the fixed `expense_date` -> `date` reference in tax_report.py). Proves
    # quarterly() now reaches its `return` and computes correct totals for
    # every valid quarter, with quarter-boundary month selection verified by
    # data landing in the expected quarter only.
    with isolated_db():
        _seed_full_year(2026)
        for q in VALID_QUARTERS:
            expected = EXPECTED_QUARTERS[q]
            result = tr.quarterly(2026, q)
            assert result["year"] == 2026, (q, result)
            assert result["quarter"] == q, (q, result)
            for key, value in expected.items():
                assert result[key] == value, (q, key, result)


def test_annual_aggregates_all_four_quarters_with_real_schema():
    with isolated_db():
        _seed_full_year(2026)
        result = tr.annual(2026)
        assert result["revenue"] == 5800.0, result
        assert result["net_revenue"] == 5650.0, result
        assert result["total_expenses"] == 225.0, result
        assert result["gross_profit"] == 5425.0, result
        assert result["standard_deduction"] == 3390.0, result
        assert result["taxable_income_std"] == 2260.0, result
        assert result["taxable_income_actual"] == 5425.0, result
        assert result["orders"] == 6, result
        assert result["vat_required"] is False, result
        assert result["expenses"] == {
            "shipping": 95.0, "packaging": 20.0,
            "advertising": 50.0, "platform_fee": 60.0,
        }, result
        assert [q["quarter"] for q in result["by_quarter"]] == [1, 2, 3, 4], result
        for q_report in result["by_quarter"]:
            expected = EXPECTED_QUARTERS[q_report["quarter"]]
            for key, value in expected.items():
                assert q_report[key] == value, (q_report["quarter"], key, q_report)


# ---- runner -----------------------------------------------------------------
def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✅ {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ❌ {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  \U0001F4A5 {t.__name__}: {type(e).__name__}: {e}")
    print(f"\ntax_report characterization tests: {passed} passed, {failed} failed ({len(tests)} total)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
