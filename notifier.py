"""Gửi thông báo Telegram hằng ngày.

  python notifier.py --daemon                    # chạy nền: 7:00 việc hôm nay, 19:00 tổng kết
  python notifier.py --once                      # kiểm tra một lần rồi thoát (dùng với GitHub Actions)
  python notifier.py --send morning              # gửi thử ngay
  python notifier.py --send evening --dry-run    # chỉ in nội dung, không gửi
"""
import argparse
import sys
import time

from core import notify, repo
from core.common import now as vn_now, today
from core.db import init_db

CHECK_INTERVAL_SECONDS = 30


def main() -> int:
    parser = argparse.ArgumentParser(description="Thông báo Telegram cho Personal OS")
    parser.add_argument("--daemon", action="store_true", help="Chạy nền, kiểm tra mỗi 30 giây")
    parser.add_argument("--once", action="store_true", help="Kiểm tra một lần rồi thoát")
    parser.add_argument("--send", choices=["morning", "evening"], help="Gửi thử ngay")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in nội dung khi dùng --send")
    args = parser.parse_args()

    init_db()
    # Tạo nhiệm vụ thói quen cho hôm nay trước khi gửi, để tin nhắn buổi sáng có đủ việc.
    if not (args.send and args.dry_run):
        repo.ensure_habit_tasks()

    if args.send:
        text = notify.build_message(args.send, today())
        if args.dry_run:
            print(text)
            return 0
        notify.send_telegram(text, repo.get_telegram_chat_id())
        print("Đã gửi tin nhắn.")
        return 0

    if args.once:
        kind = notify.run_due(vn_now(), notify.ONCE_WINDOW_MINUTES)
        print(f"Đã gửi thông báo {kind}." if kind else "Chưa đến giờ hoặc đã gửi hôm nay.")
        return 0

    if args.daemon:
        print("Notifier đang chạy: 7:00 gửi việc hôm nay, 19:00 gửi tổng kết (giờ Hà Nội).", flush=True)
        while True:
            try:
                kind = notify.run_due(vn_now())
                if kind:
                    print(f"{vn_now():%d/%m %H:%M} đã gửi thông báo {kind}.", flush=True)
            except Exception as exc:  # không để một lỗi làm dừng tiến trình
                print(f"{vn_now():%d/%m %H:%M} lỗi gửi thông báo: {exc}", file=sys.stderr, flush=True)
            time.sleep(CHECK_INTERVAL_SECONDS)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
