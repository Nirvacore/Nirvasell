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


def field_label(field: str) -> str:
    return _lookup("outfield", field)


def loyalty_tier(tier: str) -> str:
    key = f"loy.tier_{tier}"
    if key in STRINGS:
        return t(key)
    return tier.replace("_", " ").title()


def po_status(status: str) -> str:
    key = f"po.status_{status}"
    if key in STRINGS:
        return t(key)
    return status.replace("_", " ").title()


def notif_kind_name(kind: str) -> str:
    key = f"notif.kind_{kind}"
    if key in STRINGS:
        return t(key)
    return kind.replace("_", " ").title()


def budget_category(cat: str) -> str:
    key = f"bgt.cat_{cat}"
    if key in STRINGS:
        return t(key)
    return cat.replace("_", " ").title()


def content_type_label(content_type: str) -> str:
    return _lookup("ccal.type", content_type)


def content_status_label(status: str) -> str:
    return _lookup("ccal.status", status)


def live_promo_label(slug: str) -> str:
    return _lookup("live.promo", slug)


def alert_kind_name(kind: str) -> str:
    return _lookup("alrt.kind", kind)


def brief_task_text(task: dict) -> str:
    key = task.get("task_key", "")
    if not key:
        return task.get("task", "")
    fmt = {k: task[k] for k in ("count",) if k in task}
    return t(f"brief.task_{key}", **fmt)


def brief_alert_text(alert: dict) -> str:
    key = alert.get("alert_key", "")
    if not key:
        return alert.get("msg", "")
    fmt = {k: alert[k] for k in ("count", "rate") if k in alert}
    return t(f"brief.alert_{key}", **fmt)
