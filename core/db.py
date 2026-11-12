"""Kết nối cơ sở dữ liệu.

- Có DATABASE_URL kiểu postgresql://... (Supabase/Neon): dùng PostgreSQL.
- Không có: dùng file SQLite data/personal_os.db (chạy trên máy).

Một kết nối dùng chung được giữ trong tiến trình, có khóa để tránh xung đột giữa các lần chạy.
"""
import sqlite3
import threading
from contextlib import contextmanager

from core.common import DATA_DIR, DB_PATH, get_secret

_lock = threading.RLock()
_conn = None
_dialect = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS profile_years (
    school_year   TEXT PRIMARY KEY,
    major         TEXT NOT NULL DEFAULT '',
    health_status TEXT NOT NULL DEFAULT '',
    health_note   TEXT NOT NULL DEFAULT '',
    dream         TEXT NOT NULL DEFAULT '',
    interests     TEXT NOT NULL DEFAULT '[]',
    gpa           {real},
    updated_at    TEXT
);

CREATE TABLE IF NOT EXISTS goals (
    id            {pk},
    level         TEXT NOT NULL,
    parent_id     INTEGER REFERENCES goals(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    plan_month    TEXT,
    deadline      TEXT,
    target_value  {real} NOT NULL DEFAULT 100,
    current_value {real} NOT NULL DEFAULT 0,
    unit          TEXT NOT NULL DEFAULT '%',
    status        TEXT NOT NULL DEFAULT 'active',
    estimated_minutes INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id               {pk},
    title            TEXT NOT NULL,
    task_date        TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    goal_id          INTEGER REFERENCES goals(id) ON DELETE SET NULL,
    done             INTEGER NOT NULL DEFAULT 0,
    done_at          TEXT,
    created_at       TEXT,
    habit_id         INTEGER,
    optional         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_tasks_date ON tasks(task_date);
CREATE INDEX IF NOT EXISTS idx_tasks_goal ON tasks(goal_id);

CREATE TABLE IF NOT EXISTS habits (
    id               {pk},
    title            TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    goal_id          INTEGER REFERENCES goals(id) ON DELETE SET NULL,
    start_date       TEXT NOT NULL,
    active           INTEGER NOT NULL DEFAULT 1,
    created_at       TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id         {pk},
    title      TEXT NOT NULL,
    body       TEXT NOT NULL DEFAULT '',
    important  INTEGER NOT NULL DEFAULT 0,
    links      TEXT NOT NULL DEFAULT '[]',
    images     TEXT NOT NULL DEFAULT '[]',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS note_images (
    name       TEXT PRIMARY KEY,
    data       {blob} NOT NULL,
    created_at TEXT
);
"""


# Cột mới cho database đã tồn tại. ALTER TABLE ... ADD COLUMN chỉ thêm cột với giá trị mặc định,
# không sửa hay xóa bản ghi hiện có. Cột đã có thì bỏ qua.
ADDED_COLUMNS = [
    ("tasks", "habit_id", "INTEGER"),
    ("tasks", "optional", "INTEGER NOT NULL DEFAULT 0"),
    ("goals", "estimated_minutes", "INTEGER NOT NULL DEFAULT 0"),
]

# Chạy sau khi đã có đủ cột. Index không thay đổi dữ liệu.
POST_MIGRATION_SQL = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_tasks_habit_day ON tasks(habit_id, task_date);
"""


def database_url() -> str:
    return get_secret("DATABASE_URL")


def _is_postgres(url: str) -> bool:
    return url.startswith(("postgres://", "postgresql://"))


def _open() -> None:
    global _conn, _dialect
    url = database_url()
    if _is_postgres(url):
        import psycopg
        from psycopg.rows import dict_row

        # prepare_threshold=None: tương thích với connection pooler (Supabase) ở chế độ transaction.
        _conn = psycopg.connect(url, autocommit=False, row_factory=dict_row, prepare_threshold=None)
        _dialect = "postgres"
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
        _dialect = "sqlite"


class Conn:
    """Bọc kết nối để dùng cùng một kiểu SQL: dấu ? ở mọi nơi, tự đổi sang %s khi dùng Postgres."""

    def __init__(self, raw, dialect: str):
        self.raw = raw
        self.dialect = dialect

    def execute(self, sql: str, params=()):
        cur = self.raw.cursor()
        if not params:
            cur.execute(sql)
        else:
            if self.dialect == "postgres":
                sql = sql.replace("%", "%%").replace("?", "%s")
            cur.execute(sql, tuple(params))
        return cur


@contextmanager
def db():
    """Mở giao dịch: tự commit khi thành công, rollback khi có lỗi."""
    with _lock:
        if _conn is None or getattr(_conn, "closed", False):
            _open()
        conn = Conn(_conn, _dialect)
        try:
            yield conn
            _conn.commit()
        except Exception:
            _conn.rollback()
            raise


def dialect() -> str:
    if _conn is None:
        _open()
    return _dialect


def init_db() -> None:
    with _lock:
        if _conn is None or getattr(_conn, "closed", False):
            _open()
        if _dialect == "postgres":
            fmt = {"pk": "SERIAL PRIMARY KEY", "real": "DOUBLE PRECISION", "blob": "BYTEA"}
        else:
            fmt = {"pk": "INTEGER PRIMARY KEY AUTOINCREMENT", "real": "REAL", "blob": "BLOB"}
        with db() as c:
            for statement in SCHEMA.format(**fmt).split(";"):
                if statement.strip():
                    c.execute(statement)
            for table, column, ddl in ADDED_COLUMNS:
                if column not in _existing_columns(c, table):
                    c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")
            for statement in POST_MIGRATION_SQL.split(";"):
                if statement.strip():
                    c.execute(statement)


def _existing_columns(c, table: str) -> set[str]:
    if c.dialect == "postgres":
        rows = c.execute(
            "SELECT column_name AS name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = ?",
            (table,),
        ).fetchall()
    else:
        rows = c.execute(f"PRAGMA table_info({table})").fetchall()
    return {r["name"] for r in rows}
