"""Soạn và gửi thông báo Telegram: 7:00 sáng (việc hôm nay) và 19:00 tối (tổng kết).

Token bot lấy từ biến môi trường TELEGRAM_BOT_TOKEN, không lưu trong mã nguồn hay DB.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

from core import repo
from core.common import VN_TZ, get_secret

MORNING_AT = (7, 0)
EVENING_AT = (19, 0)
WINDOW_MINUTES = 60   # chế độ --daemon: chỉ gửi trong 60 phút kể từ giờ hẹn
ONCE_WINDOW_MINUTES = 240  # chế độ --once (GitHub Actions): lịch có thể bị trễ, nên cửa sổ rộng hơn


def get_token() -> str:
    return get_secret("TELEGRAM_BOT_TOKEN")


def _fmt_minutes(minutes: int) -> str:
    minutes = int(minutes or 0)
    if minutes >= 60:
        hours, rest = divmod(minutes, 60)
        return f"{hours}h {rest:02d}p" if rest else f"{hours} giờ"
    return f"{minutes} phút"


def send_telegram(text: str, chat_id: str) -> None:
    token = get_token()
    if not token:
        raise RuntimeError("Chưa cấu hình TELEGRAM_BOT_TOKEN (biến môi trường hoặc secrets).")
    if not chat_id:
        raise RuntimeError("Chưa có Telegram chat ID. Nhập ở mục Hồ sơ & Telegram.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method="POST"), timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Không in nội dung lỗi gốc vì URL chứa token.
        raise RuntimeError(f"Telegram trả về lỗi HTTP {exc.code}. Kiểm tra token và chat ID.") from None
    except urllib.error.URLError:
        raise RuntimeError("Không kết nối được tới Telegram. Kiểm tra mạng.") from None

    if not body.get("ok"):
        raise RuntimeError(f"Telegram từ chối tin nhắn: {body.get('description', 'lỗi không rõ')}")


def build_morning(d: date) -> str:
    name = repo.get_name() or "bạn"
    tasks = repo.tasks_on(d)
    date_text = f"{d.day:02d}/{d.month:02d}/{d.year}"
    if not tasks:
        return (f"☀️ Chào {name}! Hôm nay ({date_text}) chưa có nhiệm vụ nào. "
                "Mở Personal OS để thêm việc cần làm nhé.")
    # Việc tùy chọn (thói quen ngày nghỉ) vẫn hiện, nhưng không tính vào số việc bắt buộc.
    required = [t for t in tasks if not t.get("optional")]
    if not required:
        optional_names = ", ".join(t["title"] for t in tasks)
        return (f"☀️ Chào {name}! Hôm nay ({date_text}) không có việc bắt buộc. "
                f"Tùy chọn: {optional_names}.")
    lines = [f"☀️ Chào {name}! Hôm nay ({date_text}) bạn có {len(required)} việc cần làm:"]
    for i, t in enumerate(required, 1):
        goal = f" ({t['goal_title']})" if t.get("goal_title") else ""
        lines.append(f"{i}. {t['title']} · {_fmt_minutes(t['duration_minutes'])}{goal}")
    optional = [t for t in tasks if t.get("optional")]
    if optional:
        lines.append("\nTùy chọn (ngày nghỉ): " + ", ".join(t["title"] for t in optional))
    total = sum(int(t["duration_minutes"]) for t in required)
    lines.append(f"\nTổng thời lượng dự kiến: {_fmt_minutes(total)}. Chúc bạn một ngày hiệu quả!")
    return "\n".join(lines)


def build_evening(d: date) -> str:
    name = repo.get_name() or "bạn"
    # Việc tùy chọn chưa làm không tính vào tiến độ và không liệt kê là "chưa xong".
    tasks = [t for t in repo.tasks_on(d) if not (t.get("optional") and not t["done"])]
    done = [t for t in tasks if t["done"]]
    pending = [t for t in tasks if not t["done"]]
    rate = (len(done) / len(tasks) * 100) if tasks else 0.0

    lines = [f"🌙 Tổng kết ngày {d.day:02d}/{d.month:02d}/{d.year}, {name}:"]
    if not tasks:
        lines.append("Hôm nay chưa ghi nhận nhiệm vụ nào.")
    else:
        lines.append(f"\n✅ Đã xong ({len(done)}/{len(tasks)}):")
        lines += [f"- {t['title']} · {_fmt_minutes(t['duration_minutes'])}" for t in done] or ["—"]
        lines.append(f"\n⏳ Chưa xong ({len(pending)}):")
        lines += [f"- {t['title']} · {_fmt_minutes(t['duration_minutes'])}" for t in pending] or ["—"]
        lines.append(f"\nHoàn thành {rate:.0f}% kế hoạch hôm nay.")
    lines.append("Nghỉ ngơi thật tốt nhé!" if rate >= 100 or not tasks else
                 "Ngày mai là một cơ hội mới, bạn làm được!")
    return "\n".join(lines)


def build_message(kind: str, d: date) -> str:
    if kind == "morning":
        return build_morning(d)
    if kind == "evening":
        return build_evening(d)
    raise ValueError("kind phải là 'morning' hoặc 'evening'")


def due_kind(now: datetime, window_minutes: int = WINDOW_MINUTES) -> str | None:
    """Trả về loại thông báo đang đến giờ gửi (trong cửa sổ cho phép), hoặc None."""
    for kind, (hour, minute) in (("morning", MORNING_AT), ("evening", EVENING_AT)):
        start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if start <= now < start + timedelta(minutes=window_minutes):
            return kind
    return None


def run_due(now: datetime, window_minutes: int = WINDOW_MINUTES) -> str | None:
    """Gửi thông báo nếu đến giờ và chưa gửi trong ngày. Trả về loại đã gửi hoặc None."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=VN_TZ)
    kind = due_kind(now, window_minutes)
    if not kind:
        return None
    flag = f"notif_sent_{kind}_{now.date().isoformat()}"
    if repo.get_setting(flag):
        return None
    send_telegram(build_message(kind, now.date()), repo.get_telegram_chat_id())
    repo.set_setting(flag, "1")  # chỉ đánh dấu sau khi gửi thành công
    return kind
