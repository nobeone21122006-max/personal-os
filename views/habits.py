from datetime import date

import streamlit as st

from core import repo
from core.common import today
from core.theme import page_heading, section
from core.widgets import fmt_minutes, goal_choice_options

page_heading(
    "THÓI QUEN",
    "Thói quen hằng ngày",
    "Mỗi thói quen tự tạo một nhiệm vụ cho mỗi ngày kể từ ngày bắt đầu. "
    "Ngày nghỉ vẫn có nhiệm vụ nhưng là tùy chọn: làm hay không đều được và không kéo tiến độ xuống.",
)

options, labels = goal_choice_options()


def _goal_index(goal_id) -> int:
    return options.index(goal_id) if goal_id in options else 0


# ---------- Tạo thói quen mới ----------
with st.expander("➕ Thêm thói quen mới", expanded=not repo.list_habits()):
    with st.form("new_habit_form", clear_on_submit=True):
        title = st.text_input("Tên thói quen", placeholder="VD: Đọc 20 trang sách")
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            minutes = st.number_input("Thời lượng (phút)", min_value=5, max_value=1440, value=30, step=5)
        with col_b:
            start = st.date_input("Bắt đầu từ", value=today())
        with col_c:
            goal_id = st.selectbox("Gắn với mục tiêu (không bắt buộc)", options=options,
                                   format_func=lambda gid: "— Không gắn —" if gid is None else labels.get(gid, ""))
        submitted = st.form_submit_button("Tạo thói quen", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("Vui lòng nhập tên thói quen.")
        else:
            repo.create_habit(title, int(minutes), goal_id, start)
            st.toast("Đã tạo thói quen. Nhiệm vụ hôm nay đã xuất hiện ở Dashboard.")
            st.rerun()

# ---------- Danh sách thói quen ----------
habits = repo.list_habits()
section("Danh sách thói quen")
if not habits:
    st.info("Chưa có thói quen nào. Tạo thói quen đầu tiên ở phía trên.")

for habit in habits:
    done, total = repo.habit_stats(habit["id"])
    rate = (done / total) if total else 0.0
    status = "Đang bật" if habit["active"] else "Đã dừng"
    goal_title = next((g["title"] for g in repo.list_goals() if g["id"] == habit["goal_id"]), None)

    with st.container(border=True):
        head, stat = st.columns([3, 2], vertical_alignment="center")
        with head:
            st.markdown(f"**{habit['title']}**")
            extra = f" · ↳ {goal_title}" if goal_title else ""
            st.caption(f"{status} · {fmt_minutes(habit['duration_minutes'])} mỗi ngày · "
                       f"bắt đầu {date.fromisoformat(habit['start_date']).strftime('%d/%m/%Y')}{extra}")
        with stat:
            st.progress(rate, text=f"{done}/{total} lần · {rate:.0%}")

        with st.expander("Sửa · dừng · tiếp tục"):
            with st.form(f"edit_habit_{habit['id']}"):
                new_title = st.text_input("Tên thói quen", value=habit["title"], key=f"hb_title_{habit['id']}")
                col_a, col_b = st.columns(2)
                with col_a:
                    new_minutes = st.number_input("Thời lượng (phút)", min_value=5, max_value=1440,
                                                  value=min(1440, max(5, int(habit["duration_minutes"]))),
                                                  step=5, key=f"hb_min_{habit['id']}")
                with col_b:
                    new_goal = st.selectbox("Gắn với mục tiêu", options=options,
                                            index=_goal_index(habit["goal_id"]),
                                            format_func=lambda gid: "— Không gắn —" if gid is None else labels.get(gid, ""),
                                            key=f"hb_goal_{habit['id']}")
                st.caption("Thay đổi chỉ áp dụng cho các ngày từ hôm nay trở đi và nhiệm vụ chưa làm. "
                           "Lịch sử giữ nguyên.")
                save = st.form_submit_button("Lưu thay đổi", type="primary", use_container_width=True)
            if save:
                if not new_title.strip():
                    st.warning("Vui lòng nhập tên thói quen.")
                else:
                    repo.update_habit(habit["id"], new_title, int(new_minutes), new_goal)
                    st.toast("Đã cập nhật thói quen.")
                    st.rerun()

            if habit["active"]:
                if st.button("⏸️ Dừng thói quen", key=f"hb_stop_{habit['id']}", use_container_width=True):
                    repo.set_habit_active(habit["id"], False)
                    st.toast("Đã dừng. Lịch sử được giữ lại, các ngày sau không còn nhiệm vụ.")
                    st.rerun()
            else:
                if st.button("▶️ Tiếp tục thói quen", key=f"hb_resume_{habit['id']}", use_container_width=True):
                    repo.set_habit_active(habit["id"], True)
                    st.toast("Đã bật lại thói quen.")
                    st.rerun()
