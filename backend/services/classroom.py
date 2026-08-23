"""Общие хелперы для EduClass + мост из legacy ClassRoom."""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.models import ClassRoom, EduClass, Teacher


def ensure_edu_class(
    db: Session, *, class_id: Optional[int] = None, class_code: Optional[str] = None
) -> EduClass:
    """Найти EduClass по id/коду; при необходимости создать из legacy ClassRoom."""
    if class_id:
        classroom = db.query(EduClass).filter(EduClass.id == class_id).first()
        if classroom:
            return classroom
        raise HTTPException(status_code=404, detail="Класс не найден")

    code = (class_code or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Укажите class_id или class_code")

    classroom = db.query(EduClass).filter(EduClass.code == code).first()
    if classroom:
        return classroom

    legacy = db.query(ClassRoom).filter(ClassRoom.access_code == code).first()
    if not legacy:
        raise HTTPException(status_code=404, detail="Класс с таким кодом не найден")

    email = f"legacy-{legacy.teacher_id}@edusense.local"
    teacher = db.query(Teacher).filter(Teacher.email == email).first()
    if not teacher:
        teacher = Teacher(name=f"Учитель #{legacy.teacher_id}", email=email)
        db.add(teacher)
        db.flush()

    classroom = EduClass(
        teacher_id=teacher.id,
        name=legacy.name,
        code=legacy.access_code,
        subject=legacy.subject,
        target_exam=legacy.exam_type,
    )
    db.add(classroom)
    db.flush()
    return classroom


def normalize_student_name(name: str) -> str:
    return " ".join((name or "").strip().split())
