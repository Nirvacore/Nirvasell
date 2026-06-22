"""G6 Live Sell Tracker — log orders and tally sales during live streams."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import live_sell_tracker as lt
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
lt.init()
render_sidebar()

st.title(t("live.title"))
st.caption(t("live.caption"))

active = lt.active_sessions()

if active:
    st.success("🔴 " + t("live.live_now") + ": **" + active[0]["title"] + "**")
    sess = active[0]
    sid  = sess["id"]
    summary = lt.session_summary(sid)

    c1, c2, c3 = st.columns(3)
    c1.metric(t("live.kpi_orders"), summary.get("order_count",0))
    c2.metric(t("live.kpi_revenue"), "฿{:,.0f}".format(summary.get("total_revenue",0)))
    c3.metric(t("live.kpi_units"), summary.get("total_units",0))

    st.divider()
    col_a, col_e = st.columns([2,1])
    with col_a.form("live_order_form"):
        c1f, c2f, c3f = st.columns(3)
        sku    = c1f.text_input(t("live.f_sku"), placeholder=t("common.sku_ph"))
        qty    = c2f.number_input(t("live.f_qty"), min_value=1, value=1)
        note_l = c3f.text_input(t("live.f_note"))
        if st.form_submit_button("➕ " + t("live.add_order")):
            if sku.strip():
                lt.add_order(sid, sku.strip(), qty=int(qty), note=note_l)
                st.rerun()
    if col_e.button("⏹ " + t("live.end_session"), type="secondary"):
        peak = st.session_state.get("peak_viewers_" + str(sid), 0)
        lt.end_session(sid, viewers_peak=int(peak))
        st.rerun()

    st.subheader(t("live.order_list"))
    orders = summary.get("orders", [])
    if not orders:
        st.info(t("live.no_orders"))
    for o in orders:
        row_html = (
            "<div style='margin:2px 0;font-size:0.84rem'>"
            "<span style='color:#4d6c5c;width:80px;display:inline-block;font-family:monospace'>" +
            (o.get("sku") or "—") + "</span>"
            "<span style='color:#d4d0c8;width:40px;display:inline-block'>×" +
            str(o.get("qty",1)) + "</span>"
            "<span style='color:#9a9485'>฿{:,.0f}".format(o.get("revenue",0)) + "</span>"
            "</div>"
        )
        st.html(row_html)

    st.caption(t("live.peak_viewers"))
    peak_v = st.number_input(t("live.peak_input"), min_value=0, step=10,
                              key="peak_viewers_" + str(sid))

else:
    st.info(t("live.no_active"))
    if st.button("🔴 " + t("live.start_session")):
        st.session_state["show_start"] = True

    if st.session_state.get("show_start"):
        with st.form("start_live_form"):
            col1, col2 = st.columns(2)
            sess_title = col1.text_input(t("live.f_title"), placeholder=t("live.title_ph"))
            platform   = col2.selectbox(t("live.f_platform"),
                ["facebook","tiktok_shop","shopee_live","line","instagram"])
            if st.form_submit_button("🔴 " + t("live.go_live")):
                if sess_title.strip():
                    lt.create_session(sess_title.strip(), platform=platform)
                    st.rerun()

st.divider()
st.subheader(t("live.history"))
past = lt.all_sessions(limit=20)
finished = [s for s in past if s.get("status") != "active"]
if not finished:
    st.info(t("live.no_history"))
for s in finished:
    label = ("📹 **" + s["title"] + "**"
             + " · " + (s.get("platform") or "—")
             + " · " + (s.get("ended_at") or s.get("created_at") or "—"))
    with st.expander(label):
        ssum = lt.session_summary(s["id"])
        c1, c2, c3 = st.columns(3)
        c1.metric(t("live.kpi_orders"), ssum.get("order_count",0))
        c2.metric(t("live.kpi_revenue"), "฿{:,.0f}".format(ssum.get("total_revenue",0)))
        c3.metric(t("live.kpi_units"), ssum.get("total_units",0))
        st.caption(t("live.duration") + ": " + str(s.get("duration_mins",0)) + t("live.mins"))
