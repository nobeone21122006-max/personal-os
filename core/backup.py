"""Sao lưu và xuất dữ liệu. Chỉ đọc database, không ghi gì."""
import base64
import csv
import io
import json

from core.common import now_iso, today
from core.db import db

BACKUP_FORMAT = "personal-os-backup"
BACKUP_VERSION = 2
TABLES = ["settings", "profile_years", "goals", "tasks", "habits", "notes"]


def _all_rows(table: str) -> list[dict]:
    order = "ORDER BY id" if table not in ("settings", "profile_years") else ""
    with db() as c:
        return [dict(r) for r in c.execute(f"SELECT * FROM {table} {order}").fetchall()]


def _image_rows() -> list[dict]:
    with db() as c:
        rows = c.execute("SELECT name, data, created_at FROM note_images ORDER BY name").fetchall()
    return [{"name": r["name"], "created_at": r["created_at"],
             "data_base64": base64.b64encode(bytes(r["data"])).decode("ascii")} for r in rows]


def build_backup_json() -> bytes:
    """Toàn bộ dữ liệu (kể cả ảnh ghi chú dạng base64) trong một file JSON."""
    tables = {name: _all_rows(name) for name in TABLES}
    payload = {
        "format": BACKUP_FORMAT,
        "version": BACKUP_VERSION,
        "exported_at": now_iso(),
        "tables": tables,
        "note_images": _image_rows(),
    }
    return json.dumps(payload, ensure_ascii=False, indent=1, default=str).encode("utf-8")


def _goal_titles() -> dict[int, str]:
    with db() as c:
        return {r["id"]: r["title"] for r in c.execute("SELECT id, title FROM goals").fetchall()}


def _habit_titles() -> dict[int, str]:
    with db() as c:
        return {r["id"]: r["title"] for r in c.execute("SELECT id, title FROM habits").fetchall()}


def _csv_bytes(header: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    writer.writerows(rows)
    # utf-8-sig để Excel đọc đúng tiếng Việt
    return buf.getvalue().encode("utf-8-sig")


def tasks_csv() -> bytes:
    goals = _goal_titles()
    habits = _habit_titles()
    with db() as c:
        rows = c.execute("SELECT * FROM tasks ORDER BY task_date, id").fetchall()
    data = [[
        r["task_date"], r["title"], r["duration_minutes"],
        goals.get(r["goal_id"], ""), habits.get(r["habit_id"], "") if r["habit_id"] else "",
        "xong" if r["done"] else "chưa", "tùy chọn" if r["optional"] else "",
        r["done_at"] or "",
    ] for r in rows]
    return _csv_bytes(["Ngày", "Nhiệm vụ", "Thời lượng (phút)", "Mục tiêu", "Thói quen",
                       "Trạng thái", "Loại", "Hoàn thành lúc"], data)


def goals_csv() -> bytes:
    with db() as c:
        rows = c.execute("SELECT * FROM goals ORDER BY level, id").fetchall()
    titles = {r["id"]: r["title"] for r in rows}
    level_names = {"year": "Tầm nhìn năm", "month": "Kế hoạch tháng", "week": "Ưu tiên tuần"}
    data = [[
        level_names.get(r["level"], r["level"]), r["title"], titles.get(r["parent_id"], ""),
        r["plan_month"] or "", r["deadline"] or "", r["status"],
        r["target_value"], r["current_value"], r["unit"], r["estimated_minutes"] or 0,
    ] for r in rows]
    return _csv_bytes(["Cấp", "Tên", "Thuộc", "Tháng", "Hạn", "Trạng thái", "Mục tiêu số",
                       "Tiến độ nhập tay", "Đơn vị", "Thời lượng dự kiến (phút)"], data)


def file_stamp() -> str:
    return today().isoformat()
