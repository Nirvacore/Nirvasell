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
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("skutr.kpi_rising"), summary.get("rising_count",0))
c2.metric(t("skutr.kpi_declining"), summary.get("declining_count",0),
          delta_color="inverse" if summary.get("declining_count",0) > 0 else "off")
c3.metric(t("skutr.kpi_new"), summary.get("new_count",0))
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
    rising = skut.rising_stars(min_change=10)
    if not rising:
        st.info(t("skutr.no_rising"))
    for r in rising:
        pct  = r.get("change_pct",0)
        sku  = r.get("sku","?")
        name = r.get("name") or sku
        row_html = (
            "<div style='margin:4px 0;font-size:0.84rem'>"
            "<div style='color:#d4d0c8'>🚀 <b>" + name + "</b>"
            " <span style='color:#9a9485'>(" + sku + ")</span></div>"
            "<div style='margin-top:2px'>" + _trend_bar(pct, True) +
            "<span style='color:#9a9485;margin-left:8px'>prev " +
            str(r.get("prev_qty",0)) + " → " + str(r.get("curr_qty",0)) + t("skutr.units") +
            "</span></div></div>"
        )
        st.html(row_html)

with tab_declining:
    declining = skut.declining(min_change=-10)
    if not declining:
        st.success(t("skutr.no_declining"))
    for d in declining:
        pct  = d.get("change_pct",0)
        sku  = d.get("sku","?")
        name = d.get("name") or sku
        row_html = (
            "<div style='margin:4px 0;font-size:0.84rem'>"
            "<div style='color:#d4d0c8'>📉 <b>" + name + "</b>"
            " <span style='color:#9a9485'>(" + sku + ")</span></div>"
            "<div style='margin-top:2px'>" + _trend_bar(pct, False) +
            "<span style='color:#9a9485;margin-left:8px'>prev " +
            str(d.get("prev_qty",0)) + " → " + str(d.get("curr_qty",0)) + t("skutr.units") +
            "</span></div></div>"
        )
        st.html(row_html)

with tab_new:
    new_prods = skut.new_products(days=14)
    if not new_prods:
        st.info(t("skutr.no_new"))
    for p in new_prods:
        sku  = p.get("sku","?")
        name = p.get("name") or sku
        qty  = p.get("total_qty",0)
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
    weekly = skut.weekly_trend(weeks=int(weeks))
    if not weekly:
        st.info(t("skutr.empty"))
    else:
        skus = list({r.get("sku","?") for r in weekly})[:12]
        for sku in skus:
            rows = [r for r in weekly if r.get("sku") == sku]
            name = rows[0].get("name") or sku if rows else sku
            st.write("**" + name + "**")
            max_qty = max(r.get("qty",0) for r in rows) or 1
            row_html = "<div style='display:flex;gap:4px;margin-bottom:8px'>"
            for r in rows:
                q  = r.get("qty",0)
                bh = max(int(q / max_qty * 40), 2)
                row_html += ("<div style='display:flex;flex-direction:column;align-items:center;"
                             "font-size:0.7rem;color:#9a9485'>"
                             "<div style='background:#4d6c5c;width:20px;height:" + str(bh) +
                             "px;margin-bottom:2px'></div>" +
                             str(q) + "</div>")
            row_html += "</div>"
            st.html(row_html)
