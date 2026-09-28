"""H6 SKU Trends — rising stars, declining SKUs, and new products."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import sku_trends as skut
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("skutr.title"))
st.caption(t("skutr.caption"))

summary = skut.summary()
new_evidence = skut.new_products_summary(days=14)
if not summary["evidence_complete"] or not new_evidence["evidence_complete"]:
    st.warning(
        "SKU trends unavailable: incomplete order/product evidence "
        f"(trend orders {summary['missing_order_evidence_rows']}; "
        f"new-product orders {new_evidence['missing_order_evidence_rows']}; "
        f"new products {new_evidence['missing_product_evidence_rows']})."
    )
    st.stop()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("skutr.kpi_rising"), summary.get("rising",0))
c2.metric(t("skutr.kpi_declining"), summary.get("declining",0),
          delta_color="inverse" if summary.get("declining",0) > 0 else "off")
c3.metric(t("skutr.kpi_new"), len(new_evidence["items"]))
c4.metric(t("skutr.kpi_total"), summary.get("total_skus",0))

st.divider()
tab_rising, tab_declining, tab_new, tab_weekly = st.tabs([
    t("skutr.tab_rising"), t("skutr.tab_declining"),
    t("skutr.tab_new"), t("skutr.tab_weekly")
])

def _trend_bar(pct, positive=True):
    bar_color = "#4d6c5c" if positive else "#c54c4c"
    bar_w = min(int(abs(pct) * 2), 160)
    return (
        "<div style='display:inline-flex;align-items:center;gap:4px'>"
        "<div style='background:" + bar_color + ";width:" + str(bar_w) + "px;height:8px'></div>"
        "<span style='color:" + bar_color + ";font-size:0.82rem'>" +
        ("+" if positive else "") + str(round(pct,1)) + "%</span></div>"
    )

with tab_rising:
    rising = [
        item for item in summary["items"]
        if item["trend"] == "rising"
    ]
    if not rising:
        st.info(t("skutr.no_rising"))
    for r in rising:
        pct  = r.get("qty_change_pct",0)
        sku  = r.get("sku","?")
        name = r.get("name") or sku
        row_html = (
            "<div style='margin:4px 0;font-size:0.84rem'>"
            "<div style='color:#d4d0c8'>🚀 <b>" + name + "</b>"
            " <span style='color:#9a9485'>(" + sku + ")</span></div>"
            "<div style='margin-top:2px'>" + _trend_bar(pct, True) +
            "<span style='color:#9a9485;margin-left:8px'>prev " +
            str(r.get("qty_last_week",0)) + " → " + str(r.get("qty_this_week",0)) + t("skutr.units") +
            "</span></div></div>"
        )
        st.html(row_html)

with tab_declining:
    declining = [item for item in summary["items"] if item["trend"] == "declining"]
    if not declining:
        st.success(t("skutr.no_declining"))
    for d in declining:
        pct  = d.get("qty_change_pct",0)
        sku  = d.get("sku","?")
        name = d.get("name") or sku
        row_html = (
            "<div style='margin:4px 0;font-size:0.84rem'>"
            "<div style='color:#d4d0c8'>📉 <b>" + name + "</b>"
            " <span style='color:#9a9485'>(" + sku + ")</span></div>"
            "<div style='margin-top:2px'>" + _trend_bar(pct, False) +
            "<span style='color:#9a9485;margin-left:8px'>prev " +
            str(d.get("qty_last_week",0)) + " → " + str(d.get("qty_this_week",0)) + t("skutr.units") +
            "</span></div></div>"
        )
        st.html(row_html)

with tab_new:
    new_prods = new_evidence["items"]
    if not new_prods:
        st.info(t("skutr.no_new"))
    for p in new_prods:
        sku  = p.get("sku","?")
        name = p.get("name") or sku
        qty  = p.get("total_sold",0)
        rev  = p.get("total_revenue",0)
        new_html = (
            "<div style='margin:4px 0;font-size:0.84rem'>"
            "✨ <b style='color:#d4d0c8'>" + name + "</b>"
            " <span style='color:#9a9485'>(" + sku + ")</span>"
            " · " + str(qty) + t("skutr.units") +
            " · ฿{:,.0f}".format(rev) +
            "</div>"
        )
        st.html(new_html)

with tab_weekly:
    weeks = st.slider(t("skutr.weeks"), 2, 8, 4)
    weekly_evidence = skut.trend_summary(weeks=int(weeks))
    if not weekly_evidence["evidence_complete"]:
        st.warning("SKU weekly trends unavailable: incomplete order evidence.")
        st.stop()
    weekly = weekly_evidence["items"]
    if not weekly:
        st.info(t("skutr.empty"))
    else:
        for item in weekly[:12]:
            sku = item.get("sku", "?")
            name = item.get("name") or sku
            st.write("**" + name + "**")
            series = list(reversed(list(item.get("weeks", {}).items())))
            max_qty = max((values.get("qty", 0) for _, values in series), default=0) or 1
            row_html = "<div style='display:flex;gap:4px;margin-bottom:8px'>"
            for label, values in series:
                q = values.get("qty", 0)
                bh = max(int(q / max_qty * 40), 2)
                row_html += ("<div style='display:flex;flex-direction:column;align-items:center;"
                             "font-size:0.7rem;color:#9a9485'>"
                             "<div style='background:#4d6c5c;width:20px;height:" + str(bh) +
                             "px;margin-bottom:2px'></div>" +
                             label + ": " + str(q) + "</div>")
            row_html += "</div>"
            st.html(row_html)
