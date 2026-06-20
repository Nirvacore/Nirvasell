"""Return Tracker — understand what comes back and why.

High return rate = low seller score = fewer sales. This page helps
sellers spot patterns: which products get returned most, which platform
has the worst rate, which reason dominates."""
from __future__ import annotations
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import returns as ret
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import platform_name

st.set_page_config(page_title="nirva.sell · Returns",
                   page_icon="↩", layout="wide")
apply_theme()
require_auth()
db.init()
ret.init()
render_sidebar()

page_header(icon="↩", title=t("ret.title"), subtitle=t("ret.caption"))


# ---- KPI overview -------------------------------------------------------

s = ret.stats()

m1, m2, m3, m4 = st.columns(4)
with m1:
    rate_tone = "danger" if s["return_rate"] > 5 else ("warn" if s["return_rate"] > 2 else "ok")
    metric_with_hint(
        t("ret.kpi_rate"), "{:.1f}%".format(s["return_rate"]),
        hint=t("ret.hint_rate_high") if s["return_rate"] > 5 else "",
        hint_tone=rate_tone,
    )
with m2:
    metric_with_hint(
        t("ret.kpi_count"), str(s["total_returns"]),
        hint="",
        hint_tone="info",
    )
with m3:
    metric_with_hint(
        t("ret.kpi_refund"), "{:,.0f}".format(s["total_refund"]),
        hint="",
        hint_tone="warn" if s["total_refund"] > 0 else "info",
    )
with m4:
    metric_with_hint(
        t("ret.kpi_loss"), "{:,.0f}".format(s["total_loss"]),
        hint=t("ret.hint_loss") if s["total_loss"] > 0 else "",
        hint_tone="danger" if s["total_loss"] > 1000 else "info",
    )


# ---- Add return form ----------------------------------------------------

st.divider()
st.markdown("### " + t("ret.add_title"))

with st.form("add_return"):
    c1, c2, c3 = st.columns(3)
    with c1:
        n_order = st.text_input(t("ret.f_order_id"), placeholder="ORD-12345")
        n_sku = st.text_input(t("ret.f_sku"), placeholder="SKU-001")
    with c2:
        n_plat = st.selectbox(
            t("ret.f_platform"),
            ["shopee", "lazada", "tiktok", "shopify", "other"],
            format_func=lambda p: {
                "shopee": "🛒", "lazada": "🟧", "tiktok": "🎵",
                "shopify": "🛍", "other": "📝",
            }.get(p, "📦") + " " + platform_name(p),
        )
        n_reason = st.selectbox(
            t("ret.f_reason"),
            ret.RETURN_REASONS,
            format_func=lambda r: ret.REASON_ICONS.get(r, "") + " " + t("ret.reason_" + r),
        )
    with c3:
        n_refund = st.number_input(t("ret.f_refund"), min_value=0.0, step=10.0, format="%.0f")
        n_ship = st.number_input(t("ret.f_shipping"), min_value=0.0, step=10.0, format="%.0f")
    n_date = st.date_input(t("ret.f_date"), value=date.today())
    n_note = st.text_input(t("ret.f_note"), placeholder=t("ret.note_placeholder"))

    if st.form_submit_button(t("ret.add_btn"), type="primary"):
        ret.add(
            order_id=n_order, sku=n_sku, platform=n_plat,
            reason=n_reason, refund_amount=n_refund,
            shipping_cost=n_ship, note=n_note,
            return_date=n_date.isoformat(),
        )
        toast(t("ret.added"), icon="✓")
        st.rerun()


# ---- Analysis: by platform + by reason ----------------------------------

st.divider()
cP, cR = st.columns(2)

with cP:
    st.markdown("### " + t("ret.by_platform"))
    bp = ret.by_platform()
    if bp:
        for r in bp:
            plat = r.get("platform", "?")
            icon = {"shopee": "🛒", "lazada": "🟧", "tiktok": "🎵"}.get(plat, "📦")
            loss = (r.get("refund") or 0) + (r.get("ship") or 0)
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:8px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div>" + icon + " " + platform_name(plat) + " · " +
                t("common.n_returns", n=str(r["count"])) + "</div>"
                "<div style='color:#c54c4c'>-฿" + "{:,.0f}".format(loss) + "</div>"
                "</div>",
                unsafe_allow_html=True,
            )
    else:
        st.caption(t("ret.no_data"))

with cR:
    st.markdown("### " + t("ret.by_reason"))
    br = ret.by_reason()
    if br:
        for r in br:
            reason = r.get("reason", "other")
            icon = ret.REASON_ICONS.get(reason, "📝")
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:8px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div>" + icon + " " + t("ret.reason_" + reason) + "</div>"
                "<div style='font-weight:600'>" + str(r["count"]) + "</div>"
                "</div>",
                unsafe_allow_html=True,
            )
    else:
        st.caption(t("ret.no_data"))


# ---- Top returned SKUs --------------------------------------------------

st.divider()
st.markdown("### " + t("ret.top_skus"))
bs = ret.by_sku()
if bs:
    for r in bs:
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:8px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div style='font-size:14px'>📦 " + (r.get("sku") or "?") + "</div>"
            "<div>" + str(r["count"]) + " returns · "
            "<span style='color:#c54c4c'>-฿" + "{:,.0f}".format(r.get("refund") or 0) + "</span></div>"
            "</div>",
            unsafe_allow_html=True,
        )
else:
    st.caption(t("ret.no_data"))


# ---- Return history list ------------------------------------------------

st.divider()
st.markdown("### " + t("ret.history"))

rows = ret.all_returns()
if rows:
    for r in rows:
        icon = ret.REASON_ICONS.get(r.get("reason", ""), "📝")
        reason_label = t("ret.reason_" + r.get("reason", "other"))
        loss = (r.get("refund_amount") or 0) + (r.get("shipping_cost") or 0)
        cA, cB = st.columns([6, 1])
        with cA:
            plat = r.get("platform", "")
            st.markdown(
                "<div style='padding:6px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;justify-content:space-between'>"
                "<div>" + icon + " " + (r.get("order_id") or "—") +
                " · " + (r.get("sku") or "") +
                " · " + plat +
                " <span style='color:#7a7569;font-size:12px'>" + reason_label + "</span></div>"
                "<div style='color:#c54c4c'>-฿" + "{:,.0f}".format(loss) + "</div>"
                "</div>"
                "<div style='color:#9a9485;font-size:11px'>" +
                (r.get("return_date") or "") +
                (" · " + r.get("note", "") if r.get("note") else "") +
                "</div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            if st.button("🗑", key="_rd_" + str(r["id"]),
                         type="tertiary", help=t("common.delete")):
                ret.delete(r["id"])
                toast(t("common.deleted"), icon="🗑")
                st.rerun()
else:
    st.info(t("ret.empty"))
