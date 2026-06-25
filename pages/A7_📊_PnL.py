"""P&L Statement — formal income statement for tax and business review."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from datetime import datetime
import db
import pnl_statement as pnl
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint
from i18n import t
from i18n_inline import expense_category

st.set_page_config(page_title="nirva.sell · P&L", page_icon="📊", layout="wide")
apply_theme()
require_auth()
db.init()
render_sidebar()

page_header(icon="📊", title=t("pnl.title"), subtitle=t("pnl.caption"))

today = datetime.today()

# ---- Period selector --------------------------------------------------------
col_mode, col_y, col_m = st.columns(3)
with col_mode:
    mode = st.selectbox(
        t("pnl.f_period"),
        ["monthly", "quarterly", "annual"],
        format_func=lambda x: {"monthly": t("pnl.monthly"),
                                "quarterly": t("pnl.quarterly"),
                                "annual": t("pnl.annual")}.get(x, x),
        key="_pnl_mode",
    )
with col_y:
    year = st.number_input(t("pnl.f_year"), min_value=2020,
                           value=today.year, step=1, key="_pnl_year")
with col_m:
    if mode == "monthly":
        month = st.number_input(t("pnl.f_month"), min_value=1, max_value=12,
                                value=today.month, step=1, key="_pnl_month")
    elif mode == "quarterly":
        month = st.selectbox(t("pnl.f_quarter"), [1, 2, 3, 4],
                             format_func=lambda q: "Q" + str(q),
                             key="_pnl_qtr")
    else:
        month = None
        st.empty()

# Fetch statement
if mode == "monthly":
    stmt = pnl.monthly(int(year), int(month))
elif mode == "quarterly":
    stmt = pnl.quarterly(int(year), int(month))
else:
    stmt = pnl.annual(int(year))

profit_color = "#4d6c5c" if stmt["profitable"] else "#c54c4c"

# ---- KPIs -------------------------------------------------------------------
st.divider()
k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint("💰 " + t("pnl.net_revenue"),
                     "฿{:,.0f}".format(stmt["net_revenue"]),
                     hint="", hint_tone="info")
with k2:
    metric_with_hint("📈 " + t("pnl.gross_profit"),
                     "฿{:,.0f}".format(stmt["gross_profit"]) +
                     " ({:.0f}%)".format(stmt["gross_margin"]),
                     hint="", hint_tone="ok" if stmt["gross_profit"] > 0 else "danger")
with k3:
    metric_with_hint("💸 " + t("pnl.total_expenses"),
                     "฿{:,.0f}".format(stmt["total_expenses"]),
                     hint="", hint_tone="info")
with k4:
    metric_with_hint("🏆 " + t("pnl.net_profit"),
                     "฿{:,.0f}".format(stmt["net_profit"]) +
                     " ({:.0f}%)".format(stmt["net_margin"]),
                     hint="", hint_tone="ok" if stmt["profitable"] else "danger")

# ---- Full statement ---------------------------------------------------------
st.divider()
st.markdown("### " + t("pnl.statement_title") + " — " + stmt["label"])

ROWS = [
    ("revenue_header",   t("pnl.revenue_header"),   None,                True,  False),
    ("revenue",          t("pnl.gross_revenue"),     stmt["revenue"],     False, False),
    ("returns",          t("pnl.returns"),            -stmt["returns"],    False, False),
    ("net_revenue",      t("pnl.net_revenue"),        stmt["net_revenue"], False, True),
    ("spacer", "", None, False, False),
    ("cogs_header",      t("pnl.cogs_header"),        None,                True,  False),
    ("cogs",             t("pnl.cogs"),               -stmt["cogs"],       False, False),
    ("gross_profit",     t("pnl.gross_profit"),       stmt["gross_profit"],False, True),
    ("gross_margin",     "  " + t("pnl.gross_margin"),
                         str(stmt["gross_margin"]) + "%",                  False, False),
    ("spacer2", "", None, False, False),
    ("exp_header",       t("pnl.expenses_header"),    None,                True,  False),
]
for cat, amt in stmt["expenses"].items():
    ROWS.append((cat, "  " + expense_category(cat), -amt, False, False))
ROWS += [
    ("total_exp",        t("pnl.total_expenses"),     -stmt["total_expenses"], False, True),
    ("spacer3", "", None, False, False),
    ("net_profit",       t("pnl.net_profit"),         stmt["net_profit"],   False, True),
    ("net_margin",       "  " + t("pnl.net_margin"),
                         str(stmt["net_margin"]) + "%",                    False, False),
]

for row_id, label, value, is_header, is_subtotal in ROWS:
    if label == "":
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        continue

    if isinstance(value, str):
        val_str = value
    elif value is None:
        val_str = ""
    else:
        val_str = ("฿{:,.0f}".format(value) if value >= 0
                   else "−฿{:,.0f}".format(abs(value)))

    if is_header:
        bg = "rgba(77,108,92,0.06)"
        fw = "700"
        fs = "14px"
        color = "#3d5c4c"
    elif is_subtotal:
        bg = "rgba(40,30,20,0.04)"
        fw = "600"
        fs = "14px"
        color = profit_color if "profit" in row_id else "#2a2418"
    else:
        bg = "transparent"
        fw = "400"
        fs = "13px"
        color = "#4a4035"

    val_color = profit_color if (isinstance(value, float) and
                                  "profit" in row_id and is_subtotal) else color

    st.markdown(
        "<div style='display:flex;justify-content:space-between;align-items:center;"
        "padding:7px 16px;background:" + bg + ";border-radius:4px'>"
        "<span style='font-weight:" + fw + ";font-size:" + fs + ";color:" + color + "'>"
        + label + "</span>"
        "<span style='font-weight:" + fw + ";font-size:" + fs + ";color:" + val_color + "'>"
        + val_str + "</span></div>",
        unsafe_allow_html=True,
    )

# ---- Trend mini-chart -------------------------------------------------------
st.divider()
st.markdown("### " + t("pnl.trend_title"))

trend = pnl.monthly_trend(6)
if trend:
    import pandas as pd
    df = pd.DataFrame(trend)
    df = df.set_index("month")
    st.line_chart(df[["revenue", "gross_profit", "net_profit"]])
