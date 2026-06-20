"""E1 Order Analytics — deep order pattern analysis."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import order_analytics as oa
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar
from i18n_inline import day_name

apply_theme()
require_auth()
render_sidebar()

st.title(t("ana.title"))
st.caption(t("ana.caption"))

tab_aov, tab_time, tab_platform, tab_repeat = st.tabs([
    t("ana.tab_aov"), t("ana.tab_time"),
    t("ana.tab_platform"), t("ana.tab_repeat")
])

with tab_aov:
    st.subheader(t("ana.aov_title"))
    months = st.slider(t("ana.months"), 2, 12, 6, key="aov_months")
    aov_data = oa.aov_trend(months=months)
    if aov_data:
        max_aov = max((r["aov"] or 0) for r in aov_data) or 1
        for r in aov_data:
            aov = r["aov"] or 0
            bar_w = int((aov / max_aov) * 200)
            color = "#4d6c5c" if aov > 0 else "#2a2a2a"
            row_html = (
                "<div style='margin:3px 0;font-size:0.85rem'>"
                "<span style='color:#9a9485;width:80px;display:inline-block'>"
                + (r["month"] or "—") + "</span>"
                "<div style='display:inline-block;background:" + color +
                ";width:" + str(bar_w) + "px;height:14px;vertical-align:middle'></div>"
                " <span style='color:#d4d0c8'>" + t("chan.line_aov", amount="{:,.0f}".format(aov)) +
                " · " + str(r["orders"]) + t("ana.orders_unit") + "</span>"
                "</div>"
            )
            st.html(row_html)
    else:
        st.info(t("ana.empty"))

with tab_time:
    st.subheader(t("ana.time_title"))
    hourly = oa.hourly_distribution()
    if hourly:
        st.write(t("ana.hourly_title"))
        max_h = max((r["count"] or 0) for r in hourly) or 1
        for r in hourly:
            cnt = r["count"] or 0
            bar_w = int((cnt / max_h) * 180)
            h = r["hour"]
            label = str(h).zfill(2) + ":00"
            h_html = (
                "<div style='margin:2px 0;font-size:0.83rem'>"
                "<span style='color:#9a9485;width:55px;display:inline-block'>" + label + "</span>"
                "<div style='display:inline-block;background:#3a5a8a;width:" +
                str(bar_w) + "px;height:10px;vertical-align:middle'></div>"
                " <span style='color:#d4d0c8'>" + str(cnt) + "</span>"
                "</div>"
            )
            st.html(h_html)
    st.divider()
    daily = oa.daily_distribution()
    if daily:
        st.write(t("ana.daily_title"))
        max_d = max((r["count"] or 0) for r in daily) or 1
        for r in daily:
            cnt = r["count"] or 0
            bar_w = int((cnt / max_d) * 180)
            dow = r["dow"]
            name = day_name(dow)
            d_html = (
                "<div style='margin:2px 0;font-size:0.83rem'>"
                "<span style='color:#9a9485;width:80px;display:inline-block'>" + name + "</span>"
                "<div style='display:inline-block;background:#5a4a8a;width:" +
                str(bar_w) + "px;height:10px;vertical-align:middle'></div>"
                " <span style='color:#d4d0c8'>" + str(cnt) + "</span>"
                "</div>"
            )
            st.html(d_html)
    if not hourly and not daily:
        st.info(t("ana.empty"))

with tab_platform:
    st.subheader(t("ana.platform_title"))
    months2 = st.slider(t("ana.months"), 2, 12, 6, key="plat_months")
    trend = oa.platform_trend(months=months2)
    if trend:
        platforms = list({r["platform"] for r in trend if r["platform"]})
        for p in platforms:
            p_data = [r for r in trend if r["platform"] == p]
            if p_data:
                total_rev = sum(r["revenue"] or 0 for r in p_data)
                st.write(t("ana.platform_revenue_line",
                           platform=p or t("common.platform_direct"),
                           amount="{:,.0f}".format(total_rev)))
    else:
        st.info(t("ana.empty"))
    st.divider()
    top = oa.top_combos(limit=5)
    if top:
        st.write("**" + t("ana.combos_title") + "**")
        for c in top:
            st.write(t("ana.combo_line",
                       sku_a=c["sku_a"] or "?",
                       sku_b=c["sku_b"] or "?",
                       n=str(c["freq"]),
                       times=t("ana.times")))

with tab_repeat:
    st.subheader(t("ana.repeat_title"))
    rr = oa.repeat_purchase_rate()
    r1, r2, r3 = st.columns(3)
    r1.metric(t("ana.total_buyers"), rr["total_buyers"])
    r2.metric(t("ana.repeat_buyers"), rr["repeat_buyers"])
    r3.metric(t("ana.repeat_rate"), str(rr["repeat_rate"]) + "%",
              delta_color="normal" if rr["repeat_rate"] > 20 else "inverse")

    if rr["repeat_rate"] < 20:
        st.warning(t("ana.repeat_low_hint"))
    else:
        st.success(t("ana.repeat_good_hint"))

    st.divider()
    peak_h = oa.peak_hours(top_n=3)
    if peak_h:
        st.write("**" + t("ana.peak_hours_title") + "**")
        for h in peak_h:
            rev = h.get("revenue") or 0
            st.write(t("ana.peak_hour_line",
                       hour=str(h["hour"]).zfill(2),
                       n=str(h["count"]),
                       orders_unit=t("ana.orders_unit"),
                       amount="{:,.0f}".format(rev)))
    best = oa.best_day()
    if best:
        dow = best.get("dow", 0)
        name = day_name(dow)
        rev = best.get("revenue") or 0
        st.write("**" + t("ana.best_day") + "**: " +
                 t("ana.best_day_line", day=name, amount="{:,.0f}".format(rev)))
