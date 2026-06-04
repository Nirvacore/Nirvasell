"""First-run wizard. Walks a new user through:
  1. Paste Anthropic API key
  2. Add a product (manual or jump to Vision)
  3. Run one AI task on it
  4. Download a marketplace CSV
  5. Done

State persists in user_settings — re-visiting picks up where they left off.
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import user_settings as us
import onboarding as ob
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import friendly_error
from i18n import t

st.set_page_config(page_title="nirva.sell · Start", page_icon="🚀", layout="wide")
apply_theme()
require_auth()
db.init()
us.init()
render_sidebar()

# Pick up any milestones already met (e.g. user imported a CSV before
# returning to the wizard).
ob.autodetect_progress()

done, total = ob.progress()
visible_total = total - 1  # exclude the silent "done" marker step

page_header(icon="🚀", title=t("onboard.title"), subtitle=t("onboard.caption"))

# ---- Progress bar -------------------------------------------------------
visible_done = min(done, visible_total)
st.progress(visible_done / visible_total if visible_total else 1.0)
st.caption(f"{visible_done} / {visible_total}")

completed = set(ob.completed_steps())


def _step_header(num: int, key: str, label: str):
    icon = "✅" if key in completed else f"**{num}.**"
    st.markdown(f"### {icon} {label}")


st.divider()

# ---- Step 1: API key ----------------------------------------------------

_step_header(1, "api_key", t("onboard.step1_title"))
st.caption(t("onboard.step1_help"))

if "api_key" not in completed:
    with st.form("ob_api"):
        key = st.text_input(
            t("sidebar.api_key"),
            value=us.get("anthropic_api_key", "") or "",
            type="password",
        )
        if st.form_submit_button(t("common.save"), type="primary"):
            us.set("anthropic_api_key", key.strip())
            st.session_state["api_key"] = key.strip()
            if key.strip():
                ob.mark_step("api_key")
            st.rerun()
else:
    st.success(t("onboard.step1_done"))

# ---- Step 2: First product ---------------------------------------------

st.divider()
_step_header(2, "first_product", t("onboard.step2_title"))
st.caption(t("onboard.step2_help"))

if "first_product" not in completed:
    cA, cB = st.columns(2)
    with cA:
        st.markdown(f"**{t('onboard.step2_manual')}**")
        with st.form("ob_product"):
            name = st.text_input(t("catalog.col_name"), placeholder="Logitech MX Master 3S")
            brand = st.text_input(t("catalog.col_brand"), placeholder="Logitech")
            price = st.number_input(t("common.price"), min_value=0, value=3200)
            specs = st.text_area(t("catalog.col_specs"), placeholder="8K DPI, wireless, 70-day battery")
            if st.form_submit_button(t("onboard.step2_add"), type="primary"):
                if name.strip():
                    try:
                        with db.conn() as c:
                            c.execute(
                                """INSERT INTO products (sku, name, brand, category,
                                                         specs, cost_price, sell_price)
                                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                ("SKU-START-1", name.strip(), brand.strip(),
                                 "Demo", specs.strip(), price, price),
                            )
                        ob.mark_step("first_product")
                        st.success(t("onboard.step2_added"))
                        st.rerun()
                    except Exception as e:
                        friendly_error(e)
                else:
                    st.error(t("onboard.step2_need_name"))
    with cB:
        st.markdown(f"**{t('onboard.step2_vision')}**")
        st.caption(t("onboard.step2_vision_help"))
        st.page_link("pages/8_📸_Vision.py", label=f"📸 {t('onboard.step2_open_vision')}")
        st.page_link("pages/5_🔌_Import.py", label=f"🔌 {t('onboard.step2_open_import')}")
else:
    st.success(t("onboard.step2_done"))

# ---- Step 3: First AI generation ---------------------------------------

st.divider()
_step_header(3, "first_generate", t("onboard.step3_title"))
st.caption(t("onboard.step3_help"))

if "first_generate" not in completed:
    if "api_key" not in completed:
        st.warning(t("onboard.step3_need_key"))
    elif "first_product" not in completed:
        st.warning(t("onboard.step3_need_product"))
    else:
        st.page_link("pages/3_🤖_Generate.py", label=f"🤖 {t('onboard.step3_open_generate')}")
        if st.button(t("onboard.step3_mark_done")):
            ob.mark_step("first_generate")
            st.rerun()
else:
    st.success(t("onboard.step3_done"))

# ---- Step 4: First export ----------------------------------------------

st.divider()
_step_header(4, "first_export", t("onboard.step4_title"))
st.caption(t("onboard.step4_help"))

if "first_export" not in completed:
    if "first_generate" not in completed:
        st.warning(t("onboard.step4_need_generate"))
    else:
        st.page_link("pages/4_📜_History.py", label=f"📜 {t('onboard.step4_open_history')}")
        if st.button(t("onboard.step4_mark_done")):
            ob.mark_step("first_export")
            st.rerun()
else:
    st.success(t("onboard.step4_done"))

# ---- Finish -------------------------------------------------------------

st.divider()
if "first_export" in completed and "first_generate" in completed:
    st.markdown(f"### 🎉 {t('onboard.finish_title')}")
    st.write(t("onboard.finish_body"))
    cF1, cF2 = st.columns(2)
    with cF1:
        if st.button(t("onboard.finish_dismiss"), type="primary"):
            ob.mark_step("done")
            st.balloons()
            st.rerun()
    with cF2:
        if st.button(t("onboard.finish_restart")):
            ob.reset()
            st.rerun()
else:
    st.caption(t("onboard.finish_keep_going"))
