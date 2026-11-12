import streamlit as st

from core import plan_import
from core.theme import page_heading, section

page_heading(
    "NHẬP KẾ HOẠCH",
    "Nhập kế hoạch từ AI",
    "Nhờ một AI bất kỳ chia mục tiêu năm thành kế hoạch theo định dạng bên dưới, rồi dán kết quả vào đây. "
    "Ứng dụng sẽ kiểm tra và hiển thị bản xem trước trước khi tạo bất cứ thứ gì.",
)

section("1 · Gửi lời nhắc này cho AI")
st.caption(
    "Sao chép lời nhắc (nút góc phải khung), thay dòng cuối bằng mục tiêu năm của bạn, rồi gửi cho AI. "
    "Lời nhắc đã có sẵn ngày hôm nay, ngày nghỉ và giờ rảnh của bạn. Ứng dụng không tự gọi AI."
)
st.code(plan_import.build_prompt(), language="text")

section("2 · Dán kết quả AI trả về")
st.caption("Dán nguyên khối JSON. Nếu AI có thêm hàng rào ```json thì không sao, ứng dụng tự bỏ đi.")
st.text_area("Kết quả JSON", height=240, key="import_text", placeholder='{ "format": "personal-os-plan", ... }')

if st.button("🔍 Kiểm tra và xem trước", type="primary", use_container_width=True):
    st.session_state.pop("import_plan", None)
    try:
        data = plan_import.parse_text(st.session_state.get("import_text", ""))
        plan, errors = plan_import.normalize(data)
    except plan_import.PlanError as exc:
        st.error(str(exc))
    else:
        if errors:
            st.error("Kế hoạch có lỗi, chưa tạo gì cả. Hãy sửa rồi kiểm tra lại:")
            for err in errors[:30]:
                st.markdown(f"- {err}")
            if len(errors) > 30:
                st.caption(f"… và {len(errors) - 30} lỗi khác.")
        else:
            st.session_state["import_plan"] = plan

plan = st.session_state.get("import_plan")
if plan:
    section("3 · Xem trước")
    for warning in plan_import.duplicate_warnings(plan):
        st.warning(warning)
    st.success(
        f"Sẵn sàng: {len(plan['years'])} tầm nhìn năm, {plan['total_tasks']} nhiệm vụ cụ thể, "
        f"{plan['total_habits']} thói quen."
    )
    with st.container(border=True):
        st.markdown("  \n".join(plan_import.preview_lines(plan)), unsafe_allow_html=True)

    if st.button("✅ Tạo kế hoạch này", type="primary", use_container_width=True):
        counts = plan_import.import_plan(plan)
        st.session_state.pop("import_plan", None)
        st.toast("Đã tạo kế hoạch.")
        st.success(
            f"Đã tạo {counts['goals']} mục tiêu, {counts['tasks']} nhiệm vụ và {counts['habits']} thói quen. "
            "Xem ở trang Mục tiêu 4 cấp, Dashboard và Thói quen."
        )
