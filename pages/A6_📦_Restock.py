"""Restock Planner — when to reorder, how much, from whom.

Sales velocity + lead time = optimal reorder point and quantity."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import restock_planner as rp
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Restock",
                   page_icon="📦", layout="wide")
apply_theme()
require_auth()
db.init()
rp.init()
render_sidebar()

page_header(icon="📦", title=t("rst.title"), subtitle=t("rst.caption"))

s = rp.summary()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("🔴 " + t("rst.kpi_critical"), str(s["critical"]),
                     hint=t("rst.critical_hint") if s["critical"] > 0 else "",
                     hint_tone="danger" if s["critical"] > 0 else "ok")
with k2:
    metric_with_hint("🟡 " + t("rst.kpi_urgent"), str(s["urgent"]),
                     hint="", hint_tone="warn" if s["urgent"] > 0 else "ok")
with k3:
    metric_with_hint("🟢 " + t("rst.kpi_ok"), str(s["ok"]),
                     hint="", hint_tone="ok")
with k4:
    metric_with_hint("💰 " + t("rst.kpi_cost"), "฿{:,.0f}".format(s["total_reorder_cost"]),
                     hint=t("rst.cost_hint"), hint_tone="info")


# ---- Pending restock orders -------------------------------------------------

pending = rp.pending_orders()
if pending:
    st.divider()
    st.markdown("### 📬 " + t("rst.pending_title") + " (" + str(len(pending)) + ")")

    for po in pending:
        pc1, pc2 = st.columns([5, 1])
        with pc1:
            st.markdown(
                "<div style='padding:6px 14px;border-left:3px solid #c5963d'>"
                "📦 <strong>" + po["sku"] + "</strong>"
                " · " + t("rst.reorder_pieces", n=str(po["qty"])) +
                " · " + (po["supplier"] or "—") +
                " <span style='color:#9a9485;font-size:11px'>"
                + (po["ordered_at"] or "")[:10] + "</span></div>",
                unsafe_allow_html=True,
            )
        with pc2:
            if st.button("✅ " + t("rst.received_btn"), key="_rcv_" + str(po["id"]),
                          type="tertiary"):
                rp.receive_order(po["id"])
                toast(t("rst.received_msg"), icon="✅")
                st.rerun()


# ---- Restock plan -----------------------------------------------------------

st.divider()
st.markdown("### " + t("rst.plan_title"))

plan = rp.plan()
if not plan:
    st.info(t("rst.empty"))
    st.stop()

urgency_filter = st.selectbox(
    t("rst.f_filter"),
    ["all", "critical", "urgent", "soon", "ok"],
    format_func=lambda x: {
        "all": "🔍 " + t("rst.filter_all"),
        "critical": "🔴 " + t("rst.filter_critical"),
        "urgent": "🟡 " + t("rst.filter_urgent"),
        "soon": "🔵 " + t("rst.filter_soon"),
        "ok": "🟢 " + t("rst.filter_ok"),
    }.get(x, x),
    key="_rst_filter",
)

filtered = plan if urgency_filter == "all" else [
    p for p in plan if p["urgency"] == urgency_filter
]

for item in filtered:
    urg = item["urgency"]
    urg_icon = {"critical": "🔴", "urgent": "🟡", "soon": "🔵", "ok": "🟢",
                "none": "⚪"}.get(urg, "?")
    urg_color = {"critical": "#c54c4c", "urgent": "#c5963d", "soon": "#4a7ab5",
                 "ok": "#4d6c5c", "none": "#9a9485"}.get(urg, "#7a7569")

    days_out = item["days_until_out"]
    days_str = str(int(days_out)) + " " + t("rst.days") if days_out < 999 else "∞"

    ic1, ic2 = st.columns([5, 1])
    with ic1:
        st.markdown(
            "<div style='padding:10px 14px;border-left:3px solid " + urg_color + ";"
            "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            "<span>" + urg_icon + " <strong>" + item["sku"] + "</strong>"
            " · " + (item["name"] or "")[:30] + "</span>"
            "<span style='font-size:12px;color:#9a9485'>"
            + (item["supplier"] or "") + "</span></div>"
            "<div style='display:flex;gap:16px;font-size:12px;color:#7a7569;margin-top:4px'>"
            "<span>" + t("rst.line_stock", n=str(item["stock"])) + "</span>"
            "<span>" + t("rst.line_velocity", n=str(item["velocity_day"])) + "</span>"
            "<span>" + t("rst.line_days_out", label=days_str) + "</span>"
            "<span>" + t("rst.line_reorder") + " <strong style='color:" + urg_color + "'>"
            + t("rst.reorder_pieces", n=str(item["reorder_qty"])) + "</strong></span>"
            + ("<span>฿" + "{:,.0f}".format(item["reorder_cost"]) + "</span>"
               if item["reorder_cost"] > 0 else "") +
            "</div></div>",
            unsafe_allow_html=True,
        )
    with ic2:
        if item["reorder_qty"] > 0:
            if st.button("🛒", key="_ord_" + item["sku"], type="tertiary"):
                rp.record_order(item["sku"], item["reorder_qty"],
                                item["supplier"])
                toast(t("rst.ordered_msg"), icon="🛒")
                st.rerun()


# ---- Configure lead times ---------------------------------------------------

st.divider()
with st.expander(t("rst.config_title")):
    with st.form("rst_config"):
        with db.conn() as c:
            products = c.execute("SELECT sku, name FROM products ORDER BY sku").fetchall()

        if products:
            sku_opts = [p["sku"] + " — " + (p["name"] or "")[:30] for p in products]
            sel_idx = st.selectbox(t("rst.f_sku"), range(len(sku_opts)),
                                   format_func=lambda i: sku_opts[i])
            sel_sku = products[sel_idx]["sku"]
        else:
            sel_sku = st.text_input(t("rst.f_sku"))

        cfc1, cfc2, cfc3 = st.columns(3)
        with cfc1:
            cfg_lead = st.number_input(t("rst.f_lead_days"), min_value=1,
                                       value=7, step=1)
        with cfc2:
            cfg_safety = st.number_input(t("rst.f_safety_stock"), min_value=0,
                                         value=5, step=1)
        with cfc3:
            cfg_moq = st.number_input(t("rst.f_min_qty"), min_value=1,
                                      value=10, step=1)

        cfg_supplier = st.text_input(t("rst.f_supplier"))

        if st.form_submit_button(t("rst.save_btn"), type="primary"):
            rp.set_config(sel_sku, cfg_lead, cfg_safety, cfg_moq, cfg_supplier)
            toast(t("rst.config_saved"), icon="✓")
            st.rerun()
