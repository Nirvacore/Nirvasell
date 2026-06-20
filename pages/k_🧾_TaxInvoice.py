"""Tax Invoice (ใบกำกับภาษี) — legal requirement for VAT-registered sellers.

Thai tax invoice with VAT 7%, TIN, running number INV-YYYYMM-NNNN.
Generate → download plain text → print or copy-paste to a form."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import tax_invoice as ti
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Tax Invoice",
                   page_icon="🧾", layout="wide")
apply_theme()
require_auth()
db.init()
ti.init()
render_sidebar()

page_header(icon="🧾", title=t("tax.title"), subtitle=t("tax.caption"))


# ---- KPI overview -----------------------------------------------------------

invoices = ti.all_invoices()
total_revenue = sum(i.get("total", 0) for i in invoices)

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("tax.kpi_total"), str(len(invoices)),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("tax.kpi_revenue"),
        "{:,.0f}".format(total_revenue),
        hint="", hint_tone="ok",
    )
with k3:
    next_no = ti.next_invoice_no()
    metric_with_hint(
        t("tax.kpi_next"), next_no,
        hint="", hint_tone="info",
    )


# ---- Create invoice ----------------------------------------------------------

st.divider()
with st.expander(t("tax.create_title"), expanded=len(invoices) == 0):
    with st.form("create_invoice"):
        st.markdown("**" + t("tax.seller_section") + "**")
        sc1, sc2 = st.columns(2)
        with sc1:
            seller_name = st.text_input(
                t("tax.f_seller_name") + " *",
                value=st.session_state.get("_tax_seller_name", ""),
                placeholder=t("tax.ph_seller_name"),
            )
        with sc2:
            seller_tin = st.text_input(
                t("tax.f_seller_tin") + " *",
                value=st.session_state.get("_tax_seller_tin", ""),
                placeholder="0-0000-00000-00-0",
            )
        seller_addr = st.text_input(
            t("tax.f_seller_addr"),
            value=st.session_state.get("_tax_seller_addr", ""),
            placeholder=t("tax.ph_seller_addr"),
        )

        st.markdown("**" + t("tax.buyer_section") + "**")
        bc1, bc2 = st.columns(2)
        with bc1:
            buyer_name = st.text_input(
                t("tax.f_buyer_name") + " *",
                placeholder=t("tax.ph_buyer_name"),
            )
        with bc2:
            buyer_tin = st.text_input(
                t("tax.f_buyer_tin"),
                placeholder="0-0000-00000-00-0",
            )
        buyer_addr = st.text_input(
            t("tax.f_buyer_addr"),
            placeholder=t("tax.ph_buyer_addr"),
        )

        # Items — up to 10 line items
        st.markdown("**" + t("tax.items_section") + "**")

        items = []
        for row_idx in range(5):
            ic1, ic2, ic3 = st.columns([4, 1, 2])
            with ic1:
                iname = st.text_input(
                    t("tax.f_item_name"),
                    key="_ti_name_" + str(row_idx),
                    placeholder=t("tax.ph_item") if row_idx == 0 else "",
                    label_visibility="collapsed" if row_idx > 0 else "visible",
                )
            with ic2:
                iqty = st.number_input(
                    t("tax.f_item_qty"),
                    min_value=0, value=0, step=1,
                    key="_ti_qty_" + str(row_idx),
                    label_visibility="collapsed" if row_idx > 0 else "visible",
                )
            with ic3:
                iprice = st.number_input(
                    t("tax.f_item_price"),
                    min_value=0.0, value=0.0, step=1.0,
                    key="_ti_price_" + str(row_idx),
                    label_visibility="collapsed" if row_idx > 0 else "visible",
                )

            if iname.strip() and iqty > 0 and iprice > 0:
                items.append({
                    "name": iname.strip(),
                    "qty": int(iqty),
                    "unit_price": float(iprice),
                })

        # Preview totals
        if items:
            subtotal = sum(i["unit_price"] * i["qty"] for i in items)
            vat = round(subtotal * 7 / 100, 2)
            total = round(subtotal + vat, 2)
            st.markdown(
                "<div style='text-align:right;padding:8px 14px;"
                "background:rgba(77,108,92,0.04);border-radius:8px;margin-top:8px'>"
                "<span style='color:#7a7569'>" + t("tax.preview_subtotal", amount="{:,.2f}".format(subtotal)) + "</span>"
                " · <span style='color:#7a7569'>" + t("tax.preview_vat", amount="{:,.2f}".format(vat)) + "</span>"
                " · <strong style='color:#4d6c5c'>" + t("tax.preview_total", amount="{:,.2f}".format(total)) + "</strong></div>",
                unsafe_allow_html=True,
            )

        order_id = st.text_input(
            t("tax.f_order_id"),
            placeholder="SHP-20260601-001",
        )
        note = st.text_input(t("tax.f_note"), placeholder=t("tax.ph_note"))

        if st.form_submit_button(t("tax.create_btn"), type="primary"):
            if not seller_name.strip():
                st.warning(t("tax.need_seller"))
            elif not seller_tin.strip():
                st.warning(t("tax.need_tin"))
            elif not buyer_name.strip():
                st.warning(t("tax.need_buyer"))
            elif not items:
                st.warning(t("tax.need_items"))
            else:
                # Remember seller info
                st.session_state["_tax_seller_name"] = seller_name
                st.session_state["_tax_seller_tin"] = seller_tin
                st.session_state["_tax_seller_addr"] = seller_addr

                result = ti.create_invoice(
                    seller_name=seller_name.strip(),
                    seller_tin=seller_tin.strip(),
                    seller_address=seller_addr.strip(),
                    buyer_name=buyer_name.strip(),
                    items=items,
                    buyer_tin=buyer_tin.strip(),
                    buyer_address=buyer_addr.strip(),
                    order_id=order_id.strip(),
                    note=note.strip(),
                )
                toast(
                    t("tax.created") + " " + result["invoice_no"],
                    icon="✓",
                )
                st.rerun()


# ---- Invoice list + view/download -------------------------------------------

if invoices:
    st.divider()
    st.markdown("### " + t("tax.list_title"))

    for inv in invoices:
        total_str = "{:,.0f}".format(inv.get("total", 0))
        inv_date = (inv.get("invoice_date") or "")[:10]
        buyer = inv.get("buyer_name") or "—"
        oid = inv.get("order_id") or ""

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='display:flex;justify-content:space-between;align-items:center;"
                "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div>"
                "<span style='font-weight:600;font-family:monospace'>" +
                inv["invoice_no"] + "</span>"
                " <span style='color:#7a7569;font-size:12px'>" +
                inv_date + "</span></div>"
                "<div style='display:flex;gap:12px;align-items:center'>"
                "<span style='color:#7a7569;font-size:12px'>" + buyer + "</span>"
                "<span style='font-weight:600;color:#4d6c5c'>"
                "฿" + total_str + "</span></div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            bc1, bc2 = st.columns(2)
            with bc1:
                inv_text = ti.to_text(inv["id"])
                st.download_button(
                    "📥",
                    data=inv_text.encode("utf-8"),
                    file_name=inv["invoice_no"] + ".txt",
                    mime="text/plain",
                    key="_dl_inv_" + str(inv["id"]),
                    type="tertiary",
                )
            with bc2:
                if st.button(
                    "🗑", key="_del_inv_" + str(inv["id"]),
                    type="tertiary",
                ):
                    ti.delete_invoice(inv["id"])
                    st.rerun()


# ---- Preview drawer ----------------------------------------------------------

if invoices:
    st.divider()
    with st.expander("👁 " + t("tax.preview_title"), expanded=False):
        preview_opts = [(i["id"], i["invoice_no"] + " · " + (i.get("buyer_name") or ""))
                        for i in invoices]
        preview_id = st.selectbox(
            t("tax.select_preview"),
            [p[0] for p in preview_opts],
            format_func=lambda k: next(p[1] for p in preview_opts if p[0] == k),
            label_visibility="collapsed",
        )
        if preview_id:
            txt = ti.to_text(preview_id)
            st.code(txt, language=None)
