"""Content Calendar — post consistently, sell consistently.

Plan social media posts across Facebook, Instagram, TikTok, LINE OA.
See a weekly view. Know when to post based on peak buying hours."""
from __future__ import annotations
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import content_calendar as cal
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t
from i18n_inline import day_names_mon_first, platform_name

st.set_page_config(page_title="nirva.sell · Calendar",
                   page_icon="📅", layout="wide")
apply_theme()
require_auth()
db.init()
cal.init()
render_sidebar()

page_header(icon="📅", title=t("cal.title"), subtitle=t("cal.caption"))


# ---- KPI overview -----------------------------------------------------------

cs = cal.stats()

k1, k2, k3, k4 = st.columns(4)
with k1:
    metric_with_hint(
        t("cal.kpi_total"), str(cs["total"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("cal.kpi_draft"), str(cs["draft"]),
        hint="", hint_tone="warn" if cs["draft"] > 0 else "info",
    )
with k3:
    metric_with_hint(
        t("cal.kpi_scheduled"), str(cs["scheduled"]),
        hint="", hint_tone="info",
    )
with k4:
    metric_with_hint(
        t("cal.kpi_posted"), str(cs["posted"]),
        hint="", hint_tone="ok",
    )


# ---- Weekly view -------------------------------------------------------------

st.divider()
st.markdown("### " + t("cal.week_title"))

# Week navigation
today = date.today()
week_offset = st.session_state.get("_cal_week", 0)
start = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)

nav1, nav2, nav3 = st.columns([1, 3, 1])
with nav1:
    if st.button("◀ " + t("cal.prev_week"), type="tertiary"):
        st.session_state["_cal_week"] = week_offset - 1
        st.rerun()
with nav2:
    end = start + timedelta(days=6)
    st.markdown(
        "<div style='text-align:center;font-weight:600;font-size:15px'>"
        + start.strftime("%d %b") + " — " + end.strftime("%d %b %Y") + "</div>",
        unsafe_allow_html=True,
    )
with nav3:
    if st.button(t("cal.next_week") + " ▶", type="tertiary"):
        st.session_state["_cal_week"] = week_offset + 1
        st.rerun()

# Day columns
DAY_NAMES_SHORT = day_names_mon_first()

week = cal.weekly_view(start)
day_cols = st.columns(7)

for i, (d_str, posts) in enumerate(week.items()):
    d = date.fromisoformat(d_str)
    is_today = d == today
    bg = "rgba(77,108,92,0.08)" if is_today else "rgba(40,30,20,0.02)"
    border = "2px solid #4d6c5c" if is_today else "1px solid rgba(40,30,20,0.06)"

    with day_cols[i]:
        st.markdown(
            "<div style='background:" + bg + ";border:" + border + ";"
            "border-radius:10px;padding:8px;min-height:120px;margin-bottom:4px'>"
            "<div style='font-weight:600;font-size:12px;text-align:center;"
            "margin-bottom:6px;color:" + ("#4d6c5c" if is_today else "#7a7569") + "'>"
            + DAY_NAMES_SHORT[i] + " " + str(d.day) + "</div>",
            unsafe_allow_html=True,
        )
        if posts:
            for p in posts:
                p_icon = cal.PLATFORM_ICONS.get(p.get("platform", ""), "📣")
                t_icon = cal.TYPE_ICONS.get(p.get("post_type", ""), "📦")
                status = p.get("status", "draft")
                s_color = {"draft": "#c5963d", "scheduled": "#4d6c5c",
                           "posted": "#7a7569", "cancelled": "#c54c4c"}.get(status, "#9a9485")
                time_str = (p.get("scheduled_time") or "")[:5]

                st.markdown(
                    "<div style='background:white;border-radius:6px;padding:4px 6px;"
                    "margin-bottom:3px;font-size:11px;border-left:3px solid " + s_color + "'>"
                    + p_icon + " " + t_icon + " " + time_str +
                    "<br><span style='font-weight:500'>" +
                    (p.get("title") or "—")[:20] + "</span></div>",
                    unsafe_allow_html=True,
                )

                if status == "draft":
                    if st.button("✅", key="_cpost_" + str(p["id"]),
                                 type="tertiary", help=t("cal.mark_posted")):
                        cal.update(p["id"], status="posted")
                        st.rerun()
        else:
            st.caption("—")
        st.markdown("</div>", unsafe_allow_html=True)


# ---- Add post ----------------------------------------------------------------

st.divider()
st.markdown("### " + t("cal.add_title"))

with st.form("add_post"):
    c1, c2, c3 = st.columns(3)
    with c1:
        n_title = st.text_input(t("cal.f_title") + " *", placeholder=t("cal.title_placeholder"))
        n_plat = st.selectbox(
            t("cal.f_platform"),
            cal.POST_PLATFORMS,
            format_func=lambda p: cal.PLATFORM_ICONS.get(p, "📣") + " " +
            platform_name(p),
        )
    with c2:
        n_type = st.selectbox(
            t("cal.f_type"),
            cal.POST_TYPES,
            format_func=lambda pt: cal.TYPE_ICONS.get(pt, "📦") + " " + t("cal.type_" + pt),
        )
        n_date = st.date_input(t("cal.f_date"), value=today)
    with c3:
        n_time = st.selectbox(
            t("cal.f_time"),
            ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00",
             "14:00", "15:00", "16:00", "17:00", "18:00", "19:00",
             "20:00", "21:00", "22:00"],
            index=2,
        )
        with db.conn() as c:
            sku_opts = [""] + [r["sku"] for r in c.execute(
                "SELECT sku FROM products WHERE sku IS NOT NULL ORDER BY sku"
            ).fetchall()]
        n_sku = st.selectbox(t("cal.f_sku"), sku_opts)

    n_caption = st.text_area(t("cal.f_caption"), height=80, placeholder=t("cal.caption_placeholder"))
    n_hashtags = st.text_input(t("cal.f_hashtags"), placeholder=t("cal.hashtags_ph"))

    if st.form_submit_button(t("cal.add_btn"), type="primary"):
        if n_title.strip():
            cal.add(
                title=n_title.strip(), platform=n_plat, post_type=n_type,
                scheduled_date=n_date.isoformat(), scheduled_time=n_time,
                product_sku=n_sku, caption=n_caption, hashtags=n_hashtags,
            )
            toast(t("cal.added"), icon="✓")
            st.rerun()
        else:
            st.warning(t("cal.need_title"))


# ---- Best posting times suggestion -------------------------------------------

st.divider()
st.markdown("### 🔥 " + t("cal.best_times"))

suggestions = cal.suggest_post_times()
if suggestions:
    st.caption(t("cal.best_times_help"))
    for s in suggestions:
        st.markdown(
            "<div style='display:inline-block;background:rgba(77,108,92,0.08);"
            "padding:6px 14px;border-radius:8px;margin:4px;font-size:13px'>"
            "📣 " + t("cal.post_at") + " <strong>" + s["post_time"] +
            "</strong> → 🛒 " + t("cal.peak_at") + " " + s["peak_buy_time"] +
            " (฿" + "{:,.0f}".format(s["revenue"]) + ")</div>",
            unsafe_allow_html=True,
        )
else:
    st.caption(t("cal.no_times_data"))


# ---- Upcoming posts ----------------------------------------------------------

st.divider()
st.markdown("### " + t("cal.upcoming_title"))
upcoming = cal.upcoming(14)
if upcoming:
    for p in upcoming:
        p_icon = cal.PLATFORM_ICONS.get(p.get("platform", ""), "📣")
        t_icon = cal.TYPE_ICONS.get(p.get("post_type", ""), "📦")
        status = p.get("status", "draft")
        s_label = t("cal.status_" + status)

        cA, cB = st.columns([5, 2])
        with cA:
            st.markdown(
                "<div style='padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div style='display:flex;justify-content:space-between'>"
                "<div>" + p_icon + " " + t_icon + " <strong>" +
                (p.get("title") or "—") + "</strong></div>"
                "<div style='color:#7a7569;font-size:12px'>" +
                (p.get("scheduled_date") or "") + " " +
                (p.get("scheduled_time") or "") + " · " + s_label +
                "</div></div></div>",
                unsafe_allow_html=True,
            )
        with cB:
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if status != "posted":
                    if st.button("✅", key="_up_" + str(p["id"]),
                                 type="tertiary", help=t("cal.mark_posted")):
                        cal.update(p["id"], status="posted")
                        st.rerun()
            with bc2:
                if status != "cancelled":
                    if st.button("❌", key="_uc_" + str(p["id"]),
                                 type="tertiary", help=t("cal.cancel")):
                        cal.update(p["id"], status="cancelled")
                        st.rerun()
            with bc3:
                if st.button("🗑", key="_ud_" + str(p["id"]),
                             type="tertiary", help=t("common.delete")):
                    cal.delete(p["id"])
                    st.rerun()
else:
    st.info(t("cal.no_upcoming"))
