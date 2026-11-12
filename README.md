# Personal OS (một người dùng)

Ứng dụng quản lý cá nhân: tổng quan, nhiệm vụ theo ngày, thói quen hằng ngày, mục tiêu 4 cấp, ghi chú,
và nhắc việc qua Telegram (7:00 sáng và 19:00 tối). Không đăng nhập, không dùng AI.

## Tính năng chính
- **Nhiệm vụ theo ngày:** ở Dashboard chọn ngày để xem hoặc lập việc cho ngày bất kỳ. Bấm ✏️ để sửa tên,
  thời lượng, mục tiêu hoặc ngày.
- **Thói quen:** mỗi thói quen tự tạo một nhiệm vụ cho mỗi ngày kể từ ngày bắt đầu. Ngày nghỉ vẫn có việc
  nhưng là tùy chọn và không kéo tiến độ xuống. Sửa thói quen chỉ áp dụng từ hôm nay trở đi.
- **Ưu tiên tuần:** nhập tổng thời lượng dự kiến, rồi chọn tự động chia đều cho các ngày làm việc từ hôm nay
  đến hạn, hoặc tự tạo thủ công từng ngày.
- **Mục tiêu 4 cấp:** tiến độ tổng quan theo từng cấp và một lịch trạng thái theo tháng, màu thể hiện mức hoàn thành.
- **Sửa mục tiêu đầy đủ:** tên, mô tả, hạn, tháng, cấp cha, mục tiêu số, thời lượng dự kiến và trạng thái.
- **Nhập kế hoạch từ AI:** trang **📥 Nhập kế hoạch** có sẵn lời nhắc để bạn gửi cho AI. AI trả về JSON theo
  định dạng `personal-os-plan`, bạn dán vào, ứng dụng kiểm tra và xem trước rồi mới tạo mục tiêu, nhiệm vụ
  (tự chia theo giờ) và thói quen. Ứng dụng không tự gọi AI.
- **Sao lưu & xuất:** ở trang Hồ sơ, tải file JSON toàn bộ dữ liệu (kể cả ảnh ghi chú) hoặc CSV nhiệm vụ/mục tiêu.

## Nâng cấp cơ sở dữ liệu
Các thay đổi schema chỉ **thêm** bảng `habits` và thêm các cột `tasks.habit_id`, `tasks.optional`,
`goals.estimated_minutes` với giá trị mặc định. Không xóa hay sửa dữ liệu hiện có. Khi khởi động, ứng dụng tự
thêm cột còn thiếu, nên database cũ vẫn dùng được mà không cần chạy script.

## Chạy trên máy (SQLite)
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
Không đặt `DATABASE_URL` thì dữ liệu lưu trong `data/personal_os.db`.

## Triển khai miễn phí lên web

Kiến trúc: giao diện chạy trên **Streamlit Community Cloud**, dữ liệu lưu trên **Supabase** (PostgreSQL),
còn nhắc việc Telegram chạy bằng **GitHub Actions** theo lịch.

### 1. Tạo database trên Supabase
1. Đăng ký tại supabase.com, tạo project mới và lưu lại mật khẩu database.
2. Vào **Connect** và copy chuỗi **Session pooler** (dạng `postgresql://postgres.xxxx:[PASSWORD]@...pooler.supabase.com:5432/postgres`).
   Thay `[PASSWORD]` bằng mật khẩu thật. Đây là `DATABASE_URL`.

### 2. Chuyển dữ liệu cũ (nếu đã có dữ liệu trên máy)
```bash
export DATABASE_URL="postgresql://postgres.xxxx:...@...pooler.supabase.com:5432/postgres"
python migrate_to_postgres.py --source data/personal_os.db --uploads data/uploads
```
Script chỉ chạy trên database trống. Nếu đã có dữ liệu, script sẽ dừng để tránh nhân đôi.

### 3. Đưa mã lên GitHub
Nên dùng repo **private**. Các file bí mật (`.streamlit/secrets.toml`, `data/`, `.env`) đã được loại khỏi git.
```bash
git init && git add . && git commit -m "Personal OS"
git branch -M main && git remote add origin <link_repo> && git push -u origin main
```

### 4. Deploy giao diện (Streamlit Community Cloud)
1. Vào share.streamlit.io, chọn **New app**, chọn repo, branch `main`, file chính `streamlit_app.py`.
2. Mục **Advanced settings**: chọn Python 3.11.
3. Mục **Secrets**, dán:
   ```toml
   DATABASE_URL = "postgresql://postgres.xxxx:...@...pooler.supabase.com:5432/postgres"
   TELEGRAM_BOT_TOKEN = "token_mới_từ_BotFather"
   ```
4. Bấm **Deploy**. Bạn sẽ có link dạng `https://ten-app.streamlit.app`.
5. **Bắt buộc:** vào app → **Settings → Sharing** → chọn **Only specific people can view** và thêm email của bạn.
   Không làm bước này thì bất kỳ ai có link cũng xem và sửa được dữ liệu, kể cả thông tin sức khỏe.

### 5. Bật nhắc việc (GitHub Actions)
1. Trong repo: **Settings → Secrets and variables → Actions**, thêm hai secret:
   `DATABASE_URL` và `TELEGRAM_BOT_TOKEN` (cùng giá trị như trên).
2. Vào tab **Actions → Nhắc việc Telegram → Run workflow** để chạy thử.
   Nếu đúng giờ gửi thì tin đã được gửi. Nếu ngoài giờ, lần chạy sẽ báo "Chưa đến giờ" và không gửi.
3. Lịch tự động chạy hằng ngày theo `.github/workflows/notify.yml`.

## Lưu ý
- **Token Telegram:** token cũ đã lộ trong ảnh trước đó. Hãy dùng `/revoke` trong BotFather và dùng token mới cho cả Streamlit lẫn GitHub.
- **Thời gian gửi:** GitHub có thể chạy lịch trễ vài phút đến hơn chục phút. Workflow chạy thêm vài lần để bù, và mỗi loại thông báo chỉ gửi một lần mỗi ngày.
- **Supabase free:** project có thể tạm dừng khi không hoạt động trong một thời gian dài. Lịch nhắc việc hằng ngày truy cập database nên thường giữ project luôn hoạt động.
- **Ảnh ghi chú** được lưu trong database (bảng `note_images`), nên không bị mất khi app khởi động lại.

## Cấu trúc
- `streamlit_app.py`: điểm vào, kiểm tra khảo sát ban đầu, tạo nhiệm vụ thói quen và thanh điều hướng.
- `views/`: các trang của ứng dụng.
- `core/`: kết nối database (`db.py`), truy cập dữ liệu (`repo.py`), thông báo Telegram (`notify.py`), giao diện (`theme.py`, `widgets.py`).
- `notifier.py`: gửi thông báo. `--once` cho GitHub Actions, `--daemon` để chạy nền trên máy, `--send` để gửi thử.
- `migrate_to_postgres.py`: chuyển dữ liệu SQLite sang PostgreSQL.
- `core/plan_import.py`: đọc, kiểm tra và ghi kế hoạch do AI soạn (định dạng `personal-os-plan`).
- `core/backup.py`: sao lưu JSON và xuất CSV (chỉ đọc).
