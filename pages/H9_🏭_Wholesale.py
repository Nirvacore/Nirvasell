"""H9 Wholesale Pricing — tiered price tables and quick quotes."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import wholesale_pricing as wp
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
wp.init()
render_sidebar()

st.title(t("ws.title"))
st.caption(t("ws.caption"))

stats = wp.stats()
c1, c2 = st.columns(2)
c1.metric(t("ws.kpi_skus"), stats.get("skus_with_tiers",0))
c2.metric(t("ws.kpi_tiers"), stats.get("total_tier_entries",0))

st.divider()
tab_tiers, tab_quote, tab_set = st.tabs([
    t("ws.tab_tiers"), t("ws.tab_quote"), t("ws.tab_set")
])

with tab_tiers:
    skus_wt = wp.skus_with_tiers()
    if not skus_wt:
        st.info(t("ws.empty"))
    for sku_info in skus_wt:
        sku   = sku_info if isinstance(sku_info, str) else sku_info.get("sku","?")
        name  = sku_info.get("name","") if isinstance(sku_info, dict) else ""
        tiers = wp.get_tiers(sku)
        label = "🏭 **" + (name or sku) + "**" + (" · " + sku if name else "")
        with st.expander(label):
            if tiers:
                tier_html = "<table style='width:100%;border-collapse:collapse;font-size:0.83rem'>"
                tier_html += "<tr style='color:#9a9485'>"
                for col in [t("ws.min_qty"), t("ws.price"), t("ws.note")]:
                    tier_html += "<th style='text-align:left;padding:3px 8px'>" + col + "</th>"
                tier_html += "</tr>"
                for tier in tiers:
                    tier_html += "<tr style='border-top:1px solid #2a2a2a'>"
                    tier_html += "<td style='padding:3px 8px'>" + str(tier.get("min_qty",1)) + "+" + "</td>"
                    tier_html += "<td style='padding:3px 8px;color:#d4d0c8'>฿{:,.2f}".format(tier.get("price",0)) + "</td>"
                    tier_html += "<td style='padding:3px 8px;color:#9a9485'>" + (tier.get("note","") or "") + "</td>"
                    tier_html += "</tr>"
                tier_html += "</table>"
                st.html(tier_html)

with tab_quote:
    st.subheader(t("ws.quote_title"))
    skus_for_quote = wp.skus_with_tiers()
    available_skus = [s if isinstance(s,str) else s.get("sku","?") for s in skus_for_quote]
    if not available_skus:
        st.info(t("ws.empty"))
    else:
        if "quote_items" not in st.session_state:
            st.session_state.quote_items = [{"sku": available_skus[0] if available_skus else "", "qty": 1}]
        for i, qi in enumerate(st.session_state.quote_items):
            col1, col2, col3 = st.columns([2,1,1])
            qi["sku"] = col1.selectbox(t("ws.f_sku"), available_skus,
                                        index=available_skus.index(qi["sku"])
                                        if qi["sku"] in available_skus else 0,
                                        key="qs_" + str(i))
            qi["qty"] = col2.number_input(t("ws.f_qty"), min_value=1, value=qi["qty"],
                                           key="qq_" + str(i))
            price_at  = wp.price_for_qty(qi["sku"], qi["qty"])
            col3.metric(t("ws.price_per_unit"), "฿{:,.2f}".format(price_at) if price_at else "—")

        col_a, col_c = st.columns(2)
        if col_a.button("+" + t("ws.add_line")):
            st.session_state.quote_items.append({"sku": available_skus[0], "qty":1})
            st.rerun()
        if col_c.button(t("ws.calc_quote"), type="primary"):
            result = wp.quick_quote([(qi["sku"], qi["qty"]) for qi in st.session_state.quote_items])
            total  = sum(r.get("subtotal",0) for r in result) if result else 0
            st.subheader("฿{:,.2f}".format(total))
            if result:
                for r in result:
                    st.write(t("ws.quote_line",
                               sku=r.get("sku", "?"),
                               qty=str(r.get("qty", 0)),
                               price="{:,.2f}".format(r.get("unit_price", 0)),
                               subtotal="{:,.2f}".format(r.get("subtotal", 0))))

with tab_set:
    st.subheader(t("ws.set_tiers_title"))
    with st.form("ws_tiers_form"):
        col1, col2 = st.columns(2)
        sku_input  = col1.text_input(t("ws.f_sku_input"), placeholder=t("common.sku_ph"))
        tier_count = col2.number_input(t("ws.f_tier_count"), min_value=1, max_value=8, value=3)

        tiers_input = []
        for i in range(int(tier_count)):
            tc1, tc2, tc3 = st.columns([1,2,2])
            min_qty = tc1.number_input(t("ws.min_qty"), min_value=1,
                                        value=[1,10,50][i] if i < 3 else (i+1)*20,
                                        key="wmin_" + str(i))
            price   = tc2.number_input(t("ws.price"), min_value=0.0, step=5.0,
                                        key="wprc_" + str(i))
            note    = tc3.text_input(t("ws.note"), key="wnote_" + str(i))
            tiers_input.append({"min_qty": int(min_qty), "price": price, "note": note})

        if st.form_submit_button(t("ws.save_tiers")):
            if sku_input.strip():
                wp.set_tiers(sku_input.strip(), tiers_input)
                st.success(t("ws.tiers_saved"))
                st.rerun()
