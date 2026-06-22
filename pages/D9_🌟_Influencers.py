"""D9 Influencer Tracker — manage creator partnerships and commissions."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import influencer_tracker as it
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
it.init()
render_sidebar()

st.title(t("inf.title"))
st.caption(t("inf.caption"))

stats = it.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("inf.kpi_total"), stats["total"])
c2.metric(t("inf.kpi_active"), stats["active"])
c3.metric(t("inf.kpi_sales"), "฿{:,.0f}".format(stats["total_sales"]))
c4.metric(t("inf.kpi_unpaid"), "฿{:,.0f}".format(stats["unpaid_commission"]),
          delta_color="inverse" if stats["unpaid_commission"] > 0 else "off")

st.divider()

tab_list, tab_add, tab_sales = st.tabs([
    t("inf.tab_list"), t("inf.tab_add"), t("inf.tab_sales")
])

with tab_list:
    status_filter = st.selectbox(
        t("inf.status_filter"),
        [""] + list(it.STATUSES.keys()),
        format_func=lambda s: t("inf.all") if s=="" else it.STATUSES[s]["label"],
    )
    influencers = it.all_influencers(status=status_filter or None)
    if not influencers:
        st.info(t("inf.empty"))
    for inf in influencers:
        si = inf["status_info"]
        followers_str = "{:,}".format(inf["followers"]) if inf["followers"] else "—"
        label = si["icon"] + " **" + inf["name"] + "**" + \
                " · " + inf.get("platform","") + " · " + followers_str + t("inf.followers_unit")
        with st.expander(label):
            col1, col2 = st.columns(2)
            col1.write(t("inf.handle") + ": @" + (inf.get("handle") or "—"))
            col1.write(t("inf.niche") + ": " + (inf.get("niche") or "—"))
            col1.write(t("inf.contact") + ": " + (inf.get("contact") or "—"))
            col2.write(t("inf.promo_code") + ": " + (inf.get("promo_code") or "—"))
            col2.write(t("inf.commission") + ": " +
                       str(inf["commission_rate"]) + (
                           "%" if inf["commission_type"] == "percentage" else " ฿"
                       ) + " / " + it.COMMISSION_TYPES.get(inf["commission_type"],""))
            col2.metric(t("inf.unpaid"), "฿{:,.0f}".format(inf["unpaid_commission"]))
            if inf.get("notes"):
                st.caption(inf["notes"])

            col_a, col_b, col_c = st.columns(3)
            if col_a.button(t("inf.activate"), key="ia_" + str(inf["id"])):
                it.set_status(inf["id"], "active")
                st.rerun()
            if col_b.button(t("inf.end"), key="ie_" + str(inf["id"])):
                it.set_status(inf["id"], "ended")
                st.rerun()
            if col_c.button(t("inf.mark_paid"), key="ip_" + str(inf["id"])):
                it.mark_paid(inf["id"])
                st.success(t("inf.paid"))
                st.rerun()

with tab_add:
    st.subheader(t("inf.add_title"))
    with st.form("add_inf_form"):
        col1, col2 = st.columns(2)
        name      = col1.text_input(t("inf.f_name"))
        handle    = col2.text_input(t("inf.f_handle"), placeholder=t("inf.handle_ph"))
        platform  = col1.selectbox(t("inf.f_platform"), it.PLATFORMS)
        followers = col2.number_input(t("inf.f_followers"), min_value=0, step=100)
        niche     = col1.text_input(t("inf.f_niche"), placeholder=t("inf.niche_ph"))
        contact   = col2.text_input(t("inf.f_contact"), placeholder=t("inf.contact_ph"))
        comm_type = col1.selectbox(t("inf.f_comm_type"),
                                    list(it.COMMISSION_TYPES.keys()),
                                    format_func=lambda k: it.COMMISSION_TYPES[k])
        comm_rate = col2.number_input(t("inf.f_comm_rate"), min_value=0.0, step=1.0, value=10.0)
        promo_code = col1.text_input(t("inf.f_promo_code"))
        notes      = col2.text_input(t("inf.f_notes"))
        if st.form_submit_button(t("inf.add_btn")):
            if name:
                it.add(name, handle, platform, int(followers), niche,
                       comm_type, comm_rate, contact, promo_code, notes)
                st.success(t("inf.added"))
                st.rerun()

with tab_sales:
    st.subheader(t("inf.sales_title"))
    influencers_all = it.all_influencers()
    active_inf = [i for i in influencers_all if i["status"] in ("active","pending")]
    if not active_inf:
        st.info(t("inf.no_active"))
    else:
        with st.form("record_sale_form"):
            sel_inf = st.selectbox(
                t("inf.sel_influencer"),
                [i["id"] for i in active_inf],
                format_func=lambda i: next((x["name"] for x in active_inf if x["id"]==i), ""),
            )
            col1, col2 = st.columns(2)
            sale_amount = col1.number_input(t("inf.f_sale_amount"), min_value=0.0, step=10.0)
            order_id    = col2.text_input(t("inf.f_order_id"))
            sku         = col1.text_input(t("inf.f_sku"))
            sale_date   = col2.text_input(t("inf.f_sale_date"), placeholder=t("common.date_ph"))
            if st.form_submit_button(t("inf.record_btn")):
                if sale_amount > 0:
                    it.record_sale(sel_inf, sale_amount, order_id, sku, sale_date)
                    st.success(t("inf.sale_recorded"))
                    st.rerun()
