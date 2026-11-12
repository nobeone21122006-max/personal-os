import streamlit as st

from core import repo
from core.common import today
from core.theme import page_heading, section
from core.widgets import add_task_form, day_label, day_task_summary, fmt_minutes, render_task_checklist

page_heading(
    "DASHBOARD",
    "Nhiệm vụ theo ngày",
    "Chọn ngày để xem hoặc lập nhiệm vụ. Mặc định là hôm nay; bạn có thể lập việc cho các ngày khác.",
)

selected = st.date_input("Xem nhiệm vụ của ngày", value=today(), key="dash_day", format="DD/MM/YYYY")
tasks = repo.tasks_on(selected)
summary = day_task_summary(tasks)
is_today = selected == today()
section("Nhiệm vụ hôm nay" if is_today else f"Nhiệm vụ · {day_label(selected)}")

m1, m2, m3 = st.columns(3, gap="medium")
m1.metric("Tổng nhiệm vụ", summary["total"])
m2.metric("Đã hoàn thành", f"{summary['done']}/{summary['total']}")
m3.metric("Thời gian còn lại", fmt_minutes(summary["remaining_minutes"]) if summary["total"] else "—")

st.progress(summary["rate"], text=f"{summary['rate']:.0%} hoàn thành")

with st.expander("➕ Thêm nhiệm vụ", expanded=not tasks):
    if add_task_form(selected, key=f"dash_add_{selected.isoformat()}"):
        st.rerun()

st.caption("Tích vào ô để đánh dấu hoàn thành. Bấm ✏️ để sửa tên, thời lượng, mục tiêu hoặc ngày.")
render_task_checklist(tasks, key_prefix=f"dash_{selected.isoformat()}", title="Việc cần làm")

if summary["total"]:
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption(f"Tổng thời lượng dự kiến: {fmt_minutes(summary['planned_minutes'])}")
