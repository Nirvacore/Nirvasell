"""Browse / filter / search saved products. Click any row → see detail."""
from __future__ import annotations
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import db
import tasks as task_registry
import onboarding
from _theme import apply as apply_theme
from _sidebar import render as render_sidebar
from _auth_gate import require_auth
from _components import split_images, image_grid, render_content_for_task, product_summary_row, empty_state, page_header
from i18n import t

db.init()
st.set_page_config(page_title="nirva · Catalog", page_icon="📦", layout="wide")
apply_theme()
require_auth()
render_sidebar()

page_header(icon="📦", title=t("catalog.title"), subtitle=t("catalog.caption"))
onboarding.tip("catalog")

s = db.stats()
if s["products"] == 0:
    empty_state(
        icon="📦",
        title=t("catalog.empty_title"),
        body=t("catalog.empty_body"),
        cta_label=t("catalog.empty_cta"),
        cta_target="app.py",
    )
    st.stop()


# ----- Filters -----
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
    task_opts = [("", all_label)] + [(k, t(f"task.{k}.label")) for k in task_registry.ALL]
    sel = st.selectbox(
        t("catalog.has_content_filter"),
        range(len(task_opts)),
        format_func=lambda i: task_opts[i][1],
        index=0,
    )

df = db.fetch_products(
    brand=None if brand == all_label else brand,
    category=None if cat == all_label else cat,
    search=q or None,
)

if df.empty:
    st.info(t("generate.empty_filter"))
    st.stop()

# Content-task icons per row.
with db.conn() as c:
    content_rows = c.execute(
        "SELECT product_id, task FROM content WHERE product_id IN ("
        + ",".join("?" * len(df))
        + ")",
        df["id"].tolist(),
    ).fetchall()
by_pid: dict[int, list[str]] = {}
for r in content_rows:
    by_pid.setdefault(r["product_id"], []).append(r["task"])

icons = {mod.TASK["key"]: mod.TASK["icon"] for mod in task_registry.ALL.values()}
df["content"] = df["id"].apply(
    lambda pid: " ".join(icons[k] for k in by_pid.get(pid, []))
)
df["thumb"] = df["image_url"].apply(lambda u: split_images(u)[0] if u else "")

st.markdown(
    f"<div style='color:#6b6b6b;font-size:0.85rem;margin:0.5rem 0'>"
    f"{t('catalog.found', n=len(df))}</div>",
    unsafe_allow_html=True,
)


# ----- Table with selection -----
sel_col = "✓"
display = df.copy()
display.insert(0, sel_col, False)

show_cols = [sel_col, "thumb", "sku", "name", "brand", "category",
             "cost_price", "sell_price", "stock", "content"]
show_cols = [c for c in show_cols if c in display.columns]

edited = st.data_editor(
    display[show_cols],
    width='stretch',
    hide_index=True,
    height=420,
    column_config={
        sel_col: st.column_config.CheckboxColumn(width="small"),
        "thumb": st.column_config.ImageColumn(t("common.images"), width="small"),
        "sku": st.column_config.TextColumn("SKU", width="small"),
        "name": st.column_config.TextColumn(t("upload.field.name").rstrip(" *"), width="large"),
        "brand": st.column_config.TextColumn(t("upload.field.brand"), width="small"),
        "category": st.column_config.TextColumn(t("upload.field.category"), width="small"),
        "cost_price": st.column_config.NumberColumn(t("common.cost"), format="฿%d", width="small"),
        "sell_price": st.column_config.NumberColumn(t("common.sell"), format="฿%d", width="small"),
        "stock": st.column_config.NumberColumn(t("upload.field.stock"), width="small"),
        "content": st.column_config.TextColumn(
            t("catalog.col_content"),
            help=t("catalog.col_content_help"),
            width="medium",
        ),
    },
    disabled=["thumb", "sku", "name", "brand", "category",
              "cost_price", "sell_price", "stock", "content"],
    key="catalog_editor",
)

picked_idx = edited.index[edited[sel_col]].tolist()
picked_count = len(picked_idx)


# ----- Bulk actions -----
if picked_count > 0:
    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button(
            f"{t('common.delete_selected')} ({picked_count})",
            width='stretch',
        ):
            ids_to_delete = df.iloc[picked_idx]["id"].tolist()
            with db.conn() as c:
                c.executemany(
                    "DELETE FROM products WHERE id = ?",
                    [(i,) for i in ids_to_delete],
                )
            st.success(t("common.deleted_n", n=len(ids_to_delete)))
            st.rerun()


# ----- Product detail (first selected row) -----
st.divider()
st.subheader(t("common.details"))

if picked_count == 0:
    st.caption(t("catalog.pick_to_view"))
else:
    chosen = df.iloc[picked_idx[0]].to_dict()
    product_summary_row(
        chosen,
        int(chosen.get("sell_price") or 0),
        float(chosen.get("cost_price") or 0),
    )

    tab_imgs, tab_specs, tab_content, tab_qr, tab_prep, tab_md = st.tabs([
        t("common.images"),
        t("upload.field.specs"),
        t("catalog.col_content"),
        t("common.qr_code"),
        t("common.prep_images"),
        t("common.markdown_export"),
    ])

    with tab_imgs:
        imgs = split_images(chosen.get("image_url"))
        if imgs:
            image_grid(imgs, cols=4)
        else:
            st.caption(t("common.no_images"))

        st.markdown("---")
        c_e1, c_e2 = st.columns([1, 4])
        with c_e1:
            enrich_btn = st.button(t("common.find_better_image"), width='stretch')
        with c_e2:
            st.caption(t("common.find_better_help"))

        if enrich_btn:
            import image_fetch as imf
            with st.spinner(t("common.searching")):
                supplier_first = imgs[0] if imgs else None
                result = imf.find_better_image(
                    chosen.get("brand"),
                    chosen.get("name"),
                    supplier_url=supplier_first,
                    force=True,
                )
            if result.get("url") and result.get("source") != "supplier":
                st.success(t("common.found_image", source=result["source"]))
                st.image(result["url"], caption=f"{result['source']} · score {result['score']:.1f}")
                if st.button(t("common.replace_image"), key="replace_img"):
                    # Prepend new URL to image_url list
                    new_url = result["url"]
                    existing = chosen.get("image_url") or ""
                    new_value = f"{new_url}|{existing}" if existing and new_url not in existing else (new_url or existing)
                    with db.conn() as c:
                        c.execute(
                            "UPDATE products SET image_url = ? WHERE id = ?",
                            (new_value, chosen["id"]),
                        )
                    st.success(t("common.image_replaced"))
                    st.rerun()
            else:
                st.info(t("common.no_better_image"))

    with tab_specs:
        specs = chosen.get("specs") or ""
        if specs:
            st.text(specs)
        else:
            st.caption("—")

    with tab_content:
        with db.conn() as c:
            rows = c.execute(
                "SELECT task, payload FROM content WHERE product_id = ?",
                (chosen["id"],),
            ).fetchall()
        if not rows:
            st.caption(t("history.empty"))
        else:
            for r in rows:
                payload = json.loads(r["payload"] or "{}")
                mod = task_registry.get(r["task"])
                label = t(f"task.{r['task']}.label")
                clean_label = label.replace(mod.TASK["icon"], "").strip()
                with st.expander(f"{mod.TASK['icon']} {clean_label}", expanded=False):
                    render_content_for_task(payload, mod)

    with tab_qr:
        import qrcode_util as qr
        sku = chosen.get("sku") or ""
        c1, c2 = st.columns([1, 2])
        with c1:
            target = st.selectbox(
                t("common.qr_target"),
                [
                    ("shopee", qr.shopee_search_url(sku)),
                    ("lazada", qr.lazada_search_url(sku)),
                    ("custom", ""),
                ],
                format_func=lambda x: x[0].title(),
            )
            url = target[1]
            if target[0] == "custom":
                url = st.text_input("URL", "")
        with c2:
            if url:
                png = qr.make_png(url, box_size=8)
                st.image(png, caption=url, width=240)
                st.download_button(
                    t("common.download"),
                    data=png,
                    file_name=f"{sku}_qr.png",
                    mime="image/png",
                )

    with tab_prep:
        import image_utils as imu
        from pathlib import Path
        imgs = split_images(chosen.get("image_url"))
        if not imgs:
            st.caption(t("common.no_images"))
        else:
            src = imgs[0]
            # Load source bytes
            try:
                if src.startswith("http"):
                    import httpx
                    raw = httpx.get(src, timeout=10).content
                else:
                    p = Path(src)
                    raw = p.read_bytes() if p.exists() else None
            except Exception as e:
                raw = None
                st.error(str(e))

            if raw:
                presets = list(imu.PLATFORM_SIZES.keys())
                selected = st.multiselect(
                    t("common.pick_platforms"),
                    presets,
                    default=["shopee_main", "lazada_main", "tiktok_main", "tiktok_video"],
                    format_func=lambda p: imu.PLATFORM_SIZES[p]["label"],
                )
                remove_bg = st.checkbox(t("common.remove_bg"), value=False, help=t("common.remove_bg_help"))

                if st.button(t("common.process"), type="primary"):
                    base = imu.remove_bg_then_white(raw) if remove_bg else raw
                    cols = st.columns(min(len(selected), 3) or 1)
                    for i, p in enumerate(selected):
                        with cols[i % len(cols)]:
                            try:
                                out = imu.resize_for(base, p)
                                cfg = imu.PLATFORM_SIZES[p]
                                st.image(out, caption=cfg["label"], width='stretch')
                                st.download_button(
                                    f"⬇ {cfg['label']}",
                                    data=out,
                                    file_name=f"{sku}_{p}.jpg",
                                    mime="image/jpeg",
                                    key=f"dl_img_{p}",
                                )
                            except Exception as e:
                                st.error(f"{p}: {e}")

    with tab_md:
        import export_utils as exu
        with db.conn() as c:
            content_rows = c.execute(
                "SELECT task, payload FROM content WHERE product_id = ?",
                (chosen["id"],),
            ).fetchall()
        if not content_rows:
            st.caption(t("history.empty"))
        else:
            contents = {r["task"]: json.loads(r["payload"] or "{}") for r in content_rows}
            md = exu.product_to_full_markdown(chosen, contents)
            st.code(md, language="markdown")
            st.download_button(
                t("common.download") + " .md",
                data=md.encode("utf-8"),
                file_name=f"{sku}.md",
                mime="text/markdown",
            )


# ---- v59: Smart Restock Predictions ------------------------------------

st.divider()
st.markdown(f"### 📊 {t('restock.title')}")
st.caption(t("restock.caption"))

try:
    import smart_restock as sr
    predictions = sr.all_predictions()
    active = [p for p in predictions if p["status"] != "no_sales"]
    if not active:
        st.info(t("restock.all_ok"))
    else:
        for p in active[:15]:
            days = int(p["days_until_out"])
            if p["status"] == "critical":
                color = "#c54c4c"
                badge = "🔴 " + t("restock.critical")
            elif p["status"] == "warning":
                color = "#c5963d"
                badge = "🟡"
            elif p["status"] == "watch":
                color = "#4d6c5c"
                badge = "🟢"
            else:
                color = "#7a7569"
                badge = "✓"

            name_str = (p.get("name") or "")[:40]
            daily_str = str(p["daily_sales"])
            reorder_str = str(p.get("reorder_qty", 0))
            days_str = t("restock.days_out", n=days)

            st.markdown(
                "<div style='display:flex;justify-content:space-between;align-items:center;"
                "padding:8px 14px;border-bottom:0.5px solid rgba(40,30,20,0.05)'>"
                "<div><strong>" + p["sku"] + "</strong>"
                " <span style='color:#7a7569;font-size:12px'>" + name_str + "</span></div>"
                "<div style='display:flex;gap:18px;align-items:center;font-size:13px'>"
                "<span>" + t("restock.daily_sales") + ": " + daily_str + "</span>"
                "<span style='color:" + color + ";font-weight:600'>" + badge + " " + days_str + "</span>"
                "<span style='background:rgba(77,108,92,0.08);padding:2px 8px;"
                "border-radius:6px;font-size:12px'>" + t("restock.reorder") + ": " + reorder_str + "</span>"
                "</div></div>",
                unsafe_allow_html=True,
            )
except Exception:
    pass
