"""G9 Tax Invoice — VAT-compliant tax invoices with running serial numbers."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import tax_invoice as ti
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
ti.init()
render_sidebar()

st.title(t("tax.title"))
st.caption(t("tax.caption"))

all_tax = ti.all_invoices()
c1, c2 = st.columns(2)
c1.metric(t("tax.kpi_total"), len(all_tax))
total_vat = sum((inv.get("vat_amount") or 0) for inv in all_tax)
c2.metric(t("tax.kpi_vat"), "฿{:,.0f}".format(total_vat))

next_no = ti.next_invoice_no()
st.info("📄 " + t("tax.next_no") + ": **" + next_no + "**")

st.divider()
tab_list, tab_create = st.tabs([t("tax.tab_list"), t("tax.tab_create")])

with tab_list:
    if not all_tax:
        st.info(t("tax.empty"))
    for inv in all_tax:
        iid = inv.get("inv_id") or inv.get("id","?")
        inv_no = inv.get("invoice_no") or str(iid)
        label = ("📄 **" + inv_no + "**"
                 + " · " + (inv.get("customer_name") or "—")
                 + " · ฿{:,.0f}".format(inv.get("total_amount",0))
                 + " (VAT ฿{:,.0f})".format(inv.get("vat_amount",0)))
        with st.expander(label):
            col1, col2 = st.columns(2)
            col1.write(t("tax.tax_id") + ": " + (inv.get("customer_tax_id") or "—"))
            col2.write(t("tax.date") + ": " + (inv.get("invoice_date") or "—"))
            col_v, col_d = st.columns(2)
            if col_v.button(t("tax.view_text"), key="txv_" + str(iid)):
                txt = ti.to_text(iid)
                st.code(txt, language=None)
            if col_d.button(t("tax.delete"), key="txd_" + str(iid)):
                ti.delete_invoice(iid); st.rerun()

with tab_create:
    st.subheader(t("tax.create_title"))
    with st.form("tax_form"):
        col1, col2 = st.columns(2)
        cust_name = col1.text_input(t("tax.f_customer"), placeholder=t("tax.f_customer_hint"))
        cust_tax  = col2.text_input(t("tax.f_tax_id"), placeholder="0-0000-00000-00-0")
        cust_addr = st.text_area(t("tax.f_address"), height=60)

        st.subheader(t("tax.items_title") + " (VAT " + str(ti.VAT_RATE) + "%)")
        if "tax_items" not in st.session_state:
            st.session_state.tax_items = [{"desc":"","qty":1,"price":0}]
        for i, item in enumerate(st.session_state.tax_items):
            ic1, ic2, ic3 = st.columns([3,1,2])
            item["desc"]  = ic1.text_input(t("tax.f_desc"), value=item["desc"], key="td_" + str(i))
            item["qty"]   = ic2.number_input(t("tax.f_qty"), value=item["qty"], min_value=1, key="tq_" + str(i))
            item["price"] = ic3.number_input(t("tax.f_price"), value=float(item["price"]),
                                              min_value=0.0, step=10.0, key="tp_" + str(i))

        subtotal = sum(it["qty"] * it["price"] for it in st.session_state.tax_items)
        vat_amt  = round(subtotal * ti.VAT_RATE / 100, 2)
        st.write(t("tax.subtotal") + ": ฿{:,.2f}".format(subtotal))
        st.write(t("tax.vat") + " (" + str(ti.VAT_RATE) + "%): ฿{:,.2f}".format(vat_amt))
        st.write("**" + t("tax.total") + ": ฿{:,.2f}**".format(subtotal + vat_amt))

        notes = st.text_input(t("tax.f_notes"))
        add_item_btn = st.form_submit_button("+" + t("tax.add_item"))
        create_btn   = st.form_submit_button(t("tax.create_btn"))

        if add_item_btn:
            st.session_state.tax_items.append({"desc":"","qty":1,"price":0})
            st.rerun()
        if create_btn:
            if cust_name.strip():
                items_payload = [
                    {"description": it["desc"], "qty": it["qty"],
                     "unit_price": it["price"]}
                    for it in st.session_state.tax_items if it["desc"]
                ]
                new_id = ti.create_invoice(
                    customer_name=cust_name.strip(),
                    customer_tax_id=cust_tax,
                    customer_address=cust_addr,
                    items=items_payload,
                    notes=notes
                )
                st.success(t("tax.created"))
                st.session_state.tax_items = [{"desc":"","qty":1,"price":0}]
                st.rerun()
