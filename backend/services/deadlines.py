"""Дедлайны: храним UTC, в API отдаём с таймзоной."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional


def utc_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Naive из SQLite считаем UTC (фронт шлёт ISO с Z)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utc_naive(dt: Optional[datetime]) -> Optional[datetime]:
    aware = utc_aware(dt)
    if aware is None:
        return None
    return aware.replace(tzinfo=None)


def deadline_passed(dt: Optional[datetime]) -> bool:
    if dt is None:
        return False
    try:
        aware = utc_aware(dt)
        if aware is None:
            return False
        return datetime.now(timezone.utc) > aware
    except Exception:
        return False
