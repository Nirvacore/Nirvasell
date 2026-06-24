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


def promo_type_label(promo_type: str) -> str:
    key = f"promo.type_{promo_type}"
    if key in STRINGS:
        return t(key)
    return promo_type.replace("_", " ").title()


def promo_status_label(status: str) -> str:
    key = f"promo.status_{status}"
    if key in STRINGS:
        return t(key)
    return status.replace("_", " ").title()


def loyalty_reward_name(reward_id: str) -> str:
    return _lookup("loy.reward", reward_id)


def peng_type_label(promo_type: str) -> str:
    return _lookup("peng.type", promo_type)


def peng_discount_label(discount_type: str) -> str:
    return _lookup("peng.disc", discount_type)


def cal_post_type_label(post_type: str) -> str:
    key = f"cal.type_{post_type}"
    if key in STRINGS:
        return t(key)
    return post_type.replace("_", " ").title()


def cal_post_status_label(status: str) -> str:
    slug = {"published": "posted"}.get(status, status)
    key = f"cal.status_{slug}"
    if key in STRINGS:
        return t(key)
    return status.replace("_", " ").title()


def ws_tier_label(tier_key: str) -> str:
    return _lookup("ws.tier", tier_key)


def task_priority_label(priority: str) -> str:
    return _lookup("task.priority", priority)


def task_status_label(status: str) -> str:
    return _lookup("task.status", status)


def flash_status_label(status: str) -> str:
    return _lookup("flash.status", status)


def flash_discount_label(discount_type: str) -> str:
    return _lookup("flash.disc", discount_type)


def goal_type_label(goal_type: str) -> str:
    return _lookup("goal.type", goal_type)


def goal_type_unit(goal_type: str) -> str:
    key = f"goal.unit_{goal_type}"
    if key in STRINGS:
        return t(key)
    return ""


def goal_period_label(period: str) -> str:
    return _lookup("goal.period", period)


def inf_status_label(status: str) -> str:
    return _lookup("inf.status", status)


def inf_commission_label(commission_type: str) -> str:
    return _lookup("inf.comm", commission_type)


def note_type_label(note_type: str) -> str:
    return _lookup("nt.type", note_type)


def note_priority_label(priority: str) -> str:
    return _lookup("nt.priority", priority)


def crm_note_type_label(note_type: str) -> str:
    return _lookup("crm.type", note_type)


def crm_tag_label(tag: str) -> str:
    key = f"crm.tag_{tag}"
    if key in STRINGS:
        return t(key)
    return tag


def rev_status_label(status: str) -> str:
    return _lookup("rev.status", status)


def rule_trigger_label(trigger: str) -> str:
    return _lookup("rule.trig", trigger)


def rule_action_label(action: str) -> str:
    return _lookup("rule.act", action)


def channel_fee_label(platform: str) -> str:
    fee = PLATFORM_FEE_KEYS.get(platform)
    if fee:
        return t(fee)
    return t("ch.fee_no_gp")


PLATFORM_FEE_KEYS = {
    "shopee": "ch.fee_shopee",
    "lazada": "ch.fee_lazada",
    "tiktok_shop": "ch.fee_tiktok_shop",
}


def msg_cat_label(cat: str) -> str:
    return _lookup("msg.cat", cat)


def tmpl_cat_label(cat: str) -> str:
    return _lookup("tmpl.cat", cat)


def voucher_tpl_label(key: str) -> str:
    return _lookup("vouch.tpl", key)


def review_sentiment_label(rating: int) -> str:
    key = f"rt.sent_{rating}"
    if key in STRINGS:
        return t(key)
    return str(rating)


def seg_rfm_label(segment: str) -> str:
    return _lookup("seg.rfm", segment)


def seg_rfm_desc(segment: str) -> str:
    key = f"seg.rfm_desc_{segment}"
    if key in STRINGS:
        return t(key)
    return ""


def seg_tag_label(tag: str) -> str:
    key = f"seg.tag_{tag.lower()}"
    if key in STRINGS:
        return t(key)
    return tag


def rfm_segment_label(segment: str) -> str:
    return _lookup("rfm.seg", segment)


def rfm_action_label(action: str) -> str:
    return _lookup("rfm.action", action.replace("-", "_"))


def cod_status_label(status: str) -> str:
    key = f"cod.status_{status}"
    if key in STRINGS:
        return t(key)
    return status.replace("_", " ").title()


def sup_cat_label(cat: str) -> str:
    return _lookup("sup.cat", cat)


def sup_term_label(term: str) -> str:
    return _lookup("sup.term", term)
