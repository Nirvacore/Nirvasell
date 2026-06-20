"""Automation Rules — if/then without coding.

"Stock < 5 → LINE alert"
"Return rate > 5% → flag product"
Set it once, forget it."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import auto_rules as ar
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Auto Rules",
                   page_icon="⚙", layout="wide")
apply_theme()
require_auth()
db.init()
ar.init()
render_sidebar()

page_header(icon="⚙", title=t("rule.title"), subtitle=t("rule.caption"))


# ---- KPI overview -----------------------------------------------------------

rs = ar.stats()

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("rule.kpi_total"), str(rs["total"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("rule.kpi_active"), str(rs["active"]),
        hint="", hint_tone="ok",
    )
with k3:
    metric_with_hint(
        t("rule.kpi_fired"), str(rs["total_fires"]),
        hint="", hint_tone="info",
    )


# ---- Create rule -------------------------------------------------------------

st.divider()
with st.expander(t("rule.add_title"), expanded=rs["total"] == 0):
    with st.form("create_rule"):
        n_name = st.text_input(t("rule.f_name") + " *", placeholder=t("rule.name_placeholder"))

        c1, c2 = st.columns(2)
        with c1:
            trigger_keys = list(ar.TRIGGERS.keys())
            n_trigger = st.selectbox(
                t("rule.f_trigger"),
                trigger_keys,
                format_func=lambda k: ar.TRIGGERS[k]["icon"] + " " + ar.TRIGGERS[k]["label"],
            )
        with c2:
            action_keys = list(ar.ACTIONS.keys())
            n_action = st.selectbox(
                t("rule.f_action"),
                action_keys,
                format_func=lambda k: ar.ACTIONS[k]["icon"] + " " + ar.ACTIONS[k]["label"],
            )

        # Condition config based on trigger type
        condition = {}
        if n_trigger == "low_stock":
            threshold = st.number_input(
                t("rule.f_threshold"), min_value=1, value=5, step=1,
            )
            condition = {"threshold": threshold}
        elif n_trigger == "high_return":
            threshold_pct = st.number_input(
                t("rule.f_threshold_pct"), min_value=1.0, value=5.0, step=0.5,
            )
            condition = {"threshold_pct": threshold_pct}
        elif n_trigger == "vip_order":
            min_orders = st.number_input(
                t("rule.f_min_orders"), min_value=2, value=5,
            )
            condition = {"min_orders": min_orders}

        # Action config
        action_config = {}
        if n_action == "line_notify":
            msg = st.text_input(
                t("rule.f_message"),
                placeholder=t("rule.message_ph"),
            )
            action_config = {"message": msg}

        if st.form_submit_button(t("rule.add_btn"), type="primary"):
            if n_name.strip():
                ar.add_rule(n_name.strip(), n_trigger, condition,
                           n_action, action_config)
                toast(t("rule.added"), icon="✓")
                st.rerun()
            else:
                st.warning(t("rule.need_name"))


# ---- Quick templates ---------------------------------------------------------

st.divider()
st.markdown("### ⚡ " + t("rule.templates_title"))
st.caption(t("rule.templates_help"))

templates = [
    {
        "name": t("rule.tpl_low_stock"),
        "trigger": "low_stock",
        "condition": {"threshold": 5},
        "action": "line_notify",
        "action_config": {"message": t("rule.tpl_low_stock_msg")},
    },
    {
        "name": t("rule.tpl_high_return"),
        "trigger": "high_return",
        "condition": {"threshold_pct": 5},
        "action": "flag_product",
        "action_config": {},
    },
    {
        "name": t("rule.tpl_vip"),
        "trigger": "vip_order",
        "condition": {"min_orders": 5},
        "action": "line_notify",
        "action_config": {"message": t("rule.tpl_vip_msg")},
    },
    {
        "name": t("rule.tpl_daily"),
        "trigger": "daily_summary",
        "condition": {},
        "action": "line_notify",
        "action_config": {"message": t("rule.tpl_daily_msg")},
    },
]

tcols = st.columns(len(templates))
for i, tmpl in enumerate(templates):
    with tcols[i]:
        trig_info = ar.TRIGGERS.get(tmpl["trigger"], {})
        act_info = ar.ACTIONS.get(tmpl["action"], {})
        if st.button(
            tmpl["name"],
            key="_tmpl_" + str(i),
            type="tertiary",
            use_container_width=True,
        ):
            ar.add_rule(
                tmpl["name"], tmpl["trigger"], tmpl["condition"],
                tmpl["action"], tmpl["action_config"],
            )
            toast(t("rule.added"), icon="✓")
            st.rerun()


# ---- Rule list ---------------------------------------------------------------

rules = ar.all_rules()
if rules:
    st.divider()
    st.markdown("### " + t("rule.list_title"))

    for rule in rules:
        enabled = rule.get("enabled", True)
        trig = ar.TRIGGERS.get(rule["trigger_type"], {})
        act = ar.ACTIONS.get(rule["action_type"], {})
        fire_count = rule.get("fire_count", 0)
        last = (rule.get("last_fired") or "—")[:16]

        e_badge = "🟢" if enabled else "⏸"

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;justify-content:space-between'>"
                "<div>" + e_badge + " <strong>" + (rule.get("name") or "—") + "</strong></div>"
                "<div style='color:#9a9485;font-size:12px'>"
                + t("rule.fires_line", n=str(fire_count), when=last) + "</div></div>"
                "<div style='font-size:12px;color:#7a7569;margin-top:4px'>"
                + trig.get("icon", "") + " " + trig.get("label", rule["trigger_type"]) +
                " → " + act.get("icon", "") + " " + act.get("label", rule["action_type"]) +
                "</div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                toggle_icon = "⏸" if enabled else "▶"
                if st.button(toggle_icon, key="_rt_" + str(rule["id"]),
                             type="tertiary"):
                    ar.toggle_rule(rule["id"], not enabled)
                    st.rerun()
            with bc2:
                if st.button("▶️", key="_rr_" + str(rule["id"]),
                             type="tertiary", help=t("rule.run_now")):
                    if rule["trigger_type"] == "low_stock":
                        fired = ar.evaluate_low_stock()
                        toast(t("rule.fired", n=len(fired)), icon="🔥")
                    elif rule["trigger_type"] == "high_return":
                        fired = ar.evaluate_high_return()
                        toast(t("rule.fired", n=len(fired)), icon="🔥")
                    st.rerun()
            with bc3:
                if st.button("🗑", key="_rd_" + str(rule["id"]),
                             type="tertiary"):
                    ar.delete_rule(rule["id"])
                    st.rerun()
