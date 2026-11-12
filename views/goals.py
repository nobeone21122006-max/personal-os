
import streamlit as st

from core import repo
from core.common import today
from core.theme import page_heading, section
from core.widgets import LEVEL_SHORT, edit_goal_dialog, render_week_planner

page_heading(
    "GOAL ARCHITECTURE",
    "Mục tiêu 4 cấp",
    "Tổng quan tiến độ theo từng cấp, và trạng thái hoàn thành từng ngày trong tháng.",
)

years = repo.list_goals("year")
months = repo.list_goals("month")
weeks = repo.list_goals("week")


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# ---------- Tổng quan tiến độ (4 cấp, gọn) ----------
avg_year = _avg([repo.goal_progress(g) for g in years])
avg_month = _avg([repo.goal_progress(g) for g in months])
avg_week = _avg([repo.goal_progress(g) for g in weeks])
day_tasks_today = repo.tasks_on(today())
countable = [t for t in day_tasks_today if not (t.get("optional") and not t["done"])]
day_done = sum(1 for t in countable if t["done"])
day_rate = (day_done / len(countable)) if countable else 0.0

section("Tiến độ theo cấp")
levels = st.columns(4, gap="medium")
level_cards = [
    ("01 · TẦM NHÌN NĂM", avg_year, f"{len(years)} mục tiêu", "#6550cb"),
    ("02 · KẾ HOẠCH THÁNG", avg_month, f"{len(months)} kế hoạch", "#3869ba"),
    ("03 · ƯU TIÊN TUẦN", avg_week, f"{len(weeks)} đầu việc", "#16866a"),
    ("04 · HÀNH ĐỘNG NGÀY", day_rate, f"{day_done}/{len(countable)} hoàn thành", "#b77b22"),
]
for col, (label, value, sub, color) in zip(levels, level_cards):
    width = max(0, min(100, value * 100))
    with col:
        st.markdown(
            f'<div class="goal-level"><div class="goal-level-kicker">{label}</div>'
            f'<div class="goal-level-value">{value:.0%}</div>'
            f'<div style="color:{color};font-size:.76rem;font-weight:700">{sub}</div>'
            f'<div style="height:5px;background:#eff0f5;border-radius:99px;margin-top:.75rem;overflow:hidden">'
            f'<div style="height:5px;width:{width:.1f}%;background:{color};border-radius:99px"></div></div></div>',
            unsafe_allow_html=True,
        )

# ============================ TRẠNG THÁI THEO THÁNG ============================

def _day_colors(rate: float) -> tuple[str, str]:
    if rate <= 0:
        return "#eef0f5", "#626a80"
    if rate <= 40:
        return "#fbe9e8", "#a34e54"
    if rate <= 70:
        return "#fff2d7", "#94651d"
    if rate < 100:
        return "#e7efff", "#3d64aa"
    return "#dff5eb", "#167456"


def _month_key(year: int, month: int) -> str:
    return f"{year}-{month:02d}"


def _month_options() -> list[str]:
    """Từ 12 tháng trước đến 3 tháng sau, cộng thêm các tháng đã có kế hoạch."""
    t = today()
    keys = []
    for offset in range(-12, 4):
        total = t.year * 12 + (t.month - 1) + offset
        keys.append(_month_key(total // 12, total % 12 + 1))
    keys += [m["plan_month"] for m in months if m.get("plan_month")]
    return sorted(set(keys), reverse=True)


section("Trạng thái trong tháng")
st.caption("Mỗi ô là một ngày. Màu thể hiện tỷ lệ nhiệm vụ đã hoàn thành trong ngày đó.")

month_opts = _month_options()
current_key = _month_key(today().year, today().month)
if st.session_state.get("status_month") not in month_opts:
    st.session_state["status_month"] = current_key if current_key in month_opts else month_opts[0]

col_m, col_p = st.columns([1, 2], vertical_alignment="bottom")
with col_m:
    month_key = st.selectbox(
        "Tháng",
        options=month_opts,
        format_func=lambda k: f"Tháng {k[5:]}/{k[:4]}",
        key="status_month",
    )
year, month = (int(part) for part in month_key.split("-"))

plans_this_month = [m for m in months if m.get("plan_month") == month_key]
plan_ids = [None] + [p["id"] for p in plans_this_month]
plan_labels = {p["id"]: f"{p['title']}" for p in plans_this_month}
if st.session_state.get("status_plan") not in plan_ids:
    st.session_state.pop("status_plan", None)  # kế hoạch đã chọn thuộc tháng khác: đặt lại
with col_p:
    if plan_ids[1:]:
        plan_id = st.selectbox(
            "Kế hoạch",
            options=plan_ids,
            format_func=lambda pid: "Tất cả kế hoạch trong tháng" if pid is None else plan_labels.get(pid, ""),
            key="status_plan",
        )
    else:
        plan_id = None
        st.caption("Tháng này chưa có kế hoạch tháng riêng. Đang hiển thị toàn bộ nhiệm vụ trong tháng.")

tracker = repo.month_overview(year, month, plan_id)

m1, m2, m3, m4 = st.columns(4, gap="medium")
m1.metric("Hoàn thành trung bình", f"{tracker['monthly_average']:.1f}%")
m2.metric("Ngày đạt 100%", f"{tracker['perfect_days']} ngày")
m3.metric("Ngày có nhiệm vụ", f"{tracker['active_days']}/{len(tracker['days'])}")
m4.metric("Nhiệm vụ đã xong", f"{tracker['done']}/{tracker['total']}")

legend_items = [
    ("#eef0f5", "0% · Chưa làm"),
    ("#fbe9e8", "1–40% · Khởi động"),
    ("#fff2d7", "41–70% · Đang tiến bộ"),
    ("#e7efff", "71–99% · Gần hoàn tất"),
    ("#dff5eb", "100% · Hoàn thành"),
]
legend = st.columns(5)
for col, (color, label) in zip(legend, legend_items):
    with col:
        st.markdown(
            f'<div class="legend-item"><span class="legend-swatch" style="background:{color}"></span>{label}</div>',
            unsafe_allow_html=True,
        )

if tracker["total"] == 0:
    st.info("Chưa có nhiệm vụ nào trong khoảng này. Thêm nhiệm vụ ở trang Dashboard và chọn đúng ngày.")

st.markdown("<br>", unsafe_allow_html=True)

header = st.columns(7, gap="small")
for col, name in zip(header, ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]):
    col.markdown(f'<div class="muted-small" style="text-align:center;font-weight:700">{name}</div>',
                 unsafe_allow_html=True)

days = tracker["days"]
cells: list = [None] * days[0]["weekday"] + days
cells += [None] * ((7 - len(cells) % 7) % 7)
t_today = today()
for start in range(0, len(cells), 7):
    cols = st.columns(7, gap="small")
    for col, info in zip(cols, cells[start:start + 7]):
        with col:
            if info is None:
                st.markdown('<div style="min-height:88px"></div>', unsafe_allow_html=True)
                continue
            if info["future"]:
                background, foreground = "#fbfbfd", "#7b8197"
                rate_text = "—"
                sub = f"{info['total']} việc sắp tới" if info["total"] else "chưa có việc"
            elif info["total"] == 0:
                background, foreground, rate_text, sub = "#eef0f5", "#626a80", "0%", "không có việc"
            else:
                background, foreground = _day_colors(info["rate"])
                rate_text = f"{info['rate']:.0f}%"
                sub = f"{info['done']}/{info['total']} việc"
            ring = "box-shadow:0 0 0 2px #7357e8;" if info["date"] == t_today else ""
            st.markdown(
                f'<div class="calendar-day" style="background:{background};color:{foreground};{ring}">'
                f'<div class="calendar-day-number">NGÀY {info["day"]}</div>'
                f'<div class="calendar-day-rate">{rate_text}</div>'
                f'<div class="muted-small" style="color:{foreground}">{sub}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ============================ LẬP LỊCH ƯU TIÊN TUẦN ============================

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🗂️ Lập lịch cho ưu tiên tuần"):
    if not weeks:
        st.info("Chưa có ưu tiên tuần. Thêm ở trang Thêm mục tiêu.")
    else:
        week_ids = [w["id"] for w in weeks]
        labels = {w["id"]: w["title"] for w in weeks}
        week_id = st.selectbox("Chọn ưu tiên tuần", options=week_ids,
                               format_func=lambda gid: labels.get(gid, ""), key="planner_week")
        render_week_planner(repo.get_goal(week_id), key_prefix=f"gp_{week_id}")

# ============================ QUẢN LÝ MỤC TIÊU ============================

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("⚙️ Cập nhật tiến độ · đổi trạng thái · xóa mục tiêu"):
    all_goals = years + months + weeks
    if not all_goals:
        st.info("Chưa có mục tiêu nào.")
    else:
        labels = {g["id"]: f"[{LEVEL_SHORT[g['level']]}] {g['title']}" for g in all_goals}
        goal_id = st.selectbox("Chọn mục tiêu", options=[g["id"] for g in all_goals],
                               format_func=lambda gid: labels[gid], key="manage_goal")
        goal = repo.get_goal(goal_id)
        status_options = ["active", "completed", "paused"]
        status_labels = {"active": "Đang thực hiện", "completed": "Hoàn thành", "paused": "Tạm dừng"}
        col_a, col_b = st.columns(2)
        with col_a:
            status = st.selectbox("Trạng thái", options=status_options,
                                  index=status_options.index(goal["status"]) if goal["status"] in status_options else 0,
                                  format_func=status_labels.get, key=f"manage_status_{goal_id}")
            manual = st.number_input("Tiến độ nhập tay (dùng khi chưa có nhiệm vụ)",
                                     min_value=0.0, value=float(goal["current_value"] or 0.0),
                                     step=1.0, key=f"manage_current_{goal_id}")
        with col_b:
            st.caption("Với kế hoạch tháng/tuần có nhiệm vụ, tiến độ tự tính theo số việc đã xong.")
            st.caption("Mục tiêu năm tự tính theo trung bình các kế hoạch tháng con.")
        col_save, col_del = st.columns(2)
        with col_save:
            if st.button("Lưu thay đổi", type="primary", use_container_width=True, key=f"manage_save_{goal_id}"):
                repo.update_goal(goal_id, status=status, current_value=manual)
                st.toast("Đã lưu.")
                st.rerun()
        with col_del:
            if st.button("Xóa mục tiêu này", use_container_width=True, key=f"manage_delete_{goal_id}"):
                repo.delete_goal(goal_id)
                st.toast("Đã xóa mục tiêu.")
                st.rerun()
        if st.button("✏️ Sửa đầy đủ (tên, mô tả, hạn, tháng, cấp cha, thời lượng)",
                     use_container_width=True, key=f"manage_edit_{goal_id}"):
            edit_goal_dialog(goal_id)
        st.caption("Xóa một mục tiêu năm sẽ xóa luôn các kế hoạch tháng và tuần con. Nhiệm vụ vẫn được giữ lại.")

st.markdown(
    '<div class="info-banner">Gợi ý: giữ mục tiêu năm ở mức định hướng, sau đó cập nhật kế hoạch tháng và tuần '
    'để các hành động hằng ngày luôn có ngữ cảnh.</div>',
    unsafe_allow_html=True,
)
