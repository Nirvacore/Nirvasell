"""D1 COD Tracker — cash-on-delivery order tracking."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import cod_tracker as ct
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
ct.init()
render_sidebar()

st.title(t("cod.title"))
st.caption(t("cod.caption"))

stats = ct.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("cod.kpi_pending_amount"), "฿{:,.0f}".format(stats["pending_amount"]))
c2.metric(t("cod.kpi_collected"), "฿{:,.0f}".format(stats["collected_amount"]))
c3.metric(t("cod.kpi_return_rate"), str(stats["cod_return_rate"]) + "%")
c4.metric(t("cod.kpi_lost_shipping"), "฿{:,.0f}".format(stats["lost_shipping"]))

st.divider()

tab_log, tab_track, tab_stats = st.tabs([
    t("cod.tab_log"), t("cod.tab_track"), t("cod.tab_stats")
])

with tab_log:
    st.subheader(t("cod.log_title"))
    with st.form("cod_add"):
        col1, col2 = st.columns(2)
        order_id   = col1.text_input(t("cod.f_order_id"))
        buyer_name = col2.text_input(t("cod.f_buyer"))
        platform   = col1.selectbox(t("cod.f_platform"),
                        ["shopee","lazada","tiktok_shop","facebook","line","direct"])
        payment    = col2.selectbox(t("cod.f_payment"), ["cod","prepaid"])
        amount     = col1.number_input(t("cod.f_amount"), min_value=0.0, step=10.0)
        shipping   = col2.number_input(t("cod.f_shipping"), min_value=0.0, step=5.0)
        note       = st.text_input(t("cod.f_note"))
        if st.form_submit_button(t("cod.add_btn")):
            if order_id and amount > 0:
                ct.add(order_id, platform, amount, shipping, payment, buyer_name, note)
                st.success(t("cod.added"))
                st.rerun()

with tab_track:
    st.subheader(t("cod.track_title"))
    orders = ct.all_orders(limit=80)
    status_filter = st.selectbox(t("cod.status_filter"),
                                  ["all"] + ct.COD_STATUSES, key="cod_sf")
    if status_filter != "all":
        orders = [o for o in orders if o["status"] == status_filter]
    for o in orders:
        icon = ct.STATUS_ICONS.get(o["status"], "•")
        label = icon + " " + (o["order_id"] or "—") + " · " + \
                o.get("buyer_name", "") + " · ฿{:,.0f}".format(o["amount"])
        with st.expander(label):
            st.write(t("cod.platform") + ": " + o.get("platform",""))
            st.write(t("cod.payment") + ": " + o.get("payment_type",""))
            st.write(t("cod.shipping") + ": ฿{:,.0f}".format(o.get("shipping_cost",0)))
            if o.get("note"):
                st.write(t("cod.note") + ": " + o["note"])
            new_status = st.selectbox(
                t("cod.update_status"),
                ct.COD_STATUSES,
                index=ct.COD_STATUSES.index(o["status"]) if o["status"] in ct.COD_STATUSES else 0,
                key="cs_" + str(o["id"]),
            )
            col_s, col_d = st.columns(2)
            if col_s.button(t("cod.save_status"), key="css_" + str(o["id"])):
                ct.update_status(o["id"], new_status)
                st.rerun()
            if col_d.button(t("cod.delete"), key="cod_del_" + str(o["id"])):
                ct.delete(o["id"])
                st.rerun()

with tab_stats:
    st.subheader(t("cod.stats_title"))
    by_p = ct.by_platform()
    if by_p:
        html = "<table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
        html += "<tr style='color:#9a9485'>"
        for col in [t("cod.col_platform"), t("cod.col_type"),
                    t("cod.col_count"), t("cod.col_revenue"), t("cod.col_returns")]:
            html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
        html += "</tr>"
        for r in by_p:
            html += "<tr style='border-top:1px solid #2a2a2a'>"
            html += "<td style='padding:4px 8px'>" + (r["platform"] or "—") + "</td>"
            html += "<td style='padding:4px 8px'>" + (r["payment_type"] or "—") + "</td>"
            html += "<td style='padding:4px 8px'>" + str(r["count"]) + "</td>"
            html += "<td style='padding:4px 8px'>฿{:,.0f}".format(r["revenue"] or 0) + "</td>"
            html += "<td style='padding:4px 8px'>" + str(r["returns"]) + "</td>"
            html += "</tr>"
        html += "</table>"
        st.html(html)
    else:
        st.info(t("cod.no_data"))
