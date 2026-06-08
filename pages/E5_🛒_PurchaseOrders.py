"""E5 Purchase Orders — create POs, track supplier orders, receive stock."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import purchase_orders as po
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
po.init()
render_sidebar()

st.title(t("po.title"))
st.caption(t("po.caption"))

summary = po.summary()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("po.kpi_total"), summary["total"])
c2.metric(t("po.kpi_pending"), summary["pending_count"],
          delta_color="inverse" if summary["pending_count"] > 0 else "off")
c3.metric(t("po.kpi_value"), "฿{:,.0f}".format(summary["pending_value"]))
c4.metric(t("po.kpi_overdue"), summary["overdue"],
          delta_color="inverse" if summary["overdue"] > 0 else "off")

if summary["overdue"] > 0:
    st.warning("⚠️ " + str(summary["overdue"]) + t("po.overdue_warning"))

st.divider()

tab_list, tab_create, tab_receive = st.tabs([
    t("po.tab_list"), t("po.tab_create"), t("po.tab_receive")
])

with tab_list:
    status_f = st.segmented_control(
        t("po.status_filter"),
        ["all"] + list(po.STATUSES.keys()),
        format_func=lambda s: t("po.all") if s=="all" else
                              po.STATUSES.get(s,{}).get("label_th", s),
        default="all",
    )
    orders = po.all_pos(status=None if status_f=="all" else status_f)
    if not orders:
        st.info(t("po.empty"))
    for order in orders:
        si = order.get("status_info", {})
        icon = si.get("icon","📋")
        label = icon + " **" + order["po_number"] + "**" + \
                " · " + order["supplier"] + \
                " · ฿{:,.0f}".format(order["total_amount"]) + \
                " · " + (order.get("expected_date","") or t("po.no_date"))
        with st.expander(label):
            full = po.get(order["id"])
            col1, col2 = st.columns(2)
            col1.write(t("po.order_date") + ": " + (order.get("order_date","") or "—"))
            col2.write(t("po.expected_date") + ": " + (order.get("expected_date","") or "—"))
            if order.get("notes"):
                st.caption(order["notes"])
            if full.get("items"):
                table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.83rem'><tr style='color:#9a9485'>"
                for col in [t("po.col_sku"), t("po.col_name"), t("po.col_ordered"), t("po.col_received"), t("po.col_cost")]:
                    table_html += "<th style='text-align:left;padding:3px 6px'>" + col + "</th>"
                table_html += "</tr>"
                for item in full["items"]:
                    rem = item["qty_ordered"] - item["qty_received"]
                    color = "#4d6c5c" if rem == 0 else "#c5963d"
                    table_html += "<tr style='border-top:1px solid #2a2a2a'>"
                    table_html += "<td style='padding:3px 6px'>" + (item["sku"] or "—") + "</td>"
                    table_html += "<td style='padding:3px 6px'>" + (item["product_name"] or "—") + "</td>"
                    table_html += "<td style='padding:3px 6px'>" + str(item["qty_ordered"]) + "</td>"
                    table_html += "<td style='padding:3px 6px;color:" + color + "'>" + str(item["qty_received"]) + "</td>"
                    table_html += "<td style='padding:3px 6px'>฿{:,.0f}".format(item["unit_cost"]) + "</td>"
                    table_html += "</tr>"
                table_html += "</table>"
                st.html(table_html)
            col_s, col_c = st.columns(2)
            if order["status"] == "draft":
                if col_s.button(t("po.send_btn"), key="pos_" + str(order["id"])):
                    po.send(order["id"])
                    st.rerun()
            if order["status"] not in ("received","cancelled"):
                if col_c.button(t("po.cancel_btn"), key="poc_" + str(order["id"])):
                    po.cancel(order["id"])
                    st.rerun()

with tab_create:
    st.subheader(t("po.create_title"))
    supplier = st.text_input(t("po.f_supplier"))
    expected = st.text_input(t("po.f_expected"), placeholder="YYYY-MM-DD")
    notes    = st.text_input(t("po.f_notes"))
    st.write(t("po.items_title"))
    if "po_items" not in st.session_state:
        st.session_state.po_items = [{"sku":"","name":"","qty":1,"unit_cost":0.0}]

    items_data = st.session_state.po_items
    updated_items = []
    for i, item in enumerate(items_data):
        col1, col2, col3, col4, col5 = st.columns([2,2,1,1.5,0.5])
        sku  = col1.text_input(t("po.col_sku"), value=item["sku"], key="pi_sku_" + str(i))
        name = col2.text_input(t("po.col_name"), value=item["name"], key="pi_nm_" + str(i))
        qty  = col3.number_input(t("po.col_qty"), value=item["qty"], min_value=1, key="pi_qty_" + str(i))
        cost = col4.number_input(t("po.col_unit_cost"), value=float(item["unit_cost"]),
                                  min_value=0.0, step=1.0, key="pi_cost_" + str(i))
        del_item = col5.button("✕", key="pi_del_" + str(i))
        if not del_item:
            updated_items.append({"sku":sku,"name":name,"qty":qty,"unit_cost":cost})
    st.session_state.po_items = updated_items

    col_add, col_create = st.columns(2)
    if col_add.button(t("po.add_item_btn")):
        st.session_state.po_items.append({"sku":"","name":"","qty":1,"unit_cost":0.0})
        st.rerun()

    total_preview = sum(i["qty"] * i["unit_cost"] for i in st.session_state.po_items)
    st.write(t("po.total_preview") + ": ฿{:,.0f}".format(total_preview))

    if col_create.button(t("po.create_btn")):
        if supplier.strip() and any(i["sku"] for i in st.session_state.po_items):
            po.create(supplier.strip(), st.session_state.po_items, expected, notes)
            st.session_state.po_items = [{"sku":"","name":"","qty":1,"unit_cost":0.0}]
            st.success(t("po.created"))
            st.rerun()
        else:
            st.error(t("po.need_supplier"))

with tab_receive:
    st.subheader(t("po.receive_title"))
    open_pos = po.all_pos(status="sent") + po.all_pos(status="partial")
    if not open_pos:
        st.info(t("po.no_open"))
    else:
        sel_po_id = st.selectbox(
            t("po.sel_po"),
            [p["id"] for p in open_pos],
            format_func=lambda i: next((p["po_number"] + " — " + p["supplier"]
                                         for p in open_pos if p["id"]==i), ""),
        )
        po_detail = po.get(sel_po_id)
        if po_detail and po_detail.get("items"):
            with st.form("receive_form"):
                receives = {}
                for item in po_detail["items"]:
                    remaining = item["qty_ordered"] - item["qty_received"]
                    if remaining > 0:
                        qty_rec = st.number_input(
                            item["sku"] + " · " + t("po.receive_qty") +
                            " (max " + str(remaining) + ")",
                            min_value=0, max_value=remaining,
                            value=remaining, key="recv_" + item["sku"]
                        )
                        receives[item["sku"]] = qty_rec
                if st.form_submit_button(t("po.confirm_receive")):
                    for sku, qty in receives.items():
                        if qty > 0:
                            po.receive_item(sel_po_id, sku, qty)
                    st.success(t("po.received"))
                    st.rerun()
