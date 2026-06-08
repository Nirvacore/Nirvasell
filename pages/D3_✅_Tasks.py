"""D3 Team Tasks — assign and track to-dos."""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import team_tasks as tt
from theme import apply_theme
from auth import require_auth
from i18n import t
from sidebar import render_sidebar

apply_theme()
require_auth()
tt.init()
render_sidebar()

st.title(t("task.title"))
st.caption(t("task.caption"))

stats = tt.stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric(t("task.kpi_open"), stats["total_open"])
c2.metric(t("task.kpi_urgent"), stats["urgent"])
c3.metric(t("task.kpi_overdue"), stats["overdue"])
c4.metric(t("task.kpi_done_today"), stats["done_today"])

st.divider()

tab_board, tab_add, tab_team = st.tabs([
    t("task.tab_board"), t("task.tab_add"), t("task.tab_team")
])

with tab_board:
    status_sel = st.selectbox(
        t("task.status_filter"),
        ["open"] + list(tt.STATUSES.keys()),
        format_func=lambda s: t("task.all_open") if s == "open" else
                              tt.STATUSES[s]["label"],
    )
    member_sel = st.selectbox(
        t("task.member_filter"),
        [0] + [m["id"] for m in tt.all_members()],
        format_func=lambda i: t("task.all_members") if i == 0 else
                              next((m["name"] for m in tt.all_members() if m["id"] == i), ""),
    )
    status_q = None if status_sel == "open" else status_sel
    tasks = tt.all_tasks(
        status=status_q,
        assignee_id=member_sel if member_sel else None,
    )
    if status_sel == "open":
        tasks = [t_ for t_ in tasks if t_["status"] not in ("done", "cancelled")]

    if not tasks:
        st.info(t("task.no_tasks"))
    else:
        for tk in tasks:
            pi = tk["priority_info"]
            si = tk["status_info"]
            label = pi["icon"] + " " + si["icon"] + " " + tk["title"]
            if tk.get("assignee_name"):
                label += " · " + tk["assignee_name"]
            if tk.get("due_date"):
                label += " · " + tk["due_date"]
            with st.expander(label):
                if tk.get("description"):
                    st.write(tk["description"])
                st.write(t("task.category") + ": " + tk.get("category",""))
                col_s, col_d, col_x = st.columns(3)
                if col_s.button(t("task.mark_done"), key="td_" + str(tk["id"])):
                    tt.update_status(tk["id"], "done")
                    st.rerun()
                if col_d.button(t("task.mark_progress"), key="tp_" + str(tk["id"])):
                    tt.update_status(tk["id"], "in_progress")
                    st.rerun()
                if col_x.button(t("task.delete"), key="tdel_" + str(tk["id"])):
                    tt.delete(tk["id"])
                    st.rerun()

with tab_add:
    st.subheader(t("task.add_title"))
    members = tt.all_members()
    with st.form("add_task_form"):
        title = st.text_input(t("task.f_title"))
        desc  = st.text_area(t("task.f_desc"), height=80)
        col1, col2 = st.columns(2)
        category = col1.selectbox(t("task.f_category"), tt.CATEGORIES)
        priority = col2.selectbox(t("task.f_priority"),
                                   list(tt.PRIORITIES.keys()),
                                   format_func=lambda k: tt.PRIORITIES[k]["label"])
        col3, col4 = st.columns(2)
        member_ids = [0] + [m["id"] for m in members]
        assignee = col3.selectbox(
            t("task.f_assignee"), member_ids,
            format_func=lambda i: t("task.unassigned") if i == 0 else
                                  next((m["name"] for m in members if m["id"] == i), ""),
        )
        due_date = col4.text_input(t("task.f_due"), placeholder="YYYY-MM-DD")
        if st.form_submit_button(t("task.add_btn")):
            if title:
                tt.add_task(title, desc, category, priority,
                            assignee if assignee else None, due_date)
                st.success(t("task.added"))
                st.rerun()

with tab_team:
    st.subheader(t("task.team_title"))
    with st.form("add_member_form"):
        m_name = st.text_input(t("task.f_member_name"))
        m_role = st.text_input(t("task.f_member_role"))
        if st.form_submit_button(t("task.add_member_btn")):
            if m_name:
                tt.add_member(m_name, m_role)
                st.success(t("task.member_added"))
                st.rerun()
    members = tt.all_members()
    if members:
        for m in members:
            open_count = len(tt.all_tasks(assignee_id=m["id"]))
            open_filtered = [t_ for t_ in tt.all_tasks(assignee_id=m["id"])
                             if t_["status"] not in ("done","cancelled")]
            st.write("**" + m["name"] + "**" +
                     (" · " + m["role"] if m["role"] else "") +
                     " — " + str(len(open_filtered)) + t("task.open_tasks"))
