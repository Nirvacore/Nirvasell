"""Shared inline i18n helpers — Thai source of truth via i18n.t()."""
from i18n import t, STRINGS

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


def _lookup(prefix: str, slug: str, *, fallback: str | None = None) -> str:
    key = f"{prefix}.{slug}"
    if key in STRINGS:
        return t(key)
    if fallback is not None:
        return fallback
    return slug.replace("_", " ").title()


def platform_name(slug: str | None) -> str:
    if not slug:
        return t("common.platform_direct")
    if slug == "direct":
        return t("common.platform_direct")
    return _lookup("plat", slug)


_CARRIER_SLUGS = {"j&t": "j_and_t"}


def carrier_name(slug: str) -> str:
    return _lookup("carrier", _CARRIER_SLUGS.get(slug, slug))


def expense_category(cat: str) -> str:
    key = f"exp.cat_{cat}"
    if key in STRINGS:
        return t(key)
    return cat.replace("_", " ").title()


def payment_type_name(ptype: str, *, icon: bool = True) -> str:
    if icon:
        key = f"cod.type_{ptype}"
    else:
        key = f"cod.payment_{ptype}"
    if key in STRINGS:
        return t(key)
    return ptype.upper()
