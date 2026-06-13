"""Payroll domain.

A :class:`Payroll` is the result of running pay for a period: one
:class:`Payslip` per employee, computed from worked hours × hourly rate. The
MVP computes gross pay only (no overtime/deductions yet — Rule 5); those slot
in here later without touching the application or persistence layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .ids import EmployeeId
from .money import Money


@dataclass(frozen=True, slots=True)
class Payslip:
    employee_id: EmployeeId
    employee_name: str
    hours: Decimal
    hourly_rate: Money
    gross_pay: Money

    @classmethod
    def compute(
        cls,
        employee_id: EmployeeId,
        employee_name: str,
        hours: Decimal,
        hourly_rate: Money,
    ) -> Payslip:
        return cls(
            employee_id=employee_id,
            employee_name=employee_name,
            hours=hours,
            hourly_rate=hourly_rate,
            gross_pay=hourly_rate * hours,
        )


@dataclass(frozen=True, slots=True)
class Payroll:
    start: datetime
    end: datetime
    currency: str
    slips: tuple[Payslip, ...]

    @property
    def total_gross(self) -> Money:
        total = Money.zero(self.currency)
        for slip in self.slips:
            total = total + slip.gross_pay
        return total
