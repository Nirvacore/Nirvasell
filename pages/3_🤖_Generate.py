"""Pick a task + a set of products → AI generates → save to DB."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import generate as gen
import tasks as task_registry
import onboarding
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import toast, friendly_error, empty_state, page_header
from i18n import t

db.init()
st.set_page_config(page_title="nirva · Generate", page_icon="🤖", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="🤖", title=t("generate.title"), subtitle=t("generate.caption"))
onboarding.tip("generate")

api_key = st.session_state.get("api_key", "")
if not api_key:
    st.warning(t("generate.api_warn"))
    st.stop()


# ----- Step 1: Pick task -----
st.subheader(t("generate.step1"))

task_keys = list(task_registry.ALL.keys())
task_labels = [t(f"task.{k}.label") for k in task_keys]
sel = st.radio(
    " ",
    options=range(len(task_keys)),
    format_func=lambda i: task_labels[i],
    horizontal=True,
    label_visibility="collapsed",
)
task_key = task_keys[sel]
task = task_registry.get(task_key)
st.caption(t(f"task.{task_key}.blurb"))

multi = task.TASK.get("multi_product", False)


# ----- Step 2: Pick products -----
st.subheader(t("generate.step2"))

all_label = t("catalog.all")
c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    q = st.text_input(t("catalog.search"), "")
with c2:
    brands = [all_label] + db.distinct_values("brand")
    brand = st.selectbox(t("upload.field.brand"), brands)
with c3:
    cats = [all_label] + db.distinct_values("category")
    cat = st.selectbox(t("upload.field.category"), cats)
with c4:
    only_missing = st.checkbox(
        t("generate.only_missing"),
        value=not multi,
        help=t("generate.only_missing_help"),
    )

df = db.fetch_products(
    brand=None if brand == all_label else brand,
    category=None if cat == all_label else cat,
    search=q or None,
    with_content_task=task_key,
    only_missing_task=only_missing,
)

if df.empty:
    empty_state(
        icon="🤖",
        title=t("generate.empty_title"),
        body=t("generate.empty_body"),
        cta_label=t("generate.empty_cta"),
        cta_target="pages/2_📦_Catalog.py",
    )
    st.stop()

sel_col = t("generate.col_select")
df = df.reset_index(drop=True)
df[sel_col] = False
display = df[[sel_col, "sku", "name", "brand", "cost_price", "sell_price"]].copy()

c_a, c_b = st.columns([1, 4])
with c_a:
    if st.button(t("generate.select_all"), width='stretch'):
        display[sel_col] = True
with c_b:
    st.caption(t("generate.n_in_list", n=len(df)))

edited = st.data_editor(
    display,
    width='stretch',
    hide_index=True,
    height=380,
    column_config={
        sel_col: st.column_config.CheckboxColumn(sel_col, width="small"),
        "sku": st.column_config.TextColumn(t("upload.field.sku").rstrip(" *"), width="small", disabled=True),
        "name": st.column_config.TextColumn(t("upload.field.name").rstrip(" *"), width="large", disabled=True),
        "brand": st.column_config.TextColumn(t("upload.field.brand"), width="small", disabled=True),
        "cost_price": st.column_config.NumberColumn(t("common.cost"), format="฿%d", width="small", disabled=True),
        "sell_price": st.column_config.NumberColumn(t("common.sell"), format="฿%d", width="small", disabled=True),
    },
    disabled=["sku", "name", "brand", "cost_price", "sell_price"],
)

picked_idx = edited.index[edited[sel_col]].tolist()
picked_rows = df.loc[picked_idx].to_dict("records")


# ----- Step 3: Run -----
st.subheader(t("generate.step3", n=len(picked_rows)))
c_run1, c_run2 = st.columns([3, 1])
with c_run2:
    workers = st.number_input(t("generate.parallel"), 1, 16, 8) if not multi else 1
with c_run1:
    run_btn = st.button(
        t("generate.run_btn", label=t(f"task.{task_key}.label")),
        type="primary",
        disabled=not picked_rows,
        width='stretch',
    )

if run_btn:
    if multi:
        with st.spinner(t("generate.running")):
            try:
                out = gen.run_multi_product(picked_rows, task, api_key=api_key)
                anchor_id = min(r["id"] for r in picked_rows)
                payload = {
                    **out,
                    "product_ids": [r["id"] for r in picked_rows],
                    "products_summary": ", ".join(
                        f"{r.get('name') or r.get('sku')}" for r in picked_rows
                    ),
                }
                db.save_content(anchor_id, task_key, payload)
                toast(t("generate.done"), icon="✨")
                st.json(out)
            except Exception as e:
                friendly_error(e, hint=t("generate.err_hint"))
    else:
        progress = st.progress(0, text=t("generate.running"))
        def on_progress(d: int, total: int):
            progress.progress(d / total, text=f"{d}/{total}")
        try:
            results = gen.run_per_product(
                picked_rows, task, api_key=api_key, workers=workers, on_progress=on_progress,
            )
            ok = 0
            for r in results:
                if "error" in r:
                    continue
                payload = {f: r.get(f, "") for f in task.TASK["output_fields"]}
                db.save_content(r["id"], task_key, payload)
                ok += 1
            if ok > 0:
                try:
                    import onboarding as _ob
                    _ob.mark_step("first_generate")
                except Exception:
                    pass
            toast(t("generate.ok_n_of_m", ok=ok, total=len(results)), icon="✨")
            errs = [r for r in results if "error" in r]
            if errs:
                with st.expander(t("generate.errs", n=len(errs))):
                    for r in errs[:20]:
                        st.write(f"**{r['sku']}** — {r['error']}")

            with st.expander(t("generate.preview3"), expanded=True):
                for r in results[:3]:
                    if "error" in r:
                        continue
                    st.markdown(f"**{r['sku']} — {(r.get('name') or '')[:60]}**")
                    for f in task.TASK["output_fields"]:
                        v = r.get(f, "")
                        if v:
                            if len(str(v)) < 100:
                                st.markdown(f"*{f}:* {v}")
                            else:
                                st.markdown(f"*{f}:*")
                                st.text(str(v)[:600])
                    st.divider()
        except Exception as e:
            friendly_error(e, hint=t("generate.err_hint"))
