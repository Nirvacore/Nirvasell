"""H8 Product Score — composite health scores: revenue × margin × reviews."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import product_score as ps
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
render_sidebar()

st.title(t("pscore.title"))
st.caption(t("pscore.caption"))

days = st.segmented_control(t("pscore.period"), [7, 30, 90], default=30,
    format_func=lambda d: str(d) + t("pscore.days"))
summary = ps.summary()
c1, c2, c3 = st.columns(3)
c1.metric(t("pscore.kpi_stars"), summary.get("star_count",0))
c2.metric(t("pscore.kpi_avg_score"), str(summary.get("avg_score",0)) + "/100")
c3.metric(t("pscore.kpi_total"), summary.get("total_skus",0))

st.divider()
tab_top, tab_bottom, tab_quad = st.tabs([
    t("pscore.tab_top"), t("pscore.tab_bottom"), t("pscore.tab_quad")
])

def _score_color(score):
    return "#4d6c5c" if score >= 70 else ("#c5963d" if score >= 40 else "#c54c4c")

def _score_bar(score):
    bar_w = int(score * 1.8)
    color = _score_color(score)
    return (
        "<div style='display:flex;align-items:center;gap:6px'>"
        "<div style='background:" + color + ";width:" + str(bar_w) +
        "px;height:10px'></div>"
        "<span style='color:" + color + ";font-size:0.82rem;font-variant-numeric:tabular-nums'>" +
        str(score) + "/100</span></div>"
    )

def _render_scored(items):
    if not items:
        st.info(t("pscore.empty"))
    for item in items:
        sku   = item.get("sku","?")
        name  = item.get("name") or sku
        score = item.get("score",0)
        rev   = item.get("revenue",0)
        margin= item.get("margin_pct",0)
        rating= item.get("avg_rating",0)
        label = _score_color(score) and "**" + name + "** · score " + str(score)
        with st.expander("**" + name + "** · " + str(score) + "/100"):
            st.html(_score_bar(score))
            c1, c2, c3 = st.columns(3)
            c1.metric(t("pscore.revenue"), "฿{:,.0f}".format(rev))
            c2.metric(t("pscore.margin"), str(margin) + "%")
            c3.metric(t("pscore.rating"), str(rating) + "⭐" if rating else "—")

with tab_top:
    top = ps.top_performers(n=10)
    _render_scored(top)

with tab_bottom:
    bottom = ps.bottom_performers(n=10)
    _render_scored(bottom)

with tab_quad:
    st.subheader(t("pscore.quad_title"))
    QUADS = [
        ("star", "⭐ " + t("pscore.q_star"), "#4d6c5c"),
        ("question_mark", "❓ " + t("pscore.q_question"), "#c5963d"),
        ("cash_cow", "🐄 " + t("pscore.q_cow"), "#3a5a8c"),
        ("dog", "🐕 " + t("pscore.q_dog"), "#c54c4c"),
    ]
    for qkey, qlabel, qcolor in QUADS:
        items_q = ps.by_quadrant(qkey)
        with st.expander(qlabel + " (" + str(len(items_q)) + ")"):
            if not items_q:
                st.write(t("pscore.empty_quad"))
            for item in items_q:
                sku  = item.get("sku","?")
                name = item.get("name") or sku
                score= item.get("score",0)
                q_html = (
                    "<div style='margin:2px 0;font-size:0.83rem'>"
                    "<span style='color:#d4d0c8'>" + name + "</span>"
                    " <span style='color:#9a9485'>(" + sku + ")</span>"
                    " <span style='color:" + qcolor + ";margin-left:6px'>" +
                    str(score) + "/100</span>"
                    "</div>"
                )
                st.html(q_html)
