"""E0 Flash Sale Scheduler — plan and run time-limited sales."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import flash_sale as fs
from theme import apply_theme
from auth import require_auth
from i18n import t
from i18n_inline import flash_status_label, flash_discount_label
from sidebar import render_sidebar

apply_theme()
require_auth()
fs.init()
render_sidebar()

st.title(t("flash.title"))
st.caption(t("flash.caption"))

stats = fs.stats()
c1, c2, c3 = st.columns(3)
c1.metric(t("flash.kpi_total"), stats["total"])
c2.metric(t("flash.kpi_active"), stats["active"],
          delta=t("flash.live_now") if stats["active"] > 0 else None,
          delta_color="normal")
c3.metric(t("flash.kpi_upcoming"), stats["upcoming"])

if stats["active_titles"]:
    for title in stats["active_titles"]:
        st.success("🔥 " + t("flash.active_alert") + ": **" + title + "**")

st.divider()

tab_active, tab_all, tab_create = st.tabs([
    t("flash.tab_active"), t("flash.tab_all"), t("flash.tab_create")
])

with tab_active:
    active_sales = fs.active_now()
    if not active_sales:
        st.info(t("flash.no_active"))
    for sale in active_sales:
        si = sale["status_info"]
        st.markdown("### 🔥 " + sale["title"])
        col1, col2, col3 = st.columns(3)
        dt = flash_discount_label(sale["discount_type"])
        col1.metric(t("flash.discount"),
                    str(sale["discount_value"]) + ("%" if sale["discount_type"]=="percentage" else " ฿") +
                    " (" + dt + ")")
        col2.metric(t("flash.time_left"), sale.get("time_remaining","—"))
        uses = str(sale["current_uses"])
        max_u = str(sale["max_uses"]) if sale["max_uses"] > 0 else "∞"
        col3.metric(t("flash.uses"), uses + " / " + max_u)
        if st.button(t("flash.cancel_btn"), key="fc_" + str(sale["id"])):
            fs.cancel(sale["id"])
            st.rerun()

with tab_all:
    status_f = st.segmented_control(
        t("flash.status_filter"),
        ["all", "upcoming", "active", "ended", "draft"],
        format_func=lambda s: (
            t("flash.all") if s == "all" else flash_status_label(s)
        ),
        default="all",
    )
    sales = fs.all_sales(status_filter=None if status_f=="all" else status_f)
    if not sales:
        st.info(t("flash.empty"))
    for sale in sales:
        si = sale["status_info"]
        label = si["icon"] + " " + sale["title"] + \
                " · " + sale["start_dt"] + " → " + sale["end_dt"]
        with st.expander(label):
            col1, col2 = st.columns(2)
            dt_label = flash_discount_label(sale["discount_type"])
            col1.write(t("flash.discount") + ": " +
                       str(sale["discount_value"]) +
                       ("%" if sale["discount_type"]=="percentage" else "฿") +
                       " (" + dt_label + ")")
            col2.write(t("flash.platform") + ": " + (sale.get("platform") or "all"))
            col1.write(t("flash.uses") + ": " + str(sale["current_uses"]) +
                       (" / " + str(sale["max_uses"]) if sale["max_uses"] > 0 else ""))
            col2.write(t("flash.time_left") + ": " + sale.get("time_remaining","—"))
            if sale.get("notes"):
                st.caption(sale["notes"])
            col_c, col_d = st.columns(2)
            if col_c.button(t("flash.cancel_btn"), key="fca_" + str(sale["id"])):
                fs.cancel(sale["id"])
                st.rerun()
            if col_d.button(t("flash.delete_btn"), key="fdel_" + str(sale["id"])):
                fs.delete(sale["id"])
                st.rerun()

with tab_create:
    st.subheader(t("flash.create_title"))
    with st.form("flash_form"):
        title      = st.text_input(t("flash.f_title"), placeholder=t("flash.title_ph"))
        col1, col2 = st.columns(2)
        disc_type  = col1.selectbox(t("flash.f_discount_type"),
                                     list(fs.DISCOUNT_TYPES.keys()),
                                     format_func=flash_discount_label)
        disc_val   = col2.number_input(t("flash.f_discount_value"), min_value=0.0, step=5.0)
        col3, col4 = st.columns(2)
        start_dt   = col3.text_input(t("flash.f_start"), placeholder=t("common.datetime_ph"))
        end_dt     = col4.text_input(t("flash.f_end"), placeholder=t("common.datetime_ph"))
        col5, col6 = st.columns(2)
        platform   = col5.selectbox(t("flash.f_platform"),
                                     ["all","shopee","lazada","tiktok_shop","facebook","line"])
        max_uses   = col6.number_input(t("flash.f_max_uses"), min_value=0, step=10,
                                        help=t("flash.max_uses_help"))
        min_order  = col5.number_input(t("flash.f_min_order"), min_value=0.0, step=50.0)
        notes      = st.text_input(t("flash.f_notes"))
        if st.form_submit_button(t("flash.create_btn")):
            if title and start_dt and end_dt:
                fs.create(title, disc_type, disc_val, min_order,
                          int(max_uses), platform, "", start_dt, end_dt, notes)
                st.success(t("flash.created"))
                st.rerun()
            else:
                st.error(t("flash.need_fields"))
