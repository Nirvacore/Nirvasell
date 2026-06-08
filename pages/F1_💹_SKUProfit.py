"""F1 SKU Profit — true profit per product after fees, returns, COGS."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import sku_profit as sp
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("skup.title"))
st.caption(t("skup.caption"))

with st.spinner(t("skup.loading")):
    summary = sp.summary()

c1, c2, c3, c4 = st.columns(4)
c1.metric(t("skup.kpi_skus"), summary["total_skus"])
c2.metric(t("skup.kpi_profitable"), summary["profitable"],
          delta_color="normal" if summary["profitable"] > 0 else "off")
c3.metric(t("skup.kpi_losing"), summary["losing"],
          delta_color="inverse" if summary["losing"] > 0 else "off")
c4.metric(t("skup.kpi_avg_margin"), str(summary["avg_margin"]) + "%",
          delta_color="normal" if summary["avg_margin"] > 20 else "inverse")

st.divider()

HEALTH_ICONS = {
    "healthy": ("✅", "#4d6c5c"),
    "warning": ("⚠️", "#c5963d"),
    "thin":    ("🟡", "#c5963d"),
    "losing":  ("❌", "#c54c4c"),
}

tab_all, tab_losers, tab_stars = st.tabs([
    t("skup.tab_all"), t("skup.tab_losers"), t("skup.tab_stars")
])

def _sku_table(skus: list):
    if not skus:
        st.info(t("skup.empty"))
        return
    table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.83rem'>"
    table_html += "<tr style='color:#9a9485'>"
    for col in [t("skup.col_sku"), t("skup.col_name"), t("skup.col_qty"),
                t("skup.col_revenue"), t("skup.col_net"), t("skup.col_margin"),
                t("skup.col_ppu"), t("skup.col_health")]:
        table_html += "<th style='text-align:left;padding:4px 8px'>" + col + "</th>"
    table_html += "</tr>"
    for s in skus:
        icon, color = HEALTH_ICONS.get(s["health"], ("", "#9a9485"))
        table_html += "<tr style='border-top:1px solid #2a2a2a'>"
        table_html += "<td style='padding:4px 8px'>" + (s["sku"] or "—") + "</td>"
        table_html += "<td style='padding:4px 8px;color:#9a9485'>" + (s["name"] or "—")[:20] + "</td>"
        table_html += "<td style='padding:4px 8px'>" + str(s["total_qty"]) + "</td>"
        table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(s["total_revenue"]) + "</td>"
        table_html += "<td style='padding:4px 8px;color:" + color + "'>฿{:,.0f}".format(s["net_profit"]) + "</td>"
        table_html += "<td style='padding:4px 8px;color:" + color + "'>" + str(s["net_margin"]) + "%</td>"
        table_html += "<td style='padding:4px 8px'>฿{:,.0f}".format(s["profit_per_unit"]) + "</td>"
        table_html += "<td style='padding:4px 8px'>" + icon + "</td>"
        table_html += "</tr>"
    table_html += "</table>"
    st.html(table_html)

with tab_all:
    with st.spinner(t("skup.loading")):
        all_skus = sp.per_sku_profit()
    sort_key = st.segmented_control(
        t("skup.sort_by"),
        ["net_profit","net_margin","total_revenue","total_qty"],
        format_func=lambda k: {
            "net_profit": t("skup.sort_profit"),
            "net_margin": t("skup.sort_margin"),
            "total_revenue": t("skup.sort_revenue"),
            "total_qty": t("skup.sort_qty"),
        }.get(k, k),
        default="net_profit",
    )
    sorted_skus = sorted(all_skus, key=lambda x: x.get(sort_key or "net_profit", 0), reverse=True)
    _sku_table(sorted_skus[:50])

with tab_losers:
    with st.spinner(t("skup.loading")):
        all_s = sp.per_sku_profit()
    losers = [s for s in all_s if s["net_profit"] < 0]
    if not losers:
        st.success(t("skup.no_losers"))
    else:
        st.warning("⚠️ " + str(len(losers)) + t("skup.loser_count"))
        _sku_table(sorted(losers, key=lambda x: x["net_profit"]))

with tab_stars:
    with st.spinner(t("skup.loading")):
        all_s2 = sp.per_sku_profit()
    stars = [s for s in all_s2 if s["health"] == "healthy"]
    st.write("**" + str(len(stars)) + t("skup.star_count") + "**")
    _sku_table(sorted(stars, key=lambda x: x["net_profit"], reverse=True)[:20])
