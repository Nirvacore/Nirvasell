"""Promotions — flash sales, coupons, percentage and fixed discounts."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date, timedelta
import db
import promotions as pm
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import promo_type_label, promo_status_label

st.set_page_config(page_title="nirva.sell · Promotions",
                   page_icon="🎯", layout="wide")
apply_theme()
require_auth()
db.init()
pm.init()
render_sidebar()

page_header(icon="🎯", title=t("promo.title"), subtitle=t("promo.caption"))

s = pm.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("🎯 " + t("promo.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("✅ " + t("promo.kpi_active"), str(s["active"]),
                     hint="", hint_tone="ok" if s["active"] > 0 else "info")
with k3:
    metric_with_hint("🔢 " + t("promo.kpi_uses"), str(s["total_uses"]),
                     hint="", hint_tone="info")

# ---- Create promo -----------------------------------------------------------
st.divider()
with st.expander(t("promo.create_title"), expanded=s["total"] == 0):
    with st.form("create_promo"):
        pc1, pc2 = st.columns(2)
        with pc1:
            promo_title = st.text_input(t("promo.f_title"),
                                        placeholder=t("promo.title_ph"))
            promo_type = st.selectbox(
                t("promo.f_type"),
                list(pm.PROMO_TYPES.keys()),
                format_func=lambda k: (
                    pm.PROMO_TYPES[k]["icon"] + " " + promo_type_label(k)
                ),
            )
            discount_value = st.number_input(
                t("promo.f_value"),
                min_value=0.0, value=10.0, step=5.0,
            )
        with pc2:
            coupon_code = st.text_input(t("promo.f_coupon"),
                                        placeholder=t("promo.coupon_ph"))
            min_order = st.number_input(t("promo.f_min_order"),
                                        min_value=0.0, value=0.0, step=50.0)
            col_s, col_e = st.columns(2)
            with col_s:
                start_dt = st.date_input(t("promo.f_start"),
                                         value=date.today())
            with col_e:
                end_dt = st.date_input(t("promo.f_end"),
                                       value=date.today() + timedelta(days=7))
        promo_notes = st.text_input(t("promo.f_notes"), placeholder="")
        if st.form_submit_button(t("promo.create_btn"), type="primary"):
            if promo_title.strip():
                pm.create(
                    promo_type=promo_type,
                    title=promo_title.strip(),
                    discount_value=discount_value,
                    min_order=min_order,
                    coupon_code=coupon_code.strip().upper(),
                    start_dt=str(start_dt),
                    end_dt=str(end_dt),
                    notes=promo_notes.strip(),
                )
                toast(t("promo.created"), icon="✓")
                st.rerun()

# ---- Filter -----------------------------------------------------------------
st.divider()
filter_status = st.segmented_control(
    t("promo.f_status"),
    ["all", "active", "draft", "paused", "ended"],
    format_func=lambda x: {
        "all": "🔍 " + t("promo.all"),
        "active": "✅ " + t("promo.status_active"),
        "draft": "📝 " + t("promo.status_draft"),
        "paused": "⏸ " + t("promo.status_paused"),
        "ended": "⏹ " + t("promo.status_ended"),
    }.get(x, x),
    default="all",
    key="_pm_fs",
)

promos = pm.all_promos(status=None if filter_status == "all" else filter_status)

if not promos:
    st.info(t("promo.empty"))
    st.stop()

for p in promos:
    p_info = p["promo_info"]
    s_info = p["status_info"]
    s_color = s_info.get("color", "#7a7569")

    disc_str = (
        str(int(p["discount_value"])) + "%"
        if p["promo_type"] in ("percentage_off", "flash_sale")
        else "฿{:,.0f}".format(p["discount_value"])
        if p["promo_type"] == "fixed_off"
        else "—"
    )
    code_str = (
        t("promo.code_line", code=p["coupon_code"])
        if p.get("coupon_code") else ""
    )

    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:10px 14px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-left:4px solid " + s_color + ";"
        "border-radius:8px;background:white;margin-bottom:4px'>"
        "<div>" + p_info["icon"] + " <strong>" + p["title"] + "</strong>"
        "<span style='font-size:11px;color:#9a9485;margin-left:6px'>"
        + disc_str + code_str + "</span></div>"
        "<div style='display:flex;gap:10px;align-items:center'>"
        "<span style='font-size:12px'>" +
        t("promo.use_count", n=p["use_count"]) + "</span>"
        "<span style='font-size:12px;font-weight:600;color:" + s_color + "'>"
        + s_info["icon"] + " " + promo_status_label(p["status"]) + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    ac1, ac2, ac3, ac4 = st.columns(4)
    with ac1:
        if p["status"] == "draft" and st.button(
            t("promo.activate_btn"), key="_pa_" + str(p["id"]), type="tertiary"
        ):
            pm.activate(p["id"])
            toast(t("promo.activated"), icon="✅")
            st.rerun()
    with ac2:
        if p["status"] == "active" and st.button(
            t("promo.pause_btn"), key="_pp_" + str(p["id"]), type="tertiary"
        ):
            pm.pause(p["id"])
            st.rerun()
    with ac3:
        if p["status"] in ("active", "paused") and st.button(
            t("promo.end_btn"), key="_pe_" + str(p["id"]), type="tertiary"
        ):
            pm.end(p["id"])
            st.rerun()
    with ac4:
        if p["status"] == "draft" and st.button(
            t("promo.delete_btn"), key="_pd_" + str(p["id"]), type="tertiary"
        ):
            pm.delete(p["id"])
            st.rerun()
