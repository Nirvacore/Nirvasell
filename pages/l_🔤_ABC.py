"""ABC Analysis — know which products deserve your cash.

A = 80% of revenue (protect at all costs)
B = 15% (important)
C = 5% (consider trimming)"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import abc_analysis as abc
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · ABC Analysis",
                   page_icon="🔤", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="🔤", title=t("abc.title"), subtitle=t("abc.caption"))

# ---- Summary KPIs -----------------------------------------------------------

s = abc.summary()

if s["total_skus"] == 0:
    st.info(t("abc.empty"))
    st.stop()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("abc.kpi_total"), str(s["total_skus"]),
        hint="", hint_tone="info",
    )
with k2:
    a_pct = round(s["A"]["count"] / s["total_skus"] * 100, 0) if s["total_skus"] else 0
    metric_with_hint(
        t("abc.kpi_a_items"), str(s["A"]["count"]),
        hint=t("abc.hint_a_pct", pct=str(int(a_pct))),
        hint_tone="ok",
    )
with k3:
    metric_with_hint(
        t("abc.kpi_b_items"), str(s["B"]["count"]),
        hint=t("abc.hint_b_revenue"), hint_tone="info",
    )
with k4:
    metric_with_hint(
        t("abc.kpi_c_items"), str(s["C"]["count"]),
        hint=t("abc.hint_c_revenue"), hint_tone="warn",
    )


# ---- Class cards with stock value -------------------------------------------

st.divider()
st.markdown("### " + t("abc.stock_investment"))

class_data = [
    ("🅰️", "A", "#4d6c5c", s["A"]),
    ("🅱️", "B", "#c5963d", s["B"]),
    ("🆑", "C", "#c54c4c", s["C"]),
]
ccols = st.columns(3)
for i, (icon, cls, color, data) in enumerate(class_data):
    with ccols[i]:
        rev_str = "{:,.0f}".format(data["revenue"])
        stk_str = "{:,.0f}".format(data["stock_value"])
        st.markdown(
            "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
            "border-top:4px solid " + color + ";border-radius:10px;padding:16px;"
            "text-align:center'>"
            "<div style='font-size:1.8rem'>" + icon + "</div>"
            "<div style='font-size:1.6rem;font-weight:600;color:" + color + "'>"
            + t("abc.card_skus", n=str(data["count"])) + "</div>"
            "<div style='color:#7a7569;font-size:13px;margin-top:6px'>"
            + t("abc.card_revenue", amount=rev_str) + "</div>"
            "<div style='color:#7a7569;font-size:13px'>"
            + t("abc.card_stock_value", amount=stk_str) + "</div></div>",
            unsafe_allow_html=True,
        )


# ---- Detailed list per class ------------------------------------------------

st.divider()

tab_a, tab_b, tab_c = st.tabs([
    "🅰️ A — " + t("abc.tab_a") + " (" + str(s["A"]["count"]) + ")",
    "🅱️ B — " + t("abc.tab_b") + " (" + str(s["B"]["count"]) + ")",
    "🆑 C — " + t("abc.tab_c") + " (" + str(s["C"]["count"]) + ")",
])


def _render_items(items, color):
    for item in items:
        rev_str = "{:,.0f}".format(item["total_revenue"])
        stk_str = str(item.get("stock") or 0)
        pct_str = "{:.1f}%".format(item.get("revenue_pct") or 0)
        cum_str = "{:.1f}%".format(item.get("cumulative_pct") or 0)

        st.markdown(
            "<div style='display:flex;justify-content:space-between;align-items:center;"
            "padding:10px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            "<div>"
            "<span style='font-weight:600'>" + item["sku"] + "</span>"
            " <span style='color:#7a7569;font-size:12px'>" + (item["name"] or "")[:30] + "</span>"
            "</div>"
            "<div style='display:flex;gap:14px;align-items:center;font-size:13px'>"
            "<span>📦 " + stk_str + "</span>"
            "<span>" + pct_str + "</span>"
            "<span style='color:#9a9485;font-size:11px'>" +
            t("abc.cum_label", pct=cum_str) + "</span>"
            "<span style='font-weight:600;color:" + color + "'>฿" + rev_str + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


with tab_a:
    _render_items(abc.class_items("A"), "#4d6c5c")

with tab_b:
    _render_items(abc.class_items("B"), "#c5963d")

with tab_c:
    _render_items(abc.class_items("C"), "#c54c4c")


# ---- Investment advice -------------------------------------------------------

advice = abc.investment_advice()
if advice:
    st.divider()
    st.markdown("### " + t("abc.advice_title"))

    for a in advice:
        p_icon = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(a["priority"], "?")
        a_label = t("abc.action_" + a["action"])
        st.markdown(
            "<div style='padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
            + p_icon + " <strong>" + a["sku"] + "</strong>"
            " — " + (a["name"] or "")[:25] +
            + t("abc.advice_stock", n=str(a["stock"])) +
            " · <span style='color:#4d6c5c'>" + a_label + "</span></div>",
            unsafe_allow_html=True,
        )
