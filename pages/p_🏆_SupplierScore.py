"""Supplier Scorecard — rate your suppliers objectively.

Score on: price competitiveness, delivery speed, SKU coverage, volume.
Stop guessing which supplier is best."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import supplier_score as ss
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Supplier Score",
                   page_icon="🏆", layout="wide")
apply_theme()
require_auth()
db.init()

# Init supplier tables
try:
    import supplier_mgmt as sm
    sm.init()
except ImportError:
    pass

render_sidebar()

page_header(icon="🏆", title=t("sscore.title"), subtitle=t("sscore.caption"))

suppliers = ss.score_all()

if not suppliers:
    st.info(t("sscore.empty"))
    st.caption(t("sscore.empty_hint"))
    st.stop()


# ---- KPIs -------------------------------------------------------------------

s = ss.summary()

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("sscore.kpi_total"), str(s["total"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("sscore.kpi_avg"), str(s["avg_score"]) + "/100",
        hint="", hint_tone="ok" if s["avg_score"] >= 60 else "warn",
    )
with k3:
    metric_with_hint(
        t("sscore.kpi_top"), s["top_supplier"],
        hint="", hint_tone="ok",
    )


# ---- Grade distribution ------------------------------------------------------

st.divider()
st.markdown("### " + t("sscore.grades_title"))

grade_data = [
    ("A", "🟢", s["grades"]["A"], "#4d6c5c", "80-100"),
    ("B", "🔵", s["grades"]["B"], "#4a7ab5", "60-79"),
    ("C", "🟡", s["grades"]["C"], "#c5963d", "40-59"),
    ("D", "🔴", s["grades"]["D"], "#c54c4c", "0-39"),
]
gcols = st.columns(4)
for i, (grade, icon, count, color, score_range) in enumerate(grade_data):
    with gcols[i]:
        st.markdown(
            "<div style='text-align:center;padding:14px;background:white;"
            "border:0.5px solid rgba(40,30,20,0.07);border-radius:10px;"
            "border-top:3px solid " + color + "'>"
            "<div style='font-size:1.4rem;font-weight:600;color:" + color + "'>"
            + icon + " Grade " + grade + "</div>"
            "<div style='font-size:1.8rem;font-weight:600'>" + str(count) + "</div>"
            "<div style='font-size:11px;color:#9a9485'>Score " + score_range + "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Supplier cards ----------------------------------------------------------

st.divider()
st.markdown("### " + t("sscore.list_title"))

for sup in suppliers:
    grade = sup["grade"]
    grade_color = {"A": "#4d6c5c", "B": "#4a7ab5", "C": "#c5963d", "D": "#c54c4c"}.get(grade, "#7a7569")
    grade_icon = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🔴"}.get(grade, "?")

    vol_str = "{:,.0f}".format(sup["total_volume"])

    st.markdown(
        "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
        "border-left:4px solid " + grade_color + ";border-radius:10px;"
        "padding:14px 16px;margin-bottom:8px'>"
        "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
        "<div>"
        "<span style='font-weight:600;font-size:1.1rem'>" +
        grade_icon + " " + sup["name"] + "</span>"
        " <span style='color:#9a9485;font-size:12px'>" + sup.get("contact", "") + "</span>"
        "</div>"
        "<div style='font-size:1.4rem;font-weight:600;color:" + grade_color + "'>"
        + str(sup["overall"]) + "/100</div></div>"
        "<div style='display:flex;gap:18px;margin-top:8px;font-size:12px;color:#7a7569'>"
        "<span>" + t("sscore.dim_price") + " " + str(int(sup["price_score"])) + "</span>"
        "<span>" + t("sscore.dim_delivery") + " " + str(int(sup["delivery_score"])) + "</span>"
        "<span>" + t("sscore.dim_skus") + " " + str(sup["sku_count"]) + "</span>"
        "<span>" + t("sscore.dim_volume") + " ฿" + vol_str + "</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )
