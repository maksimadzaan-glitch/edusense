"""Отдельное подключение PostgreSQL для universal-генерации (не трогает SQLite)."""

from backend.db.pg import PgBase, get_pg_session, init_pg_tables, is_postgres_configured, pg_engine

__all__ = [
    "PgBase",
    "get_pg_session",
    "init_pg_tables",
    "is_postgres_configured",
    "pg_engine",
]
