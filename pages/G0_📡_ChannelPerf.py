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
c1.metric(t("ch.kpi_revenue"), "฿{:,.0f}".format(summary.get("total_revenue",0)))
c2.metric(t("ch.kpi_orders"), summary.get("total_orders",0))
c3.metric(t("ch.kpi_platforms"), summary.get("active_platforms",0))

st.divider()

tab_compare, tab_growth = st.tabs([t("ch.tab_compare"), t("ch.tab_growth")])

with tab_compare:
    platforms = cp.platform_comparison(days=int(days or 30))
    if not platforms:
        st.info(t("ch.empty"))
    else:
        max_rev = max(p.get("revenue",0) for p in platforms) or 1
        for p in platforms:
            rev   = p.get("revenue",0)
            aov   = p.get("aov",0)
            orders = p.get("orders",0)
            rr    = p.get("return_rate",0)
            bar_w = int(rev / max_rev * 220)
            color = "#4d6c5c" if rev == max_rev else "#3a4a4a"
            p_html = (
                "<div style='margin:6px 0'>"
                "<div style='font-size:0.85rem;color:#d4d0c8'><b>" +
                (p.get("platform") or "direct") + "</b>"
                " · " + str(orders) + t("ch.orders") +
                " · " + t("chan.line_aov", amount="{:,.0f}".format(aov)) +
                " · return " + str(rr) + "%</div>"
                "<div style='display:flex;align-items:center;gap:8px;margin-top:3px'>"
                "<div style='background:" + color + ";width:" + str(bar_w) +
                "px;height:14px'></div>"
                "<span style='color:#d4d0c8;font-size:0.84rem'>฿{:,.0f}".format(rev) +
                "</span></div></div>"
            )
            st.html(p_html)

with tab_growth:
    months = st.slider(t("ch.months"), 2, 12, 3)
    growth = cp.growth_by_platform(months=int(months))
    if not growth:
        st.info(t("ch.empty"))
    else:
        plats = list({r["platform"] for r in growth if r.get("platform")})
        for plat in plats:
            g_rows = [r for r in growth if r.get("platform") == plat]
            if g_rows:
                st.write("**" + plat + "**")
                for r in g_rows:
                    grow_pct = r.get("growth_pct", 0)
                    color = "#4d6c5c" if grow_pct >= 0 else "#c54c4c"
                    g_html = (
                        "<div style='margin:2px 0;font-size:0.83rem'>"
                        "<span style='color:#9a9485;width:80px;display:inline-block'>" +
                        (r.get("month","") or "—") + "</span>"
                        "฿{:,.0f}".format(r.get("revenue",0)) +
                        " <span style='color:" + color + ";margin-left:8px'>" +
                        ("+" if grow_pct >= 0 else "") + str(grow_pct) + "%</span>"
                        "</div>"
                    )
                    st.html(g_html)
