"""E3 Customer CRM — know who buys, who's VIP, who's gone quiet."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import customers as cu
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
cu.init()
render_sidebar()

st.title(t("cust.title"))
st.caption(t("cust.caption"))

stats = cu.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("cust.kpi_total"), stats["total"])
c2.metric(t("cust.kpi_vip"), stats["vip"],
          delta_color="normal" if stats["vip"] > 0 else "off")
c3.metric(t("cust.kpi_dormant"), stats["dormant"],
          delta_color="inverse" if stats["dormant"] > 0 else "off")
c4.metric(t("cust.kpi_avg_spend"), "฿{:,.0f}".format(stats["avg_total_spent"]))

st.divider()

tab_all, tab_vip, tab_dormant, tab_edit = st.tabs([
    t("cust.tab_all"), t("cust.tab_vip"), t("cust.tab_dormant"), t("cust.tab_edit")
])

TIER_ICONS = {"Bronze": "🥉", "Silver": "🥈", "Gold": "🥇", "Diamond": "💎"}

def _render_customer_row(cust):
    icon = TIER_ICONS.get(cu.tier(cust["order_count"]), "👤")
    tier_name = cu.tier(cust["order_count"])
    label = (icon + " **" + (cust["name"] or "—") + "**" +
             " · " + tier_name +
             " · " + str(cust["order_count"]) + t("cust.orders_unit") +
             " · ฿{:,.0f}".format(cust["total_spent"]))
    with st.expander(label):
        col1, col2 = st.columns(2)
        col1.write(t("cust.phone") + ": " + (cust.get("phone") or "—"))
        col1.write(t("cust.email") + ": " + (cust.get("email") or "—"))
        col1.write(t("cust.line") + ": " + (cust.get("line_id") or "—"))
        col2.write(t("cust.platforms") + ": " + (cust.get("platforms") or "—"))
        col2.write(t("cust.first_order") + ": " + (cust.get("first_order") or "—"))
        col2.write(t("cust.last_order") + ": " + (cust.get("last_order") or "—"))
        if cust.get("note"):
            st.caption(cust["note"])

with tab_all:
    q = st.text_input(t("cust.search"), placeholder=t("cust.search_ph"))
    if q.strip():
        custs = cu.search(q.strip())
    else:
        sort_col = st.selectbox(t("cust.sort_by"),
                                ["total_spent","order_count","last_order"],
                                format_func=lambda s: {
                                    "total_spent": t("cust.sort_spent"),
                                    "order_count": t("cust.sort_orders"),
                                    "last_order":  t("cust.sort_recent"),
                                }.get(s, s))
        custs = cu.all_customers(sort=sort_col)
    if not custs:
        st.info(t("cust.empty"))
    for cust in custs[:80]:
        _render_customer_row(cust)

with tab_vip:
    st.subheader(t("cust.vip_title"))
    vips = cu.vip_customers(min_orders=3)
    if not vips:
        st.info(t("cust.empty"))
    for cust in vips:
        _render_customer_row(cust)

with tab_dormant:
    st.subheader(t("cust.dormant_title"))
    days_dormant = st.slider(t("cust.dormant_days"), 14, 90, 30)
    dormants = cu.dormant_customers(days=days_dormant)
    if not dormants:
        st.success(t("cust.no_dormant"))
    else:
        st.warning("⚠️ " + str(len(dormants)) + t("cust.dormant_count"))
        for cust in dormants[:50]:
            _render_customer_row(cust)

with tab_edit:
    st.subheader(t("cust.edit_title"))
    custs_all = cu.all_customers()
    if not custs_all:
        st.info(t("cust.empty"))
    else:
        sel_id = st.selectbox(
            t("cust.sel_customer"),
            [c["id"] for c in custs_all],
            format_func=lambda i: next((c["name"] or "—" for c in custs_all if c["id"]==i), ""),
        )
        sel = next((c for c in custs_all if c["id"]==sel_id), None)
        if sel:
            with st.form("edit_cust_form"):
                col1, col2 = st.columns(2)
                name  = col1.text_input(t("cust.f_name"), value=sel.get("name",""))
                phone = col2.text_input(t("cust.f_phone"), value=sel.get("phone",""))
                email = col1.text_input(t("cust.f_email"), value=sel.get("email",""))
                line  = col2.text_input(t("cust.f_line"), value=sel.get("line_id",""))
                note  = st.text_input(t("cust.f_note"), value=sel.get("note",""))
                if st.form_submit_button(t("cust.save_btn")):
                    cu.update(sel_id, name=name, phone=phone,
                              email=email, line_id=line, note=note)
                    st.success(t("cust.saved"))
                    st.rerun()
