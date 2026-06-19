"""Purchase Orders — create POs to suppliers, track receipt, auto-update stock."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date, timedelta
import db
import purchase_orders as po
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Purchase Orders",
                   page_icon="🛒", layout="wide")
apply_theme()
require_auth()
db.init()
po.init()
render_sidebar()

page_header(icon="🛒", title=t("po.title"), subtitle=t("po.caption"))

s = po.summary()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📋 " + t("po.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("📤 " + t("po.kpi_pending"), str(s["pending_count"]),
                     hint="", hint_tone="warn" if s["pending_count"] > 0 else "ok")
with k3:
    metric_with_hint("💰 " + t("po.kpi_value"),
                     "฿{:,.0f}".format(s["pending_value"]),
                     hint="", hint_tone="info")
with k4:
    metric_with_hint("⚠️ " + t("po.kpi_overdue"), str(s["overdue"]),
                     hint=t("po.overdue_hint") if s["overdue"] > 0 else "",
                     hint_tone="danger" if s["overdue"] > 0 else "ok")

# ---- Create PO --------------------------------------------------------------
st.divider()
with st.expander(t("po.create_title"), expanded=False):
    with db.conn() as c:
        products = c.execute(
            "SELECT sku, name, cost_price FROM products ORDER BY sku"
        ).fetchall()
    suppliers_raw = []
    try:
        with db.conn() as c:
            sup_rows = c.execute(
                "SELECT name FROM suppliers ORDER BY name"
            ).fetchall()
            suppliers_raw = [r["name"] for r in sup_rows]
    except Exception:
        pass

    if not products:
        st.info(t("po.no_products"))
    else:
        st.markdown("#### " + t("po.f_supplier"))
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            supplier_name = st.text_input(
                t("po.f_supplier"),
                placeholder=t("po.supplier_ph"),
                label_visibility="collapsed",
            )
        with pc2:
            exp_date = st.date_input(
                t("po.f_expected"),
                value=date.today() + timedelta(days=7),
            )
        with pc3:
            po_notes = st.text_input(t("po.f_notes"), placeholder="")

        st.markdown("#### " + t("po.items_title"))
        num_items = st.slider(t("po.f_num_items"), 1, 10, 3, key="_po_ni")

        prod_opts = [p["sku"] + " — " + (p["name"] or "")[:25] for p in products]
        items_data = []
        for idx in range(num_items):
            c1, c2, c3 = st.columns(3)
            with c1:
                si = st.selectbox(
                    t("po.f_sku"),
                    range(len(prod_opts)),
                    format_func=lambda i: prod_opts[i],
                    key="_po_sku_" + str(idx),
                    label_visibility="collapsed",
                )
            with c2:
                qty = st.number_input(
                    t("po.f_qty"), min_value=1, value=10, step=1,
                    key="_po_qty_" + str(idx),
                    label_visibility="collapsed",
                )
            with c3:
                unit_cost = st.number_input(
                    t("po.f_cost"),
                    value=float(products[si]["cost_price"] or 0),
                    min_value=0.0, step=10.0,
                    key="_po_cost_" + str(idx),
                    label_visibility="collapsed",
                )
            items_data.append({
                "sku": products[si]["sku"],
                "name": products[si]["name"] or "",
                "qty": qty,
                "unit_cost": unit_cost,
            })

        total_val = sum(i["qty"] * i["unit_cost"] for i in items_data)
        st.markdown(
            "<div style='text-align:right;font-size:1.1rem;font-weight:600;"
            "padding:8px 0'>รวม: ฿{:,.0f}</div>".format(total_val),
            unsafe_allow_html=True,
        )

        if st.button(t("po.create_btn"), type="primary", key="_po_create"):
            if supplier_name.strip():
                po_id = po.create(
                    supplier=supplier_name.strip(),
                    items=items_data,
                    expected_date=str(exp_date),
                    notes=po_notes.strip(),
                )
                toast(t("po.created"), icon="✓")
                st.rerun()
            else:
                st.warning(t("po.need_supplier"))

# ---- Active POs -------------------------------------------------------------
st.divider()
st.markdown("### " + t("po.active_title"))

active = po.all_pos()
if not active:
    st.info(t("po.empty"))
    st.stop()

for order in active:
    st_info = order["status_info"]
    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:10px 14px;border:0.5px solid rgba(40,30,20,0.07);"
        "border-left:4px solid " + (st_info.get("color") or "#9a9485") + ";"
        "border-radius:8px;background:white;margin-bottom:6px'>"
        "<div>"
        + st_info.get("icon", "📋") + " <strong>" + order["po_number"] + "</strong>"
        " · " + order["supplier"] +
        " <span style='font-size:11px;color:#9a9485'>"
        + order["order_date"][:10] +
        (" → " + order["expected_date"][:10] if order.get("expected_date") else "") +
        "</span></div>"
        "<div style='display:flex;gap:12px;align-items:center'>"
        "<span style='font-size:12px'>" + str(order["item_count"]) + " รายการ</span>"
        "<span style='font-weight:600'>฿{:,.0f}".format(order["total_amount"]) + "</span>"
        "<span style='font-size:12px;color:" + (st_info.get("color") or "#9a9485") + ";font-weight:600'>"
        + st_info.get("label_th", order["status"]) + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    if order["status"] in ("sent", "partial"):
        with st.expander(t("po.receive_title") + " — " + order["po_number"]):
            details = po.get(order["id"])
            for item in details.get("items", []):
                if item["pending_qty"] > 0:
                    rc1, rc2 = st.columns([4, 1])
                    with rc1:
                        st.markdown(
                            "<span style='font-size:13px'><strong>" +
                            item["sku"] + "</strong> · " +
                            (item.get("product_name") or "")[:25] +
                            " · " + t("po.ordered_qty", n=item["qty_ordered"]) +
                            " " + t("po.received_qty", n=item["qty_received"]) +
                            " <strong style='color:#c54c4c'>" +
                            t("po.waiting_qty", n=item["pending_qty"]) + "</strong></span>",
                            unsafe_allow_html=True,
                        )
                    with rc2:
                        recv_qty = st.number_input(
                            "recv",
                            min_value=0,
                            max_value=item["pending_qty"],
                            value=item["pending_qty"],
                            key="_recv_" + str(order["id"]) + "_" + item["sku"],
                            label_visibility="collapsed",
                        )
                    if st.button(
                        t("po.receive_btn"),
                        key="_po_rcv_" + str(order["id"]) + "_" + item["sku"],
                        type="tertiary",
                    ):
                        po.receive_item(order["id"], item["sku"], recv_qty)
                        toast(t("po.received_msg"), icon="✅")
                        st.rerun()
