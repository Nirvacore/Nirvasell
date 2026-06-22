"""G2 Content Calendar — schedule & track posts across platforms."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import content_calendar as cc
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar
from datetime import datetime

apply_theme()
require_auth()
cc.init()
render_sidebar()

st.title(t("cal.title"))
st.caption(t("cal.caption"))

today_posts = cc.today_posts()
upcoming    = cc.upcoming(days=7)

c1, c2 = st.columns(2)
c1.metric(t("cal.kpi_today"), len(today_posts))
c2.metric(t("cal.kpi_upcoming"), len(upcoming))

if today_posts:
    st.info("📌 " + t("cal.today_reminder") + ": " + ", ".join(p["title"] for p in today_posts))

st.divider()
tab_upcoming, tab_all, tab_add = st.tabs([
    t("cal.tab_upcoming"), t("cal.tab_all"), t("cal.tab_add")
])

def _post_row(p):
    st_info = {"draft":"⚫","scheduled":"🔵","published":"🟢","overdue":"🔴"}
    icon = st_info.get(p.get("status","draft"), "⚫")
    label = (icon + " **" + p["title"] + "**"
             + " · " + (p.get("platform") or "—")
             + " · " + (p.get("post_date") or "—"))
    with st.expander(label):
        col1, col2 = st.columns(2)
        col1.write(t("cal.platform") + ": " + (p.get("platform") or "—"))
        col2.write(t("cal.type") + ": " + (p.get("post_type") or "—"))
        col1.write(t("cal.status") + ": " + (p.get("status") or "—"))
        col2.write(t("cal.date") + ": " + (p.get("post_date") or "—"))
        if p.get("body"):
            st.markdown("> " + p["body"][:200])
        if p.get("caption"):
            st.caption(p["caption"])
        col_s, col_d = st.columns(2)
        new_status = col_s.selectbox(t("cal.update_status"),
            ["draft","scheduled","published","overdue"],
            index=["draft","scheduled","published","overdue"].index(p.get("status","draft")),
            key="cst_" + str(p["id"]))
        if col_s.button(t("cal.save"), key="csv_" + str(p["id"])):
            cc.update(p["id"], status=new_status); st.rerun()
        if col_d.button(t("cal.delete"), key="cdl_" + str(p["id"])):
            cc.delete(p["id"]); st.rerun()

with tab_upcoming:
    if not upcoming:
        st.info(t("cal.no_upcoming"))
    for p in upcoming:
        _post_row(p)

with tab_all:
    status_f = st.segmented_control(t("cal.status_filter"),
        ["all","draft","scheduled","published","overdue"],
        format_func=lambda s: t("cal.all") if s=="all" else s,
        default="all")
    posts = cc.all_posts(status=None if status_f=="all" else status_f)
    if not posts:
        st.info(t("cal.empty"))
    for p in posts:
        _post_row(p)

with tab_add:
    st.subheader(t("cal.add_title"))
    with st.form("content_form"):
        title    = st.text_input(t("cal.f_title"))
        col1, col2 = st.columns(2)
        platform = col1.selectbox(t("cal.f_platform"),
            ["shopee","lazada","tiktok_shop","facebook","instagram","line","youtube"])
        post_type = col2.selectbox(t("cal.f_type"),
            ["product_post","story","live_announcement","promotion","review_response",
             "general","educational"])
        col3, col4 = st.columns(2)
        post_date = col3.text_input(t("cal.f_date"),
                                     value=datetime.now().strftime("%Y-%m-%d"),
                                     placeholder=t("common.date_ph"))
        post_time = col4.text_input(t("cal.f_time"), placeholder=t("common.time_hhmm_ph"),
        body     = st.text_area(t("cal.f_body"), height=80)
        caption  = st.text_input(t("cal.f_caption"))
        if st.form_submit_button(t("cal.add_btn")):
            if title.strip():
                sched = post_date + " " + post_time if post_time else post_date
                cc.add(title.strip(), platform, post_type=post_type,
                       post_date=sched, body=body, caption=caption)
                st.success(t("cal.added"))
                st.rerun()
