"""Quick Replies — copy-paste daily FAQ answers in one click.

The "page every home seller will open 10 times per day". Designed to be
keyboard-light: open page → see all replies → click → text on clipboard
→ paste into LINE / FB / Shopee chat."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import quick_replies as qr
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import page_header, toast, friendly_error
from i18n import t

st.set_page_config(page_title="nirva.sell · Quick Replies",
                   page_icon="💬", layout="wide")
apply_theme()
require_auth()
db.init()
qr.init()
render_sidebar()

page_header(icon="💬", title=t("qr.title"), subtitle=t("qr.caption"))

# ---- Category filter chips --------------------------------------------
CATEGORY_ICONS = {
    "all":      "🌐",
    "shipping": "🚚",
    "stock":    "📦",
    "price":    "💰",
    "payment":  "💳",
    "delivery": "📅",
    "return":   "🔄",
    "greeting": "👋",
    "general":  "💬",
}

cats = ["all"] + qr.categories()
chosen = st.session_state.get("_qr_cat", "all")
cat_cols = st.columns(min(len(cats), 8))
for i, cat in enumerate(cats):
    icon = CATEGORY_ICONS.get(cat, "💬")
    with cat_cols[i % len(cat_cols)]:
        if st.button(
            f"{icon} {t(f'qr.cat_{cat}')}",
            key=f"_qr_pick_{cat}",
            type="primary" if chosen == cat else "tertiary",
            width="stretch",
        ):
            st.session_state["_qr_cat"] = cat
            st.rerun()


# ---- The replies — rendered as click-to-copy cards -------------------
replies = qr.all_replies(category=None if chosen == "all" else chosen)

if not replies:
    st.info(t("qr.empty"))
else:
    # 2-column grid of reply cards
    for i in range(0, len(replies), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j >= len(replies):
                break
            r = replies[i + j]
            with cols[j]:
                rendered = qr.render(r["body"])
                # Card
                cat_icon = CATEGORY_ICONS.get(r["category"], "💬")
                st.markdown(
                    f"<div style='background:white;border:1px solid rgba(40,30,20,0.06);"
                    f"border-radius:10px;padding:14px 16px;margin-bottom:10px;"
                    f"min-height:130px'>"
                    f"<div style='display:flex;justify-content:space-between;"
                    f"align-items:center;margin-bottom:6px'>"
                    f"<div style='font-weight:600;color:#1f1f1f;font-size:14px'>"
                    f"{cat_icon} {r['title']}</div>"
                    f"<div style='color:#9a9485;font-size:11px'>×{r['use_count']}</div>"
                    f"</div>"
                    f"<div style='color:#3d3d3d;font-size:13px;line-height:1.55;"
                    f"white-space:pre-wrap'>{rendered}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                # Action row — copy + edit + delete
                cA, cB, cC = st.columns([2, 1, 1])
                with cA:
                    if st.button(f"📋 {t('qr.copy')}",
                                 key=f"_qr_copy_{r['id']}",
                                 type="primary", width="stretch"):
                        # Streamlit can't write to clipboard server-side — we
                        # show the text in a code block and use JS to copy.
                        st.session_state[f"_qr_copy_target_{r['id']}"] = rendered
                        qr.bump_use(r["id"])
                        toast(t("qr.copied"), icon="📋")
                with cB:
                    if st.button("✏", key=f"_qr_edit_{r['id']}",
                                 type="tertiary", width="stretch",
                                 help=t("common.edit")):
                        st.session_state["_qr_edit_id"] = r["id"]
                        st.rerun()
                with cC:
                    if st.button("🗑", key=f"_qr_del_{r['id']}",
                                 type="tertiary", width="stretch",
                                 help=t("common.delete")):
                        qr.delete(r["id"])
                        toast(t("common.deleted"), icon="🗑")
                        st.rerun()
                # JS one-shot copy when the user clicked Copy
                if st.session_state.get(f"_qr_copy_target_{r['id']}"):
                    txt = st.session_state.pop(f"_qr_copy_target_{r['id']}")
                    safe = (txt.replace("\\", "\\\\").replace("`", "\\`")
                                .replace("\n", "\\n").replace("$", "\\$"))
                    st.components.v1.html(
                        f"""<script>
                          navigator.clipboard.writeText(`{safe}`).catch(()=>{{}});
                        </script>""",
                        height=0,
                    )


# ---- Edit drawer (only if a row was clicked) -------------------------
edit_id = st.session_state.get("_qr_edit_id")
if edit_id:
    target = next((r for r in qr.all_replies() if r["id"] == edit_id), None)
    if target:
        st.divider()
        st.markdown(f"### ✏ {t('qr.edit_title')}")
        with st.form("_qr_edit_form"):
            new_title = st.text_input(t("qr.f_title"), value=target["title"])
            new_cat = st.selectbox(
                t("qr.f_category"),
                options=list(CATEGORY_ICONS.keys())[1:],  # skip "all"
                index=list(CATEGORY_ICONS.keys())[1:].index(target["category"])
                      if target["category"] in CATEGORY_ICONS else 7,
            )
            new_body = st.text_area(t("qr.f_body"), value=target["body"], height=150)
            st.caption(t("qr.variables_hint"))
            c1, c2 = st.columns([1, 1])
            with c1:
                if st.form_submit_button(t("common.save"), type="primary",
                                          width="stretch"):
                    qr.update(edit_id, title=new_title, body=new_body,
                              category=new_cat)
                    st.session_state.pop("_qr_edit_id", None)
                    toast(t("common.saved"), icon="✓")
                    st.rerun()
            with c2:
                if st.form_submit_button(t("common.cancel"), width="stretch"):
                    st.session_state.pop("_qr_edit_id", None)
                    st.rerun()


# ---- Create new ------------------------------------------------------
st.divider()
with st.expander(f"➕ {t('qr.add_new_title')}", expanded=False):
    cA, cB = st.columns(2)
    with cA:
        st.markdown(f"**{t('qr.add_manual')}**")
        with st.form("_qr_add"):
            n_title = st.text_input(t("qr.f_title"))
            n_cat = st.selectbox(
                t("qr.f_category"),
                options=list(CATEGORY_ICONS.keys())[1:],
                index=7,  # general
            )
            n_body = st.text_area(t("qr.f_body"), height=120,
                                   placeholder=t("qr.body_placeholder"))
            if st.form_submit_button(t("common.save"), type="primary"):
                if n_title.strip() and n_body.strip():
                    qr.add(title=n_title, body=n_body, category=n_cat)
                    toast(t("qr.added"), icon="✨")
                    st.rerun()

    with cB:
        st.markdown(f"**{t('qr.add_ai')}**")
        api_key = st.session_state.get("api_key", "")
        if not api_key:
            st.caption(t("qr.ai_need_key"))
        else:
            with st.form("_qr_ai_form"):
                question = st.text_area(
                    t("qr.ai_question"),
                    placeholder=t("qr.ai_placeholder"),
                    height=120,
                )
                if st.form_submit_button(t("qr.ai_generate"), type="primary"):
                    if question.strip():
                        with st.spinner(t("qr.ai_thinking")):
                            try:
                                gen = qr.ai_generate(question, api_key)
                            except Exception as e:
                                friendly_error(e)
                                gen = None
                        if gen and gen.get("body"):
                            qr.add(title=gen["title"], body=gen["body"],
                                   category=gen.get("category", "general"))
                            toast(t("qr.added"), icon="🤖")
                            st.rerun()
                        else:
                            st.error(t("qr.ai_failed"))
