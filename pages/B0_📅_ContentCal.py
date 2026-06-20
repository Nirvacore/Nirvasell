"""Content Calendar — plan posts, live sells, and promotions by date."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date, datetime
import db
import content_calendar as cc
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Content Calendar",
                   page_icon="📅", layout="wide")
apply_theme()
require_auth()
db.init()
cc.init()
render_sidebar()

page_header(icon="📅", title=t("ccal.title"), subtitle=t("ccal.caption"))

s = cc.stats()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📋 " + t("ccal.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("📅 " + t("ccal.kpi_this_month"), str(s["this_month"]),
                     hint="", hint_tone="info")
with k3:
    metric_with_hint("✅ " + t("ccal.kpi_done"), str(s["done"]),
                     hint="", hint_tone="ok")
with k4:
    metric_with_hint("💰 " + t("ccal.kpi_revenue"),
                     "฿{:,.0f}".format(s["total_revenue"]),
                     hint="", hint_tone="ok")

# ---- Add content item -------------------------------------------------------
st.divider()
with st.expander(t("ccal.add_title"), expanded=False):
    with st.form("add_content"):
        ad1, ad2, ad3 = st.columns(3)
        with ad1:
            sched_date = st.date_input(t("ccal.f_date"), value=date.today())
            sched_time = st.text_input(t("ccal.f_time"), placeholder="19:00",
                                       key="_cc_time")
        with ad2:
            ct = st.selectbox(
                t("ccal.f_type"),
                list(cc.CONTENT_TYPES.keys()),
                format_func=lambda k: cc.CONTENT_TYPES[k]["icon"] + " " +
                cc.CONTENT_TYPES[k]["label_th"],
                key="_cc_type",
            )
            platform = st.selectbox(t("ccal.f_platform"), cc.PLATFORMS,
                                    key="_cc_plat")
        with ad3:
            target_rev = st.number_input(t("ccal.f_target"), min_value=0.0,
                                         value=0.0, step=500.0)

        title = st.text_input(t("ccal.f_title") + " *",
                              placeholder=t("ccal.title_ph"))
        desc = st.text_input(t("ccal.f_desc"), placeholder=t("ccal.desc_ph"))

        if st.form_submit_button(t("ccal.add_btn"), type="primary"):
            if title.strip():
                cc.add(
                    scheduled_date=str(sched_date),
                    title=title.strip(),
                    content_type=ct,
                    platform=platform,
                    scheduled_time=sched_time.strip(),
                    description=desc.strip(),
                    target_revenue=target_rev,
                )
                toast(t("ccal.added"), icon="✓")
                st.rerun()
            else:
                st.warning(t("ccal.need_title"))

# ---- Upcoming items ---------------------------------------------------------
upcoming = cc.upcoming(7)
if upcoming:
    st.divider()
    st.markdown("### 🔔 " + t("ccal.upcoming_title"))
    for item in upcoming:
        ct_info = cc.CONTENT_TYPES.get(item["content_type"], {})
        icon = ct_info.get("icon", "📌")
        label = ct_info.get("label_th", item["content_type"])

        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "align-items:center;padding:8px 14px;"
            "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span>" + icon + " <strong>" + item["title"] + "</strong>"
            " <span style='color:#9a9485;font-size:11px'>"
            + label + " · " + (item.get("platform") or "") + "</span></span>"
            "<span style='font-size:12px;color:#7a7569'>"
            + item["scheduled_date"] +
            (" " + item["scheduled_time"] if item.get("scheduled_time") else "") +
            "</span></div>",
            unsafe_allow_html=True,
        )

# ---- Weekly view ------------------------------------------------------------
st.divider()
st.markdown("### 📆 " + t("ccal.week_title"))

week_date = st.date_input(t("ccal.f_week"), value=date.today(),
                          key="_cc_week")
week = cc.week_items(str(week_date))

DAYS_TH = [
    t("ccal.day_mon"), t("ccal.day_tue"), t("ccal.day_wed"),
    t("ccal.day_thu"), t("ccal.day_fri"), t("ccal.day_sat"), t("ccal.day_sun"),
]
day_cols = st.columns(7)
for i, (day_str, items) in enumerate(week.items()):
    d_obj = datetime.strptime(day_str, "%Y-%m-%d")
    is_today = day_str == date.today().strftime("%Y-%m-%d")
    header_bg = "rgba(77,108,92,0.1)" if is_today else "transparent"

    with day_cols[i]:
        st.markdown(
            "<div style='text-align:center;padding:6px;"
            "background:" + header_bg + ";border-radius:6px;"
            "margin-bottom:4px'>"
            "<div style='font-weight:600;font-size:12px'>"
            + DAYS_TH[i] + "</div>"
            "<div style='font-size:11px;color:#7a7569'>"
            + str(d_obj.day) + "</div></div>",
            unsafe_allow_html=True,
        )

        if items:
            for item in items:
                ct_info = cc.CONTENT_TYPES.get(item["content_type"], {})
                s_info = cc.STATUSES.get(item["status"], {})
                st.markdown(
                    "<div style='font-size:11px;padding:4px 6px;"
                    "background:white;border:0.5px solid rgba(40,30,20,0.1);"
                    "border-radius:4px;margin-bottom:3px;'>"
                    + ct_info.get("icon", "📌") + " " + item["title"][:15] +
                    " " + s_info.get("icon", "") + "</div>",
                    unsafe_allow_html=True,
                )

            for item in items:
                sc1, sc2 = st.columns([3, 1])
                with sc2:
                    new_status = st.selectbox(
                        t("ccal.f_status"),
                        list(cc.STATUSES.keys()),
                        index=list(cc.STATUSES.keys()).index(
                            item.get("status", "planned")
                        ),
                        key="_ccs_" + str(item["id"]),
                        label_visibility="collapsed",
                        format_func=lambda k: cc.STATUSES[k]["icon"],
                    )
                    if new_status != item["status"]:
                        cc.update_status(item["id"], new_status)
                        st.rerun()
