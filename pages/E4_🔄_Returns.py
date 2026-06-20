"""E4 Returns Tracker — track refunds, reasons, and financial impact."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import returns as rt
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar
from datetime import datetime

apply_theme()
require_auth()
rt.init()
render_sidebar()

st.title(t("ret.title"))
st.caption(t("ret.caption"))

stats = rt.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("ret.kpi_total"), stats["total_returns"])
c2.metric(t("ret.kpi_refund"), "฿{:,.0f}".format(stats["total_refund"]))
c3.metric(t("ret.kpi_loss"), "฿{:,.0f}".format(stats["total_loss"]),
          delta_color="inverse" if stats["total_loss"] > 0 else "off")
c4.metric(t("ret.kpi_rate"), str(stats["return_rate"]) + "%",
          delta_color="inverse" if stats["return_rate"] > 5 else "off")

if stats["return_rate"] > 5:
    st.warning("⚠️ " + t("ret.rate_warning"))

st.divider()

tab_list, tab_log, tab_analysis = st.tabs([
    t("ret.tab_list"), t("ret.tab_log"), t("ret.tab_analysis")
])

with tab_list:
    returns = rt.all_returns(limit=100)
    if not returns:
        st.info(t("ret.empty"))
    for r in returns:
        icon = rt.REASON_ICONS.get(r["reason"], "📝")
        label = icon + " " + (r.get("return_date","") or "—") + \
                " · " + (r.get("order_id") or "—") + \
                " · " + r["reason"] + \
                " · ฿{:,.0f}".format(r["refund_amount"])
        if r.get("sku"):
            label += " · " + r["sku"]
        col_l, col_d = st.columns([5,1])
        col_l.write(label)
        if col_d.button("🗑", key="rdel_" + str(r["id"])):
            rt.delete(r["id"])
            st.rerun()

with tab_log:
    st.subheader(t("ret.log_title"))
    with st.form("return_form"):
        col1, col2 = st.columns(2)
        order_id  = col1.text_input(t("ret.f_order_id"))
        platform  = col2.selectbox(t("ret.f_platform"),
                                    ["shopee","lazada","tiktok_shop","facebook","line","other"])
        col3, col4 = st.columns(2)
        reason    = col3.selectbox(t("ret.f_reason"),
                                    rt.RETURN_REASONS,
                                    format_func=lambda r: rt.REASON_ICONS.get(r,"") + " " + r.replace("_"," ").title())
        sku       = col4.text_input(t("ret.f_sku"))
        col5, col6 = st.columns(2)
        refund    = col5.number_input(t("ret.f_refund"), min_value=0.0, step=10.0)
        ship_cost = col6.number_input(t("ret.f_ship_cost"), min_value=0.0, step=10.0)
        ret_date  = col1.text_input(t("ret.f_date"),
                                     value=datetime.now().strftime("%Y-%m-%d"))
        note      = col2.text_input(t("ret.f_note"))
        if st.form_submit_button(t("ret.log_btn")):
            rt.add(order_id=order_id, sku=sku, platform=platform,
                   reason=reason, refund_amount=refund,
                   shipping_cost=ship_cost, note=note, return_date=ret_date)
            st.success(t("ret.logged"))
            st.rerun()

with tab_analysis:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader(t("ret.by_reason_title"))
        reasons = rt.by_reason()
        if reasons:
            max_r = max(r["count"] for r in reasons) or 1
            for r in reasons:
                icon = rt.REASON_ICONS.get(r["reason"],"📝")
                bar_w = int(r["count"] / max_r * 180)
                row_html = (
                    "<div style='margin:3px 0;font-size:0.84rem'>"
                    "<span style='color:#9a9485;width:170px;display:inline-block'>"
                    + icon + " " + r["reason"] + "</span>"
                    "<div style='display:inline-block;background:#7a3a3a;width:" +
                    str(bar_w) + "px;height:10px;vertical-align:middle'></div>"
                    " <span style='color:#d4d0c8'>" + str(r["count"]) +
                    " · ฿{:,.0f}".format(r["refund"] or 0) + "</span>"
                    "</div>"
                )
                st.html(row_html)
        else:
            st.info(t("ret.empty"))

    with col_r:
        st.subheader(t("ret.by_platform_title"))
        by_p = rt.by_platform()
        for p in by_p:
            refund = p.get("refund") or 0
            ship = p.get("ship") or 0
            loss = refund + ship
            prow_html = (
                "<div style='margin:3px 0;font-size:0.84rem'>"
                "<span style='color:#9a9485;width:120px;display:inline-block'>"
                + (p["platform"] or "—") + "</span>"
                "<span style='color:#d4d0c8'>" + str(p["count"]) + t("ret.returns_unit") +
                t("ret.total_loss_line", amount="{:,.0f}".format(loss)) + "</span>"
                "</div>"
            )
            st.html(prow_html)
        st.divider()
        st.subheader(t("ret.by_sku_title"))
        by_sku = rt.by_sku(limit=10)
        for s in by_sku:
            st.write(t("ret.sku_line",
                       sku=s["sku"] or "—",
                       count=str(s["count"]),
                       returns_unit=t("ret.returns_unit"),
                       amount="{:,.0f}".format(s["refund"] or 0)))
