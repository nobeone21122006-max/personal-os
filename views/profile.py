import streamlit as st

from core import backup, notify, repo
from core.common import WEEKDAYS
from core.common import today
from core.theme import page_heading, section

page_heading(
    "HỒ SƠ",
    "Hồ sơ & Telegram",
    "Tên gọi, thời gian rảnh và ngày nghỉ dùng để lập kế hoạch. Múi giờ mặc định là Hà Nội (GMT+7).",
)

with st.form("profile_form"):
    name = st.text_input("Tên gọi", value=repo.get_name(), placeholder="VD: Long")
    free_hours = st.slider("Giờ rảnh mỗi ngày", min_value=0.5, max_value=16.0,
                           value=float(repo.get_free_hours()), step=0.5)
    rest_days = st.multiselect(
        "Ngày nghỉ",
        options=list(WEEKDAYS),
        default=repo.get_rest_days(),
        format_func=WEEKDAYS.get,
    )
    st.caption("🕒 Múi giờ: Hà Nội (GMT+7)")
    telegram_chat_id = st.text_input(
        "Telegram chat ID",
        value=repo.get_telegram_chat_id(),
        placeholder="VD: 123456789",
        help="Dùng để nhận nhắc việc qua Telegram khi bot được kết nối.",
    )
    save = st.form_submit_button("Lưu hồ sơ", type="primary", use_container_width=True)

if save:
    if not name.strip():
        st.warning("Vui lòng nhập tên gọi.")
    else:
        repo.update_personal_settings(name, free_hours, rest_days, telegram_chat_id)
        st.success("Đã lưu hồ sơ.")

section("Telegram")
if repo.get_telegram_chat_id():
    st.success("Đã lưu chat ID Telegram. Bot sẽ gửi nhắc việc lúc 7:00 và tổng kết lúc 19:00.")
else:
    st.info("Chưa có chat ID. Nhập chat ID ở trên để bật nhắc việc.")

has_token = bool(notify.get_token())
if has_token:
    st.success("Bot token đã được cấu hình trên máy chủ.")
else:
    st.warning("Chưa có TELEGRAM_BOT_TOKEN. Đặt biến môi trường trước khi chạy app, "
               "hoặc thêm vào Secrets khi triển khai trên Streamlit Cloud.")

if st.button("📨 Gửi tin thử", disabled=not (has_token and repo.get_telegram_chat_id())):
    try:
        notify.send_telegram("✅ Personal OS đã kết nối Telegram thành công.", repo.get_telegram_chat_id())
        st.success("Đã gửi tin thử. Kiểm tra Telegram của bạn.")
    except Exception as exc:
        st.error(str(exc))

st.caption("Lịch gửi: 7:00 sáng (việc cần làm hôm nay) và 19:00 tối (đã xong / chưa xong). "
           "Khi đã deploy, GitHub Actions sẽ tự gửi theo lịch.")

section("Sao lưu & xuất dữ liệu")
st.caption(
    "Tải dữ liệu về máy để giữ bản sao phòng khi mất dữ liệu. File JSON chứa toàn bộ dữ liệu, kể cả ảnh ghi chú. "
    "Hiện chưa có chức năng khôi phục tự động từ file này. File CSV dùng để xem hoặc phân tích trong Excel."
)
stamp = today().isoformat()
col_a, col_b, col_c = st.columns(3, gap="medium")
with col_a:
    st.download_button(
        "💾 Sao lưu toàn bộ (JSON)",
        data=backup.build_backup_json(),
        file_name=f"personal-os-backup-{stamp}.json",
        mime="application/json",
        use_container_width=True,
    )
with col_b:
    st.download_button(
        "📄 Nhiệm vụ (CSV)",
        data=backup.tasks_csv(),
        file_name=f"personal-os-nhiem-vu-{stamp}.csv",
        mime="text/csv",
        use_container_width=True,
    )
with col_c:
    st.download_button(
        "📄 Mục tiêu (CSV)",
        data=backup.goals_csv(),
        file_name=f"personal-os-muc-tieu-{stamp}.csv",
        mime="text/csv",
        use_container_width=True,
    )
