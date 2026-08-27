import hashlib
import hmac
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ClassStudent, EduClass, User
from backend.services.classroom import normalize_student_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["auth"])

_PBKDF2_ITERATIONS = 100_000


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., pattern="^(teacher|student)$")
    subject: Optional[str] = None


class UserLogin(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)


class UserResponse(BaseModel):
    id: int
    full_name: str
    role: str
    subject: Optional[str] = None
    class_code: Optional[str] = None
    class_name: Optional[str] = None
    exam: Optional[str] = None

    class Config:
        from_attributes = True


def _classroom_for_student_name(db: Session, full_name: str) -> Optional[EduClass]:
    key = normalize_student_name(full_name).casefold()
    if not key:
        return None
    rows = db.query(ClassStudent).order_by(ClassStudent.id.desc()).all()
    for row in rows:
        if normalize_student_name(row.name).casefold() == key:
            return db.query(EduClass).filter(EduClass.id == row.class_id).first()
    return None


def _user_response(db: Session, user: User) -> UserResponse:
    class_code = None
    class_name = None
    exam = None
    subject = user.subject
    if user.role == "student":
        classroom = _classroom_for_student_name(db, user.full_name)
        if classroom:
            class_code = classroom.code
            class_name = classroom.name
            exam = classroom.target_exam
            subject = classroom.subject or subject
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        role=user.role,
        subject=subject,
        class_code=class_code,
        class_name=class_name,
        exam=exam,
    )


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
    except (ValueError, AttributeError):
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(actual, expected)


def _find_user_by_name(db: Session, full_name: str) -> Optional[User]:
    """
    Поиск по ФИО без учёта регистра.
    SQLite lower() не умеет кириллицу — сравниваем через Python casefold().
    """
    needle = full_name.strip().casefold()
    if not needle:
        return None

    # Быстрый путь: точное совпадение
    exact = db.query(User).filter(User.full_name == full_name.strip()).first()
    if exact:
        return exact

    for user in db.query(User).all():
        if (user.full_name or "").casefold() == needle:
            return user
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if _find_user_by_name(db, payload.full_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким именем уже зарегистрирован.",
        )

    user = User(
        full_name=payload.full_name.strip(),
        password=_hash_password(payload.password),
        role=payload.role,
        subject=(payload.subject.strip() if payload.subject else None),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким именем уже зарегистрирован.",
        ) from None
    except OperationalError as exc:
        db.rollback()
        logger.exception("register failed: database schema mismatch")
        root = getattr(exc, "orig", None) or exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка базы данных при регистрации: {root}",
        ) from exc
    db.refresh(user)
    return _user_response(db, user)


@router.post("/login", response_model=UserResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = _find_user_by_name(db, payload.full_name)
    if not user or not _verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя или пароль.",
        )
    return _user_response(db, user)
