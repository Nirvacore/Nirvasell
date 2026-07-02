"""Expense Tracker — know where your money goes.

"ขายเยอะแต่ไม่เหลือเงิน" — the #1 complaint from Thai home sellers.
Track: shipping, packaging, ads, platform fees, supplies. See true
profit = revenue (from Dashboard) minus expenses (from here)."""
from __future__ import annotations
import sys
from datetime import date, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st
import db
import expenses as exp
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import expense_category, platform_display

st.set_page_config(page_title="nirva.sell · Expenses",
                   page_icon="💸", layout="wide")
apply_theme()
require_auth()
db.init()
exp.init()
render_sidebar()

page_header(icon="💸", title=t("exp.title"), subtitle=t("exp.caption"))


# ---- KPI overview -------------------------------------------------------

s = exp.stats()
this_month = datetime.now().strftime("%Y-%m")

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_with_hint(
        t("exp.kpi_this_month"), f"฿{s['this_month']:,.0f}",
        hint="",
        hint_tone="info",
    )
with m2:
    delta = s["change_pct"]
    tone = "danger" if delta > 20 else ("warn" if delta > 0 else "ok")
    metric_with_hint(
        t("exp.kpi_vs_last"), f"{delta:+.0f}%",
        hint=t("exp.hint_up") if delta > 20 else (t("exp.hint_down") if delta < -10 else ""),
        hint_tone=tone,
    )
with m3:
    metric_with_hint(
        t("exp.kpi_last_month"), f"฿{s['last_month']:,.0f}",
        hint="",
        hint_tone="info",
    )
with m4:
    metric_with_hint(
        t("exp.kpi_total_entries"), str(s["count"]),
        hint="",
        hint_tone="info",
    )


# ---- Quick add form + category breakdown ---------------------------------

st.divider()
cForm, cBreak = st.columns([3, 2])

with cForm:
    st.markdown(f"### ➕ {t('exp.add_title')}")
    with st.form("add_expense"):
        c1, c2, c3 = st.columns(3)
        with c1:
            n_date = st.date_input(t("exp.f_date"), value=date.today())
        with c2:
            n_cat = st.selectbox(
                t("exp.f_category"),
                exp.CATEGORIES,
                format_func=lambda k: f"{exp.CATEGORY_ICONS.get(k,'')} {t(f'exp.cat_{k}')}",
            )
        with c3:
            n_amount = st.number_input(t("exp.f_amount"), min_value=0.0,
                                        step=10.0, format="%.0f")
        c4, c5 = st.columns([3, 1])
        with c4:
            n_note = st.text_input(t("exp.f_note"),
                                    placeholder=t("exp.note_placeholder"))
        with c5:
            n_plat = st.selectbox(
                t("exp.f_platform"),
                ["", "shopee", "lazada", "tiktok", "facebook", "line"],
                format_func=lambda p: platform_display(p, empty="—"),
            )
        if st.form_submit_button(t("exp.add_btn"), type="primary"):
            if n_amount > 0:
                exp.add(date=n_date.isoformat(), category=n_cat,
                        amount=n_amount, note=n_note, platform=n_plat)
                toast(t("exp.added"), icon="✓")
                st.rerun()
            else:
                st.warning(t("exp.amount_zero"))


with cBreak:
    st.markdown(f"### 📊 {t('exp.breakdown_title')}")
    summary = exp.monthly_summary(this_month)
    if summary["total"] > 0:
        for cat, total in sorted(summary["breakdown"].items(),
                                  key=lambda x: -x[1]):
            pct = total / summary["total"] * 100
            icon = exp.CATEGORY_ICONS.get(cat, "📝")
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;"
                f"align-items:center;padding:6px 0;border-bottom:0.5px solid "
                f"rgba(40,30,20,0.05)'>"
                f"<div style='font-size:14px'>{icon} {t(f'exp.cat_{cat}')}</div>"
                f"<div style='font-family:\"Cormorant Garamond\",serif;"
                f"font-size:1.1rem;color:#1c1c1c'>฿{total:,.0f} "
                f"<span style='color:#7a7569;font-size:11px'>({pct:.0f}%)</span></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.caption(t("exp.no_data"))


# ---- Monthly trend chart ------------------------------------------------

st.divider()
st.markdown(f"### 📈 {t('exp.trend_title')}")

monthly = exp.monthly_totals(months=6)
if monthly and any(m["total"] > 0 for m in monthly):
    df_trend = pd.DataFrame(monthly)
    df_trend = df_trend.set_index("month")
    cat_cols = [c for c in df_trend.columns if c != "total" and c in exp.CATEGORIES]
    if cat_cols:
        st.bar_chart(df_trend[cat_cols], width="stretch")
    else:
        st.line_chart(df_trend[["total"]], width="stretch")
else:
    st.caption(t("exp.no_trend"))


# ---- Expense history list -----------------------------------------------

st.divider()
st.markdown(f"### 📋 {t('exp.history_title')}")

month_filter = st.selectbox(
    t("exp.month_filter"),
    [""] + [datetime(datetime.now().year, m, 1).strftime("%Y-%m")
            for m in range(datetime.now().month, 0, -1)],
    format_func=lambda m: t("exp.all_months") if not m else m,
    label_visibility="collapsed",
)

rows = exp.all_expenses(month=month_filter)
if not rows:
    st.info(t("exp.no_entries"))
else:
    for r in rows:
        icon = exp.CATEGORY_ICONS.get(r["category"], "📝")
        cat_label = t("exp.cat_" + r["category"])
        cA, cB, cC = st.columns([5, 1, 1])
        with cA:
            plat_str = " · " + r["platform"] if r.get("platform") else ""
            note_str = r.get("note", "")
            amount_str = "{:,.0f}".format(r["amount"])
            date_str = r.get("date", "")
            st.markdown(
                "<div style='padding:8px 0;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                "<div style='font-size:14px'>" + icon + " " + cat_label + " "
                "<span style='color:#7a7569;font-size:12px'>" + note_str + plat_str + "</span></div>"
                "<div style='font-family:Cormorant Garamond,serif;font-size:1.1rem;"
                "color:#c54c4c'>-฿" + amount_str + "</div></div>"
                "<div style='color:#9a9485;font-size:11px'>" + date_str + "</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        with cB:
            if st.button("✏", key=f"_ee_{r['id']}",
                         type="tertiary", help=t("common.edit")):
                st.session_state["_exp_edit_id"] = r["id"]
                st.rerun()
        with cC:
            if st.button("🗑", key=f"_ed_{r['id']}",
                         type="tertiary", help=t("common.delete")):
                exp.delete(r["id"])
                toast(t("common.deleted"), icon="🗑")
                st.rerun()


# ---- Edit drawer --------------------------------------------------------

edit_id = st.session_state.get("_exp_edit_id")
if edit_id:
    row_data = next((r for r in rows if r["id"] == edit_id), None)
    if row_data:
        st.divider()
        st.markdown(f"### ✏ {t('exp.edit_title')}")
        with st.form("_exp_edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                ed_date = st.date_input(t("exp.f_date"),
                    value=date.fromisoformat(row_data["date"]) if row_data.get("date") else date.today())
            with c2:
                ed_cat = st.selectbox(
                    t("exp.f_category"), exp.CATEGORIES,
                    index=exp.CATEGORIES.index(row_data["category"])
                          if row_data["category"] in exp.CATEGORIES else 7,
                    format_func=lambda k: f"{exp.CATEGORY_ICONS.get(k,'')} {t(f'exp.cat_{k}')}",
                )
            with c3:
                ed_amount = st.number_input(t("exp.f_amount"),
                    value=float(row_data["amount"]), step=10.0, format="%.0f")
            ed_note = st.text_input(t("exp.f_note"), value=row_data.get("note", ""))
            ca, cb = st.columns(2)
            with ca:
                if st.form_submit_button(t("common.save"), type="primary", width="stretch"):
                    exp.update(edit_id, date=ed_date.isoformat(), category=ed_cat,
                               amount=ed_amount, note=ed_note)
                    st.session_state.pop("_exp_edit_id", None)
                    toast(t("common.saved"), icon="✓")
                    st.rerun()
            with cb:
                if st.form_submit_button(t("common.cancel"), width="stretch"):
                    st.session_state.pop("_exp_edit_id", None)
                    st.rerun()
