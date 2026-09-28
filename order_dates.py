"""Canonical calendar handling for order evidence."""
from __future__ import annotations

from datetime import date, datetime
import re
from zoneinfo import ZoneInfo


_BANGKOK = ZoneInfo("Asia/Bangkok")
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_ISO_DATETIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,9})?(?:Z|[+-]\d{2}:\d{2})?$"
)


def order_business_date(value) -> date | None:
    """Return the Asia/Bangkok calendar date for bounded ISO order evidence.

    A date is already a business date. A naive datetime is explicitly local
    Bangkok time. An aware datetime is converted to Bangkok before its date is
    taken. Missing, malformed, or unbounded forms remain unknown.
    """
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        return value
    else:
        if value is None:
            return None
        raw = str(value).strip()
        if not raw:
            return None
        try:
            if _ISO_DATE.fullmatch(raw):
                parsed_date = date.fromisoformat(raw)
                return parsed_date if parsed_date.isoformat() == raw else None
            if not _ISO_DATETIME.fullmatch(raw):
                return None
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_BANGKOK)
    return parsed.astimezone(_BANGKOK).date()
