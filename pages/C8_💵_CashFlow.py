"""Cash Flow — income vs expenses, net by day and month."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import cash_flow as cf
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

st.set_page_config(page_title="nirva.sell · Cash Flow",
                   page_icon="💵", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="💵", title=t("cf.title"), subtitle=t("cf.caption"))

forecast = cf.current_month_forecast()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("📅 " + t("cf.kpi_so_far"),
                     "฿{:,.0f}".format(forecast["this_month_so_far"]),
                     hint=str(forecast["days_elapsed"]) + " " + t("common.day_unit"),
                     hint_tone="info")
with k2:
    metric_with_hint("🔮 " + t("cf.kpi_projected"),
                     "฿{:,.0f}".format(forecast["projected_month"]),
                     hint="", hint_tone="ok")
with k3:
    g_pct = forecast["growth_pct"]
    metric_with_hint(
        ("📈" if g_pct >= 0 else "📉") + " " + t("cf.kpi_growth"),
        ("+" if g_pct >= 0 else "") + str(g_pct) + "%",
        hint=t("cf.vs_last_month"), hint_tone="ok" if g_pct >= 0 else "warn",
    )
with k4:
    metric_with_hint("💸 " + t("cf.kpi_expenses"),
                     "฿{:,.0f}".format(forecast["this_month_expenses"]),
                     hint="", hint_tone="info")

st.divider()

# ---- Toggle -----------------------------------------------------------------
view = st.segmented_control(
    t("cf.f_view"),
    ["monthly", "daily"],
    format_func=lambda x: t("cf.view_monthly") if x == "monthly" else t("cf.view_daily"),
    default="monthly",
    key="_cf_view",
)

if view == "monthly":
    months_data = cf.monthly(6)
    if not months_data:
        st.info(t("cf.empty"))
        st.stop()

    if HAS_PANDAS:
        df = pd.DataFrame(months_data)
        df = df.set_index("month")
        st.line_chart(df[["income", "expenses", "net"]])
    else:
        for m in months_data:
            net_color = "#4d6c5c" if m["net"] >= 0 else "#c54c4c"
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<span><strong>" + m["month"] + "</strong></span>"
                "<span style='display:flex;gap:16px;font-size:13px'>"
                "<span style='color:#4d6c5c'>+฿{:,.0f}".format(m["income"]) + "</span>"
                "<span style='color:#c54c4c'>-฿{:,.0f}".format(m["expenses"]) + "</span>"
                "<span style='font-weight:600;color:" + net_color + "'>"
                "= ฿{:,.0f}".format(m["net"]) + " (" + str(m["margin_pct"]) + "%)</span>"
                "</span></div>",
                unsafe_allow_html=True,
            )

else:
    days = st.select_slider(t("cf.f_days"),
                             options=[7, 14, 30, 60], value=30, key="_cf_d")
    daily_data = cf.daily(days)
    if not daily_data:
        st.info(t("cf.empty"))
        st.stop()

    if HAS_PANDAS:
        df = pd.DataFrame(daily_data)
        df = df.set_index("day")
        st.line_chart(df[["income", "expenses", "cumulative"]])
    else:
        for d in daily_data[-14:]:
            net_color = "#4d6c5c" if d["net"] >= 0 else "#c54c4c"
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:6px 14px;border-bottom:0.5px solid rgba(40,30,20,0.04)'>"
                "<span>" + d["day"] + "</span>"
                "<span style='display:flex;gap:12px;font-size:12px'>"
                "<span style='color:#4d6c5c'>+฿{:,.0f}".format(d["income"]) + "</span>"
                "<span style='color:#c54c4c'>-฿{:,.0f}".format(d["expenses"]) + "</span>"
                "<span style='font-weight:600;color:" + net_color + "'>"
                "฿{:,.0f}".format(d["net"]) + "</span>"
                "</span></div>",
                unsafe_allow_html=True,
            )

# ---- Monthly summary --------------------------------------------------------
st.divider()
s = cf.summary()
st.caption(
    t("cf.avg_net_caption") + " ฿{:,.0f}".format(s["avg_monthly_net"]) +
    " · " + t("common.trend") + ": " + s["trend"]
)
