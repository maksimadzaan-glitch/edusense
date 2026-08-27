from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# .env рядом с корнем проекта
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = "sqlite:///./edusense.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_columns() -> None:
    """Добавляет новые колонки в уже существующие SQLite-таблицы (без Alembic)."""
    specs: dict[str, list[tuple[str, str]]] = {
        # Legacy auth: старые БД создавались без subject → INSERT в /api/register давал 500
        "users": [
            ("subject", "VARCHAR"),
        ],
        "assignments": [
            ("shuffle_variants", "INTEGER NOT NULL DEFAULT 0"),
            ("accepting_submissions", "INTEGER NOT NULL DEFAULT 1"),
            ("expected_students", "INTEGER"),
            ("difficulty", "VARCHAR(20)"),
            ("settings_json", "TEXT"),
        ],
        "submissions": [
            ("started_at", "DATETIME"),
            ("teacher_score", "REAL"),
            ("teacher_comment", "TEXT"),
            ("teacher_reviewed_at", "DATETIME"),
        ],
    }
    with engine.begin() as conn:
        for table, columns in specs.items():
            try:
                rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            except Exception:
                continue
            # Пустой PRAGMA = таблицы ещё нет (create_all создаст её с нужными колонками)
            if not rows:
                continue
            existing = {r[1] for r in rows}
            for name, ddl in columns:
                if name in existing:
                    continue
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
