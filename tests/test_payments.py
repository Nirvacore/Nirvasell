"""Tests for payments.py — PromptPay QR, Stripe link, donation log."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

import payments


# ---------------------------------------------------------------------------
# Helpers — in-memory SQLite
# ---------------------------------------------------------------------------

_mem_db: sqlite3.Connection | None = None


class _ConnWrapper:
    """Thin proxy that forwards lastrowid from the most recent cursor."""

    def __init__(self, real_conn: sqlite3.Connection):
        self._conn = real_conn
        self.lastrowid: int | None = None

    def execute(self, sql, params=()):
        cur = self._conn.execute(sql, params)
        self.lastrowid = cur.lastrowid
        return cur

    def executescript(self, sql):
        return self._conn.executescript(sql)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    @property
    def row_factory(self):
        return self._conn.row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._conn.row_factory = value


@contextmanager
def _mem_conn():
    global _mem_db
    if _mem_db is None:
        _mem_db = sqlite3.connect(":memory:")
        _mem_db.row_factory = sqlite3.Row
        _mem_db.execute("PRAGMA foreign_keys = ON")
    wrapper = _ConnWrapper(_mem_db)
    try:
        yield wrapper
        _mem_db.commit()
    except Exception:
        _mem_db.rollback()
        raise


@pytest.fixture(autouse=True)
def _fresh_db():
    """Provide a clean in-memory database for every test."""
    global _mem_db
    _mem_db = None
    with patch("db.conn", _mem_conn):
        payments.init()
        yield


# ---------------------------------------------------------------------------
# _tlv
# ---------------------------------------------------------------------------

class TestTlv:
    def test_basic(self):
        result = payments._tlv("00", "01")
        assert result == "000201"

    def test_longer_value(self):
        result = payments._tlv("29", "ABCDE")
        assert result == "2905ABCDE"

    def test_empty_value(self):
        result = payments._tlv("58", "")
        assert result == "5800"

    def test_long_value_length_padded(self):
        val = "A" * 5
        result = payments._tlv("10", val)
        assert result == "1005AAAAA"


# ---------------------------------------------------------------------------
# _crc16
# ---------------------------------------------------------------------------

class TestCrc16:
    def test_returns_4_char_hex(self):
        result = payments._crc16("test")
        assert len(result) == 4
        # Should be uppercase hex
        assert result == result.upper()
        int(result, 16)  # Should not raise

    def test_deterministic(self):
        a = payments._crc16("hello world")
        b = payments._crc16("hello world")
        assert a == b

    def test_different_inputs_differ(self):
        a = payments._crc16("hello")
        b = payments._crc16("world")
        assert a != b

    def test_empty_string(self):
        result = payments._crc16("")
        assert len(result) == 4


# ---------------------------------------------------------------------------
# _normalize_promptpay_id
# ---------------------------------------------------------------------------

class TestNormalizePromptpayId:
    def test_phone_10_digits(self):
        result = payments._normalize_promptpay_id("0812345678")
        assert result is not None
        tag, value = result
        assert tag == "01"  # phone
        assert value == "0066812345678"  # 13 digits
        assert len(value) == 13

    def test_national_id_13_digits(self):
        result = payments._normalize_promptpay_id("1234567890123")
        assert result is not None
        tag, value = result
        assert tag == "02"  # NID
        assert value == "1234567890123"

    def test_ewallet_15_digits(self):
        result = payments._normalize_promptpay_id("123456789012345")
        assert result is not None
        tag, value = result
        assert tag == "03"
        assert value == "123456789012345"

    def test_strips_non_digits(self):
        result = payments._normalize_promptpay_id("081-234-5678")
        assert result is not None
        tag, value = result
        assert tag == "01"
        assert value == "0066812345678"

    def test_invalid_length(self):
        assert payments._normalize_promptpay_id("12345") is None
        assert payments._normalize_promptpay_id("12345678") is None

    def test_none_input(self):
        assert payments._normalize_promptpay_id(None) is None

    def test_empty_string(self):
        assert payments._normalize_promptpay_id("") is None

    def test_phone_must_start_with_zero(self):
        """10-digit number NOT starting with 0 is invalid."""
        result = payments._normalize_promptpay_id("1234567890")
        assert result is None


# ---------------------------------------------------------------------------
# promptpay_payload
# ---------------------------------------------------------------------------

class TestPromptpayPayload:
    def test_valid_phone_without_amount(self):
        payload = payments.promptpay_payload("0812345678")
        assert payload is not None
        assert isinstance(payload, str)
        # Static QR uses 11
        assert "010211" in payload
        # THB currency
        assert "53" in payload

    def test_valid_phone_with_amount(self):
        payload = payments.promptpay_payload("0812345678", amount=100.0)
        assert payload is not None
        # Dynamic QR uses 12
        assert "010212" in payload
        # Amount should appear
        assert "100.00" in payload

    def test_valid_nid(self):
        payload = payments.promptpay_payload("1234567890123")
        assert payload is not None

    def test_invalid_id_returns_none(self):
        result = payments.promptpay_payload("invalid")
        assert result is None

    def test_payload_ends_with_crc(self):
        payload = payments.promptpay_payload("0812345678")
        # Last 4 chars should be the CRC (hex digits)
        crc_part = payload[-4:]
        int(crc_part, 16)  # Should not raise

    def test_payload_contains_promptpay_aid(self):
        payload = payments.promptpay_payload("0812345678")
        assert "A000000677010111" in payload

    def test_payload_contains_country_code(self):
        payload = payments.promptpay_payload("0812345678")
        assert "5802TH" in payload

    def test_payload_contains_currency_thb(self):
        payload = payments.promptpay_payload("0812345678")
        assert "5303764" in payload

    def test_none_amount_is_static_qr(self):
        payload = payments.promptpay_payload("0812345678", amount=None)
        assert "010211" in payload

    def test_zero_amount_is_static_qr(self):
        """amount=0 is falsy, so should produce static QR (01=11)."""
        payload = payments.promptpay_payload("0812345678", amount=0)
        assert "010211" in payload


# ---------------------------------------------------------------------------
# promptpay_qr_png (best-effort — depends on qrcode library)
# ---------------------------------------------------------------------------

class TestPromptpayQrPng:
    def test_invalid_id_returns_none(self):
        result = payments.promptpay_qr_png("invalid")
        assert result is None

    def test_valid_id_returns_bytes_or_none(self):
        """Returns bytes if qrcode installed, None if not."""
        result = payments.promptpay_qr_png("0812345678")
        assert result is None or isinstance(result, bytes)

    def test_with_amount(self):
        result = payments.promptpay_qr_png("0812345678", amount=50.0)
        assert result is None or isinstance(result, bytes)


# ---------------------------------------------------------------------------
# get_settings
# ---------------------------------------------------------------------------

class TestGetSettings:
    def test_fallback_to_env_vars(self):
        """When user_settings import fails, falls back to env vars."""
        env = {
            "PROMPTPAY_ID": "0899999999",
            "PROMPTPAY_NAME": "Test Shop",
            "STRIPE_PAYMENT_LINK": "https://buy.stripe.com/test",
            "BUYMEACOFFEE_URL": "https://bmac.test",
            "GITHUB_SPONSORS_URL": "https://github.com/sponsors/test",
        }
        with patch.dict(os.environ, env, clear=False):
            # Force user_settings to fail
            with patch.dict("sys.modules", {"user_settings": None}):
                settings = payments.get_settings()
        assert settings["promptpay_id"] == "0899999999"
        assert settings["promptpay_name"] == "Test Shop"
        assert settings["stripe_link"] == "https://buy.stripe.com/test"
        assert settings["bmac_url"] == "https://bmac.test"
        assert settings["github_sponsors"] == "https://github.com/sponsors/test"

    def test_defaults_to_empty_strings(self):
        """When no env vars and user_settings fails, all values are empty."""
        clean_env = {k: "" for k in ["PROMPTPAY_ID", "PROMPTPAY_NAME",
                                      "STRIPE_PAYMENT_LINK", "BUYMEACOFFEE_URL",
                                      "GITHUB_SPONSORS_URL"]}
        with patch.dict(os.environ, clean_env, clear=False):
            with patch.dict("sys.modules", {"user_settings": None}):
                settings = payments.get_settings()
        assert settings["promptpay_id"] == ""
        assert settings["stripe_link"] == ""

    def test_returns_dict_with_expected_keys(self):
        with patch.dict("sys.modules", {"user_settings": None}):
            settings = payments.get_settings()
        expected = {"promptpay_id", "promptpay_name", "stripe_link", "bmac_url", "github_sponsors"}
        assert set(settings.keys()) == expected


# ---------------------------------------------------------------------------
# init (donations table)
# ---------------------------------------------------------------------------

class TestInit:
    def test_creates_donations_table(self):
        global _mem_db
        with patch("db.conn", _mem_conn):
            tables = {r[0] for r in _mem_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
        assert "donations" in tables

    def test_idempotent(self):
        with patch("db.conn", _mem_conn):
            payments.init()  # second call should not raise


# ---------------------------------------------------------------------------
# log_donation
# ---------------------------------------------------------------------------

class TestLogDonation:
    def test_basic_donation(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            did = payments.log_donation(amount=100, method="promptpay")
        assert isinstance(did, int)
        assert did >= 1

    def test_stores_correct_values(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(
                amount=500, method="stripe", currency="USD", note="Thanks!"
            )
            rows = payments.list_donations()
        assert len(rows) == 1
        assert rows[0]["amount"] == 500
        assert rows[0]["method"] == "stripe"
        assert rows[0]["currency"] == "USD"
        assert rows[0]["note"] == "Thanks!"

    def test_method_is_lowered_and_stripped(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(amount=100, method="  PromptPay  ")
            rows = payments.list_donations()
        assert rows[0]["method"] == "promptpay"

    def test_note_is_stripped(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(amount=100, method="bmac", note="  nice  ")
            rows = payments.list_donations()
        assert rows[0]["note"] == "nice"

    def test_confirmed_defaults_to_zero(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(amount=100, method="promptpay")
            rows = payments.list_donations()
        assert rows[0]["confirmed"] == 0

    def test_default_currency_is_thb(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(amount=100, method="promptpay")
            rows = payments.list_donations()
        assert rows[0]["currency"] == "THB"

    def test_events_failure_does_not_break(self):
        """If events module fails, log_donation should still succeed."""
        mock_events = MagicMock()
        mock_events.log.side_effect = Exception("Event system down")
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": mock_events}):
            did = payments.log_donation(amount=100, method="promptpay")
        assert isinstance(did, int)


# ---------------------------------------------------------------------------
# list_donations
# ---------------------------------------------------------------------------

class TestListDonations:
    def test_empty_list(self):
        with patch("db.conn", _mem_conn):
            result = payments.list_donations()
        assert result == []

    def test_returns_list_of_dicts(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(amount=100, method="promptpay")
            result = payments.list_donations()
        assert isinstance(result, list)
        assert isinstance(result[0], dict)

    def test_limit_parameter(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            for i in range(10):
                payments.log_donation(amount=i * 10, method="promptpay")
            result = payments.list_donations(limit=3)
        assert len(result) == 3

    def test_returns_multiple(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(amount=100, method="promptpay")
            payments.log_donation(amount=200, method="stripe")
            result = payments.list_donations()
        assert len(result) == 2
        amounts = {r["amount"] for r in result}
        assert amounts == {100, 200}


# ---------------------------------------------------------------------------
# confirm
# ---------------------------------------------------------------------------

class TestConfirm:
    def test_confirm_donation(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            did = payments.log_donation(amount=100, method="promptpay")
            result = payments.confirm(did)
        assert result is True
        with patch("db.conn", _mem_conn):
            rows = payments.list_donations()
        assert rows[0]["confirmed"] == 1

    def test_confirm_nonexistent_returns_false(self):
        with patch("db.conn", _mem_conn):
            result = payments.confirm(99999)
        assert result is False

    def test_double_confirm_is_idempotent(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            did = payments.log_donation(amount=100, method="promptpay")
            payments.confirm(did)
            result = payments.confirm(did)
        assert result is True


# ---------------------------------------------------------------------------
# total_received
# ---------------------------------------------------------------------------

class TestTotalReceived:
    def test_empty_returns_empty_dict(self):
        with patch("db.conn", _mem_conn):
            result = payments.total_received()
        assert result == {}

    def test_confirmed_only_default(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            d1 = payments.log_donation(amount=100, method="promptpay")
            d2 = payments.log_donation(amount=200, method="stripe")
            payments.confirm(d1)
            # d2 is unconfirmed
            result = payments.total_received(confirmed_only=True)
        assert result.get("THB", 0) == 100

    def test_all_donations(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            payments.log_donation(amount=100, method="promptpay")
            payments.log_donation(amount=200, method="stripe")
            result = payments.total_received(confirmed_only=False)
        assert result["THB"] == 300

    def test_multi_currency(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            d1 = payments.log_donation(amount=100, method="promptpay", currency="THB")
            d2 = payments.log_donation(amount=50, method="stripe", currency="USD")
            payments.confirm(d1)
            payments.confirm(d2)
            result = payments.total_received()
        assert result["THB"] == 100
        assert result["USD"] == 50

    def test_total_received_returns_float_values(self):
        with patch("db.conn", _mem_conn), \
             patch.dict("sys.modules", {"events": MagicMock()}):
            d1 = payments.log_donation(amount=99.50, method="promptpay")
            payments.confirm(d1)
            result = payments.total_received()
        assert isinstance(result["THB"], float)
        assert result["THB"] == 99.50
