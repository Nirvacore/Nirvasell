"""COD Tracker — the hidden profit killer every Thai seller ignores.

60%+ of Thai e-commerce is COD. Failed COD = double shipping cost + zero
revenue. This page tracks COD vs prepaid, monitors pending collection,
and reveals the true cost of cash-on-delivery."""
from __future__ import annotations
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import cod_tracker as cod
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · COD",
                   page_icon="📮", layout="wide")
apply_theme()
require_auth()
db.init()
cod.init()
render_sidebar()

page_header(icon="📮", title=t("cod.title"), subtitle=t("cod.caption"))


# ---- KPI overview -----------------------------------------------------------

s = cod.stats()

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    metric_with_hint(
        t("cod.kpi_total"), str(s["total"]),
        hint="COD: " + str(s["cod_count"]) + " · Prepaid: " + str(s["prepaid_count"]),
        hint_tone="info",
    )
with k2:
    cod_tone = "warn" if s["cod_pct"] > 60 else "ok"
    metric_with_hint(
        t("cod.kpi_cod_pct"), "{:.0f}%".format(s["cod_pct"]),
        hint=t("cod.hint_cod_high") if s["cod_pct"] > 60 else "",
        hint_tone=cod_tone,
    )
with k3:
    ret_tone = "danger" if s["cod_return_rate"] > 10 else ("warn" if s["cod_return_rate"] > 5 else "ok")
    metric_with_hint(
        t("cod.kpi_return_rate"), "{:.1f}%".format(s["cod_return_rate"]),
        hint=t("cod.hint_return_high") if s["cod_return_rate"] > 10 else "",
        hint_tone=ret_tone,
    )
with k4:
    metric_with_hint(
        t("cod.kpi_pending"), "{:,.0f}".format(s["pending_amount"]),
        hint=t("cod.hint_pending"),
        hint_tone="warn" if s["pending_amount"] > 5000 else "info",
    )
with k5:
    metric_with_hint(
        t("cod.kpi_lost"), "{:,.0f}".format(s["lost_shipping"]),
        hint=t("cod.hint_lost"),
        hint_tone="danger" if s["lost_shipping"] > 500 else "info",
    )


# ---- Add COD order ----------------------------------------------------------

st.divider()
st.markdown("### " + t("cod.add_title"))

with st.form("add_cod"):
    c1, c2, c3 = st.columns(3)
    with c1:
        n_order = st.text_input(t("cod.f_order_id"), placeholder="ORD-12345")
        n_buyer = st.text_input(t("cod.f_buyer"), placeholder=t("cod.buyer_placeholder"))
    with c2:
        n_plat = st.selectbox(
            t("cod.f_platform"),
            ["shopee", "lazada", "tiktok", "shopify", "other"],
            format_func=lambda p: {
                "shopee": "🛒 Shopee", "lazada": "🟧 Lazada",
                "tiktok": "🎵 TikTok", "shopify": "🛍 Shopify",
                "other": "📝 Other",
            }.get(p, p),
        )
        n_type = st.selectbox(
            t("cod.f_payment_type"),
            ["cod", "prepaid"],
            format_func=lambda p: {
                "cod": "📮 COD",
                "prepaid": "💳 Prepaid",
            }.get(p, p),
        )
    with c3:
        n_amount = st.number_input(t("cod.f_amount"), min_value=0.0, step=10.0, format="%.0f")
        n_ship = st.number_input(t("cod.f_shipping"), min_value=0.0, step=5.0, format="%.0f")

    if st.form_submit_button(t("cod.add_btn"), type="primary"):
        if n_order.strip():
            cod.add(
                order_id=n_order.strip(),
                platform=n_plat,
                amount=n_amount,
                shipping_cost=n_ship,
                payment_type=n_type,
                buyer_name=n_buyer.strip(),
            )
            toast(t("cod.added"), icon="✓")
            st.rerun()
        else:
            st.warning(t("cod.need_order_id"))


# ---- Pending collection (delivered but cash not received) -------------------

st.divider()
st.markdown("### " + t("cod.pending_title"))
st.caption(t("cod.pending_help"))

pending = cod.pending_collection()
if pending:
    for p in pending:
        days_ago = ""
        if p.get("delivered_at"):
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(p["delivered_at"])
                delta = (datetime.now() - dt).days
                days_ago = str(delta) + " " + t("dashboard.days")
            except Exception:
                pass

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05);"
                "background:rgba(197,150,61,0.04);border-radius:8px;margin-bottom:4px'>"
                "<div><strong>" + (p.get("order_id") or "—") + "</strong>"
                " <span style='color:#7a7569;font-size:12px'>" +
                (p.get("buyer_name") or "") + " · " +
                (p.get("platform") or "") + "</span></div>"
                "<div style='display:flex;gap:14px;align-items:center'>"
                "<span style='font-variant-numeric:tabular-nums;font-weight:600;"
                "color:#c5963d'>฿" + "{:,.0f}".format(p.get("amount", 0)) + "</span>"
                "<span style='color:#9a9485;font-size:12px'>" + days_ago + "</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            if st.button("💰 " + t("cod.mark_collected"), key="_cod_col_" + str(p["id"]),
                         type="tertiary"):
                cod.update_status(p["id"], "collected")
                toast(t("cod.collected"), icon="💰")
                st.rerun()
else:
    st.success(t("cod.no_pending"))


# ---- Platform breakdown -----------------------------------------------------

st.divider()
st.markdown("### " + t("cod.by_platform"))

bp = cod.by_platform()
if bp:
    for r in bp:
        plat = r.get("platform", "?")
        ptype = r.get("payment_type", "?")
        icon = {"shopee": "🛒", "lazada": "🟧", "tiktok": "🎵"}.get(plat, "📦")
        type_icon = "📮" if ptype == "cod" else "💳"
        returns = r.get("returns", 0)
        ret_badge = ""
        if returns > 0:
            ret_badge = " <span style='color:#c54c4c;font-size:12px'>↩ " + str(returns) + "</span>"

        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div>" + icon + " " + plat.title() + " " + type_icon + " " +
            ptype.upper() + " · " + t("common.n_orders", n=str(r["count"])) + ret_badge + "</div>"
            "<div style='font-variant-numeric:tabular-nums'>฿" +
            "{:,.0f}".format(r.get("revenue", 0)) + "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
else:
    st.caption(t("cod.no_data"))


# ---- Full order list --------------------------------------------------------

st.divider()
st.markdown("### " + t("cod.history"))

orders = cod.all_orders()
if orders:
    for o in orders:
        status = o.get("status", "pending")
        s_icon = cod.STATUS_ICONS.get(status, "⏳")
        ptype_icon = "📮" if o.get("payment_type") == "cod" else "💳"
        plat = o.get("platform", "")

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;justify-content:space-between'>"
                "<div>" + s_icon + " " + (o.get("order_id") or "—") +
                " " + ptype_icon + " <span style='color:#7a7569;font-size:12px'>" +
                (o.get("buyer_name") or "") + " · " + plat + "</span></div>"
                "<div style='font-variant-numeric:tabular-nums;font-weight:500'>"
                "฿" + "{:,.0f}".format(o.get("amount", 0)) + "</div></div>"
                "<div style='color:#9a9485;font-size:11px'>" +
                (o.get("created_at") or "")[:10] +
                " · " + t("cod.status_" + status) + "</div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            col_btns = st.columns(3)
            next_status = {
                "pending": "shipped",
                "shipped": "delivered",
                "delivered": "collected",
            }
            ns = next_status.get(status)
            if ns:
                with col_btns[0]:
                    ns_icon = cod.STATUS_ICONS.get(ns, "→")
                    if st.button(ns_icon, key="_cs_" + str(o["id"]),
                                 type="tertiary",
                                 help=t("cod.status_" + ns)):
                        cod.update_status(o["id"], ns)
                        st.rerun()
            if status not in ("returned", "cancelled", "collected"):
                with col_btns[1]:
                    if st.button("↩", key="_cr_" + str(o["id"]),
                                 type="tertiary", help=t("cod.mark_returned")):
                        cod.update_status(o["id"], "returned")
                        st.rerun()
            with col_btns[2]:
                if st.button("🗑", key="_cd_" + str(o["id"]),
                             type="tertiary", help=t("common.delete")):
                    cod.delete(o["id"])
                    st.rerun()
else:
    st.info(t("cod.empty"))
