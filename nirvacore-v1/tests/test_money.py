"""Money value-object behaviour."""
from __future__ import annotations

from decimal import Decimal

import pytest

from nirvacore.domain.money import Money


def test_normalises_to_two_dp() -> None:
    assert Money.of("100").amount == Decimal("100.00")
    assert Money.of("100.005").amount == Decimal("100.01")  # half-up


def test_multiply_by_hours() -> None:
    rate = Money.of("75")
    assert (rate * Decimal("8.50")).amount == Decimal("637.50")


def test_add_same_currency() -> None:
    assert (Money.of("10") + Money.of("5")).amount == Decimal("15.00")


def test_add_mismatched_currency_raises() -> None:
    with pytest.raises(ValueError):
        Money.of("10", "THB") + Money.of("5", "USD")


def test_zero() -> None:
    assert Money.zero().amount == Decimal("0.00")
    assert Money.zero("USD").currency == "USD"
