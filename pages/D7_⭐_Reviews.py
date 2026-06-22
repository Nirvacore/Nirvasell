"""D7 Review Manager — track and respond to product reviews."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import review_manager as rm
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
rm.init()
render_sidebar()

st.title(t("rev.title"))
st.caption(t("rev.caption"))

stats = rm.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("rev.kpi_total"), stats["total"])
avg_color = "normal"
c2.metric(t("rev.kpi_avg"), "⭐ " + str(stats["avg_rating"]))
c3.metric(t("rev.kpi_unanswered"), stats["unanswered"],
          delta=(("-" + str(stats["unanswered"])) if stats["unanswered"] else "✓"),
          delta_color="inverse" if stats["unanswered"] else "off")
c4.metric(t("rev.kpi_negative"), stats["negative"],
          delta_color="inverse" if stats["negative"] else "off")

st.divider()

tab_reviews, tab_log, tab_skus, tab_platforms = st.tabs([
    t("rev.tab_reviews"), t("rev.tab_log"),
    t("rev.tab_skus"), t("rev.tab_platforms")
])

with tab_reviews:
    col_f1, col_f2, col_f3 = st.columns(3)
    plat_f = col_f1.selectbox(t("rev.f_platform_filter"),
                               [""] + ["shopee","lazada","tiktok_shop","facebook","line","other"])
    rat_f  = col_f2.selectbox(t("rev.f_rating_filter"), [0,1,2,3,4,5],
                               format_func=lambda r: t("rev.all_ratings") if r==0 else "⭐"*r)
    stat_f = col_f3.selectbox(t("rev.f_status_filter"),
                               [""] + list(rm.STATUSES.keys()),
                               format_func=lambda s: t("rev.all_statuses") if s=="" else rm.STATUSES[s]["label"])
    reviews = rm.all_reviews(
        platform=plat_f or None,
        rating=rat_f or None,
        status=stat_f or None,
    )
    if not reviews:
        st.info(t("rev.empty"))
    for rv in reviews:
        si = rv["status_info"]
        label = rv["stars"] + " · " + (rv.get("platform") or "—") + \
                " · " + (rv.get("product_name") or rv.get("sku") or "—") + \
                " · " + si["icon"] + " " + si["label"]
        with st.expander(label):
            if rv.get("reviewer"):
                st.caption(t("rev.reviewer") + ": " + rv["reviewer"])
            if rv.get("review_text"):
                st.write(rv["review_text"])
            if rv.get("reply_text"):
                st.info(t("rev.your_reply") + ": " + rv["reply_text"])
            new_status = st.selectbox(
                t("rev.status_label"),
                list(rm.STATUSES.keys()),
                index=list(rm.STATUSES.keys()).index(rv["status"])
                      if rv["status"] in rm.STATUSES else 0,
                format_func=lambda s: rm.STATUSES[s]["label"],
                key="rs_" + str(rv["id"]),
            )
            reply_txt = st.text_area(t("rev.reply_label"), value=rv.get("reply_text",""),
                                      key="rr_" + str(rv["id"]), height=80)
            col_s, col_d = st.columns(2)
            if col_s.button(t("rev.save_btn"), key="rsave_" + str(rv["id"])):
                rm.set_status(rv["id"], new_status)
                if reply_txt.strip():
                    rm.reply(rv["id"], reply_txt.strip())
                st.rerun()
            if col_d.button(t("rev.delete_btn"), key="rdel_" + str(rv["id"])):
                rm.delete(rv["id"])
                st.rerun()

with tab_log:
    st.subheader(t("rev.log_title"))
    with st.form("log_review_form"):
        col1, col2 = st.columns(2)
        platform    = col1.selectbox(t("rev.f_platform"),
                                      ["shopee","lazada","tiktok_shop","facebook","line","other"])
        rating      = col2.selectbox(t("rev.f_rating"), [5,4,3,2,1],
                                      format_func=lambda r: "⭐"*r)
        col3, col4 = st.columns(2)
        try:
            import products as _p
            _p.init()
            prods = _p.all_products()
        except Exception:
            prods = []
        sku_options = [""] + [p["sku"] for p in prods]
        sku         = col3.selectbox(t("rev.f_sku"), sku_options)
        product_name = col4.text_input(t("rev.f_product_name"))
        reviewer    = col1.text_input(t("rev.f_reviewer"))
        rev_date    = col2.text_input(t("rev.f_date"), placeholder=t("common.date_ph"))
        review_text = st.text_area(t("rev.f_text"), height=100)
        if st.form_submit_button(t("rev.log_btn")):
            rm.add(platform, sku, rating, review_text, reviewer, product_name, rev_date)
            st.success(t("rev.logged"))
            st.rerun()

with tab_skus:
    st.subheader(t("rev.sku_title"))
    by_sku = rm.by_sku()
    if not by_sku:
        st.info(t("rev.empty"))
    else:
        table_html = "<table style='width:100%;border-collapse:collapse;font-size:0.85rem'>"
        table_html += "<tr style='color:#9a9485'>"
        for col in [t("rev.col_sku"), t("rev.col_product"), t("rev.col_reviews"),
                    t("rev.col_avg"), t("rev.col_negatives")]:
            table_html += "<th style='text-align:left;padding:5px 8px'>" + col + "</th>"
        table_html += "</tr>"
        for r in by_sku:
            neg_color = "#c54c4c" if r["negatives"] > 0 else "#4d6c5c"
            table_html += "<tr style='border-top:1px solid #2a2a2a'>"
            table_html += "<td style='padding:5px 8px'>" + (r["sku"] or "—") + "</td>"
            table_html += "<td style='padding:5px 8px'>" + (r["product_name"] or "—") + "</td>"
            table_html += "<td style='padding:5px 8px'>" + str(r["total"]) + "</td>"
            avg = round(r["avg_rating"] or 0, 1)
            table_html += "<td style='padding:5px 8px'>⭐ " + str(avg) + "</td>"
            table_html += "<td style='padding:5px 8px;color:" + neg_color + "'>" + str(r["negatives"]) + "</td>"
            table_html += "</tr>"
        table_html += "</table>"
        st.html(table_html)

with tab_platforms:
    st.subheader(t("rev.platform_title"))
    by_p = rm.by_platform()
    for p in by_p:
        avg = round(p["avg_rating"] or 0, 1)
        with st.expander(p["platform"] + " · " + "⭐"*round(avg) + " " + str(avg) +
                         " · " + str(p["total"]) + t("rev.review_count")):
            col1, col2, col3 = st.columns(3)
            col1.metric(t("rev.total_reviews"), p["total"])
            col2.metric(t("rev.negatives"), p["negatives"])
            col3.metric(t("rev.unanswered"), p["unanswered"])
