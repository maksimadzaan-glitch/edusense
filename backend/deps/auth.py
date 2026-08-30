"""FastAPI auth dependencies — Bearer token → User + class ownership checks."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ClassRoom, EduClass, Teacher, User
from backend.services.classroom import ensure_edu_class, normalize_student_name
from backend.services.session_tokens import extract_bearer, verify_access_token


def _load_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден.",
        )
    return user


def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    x_edusense_token: Optional[str] = Header(default=None, alias="X-EduSense-Token"),
    db: Session = Depends(get_db),
) -> Optional[User]:
    token = extract_bearer(authorization, x_edusense_token)
    user_id = verify_access_token(token)
    if not user_id:
        return None
    return _load_user(db, user_id)


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_edusense_token: Optional[str] = Header(default=None, alias="X-EduSense-Token"),
    db: Session = Depends(get_db),
) -> User:
    token = extract_bearer(authorization, x_edusense_token)
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла. Войдите снова.",
        )
    return _load_user(db, user_id)


def require_teacher(user: User = Depends(get_current_user)) -> User:
    if user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для учителя.",
        )
    return user


def require_student(user: User = Depends(get_current_user)) -> User:
    if user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ только для ученика.",
        )
    return user


def require_teacher_or_student(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("teacher", "student"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуется вход в аккаунт.",
        )
    return user


def teacher_owns_edu_class(db: Session, user: User, classroom: EduClass) -> bool:
    if user.role != "teacher":
        return False
    legacy = (
        db.query(ClassRoom)
        .filter(ClassRoom.access_code == classroom.code)
        .first()
    )
    if legacy and legacy.teacher_id == user.id:
        return True
    teacher = db.query(Teacher).filter(Teacher.id == classroom.teacher_id).first()
    if teacher and teacher.email == f"legacy-{user.id}@edusense.local":
        return True
    return False


def require_teacher_class(
    code: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_teacher),
) -> EduClass:
    classroom = ensure_edu_class(db, class_code=code)
    if not teacher_owns_edu_class(db, user, classroom):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этому классу.",
        )
    return classroom


def require_teacher_classroom_by_assignment(
    assignment_row,
    db: Session,
    user: User,
) -> EduClass:
    classroom = db.query(EduClass).filter(EduClass.id == assignment_row.class_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Класс не найден")
    if not teacher_owns_edu_class(db, user, classroom):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет доступа к этой работе.",
        )
    return classroom


def assert_student_name_matches_user(user: User, student_name: str) -> None:
    if normalize_student_name(user.full_name).casefold() != normalize_student_name(student_name).casefold():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Имя не совпадает с вашим аккаунтом.",
        )
