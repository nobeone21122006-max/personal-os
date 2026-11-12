"""Nhập kế hoạch do AI soạn theo định dạng "personal-os-plan" (JSON).

Ứng dụng KHÔNG gọi AI. Quy trình:
1. Bạn nhờ một AI bất kỳ soạn kế hoạch theo lời nhắc do ứng dụng tạo sẵn (build_prompt).
2. Bạn dán kết quả AI trả về vào ứng dụng.
3. Ứng dụng đọc JSON, kiểm tra từng trường, dựng bản xem trước (cây mục tiêu + từng nhiệm vụ có ngày cụ thể).
4. Khi bạn xác nhận, các mục tiêu/nhiệm vụ/thói quen được thêm vào database trong MỘT giao dịch.
   Chỉ thêm mới, không sửa hay xóa dữ liệu hiện có.
"""
import json
import re
from calendar import monthrange
from datetime import date, timedelta

from core import repo
from core.common import WEEKDAYS, now_iso, today
from core.db import db

FORMAT_ID = "personal-os-plan"
FORMAT_VERSION = 1
MAX_TASKS = 1000
MAX_HABITS = 50
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class PlanError(ValueError):
    """Lỗi đọc JSON (không đúng cú pháp hoặc không phải dữ liệu kế hoạch)."""


# ============================ LỜI NHẮC GỬI CHO AI ============================

EXAMPLE = {
    "format": FORMAT_ID,
    "version": FORMAT_VERSION,
    "year_goals": [
        {
            "title": "Đạt IELTS 6.5",
            "description": "Ưu tiên writing và speaking",
            "deadline": "2027-06-30",
            "months": [
                {
                    "title": "Luyện writing task 2",
                    "plan_month": "2026-12",
                    "description": "",
                    "tasks": [
                        {"title": "Làm đề writing mẫu", "date": "2026-12-05", "minutes": 90}
                    ],
                    "habits": [
                        {"title": "Đọc 20 trang tiếng Anh", "minutes": 30, "start_date": "2026-12-01"}
                    ],
                    "weeks": [
                        {
                            "title": "Viết 3 bài luyện writing",
                            "description": "",
                            "start": "2026-12-01",
                            "deadline": "2026-12-14",
                            "estimated_hours": 4.5,
                            "tasks": []
                        }
                    ]
                }
            ]
        }
    ]
}


def _rest_names() -> str:
    rest = repo.get_rest_days()
    return ", ".join(WEEKDAYS[d] for d in sorted(rest)) or "không có"


def build_prompt() -> str:
    """Lời nhắc có sẵn ngày hôm nay, ngày nghỉ và giờ rảnh của bạn. Dán nguyên văn vào AI."""
    t = today()
    example = json.dumps(EXAMPLE, ensure_ascii=False, indent=2)
    return f"""Bạn là trợ lý lập kế hoạch cá nhân. Hãy chia mục tiêu năm của tôi thành kế hoạch theo đúng định dạng JSON bên dưới để tôi dán vào ứng dụng Personal OS.

Quy tắc bắt buộc:
- Chỉ trả về MỘT khối JSON hợp lệ. Không lời giải thích, không chữ nào ngoài JSON.
- Ngày viết dạng YYYY-MM-DD. Tháng viết dạng YYYY-MM.
- Hôm nay là {t.isoformat()}. Bắt đầu kế hoạch từ tháng {t.year}-{t.month:02d} (hoặc tháng sau nếu tôi yêu cầu).
- Ngày nghỉ của tôi: {_rest_names()}. Giờ rảnh mỗi ngày khoảng {repo.get_free_hours():g} giờ.
- Mỗi "ưu tiên tuần" có "estimated_hours" (tổng giờ). Ứng dụng sẽ tự chia đều cho các ngày làm việc trong khoảng "start" đến "deadline". Chỉ dùng "tasks" khi cần một việc vào một ngày cụ thể.
- "habits" là việc làm đều mỗi ngày (ví dụ đọc sách, luyện tập). Đặt trong tháng tương ứng.
- Mỗi tháng nên có 1–3 ưu tiên tuần, không đặt quá nhiều việc mỗi ngày.
- Tên nhiệm vụ ngắn gọn, bằng tiếng Việt.
- Thời lượng nhiệm vụ "minutes" từ 5 đến 1440.

Định dạng (ví dụ, hãy thay bằng kế hoạch thật):
{example}

Mục tiêu năm của tôi:
[DÁN MỤC TIÊU NĂM VÀO ĐÂY]
"""


# ============================ ĐỌC VÀ KIỂM TRA ============================

def parse_text(text: str) -> dict:
    """Đọc văn bản dán vào. Bỏ hàng rào ```json nếu AI có thêm vào."""
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw).strip()
    if not raw:
        raise PlanError("Chưa có nội dung. Hãy dán kết quả AI trả về.")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlanError(f"JSON không hợp lệ ở dòng {exc.lineno}, cột {exc.colno}: {exc.msg}. "
                        "Hãy yêu cầu AI trả lại đúng JSON, không kèm lời giải thích.") from None
    if not isinstance(data, dict):
        raise PlanError("Dữ liệu phải là một object JSON (bắt đầu bằng dấu { ).")
    return data


def _text(value, path: str, errors: list, required: bool = False, max_len: int = 300) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        errors.append(f"{path}: phải là chữ.")
        return ""
    value = value.strip()
    if required and not value:
        errors.append(f"{path}: đang trống.")
    if len(value) > max_len:
        errors.append(f"{path}: quá {max_len} ký tự.")
    return value


def _date(value, path: str, errors: list) -> date | None:
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{path}: ngày phải dạng YYYY-MM-DD, nhận được “{value}”.")
        return None


def _number(value, path: str, errors: list, lo: float, hi: float, default: float) -> float:
    if value in (None, ""):
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{path}: phải là số.")
        return default
    if not lo <= value <= hi:
        errors.append(f"{path}: phải trong khoảng {lo:g}–{hi:g}.")
        return default
    return float(value)


def _items(value, path: str, errors: list) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        errors.append(f"{path}: phải là danh sách [ ].")
        return []
    return value


def _obj(value, path: str, errors: list) -> dict | None:
    if not isinstance(value, dict):
        errors.append(f"{path}: phải là một object JSON.")
        return None
    return value


def _window_days(start: date, end: date) -> list[date]:
    """Các ngày từ start đến end. Ưu tiên ngày làm việc, chỉ dùng ngày nghỉ khi không còn ngày làm việc."""
    if end < start:
        return []
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    rest = set(repo.get_rest_days())
    working = [d for d in days if d.weekday() not in rest]
    return working or days


def _task_item(item, path: str, errors: list, fallback_date: date | None) -> dict | None:
    obj = _obj(item, path, errors)
    if obj is None:
        return None
    title = _text(obj.get("title"), f"{path}.title", errors, required=True)
    when = _date(obj.get("date"), f"{path}.date", errors) or fallback_date
    if when is None:
        errors.append(f"{path}: cần có ngày (date).")
    minutes = int(_number(obj.get("minutes"), f"{path}.minutes", errors, 5, 1440, 30))
    return {"title": title, "date": when, "minutes": minutes}


def normalize(data: dict) -> tuple[dict | None, list[str]]:
    """Kiểm tra toàn bộ và dựng cấu trúc chuẩn đã tính sẵn từng nhiệm vụ cụ thể.
    Trả về (kế hoạch, danh sách lỗi). Có lỗi thì kế hoạch là None."""
    errors: list[str] = []
    fmt = data.get("format")
    if fmt not in (None, FORMAT_ID):
        errors.append(f"Trường format phải là “{FORMAT_ID}”, nhận được “{fmt}”.")

    years_raw = _items(data.get("year_goals"), "year_goals", errors)
    if not years_raw:
        errors.append("Không có mục tiêu năm nào (year_goals).")

    years = []
    total_tasks = 0
    total_habits = 0
    for i, y_item in enumerate(years_raw):
        p = f"year_goals[{i}]"
        y = _obj(y_item, p, errors)
        if y is None:
            continue
        year = {
            "title": _text(y.get("title"), f"{p}.title", errors, required=True),
            "description": _text(y.get("description"), f"{p}.description", errors, max_len=2000),
            "deadline": _date(y.get("deadline"), f"{p}.deadline", errors),
            "months": [],
        }
        for j, m_item in enumerate(_items(y.get("months"), f"{p}.months", errors)):
            mp = f"{p}.months[{j}]"
            m = _obj(m_item, mp, errors)
            if m is None:
                continue
            plan_month = _text(m.get("plan_month"), f"{mp}.plan_month", errors, required=True, max_len=7)
            if plan_month and not MONTH_RE.match(plan_month):
                errors.append(f"{mp}.plan_month: phải dạng YYYY-MM, nhận được “{plan_month}”.")
                continue
            if not plan_month:
                continue
            ym = int(plan_month[:4]), int(plan_month[5:])
            month_start = date(ym[0], ym[1], 1)
            month_end = date(ym[0], ym[1], monthrange(ym[0], ym[1])[1])
            month = {
                "title": _text(m.get("title"), f"{mp}.title", errors, required=True) or f"Kế hoạch {plan_month}",
                "description": _text(m.get("description"), f"{mp}.description", errors, max_len=2000),
                "plan_month": plan_month,
                "deadline": _date(m.get("deadline"), f"{mp}.deadline", errors) or month_end,
                "tasks": [],
                "habits": [],
                "weeks": [],
            }

            for k, t_item in enumerate(_items(m.get("tasks"), f"{mp}.tasks", errors)):
                task = _task_item(t_item, f"{mp}.tasks[{k}]", errors, None)
                if task:
                    month["tasks"].append(task)

            for k, h_item in enumerate(_items(m.get("habits"), f"{mp}.habits", errors)):
                hp = f"{mp}.habits[{k}]"
                h = _obj(h_item, hp, errors)
                if h is None:
                    continue
                start = _date(h.get("start_date"), f"{hp}.start_date", errors) or max(today(), month_start)
                month["habits"].append({
                    "title": _text(h.get("title"), f"{hp}.title", errors, required=True),
                    "minutes": int(_number(h.get("minutes"), f"{hp}.minutes", errors, 5, 1440, 30)),
                    "start_date": start,
                })
                total_habits += 1

            for k, w_item in enumerate(_items(m.get("weeks"), f"{mp}.weeks", errors)):
                wp = f"{mp}.weeks[{k}]"
                w = _obj(w_item, wp, errors)
                if w is None:
                    continue
                w_end = _date(w.get("deadline"), f"{wp}.deadline", errors) or month_end
                w_start = _date(w.get("start"), f"{wp}.start", errors) or max(today(), month_start)
                if w_start > w_end:
                    errors.append(f"{wp}: ngày bắt đầu sau hạn.")
                hours = _number(w.get("estimated_hours"), f"{wp}.estimated_hours", errors, 0, 200, 0)
                minutes_total = int(round(hours * 60))
                week = {
                    "title": _text(w.get("title"), f"{wp}.title", errors, required=True),
                    "description": _text(w.get("description"), f"{wp}.description", errors, max_len=2000),
                    "deadline": w_end,
                    "estimated_minutes": minutes_total,
                    "tasks": [],
                }
                for n, t_item in enumerate(_items(w.get("tasks"), f"{wp}.tasks", errors)):
                    task = _task_item(t_item, f"{wp}.tasks[{n}]", errors, None)
                    if task:
                        week["tasks"].append(task)
                # Tự chia thời lượng đều cho các ngày trong khoảng
                if minutes_total > 0:
                    days = _window_days(w_start, w_end)
                    if not days:
                        errors.append(f"{wp}: không có ngày nào để chia (kiểm tra start và deadline).")
                    else:
                        for day, mins in zip(days, repo.split_minutes(minutes_total, len(days))):
                            if mins > 0:
                                week["tasks"].append({"title": week["title"], "date": day, "minutes": mins,
                                                      "auto": True})
                total_tasks += len(week["tasks"])
                month["weeks"].append(week)

            total_tasks += len(month["tasks"])
            year["months"].append(month)

        years.append(year)

    if total_tasks > MAX_TASKS:
        errors.append(f"Kế hoạch có {total_tasks} nhiệm vụ, vượt giới hạn {MAX_TASKS}. Hãy yêu cầu AI rút gọn.")
    if total_habits > MAX_HABITS:
        errors.append(f"Có {total_habits} thói quen, vượt giới hạn {MAX_HABITS}.")

    # Nhiệm vụ không có ngày sau khi tính: báo lỗi rõ ràng
    for y in years:
        for m in y["months"]:
            for t in m["tasks"] + [t for w in m["weeks"] for t in w["tasks"]]:
                if t["date"] is None:
                    errors.append(f"Nhiệm vụ “{t['title']}”: thiếu ngày.")
                    break

    if errors:
        return None, errors
    return {"years": years, "total_tasks": total_tasks, "total_habits": total_habits}, []


# ============================ BẢN XEM TRƯỚC ============================

def preview_lines(plan: dict) -> list[str]:
    """Các dòng mô tả kế hoạch sẽ được tạo (dùng để hiển thị markdown)."""
    lines = []
    for y in plan["years"]:
        lines.append(f"**🎯 {y['title']}**" + (f" · hạn {y['deadline']:%d/%m/%Y}" if y["deadline"] else ""))
        for m in y["months"]:
            lines.append(f"&nbsp;&nbsp;**🗓️ {m['title']}** · tháng {m['plan_month']}")
            for h in m["habits"]:
                lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;🔁 Thói quen: {h['title']} · {h['minutes']} phút/ngày "
                             f"từ {h['start_date']:%d/%m}")
            for t in m["tasks"]:
                lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;• {t['date']:%d/%m} · {t['title']} · {t['minutes']} phút")
            for w in m["weeks"]:
                auto = sum(1 for t in w["tasks"] if t.get("auto"))
                manual = len(w["tasks"]) - auto
                lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;**📅 {w['title']}** · đến {w['deadline']:%d/%m} · "
                             f"{auto} việc tự chia, {manual} việc cụ thể")
                for t in w["tasks"][:60]:
                    lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {t['date']:%d/%m} · {t['minutes']} phút")
                if len(w["tasks"]) > 60:
                    lines.append(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;… và {len(w['tasks']) - 60} việc nữa")
    return lines


def duplicate_warnings(plan: dict) -> list[str]:
    existing = {g["title"].strip().lower() for g in repo.list_goals("year")}
    return [f"Đã có tầm nhìn năm tên “{y['title']}”. Nếu nhập tiếp, bạn sẽ có hai mục giống nhau."
            for y in plan["years"] if y["title"].strip().lower() in existing]


# ============================ GHI VÀO DATABASE ============================

def _insert_goal(c, level: str, title: str, description: str, parent_id, plan_month, deadline,
                 estimated_minutes: int = 0) -> int:
    cur = c.execute(
        """
        INSERT INTO goals(level, parent_id, title, description, plan_month, deadline,
                          target_value, current_value, unit, status, estimated_minutes, created_at)
        VALUES(?, ?, ?, ?, ?, ?, 100, 0, '%', 'active', ?, ?)
        RETURNING id
        """,
        (level, parent_id, title.strip(), (description or "").strip(), plan_month,
         deadline.isoformat() if deadline else None, int(estimated_minutes), now_iso()),
    )
    return cur.fetchone()["id"]


def _insert_task(c, task: dict, goal_id: int) -> None:
    c.execute(
        "INSERT INTO tasks(title, task_date, duration_minutes, goal_id, done, created_at, habit_id, optional) "
        "VALUES(?, ?, ?, ?, 0, ?, NULL, 0)",
        (task["title"].strip(), task["date"].isoformat(), int(task["minutes"]), goal_id, now_iso()),
    )


def import_plan(plan: dict) -> dict:
    """Ghi toàn bộ kế hoạch trong một giao dịch. Trả về số lượng đã tạo."""
    counts = {"goals": 0, "tasks": 0, "habits": 0}
    with db() as c:
        for y in plan["years"]:
            year_id = _insert_goal(c, "year", y["title"], y["description"], None, None, y["deadline"])
            counts["goals"] += 1
            for m in y["months"]:
                month_id = _insert_goal(c, "month", m["title"], m["description"], year_id,
                                        m["plan_month"], m["deadline"])
                counts["goals"] += 1
                for t in m["tasks"]:
                    _insert_task(c, t, month_id)
                    counts["tasks"] += 1
                for h in m["habits"]:
                    c.execute(
                        "INSERT INTO habits(title, duration_minutes, goal_id, start_date, active, created_at) "
                        "VALUES(?, ?, ?, ?, 1, ?)",
                        (h["title"].strip(), int(h["minutes"]), month_id, h["start_date"].isoformat(), now_iso()),
                    )
                    counts["habits"] += 1
                for w in m["weeks"]:
                    week_id = _insert_goal(c, "week", w["title"], w["description"], month_id, None,
                                           w["deadline"], w["estimated_minutes"])
                    counts["goals"] += 1
                    for t in w["tasks"]:
                        _insert_task(c, t, week_id)
                        counts["tasks"] += 1
    # Tạo nhiệm vụ thói quen cho các ngày đã qua/hôm nay (sau khi giao dịch đã ghi xong)
    repo.ensure_habit_tasks()
    return counts
