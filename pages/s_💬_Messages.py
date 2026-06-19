"""Message Templates — copy-paste sales messages in seconds.

Pre-built Thai seller templates: order confirm, shipping notice,
review request, VIP follow-up. Fill variables, copy, paste to LINE."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import msg_templates as mt
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, metric_with_hint, toast
from i18n import t

st.set_page_config(page_title="nirva.sell · Messages",
                   page_icon="💬", layout="wide")
apply_theme()
require_auth()
db.init()
mt.init()
render_sidebar()

page_header(icon="💬", title=t("msg.title"), subtitle=t("msg.caption"))


# ---- KPIs -------------------------------------------------------------------

s = mt.stats()

k1, k2, k3 = st.columns(3)
with k1:
    metric_with_hint(
        t("msg.kpi_templates"), str(s["total"]),
        hint="", hint_tone="info",
    )
with k2:
    metric_with_hint(
        t("msg.kpi_uses"), str(s["total_uses"]),
        hint="", hint_tone="ok",
    )
with k3:
    metric_with_hint(
        t("msg.kpi_popular"), s["most_used"],
        hint="", hint_tone="info",
    )


# ---- Quick use: fill and copy -----------------------------------------------

st.divider()
st.markdown("### " + t("msg.quick_use"))

templates = mt.all_templates()
if not templates:
    st.info(t("msg.empty"))
    st.stop()

# Category filter
cat_keys = ["all"] + list(mt.CATEGORIES.keys())
selected_cat = st.selectbox(
    t("msg.filter_cat"),
    cat_keys,
    format_func=lambda k: ("📋 " + t("msg.all")) if k == "all"
    else (mt.CATEGORIES[k]["icon"] + " " + mt.CATEGORIES[k]["label"]),
    label_visibility="collapsed",
)

filtered = templates if selected_cat == "all" else mt.by_category(selected_cat)

for tmpl in filtered:
    cat_info = mt.CATEGORIES.get(tmpl["category"], {"icon": "📝", "label": ""})
    uses = tmpl.get("use_count", 0)

    with st.expander(
        cat_info["icon"] + " " + tmpl["name"] +
        " · " + t("msg.used_count", n=str(uses)),
        expanded=False,
    ):
        # Show template with variable placeholders
        st.code(tmpl["body"], language=None)

        # Variable inputs
        variables = [v.strip() for v in (tmpl.get("variables") or "").split(",") if v.strip()]
        if variables:
            st.caption(t("msg.fill_vars"))
            values = {}
            vcols = st.columns(min(len(variables), 3))
            for vi, var in enumerate(variables):
                with vcols[vi % len(vcols)]:
                    values[var] = st.text_input(
                        var,
                        key="_v_" + str(tmpl["id"]) + "_" + var,
                        placeholder=var,
                        label_visibility="collapsed",
                    )

            # Generate filled message
            if any(values.values()):
                filled = tmpl["body"]
                for k, v in values.items():
                    if v:
                        filled = filled.replace("{" + k + "}", v)

                st.markdown("---")
                st.markdown("**" + t("msg.result") + ":**")
                st.code(filled, language=None)

                if st.button(
                    "📋 " + t("msg.copy"),
                    key="_cp_" + str(tmpl["id"]),
                    type="primary",
                ):
                    mt.record_use(tmpl["id"])
                    st.code(filled, language=None)
                    toast(t("msg.copied"), icon="✓")
        else:
            if st.button(
                "📋 " + t("msg.copy"),
                key="_cp2_" + str(tmpl["id"]),
                type="tertiary",
            ):
                mt.record_use(tmpl["id"])
                toast(t("msg.copied"), icon="✓")


# ---- Create custom template -------------------------------------------------

st.divider()
with st.expander(t("msg.create_title"), expanded=False):
    with st.form("create_msg"):
        m_name = st.text_input(t("msg.f_name") + " *", placeholder=t("msg.name_ph"))

        mc1, mc2 = st.columns(2)
        with mc1:
            m_cat = st.selectbox(
                t("msg.f_category"),
                list(mt.CATEGORIES.keys()),
                format_func=lambda k: mt.CATEGORIES[k]["icon"] + " " + mt.CATEGORIES[k]["label"],
            )
        with mc2:
            m_plat = st.selectbox(t("msg.f_platform"), mt.PLATFORMS)

        m_body = st.text_area(
            t("msg.f_body") + " *",
            height=150,
            placeholder=t("msg.body_ph"),
        )
        m_vars = st.text_input(
            t("msg.f_vars"),
            placeholder=t("msg.vars_ph"),
        )

        if st.form_submit_button(t("msg.create_btn"), type="primary"):
            if m_name.strip() and m_body.strip():
                mt.add(m_name.strip(), m_cat, m_plat, m_body.strip(), m_vars.strip())
                toast(t("msg.created"), icon="✓")
                st.rerun()
            else:
                st.warning(t("msg.need_fields"))
