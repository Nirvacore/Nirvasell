"""H5 Stock Turnover — see how fast inventory moves and what's sitting."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import stock_turnover as st_mod
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("turn.title"))
st.caption(t("turn.caption"))

summary = st_mod.summary()
c1, c2, c3 = st.columns(3)
c1.metric(t("turn.kpi_avg"), str(summary.get("avg_turnover_ratio",0)) + "x")
c2.metric(t("turn.kpi_fast"), summary.get("fast_movers",0))
c3.metric(t("turn.kpi_slow"), summary.get("slow_movers",0),
          delta_color="inverse" if summary.get("slow_movers",0) > 3 else "off")

st.divider()
tab_all, tab_reorder = st.tabs([t("turn.tab_all"), t("turn.tab_reorder")])

with tab_all:
    items = st_mod.calculate()
    if not items:
        st.info(t("turn.empty"))
    else:
        # Sort by turnover ratio descending
        items_sorted = sorted(items, key=lambda x: x.get("turnover_ratio",0), reverse=True)
        max_ratio = items_sorted[0].get("turnover_ratio",1) if items_sorted else 1
        for item in items_sorted:
            ratio   = item.get("turnover_ratio",0)
            doh     = item.get("days_on_hand",0)
            sku     = item.get("sku","?")
            name    = item.get("name") or sku
            stock   = item.get("current_stock",0)
            bar_color = "#4d6c5c" if ratio >= 2 else ("#c5963d" if ratio >= 1 else "#c54c4c")
            bar_w   = int(ratio / max_ratio * 160) if max_ratio > 0 else 0
            row_html = (
                "<div style='margin:4px 0;font-size:0.83rem'>"
                "<div style='color:#d4d0c8'>" + name + " <span style='color:#9a9485'>(" + sku + ")</span>"
                + t("turn.item_stock_doh", stock=str(stock), doh=str(doh)) +
                "</div>"
                "<div style='display:flex;align-items:center;gap:6px;margin-top:2px'>"
                "<div style='background:" + bar_color + ";width:" + str(bar_w) + "px;height:8px'></div>"
                "<span style='color:" + bar_color + ";font-size:0.82rem'>" +
                str(ratio) + "x</span>"
                "</div></div>"
            )
            st.html(row_html)

with tab_reorder:
    reorder = st_mod.reorder_list()
    if not reorder:
        st.success(t("turn.no_reorder"))
    else:
        st.write(t("turn.reorder_hint"))
        for item in reorder:
            sku  = item.get("sku","?")
            name = item.get("name") or sku
            doh  = item.get("days_on_hand",0)
            reorder_qty = item.get("suggested_reorder_qty",0)
            urgency = "🔴" if doh < 7 else "🟡"
            r_html = (
                "<div style='margin:3px 0;font-size:0.84rem;display:flex;gap:8px'>"
                "<span>" + urgency + "</span>"
                "<span style='color:#d4d0c8;width:160px'>" + name + "</span>"
                "<span style='color:#9a9485'>" + str(doh) + t("turn.days_left") + "</span>"
                "<span style='color:#c5963d;margin-left:8px'>→ " +
                t("turn.reorder") + " " + str(reorder_qty) + t("turn.pcs") +
                "</span></div>"
            )
            st.html(r_html)
