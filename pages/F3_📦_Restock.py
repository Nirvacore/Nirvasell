"""F3 Restock Planner — when to order, how much, lead time tracking."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import restock_planner as rp
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
rp.init()
render_sidebar()

st.title(t("rstock.title"))
st.caption(t("rstock.caption"))

summary = rp.summary()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("rstock.kpi_critical"), summary["critical"],
          delta_color="inverse" if summary["critical"] > 0 else "off")
c2.metric(t("rstock.kpi_urgent"), summary["urgent"],
          delta_color="inverse" if summary["urgent"] > 0 else "off")
c3.metric(t("rstock.kpi_soon"), summary["soon"],
          delta_color="inverse" if summary["soon"] > 0 else "off")
c4.metric(t("rstock.kpi_cost"), "฿{:,.0f}".format(summary["total_reorder_cost"]))

if summary["critical"] > 0:
    st.error("🚨 " + str(summary["critical"]) + t("rstock.critical_warning"))
elif summary["urgent"] > 0:
    st.warning("⚠️ " + str(summary["urgent"]) + t("rstock.urgent_warning"))

st.divider()

tab_plan, tab_order, tab_pending, tab_config = st.tabs([
    t("rstock.tab_plan"), t("rstock.tab_order"),
    t("rstock.tab_pending"), t("rstock.tab_config")
])

URGENCY_STYLES = {
    "critical": ("🚨", "#c54c4c"),
    "urgent":   ("⚠️", "#c5963d"),
    "soon":     ("🔶", "#c5963d"),
    "ok":       ("✅", "#4d6c5c"),
    "none":     ("—",  "#7a7569"),
}

with tab_plan:
    horizon = st.slider(t("rstock.horizon"), 14, 90, 30)
    plan = rp.plan(days_horizon=int(horizon))
    action_items = [p for p in plan if p["urgency"] in ("critical","urgent","soon")]
    if not action_items:
        st.success(t("rstock.all_ok"))
    else:
        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.83rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("rstock.col_sku"), t("rstock.col_name"), t("rstock.col_stock"),
                    t("rstock.col_velocity"), t("rstock.col_days_out"),
                    t("rstock.col_order_qty"), t("rstock.col_urgency")]:
            table_html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
        table_html += "</tr>"
        for p in plan:
            icon, color = URGENCY_STYLES.get(p["urgency"], ("","#9a9485"))
            table_html += "<tr style='border-top:1px solid #2a2a2a'>"
            table_html += "<td style='padding:4px 8px'>" + p["sku"] + "</td>"
            table_html += "<td style='padding:4px 8px;color:#9a9485'>" + (p["name"] or "—")[:18] + "</td>"
            table_html += "<td style='padding:4px 8px'>" + str(p["stock"]) + "</td>"
            table_html += "<td style='padding:4px 8px;color:#9a9485'>" + str(p["velocity_day"]) + t("rstock.per_day") + "</td>"
            days_out = p["days_until_out"]
            days_str = "∞" if days_out >= 999 else str(int(days_out)) + t("rstock.days")
            table_html += "<td style='padding:4px 8px;color:" + color + "'>" + days_str + "</td>"
            table_html += "<td style='padding:4px 8px;color:#d4d0c8'>" + str(p["reorder_qty"]) + "</td>"
            table_html += "<td style='padding:4px 8px'>" + icon + " " + p["urgency"] + "</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)

with tab_order:
    st.subheader(t("rstock.order_title"))
    plan2 = rp.plan()
    skus_need = [p for p in plan2 if p["reorder_qty"] > 0]
    if not skus_need:
        st.info(t("rstock.nothing_to_order"))
    else:
        with st.form("order_form"):
            sel_sku = st.selectbox(
                t("rstock.sel_sku"),
                [p["sku"] for p in skus_need],
                format_func=lambda s: next((p["sku"] + " — " + (p["name"] or "") +
                                             " (suggest " + str(p["reorder_qty"]) + ")"
                                             for p in skus_need if p["sku"]==s), s),
            )
            sel_p = next((p for p in skus_need if p["sku"]==sel_sku), {})
            col1, col2 = st.columns(2)
            order_qty  = col1.number_input(t("rstock.f_qty"),
                                            value=sel_p.get("reorder_qty", 1),
                                            min_value=1)
            supplier   = col2.text_input(t("rstock.f_supplier"),
                                          value=sel_p.get("supplier",""))
            if st.form_submit_button(t("rstock.order_btn")):
                rp.record_order(sel_sku, int(order_qty), supplier)
                st.success(t("rstock.ordered"))
                st.rerun()

with tab_pending:
    st.subheader(t("rstock.pending_title"))
    pending = rp.pending_orders()
    if not pending:
        st.info(t("rstock.no_pending"))
    else:
        for order in pending:
            col_l, col_r = st.columns([4,1])
            col_l.write("**" + order["sku"] + "** · " + str(order["qty"]) + t("rstock.units") +
                        " · " + (order.get("supplier") or t("rstock.no_supplier")) +
                        " · " + (order.get("ordered_at","")[:10] or "—"))
            if col_r.button(t("rstock.receive_btn"), key="recv_" + str(order["id"])):
                rp.receive_order(order["id"])
                st.success(t("rstock.received"))
                st.rerun()

with tab_config:
    st.subheader(t("rstock.config_title"))
    try:
        import products as _p; _p.init()
        prods = _p.all_products()
    except Exception:
        prods = []
    if not prods:
        st.info(t("rstock.no_products"))
    else:
        sel_sku_c = st.selectbox(t("rstock.sel_sku"), [p["sku"] for p in prods],
                                  key="cfg_sku")
        with st.form("rstock_config_form"):
            col1, col2 = st.columns(2)
            lead_days    = col1.number_input(t("rstock.f_lead_days"), min_value=1, value=7, step=1)
            safety_stock = col2.number_input(t("rstock.f_safety"), min_value=0, value=0, step=5)
            min_order    = col1.number_input(t("rstock.f_min_order"), min_value=1, value=1, step=1)
            supplier_n   = col2.text_input(t("rstock.f_supplier"))
            notes        = st.text_input(t("rstock.f_notes"))
            if st.form_submit_button(t("rstock.save_btn")):
                rp.set_config(sel_sku_c, int(lead_days), int(safety_stock),
                               int(min_order), supplier_n, notes)
                st.success(t("rstock.saved"))
                st.rerun()
