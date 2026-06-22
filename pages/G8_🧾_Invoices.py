"""G8 Invoices — create and view customer invoices."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import invoices as inv
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
inv.init()
render_sidebar()

st.title(t("inv.title"))
st.caption(t("inv.caption"))

stats = inv.stats()
c1, c2, c3 = st.columns(3)
c1.metric(t("inv.kpi_total"), stats.get("total",0))
c2.metric(t("inv.kpi_revenue"), "฿{:,.0f}".format(stats.get("total_revenue",0)))
c3.metric(t("inv.kpi_avg"), "฿{:,.0f}".format(stats.get("avg_value",0)))

st.divider()
tab_list, tab_create = st.tabs([t("inv.tab_list"), t("inv.tab_create")])

with tab_list:
    invoices_list = inv.all_invoices(limit=50)
    if not invoices_list:
        st.info(t("inv.empty"))
    for invoice in invoices_list:
        iid = invoice.get("invoice_id") or invoice.get("id","?")
        label = ("🧾 **" + str(iid) + "**"
                 + " · " + (invoice.get("customer_name") or "—")
                 + " · ฿{:,.0f}".format(invoice.get("total_amount",0))
                 + (" (VAT)" if invoice.get("include_vat") else ""))
        with st.expander(label):
            items = invoice.get("items") or []
            if items:
                for it in items:
                    st.write("• " + (it.get("description") or it.get("sku","")) +
                             " × " + str(it.get("qty",1)) +
                             " @ ฿{:,.0f}".format(it.get("unit_price",0)))
            col_v, col_e = st.columns(2)
            if col_v.button(t("inv.view_text"), key="invv_" + str(iid)):
                rendered = inv.render_text(iid)
                st.code(rendered, language=None)

with tab_create:
    st.subheader(t("inv.create_title"))
    with st.form("inv_form"):
        col1, col2 = st.columns(2)
        order_id   = col1.text_input(t("inv.f_order"), placeholder=t("common.order_ref_ph"))
        cust_name  = col2.text_input(t("inv.f_customer"), placeholder=t("inv.f_customer_hint"))
        cust_addr  = st.text_area(t("inv.f_address"), height=60)
        col3, col4 = st.columns(2)
        cust_tax   = col3.text_input(t("inv.f_tax_id"), placeholder=t("common.tax_id_ph"))
        include_vat= col4.checkbox(t("inv.f_vat"), value=False)

        st.subheader(t("inv.items_title"))
        if "inv_items" not in st.session_state:
            st.session_state.inv_items = [{"sku":"","desc":"","qty":1,"price":0}]
        for i, item in enumerate(st.session_state.inv_items):
            ic1, ic2, ic3, ic4 = st.columns([1,2,1,1])
            item["sku"]   = ic1.text_input("SKU", value=item["sku"], key="is_" + str(i))
            item["desc"]  = ic2.text_input(t("inv.f_desc"), value=item["desc"], key="id_" + str(i))
            item["qty"]   = ic3.number_input(t("inv.f_qty"), value=item["qty"], min_value=1, key="iq_" + str(i))
            item["price"] = ic4.number_input(t("inv.f_price"), value=float(item["price"]),
                                              min_value=0.0, step=10.0, key="ip_" + str(i))

        add_item_btn = st.form_submit_button("+" + t("inv.add_item"))
        create_btn   = st.form_submit_button(t("inv.create_btn"))

        if add_item_btn:
            st.session_state.inv_items.append({"sku":"","desc":"","qty":1,"price":0})
            st.rerun()
        if create_btn:
            if cust_name.strip():
                items_payload = [
                    {"sku": it["sku"], "description": it["desc"],
                     "qty": it["qty"], "unit_price": it["price"]}
                    for it in st.session_state.inv_items if it["desc"] or it["sku"]
                ]
                new_id = inv.create(order_id.strip(), cust_name.strip(),
                                     cust_addr, cust_tax, items_payload,
                                     include_vat, "")
                st.success(t("inv.created") + " #" + str(new_id))
                st.session_state.inv_items = [{"sku":"","desc":"","qty":1,"price":0}]
                st.rerun()
