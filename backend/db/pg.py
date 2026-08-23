"""Sync SQLAlchemy engine/session для PostgreSQL (universal).

Стек проекта — sync SQLAlchemy + SQLite; asyncpg/asyncio здесь не используем,
чтобы не ломать существующий FastAPI Depends(get_db). Драйвер: psycopg v3.

Env:
  POSTGRES_URL=postgresql+psycopg://user:pass@localhost:5432/edusense_universal
  (также принимается postgresql://... — префикс нормализуется к +psycopg)
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")


def _normalize_postgres_url(url: str) -> str:
    url = url.strip()
    if not url:
        return url
    # Разрешаем корот<fim-middle>кие формы из docker/docs
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql+asyncpg://"):
        # sync-стек: подменяем async-драйвер на psycopg
        return "postgresql+psycopg://" + url[len("postgresql+asyncpg://") :]
    return url


def get_postgres_url() -> str | None:
    raw = (os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL_PG") or "").strip()
    if not raw:
        return None
    return _normalize_postgres_url(raw)


def is_postgres_configured() -> bool:
    return bool(get_postgres_url())


class PgBase(DeclarativeBase):
    """Отдельный metadata от SQLite Base — таблицы universal не смешиваются с edusense.db."""


_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def pg_engine() -> Engine:
    global _engine, _SessionLocal
    url = get_postgres_url()
    if not url:
        raise RuntimeError(
            "POSTGRES_URL не задан. Добавьте в .env, например: "
            "POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:5432/edusense_universal"
        )
    if _engine is None:
        _engine = create_engine(url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_pg_session() -> Generator[Session, None, None]:
    pg_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def session_factory() -> sessionmaker[Session]:
    pg_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def ensure_pg_columns() -> None:
    """Добавить новые колонки/индексы на уже существующую БД (create_all их не создаёт).

    Также создаёт context_blocks, если таблица ещё не появилась (старые БД до пака ОГЭ).
    """
    engine = pg_engine()
    stmts = [
        # context_blocks — на случай, если create_all не вызывали / упал раньше
        """
        CREATE TABLE IF NOT EXISTS context_blocks (
            id SERIAL PRIMARY KEY,
            context_id VARCHAR(100) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description_text TEXT,
            figure_kind VARCHAR(50),
            figure_params TEXT,
            subject_code VARCHAR(50) NOT NULL,
            exam_code VARCHAR(50) NOT NULL,
            CONSTRAINT uq_context_block_id_exam
                UNIQUE (context_id, subject_code, exam_code)
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_context_blocks_context_id ON context_blocks (context_id)",
        "CREATE INDEX IF NOT EXISTS ix_context_blocks_subject_code ON context_blocks (subject_code)",
        "CREATE INDEX IF NOT EXISTS ix_context_blocks_exam_code ON context_blocks (exam_code)",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS template_text TEXT",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS template_answer TEXT",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS template_solution TEXT",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS figure_kind VARCHAR(50)",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS figure_params TEXT",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS figure_data TEXT",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS figure_svg TEXT",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS context_id VARCHAR(100)",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS answer_type VARCHAR(50)",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS max_score INTEGER",
        "ALTER TABLE task_prototypes ADD COLUMN IF NOT EXISTS acceptable_answers TEXT",
        "CREATE INDEX IF NOT EXISTS ix_task_prototypes_context_id ON task_prototypes (context_id)",
        # universal_tasks — player layer (additive, не трогает task_prototypes)
        """
        CREATE TABLE IF NOT EXISTS universal_tasks (
            id VARCHAR(64) PRIMARY KEY,
            subject VARCHAR(50) NOT NULL,
            exam_type VARCHAR(20) NOT NULL,
            task_number INTEGER NOT NULL,
            type VARCHAR(50) NOT NULL,
            statement TEXT NOT NULL,
            payload TEXT,
            correct_answer VARCHAR(500) NOT NULL DEFAULT '',
            max_score INTEGER NOT NULL DEFAULT 1,
            topic VARCHAR(255),
            difficulty VARCHAR(50),
            context_id VARCHAR(100),
            active BOOLEAN NOT NULL DEFAULT TRUE
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_universal_tasks_subject ON universal_tasks (subject)",
        "CREATE INDEX IF NOT EXISTS ix_universal_tasks_exam_type ON universal_tasks (exam_type)",
        "CREATE INDEX IF NOT EXISTS ix_universal_tasks_task_number ON universal_tasks (task_number)",
        "CREATE INDEX IF NOT EXISTS ix_universal_tasks_type ON universal_tasks (type)",
        "CREATE INDEX IF NOT EXISTS ix_universal_tasks_context_id ON universal_tasks (context_id)",
        "ALTER TABLE universal_tasks ADD COLUMN IF NOT EXISTS topic VARCHAR(255)",
        "ALTER TABLE universal_tasks ADD COLUMN IF NOT EXISTS difficulty VARCHAR(50)",
        "ALTER TABLE universal_tasks ADD COLUMN IF NOT EXISTS context_id VARCHAR(100)",
        "ALTER TABLE universal_tasks ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE",
    ]
    with engine.begin() as conn:
        for stmt in stmts:
            conn.execute(text(stmt))


def init_pg_tables() -> None:
    """Alembic-less create_all для universal-таблиц + soft-migrate колонок."""
    # импорт моделей регистрирует таблицы в PgBase.metadata
    from backend.db import pg_models  # noqa: F401

    engine = pg_engine()
    PgBase.metadata.create_all(bind=engine)
    ensure_pg_columns()
