"""G0 Channel Performance — compare platforms by revenue, orders, growth."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import channel_perf as cp
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("ch.title"))
st.caption(t("ch.caption"))

days = st.segmented_control(t("ch.period"), [7,30,90],
    format_func=lambda d: str(d) + t("ch.days"), default=30)

summary = cp.summary(days=int(days or 30))
c1, c2, c3 = st.columns(3)
total_revenue = summary.get("total_revenue")
c1.metric(
    t("ch.kpi_revenue"),
    "฿{:,.0f}".format(total_revenue) if total_revenue is not None else "—",
)
c2.metric(t("ch.kpi_orders"), summary.get("total_orders",0))
c3.metric(t("ch.kpi_platforms"), summary.get("active_platforms",0))

if not summary.get("evidence_complete", False):
    st.warning(
        "⚠️ ข้อมูลยอดขาย/ต้นทุนไม่ครบ · Revenue and profit metrics unavailable"
    )

st.divider()

tab_compare, tab_growth = st.tabs([t("ch.tab_compare"), t("ch.tab_growth")])

with tab_compare:
    platforms = cp.platform_comparison(days=int(days or 30))
    if not platforms:
        st.info(t("ch.empty"))
    else:
        complete_revenues = [
            p["revenue"] for p in platforms if p.get("revenue") is not None
        ]
        max_rev = max(complete_revenues, default=0) or 1
        for p in platforms:
            rev   = p.get("revenue")
            aov   = p.get("aov")
            orders = p.get("orders",0)
            rr    = p.get("return_rate",0)
            bar_w = int(rev / max_rev * 220) if rev is not None else 0
            color = "#4d6c5c" if rev is not None and rev == max_rev else "#3a4a4a"
            revenue_text = "฿{:,.0f}".format(rev) if rev is not None else "—"
            aov_text = "{:,.0f}".format(aov) if aov is not None else "—"
            p_html = (
                "<div style='margin:6px 0'>"
                "<div style='font-size:0.85rem;color:#d4d0c8'><b>" +
                (p.get("platform") or t("common.platform_direct")) + "</b>"
                " · " + str(orders) + t("ch.orders") +
                " · " + t("chan.line_aov", amount=aov_text) +
                " · " + t("ch.return_rate", n=str(rr)) + "</div>"
                "<div style='display:flex;align-items:center;gap:8px;margin-top:3px'>"
                "<div style='background:" + color + ";width:" + str(bar_w) +
                "px;height:14px'></div>"
                "<span style='color:#d4d0c8;font-size:0.84rem'>" + revenue_text +
                "</span></div></div>"
            )
            st.html(p_html)

with tab_growth:
    months = st.slider(t("ch.months"), 2, 12, 3)
    growth = cp.growth_by_platform(months=int(months))
    if not growth:
        st.info(t("ch.empty"))
    else:
        for row in growth:
            plat = row.get("platform") or t("common.platform_direct")
            st.write("**" + plat + "**")
            grow_pct = row.get("growth_pct")
            color = (
                "#4d6c5c" if grow_pct is not None and grow_pct >= 0
                else ("#c54c4c" if grow_pct is not None else "#9a9485")
            )
            growth_sign = "+" if grow_pct is not None and grow_pct >= 0 else ""
            growth_text = str(grow_pct) if grow_pct is not None else "—"
            months_data = row.get("months", {})
            latest_month = max(months_data, default=None)
            for month, revenue in sorted(months_data.items()):
                revenue_text = (
                    "฿{:,.0f}".format(revenue) if revenue is not None else "—"
                )
                growth_label = (
                    t("ch.growth_pct", sign=growth_sign, pct=growth_text)
                    if month == latest_month else ""
                )
                g_html = (
                    "<div style='margin:2px 0;font-size:0.83rem'>"
                    "<span style='color:#9a9485;width:80px;display:inline-block'>"
                    + month + "</span>" + revenue_text
                    + " <span style='color:" + color + ";margin-left:8px'>"
                    + growth_label + "</span></div>"
                )
                st.html(g_html)
