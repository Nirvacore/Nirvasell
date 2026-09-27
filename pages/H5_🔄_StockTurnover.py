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
if not summary.get("evidence_complete", True):
    st.warning(
        "Stock-turnover evidence is incomplete: "
        + str(summary.get("missing_order_evidence_rows", 0))
        + " order row(s), "
        + str(summary.get("missing_product_evidence_rows", 0))
        + " product row(s). Exact turnover is unavailable."
    )
    st.stop()

c1, c2, c3 = st.columns(3)
avg_turnover = summary.get("avg_turnover")
c1.metric(t("turn.kpi_avg"), "—" if avg_turnover is None else str(avg_turnover) + "x")
c2.metric(t("turn.kpi_fast"), summary.get("health",{}).get("fast",0))
c3.metric(t("turn.kpi_slow"), summary.get("health",{}).get("slow",0),
          delta_color="inverse" if summary.get("health",{}).get("slow",0) > 3 else "off")

st.divider()
tab_all, tab_reorder = st.tabs([t("turn.tab_all"), t("turn.tab_reorder")])

with tab_all:
    items = st_mod.calculate()
    if not items:
        st.info(t("turn.empty"))
    else:
        # Sort by turnover ratio descending
        items_sorted = sorted(
            items,
            key=lambda x: x.get("turnover_rate") if x.get("turnover_rate") is not None else -1,
            reverse=True,
        )
        available_ratios = [
            item["turnover_rate"] for item in items_sorted
            if item.get("turnover_rate") is not None
        ]
        max_ratio = max(available_ratios) if available_ratios else 1
        for item in items_sorted:
            ratio   = item.get("turnover_rate")
            doh     = item.get("doi",0)
            sku     = item.get("sku","?")
            name    = item.get("name") or sku
            stock   = item.get("stock",0)
            bar_color = (
                "#7a7569" if ratio is None else
                ("#4d6c5c" if ratio >= 2 else ("#c5963d" if ratio >= 1 else "#c54c4c"))
            )
            bar_w   = int(ratio / max_ratio * 160) if ratio is not None and max_ratio > 0 else 0
            ratio_label = "—" if ratio is None else str(ratio) + "x"
            row_html = (
                "<div style='margin:4px 0;font-size:0.83rem'>"
                "<div style='color:#d4d0c8'>" + name + " <span style='color:#9a9485'>(" + sku + ")</span>"
                + t("turn.item_stock_doh", stock=str(stock), doh=str(doh)) +
                "</div>"
                "<div style='display:flex;align-items:center;gap:6px;margin-top:2px'>"
                "<div style='background:" + bar_color + ";width:" + str(bar_w) + "px;height:8px'></div>"
                "<span style='color:" + bar_color + ";font-size:0.82rem'>" +
                ratio_label + "</span>"
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
            doh  = item.get("doi",0)
            reorder_qty = item.get("reorder_point",0)
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
