"""Compare nirva.sell vs BigSeller / Ginee / Page365.

Public — anyone can view (no auth gate). Used as a sales-floor weapon when
a Thai reseller is evaluating their options. Honest comparison; we don't
claim parity we don't have. Updated alongside `competitive_intel.md`."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import auth
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _components import page_header
from i18n import t

st.set_page_config(page_title="nirva.sell · vs Competitors",
                   page_icon="⚖", layout="wide")
apply_theme()

# Public — but render sidebar only if logged in
if auth.is_authenticated():
    render_sidebar()
else:
    st.sidebar.markdown(
        "<div style='font-family:Inter,sans-serif;font-size:18px;"
        "font-weight:600;letter-spacing:-0.02em;margin:6px 0 14px'>"
        "nirva<span style='color:#4d6c5c'>.sell</span></div>",
        unsafe_allow_html=True,
    )
    st.sidebar.page_link("app.py", label=f"← {t('legal.back_to_login')}")


page_header(icon="⚖", title=t("compare.title"), subtitle=t("compare.caption"))

# ---- Hero one-liner ----------------------------------------------------
st.markdown(
    f"<div style='background:linear-gradient(135deg,rgba(77,108,92,0.06),"
    f"rgba(77,108,92,0.02));border:1px solid rgba(77,108,92,0.15);"
    f"border-radius:12px;padding:22px 24px;margin:6px 0 22px;"
    f"font-family:Cormorant Garamond,serif;font-size:1.4rem;color:#1f1f1f;"
    f"font-weight:500;line-height:1.4'>"
    f"💡 {t('compare.thesis')}"
    f"</div>",
    unsafe_allow_html=True,
)


# ---- Big feature matrix ------------------------------------------------

# (i18n_key, nirva, bigseller, ginee, page365)
# Cells use "✅" (yes/clear win), "🟡" (partial), "❌" (no/missing), or a price
ROWS = [
    ("compare.row_price",   "compare.cell_nirva_price",  "RM129–1299/mo",     "$15–149/mo",       "฿799–5999/mo"),
    ("compare.row_orders",  "compare.cell_unlimited",    "1,500 free / month", "Limited free",     "800 bills/mo"),
    ("compare.row_stores",  "compare.cell_unlimited",    "3 free / 16 paid",   "Limited",          "Per-tier limit"),

    ("compare.row_ai_listing",  "✅",  "❌",  "❌",  "❌"),
    ("compare.row_ai_live",     "✅",  "❌",  "❌",  "🟡 (manual CF)"),
    ("compare.row_ai_review",   "✅",  "🟡 (template)",  "❌",  "❌"),
    ("compare.row_ai_vision",   "✅",  "❌",  "❌",  "❌"),

    ("compare.row_stock_sync",      "🟡 (CSV)",  "✅",  "✅",  "✅"),
    ("compare.row_wms",             "🟡 (label print)",  "✅",  "✅",  "🟡"),
    ("compare.row_wallet",          "🟡 (manual log)",  "✅",  "✅",  "❌"),
    ("compare.row_marketplaces",    "14 export formats",  "16 API integ.",  "20+ API",  "Native chat"),

    ("compare.row_pdpa",        "✅ Open ToS",  "🟡",  "🟡",  "🟡"),
    ("compare.row_open_source", "✅ MIT",       "❌",  "❌",  "❌"),
    ("compare.row_self_host",   "✅ Docker",    "❌",  "❌",  "❌"),
    ("compare.row_byok",        "compare.cell_nirva_byok",  "❌",  "❌",  "❌"),
    ("compare.row_languages",   "19 langs",     "EN / ZH",  "EN / ZH",  "TH only"),
]

st.markdown(f"### {t('compare.matrix_title')}")
st.caption(t("compare.matrix_legend"))

import pandas as pd

def _matrix_cell(val):
    if isinstance(val, str) and val.startswith("compare.cell_"):
        return t(val)
    return val

df = pd.DataFrame([
    {
        t("compare.col_feature"):    t(key),
        "🌙 nirva.sell":              _matrix_cell(nv),
        "BigSeller":                  bs,
        "Ginee":                      gn,
        "Page365":                    pg,
    }
    for key, nv, bs, gn, pg in ROWS
])
st.dataframe(df, width='stretch', hide_index=True, height=620)


# ---- Where nirva wins / where competitors win --------------------------
st.divider()
cW, cL = st.columns(2)

with cW:
    st.markdown(f"### ✅ {t('compare.win_title')}")
    st.markdown(t("compare.win_body"))

with cL:
    st.markdown(f"### 🔍 {t('compare.honest_title')}")
    st.markdown(t("compare.honest_body"))


# ---- Pricing wedge -----------------------------------------------------
st.divider()
st.markdown(f"### 💰 {t('compare.pricing_title')}")
st.caption(t("compare.pricing_caption"))

p1, p2, p3 = st.columns(3)
with p1:
    st.markdown(
        "<div style='background:white;border:1px solid rgba(40,30,20,0.08);"
        "border-radius:12px;padding:20px;min-height:200px'>"
        "<div style='font-size:24px'>🌙</div>"
        "<div style='font-family:Cormorant Garamond,serif;font-size:1.4rem;"
        "font-weight:500;margin-top:6px'>nirva.sell</div>"
        f"<div style='color:#4d6c5c;font-weight:600;margin:8px 0'>"
        f"{t('compare.nirva_price')}</div>"
        f"<div style='color:#6b6b6b;font-size:13px;line-height:1.6'>"
        f"{t('compare.nirva_body')}</div></div>",
        unsafe_allow_html=True,
    )
with p2:
    st.markdown(
        "<div style='background:#fbf9f3;border:1px solid rgba(40,30,20,0.05);"
        "border-radius:12px;padding:20px;min-height:200px'>"
        "<div style='font-size:24px'>📊</div>"
        "<div style='font-family:Cormorant Garamond,serif;font-size:1.4rem;"
        "font-weight:500;margin-top:6px'>BigSeller</div>"
        f"<div style='color:#7a7569;font-weight:600;margin:8px 0'>"
        f"RM129–1,299/mo</div>"
        f"<div style='color:#6b6b6b;font-size:13px;line-height:1.6'>"
        f"{t('compare.bigseller_body')}</div></div>",
        unsafe_allow_html=True,
    )
with p3:
    st.markdown(
        "<div style='background:#fbf9f3;border:1px solid rgba(40,30,20,0.05);"
        "border-radius:12px;padding:20px;min-height:200px'>"
        "<div style='font-size:24px'>💬</div>"
        "<div style='font-family:Cormorant Garamond,serif;font-size:1.4rem;"
        "font-weight:500;margin-top:6px'>Page365</div>"
        f"<div style='color:#7a7569;font-weight:600;margin:8px 0'>"
        f"฿799–5,999/mo</div>"
        f"<div style='color:#6b6b6b;font-size:13px;line-height:1.6'>"
        f"{t('compare.page365_body')}</div></div>",
        unsafe_allow_html=True,
    )

st.markdown(
    f"<div style='margin-top:28px;text-align:center;color:#9a9485;font-size:12px'>"
    f"{t('compare.disclaimer')}"
    f"</div>",
    unsafe_allow_html=True,
)
