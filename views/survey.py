import streamlit as st

from core import repo
from core.common import current_school_year
from core.theme import page_heading
from core.widgets import profile_fields

page_heading(
    "KHẢO SÁT BAN ĐẦU",
    "Chào bạn, hãy kể về bản thân",
    "Bạn chỉ cần làm khảo sát này một lần. Sau này có thể cập nhật bất cứ lúc nào trong mục Tổng quan.",
)

_, center, _ = st.columns([0.35, 2.3, 0.35])
with center:
    with st.container(border=True):
        with st.form("onboarding_form"):
            name = st.text_input("Tên của bạn", placeholder="VD: Long", key="ob_name")
            values = profile_fields("ob")
            st.caption(f"Thông tin sẽ được lưu cho năm học {current_school_year()}. "
                       "Dữ liệu sức khỏe chỉ dùng để cá nhân hóa, không thay thế tư vấn y tế.")
            submitted = st.form_submit_button("Hoàn tất khảo sát", type="primary", use_container_width=True)

        if submitted:
            if len(name.strip()) < 1:
                st.warning("Vui lòng nhập tên của bạn.")
            elif not values["health_status"]:
                st.warning("Vui lòng chọn tình trạng sức khỏe.")
            elif not values["major"].strip():
                st.warning("Vui lòng nhập ngành học.")
            else:
                repo.complete_onboarding(name, values)
                st.rerun()
