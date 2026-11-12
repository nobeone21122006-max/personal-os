"""Điểm vào của ứng dụng Personal OS (một người dùng, không đăng nhập)."""
import streamlit as st

st.set_page_config(
    page_title="Personal OS",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core import repo  # noqa: E402
from core.common import today  # noqa: E402
from core.db import init_db  # noqa: E402
from core.theme import apply_theme  # noqa: E402

init_db()
apply_theme()

# Tự tạo nhiệm vụ cho thói quen (từ ngày bắt đầu đến hôm nay). Chỉ chạy lại khi sang ngày mới
# hoặc khi thói quen thay đổi, để không ghi database ở mọi lần tương tác.
if st.session_state.get("habits_synced_on") != today().isoformat():
    repo.ensure_habit_tasks()
    st.session_state["habits_synced_on"] = today().isoformat()

with st.sidebar:
    st.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-mark">✦</div>
            <div><div class="brand-name">Personal OS</div><div class="brand-sub">PLAN · GROW · REFLECT</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if not repo.is_onboarded():
    # Lần đầu sử dụng: chỉ hiện trang khảo sát cho đến khi hoàn tất.
    navigation = st.navigation(
        [st.Page("views/survey.py", title="Khảo sát ban đầu", icon="🧭", default=True)],
        position="hidden",
    )
else:
    navigation = st.navigation(
        {
            "Workspace": [
                st.Page("views/overview.py", title="Tổng quan", icon="🏠", default=True),
                st.Page("views/dashboard.py", title="Dashboard", icon="📊"),
                st.Page("views/habits.py", title="Thói quen", icon="🔁"),
                st.Page("views/goals.py", title="Mục tiêu 4 cấp", icon="🎯"),
                st.Page("views/add_goal.py", title="Thêm mục tiêu", icon="➕"),
                st.Page("views/plan_import.py", title="Nhập kế hoạch", icon="📥"),
                st.Page("views/notes.py", title="Ghi chú", icon="📝"),
                st.Page("views/profile.py", title="Hồ sơ & Telegram", icon="👤"),
            ]
        }
    )

navigation.run()
