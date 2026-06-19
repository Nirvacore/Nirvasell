"""Product Score — rank every SKU by combined performance."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import product_score as ps
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · Product Score",
                   page_icon="🏅", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🏅", title=t("pscore.title"), subtitle=t("pscore.caption"))

days = st.select_slider(
    t("pscore.f_days"),
    options=[7, 14, 30, 60, 90],
    value=30, key="_ps_days",
)

s = ps.summary()
quads = s.get("quadrants", {})

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("⭐ " + t("pscore.star"),
                     str(quads.get("star", 0)),
                     hint=t("pscore.star_hint"), hint_tone="ok")
with k2:
    metric_with_hint("🐄 " + t("pscore.cash_cow"),
                     str(quads.get("cash_cow", 0)),
                     hint=t("pscore.cow_hint"), hint_tone="info")
with k3:
    metric_with_hint("❓ " + t("pscore.question"),
                     str(quads.get("question", 0)),
                     hint=t("pscore.question_hint"), hint_tone="warn")
with k4:
    metric_with_hint("🐕 " + t("pscore.dog"),
                     str(quads.get("dog", 0)),
                     hint=t("pscore.dog_hint"), hint_tone="danger")

st.divider()

# Filter
filter_quad = st.selectbox(
    t("pscore.f_filter"),
    ["all", "star", "cash_cow", "question", "dog"],
    format_func=lambda x: {
        "all": "🔍 " + t("pscore.all"),
        "star": "⭐ " + t("pscore.star"),
        "cash_cow": "🐄 " + t("pscore.cash_cow"),
        "question": "❓ " + t("pscore.question"),
        "dog": "🐕 " + t("pscore.dog"),
    }.get(x, x),
    key="_ps_filter",
)

scored = ps.calculate(days)
if filter_quad != "all":
    scored = [p for p in scored if p["quadrant"] == filter_quad]

if not scored:
    st.info(t("pscore.empty"))
    st.stop()

# Rank table
for item in scored:
    q_color = {
        "star": "#4d6c5c", "cash_cow": "#4a7ab5",
        "question": "#c5963d", "dog": "#c54c4c",
    }.get(item["quadrant"], "#7a7569")

    bar_w = int(item["score"])
    rank_icon = {1: "🥇", 2: "🥈", 3: "🥉"}.get(item["rank"], str(item["rank"]))

    st.markdown(
        "<div style='padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
        "<div style='display:flex;justify-content:space-between;align-items:baseline;"
        "margin-bottom:4px'>"
        "<span>" + str(rank_icon) + " " + item["quadrant_icon"] +
        " <strong>" + item["sku"] + "</strong>"
        " <span style='color:#9a9485;font-size:11px'>"
        + (item.get("name") or "")[:30] + "</span></span>"
        "<span style='display:flex;gap:12px;font-size:13px'>"
        "<span>" + t("common.revenue") + " ฿{:,.0f}".format(item["revenue"]) + "</span>"
        "<span style='color:#4d6c5c'>" + t("common.margin") + " " + str(item["margin_pct"]) + "%</span>"
        "<span style='color:#7a7569'>" + str(item["velocity"]) + t("common.per_day") + "</span>"
        "<span style='font-weight:700;color:" + q_color + ";font-size:1.1rem'>"
        + str(item["score"]) + "</span></span></div>"
        "<div style='background:rgba(40,30,20,0.06);border-radius:3px;height:6px'>"
        "<div style='width:" + str(bar_w) + "%;height:100%;background:" + q_color + ";"
        "border-radius:3px'></div></div></div>",
        unsafe_allow_html=True,
    )

st.divider()
st.caption(t("pscore.weight_note"))
