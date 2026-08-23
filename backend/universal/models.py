"""Реэкспорт PostgreSQL-моделей universal (см. backend.db.pg_models)."""

from backend.db.pg_models import ExamType, Subject, TaskPrototype

__all__ = ["ExamType", "Subject", "TaskPrototype"]
