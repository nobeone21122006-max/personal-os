"""Thành phần giao diện dùng chung giữa nhiều trang."""
from datetime import date
from html import escape

import streamlit as st

from core import repo
from core.common import WEEKDAYS, today

INTEREST_OPTIONS = [
    "Đọc sách", "Thể thao / Chạy bộ", "Âm nhạc", "Nấu ăn", "Du lịch",
    "Công nghệ", "Nghệ thuật / Thiết kế", "Viết lách", "Thiền / Yoga", "Chơi game",
]

HEALTH_OPTIONS = {
    "healthy": "Khỏe mạnh, không có vấn đề đáng lo",
    "low_activity": "Ít vận động, thường xuyên mệt mỏi",
    "chronic": "Có bệnh mạn tính đang theo dõi",
    "recovering": "Đang hồi phục sau bệnh hoặc chấn thương",
    "prefer_not_say": "Tôi không muốn chia sẻ",
}

LEVEL_SHORT = {"year": "Năm", "month": "Tháng", "week": "Tuần"}


def fmt_minutes(minutes: int) -> str:
    minutes = int(minutes or 0)
    if minutes >= 60:
        hours, rest = divmod(minutes, 60)
        return f"{hours}h {rest:02d}p" if rest else f"{hours} giờ"
    return f"{minutes} phút"


# ============================ HỒ SƠ CÁ NHÂN ============================

def profile_fields(key_prefix: str, defaults: dict | None = None) -> dict:
    """Vẽ các ô nhập thông tin cá nhân. Trả về dict giá trị hiện tại.

    key_prefix giúp widget không bị lẫn khi dùng nhiều lần (ví dụ theo từng năm học).
    """
    defaults = defaults or {}
    default_interests = list(defaults.get("interests") or [])
    options = INTEREST_OPTIONS + [i for i in default_interests if i not in INTEREST_OPTIONS]

    major = st.text_input("Ngành học", value=defaults.get("major", "") or "",
                          placeholder="VD: Công nghệ thông tin",
                          key=f"{key_prefix}_major")

    health_codes = list(HEALTH_OPTIONS)
    current_health = defaults.get("health_status")
    health_status = st.selectbox(
        "Tình trạng sức khỏe",
        options=health_codes,
        index=health_codes.index(current_health) if current_health in health_codes else None,
        format_func=lambda code: HEALTH_OPTIONS[code],
        placeholder="Chọn một mức phù hợp",
        key=f"{key_prefix}_health",
    )
    health_note = st.text_input("Ghi chú sức khỏe (không bắt buộc)",
                                value=defaults.get("health_note", "") or "",
                                key=f"{key_prefix}_health_note")

    dream = st.text_area("Ước mơ / mục tiêu lớn", value=defaults.get("dream", "") or "",
                         placeholder="VD: Trở thành kỹ sư AI và xây dựng sản phẩm riêng",
                         height=90, key=f"{key_prefix}_dream")

    interests = st.multiselect("Sở thích", options=options, default=default_interests,
                               placeholder="Chọn một hoặc nhiều sở thích",
                               key=f"{key_prefix}_interests")
    other = st.text_input("Sở thích khác (cách nhau bằng dấu phẩy)", key=f"{key_prefix}_interest_other")
    if other.strip():
        interests = list(interests) + [part.strip() for part in other.split(",") if part.strip()]

    gpa_value = float(defaults.get("gpa") or 0.0)
    gpa = st.number_input("GPA tích lũy (thang 4.0, nhập 0 nếu chưa có)",
                          min_value=0.0, max_value=4.0, value=gpa_value, step=0.01, format="%.2f",
                          key=f"{key_prefix}_gpa")

    return {
        "major": major,
        "health_status": health_status,
        "health_note": health_note,
        "dream": dream,
        "interests": list(dict.fromkeys(interests)),
        "gpa": float(gpa) if gpa and gpa > 0 else None,
    }


def render_personal_info(profile: dict | None) -> None:
    if not profile:
        st.info("Chưa có thông tin cho năm học này.")
        return
    health = HEALTH_OPTIONS.get(profile.get("health_status") or "", "Chưa cập nhật")
    health_note = (profile.get("health_note") or "").strip()
    health_html = escape(health) + (
        f'<div class="muted-small">{escape(health_note)}</div>' if health_note else ""
    )
    chips = "".join(f'<span class="interest-chip">{escape(i)}</span>' for i in profile.get("interests", [])) \
        or '<span class="muted-small">Chưa chọn sở thích</span>'
    gpa = profile.get("gpa")
    gpa_text = f"{gpa:.2f} / 4.0" if gpa else "Chưa cập nhật"
    major = escape(profile.get("major") or "Chưa cập nhật")
    dream = escape(profile.get("dream") or "Chưa cập nhật")

    st.markdown(
        f'<div class="profile-grid">'
        f'<div class="profile-item"><div class="profile-label">Ngành học</div><div class="profile-value">{major}</div></div>'
        f'<div class="profile-item"><div class="profile-label">Sức khỏe</div><div class="profile-value">{health_html}</div></div>'
        f'<div class="profile-item profile-wide"><div class="profile-label">Ước mơ · Mục tiêu lớn</div>'
        f'<div class="profile-value">{dream}</div></div>'
        f'<div class="profile-item"><div class="profile-label">Sở thích</div><div class="interest-row">{chips}</div></div>'
        f'<div class="profile-item"><div class="profile-label">GPA tích lũy</div><div class="profile-value">{gpa_text}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ============================ NHIỆM VỤ ============================

def _toggle_task(task_id: int, key: str) -> None:
    repo.set_task_done(task_id, bool(st.session_state.get(key)))


def day_label(d: date) -> str:
    return f"{WEEKDAYS[d.weekday()]}, ngày {d.day:02d}/{d.month:02d}/{d.year}"


def today_label() -> str:
    return day_label(today())


def countable_tasks(tasks: list[dict]) -> list[dict]:
    """Bỏ nhiệm vụ tùy chọn (thói quen ngày nghỉ) chưa làm: không tính vào tiến độ."""
    return [t for t in tasks if not (t.get("optional") and not t["done"])]


def day_task_summary(tasks: list[dict]) -> dict:
    counted = countable_tasks(tasks)
    total = len(counted)
    done = sum(1 for t in counted if t["done"])
    remaining_minutes = sum(int(t["duration_minutes"]) for t in counted if not t["done"])
    planned_minutes = sum(int(t["duration_minutes"]) for t in counted)
    return {
        "total": total,
        "done": done,
        "rate": (done / total) if total else 0.0,
        "remaining_minutes": remaining_minutes,
        "planned_minutes": planned_minutes,
    }


def task_board_header(tasks: list[dict], title: str = "Việc cần làm") -> None:
    """Thanh tóm tắt nổi bật đầu bảng nhiệm vụ."""
    summary = day_task_summary(tasks)
    if not summary["total"]:
        return
    pending = summary["total"] - summary["done"]
    width = max(0.0, min(1.0, summary["rate"])) * 100
    st.markdown(
        f'<div class="task-board-head">'
        f'<div class="task-board-title">{escape(title)} · {summary["done"]}/{summary["total"]} đã xong</div>'
        f'<div class="task-board-sub">Còn {pending} việc · khoảng {fmt_minutes(summary["remaining_minutes"])} nữa · '
        f'{summary["rate"]:.0%} hoàn thành</div>'
        f'<div class="task-bar"><div class="task-bar-fill" style="width:{width:.1f}%"></div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def _goal_index(options: list, goal_id) -> int:
    return options.index(goal_id) if goal_id in options else 0


@st.dialog("✏️ Chỉnh sửa nhiệm vụ")
def edit_task_dialog(task_id: int) -> None:
    """Sửa chi tiết từng phần của một nhiệm vụ: tên, thời lượng, mục tiêu, ngày."""
    task = repo.get_task(task_id)
    if not task:
        st.info("Nhiệm vụ này không còn tồn tại.")
        return

    is_habit = task.get("habit_id") is not None
    options, labels = goal_choice_options()
    with st.form(f"edit_task_form_{task_id}"):
        title = st.text_input("Tên nhiệm vụ", value=task["title"], key=f"edit_title_{task_id}")
        col_a, col_b = st.columns(2)
        with col_a:
            minutes = st.number_input(
                "Thời lượng (phút)", min_value=5, max_value=1440, step=5,
                value=min(1440, max(5, int(task["duration_minutes"]))), key=f"edit_minutes_{task_id}",
            )
        with col_b:
            if is_habit:
                st.caption("🔁 Thói quen: không đổi ngày. Để đổi ngày, hãy dừng và tạo lại thói quen.")
                task_date = None
            else:
                task_date = st.date_input("Ngày thực hiện", value=date.fromisoformat(task["task_date"]),
                                          key=f"edit_date_{task_id}")
        goal_id = st.selectbox(
            "Gắn với mục tiêu",
            options=options,
            index=_goal_index(options, task.get("goal_id")),
            format_func=lambda gid: "— Không gắn —" if gid is None else labels.get(gid, ""),
            key=f"edit_goal_{task_id}",
        )
        submitted = st.form_submit_button("Lưu thay đổi", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("Vui lòng nhập tên nhiệm vụ.")
        else:
            repo.update_task(task_id, title, int(minutes), goal_id, task_date)
            st.rerun()


def render_task_checklist(tasks: list[dict], key_prefix: str, title: str = "Việc cần làm") -> None:
    """Bảng nhiệm vụ: tích để hoàn thành, ✏️ để sửa chi tiết, thời lượng nổi bật."""
    if not tasks:
        with st.container(border=True):
            st.info("Chưa có nhiệm vụ nào. Thêm nhiệm vụ mới ở phía trên.")
        return

    task_board_header(tasks, title)

    for task in tasks:
        key = f"{key_prefix}_task_{task['id']}"
        label = f"~~{task['title']}~~" if task["done"] else task["title"]
        if task["done"]:
            chip = '<span class="task-chip task-chip-done">✓ Đã xong</span>'
        elif task.get("optional"):
            chip = '<span class="task-chip task-chip-optional">◌ Tùy chọn</span>'
        else:
            chip = '<span class="task-chip task-chip-todo">◷ Đang chờ</span>'

        meta = []
        if task.get("habit_id") is not None:
            meta.append("🔁 Thói quen")
        if task.get("goal_title"):
            meta.append(f"↳ {task['goal_title']}")

        with st.container(border=True):
            col_check, col_time, col_edit = st.columns([6.6, 2.4, 0.7], vertical_alignment="center")
            with col_check:
                st.checkbox(
                    label,
                    value=bool(task["done"]),
                    key=key,
                    on_change=_toggle_task,
                    args=(task["id"], key),
                )
                if meta:
                    st.markdown(f'<div class="task-goal">{escape(" · ".join(meta))}</div>', unsafe_allow_html=True)
            with col_time:
                st.markdown(
                    f'<div style="text-align:right">{chip}<br>'
                    f'<span class="task-duration">⏱ {fmt_minutes(task["duration_minutes"])}</span></div>',
                    unsafe_allow_html=True,
                )
            with col_edit:
                if st.button("✏️", key=f"{key}_edit", help="Sửa nhiệm vụ"):
                    edit_task_dialog(task["id"])


def goal_choice_options() -> tuple[list, dict]:
    """Danh sách mục tiêu có thể gắn vào nhiệm vụ (kế hoạch tháng và ưu tiên tuần)."""
    goals = repo.list_goals("month") + repo.list_goals("week")
    labels = {g["id"]: f"[{LEVEL_SHORT[g['level']]}] {g['title']}" for g in goals}
    return [None] + [g["id"] for g in goals], labels


def add_task_form(default_date: date, key: str, default_title: str = "",
                  default_goal_id: int | None = None) -> bool:
    """Form tạo nhiệm vụ cho một ngày bất kỳ. Trả về True khi đã thêm."""
    options, labels = goal_choice_options()
    default_index = _goal_index(options, default_goal_id)
    with st.form(f"add_task_{key}", clear_on_submit=True):
        title = st.text_input("Nhiệm vụ", value=default_title, placeholder="VD: Đọc 20 trang sách",
                              key=f"{key}_title")
        col_d, col_a, col_b = st.columns([1.3, 1, 2])
        with col_d:
            task_date = st.date_input("Ngày thực hiện", value=default_date, key=f"{key}_date")
        with col_a:
            minutes = st.number_input("Thời lượng (phút)", min_value=5, max_value=1440,
                                      value=30, step=5, key=f"{key}_minutes")
        with col_b:
            goal_id = st.selectbox("Gắn với mục tiêu (không bắt buộc)", options=options,
                                   index=default_index,
                                   format_func=lambda gid: "— Không gắn —" if gid is None else labels.get(gid, ""),
                                   key=f"{key}_goal")
        submitted = st.form_submit_button("Thêm nhiệm vụ", type="primary", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("Vui lòng nhập tên nhiệm vụ.")
            return False
        repo.add_task(title, task_date, int(minutes), goal_id)
        st.toast("Đã thêm nhiệm vụ.")
        return True
    return False


def render_week_planner(goal: dict, key_prefix: str) -> None:
    """Hỏi người dùng muốn tự động chia hay tạo thủ công nhiệm vụ cho một ưu tiên tuần."""
    with st.container(border=True):
        st.markdown(f"**🗂️ Lập lịch · {goal['title']}**")
        deadline = goal.get("deadline") or "chưa đặt hạn"
        st.caption(f"Hạn: {deadline}. Chọn cách phân bổ nhiệm vụ cho ưu tiên này.")

        mode = st.radio(
            "Bạn muốn phân bổ thế nào?",
            options=["auto", "manual"],
            format_func={"auto": "🤖 Tự động chia đều theo ngày", "manual": "✋ Tự tạo thủ công"}.get,
            horizontal=True,
            key=f"{key_prefix}_mode",
        )

        if mode == "auto":
            hours = st.number_input(
                "Tổng thời lượng dự kiến (giờ)", min_value=0.5, max_value=200.0,
                value=max(0.5, round((goal.get("estimated_minutes") or 0) / 60, 1) or 2.0),
                step=0.5, key=f"{key_prefix}_hours",
                help="Thời lượng sẽ được chia đều cho các ngày làm việc từ hôm nay đến hạn.",
            )
            total_minutes = int(round(hours * 60))
            plan = repo.build_week_plan(goal, total_minutes)
            if not plan:
                st.warning("Không có ngày nào để lập lịch. Hãy đặt hạn cho ưu tiên này (hạn phải từ hôm nay trở đi).")
            else:
                rows = [
                    {"Ngày": f"{WEEKDAYS[d.weekday()]}, {d.day:02d}/{d.month:02d}", "Thời lượng": fmt_minutes(m)}
                    for d, m in plan
                ]
                st.dataframe(rows, hide_index=True, use_container_width=True)
                free = repo.get_free_hours() * 60
                if any(m > free for _, m in plan):
                    st.warning(f"Có ngày vượt quá giờ rảnh của bạn ({fmt_minutes(int(free))}). "
                               "Cân nhắc tăng hạn hoặc giảm tổng thời lượng.")
                if st.button("Chia đều và tạo nhiệm vụ", type="primary", use_container_width=True,
                             key=f"{key_prefix}_auto_go"):
                    try:
                        created = repo.plan_week_auto(goal["id"], total_minutes)
                        st.success(f"Đã tạo {created} nhiệm vụ cho ưu tiên này.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
        else:
            add_task_form(today(), key=f"{key_prefix}_manual",
                          default_title=goal["title"], default_goal_id=goal["id"])
            existing = repo.tasks_for_goal(goal["id"])
            if existing:
                st.markdown("**Nhiệm vụ đã lập cho ưu tiên này**")
                st.caption(" · ".join(
                    f"{date.fromisoformat(t['task_date']).strftime('%d/%m')} {t['title']} ({fmt_minutes(t['duration_minutes'])})"
                    for t in existing
                ))




# ============================ SỬA MỤC TIÊU ĐẦY ĐỦ ============================

STATUS_OPTIONS = ["active", "completed", "paused"]
STATUS_LABELS = {"active": "Đang thực hiện", "completed": "Hoàn thành", "paused": "Tạm dừng"}
LEVEL_NAMES = {"year": "Tầm nhìn năm", "month": "Kế hoạch tháng", "week": "Ưu tiên tuần"}


@st.dialog("✏️ Sửa mục tiêu")
def edit_goal_dialog(goal_id: int) -> None:
    """Sửa đầy đủ một mục tiêu: tên, mô tả, hạn, tháng, cấp cha, mục tiêu số, thời lượng, trạng thái."""
    goal = repo.get_goal(goal_id)
    if not goal:
        st.info("Mục tiêu này không còn tồn tại.")
        return
    level = goal["level"]
    st.caption(f"Cấp: {LEVEL_NAMES[level]}. Đổi cấp không được hỗ trợ; nhiệm vụ đã gắn vẫn được giữ nguyên.")

    parent_id = None
    plan_month = None
    estimated_hours = 0.0
    with st.form(f"edit_goal_form_{goal_id}"):
        title = st.text_input("Tên mục tiêu", value=goal["title"], key=f"eg_title_{goal_id}")
        description = st.text_area("Mô tả / lý do", value=goal.get("description") or "", height=90,
                                   key=f"eg_desc_{goal_id}")

        if level == "month":
            current_month = (date.fromisoformat(goal["plan_month"] + "-01") if goal.get("plan_month")
                             else today().replace(day=1))
            picked = st.date_input("Tháng thực hiện", value=current_month, key=f"eg_month_{goal_id}")
            plan_month = f"{picked.year}-{picked.month:02d}"
            candidates = repo.list_goals("year")
        elif level == "week":
            candidates = repo.list_goals("month")
        else:
            candidates = []

        if candidates:
            labels = {g["id"]: g["title"] + (f" ({g['plan_month']})" if g.get("plan_month") else "")
                      for g in candidates}
            ids = [g["id"] for g in candidates]
            current = goal.get("parent_id")
            parent_id = st.selectbox(
                "Thuộc tầm nhìn năm" if level == "month" else "Thuộc kế hoạch tháng",
                options=ids,
                index=ids.index(current) if current in ids else 0,
                format_func=lambda gid: labels.get(gid, ""),
                key=f"eg_parent_{goal_id}",
            )

        deadline_value = date.fromisoformat(goal["deadline"]) if goal.get("deadline") else today()
        deadline = st.date_input("Hạn", value=deadline_value, key=f"eg_deadline_{goal_id}")

        if level == "week":
            estimated_hours = st.number_input(
                "Tổng thời lượng dự kiến (giờ)", min_value=0.0, max_value=200.0, step=0.5,
                value=float(round((goal.get("estimated_minutes") or 0) / 60, 1)), key=f"eg_hours_{goal_id}",
                help="Dùng khi lập lịch tự động. Đổi số này không tự tạo lại nhiệm vụ đã có.",
            )
            target, unit = float(goal.get("target_value") or 100), goal.get("unit") or "%"
        else:
            col_t, col_u = st.columns(2)
            with col_t:
                target = st.number_input("Mục tiêu số", min_value=1.0,
                                         value=float(goal.get("target_value") or 100), step=1.0,
                                         key=f"eg_target_{goal_id}")
            with col_u:
                unit = st.text_input("Đơn vị", value=goal.get("unit") or "%", key=f"eg_unit_{goal_id}")

        col_s, col_c = st.columns(2)
        with col_s:
            status_index = STATUS_OPTIONS.index(goal["status"]) if goal["status"] in STATUS_OPTIONS else 0
            status = st.selectbox("Trạng thái", options=STATUS_OPTIONS, index=status_index,
                                  format_func=STATUS_LABELS.get, key=f"eg_status_{goal_id}")
        with col_c:
            current_value = st.number_input("Tiến độ nhập tay", min_value=0.0,
                                            value=float(goal.get("current_value") or 0.0), step=1.0,
                                            key=f"eg_current_{goal_id}",
                                            help="Chỉ dùng khi mục tiêu chưa có nhiệm vụ.")
        submitted = st.form_submit_button("Lưu thay đổi", type="primary", use_container_width=True)

    if submitted:
        try:
            repo.update_goal_details(
                goal_id,
                title=title,
                description=description,
                deadline=deadline,
                plan_month=plan_month,
                parent_id=parent_id,
                target_value=float(target),
                unit=unit,
                estimated_minutes=int(round(estimated_hours * 60)),
                status=status,
                current_value=float(current_value),
            )
        except ValueError as exc:
            st.error(str(exc))
        else:
            st.rerun()
