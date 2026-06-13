"""Money value object.

Immutable, currency-aware, and built on :class:`~decimal.Decimal` so payroll
arithmetic is exact — never float. The MVP operates in a single currency (THB)
but the type carries currency so mixing is caught, not silently wrong.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

_CENTS = Decimal("0.01")
DEFAULT_CURRENCY = "THB"


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str = DEFAULT_CURRENCY

    def __post_init__(self) -> None:
        # Normalise to 2 decimal places at the boundary.
        object.__setattr__(
            self, "amount", self.amount.quantize(_CENTS, rounding=ROUND_HALF_UP)
        )

    @classmethod
    def of(cls, amount: str | int | Decimal, currency: str = DEFAULT_CURRENCY) -> Money:
        return cls(Decimal(str(amount)), currency)

    @classmethod
    def zero(cls, currency: str = DEFAULT_CURRENCY) -> Money:
        return cls(Decimal("0"), currency)

    def _same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"currency mismatch: {self.currency} vs {other.currency}"
            )

    def __add__(self, other: Money) -> Money:
        self._same_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, qty: Decimal | int) -> Money:
        return Money(self.amount * Decimal(str(qty)), self.currency)

    __rmul__ = __mul__

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
