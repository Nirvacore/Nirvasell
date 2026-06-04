"""Custom Tasks — define your own AI task without writing code.

Each task you save shows up in the Generate page + all_in_one flows as if
it were a built-in. Per-user — your custom tasks don't leak to others."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import custom_tasks as ct
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import friendly_error
from i18n import t


_DEFAULT_PROMPT = """คุณคือ {{role-here}} สำหรับ marketplace ไทย

ข้อมูลสินค้า:
{ctx}

(เขียนคำสั่งเฉพาะของคุณตรงนี้ — เช่น "สร้าง email สำหรับ B2B customers" หรือ "เขียน Twitter thread 5 tweets")

ส่งกลับ JSON object เท่านั้น ห้ามใส่ ``` หรือคำอธิบาย"""


st.set_page_config(page_title="nirva.sell · Custom Tasks", page_icon="✏", layout="wide")
apply_theme()
require_auth()
db.init()
ct.init()
render_sidebar()

page_header(icon="✏", title=t("custom_task.title"), subtitle=t("custom_task.caption"))


# ---- Existing custom tasks ----------------------------------------------

custom = ct.list_custom()
if custom:
    st.markdown(f"### {t('custom_task.existing_title')}")
    for row in custom:
        with st.expander(f"{row.get('icon','✨')} {row['label']} · `{row['key']}`"):
            st.caption(row.get("blurb") or "—")
            st.code(row.get("prompt") or "", language="text")
            st.caption(f"Output fields: {row.get('output_fields') or '—'}")
            if st.button(t("common.delete"), key=f"del_{row['key']}"):
                ct.delete(row["key"])
                st.rerun()


# ---- Create / edit form -------------------------------------------------

st.divider()
st.markdown(f"### {t('custom_task.create_title')}")
st.caption(t("custom_task.create_help"))

edit_key = st.session_state.get("edit_key", "")
preset = ct.get(edit_key) if edit_key else None

with st.form("custom_task_form"):
    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        key = st.text_input(
            t("custom_task.key"),
            value=preset["key"] if preset else "",
            help=t("custom_task.key_help"),
            disabled=bool(preset),
        )
    with c2:
        icon = st.text_input(
            t("custom_task.icon"),
            value=preset.get("icon", "✨") if preset else "✨",
            max_chars=4,
        )
    with c3:
        label = st.text_input(
            t("custom_task.label"),
            value=preset.get("label", "") if preset else "",
        )

    blurb = st.text_input(
        t("custom_task.blurb"),
        value=preset.get("blurb", "") if preset else "",
        placeholder=t("custom_task.blurb_placeholder"),
    )

    prompt = st.text_area(
        t("custom_task.prompt"),
        value=preset.get("prompt", "") if preset else _DEFAULT_PROMPT,
        height=240,
        help=t("custom_task.prompt_help"),
    )

    fields_text = st.text_input(
        t("custom_task.output_fields"),
        value=preset.get("output_fields", "") if preset else "headline,body",
        help=t("custom_task.output_fields_help"),
    )

    submitted = st.form_submit_button(t("common.save"), type="primary")
    if submitted:
        ok, msg = ct.save(
            key=key,
            label=label,
            icon=icon,
            blurb=blurb,
            prompt=prompt,
            output_fields=[f.strip() for f in fields_text.split(",")],
        )
        if ok:
            st.success(t("custom_task.saved"))
            st.session_state.pop("edit_key", None)
            st.rerun()
        else:
            st.error(msg)


# ---- Test runner --------------------------------------------------------

st.divider()
st.markdown(f"### {t('custom_task.test_title')}")

api_key = st.session_state.get("api_key", "")
if not api_key:
    st.info(t("generate.api_warn"))
else:
    if not custom:
        st.caption(t("custom_task.no_tasks_yet"))
    else:
        sel = st.selectbox(
            t("custom_task.pick_to_test"),
            [r["key"] for r in custom],
            format_func=lambda k: next(
                (f"{r.get('icon','')} {r['label']}" for r in custom if r["key"] == k),
                k,
            ),
        )
        sample = st.text_area(
            t("custom_task.test_product_info"),
            value="ชื่อ: Logitech MX Master 3S\nแบรนด์: Logitech\nหมวด: Mouse\nราคา: 3200\nสเปค: 8K DPI, wireless, 70-day battery",
            height=120,
        )
        if st.button(t("custom_task.run_test"), type="primary"):
            with st.spinner(t("generate.running")):
                try:
                    import generate as gen
                    task_obj = ct.CustomTask(ct.get(sel))
                    # Build a fake product dict from sample
                    product = {"sku":"TEST","name":"Test","brand":"","specs":sample,
                               "sell_price":0,"cost_price":0,"category":""}
                    results = gen.run_per_product(
                        [product], task_obj, api_key=api_key, workers=1,
                    )
                    r = results[0]
                    if "error" in r:
                        st.error(r["error"])
                    else:
                        st.success(t("custom_task.test_done"))
                        for f in task_obj.TASK["output_fields"]:
                            v = r.get(f, "")
                            st.markdown(f"**{f}**")
                            if len(str(v)) > 80:
                                st.text(str(v))
                            else:
                                st.write(v)
                except Exception as e:
                    friendly_error(e)
