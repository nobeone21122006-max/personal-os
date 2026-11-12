"""Hằng số và tiện ích dùng chung."""
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Hà Nội: GMT+7, không có giờ mùa hè nên dùng múi giờ cố định (không cần tzdata).
VN_TZ = timezone(timedelta(hours=7))

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
DB_PATH = DATA_DIR / "personal_os.db"
UPLOAD_DIR = DATA_DIR / "uploads"

WEEKDAYS = {0: "Thứ 2", 1: "Thứ 3", 2: "Thứ 4", 3: "Thứ 5", 4: "Thứ 6", 5: "Thứ 7", 6: "Chủ nhật"}


def get_secret(name: str, default: str = "") -> str:
    """Đọc cấu hình: ưu tiên biến môi trường, sau đó st.secrets (Streamlit Cloud)."""
    value = os.environ.get(name, "").strip()
    if value:
        return value
    try:
        import streamlit as st  # chỉ import khi cần, để notifier chạy được không cần UI

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return default


def now() -> datetime:
    return datetime.now(VN_TZ)


def today() -> date:
    return now().date()


def now_iso() -> str:
    return now().isoformat(timespec="seconds")


def current_school_year(d: date | None = None) -> str:
    """Năm học bắt đầu từ tháng 9: tháng 9/2026 -> '2026-2027'."""
    d = d or today()
    start = d.year if d.month >= 9 else d.year - 1
    return f"{start}-{start + 1}"


def greeting(hour: int) -> str:
    if 5 <= hour < 12:
        return "Good morning"
    if 12 <= hour < 18:
        return "Good afternoon"
    if 18 <= hour < 22:
        return "Good evening"
    return "Good night"


def month_bounds(year: int, month: int) -> tuple[date, date]:
    import calendar

    last = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last)
