"""Returns & Refunds — track what comes back and why."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
import db
import returns as rt
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import return_reason

st.set_page_config(page_title="nirva.sell · Returns",
                   page_icon="↩", layout="wide")
apply_theme()
require_auth()
db.init()
rt.init()
render_sidebar()

page_header(icon="↩", title=t("ret.title"), subtitle=t("ret.caption"))

s = rt.stats()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("↩ " + t("ret.kpi_total"), str(s["total_returns"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("📅 " + t("ret.kpi_this_month"), str(s["this_month"]),
                     hint="", hint_tone="warn" if s["this_month"] > 2 else "ok")
with k3:
    metric_with_hint("💸 " + t("ret.kpi_refunded"),
                     "฿{:,.0f}".format(s["total_refund"]),
                     hint="", hint_tone="danger" if s["total_refund"] > 0 else "ok")
with k4:
    rate_color = "danger" if s["return_rate"] > 5 else ("warn" if s["return_rate"] > 2 else "ok")
    metric_with_hint("📊 " + t("ret.kpi_rate"),
                     str(s["return_rate"]) + "%",
                     hint=t("ret.rate_warn") if s["return_rate"] > 5 else "",
                     hint_tone=rate_color)

# ---- Log new return ---------------------------------------------------------
st.divider()
with st.expander(t("ret.log_title"), expanded=False):
    with st.form("log_return"):
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            r_order = st.text_input(t("ret.f_order"),
                                    placeholder="ORD-001")
            r_sku = st.text_input(t("ret.f_sku"), placeholder="SKU-001")
        with rc2:
            r_platform = st.selectbox(t("ret.f_platform"), rt.PLATFORMS)
            r_reason = st.selectbox(
                t("ret.f_reason"),
                list(rt.RETURN_REASONS),
                format_func=lambda k: rt.REASON_ICONS.get(k, "?") + " " +
                return_reason(k),
            )
        with rc3:
            r_amount = st.number_input(t("ret.f_amount"),
                                       min_value=0.0, value=0.0, step=50.0)
            r_ship = st.number_input(t("ret.f_ship_cost"),
                                     min_value=0.0, value=0.0, step=10.0)
        r_note = st.text_input(t("ret.f_note"), placeholder="")
        r_date = st.date_input(t("ret.f_date"), value=date.today())
        if st.form_submit_button(t("ret.log_btn"), type="primary"):
            rt.add(
                order_id=r_order.strip(),
                sku=r_sku.strip(),
                platform=r_platform,
                reason=r_reason,
                refund_amount=r_amount,
                shipping_cost=r_ship,
                note=r_note.strip(),
                return_date=str(r_date),
            )
            toast(t("ret.logged"), icon="✓")
            st.rerun()

# ---- By reason breakdown ----------------------------------------------------
st.divider()
reason_data = rt.by_reason()
if reason_data:
    st.markdown("### 📊 " + t("ret.by_reason_title"))
    total_r = sum(r["count"] for r in reason_data)
    for r in reason_data:
        icon = rt.REASON_ICONS.get(r["reason"], "?")
        pct = round(r["count"] / total_r * 100, 0) if total_r else 0
        st.markdown(
            "<div style='display:flex;align-items:center;gap:10px;"
            "margin-bottom:5px'>"
            "<span style='width:180px;font-size:13px'>" + icon +
            " " + return_reason(r["reason"]) + "</span>"
            "<div style='flex:1;background:rgba(40,30,20,0.06);"
            "border-radius:3px;height:18px'>"
            "<div style='width:" + str(pct) + "%;height:100%;"
            "background:#9a7dc5;border-radius:3px'></div></div>"
            "<span style='width:60px;font-size:12px;text-align:right'>"
            + t("common.count_pct", count=str(r["count"]), pct=str(int(pct))) +
            "</span>"
            "<span style='width:80px;font-size:12px;text-align:right;"
            "color:#c54c4c'>-฿{:,.0f}".format(r["refund"] or 0) + "</span></div>",
            unsafe_allow_html=True,
        )

# ---- Platform breakdown -----------------------------------------------------
platform_data = rt.by_platform()
if platform_data:
    st.divider()
    st.markdown("### 📱 " + t("ret.by_platform_title"))
    for p in platform_data:
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span><strong>" + (p["platform"] or t("common.platform_direct")) +
            "</strong></span>"
            "<span style='display:flex;gap:16px;font-size:13px'>"
            "<span>" + str(p["count"]) + " " + t("common.items") + "</span>"
            "<span style='color:#c54c4c'>-฿{:,.0f}".format(p["refund"] or 0) + "</span>"
            "</span></div>",
            unsafe_allow_html=True,
        )

# ---- Recent returns ---------------------------------------------------------
st.divider()
st.markdown("### " + t("ret.recent_title"))

ret_rows = rt.all_returns(50)
if not ret_rows:
    st.info(t("ret.empty"))
    st.stop()

for row in ret_rows:
    icon = rt.REASON_ICONS.get(row["reason"], "?")
    st.markdown(
        "<div style='display:flex;justify-content:space-between;"
        "padding:7px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<span>" + icon +
        " <strong>" + (row.get("order_id") or "—") + "</strong>"
        " · " + (row.get("sku") or "—") +
        " · " + (row.get("platform") or "—") + "</span>"
        "<span style='display:flex;gap:12px;font-size:13px'>"
        "<span style='color:#c54c4c'>-฿{:,.0f}".format(row["refund_amount"] or 0) + "</span>"
        "<span style='font-size:11px;color:#9a9485'>"
        + (row.get("return_date") or row.get("created_at", ""))[:10] + "</span>"
        "</span></div>",
        unsafe_allow_html=True,
    )
