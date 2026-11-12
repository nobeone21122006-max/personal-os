from datetime import date, timedelta

import streamlit as st

from core import repo
from core.common import today
from core.theme import page_heading, section
from core.widgets import render_week_planner

page_heading(
    "THÊM MỤC TIÊU",
    "Thêm mục tiêu mới",
    "Tạo mục tiêu ở một trong ba cấp: tầm nhìn năm, kế hoạch tháng hoặc ưu tiên tuần. Mỗi cấp nên gắn với cấp trên.",
)

LEVEL_OPTIONS = {
    "year": "🎯 Tầm nhìn năm",
    "month": "🗓️ Kế hoạch tháng",
    "week": "📅 Ưu tiên tuần",
}

level = st.radio(
    "Cấp mục tiêu",
    options=list(LEVEL_OPTIONS),
    format_func=LEVEL_OPTIONS.get,
    horizontal=True,
    key="add_goal_level",
)

st.markdown("<br>", unsafe_allow_html=True)
_, center, _ = st.columns([0.2, 3, 0.2])


def _first_day_next_month() -> date:
    first_this = today().replace(day=1)
    return (first_this + timedelta(days=32)).replace(day=1)


def _last_day(d: date) -> date:
    nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return nxt - timedelta(days=1)


with center:
    with st.container(border=True):
        section(LEVEL_OPTIONS[level], dot=True)

        # Cấp cha cần có trước khi tạo cấp con.
        parent_id = None
        plan_month = None
        if level == "month":
            parents = repo.list_goals("year")
            if not parents:
                st.warning("Hãy tạo ít nhất một tầm nhìn năm trước khi thêm kế hoạch tháng.")
                st.stop()
        elif level == "week":
            parents = repo.list_goals("month")
            if not parents:
                st.warning("Hãy tạo ít nhất một kế hoạch tháng trước khi thêm ưu tiên tuần.")
                st.stop()
        else:
            parents = []

        with st.form(f"add_goal_form_{level}", clear_on_submit=True):
            title = st.text_input(
                "Tên mục tiêu",
                placeholder={
                    "year": "VD: Đạt IELTS 6.5",
                    "month": "VD: Hoàn thành 8 chương sách tiếng Anh",
                    "week": "VD: Viết 3 bài luyện writing",
                }[level],
            )
            description = st.text_area("Mô tả / lý do (không bắt buộc)", height=90)

            if level in ("month", "week"):
                parent_labels = {p["id"]: p["title"] for p in parents}
                parent_id = st.selectbox(
                    "Thuộc tầm nhìn năm" if level == "month" else "Thuộc kế hoạch tháng",
                    options=list(parent_labels),
                    format_func=parent_labels.get,
                )

            if level == "month":
                chosen = st.date_input("Tháng thực hiện", value=_first_day_next_month(),
                                       help="Chọn bất kỳ ngày nào trong tháng cần lập kế hoạch.")
                plan_month = f"{chosen.year}-{chosen.month:02d}"
                deadline = _last_day(chosen)
            elif level == "week":
                deadline = st.date_input("Hạn hoàn thành", value=today() + timedelta(days=7))
            else:
                deadline = st.date_input("Hạn cuối của năm học", value=date(today().year + 1, 6, 30))

            if level == "week":
                estimate_hours = st.number_input(
                    "Tổng thời lượng dự kiến (giờ)", min_value=0.0, max_value=200.0, value=0.0, step=0.5,
                    help="Dùng để tự động chia nhiệm vụ cho các ngày. Có thể để 0 và nhập sau.",
                )
                target, unit = 100.0, "%"
            else:
                col_t, col_u = st.columns(2)
                with col_t:
                    target = st.number_input("Mục tiêu số (nếu đo được)", min_value=1.0, value=100.0, step=1.0)
                with col_u:
                    unit = st.text_input("Đơn vị", value="%", help="VD: %, cuốn sách, bài, giờ")
                estimate_hours = 0.0

            submitted = st.form_submit_button("Tạo mục tiêu", type="primary", use_container_width=True)

        if submitted:
            if not title.strip():
                st.warning("Vui lòng nhập tên mục tiêu.")
            else:
                new_id = repo.create_goal(
                    level=level,
                    title=title,
                    description=description,
                    parent_id=parent_id,
                    plan_month=plan_month,
                    deadline=deadline,
                    target_value=float(target),
                    unit=unit.strip() or "%",
                    estimated_minutes=int(round(estimate_hours * 60)),
                )
                st.toast(f"Đã tạo {LEVEL_OPTIONS[level].split(' ', 1)[1].lower()}.")
                st.success("Đã thêm mục tiêu. Bạn có thể xem ở mục “Mục tiêu 4 cấp” trên thanh bên.")
                if level == "week":
                    st.session_state["planner_goal_id"] = new_id

        # Sau khi tạo ưu tiên tuần: hỏi cách phân bổ nhiệm vụ.
        planner_id = st.session_state.get("planner_goal_id")
        if level == "week" and planner_id:
            planner_goal = repo.get_goal(planner_id)
            if planner_goal:
                st.markdown("<br>", unsafe_allow_html=True)
                render_week_planner(planner_goal, key_prefix=f"ag_{planner_id}")
                if st.button("Xong, để sau", use_container_width=True, key=f"ag_close_{planner_id}"):
                    st.session_state.pop("planner_goal_id", None)
                    st.rerun()
            else:
                st.session_state.pop("planner_goal_id", None)
