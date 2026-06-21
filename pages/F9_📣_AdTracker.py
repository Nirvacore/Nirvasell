"""F9 Ad ROI Tracker — track ad spend vs revenue per campaign."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import ads_tracker as at
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import platform_name
from sidebar import render_sidebar

apply_theme()
require_auth()
at.init()
render_sidebar()

st.title(t("ads.title"))
st.caption(t("ads.caption"))

stats = at.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("ads.kpi_spent"), "฿{:,.0f}".format(stats.get("total_spent",0)))
c2.metric(t("ads.kpi_revenue"), "฿{:,.0f}".format(stats.get("total_revenue",0)))
roas = stats.get("overall_roas", 0)
c3.metric(t("ads.kpi_roas"), str(roas) + "x",
          delta_color="normal" if roas >= 2 else "inverse")
c4.metric(t("ads.kpi_campaigns"), stats.get("total_campaigns",0))

st.divider()
tab_list, tab_add = st.tabs([t("ads.tab_list"), t("ads.tab_add")])

def _roas_color(roas):
    return "#4d6c5c" if roas >= 3 else ("#c5963d" if roas >= 1.5 else "#c54c4c")

with tab_list:
    status_f = st.segmented_control(t("ads.status_filter"),
        ["all","active","ended","paused"],
        format_func=lambda s: t("ads.all") if s=="all" else s,
        default="all")
    campaigns = at.all_campaigns(status=None if status_f=="all" else status_f)
    if not campaigns:
        st.info(t("ads.empty"))
    for c in campaigns:
        roas_c = round(c["revenue"] / c["spent"], 2) if c.get("spent",0) > 0 else 0
        plat_icon = at.PLATFORM_ICONS.get(c.get("platform",""), "📣")
        label = t("ads.expander_line",
                  icon=plat_icon,
                  name=c["name"],
                  spent="{:,.0f}".format(c.get("spent", 0)),
                  spent_label=t("ads.spent"),
                  roas=str(roas_c))
        with st.expander(label):
            col1, col2, col3 = st.columns(3)
            col1.metric(t("ads.spent"), "฿{:,.0f}".format(c.get("spent",0)))
            col2.metric(t("ads.revenue"), "฿{:,.0f}".format(c.get("revenue",0)))
            r_color = _roas_color(roas_c)
            col3.metric(t("ads.roas_label"), str(roas_c) + "x")
            col4, col5, col6 = st.columns(3)
            col4.write(t("ads.impressions") + ": " + "{:,}".format(c.get("impressions",0)))
            col5.write(t("ads.clicks") + ": " + "{:,}".format(c.get("clicks",0)))
            col6.write(t("ads.orders") + ": " + str(c.get("orders",0)))
            if c.get("note"):
                st.caption(c["note"])
            col_u, col_d = st.columns(2)
            with col_u.form("upd_" + str(c["id"])):
                new_spent   = st.number_input(t("ads.f_spent"), value=float(c.get("spent",0)), key="ns_" + str(c["id"]))
                new_revenue = st.number_input(t("ads.f_revenue"), value=float(c.get("revenue",0)), key="nr_" + str(c["id"]))
                new_orders  = st.number_input(t("ads.f_orders"), value=int(c.get("orders",0)), key="no_" + str(c["id"]))
                if st.form_submit_button(t("ads.update_btn")):
                    at.update(c["id"], spent=new_spent, revenue=new_revenue, orders=int(new_orders))
                    st.rerun()
            if col_d.button(t("ads.delete_btn"), key="adel_" + str(c["id"])):
                at.delete(c["id"]); st.rerun()

with tab_add:
    st.subheader(t("ads.add_title"))
    with st.form("add_ad_form"):
        col1, col2 = st.columns(2)
        name      = col1.text_input(t("ads.f_name"), placeholder="11.11 Shopee Ads")
        platform  = col2.selectbox(t("ads.f_platform"), at.AD_PLATFORMS,
                                    format_func=lambda p: at.PLATFORM_ICONS.get(p, "") +
                                    " " + platform_name(p))
        col3, col4 = st.columns(2)
        budget    = col3.number_input(t("ads.f_budget"), min_value=0.0, step=100.0)
        spent     = col4.number_input(t("ads.f_spent"), min_value=0.0, step=100.0)
        col5, col6 = st.columns(2)
        revenue   = col5.number_input(t("ads.f_revenue"), min_value=0.0, step=100.0)
        orders    = col6.number_input(t("ads.f_orders"), min_value=0, step=1)
        note      = st.text_input(t("ads.f_note"))
        if st.form_submit_button(t("ads.add_btn")):
            if name.strip():
                at.add(name.strip(), platform, budget, spent, note,
                       revenue=revenue, orders=int(orders))
                st.success(t("ads.added"))
                st.rerun()
