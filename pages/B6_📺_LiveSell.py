"""Live Sell Tracker — track orders during Facebook/TikTok live sessions."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import live_sell_tracker as lst
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Live Sell",
                   page_icon="📺", layout="wide")
apply_theme()
require_auth()
db.init()
lst.init()
render_sidebar()

page_header(icon="📺", title=t("live.title"), subtitle=t("live.caption"))

s = lst.stats()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📺 " + t("live.kpi_sessions"), str(s["total_sessions"]),
                     hint="", hint_tone="info")
with k2:
    live_str = str(s["live_now"]) + " " + t("live.live_now_label")
    metric_with_hint("🔴 " + t("live.kpi_live"), live_str,
                     hint="", hint_tone="danger" if s["live_now"] > 0 else "ok")
with k3:
    metric_with_hint("💰 " + t("live.kpi_revenue"),
                     "฿{:,.0f}".format(s["total_revenue"]),
                     hint="", hint_tone="ok")
with k4:
    metric_with_hint("🏆 " + t("live.kpi_best"),
                     (s["best_session"] or "—")[:20],
                     hint="฿{:,.0f}".format(s["best_revenue"]) if s["best_revenue"] else "",
                     hint_tone="info")

# ---- Active sessions --------------------------------------------------------
active = lst.active_sessions()
if active:
    st.divider()
    for sess in active:
        st.markdown(
            "<div style='padding:10px 14px;background:rgba(197,76,76,0.04);"
            "border:1px solid #c54c4c;border-radius:10px;margin-bottom:6px'>"
            " 🔴 <strong>" + t("common.live_label") + "</strong> " + sess["title"] +
            " · " + sess["platform"] +
            " · " + str(sess["order_count"]) + " " + t("common.orders") +
            " · ฿{:,.0f}".format(sess["revenue"]) + "</div>",
            unsafe_allow_html=True,
        )

# ---- Start new session ------------------------------------------------------
st.divider()
with st.expander(t("live.start_title"), expanded=not bool(active)):
    with st.form("start_session"):
        lc1, lc2 = st.columns(2)
        with lc1:
            sess_title = st.text_input(t("live.f_title"),
                                       placeholder=t("live.title_ph"))
        with lc2:
            platform = st.selectbox(t("live.f_platform"), lst.PLATFORMS)
        notes = st.text_input(t("live.f_notes"), placeholder="")
        if st.form_submit_button(t("live.start_btn"), type="primary"):
            if sess_title.strip():
                sess_id = lst.create_session(sess_title.strip(), platform,
                                              notes=notes.strip())
                st.session_state["active_live_session"] = sess_id
                toast(t("live.started"), icon="🔴")
                st.rerun()

# ---- Add orders to active session -------------------------------------------
if st.session_state.get("active_live_session"):
    sess_id = st.session_state["active_live_session"]
    summary_data = lst.session_summary(sess_id)

    st.divider()
    st.markdown(
        "### 🔴 " + summary_data.get("title", t("live.default_title")) +
        " — " + str(summary_data.get("total_orders", 0)) + " " + t("common.orders") +
        " · ฿{:,.0f}".format(summary_data.get("total_revenue", 0))
    )

    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name, sell_price FROM products ORDER BY sku"
        ).fetchall()

    with st.form("add_live_order"):
        oc1, oc2, oc3, oc4 = st.columns(4)
        with oc1:
            if products:
                p_opts = [p["sku"] + " — " + (p["name"] or "")[:20]
                          for p in products]
                oi = st.selectbox(t("live.f_sku"), range(len(p_opts)),
                                  format_func=lambda i: p_opts[i], key="_lo_p")
                o_sku = products[oi]["sku"]
                default_price = float(products[oi]["sell_price"] or 0)
            else:
                o_sku = st.text_input(t("live.f_sku"), key="_lo_ps")
                default_price = 0.0
        with oc2:
            o_qty = st.number_input(t("live.f_qty"), min_value=1,
                                    value=1, step=1)
        with oc3:
            o_price = st.number_input(t("live.f_price"),
                                      value=default_price if products else 0.0,
                                      min_value=0.0, step=10.0)
        with oc4:
            o_buyer = st.text_input(t("live.f_buyer"),
                                    placeholder=t("live.buyer_ph"))
        if st.form_submit_button(t("live.add_order_btn"), type="primary"):
            lst.add_order(sess_id, o_sku, o_qty, o_price, o_buyer.strip())
            st.rerun()

    orders = summary_data.get("orders", [])
    for ord_item in orders[-10:]:
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:5px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span>" + ord_item["sku"] +
            " x" + str(ord_item["qty"]) +
            " · " + (ord_item.get("buyer_name") or "—") + "</span>"
            "<span style='color:#4d6c5c;font-weight:600'>"
            "฿{:,.0f}".format(ord_item.get("line_total") or 0) + "</span></div>",
            unsafe_allow_html=True,
        )

    ec1, ec2 = st.columns(2)
    with ec1:
        viewers = st.number_input(t("live.f_viewers"), min_value=0, value=0)
    with ec2:
        if st.button(t("live.end_btn"), type="primary", key="_live_end"):
            lst.end_session(sess_id, viewers)
            st.session_state.pop("active_live_session", None)
            toast(t("live.ended"), icon="✅")
            st.rerun()

# ---- Session history ---------------------------------------------------------
st.divider()
st.markdown("### " + t("live.history_title"))

sessions = lst.all_sessions(15)
for sess in sessions:
    if sess.get("id") == st.session_state.get("active_live_session"):
        continue
    rev_str = "฿{:,.0f}".format(sess.get("revenue") or 0)
    st.markdown(
        "<div style='display:flex;justify-content:space-between;"
        "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<span>" + sess.get("status_icon", "?") +
        " <strong>" + sess["title"] + "</strong>"
        " <span style='color:#9a9485;font-size:11px'>"
        + sess["platform"] + "</span></span>"
        "<span style='display:flex;gap:12px;font-size:13px'>"
        "<span>" + str(sess.get("order_count") or 0) + " " + t("common.orders") + "</span>"
        "<span style='color:#4d6c5c;font-weight:600'>" + rev_str + "</span>"
        "<span style='font-size:11px;color:#9a9485'>"
        + (sess.get("created_at") or "")[:10] + "</span>"
        "</span></div>",
        unsafe_allow_html=True,
    )
