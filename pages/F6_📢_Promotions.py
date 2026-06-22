"""F6 Promotions Manager — create, activate, and track promotions."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import promotions as pr
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
pr.init()
render_sidebar()

st.title(t("promo.title"))
st.caption(t("promo.caption"))

all_p = pr.all_promos()
active_p = [p for p in all_p if p["status"] == "active"]
draft_p  = [p for p in all_p if p["status"] == "draft"]

c1, c2, c3 = st.columns(3)
c1.metric(t("promo.kpi_total"), len(all_p))
c2.metric(t("promo.kpi_active"), len(active_p),
          delta_color="normal" if active_p else "off")
c3.metric(t("promo.kpi_draft"), len(draft_p))

for p in active_p:
    pi = p["promo_info"]
    st.success(pi["icon"] + " " + t("promo.active_banner") + ": **" + p["title"] + "**")

st.divider()
tab_all, tab_create = st.tabs([t("promo.tab_all"), t("promo.tab_create")])

with tab_all:
    status_f = st.segmented_control(t("promo.status_filter"),
        ["all"] + list(pr.STATUSES.keys()),
        format_func=lambda s: t("promo.all") if s=="all" else pr.STATUSES[s]["label"],
        default="all")
    promos = pr.all_promos(status=None if status_f=="all" else status_f)
    if not promos:
        st.info(t("promo.empty"))
    for p in promos:
        pi, si = p["promo_info"], p["status_info"]
        label = pi["icon"] + " **" + p["title"] + "**" + \
                " · " + pi["label"] + \
                " · " + (t("common.discount") + " " + str(p["discount_value"]) +
                          ("%" if "percent" in p["promo_type"] else " ฿")) + \
                " · " + si["icon"] + " " + si["label"]
        with st.expander(label):
            col1, col2 = st.columns(2)
            col1.write(t("promo.min_order") + ": ฿" + str(p["min_order_amount"] or 0))
            col2.write(t("promo.coupon") + ": " + (p.get("coupon_code") or "—"))
            col1.write(t("promo.start") + ": " + (p.get("start_dt") or "—"))
            col2.write(t("promo.end") + ": " + (p.get("end_dt") or "—"))
            col1.write(t("promo.uses") + ": " + str(p["use_count"]) +
                       (" / " + str(p["max_uses"]) if p["max_uses"] > 0 else ""))
            if p.get("notes"):
                st.caption(p["notes"])
            col_a, col_p, col_e = st.columns(3)
            if p["status"] in ("draft","paused"):
                if col_a.button(t("promo.activate"), key="pa_" + str(p["id"])):
                    pr.activate(p["id"]); st.rerun()
            if p["status"] == "active":
                if col_p.button(t("promo.pause"), key="pp_" + str(p["id"])):
                    pr.pause(p["id"]); st.rerun()
            if col_e.button(t("promo.delete"), key="pd_" + str(p["id"])):
                pr.delete(p["id"]); st.rerun()

with tab_create:
    st.subheader(t("promo.create_title"))
    with st.form("promo_form"):
        title     = st.text_input(t("promo.f_title"))
        col1, col2 = st.columns(2)
        ptype     = col1.selectbox(t("promo.f_type"),
                                    list(pr.PROMO_TYPES.keys()),
                                    format_func=lambda k: pr.PROMO_TYPES[k]["icon"] + " " + pr.PROMO_TYPES[k]["label"])
        disc_val  = col2.number_input(t("promo.f_value"), min_value=0.0, step=5.0)
        col3, col4 = st.columns(2)
        min_order = col3.number_input(t("promo.f_min_order"), min_value=0.0, step=50.0)
        max_uses  = col4.number_input(t("promo.f_max_uses"), min_value=0, step=10)
        col5, col6 = st.columns(2)
        coupon    = col5.text_input(t("promo.f_coupon"), placeholder=t("promo.coupon_ph"))
        sku_filter= col6.text_input(t("promo.f_sku_filter"), placeholder=t("promo.sku_filter_ph"))
        col7, col8 = st.columns(2)
        start_dt  = col7.text_input(t("promo.f_start"), placeholder=t("common.date_ph"))
        end_dt    = col8.text_input(t("promo.f_end"), placeholder=t("common.date_ph"))
        notes     = st.text_input(t("promo.f_notes"))
        if st.form_submit_button(t("promo.create_btn")):
            if title.strip():
                pr.create(ptype, title.strip(), disc_val, min_order,
                           1, int(max_uses), coupon, sku_filter,
                           start_dt, end_dt, notes)
                st.success(t("promo.created"))
                st.rerun()
