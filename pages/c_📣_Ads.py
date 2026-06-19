"""Ads ROI Tracker — every baht on ads, tracked.

Thai sellers spend 500-5000/day on FB & TikTok ads but rarely calculate
ROAS. This page makes it visible: which campaigns profit, which burn."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import ads_tracker as ads
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Ads",
                   page_icon="📣", layout="wide")
apply_theme()
require_auth()
db.init()
ads.init()
render_sidebar()

page_header(icon="📣", title=t("ads.title"), subtitle=t("ads.caption"))


# ---- KPI overview -----------------------------------------------------------

s = ads.stats()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    metric_with_hint(
        t("ads.kpi_campaigns"), str(s["total"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("ads.kpi_spent"), "{:,.0f}".format(s["total_spent"]),
        hint="", hint_tone="info",
    )
with k3:
    metric_with_hint(
        t("ads.kpi_revenue"), "{:,.0f}".format(s["total_revenue"]),
        hint="", hint_tone="info",
    )
with k4:
    roas_tone = "ok" if s["overall_roas"] >= 3 else ("warn" if s["overall_roas"] >= 1 else "danger")
    metric_with_hint(
        "ROAS", "{:.1f}x".format(s["overall_roas"]),
        hint=t("ads.hint_roas_low") if s["overall_roas"] < 2 and s["total"] > 0 else "",
        hint_tone=roas_tone,
    )
with k5:
    p_tone = "ok" if s["overall_profit"] > 0 else "danger"
    metric_with_hint(
        t("ads.kpi_profit"), "{:,.0f}".format(s["overall_profit"]),
        hint="", hint_tone=p_tone,
    )


# ---- Add campaign -----------------------------------------------------------

st.divider()
with st.expander(t("ads.add_title"), expanded=s["total"] == 0):
    with st.form("add_campaign"):
        c1, c2, c3 = st.columns(3)
        with c1:
            n_name = st.text_input(t("ads.f_name") + " *", placeholder=t("ads.name_placeholder"))
            n_plat = st.selectbox(
                t("ads.f_platform"),
                ads.AD_PLATFORMS,
                format_func=lambda p: ads.PLATFORM_ICONS.get(p, "📣") + " " + p.replace("_", " ").title(),
            )
        with c2:
            n_budget = st.number_input(t("ads.f_budget"), min_value=0.0, step=100.0, format="%.0f")
            n_spent = st.number_input(t("ads.f_spent"), min_value=0.0, step=50.0, format="%.0f")
        with c3:
            n_imp = st.number_input(t("ads.f_impressions"), min_value=0, step=100)
            n_clicks = st.number_input(t("ads.f_clicks"), min_value=0, step=10)

        c4, c5 = st.columns(2)
        with c4:
            n_orders = st.number_input(t("ads.f_orders"), min_value=0, step=1)
        with c5:
            n_rev = st.number_input(t("ads.f_revenue"), min_value=0.0, step=100.0, format="%.0f")

        n_note = st.text_input(t("ads.f_note"))

        if st.form_submit_button(t("ads.add_btn"), type="primary"):
            if n_name.strip():
                ads.add(
                    name=n_name.strip(), platform=n_plat,
                    budget=n_budget, spent=n_spent, note=n_note,
                    impressions=n_imp, clicks=n_clicks,
                    orders=n_orders, revenue=n_rev,
                )
                toast(t("ads.added"), icon="✓")
                st.rerun()
            else:
                st.warning(t("ads.need_name"))


# ---- Platform breakdown -----------------------------------------------------

st.divider()
bp = ads.by_platform()
if bp:
    st.markdown("### " + t("ads.by_platform"))
    for r in bp:
        plat = r.get("platform", "?")
        icon = ads.PLATFORM_ICONS.get(plat, "📣")
        roas = r.get("roas", 0)
        roas_color = "#4d6c5c" if roas >= 3 else ("#c5963d" if roas >= 1 else "#c54c4c")
        roas_icon = "🟢" if roas >= 3 else ("🟡" if roas >= 1 else "🔴")

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div>" + icon + " " + plat.replace("_", " ").title() +
            " <span style='color:#7a7569;font-size:12px'>" +
            str(r.get("campaigns", 0)) + t("ads.campaigns_unit") + "</span></div>"
            "<div style='display:flex;gap:18px;align-items:center;font-size:13px'>"
            "<span>" + t("ads.kpi_spent") + " ฿" + "{:,.0f}".format(float(r.get("spent", 0))) + "</span>"
            "<span>" + t("ads.kpi_revenue") + " ฿" + "{:,.0f}".format(float(r.get("revenue", 0))) + "</span>"
            "<span style='color:" + roas_color + ";font-weight:600'>" +
            roas_icon + " ROAS " + "{:.1f}x".format(roas) + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Campaign list -----------------------------------------------------------

st.divider()
st.markdown("### " + t("ads.list_title"))

tab_active, tab_all = st.tabs([
    "🟢 " + t("ads.tab_active"),
    "📋 " + t("ads.tab_all"),
])

with tab_active:
    campaigns = ads.all_campaigns(status="active")
    if not campaigns:
        st.info(t("ads.empty"))
    else:
        _render_campaigns(campaigns) if False else None  # defined below

with tab_all:
    campaigns = ads.all_campaigns()
    if not campaigns:
        st.info(t("ads.empty"))


# Render function for both tabs
def _show_campaigns(campaign_list):
    for c in campaign_list:
        roas = c.get("roas", 0)
        roas_color = "#4d6c5c" if roas >= 3 else ("#c5963d" if roas >= 1 else "#c54c4c")

        plat = c.get("platform", "?")
        icon = ads.PLATFORM_ICONS.get(plat, "📣")
        status = c.get("status", "active")
        s_badge = {"active": "🟢", "paused": "⏸", "ended": "⏹"}.get(status, "")

        spent_str = "{:,.0f}".format(float(c.get("spent", 0)))
        rev_str = "{:,.0f}".format(float(c.get("revenue", 0)))
        profit = c.get("profit", 0)
        profit_color = "#4d6c5c" if profit >= 0 else "#c54c4c"

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
                "border-radius:10px;padding:12px 16px;margin-bottom:4px'>"
                "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                "<div><span style='font-weight:600'>" + s_badge + " " + icon + " " +
                (c.get("name") or "—") + "</span></div>"
                "<div style='display:flex;gap:14px;font-size:13px;align-items:center'>"
                "<span>" + t("ads.kpi_spent") + " ฿" + spent_str + "</span>"
                "<span>→ ฿" + rev_str + "</span>"
                "<span style='color:" + roas_color + ";font-weight:600'>"
                "ROAS " + "{:.1f}x".format(roas) + "</span>"
                "<span style='color:" + profit_color + "'>" +
                ("+" if profit >= 0 else "") + "{:,.0f}".format(profit) + "</span>"
                "</div></div>"
                "<div style='color:#9a9485;font-size:11px;margin-top:4px'>"
                "CPC ฿" + "{:.0f}".format(c.get("cpc", 0)) +
                " · CTR " + "{:.1f}%".format(c.get("ctr", 0)) +
                " · Conv " + "{:.1f}%".format(c.get("conv_rate", 0)) +
                " · CPA ฿" + "{:.0f}".format(c.get("cpa", 0)) +
                "</div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if st.button("✏", key="_ae_" + str(c["id"]),
                             type="tertiary", help=t("common.edit")):
                    st.session_state["_ads_edit_id"] = c["id"]
                    st.rerun()
            with bc2:
                new_status = "paused" if status == "active" else "active"
                btn_icon = "⏸" if status == "active" else "▶"
                if st.button(btn_icon, key="_as_" + str(c["id"]),
                             type="tertiary"):
                    ads.update(c["id"], status=new_status)
                    st.rerun()
            with bc3:
                if st.button("🗑", key="_ad_" + str(c["id"]),
                             type="tertiary", help=t("common.delete")):
                    ads.delete(c["id"])
                    st.rerun()


# Re-render in both tabs
with tab_active:
    _show_campaigns(ads.all_campaigns(status="active"))

with tab_all:
    _show_campaigns(ads.all_campaigns())


# ---- Edit drawer -------------------------------------------------------------

edit_id = st.session_state.get("_ads_edit_id")
if edit_id:
    c_info = None
    for c in ads.all_campaigns():
        if c["id"] == edit_id:
            c_info = c
            break
    if c_info:
        st.divider()
        st.markdown("### ✏ " + t("ads.edit_title"))
        with st.form("edit_campaign"):
            ec1, ec2 = st.columns(2)
            with ec1:
                e_spent = st.number_input(
                    t("ads.f_spent"), value=float(c_info.get("spent", 0)),
                    step=50.0, format="%.0f",
                )
                e_clicks = st.number_input(
                    t("ads.f_clicks"), value=int(c_info.get("clicks", 0)), step=10,
                )
                e_imp = st.number_input(
                    t("ads.f_impressions"), value=int(c_info.get("impressions", 0)), step=100,
                )
            with ec2:
                e_orders = st.number_input(
                    t("ads.f_orders"), value=int(c_info.get("orders", 0)), step=1,
                )
                e_rev = st.number_input(
                    t("ads.f_revenue"), value=float(c_info.get("revenue", 0)),
                    step=100.0, format="%.0f",
                )
                e_note = st.text_input(t("ads.f_note"), value=c_info.get("note", ""))

            ca, cb = st.columns(2)
            with ca:
                if st.form_submit_button(t("common.save"), type="primary"):
                    ads.update(edit_id, spent=e_spent, clicks=e_clicks,
                               impressions=e_imp, orders=e_orders,
                               revenue=e_rev, note=e_note)
                    st.session_state.pop("_ads_edit_id", None)
                    toast(t("common.saved"), icon="✓")
                    st.rerun()
            with cb:
                if st.form_submit_button(t("common.cancel")):
                    st.session_state.pop("_ads_edit_id", None)
                    st.rerun()
