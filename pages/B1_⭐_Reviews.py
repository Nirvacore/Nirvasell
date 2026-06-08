"""Review Tracker — log and manage product reviews from all platforms."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import date
import db
import review_tracker as rt
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Reviews",
                   page_icon="⭐", layout="wide")
apply_theme()
require_auth()
db.init()
rt.init()
render_sidebar()

page_header(icon="⭐", title=t("rev.title"), subtitle=t("rev.caption"))

s = rt.stats()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("⭐ " + t("rev.kpi_total"), str(s["total"]),
                     hint="", hint_tone="info")
with k2:
    stars = "⭐" * round(s["avg_rating"])
    metric_with_hint(stars + " " + t("rev.kpi_avg"),
                     str(s["avg_rating"]) + "/5",
                     hint="", hint_tone="ok" if s["avg_rating"] >= 4 else "warn")
with k3:
    metric_with_hint("🌟 " + t("rev.kpi_5star"),
                     str(s["five_star"]) + " (" + str(int(s["five_star_pct"])) + "%)",
                     hint="", hint_tone="ok")
with k4:
    metric_with_hint("💬 " + t("rev.kpi_unanswered"),
                     str(s["unanswered_negative"]),
                     hint=t("rev.unanswered_hint") if s["unanswered_negative"] > 0 else "",
                     hint_tone="danger" if s["unanswered_negative"] > 0 else "ok")

# ---- Add review form --------------------------------------------------------
st.divider()
with st.expander(t("rev.add_title"), expanded=s["total"] == 0):
    with st.form("add_review"):
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            with db.conn() as c:
                products = c.execute(
                    "SELECT sku, name FROM products ORDER BY sku"
                ).fetchall()
            if products:
                prod_opts = ["(ไม่ระบุ สินค้า)"] + [
                    p["sku"] + " — " + (p["name"] or "")[:25] for p in products
                ]
                sel_idx = st.selectbox(t("rev.f_sku"), range(len(prod_opts)),
                                       format_func=lambda i: prod_opts[i])
                sel_sku = None if sel_idx == 0 else products[sel_idx - 1]["sku"]
            else:
                sel_sku = None
                st.caption(t("rev.no_products"))

        with rc2:
            platform = st.selectbox(t("rev.f_platform"), rt.PLATFORMS)
            rating = st.slider(t("rev.f_rating"), 1, 5, 5, key="_rev_rating")

        with rc3:
            reviewer = st.text_input(t("rev.f_reviewer"),
                                     placeholder=t("rev.reviewer_ph"))
            rev_date = st.date_input(t("rev.f_date"), value=date.today())

        review_text = st.text_area(t("rev.f_text"), height=80,
                                   placeholder=t("rev.text_ph"))

        if st.form_submit_button(t("rev.add_btn"), type="primary"):
            rt.add(
                platform=platform,
                rating=rating,
                sku=sel_sku,
                reviewer=reviewer.strip(),
                text=review_text.strip(),
                review_date=str(rev_date),
            )
            toast(t("rev.added"), icon="⭐")
            st.rerun()

# ---- Unanswered negative reviews --------------------------------------------
unanswered = rt.unanswered()
if unanswered:
    st.divider()
    st.markdown("### 🚨 " + t("rev.unanswered_title") +
                 " (" + str(len(unanswered)) + ")")

    for rev in unanswered:
        stars_str = rt.SENTIMENTS.get(rev["rating"], {}).get("icon", "⭐")
        color = rt.SENTIMENTS.get(rev["rating"], {}).get("color", "#7a7569")

        uc1, uc2 = st.columns([4, 1])
        with uc1:
            st.markdown(
                "<div style='padding:8px 14px;border-left:3px solid " + color + ";"
                "border-bottom:0.5px solid rgba(40,30,20,0.04)'>"
                + stars_str +
                " <strong>" + (rev.get("reviewer_name") or "ไม่ระบุ") + "</strong>"
                " · " + rev["platform"] +
                " · " + (rev.get("sku") or "—") +
                " <span style='color:#9a9485;font-size:11px'>"
                + rev["review_date"][:10] + "</span>"
                + ("<br><span style='font-size:12px;color:#4a4035'>"
                   + (rev.get("review_text") or "") + "</span>" if rev.get("review_text") else "") +
                "</div>",
                unsafe_allow_html=True,
            )
        with uc2:
            response = st.text_input(
                t("rev.f_response"),
                key="_rev_resp_" + str(rev["id"]),
                label_visibility="collapsed",
                placeholder=t("rev.response_ph"),
            )
            if st.button(t("rev.respond_btn"),
                          key="_rev_resp_btn_" + str(rev["id"]),
                          type="tertiary"):
                if response.strip():
                    rt.add_response(rev["id"], response.strip())
                    toast(t("rev.responded"), icon="✓")
                    st.rerun()

# ---- Platform summary -------------------------------------------------------
platform_data = rt.platform_summary()
if platform_data:
    st.divider()
    st.markdown("### " + t("rev.platform_title"))

    for p in platform_data:
        p_color = "#4d6c5c" if (p["avg_rating"] or 0) >= 4 else "#c5963d"
        st.markdown(
            "<div style='display:flex;justify-content:space-between;"
            "align-items:center;padding:8px 14px;"
            "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<span style='font-weight:600'>" + p["platform"].capitalize() + "</span>"
            "<span style='display:flex;gap:16px;font-size:13px'>"
            "<span>" + str(p["total"]) + " รีวิว</span>"
            "<span style='color:" + p_color + ";font-weight:600'>"
            "⭐ " + "{:.1f}".format(p["avg_rating"] or 0) + "</span>"
            "<span style='color:#4d6c5c'>" + str(p["positive"]) + " 👍</span>"
            "<span style='color:#c54c4c'>" + str(p["negative"]) + " 👎</span>"
            + ("<span style='color:#c5963d'>" + str(p["unanswered"]) + " รอตอบ</span>"
               if p["unanswered"] > 0 else "") +
            "</span></div>",
            unsafe_allow_html=True,
        )

# ---- All reviews feed -------------------------------------------------------
st.divider()
st.markdown("### " + t("rev.feed_title"))

rf1, rf2, rf3 = st.columns(3)
with rf1:
    filter_platform = st.selectbox(
        t("rev.f_filter_platform"),
        ["all"] + rt.PLATFORMS,
        key="_rev_fp",
    )
with rf2:
    filter_min = st.selectbox(
        t("rev.f_min_stars"), [1, 2, 3, 4, 5], index=0,
        key="_rev_min",
    )
with rf3:
    filter_max = st.selectbox(
        t("rev.f_max_stars"), [1, 2, 3, 4, 5], index=4,
        key="_rev_max",
    )

reviews = rt.all_reviews(
    platform=filter_platform if filter_platform != "all" else None,
    min_rating=filter_min,
    max_rating=filter_max,
    limit=30,
)

for rev in reviews:
    stars_str = rev["sentiment"]["icon"]
    color = rev["sentiment"]["color"]
    st.markdown(
        "<div style='padding:8px 14px;"
        "border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        + stars_str +
        " <strong>" + (rev.get("reviewer_name") or "ไม่ระบุ") + "</strong>"
        " · " + rev["platform"] +
        " · " + (rev.get("sku") or "—") +
        " <span style='color:#9a9485;font-size:11px'>"
        + rev["review_date"][:10] + "</span>"
        + (" ✓" if rev.get("responded") else " ⏳") +
        ("<br><span style='font-size:12px;color:#4a4035'>"
         + (rev.get("review_text") or "") + "</span>"
         if rev.get("review_text") else "") +
        "</div>",
        unsafe_allow_html=True,
    )
