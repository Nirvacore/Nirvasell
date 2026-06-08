"""Profit per SKU — see which products ACTUALLY make money.

Not gross margin. TRUE profit after cost + fees + shipping + returns.
The difference between a 'bestseller' and a profitable product."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import sku_profit as sp
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

st.set_page_config(page_title="nirva.sell · SKU Profit",
                   page_icon="💹", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="💹", title=t("skup.title"), subtitle=t("skup.caption"))

# ---- Summary KPIs -----------------------------------------------------------

summary = sp.summary()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("skup.kpi_total"), str(summary["total_skus"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("skup.kpi_profitable"), str(summary["profitable"]),
        hint="", hint_tone="ok",
    )
with k3:
    metric_with_hint(
        t("skup.kpi_losing"), str(summary["losing"]),
        hint=t("skup.hint_losing") if summary["losing"] > 0 else "",
        hint_tone="danger" if summary["losing"] > 0 else "info",
    )
with k4:
    metric_with_hint(
        t("skup.kpi_avg_margin"), "{:.1f}%".format(summary["avg_margin"]),
        hint="", hint_tone="ok" if summary["avg_margin"] > 10 else "warn",
    )

# ---- SKU profit table --------------------------------------------------------

st.divider()

skus = sp.per_sku_profit()
if not skus:
    st.info(t("skup.empty"))
    st.stop()

# Sort options
c1, c2 = st.columns([1, 4])
with c1:
    sort_by = st.selectbox(
        t("skup.sort"),
        ["net_profit", "net_margin", "total_revenue", "total_qty", "profit_per_unit"],
        format_func=lambda k: {
            "net_profit": "💰 " + t("skup.sort_profit"),
            "net_margin": "📊 " + t("skup.sort_margin"),
            "total_revenue": "💵 " + t("skup.sort_revenue"),
            "total_qty": "📦 " + t("skup.sort_qty"),
            "profit_per_unit": "🎯 " + t("skup.sort_per_unit"),
        }.get(k, k),
        label_visibility="collapsed",
    )

reverse = sort_by != "health"
skus_sorted = sorted(skus, key=lambda x: x.get(sort_by, 0), reverse=reverse)

# Health filter
tab_all, tab_healthy, tab_warn, tab_lose = st.tabs([
    "📋 " + t("skup.tab_all") + " (" + str(len(skus)) + ")",
    "✅ " + t("skup.tab_healthy"),
    "⚠️ " + t("skup.tab_warning"),
    "🔴 " + t("skup.tab_losing"),
])


def _render_sku_rows(sku_list):
    for s in sku_list:
        health = s.get("health", "thin")
        health_icon = {"healthy": "✅", "warning": "⚠️", "thin": "🟡", "losing": "🔴"}.get(health, "?")
        margin_color = {"healthy": "#4d6c5c", "warning": "#c5963d",
                        "thin": "#c5963d", "losing": "#c54c4c"}.get(health, "#7a7569")

        rev_str = "{:,.0f}".format(s["total_revenue"])
        cogs_str = "{:,.0f}".format(s["total_cogs"])
        fees_str = "{:,.0f}".format(s["total_fees"])
        ret_str = "{:,.0f}".format(s.get("return_loss", 0))
        net_str = "{:,.0f}".format(s["net_profit"])
        ppu_str = "{:,.0f}".format(s["profit_per_unit"])

        st.markdown(
            "<div style='background:white;border:0.5px solid rgba(40,30,20,0.07);"
            "border-left:3px solid " + margin_color + ";border-radius:10px;"
            "padding:12px 16px;margin-bottom:6px'>"
            "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
            "<div>"
            "<span style='font-weight:600'>" + health_icon + " " + s["sku"] + "</span>"
            " <span style='color:#7a7569;font-size:12px'>" + s["name"][:30] + "</span>"
            "</div>"
            "<div style='display:flex;gap:14px;align-items:baseline;font-size:13px'>"
            "<span>📦 " + str(s["total_qty"]) + "u</span>"
            "<span>💵 ฿" + rev_str + "</span>"
            "<span style='color:" + margin_color + ";font-weight:600;font-size:1.1rem'>"
            "฿" + net_str + " (" + "{:.1f}%".format(s["net_margin"]) + ")</span>"
            "</div></div>"
            "<div style='color:#9a9485;font-size:11px;margin-top:4px;display:flex;gap:14px'>"
            "<span>COGS ฿" + cogs_str + "</span>"
            "<span>Fees ฿" + fees_str + "</span>"
            "<span>Returns ฿" + ret_str + "</span>"
            "<span>Per unit ฿" + ppu_str + "</span>"
            "<span>" + s.get("platforms", "") + "</span>"
            "</div></div>",
            unsafe_allow_html=True,
        )


with tab_all:
    _render_sku_rows(skus_sorted)

with tab_healthy:
    healthy = [s for s in skus_sorted if s["health"] == "healthy"]
    if healthy:
        _render_sku_rows(healthy)
    else:
        st.info(t("skup.none_healthy"))

with tab_warn:
    warning = [s for s in skus_sorted if s["health"] in ("warning", "thin")]
    if warning:
        _render_sku_rows(warning)
    else:
        st.success(t("skup.none_warning"))

with tab_lose:
    losing = [s for s in skus_sorted if s["health"] == "losing"]
    if losing:
        st.error(t("skup.losing_alert"))
        _render_sku_rows(losing)
    else:
        st.success(t("skup.none_losing"))
