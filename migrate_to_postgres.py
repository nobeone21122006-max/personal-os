"""Chuyển dữ liệu từ SQLite cục bộ (data/personal_os.db) sang database đích.

Cách dùng (đặt DATABASE_URL trỏ tới Supabase/Neon trước khi chạy):
  export DATABASE_URL="postgresql://..."
  python migrate_to_postgres.py --source data/personal_os.db --uploads data/uploads

Chạy trên database trống. Script dừng nếu phát hiện đã có dữ liệu, để tránh nhân đôi.
"""
import argparse
import sqlite3
from pathlib import Path

from core.db import db, dialect, init_db

LEVEL_ORDER = {"year": 0, "month": 1, "week": 2}


def _rows(src: sqlite3.Connection, table: str) -> list[dict]:
    src.row_factory = sqlite3.Row
    return [dict(r) for r in src.execute(f"SELECT * FROM {table}").fetchall()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="data/personal_os.db")
    parser.add_argument("--uploads", default="data/uploads")
    args = parser.parse_args()

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Không tìm thấy file nguồn: {source_path}")
        return 1

    init_db()
    src = sqlite3.connect(source_path)

    with db() as c:
        existing = c.execute("SELECT COUNT(*) AS n FROM goals").fetchone()["n"]
        existing += c.execute("SELECT COUNT(*) AS n FROM notes").fetchone()["n"]
    if existing:
        print("Database đích đã có dữ liệu. Hãy dùng database trống để tránh nhân đôi.")
        return 1

    settings = _rows(src, "settings")
    profiles = _rows(src, "profile_years")
    goals = sorted(_rows(src, "goals"), key=lambda g: (LEVEL_ORDER.get(g["level"], 9), g["id"]))
    tasks = _rows(src, "tasks")
    notes = _rows(src, "notes")

    with db() as c:
        for s in settings:
            c.execute("INSERT INTO settings(key, value) VALUES(?, ?)", (s["key"], s["value"]))
        for p in profiles:
            c.execute(
                """INSERT INTO profile_years(school_year, major, health_status, health_note, dream,
                   interests, gpa, updated_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                (p["school_year"], p["major"], p["health_status"], p["health_note"], p["dream"],
                 p["interests"], p["gpa"], p["updated_at"]),
            )
        for g in goals:
            c.execute(
                """INSERT INTO goals(id, level, parent_id, title, description, plan_month, deadline,
                   target_value, current_value, unit, status, created_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (g["id"], g["level"], g["parent_id"], g["title"], g["description"], g["plan_month"],
                 g["deadline"], g["target_value"], g["current_value"], g["unit"], g["status"], g["created_at"]),
            )
        for t in tasks:
            c.execute(
                """INSERT INTO tasks(id, title, task_date, duration_minutes, goal_id, done, done_at, created_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                (t["id"], t["title"], t["task_date"], t["duration_minutes"], t["goal_id"],
                 t["done"], t["done_at"], t["created_at"]),
            )
        image_count = 0
        for n in notes:
            c.execute(
                """INSERT INTO notes(id, title, body, important, links, images, created_at, updated_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                (n["id"], n["title"], n["body"], n["important"], n["links"], n["images"],
                 n["created_at"], n["updated_at"]),
            )
            for name in __import__("json").loads(n["images"] or "[]"):
                file_path = Path(args.uploads) / name
                if file_path.exists():
                    c.execute("INSERT INTO note_images(name, data, created_at) VALUES(?, ?, ?)",
                              (name, file_path.read_bytes(), n["created_at"]))
                    image_count += 1

        # Với PostgreSQL, cập nhật bộ đếm id để các bản ghi mới không trùng id đã chuyển.
        if dialect() == "postgres":
            for table in ("goals", "tasks", "notes"):
                c.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1))"
                )

    src.close()
    print(f"Đã chuyển: {len(settings)} cài đặt, {len(profiles)} năm học, {len(goals)} mục tiêu, "
          f"{len(tasks)} nhiệm vụ, {len(notes)} ghi chú, {image_count} ảnh.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
