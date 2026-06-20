"""Shared inline i18n helpers — Thai source of truth via i18n.t()."""
from i18n import t

DAY_KEYS = (
    "analytics.sun",
    "analytics.mon",
    "analytics.tue",
    "analytics.wed",
    "analytics.thu",
    "analytics.fri",
    "analytics.sat",
)

DAY_KEYS_MON_FIRST = (
    "analytics.mon",
    "analytics.tue",
    "analytics.wed",
    "analytics.thu",
    "analytics.fri",
    "analytics.sat",
    "analytics.sun",
)


def day_name(dow: int) -> str:
    if 0 <= dow <= 6:
        return t(DAY_KEYS[dow])
    return str(dow)


def day_names_mon_first() -> list[str]:
    return [t(k) for k in DAY_KEYS_MON_FIRST]


def return_reason(reason: str) -> str:
    key = reason if reason else "other"
    return t("ret.reason_" + key)
