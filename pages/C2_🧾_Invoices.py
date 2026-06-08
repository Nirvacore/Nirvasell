"""Invoice Generator — Thai-style tax invoice / receipt."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import invoices as iv
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Invoices",
                   page_icon="🧾", layout="wide")
apply_theme()
require_auth()
db.init()
iv.init()
render_sidebar()

page_header(icon="🧾", title=t("inv.title"), subtitle=t("inv.caption"))

s = iv.stats()
k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint("🧾 " + t("inv.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("💰 " + t("inv.kpi_revenue"),
                     "฿{:,.0f}".format(s["total_revenue"]),
                     hint="", hint_tone="ok")
with k3:
    metric_with_hint("📅 " + t("inv.kpi_this_month"),
                     "฿{:,.0f}".format(s["this_month"]),
                     hint="", hint_tone="info")

# ---- Create invoice ---------------------------------------------------------
st.divider()
with st.expander(t("inv.create_title"), expanded=False):
    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name, sell_price FROM products ORDER BY sku"
        ).fetchall()

    ic1, ic2 = st.columns(2)
    with ic1:
        order_id = st.text_input(t("inv.f_order_id"), placeholder="ORD-001")
        customer_name = st.text_input(t("inv.f_customer"),
                                      placeholder=t("inv.customer_ph"))
        customer_address = st.text_area(t("inv.f_address"),
                                        placeholder=t("inv.address_ph"),
                                        height=80)
    with ic2:
        customer_tax_id = st.text_input(t("inv.f_tax_id"),
                                        placeholder=t("inv.tax_id_ph"))
        include_vat = st.checkbox(t("inv.f_vat"), value=False)
        inv_notes = st.text_input(t("inv.f_notes"), placeholder="")

    st.markdown("#### " + t("inv.items_title"))
    num_items = st.slider(t("inv.f_num_items"), 1, 8, 3, key="_inv_ni")
    inv_items = []

    for idx in range(num_items):
        row_c1, row_c2, row_c3 = st.columns(3)
        with row_c1:
            if products:
                p_opts = [p["sku"] + " — " + (p["name"] or "")[:20]
                          for p in products]
                pi = st.selectbox(t("inv.f_sku"), range(len(p_opts)),
                                  format_func=lambda i: p_opts[i],
                                  key="_isku_" + str(idx))
                sku_val = products[pi]["sku"]
                desc_val = products[pi]["name"] or sku_val
                default_price = float(products[pi]["sell_price"] or 0)
            else:
                sku_val = st.text_input(t("inv.f_sku"), key="_isku_t_" + str(idx))
                desc_val = sku_val
                default_price = 0.0
        with row_c2:
            qty = st.number_input(t("inv.f_qty"), min_value=1, value=1,
                                  step=1, key="_iqty_" + str(idx))
        with row_c3:
            unit_price = st.number_input(t("inv.f_price"),
                                         value=default_price,
                                         min_value=0.0, step=10.0,
                                         key="_iprice_" + str(idx))
        inv_items.append({
            "sku": sku_val,
            "description": desc_val,
            "qty": qty,
            "unit_price": unit_price,
        })

    subtotal = sum(i["qty"] * i["unit_price"] for i in inv_items)
    vat = round(subtotal * 0.07, 2) if include_vat else 0
    st.markdown(
        "<div style='text-align:right;padding:8px 0'>"
        "ยอดก่อน VAT: ฿{:,.2f}".format(subtotal) +
        (" · VAT 7%: ฿{:,.2f}".format(vat) if include_vat else "") +
        " · <strong>รวม: ฿{:,.2f}".format(subtotal + vat) + "</strong></div>",
        unsafe_allow_html=True,
    )

    if st.button(t("inv.create_btn"), type="primary", key="_inv_create"):
        inv_id = iv.create(
            order_id=order_id.strip(),
            customer_name=customer_name.strip(),
            customer_address=customer_address.strip(),
            customer_tax_id=customer_tax_id.strip(),
            items=inv_items,
            include_vat=include_vat,
            notes=inv_notes.strip(),
        )
        toast(t("inv.created"), icon="🧾")
        st.session_state["preview_invoice"] = inv_id
        st.rerun()

# ---- Preview last created ---------------------------------------------------
if st.session_state.get("preview_invoice"):
    inv_id = st.session_state["preview_invoice"]
    st.divider()
    st.markdown("### 🧾 " + t("inv.preview_title"))
    rendered = iv.render_text(inv_id)
    if rendered:
        st.code(rendered, language=None)

# ---- Invoice list -----------------------------------------------------------
st.divider()
st.markdown("### " + t("inv.list_title"))

all_inv = iv.all_invoices()
if not all_inv:
    st.info(t("inv.empty"))
    st.stop()

for inv_row in all_inv:
    st.markdown(
        "<div style='display:flex;justify-content:space-between;"
        "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<span>🧾 <strong>" + inv_row["invoice_number"] + "</strong>"
        " · " + (inv_row.get("customer_name") or t("inv.no_customer")) + "</span>"
        "<span style='display:flex;gap:12px;font-size:13px'>"
        "<span style='color:#4d6c5c;font-weight:600'>"
        "฿{:,.2f}".format(inv_row["total"]) + "</span>"
        "<span style='font-size:11px;color:#9a9485'>"
        + (inv_row.get("issued_at") or "")[:10] + "</span></span></div>",
        unsafe_allow_html=True,
    )
    if st.button(t("inv.view_btn"), key="_vw_" + str(inv_row["id"]),
                 type="tertiary"):
        st.session_state["preview_invoice"] = inv_row["id"]
        st.rerun()
