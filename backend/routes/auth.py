import hashlib
import hmac
import logging
import os
import time
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ClassStudent, EduClass, User
from backend.services.classroom import normalize_student_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["auth"])

_PBKDF2_ITERATIONS = 100_000
_SESSION_TTL_SEC = 365 * 24 * 60 * 60
_SESSION_SECRET = (
    os.environ.get("EDUSENSE_SESSION_SECRET")
    or os.environ.get("SECRET_KEY")
    or "edusense-dev-session-secret-change-me"
)


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
    access_token: Optional[str] = None

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


def _issue_access_token(user_id: int) -> str:
    exp = int(time.time()) + _SESSION_TTL_SEC
    payload = f"{int(user_id)}.{exp}"
    sig = hmac.new(
        _SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:40]
    return f"{payload}.{sig}"


def _verify_access_token(token: str) -> Optional[int]:
    raw = str(token or "").strip()
    if not raw:
        return None
    if raw.lower().startswith("bearer "):
        raw = raw[7:].strip()
    parts = raw.split(".")
    if len(parts) != 3:
        return None
    uid_s, exp_s, sig = parts
    try:
        uid = int(uid_s)
        exp = int(exp_s)
    except ValueError:
        return None
    if exp < int(time.time()):
        return None
    payload = f"{uid}.{exp}"
    expected = hmac.new(
        _SESSION_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:40]
    if not hmac.compare_digest(expected, sig):
        return None
    return uid


def _user_response(db: Session, user: User, *, with_token: bool = False) -> UserResponse:
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
        access_token=_issue_access_token(user.id) if with_token else None,
    )


def _extract_bearer(
    authorization: Optional[str] = None, x_edusense_token: Optional[str] = None
) -> str:
    if authorization and authorization.strip():
        return authorization.strip()
    if x_edusense_token and x_edusense_token.strip():
        return x_edusense_token.strip()
    return ""


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
        logger.exception("register failed: database write error")
        root = str(getattr(exc, "orig", None) or exc)
        if "readonly" in root.lower():
            detail = (
                "База данных только для чтения. На VPS выполните: "
                "chown -R www-data:www-data /opt/edusense && systemctl restart edusense"
            )
        else:
            detail = f"Ошибка базы данных при регистрации: {root}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        ) from exc
    db.refresh(user)
    return _user_response(db, user, with_token=True)


@router.post("/login", response_model=UserResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = _find_user_by_name(db, payload.full_name)
    if not user or not _verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя или пароль.",
        )
    return _user_response(db, user, with_token=True)


@router.get("/auth/me", response_model=UserResponse)
def auth_me(
    authorization: Optional[str] = Header(default=None),
    x_edusense_token: Optional[str] = Header(default=None, alias="X-EduSense-Token"),
    db: Session = Depends(get_db),
):
    token = _extract_bearer(authorization, x_edusense_token)
    user_id = _verify_access_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла. Войдите снова.",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден.",
        )
    return _user_response(db, user, with_token=True)
