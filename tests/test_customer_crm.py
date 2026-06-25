"""Tests for customer_crm.py — notes, tags, follow-ups, and customer profiles."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest

import customer_crm


# ---------------------------------------------------------------------------
# Helpers — in-memory SQLite that mirrors the real schema
# ---------------------------------------------------------------------------

def _make_db():
    """Return (fake_conn_fn, raw_connection) with CRM + orders tables."""
    mem = sqlite3.connect(":memory:")
    mem.row_factory = sqlite3.Row
    mem.execute("PRAGMA foreign_keys = ON")

    # Orders table (used by customer_profile)
    mem.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            sku TEXT,
            buyer_name TEXT,
            buyer_phone TEXT,
            platform TEXT,
            total_price REAL,
            total_amount REAL,
            order_date TEXT
        )
    """)
    mem.commit()

    @contextmanager
    def _conn():
        yield mem
        mem.commit()

    return _conn, mem


@pytest.fixture()
def crm_db():
    """Provide a patched in-memory DB with CRM tables initialized."""
    fake_conn, mem = _make_db()
    with patch("customer_crm.db") as mock_db:
        mock_db.conn = fake_conn
        # Call init() to create the CRM tables
        customer_crm.init()
        yield mock_db, mem


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

class TestConstants:

    def test_note_types_has_expected_keys(self):
        expected = {"general", "preference", "complaint", "feedback", "vip"}
        assert set(customer_crm.NOTE_TYPES.keys()) == expected

    def test_default_tags_is_nonempty(self):
        assert len(customer_crm.DEFAULT_TAGS) > 0
        assert all(isinstance(t, str) for t in customer_crm.DEFAULT_TAGS)


# ---------------------------------------------------------------------------
# init
# ---------------------------------------------------------------------------

class TestInit:

    def test_creates_tables(self, crm_db):
        _, mem = crm_db
        tables = {r[0] for r in mem.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        assert "customer_notes" in tables
        assert "customer_tags" in tables
        assert "customer_followups" in tables

    def test_idempotent(self, crm_db):
        """Calling init() twice should not raise."""
        customer_crm.init()


# ---------------------------------------------------------------------------
# add_note / notes_for / delete_note
# ---------------------------------------------------------------------------

class TestNotes:

    def test_add_and_retrieve(self, crm_db):
        note_id = customer_crm.add_note("CUST-1", "Likes fast shipping")
        assert isinstance(note_id, int)
        assert note_id > 0

        notes = customer_crm.notes_for("CUST-1")
        assert len(notes) == 1
        assert notes[0]["note"] == "Likes fast shipping"
        assert notes[0]["note_type"] == "general"

    def test_custom_note_type(self, crm_db):
        customer_crm.add_note("CUST-1", "Color issue", note_type="complaint")
        notes = customer_crm.notes_for("CUST-1")
        assert notes[0]["note_type"] == "complaint"

    def test_multiple_notes_ordered_desc(self, crm_db):
        _, mem = crm_db
        # Insert with explicit timestamps to control order
        mem.execute(
            "INSERT INTO customer_notes (customer_key, note, note_type, created_at) "
            "VALUES (?, ?, ?, ?)", ("CUST-1", "First", "general", "2025-01-01 10:00:00")
        )
        mem.execute(
            "INSERT INTO customer_notes (customer_key, note, note_type, created_at) "
            "VALUES (?, ?, ?, ?)", ("CUST-1", "Second", "general", "2025-06-01 10:00:00")
        )
        mem.commit()

        notes = customer_crm.notes_for("CUST-1")
        assert len(notes) == 2
        assert notes[0]["note"] == "Second"  # More recent first
        assert notes[1]["note"] == "First"

    def test_delete_note(self, crm_db):
        nid = customer_crm.add_note("CUST-1", "To be removed")
        assert len(customer_crm.notes_for("CUST-1")) == 1

        customer_crm.delete_note(nid)
        assert len(customer_crm.notes_for("CUST-1")) == 0

    def test_notes_isolated_by_customer(self, crm_db):
        customer_crm.add_note("CUST-A", "Note for A")
        customer_crm.add_note("CUST-B", "Note for B")

        assert len(customer_crm.notes_for("CUST-A")) == 1
        assert len(customer_crm.notes_for("CUST-B")) == 1
        assert customer_crm.notes_for("CUST-A")[0]["note"] == "Note for A"


# ---------------------------------------------------------------------------
# add_tag / remove_tag / tags_for
# ---------------------------------------------------------------------------

class TestTags:

    def test_add_and_retrieve(self, crm_db):
        customer_crm.add_tag("CUST-1", "VIP")
        tags = customer_crm.tags_for("CUST-1")
        assert tags == ["VIP"]

    def test_duplicate_tag_ignored(self, crm_db):
        customer_crm.add_tag("CUST-1", "VIP")
        customer_crm.add_tag("CUST-1", "VIP")
        tags = customer_crm.tags_for("CUST-1")
        assert tags == ["VIP"]

    def test_multiple_tags_sorted(self, crm_db):
        customer_crm.add_tag("CUST-1", "Zebra")
        customer_crm.add_tag("CUST-1", "Apple")
        customer_crm.add_tag("CUST-1", "Mango")
        tags = customer_crm.tags_for("CUST-1")
        assert tags == ["Apple", "Mango", "Zebra"]

    def test_remove_tag(self, crm_db):
        customer_crm.add_tag("CUST-1", "VIP")
        customer_crm.add_tag("CUST-1", "Loyal")
        customer_crm.remove_tag("CUST-1", "VIP")
        tags = customer_crm.tags_for("CUST-1")
        assert tags == ["Loyal"]

    def test_remove_nonexistent_tag_no_error(self, crm_db):
        customer_crm.remove_tag("CUST-1", "NoSuchTag")  # Should not raise

    def test_tags_isolated_by_customer(self, crm_db):
        customer_crm.add_tag("CUST-A", "VIP")
        customer_crm.add_tag("CUST-B", "Regular")
        assert customer_crm.tags_for("CUST-A") == ["VIP"]
        assert customer_crm.tags_for("CUST-B") == ["Regular"]


# ---------------------------------------------------------------------------
# add_followup / complete_followup / pending_followups
# ---------------------------------------------------------------------------

class TestFollowups:

    def test_add_followup(self, crm_db):
        fid = customer_crm.add_followup("CUST-1", "2026-06-30", "Check satisfaction")
        assert isinstance(fid, int)
        assert fid > 0

    def test_complete_followup(self, crm_db):
        _, mem = crm_db
        fid = customer_crm.add_followup("CUST-1", "2026-06-25", "Call back")
        customer_crm.complete_followup(fid)

        row = mem.execute(
            "SELECT status FROM customer_followups WHERE id=?", (fid,)
        ).fetchone()
        assert row["status"] == "done"

    def test_pending_followups_within_window(self, crm_db):
        _, mem = crm_db
        # Insert a pending followup for today (should appear)
        mem.execute(
            "INSERT INTO customer_followups (customer_key, followup_date, reason, status) "
            "VALUES (?, date('now','localtime'), ?, 'pending')",
            ("CUST-1", "Urgent follow-up"),
        )
        # Insert a followup far in the future (should NOT appear — beyond 7 days)
        mem.execute(
            "INSERT INTO customer_followups (customer_key, followup_date, reason, status) "
            "VALUES (?, '2099-12-31', ?, 'pending')",
            ("CUST-2", "Future task"),
        )
        # Insert a completed followup for today (should NOT appear)
        mem.execute(
            "INSERT INTO customer_followups (customer_key, followup_date, reason, status) "
            "VALUES (?, date('now','localtime'), ?, 'done')",
            ("CUST-3", "Already done"),
        )
        mem.commit()

        result = customer_crm.pending_followups()
        assert len(result) == 1
        assert result[0]["customer_key"] == "CUST-1"


# ---------------------------------------------------------------------------
# customer_profile
# ---------------------------------------------------------------------------

class TestCustomerProfile:

    def test_profile_aggregates_all_data(self, crm_db):
        _, mem = crm_db
        customer_crm.add_note("CUST-1", "Good buyer")
        customer_crm.add_tag("CUST-1", "VIP")
        customer_crm.add_followup("CUST-1", "2026-07-01", "Send coupon")

        # Add an order for this customer
        mem.execute(
            "INSERT INTO orders (buyer_name, total_amount, order_date) VALUES (?,?,?)",
            ("CUST-1", 500.0, "2026-06-20"),
        )
        mem.commit()

        profile = customer_crm.customer_profile("CUST-1")

        assert profile["customer_key"] == "CUST-1"
        assert len(profile["notes"]) == 1
        assert profile["tags"] == ["VIP"]
        assert len(profile["followups"]) == 1
        assert profile["orders"] == 1
        assert profile["total_spent"] == 500.0

    def test_profile_empty_customer(self, crm_db):
        profile = customer_crm.customer_profile("NOBODY")
        assert profile["customer_key"] == "NOBODY"
        assert profile["notes"] == []
        assert profile["tags"] == []
        assert profile["followups"] == []
        assert profile["orders"] == 0


# ---------------------------------------------------------------------------
# all_customers_with_data
# ---------------------------------------------------------------------------

class TestAllCustomersWithData:

    def test_lists_customers_with_any_crm_data(self, crm_db):
        customer_crm.add_note("CUST-A", "A note")
        customer_crm.add_tag("CUST-B", "VIP")
        customer_crm.add_followup("CUST-C", "2026-07-01")

        result = customer_crm.all_customers_with_data()
        keys = [r["customer_key"] for r in result]
        assert "CUST-A" in keys
        assert "CUST-B" in keys
        assert "CUST-C" in keys

    def test_empty_when_no_data(self, crm_db):
        result = customer_crm.all_customers_with_data()
        assert result == []


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------

class TestStats:

    def test_returns_correct_counts(self, crm_db):
        customer_crm.add_note("CUST-1", "N1")
        customer_crm.add_note("CUST-1", "N2")
        customer_crm.add_tag("CUST-1", "VIP")
        customer_crm.add_followup("CUST-1", "2026-07-01")

        result = customer_crm.stats()
        assert result["notes"] == 2
        assert result["tags"] == 1
        assert result["followups_pending"] == 1
        assert result["customers_tracked"] == 1

    def test_zero_counts_when_empty(self, crm_db):
        result = customer_crm.stats()
        assert result["notes"] == 0
        assert result["tags"] == 0
        assert result["followups_pending"] == 0
        assert result["customers_tracked"] == 0
