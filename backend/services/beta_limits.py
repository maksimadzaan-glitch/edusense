"""Лимит выдачи в открытой бете: сколько вариантов можно выдать на класс."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models import Assignment

BETA_VARIANT_LIMIT = 5
BETA_LIMIT_DETAIL = (
    f"В открытой бете на класс можно выдать {BETA_VARIANT_LIMIT} вариантов. "
    "Напишите нам, если для пилота нужно больше."
)


def issued_variant_count(db: Session, class_id: int) -> int:
    return (
        db.query(Assignment)
        .filter(
            Assignment.class_id == int(class_id),
            Assignment.status.in_(("active", "closed")),
        )
        .count()
    )


def assert_can_issue_variant(db: Session, class_id: int) -> None:
    n = issued_variant_count(db, class_id)
    if n >= BETA_VARIANT_LIMIT:
        raise HTTPException(
            status_code=403,
            detail=f"{BETA_LIMIT_DETAIL} Сейчас выдано {n}.",
        )
