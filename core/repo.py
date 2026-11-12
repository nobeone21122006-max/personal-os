"""Tầng truy cập dữ liệu. Toàn bộ thao tác với SQLite/PostgreSQL nằm ở đây để các trang UI gọn."""
import json
import re
import uuid
from datetime import date, timedelta

from core.common import current_school_year, month_bounds, now_iso, today
from core.db import db

DEFAULT_REST_DAYS = [6]
DEFAULT_FREE_HOURS = 3.0

# Nhiệm vụ thói quen trong ngày nghỉ là "tùy chọn": chỉ được tính khi đã làm.
COUNTABLE_SQL = "(optional = 0 OR done = 1)"


# ============================ SETTINGS ============================

def get_setting(key: str, default=None):
    with db() as c:
        row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row and row["value"] is not None else default


def set_setting(key: str, value) -> None:
    with db() as c:
        c.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


def is_onboarded() -> bool:
    return get_setting("onboarded") == "1"


def get_name() -> str:
    return get_setting("name", "") or ""


def get_free_hours() -> float:
    return float(get_setting("free_hours", DEFAULT_FREE_HOURS))


def get_rest_days() -> list[int]:
    return json.loads(get_setting("rest_days", json.dumps(DEFAULT_REST_DAYS)))


def get_telegram_chat_id() -> str:
    return get_setting("telegram_chat_id", "") or ""


# ============================ PROFILE (theo năm học) ============================

def _profile_row(row) -> dict:
    data = dict(row)
    data["interests"] = json.loads(data.get("interests") or "[]")
    return data


def list_profile_years() -> list[dict]:
    with db() as c:
        rows = c.execute("SELECT * FROM profile_years ORDER BY school_year DESC").fetchall()
    return [_profile_row(r) for r in rows]


def get_profile(school_year: str) -> dict | None:
    with db() as c:
        row = c.execute("SELECT * FROM profile_years WHERE school_year = ?", (school_year,)).fetchone()
    return _profile_row(row) if row else None


def latest_profile() -> dict | None:
    years = list_profile_years()
    return years[0] if years else None


def save_profile(school_year: str, data: dict) -> None:
    interests = json.dumps(sorted(set(data.get("interests") or []), key=str.lower), ensure_ascii=False)
    with db() as c:
        c.execute(
            """
            INSERT INTO profile_years(school_year, major, health_status, health_note, dream, interests, gpa, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(school_year) DO UPDATE SET
                major = excluded.major,
                health_status = excluded.health_status,
                health_note = excluded.health_note,
                dream = excluded.dream,
                interests = excluded.interests,
                gpa = excluded.gpa,
                updated_at = excluded.updated_at
            """,
            (
                school_year,
                (data.get("major") or "").strip(),
                (data.get("health_status") or "").strip(),
                (data.get("health_note") or "").strip(),
                (data.get("dream") or "").strip(),
                interests,
                data.get("gpa"),
                now_iso(),
            ),
        )


def complete_onboarding(name: str, profile_data: dict) -> None:
    save_profile(current_school_year(), profile_data)
    set_setting("name", name.strip())
    set_setting("onboarded", "1")


def update_personal_settings(name: str, free_hours: float, rest_days: list[int], telegram_chat_id: str) -> None:
    set_setting("name", name.strip())
    set_setting("free_hours", free_hours)
    set_setting("rest_days", json.dumps(sorted(rest_days)))
    set_setting("telegram_chat_id", telegram_chat_id.strip())


# ============================ GOALS (4 cấp) ============================

LEVEL_LABELS = {"year": "Tầm nhìn năm", "month": "Kế hoạch tháng", "week": "Ưu tiên tuần"}


def create_goal(
    level: str,
    title: str,
    description: str = "",
    parent_id: int | None = None,
    plan_month: str | None = None,
    deadline: date | None = None,
    target_value: float = 100.0,
    unit: str = "%",
    estimated_minutes: int = 0,
) -> int:
    with db() as c:
        cur = c.execute(
            """
            INSERT INTO goals(level, parent_id, title, description, plan_month, deadline,
                              target_value, current_value, unit, status, estimated_minutes, created_at)
            VALUES(?, ?, ?, ?, ?, ?, ?, 0, ?, 'active', ?, ?)
            RETURNING id
            """,
            (
                level,
                parent_id,
                title.strip(),
                description.strip(),
                plan_month,
                deadline.isoformat() if deadline else None,
                target_value,
                unit,
                int(estimated_minutes or 0),
                now_iso(),
            ),
        )
        return cur.fetchone()["id"]


def list_goals(level: str | None = None) -> list[dict]:
    sql = "SELECT * FROM goals"
    params: tuple = ()
    if level:
        sql += " WHERE level = ?"
        params = (level,)
    sql += " ORDER BY COALESCE(plan_month, deadline, created_at), id"
    with db() as c:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def get_goal(goal_id: int) -> dict | None:
    with db() as c:
        row = c.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
    return dict(row) if row else None


def children_of(goal_id: int) -> list[dict]:
    with db() as c:
        rows = c.execute(
            "SELECT * FROM goals WHERE parent_id = ? ORDER BY COALESCE(plan_month, deadline, created_at), id",
            (goal_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_goal(goal_id: int, **fields) -> None:
    allowed = {"title", "description", "status", "current_value", "target_value", "unit", "plan_month",
               "deadline", "estimated_minutes"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    assignments = ", ".join(f"{k} = ?" for k in fields)
    with db() as c:
        c.execute(f"UPDATE goals SET {assignments} WHERE id = ?", (*fields.values(), goal_id))


def delete_goal(goal_id: int) -> None:
    with db() as c:
        c.execute("DELETE FROM goals WHERE id = ?", (goal_id,))


def _family_ids(goal: dict) -> list[int]:
    """Một kế hoạch tháng gồm chính nó và các ưu tiên tuần con."""
    ids = [goal["id"]]
    if goal["level"] == "month":
        ids += [child["id"] for child in children_of(goal["id"])]
    return ids


def _task_counts(goal_ids: list[int]) -> tuple[int, int]:
    if not goal_ids:
        return 0, 0
    placeholders = ",".join("?" for _ in goal_ids)
    with db() as c:
        row = c.execute(
            f"SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks "
            f"WHERE goal_id IN ({placeholders}) AND {COUNTABLE_SQL}",
            tuple(goal_ids),
        ).fetchone()
    return int(row["done"]), int(row["total"])


def goal_progress(goal: dict) -> float:
    """Tiến độ 0..1.

    - Tầm nhìn năm: trung bình tiến độ các kế hoạch tháng con (nếu có), nếu không dùng giá trị nhập tay.
    - Kế hoạch tháng / ưu tiên tuần: tỷ lệ nhiệm vụ đã xong; nếu chưa có nhiệm vụ thì dùng giá trị nhập tay.
    """
    if goal["level"] == "year":
        kids = children_of(goal["id"])
        if kids:
            return sum(goal_progress(k) for k in kids) / len(kids)
    else:
        done, total = _task_counts(_family_ids(goal))
        if total:
            return done / total
    target = goal.get("target_value") or 0
    if target <= 0:
        return 0.0
    return max(0.0, min(1.0, float(goal.get("current_value") or 0) / float(target)))


def goal_task_summary(goal: dict) -> tuple[int, int]:
    return _task_counts(_family_ids(goal))


# ============================ TRẠNG THÁI THEO THÁNG ============================

def month_overview(year: int, month: int, plan_id: int | None = None) -> dict:
    """Trạng thái từng ngày trong tháng. Nếu có plan_id thì chỉ tính nhiệm vụ của kế hoạch đó."""
    start, end = month_bounds(year, month)
    where = ["task_date BETWEEN ? AND ?", COUNTABLE_SQL]
    params: list = [start.isoformat(), end.isoformat()]
    if plan_id is not None:
        plan = get_goal(plan_id)
        ids = _family_ids(plan) if plan else []
        if not ids:
            return _empty_overview(year, month)
        where.append(f"goal_id IN ({','.join('?' for _ in ids)})")
        params += ids

    with db() as c:
        rows = c.execute(
            f"""
            SELECT task_date, COUNT(*) AS total, COALESCE(SUM(done), 0) AS done
            FROM tasks
            WHERE {' AND '.join(where)}
            GROUP BY task_date
            """,
            tuple(params),
        ).fetchall()
    by_day = {r["task_date"]: (int(r["total"]), int(r["done"])) for r in rows}

    today_d = today()
    days = []
    total_all = done_all = 0
    for day_no in range(1, end.day + 1):
        d = date(year, month, day_no)
        total, done = by_day.get(d.isoformat(), (0, 0))
        total_all += total
        done_all += done
        rate = (done / total * 100) if total else 0.0
        days.append({
            "day": day_no, "date": d, "weekday": d.weekday(),
            "total": total, "done": done, "rate": rate,
            "future": d > today_d,
        })

    return {
        "days": days,
        "monthly_average": (done_all / total_all * 100) if total_all else 0.0,
        "total": total_all,
        "done": done_all,
        "perfect_days": sum(1 for d in days if d["total"] and d["rate"] >= 100),
        "active_days": sum(1 for d in days if d["total"]),
    }


def _empty_overview(year: int, month: int) -> dict:
    return month_overview_from_rows(year, month, {})


def month_overview_from_rows(year: int, month: int, by_day: dict) -> dict:
    start, end = month_bounds(year, month)
    today_d = today()
    days = []
    for day_no in range(1, end.day + 1):
        d = date(year, month, day_no)
        total, done = by_day.get(d.isoformat(), (0, 0))
        rate = (done / total * 100) if total else 0.0
        days.append({"day": day_no, "date": d, "weekday": d.weekday(), "total": total,
                     "done": done, "rate": rate, "future": d > today_d})
    return {"days": days, "monthly_average": 0.0, "total": 0, "done": 0,
            "perfect_days": 0, "active_days": 0}


def monthly_tracker(plan: dict) -> dict:
    """Trạng thái tháng của một kế hoạch tháng."""
    year, month = (int(part) for part in plan["plan_month"].split("-"))
    return month_overview(year, month, plan["id"])


# ============================ TASKS (hành động ngày) ============================

def add_task(
    title: str,
    task_date: date,
    duration_minutes: int,
    goal_id: int | None = None,
    habit_id: int | None = None,
    optional: bool = False,
) -> int:
    with db() as c:
        cur = c.execute(
            "INSERT INTO tasks(title, task_date, duration_minutes, goal_id, done, created_at, habit_id, optional) "
            "VALUES(?, ?, ?, ?, 0, ?, ?, ?) RETURNING id",
            (title.strip(), task_date.isoformat(), int(duration_minutes), goal_id, now_iso(),
             habit_id, 1 if optional else 0),
        )
        return cur.fetchone()["id"]


def get_task(task_id: int) -> dict | None:
    with db() as c:
        row = c.execute(
            "SELECT t.*, g.title AS goal_title, g.level AS goal_level "
            "FROM tasks t LEFT JOIN goals g ON g.id = t.goal_id WHERE t.id = ?",
            (task_id,),
        ).fetchone()
    return dict(row) if row else None


def tasks_on(task_date: date) -> list[dict]:
    with db() as c:
        rows = c.execute(
            """
            SELECT t.*, g.title AS goal_title, g.level AS goal_level
            FROM tasks t LEFT JOIN goals g ON g.id = t.goal_id
            WHERE t.task_date = ?
            ORDER BY t.done ASC, t.id ASC
            """,
            (task_date.isoformat(),),
        ).fetchall()
    return [dict(r) for r in rows]


def tasks_for_goal(goal_id: int) -> list[dict]:
    with db() as c:
        rows = c.execute(
            "SELECT * FROM tasks WHERE goal_id = ? ORDER BY task_date, id", (goal_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def tasks_for_goal_in_range(goal_id: int, start: date, end: date) -> list[dict]:
    with db() as c:
        rows = c.execute(
            "SELECT * FROM tasks WHERE goal_id = ? AND task_date BETWEEN ? AND ?",
            (goal_id, start.isoformat(), end.isoformat()),
        ).fetchall()
    return [dict(r) for r in rows]


def update_task(task_id: int, title: str, duration_minutes: int, goal_id: int | None,
                task_date: date | None = None) -> None:
    """Sửa một nhiệm vụ. Chỉ truyền task_date với nhiệm vụ thường (không đổi ngày của thói quen)."""
    fields: dict = {
        "title": title.strip(),
        "duration_minutes": int(duration_minutes),
        "goal_id": goal_id,
    }
    if task_date is not None:
        fields["task_date"] = task_date.isoformat()
    assignments = ", ".join(f"{k} = ?" for k in fields)
    with db() as c:
        c.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", (*fields.values(), task_id))


def set_task_done(task_id: int, done: bool) -> None:
    with db() as c:
        c.execute(
            "UPDATE tasks SET done = ?, done_at = ? WHERE id = ?",
            (1 if done else 0, now_iso() if done else None, task_id),
        )


def delete_task(task_id: int) -> None:
    with db() as c:
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


# ============================ THÓI QUEN (tự tạo nhiệm vụ mỗi ngày) ============================

def _habit_row(row) -> dict:
    data = dict(row)
    data["active"] = bool(data.get("active"))
    return data


def list_habits(active_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM habits"
    if active_only:
        sql += " WHERE active = 1"
    sql += " ORDER BY active DESC, id"
    with db() as c:
        return [_habit_row(r) for r in c.execute(sql).fetchall()]


def get_habit(habit_id: int) -> dict | None:
    with db() as c:
        row = c.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
    return _habit_row(row) if row else None


def create_habit(title: str, duration_minutes: int, goal_id: int | None, start_date: date) -> int:
    with db() as c:
        cur = c.execute(
            "INSERT INTO habits(title, duration_minutes, goal_id, start_date, active, created_at) "
            "VALUES(?, ?, ?, ?, 1, ?) RETURNING id",
            (title.strip(), int(duration_minutes), goal_id, start_date.isoformat(), now_iso()),
        )
        habit_id = cur.fetchone()["id"]
    ensure_habit_tasks(habit_id)
    return habit_id


def update_habit(habit_id: int, title: str, duration_minutes: int, goal_id: int | None) -> None:
    """Đổi thông tin thói quen. Chỉ áp dụng cho nhiệm vụ từ hôm nay trở đi và chưa làm.
    Các ngày đã qua và nhiệm vụ đã xong giữ nguyên."""
    with db() as c:
        c.execute(
            "UPDATE habits SET title = ?, duration_minutes = ?, goal_id = ? WHERE id = ?",
            (title.strip(), int(duration_minutes), goal_id, habit_id),
        )
        c.execute(
            "UPDATE tasks SET title = ?, duration_minutes = ?, goal_id = ? "
            "WHERE habit_id = ? AND task_date >= ? AND done = 0",
            (title.strip(), int(duration_minutes), goal_id, habit_id, today().isoformat()),
        )


def set_habit_active(habit_id: int, active: bool) -> None:
    """Dừng: không tạo thêm nhiệm vụ và xóa các nhiệm vụ tương lai chưa làm. Lịch sử được giữ lại."""
    with db() as c:
        c.execute("UPDATE habits SET active = ? WHERE id = ?", (1 if active else 0, habit_id))
        if not active:
            c.execute(
                "DELETE FROM tasks WHERE habit_id = ? AND task_date > ? AND done = 0",
                (habit_id, today().isoformat()),
            )
    if active:
        ensure_habit_tasks(habit_id)


def ensure_habit_tasks(habit_id: int | None = None) -> int:
    """Tạo nhiệm vụ còn thiếu cho thói quen đang bật, từ ngày bắt đầu đến hôm nay.

    Mỗi thói quen có đúng một nhiệm vụ mỗi ngày. Ngày nghỉ vẫn được tạo nhưng là tùy chọn.
    Gọi nhiều lần vẫn an toàn: ngày đã có thì bỏ qua. Trả về số nhiệm vụ mới được tạo.
    """
    habits = [get_habit(habit_id)] if habit_id else list_habits(active_only=True)
    habits = [h for h in habits if h and h["active"]]
    if not habits:
        return 0

    end = today()
    rest = set(get_rest_days())
    created = 0
    for habit in habits:
        start = date.fromisoformat(habit["start_date"])
        if start > end:
            continue
        with db() as c:
            existing = {
                r["task_date"]
                for r in c.execute(
                    "SELECT task_date FROM tasks WHERE habit_id = ? AND task_date BETWEEN ? AND ?",
                    (habit["id"], start.isoformat(), end.isoformat()),
                ).fetchall()
            }
            day = start
            while day <= end:
                if day.isoformat() not in existing:
                    c.execute(
                        "INSERT INTO tasks(title, task_date, duration_minutes, goal_id, done, created_at, "
                        "habit_id, optional) VALUES(?, ?, ?, ?, 0, ?, ?, ?)",
                        (habit["title"], day.isoformat(), habit["duration_minutes"], habit["goal_id"],
                         now_iso(), habit["id"], 1 if day.weekday() in rest else 0),
                    )
                    created += 1
                day += timedelta(days=1)
    return created


def habit_stats(habit_id: int) -> tuple[int, int]:
    """(số lần đã làm, số lần cần làm) từ đầu đến hôm nay. Ngày nghỉ tùy chọn chưa làm không tính."""
    with db() as c:
        row = c.execute(
            f"SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks "
            f"WHERE habit_id = ? AND task_date <= ? AND {COUNTABLE_SQL}",
            (habit_id, today().isoformat()),
        ).fetchone()
    return int(row["done"]), int(row["total"])


# ============================ LẬP LỊCH ƯU TIÊN TUẦN ============================

def _split_minutes(total_minutes: int, parts: int) -> list[int]:
    """Chia tổng thời lượng đều cho các ngày, làm tròn theo 5 phút. Các ngày đầu nhận phần dư."""
    if parts <= 0 or total_minutes <= 0:
        return []
    units = max(1, round(total_minutes / 5))
    base, extra = divmod(units, parts)
    return [(base + (1 if i < extra else 0)) * 5 for i in range(parts)]


split_minutes = _split_minutes  # dùng chung cho nhập kế hoạch


def week_plan_days(goal: dict) -> list[date]:
    """Các ngày có thể làm ưu tiên tuần: từ hôm nay đến hạn. Ưu tiên ngày làm việc,
    chỉ dùng ngày nghỉ khi khoảng thời gian không còn ngày làm việc nào."""
    if not goal.get("deadline"):
        return []
    start = today()
    end = date.fromisoformat(goal["deadline"])
    if end < start:
        return []
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    rest = set(get_rest_days())
    working = [d for d in days if d.weekday() not in rest]
    return working or days


def build_week_plan(goal: dict, total_minutes: int) -> list[tuple[date, int]]:
    """Kế hoạch chia đều (chưa lưu): danh sách (ngày, phút)."""
    days = week_plan_days(goal)
    minutes = _split_minutes(total_minutes, len(days))
    return [(d, m) for d, m in zip(days, minutes) if m > 0]


def plan_week_auto(goal_id: int, total_minutes: int) -> int:
    """Chia đều thời lượng ưu tiên tuần và tạo một nhiệm vụ cho mỗi ngày. Trả về số nhiệm vụ đã tạo."""
    goal = get_goal(goal_id)
    if not goal or goal["level"] != "week":
        raise ValueError("Không tìm thấy ưu tiên tuần.")
    if total_minutes <= 0:
        raise ValueError("Vui lòng nhập tổng thời lượng dự kiến lớn hơn 0.")
    plan = build_week_plan(goal, total_minutes)
    if not plan:
        raise ValueError("Hạn của ưu tiên đã qua hoặc chưa đặt. Hãy cập nhật hạn trước khi lập lịch.")
    if tasks_for_goal_in_range(goal_id, plan[0][0], plan[-1][0]):
        raise ValueError("Ưu tiên này đã có nhiệm vụ trong khoảng thời gian đó. Hãy sửa hoặc xóa chúng trước.")

    update_goal(goal_id, estimated_minutes=int(total_minutes))
    for day, minutes in plan:
        add_task(goal["title"], day, minutes, goal_id)
    return len(plan)


# ============================ NOTES ============================

def parse_links(text: str) -> list[dict]:
    """Mỗi dòng: 'Tên hiển thị | https://...' hoặc chỉ 'https://...'."""
    links = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if "|" in line:
            label, url = (part.strip() for part in line.split("|", 1))
        else:
            label, url = "", line
        if not url:
            continue
        if not url.lower().startswith(("http://", "https://")):
            url = "https://" + url
        links.append({"label": label or url, "url": url})
    return links


def _note_row(row) -> dict:
    data = dict(row)
    data["links"] = json.loads(data.get("links") or "[]")
    data["images"] = json.loads(data.get("images") or "[]")
    data["important"] = bool(data.get("important"))
    return data


def list_notes(search: str = "", important_only: bool = False) -> list[dict]:
    sql = "SELECT * FROM notes WHERE 1=1"
    params: list = []
    if important_only:
        sql += " AND important = 1"
    if search.strip():
        sql += " AND (title LIKE ? OR body LIKE ?)"
        like = f"%{search.strip()}%"
        params += [like, like]
    sql += " ORDER BY important DESC, updated_at DESC, id DESC"
    with db() as c:
        return [_note_row(r) for r in c.execute(sql, params).fetchall()]


def create_note(title: str, body: str, important: bool, links: list[dict], images: list[str]) -> int:
    with db() as c:
        cur = c.execute(
            """
            INSERT INTO notes(title, body, important, links, images, created_at, updated_at)
            VALUES(?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                title.strip(), body.strip(), 1 if important else 0,
                json.dumps(links, ensure_ascii=False), json.dumps(images),
                now_iso(), now_iso(),
            ),
        )
        return cur.fetchone()["id"]


def update_note(note_id: int, title: str, body: str, important: bool, links: list[dict], images: list[str]) -> None:
    with db() as c:
        c.execute(
            """
            UPDATE notes SET title = ?, body = ?, important = ?, links = ?, images = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                title.strip(), body.strip(), 1 if important else 0,
                json.dumps(links, ensure_ascii=False), json.dumps(images), now_iso(), note_id,
            ),
        )


def get_note(note_id: int) -> dict | None:
    with db() as c:
        row = c.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return _note_row(row) if row else None


def delete_note(note_id: int) -> None:
    note = get_note(note_id)
    if note:
        for name in note["images"]:
            delete_image_file(name)
    with db() as c:
        c.execute("DELETE FROM notes WHERE id = ?", (note_id,))


ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def save_image(file_name: str, data: bytes) -> str:
    """Lưu ảnh vào bảng note_images (trong database, không phụ thuộc ổ đĩa). Trả về tên đã lưu."""
    from pathlib import Path

    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise ValueError("Chỉ chấp nhận ảnh PNG, JPG, WEBP hoặc GIF.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Ảnh vượt quá 5 MB.")
    stored = f"{uuid.uuid4().hex}{ext}"
    with db() as c:
        c.execute(
            "INSERT INTO note_images(name, data, created_at) VALUES(?, ?, ?)",
            (stored, data, now_iso()),
        )
    return stored


def image_bytes(name: str) -> bytes | None:
    with db() as c:
        row = c.execute("SELECT data FROM note_images WHERE name = ?", (name,)).fetchone()
    return bytes(row["data"]) if row else None


def delete_image_file(name: str) -> None:
    with db() as c:
        c.execute("DELETE FROM note_images WHERE name = ?", (name,))


# ============================ SỬA MỤC TIÊU ĐẦY ĐỦ ============================

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def update_goal_details(
    goal_id: int,
    *,
    title: str,
    description: str = "",
    deadline: date | None = None,
    plan_month: str | None = None,
    parent_id: int | None = None,
    target_value: float = 100.0,
    unit: str = "%",
    estimated_minutes: int = 0,
    status: str = "active",
    current_value: float = 0.0,
) -> None:
    """Sửa toàn bộ thông tin một mục tiêu. Kiểm tra cấp cha đúng cấp (kế hoạch tháng -> năm, tuần -> tháng).
    Không đổi cấp của mục tiêu và không xóa nhiệm vụ đã gắn."""
    goal = get_goal(goal_id)
    if not goal:
        raise ValueError("Không tìm thấy mục tiêu.")
    if not (title or "").strip():
        raise ValueError("Vui lòng nhập tên mục tiêu.")
    level = goal["level"]

    if level == "month":
        if not plan_month or not MONTH_RE.match(plan_month):
            raise ValueError("Kế hoạch tháng cần một tháng hợp lệ.")
        parent = get_goal(parent_id) if parent_id else None
        if not parent or parent["level"] != "year":
            raise ValueError("Kế hoạch tháng phải thuộc một tầm nhìn năm.")
        estimated_minutes = 0
    elif level == "week":
        plan_month = None
        parent = get_goal(parent_id) if parent_id else None
        if not parent or parent["level"] != "month":
            raise ValueError("Ưu tiên tuần phải thuộc một kế hoạch tháng.")
    else:
        plan_month = None
        parent_id = None
        estimated_minutes = 0

    if level != "week":
        estimated_minutes = 0
    with db() as c:
        c.execute(
            """
            UPDATE goals SET title = ?, description = ?, deadline = ?, plan_month = ?, parent_id = ?,
                target_value = ?, unit = ?, estimated_minutes = ?, status = ?, current_value = ?
            WHERE id = ?
            """,
            (
                title.strip(), (description or "").strip(),
                deadline.isoformat() if deadline else None,
                plan_month, parent_id, float(target_value), (unit or "%").strip() or "%",
                int(estimated_minutes or 0), status, float(current_value or 0.0), goal_id,
            ),
        )
