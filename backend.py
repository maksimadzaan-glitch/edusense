import hashlib
import hmac
import os
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

# Новый файл БД под архитектуру v4 (комнаты / варианты / submissions).
# Старый ege_tracker.db не трогаем — схема несовместима.
DATABASE_URL = "sqlite:///./ege_tracker_v4.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "teacher" | "student"
    last_active = Column(DateTime, nullable=False, default=datetime.utcnow)

    rooms_taught = relationship("Room", back_populates="teacher")
    room_links = relationship("RoomStudent", back_populates="student")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    teacher = relationship("User", back_populates="rooms_taught")
    students = relationship("RoomStudent", back_populates="room", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="room", cascade="all, delete-orphan")


class RoomStudent(Base):
    __tablename__ = "room_students"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (UniqueConstraint("room_id", "student_id", name="uq_room_student"),)

    room = relationship("Room", back_populates="students")
    student = relationship("User", back_populates="room_links")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    title = Column(String, nullable=False)
    fipi_url = Column(String, nullable=True)  # ссылка на вариант/подборку ФИПИ
    fipi_keys = Column(JSON, nullable=False, default=dict)
    total_tasks_part1 = Column(Integer, nullable=False, default=12)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    room = relationship("Room", back_populates="assignments")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    answers_part1 = Column(JSON, nullable=False, default=dict)
    photo_urls_part2 = Column(JSON, nullable=False, default=list)
    time_spent_seconds = Column(Integer, nullable=False, default=0)
    primary_score = Column(Integer, nullable=False, default=0)
    secondary_score = Column(Integer, nullable=False, default=0)
    diagnostic = Column(JSON, nullable=False, default=dict)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student"),
    )

    assignment = relationship("Assignment", back_populates="submissions")


Base.metadata.create_all(bind=engine)


def _ensure_sqlite_columns() -> None:
    """Добавляет новые колонки в уже существующие SQLite-таблицы (без Alembic)."""
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(assignments)").fetchall()
        cols = {r[1] for r in rows}
        if "fipi_url" not in cols:
            conn.exec_driver_sql("ALTER TABLE assignments ADD COLUMN fipi_url VARCHAR")


_ensure_sqlite_columns()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="ЕГЭ Трекер API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Score scales (ЕГЭ-2025) + calculate_scores
# ---------------------------------------------------------------------------

SCORE_SCALES: Dict[str, Dict[int, int]] = {
    "Математика (профиль)": {
        0: 0, 1: 6, 2: 11, 3: 17, 4: 22, 5: 27, 6: 34, 7: 40, 8: 46, 9: 52,
        10: 58, 11: 64, 12: 70, 13: 72, 14: 74, 15: 76, 16: 78, 17: 80, 18: 82, 19: 84,
        20: 86, 21: 88, 22: 90, 23: 92, 24: 94, 25: 95, 26: 96, 27: 97, 28: 98, 29: 99,
        30: 100, 31: 100, 32: 100,
    },
    "Информатика": {
        0: 0, 1: 7, 2: 14, 3: 20, 4: 27, 5: 34, 6: 40, 7: 43, 8: 46, 9: 48,
        10: 51, 11: 54, 12: 56, 13: 59, 14: 62, 15: 64, 16: 67, 17: 70, 18: 72, 19: 75,
        20: 78, 21: 80, 22: 83, 23: 85, 24: 88, 25: 90, 26: 93, 27: 95, 28: 98, 29: 100,
    },
    "Русский язык": {
        0: 0, 1: 3, 2: 5, 3: 8, 4: 10, 5: 12, 6: 15, 7: 17, 8: 20, 9: 22,
        10: 24, 11: 27, 12: 29, 13: 32, 14: 34, 15: 36, 16: 37, 17: 39, 18: 40, 19: 42,
        20: 43, 21: 45, 22: 46, 23: 48, 24: 49, 25: 51, 26: 52, 27: 54, 28: 55, 29: 57,
        30: 58, 31: 60, 32: 61, 33: 63, 34: 64, 35: 66, 36: 67, 37: 69, 38: 70, 39: 72,
        40: 73, 41: 75, 42: 78, 43: 81, 44: 83, 45: 86, 46: 89, 47: 91, 48: 94, 49: 97,
        50: 100,
    },
}

SUBJECT_ALIASES = {
    "Математика (профильная)": "Математика (профиль)",
    "Информатика и ИКТ": "Информатика",
}


def normalize_subject(subject: str) -> str:
    s = (subject or "").strip()
    return SUBJECT_ALIASES.get(s, s)


def normalize_answer(value: Any) -> str:
    """Нормализация ответа для сравнения с ключом ФИПИ."""
    text = str(value if value is not None else "").strip().replace(",", ".")
    text = " ".join(text.split())
    return text.lower()


def build_diagnostic(
    fipi_keys: Dict[str, Any],
    answers_part1: Dict[str, Any],
) -> tuple[Dict[str, Dict[str, Any]], bool]:
    """
    Возвращает (diagnostic, auto_checked).
    Если ключей нет — автопроверка выключена, только сохраняем ответы ученика.
    """
    keys = fipi_keys or {}
    answers = answers_part1 or {}

    if not keys:
        diagnostic: Dict[str, Dict[str, Any]] = {}
        for task_num, user_raw in answers.items():
            diagnostic[str(task_num)] = {
                "correct": None,
                "user": str(user_raw).strip() if user_raw is not None else "",
                "key": None,
                "unchecked": True,
            }
        return diagnostic, False

    diagnostic = {}
    for task_num, key_raw in keys.items():
        key_norm = normalize_answer(key_raw)
        user_raw = answers.get(str(task_num), answers.get(task_num, ""))
        user_norm = normalize_answer(user_raw)
        is_correct = bool(key_norm) and user_norm == key_norm
        diagnostic[str(task_num)] = {
            "correct": is_correct,
            "user": str(user_raw).strip() if user_raw is not None else "",
            "key": str(key_raw).strip() if key_raw is not None else "",
            "unchecked": False,
        }
    return diagnostic, True


def calculate_scores(subject: str, diagnostic_dict: Dict[str, Any]) -> tuple[int, int]:
    """
    Первичный балл = число correct:true (строго через int()).
    Вторичный — по шкале предмета.
    """
    primary = 0
    for item in (diagnostic_dict or {}).values():
        if isinstance(item, dict) and item.get("correct") is True:
            primary = int(primary) + int(1)

    scale = SCORE_SCALES.get(normalize_subject(subject))
    if not scale:
        return int(primary), int(primary)

    max_primary = int(max(scale.keys()))
    capped = min(max(int(primary), 0), max_primary)
    secondary = int(scale[capped])
    return int(primary), int(secondary)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 100_000
ONLINE_THRESHOLD = timedelta(minutes=5)


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
    except (ValueError, AttributeError):
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(actual, expected)


def _generate_room_code(length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def _unique_room_code(db: Session) -> str:
    for _ in range(20):
        code = _generate_room_code()
        if not db.query(Room).filter(Room.code == code).first():
            return code
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Не удалось сгенерировать уникальный код комнаты.",
    )


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Пользователь id={user_id} не найден.")
    return user


def _touch_user(db: Session, user: User) -> None:
    user.last_active = datetime.utcnow()
    db.add(user)


def _find_user_by_name(db: Session, full_name: str) -> Optional[User]:
    normalized = full_name.strip().lower()
    return db.query(User).filter(func.lower(User.full_name) == normalized).first()


def _presence_label(last_active: Optional[datetime], now: Optional[datetime] = None) -> str:
    now = now or datetime.utcnow()
    if not last_active:
        return "Не был в сети"
    delta = now - last_active
    if delta <= ONLINE_THRESHOLD:
        return "В сети"
    minutes = int(delta.total_seconds() // 60)
    if minutes < 60:
        return f"Был {minutes} мин назад"
    hours = minutes // 60
    if hours < 24:
        return f"Был {hours} ч назад"
    days = hours // 24
    return f"Был {days} дн назад"


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=4, max_length=128)
    role: str = Field(..., pattern="^(teacher|student)$")


class LoginRequest(BaseModel):
    full_name: str
    password: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    role: str
    last_active: datetime

    class Config:
        from_attributes = True


class RoomCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    subject: str = Field(..., min_length=1, max_length=100)
    teacher_id: int


class RoomJoinRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
    student_id: int


class RoomSummary(BaseModel):
    id: int
    name: str
    subject: str
    code: str
    teacher_id: int
    teacher_name: Optional[str] = None


class StudentPresence(BaseModel):
    student_id: int
    full_name: str
    status: str
    last_active: datetime
    last_time_spent_seconds: Optional[int] = None


class HeatmapItem(BaseModel):
    task_number: str
    error_percent: float
    errors: int
    total: int


class AssignmentSummary(BaseModel):
    id: int
    title: str
    fipi_url: Optional[str] = None
    total_tasks_part1: int
    created_at: datetime
    submissions_count: int = 0


class RoomDashboardResponse(BaseModel):
    id: int
    name: str
    subject: str
    code: str
    teacher_id: int
    teacher_name: str
    students: List[StudentPresence]
    heatmap: List[HeatmapItem]
    assignments: List[AssignmentSummary]


class AssignmentCreateRequest(BaseModel):
    room_id: int
    title: str = Field(..., min_length=1, max_length=200)
    fipi_url: Optional[str] = Field(default=None, max_length=1000)
    fipi_keys: Optional[Dict[str, str]] = Field(default_factory=dict)
    total_tasks_part1: int = Field(default=12, ge=1, le=50)


class AssignmentResponse(BaseModel):
    id: int
    room_id: int
    title: str
    fipi_url: Optional[str] = None
    fipi_keys: Dict[str, Any] = Field(default_factory=dict)
    total_tasks_part1: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentPublicResponse(BaseModel):
    """Для ученика: без ключей ФИПИ."""

    id: int
    room_id: int
    title: str
    fipi_url: Optional[str] = None
    total_tasks_part1: int
    created_at: datetime
    already_submitted: bool = False
    primary_score: Optional[int] = None
    secondary_score: Optional[int] = None


class SubmissionSubmitRequest(BaseModel):
    assignment_id: int
    student_id: int
    answers_part1: Dict[str, str] = Field(default_factory=dict)
    photo_urls_part2: List[str] = Field(default_factory=list)
    time_spent_seconds: int = Field(default=0, ge=0)


class SubmissionResponse(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    answers_part1: Dict[str, Any]
    photo_urls_part2: List[str]
    time_spent_seconds: int
    primary_score: int
    secondary_score: int
    diagnostic: Dict[str, Any]
    submitted_at: datetime
    subject: Optional[str] = None
    assignment_title: Optional[str] = None
    auto_checked: bool = False


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


@app.post("/api/register", response_model=UserResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if _find_user_by_name(db, payload.full_name):
        raise HTTPException(status_code=409, detail="Пользователь с таким ФИО уже есть.")

    user = User(
        full_name=payload.full_name.strip(),
        password=_hash_password(payload.password),
        role=payload.role,
        last_active=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/login", response_model=UserResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = _find_user_by_name(db, payload.full_name)
    if not user or not _verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Неверное ФИО или пароль.")
    _touch_user(db, user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/ping/{user_id}", response_model=UserResponse)
def ping(user_id: int, db: Session = Depends(get_db)):
    """Обновляет last_active — для статуса «В сети»."""
    user = _get_user_or_404(db, user_id)
    _touch_user(db, user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------


@app.post("/rooms/create", response_model=RoomSummary, status_code=201)
def create_room(payload: RoomCreateRequest, db: Session = Depends(get_db)):
    teacher = _get_user_or_404(db, payload.teacher_id)
    if teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Только учитель может создавать комнаты.")

    subject = normalize_subject(payload.subject)
    if subject not in SCORE_SCALES:
        raise HTTPException(
            status_code=400,
            detail="Предмет должен быть одним из: Математика (профиль), Информатика, Русский язык.",
        )

    room = Room(
        name=payload.name.strip(),
        subject=subject,
        code=_unique_room_code(db),
        teacher_id=int(teacher.id),
    )
    _touch_user(db, teacher)
    db.add(room)
    db.commit()
    db.refresh(room)

    return RoomSummary(
        id=int(room.id),
        name=room.name,
        subject=room.subject,
        code=room.code,
        teacher_id=int(room.teacher_id),
        teacher_name=teacher.full_name,
    )


@app.post("/rooms/join", response_model=RoomSummary)
def join_room(payload: RoomJoinRequest, db: Session = Depends(get_db)):
    student = _get_user_or_404(db, payload.student_id)
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Только ученик может вступать в комнату.")

    code = payload.code.strip().upper()
    room = db.query(Room).filter(Room.code == code).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната с кодом «{code}» не найдена.")

    existing = (
        db.query(RoomStudent)
        .filter(RoomStudent.room_id == room.id, RoomStudent.student_id == student.id)
        .first()
    )
    if not existing:
        db.add(RoomStudent(room_id=int(room.id), student_id=int(student.id)))

    _touch_user(db, student)
    db.commit()

    teacher = db.query(User).filter(User.id == room.teacher_id).first()
    return RoomSummary(
        id=int(room.id),
        name=room.name,
        subject=room.subject,
        code=room.code,
        teacher_id=int(room.teacher_id),
        teacher_name=teacher.full_name if teacher else "—",
    )


@app.get("/rooms/teacher/{teacher_id}", response_model=List[RoomSummary])
def teacher_rooms(teacher_id: int, db: Session = Depends(get_db)):
    teacher = _get_user_or_404(db, teacher_id)
    if teacher.role != "teacher":
        raise HTTPException(status_code=403, detail="Доступ только для учителей.")
    _touch_user(db, teacher)
    db.commit()

    rooms = (
        db.query(Room)
        .filter(Room.teacher_id == int(teacher_id))
        .order_by(Room.id.desc())
        .all()
    )
    return [
        RoomSummary(
            id=int(r.id),
            name=r.name,
            subject=r.subject,
            code=r.code,
            teacher_id=int(r.teacher_id),
            teacher_name=teacher.full_name,
        )
        for r in rooms
    ]


@app.get("/rooms/student/{student_id}", response_model=List[RoomSummary])
def student_rooms(student_id: int, db: Session = Depends(get_db)):
    student = _get_user_or_404(db, student_id)
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Доступ только для учеников.")
    _touch_user(db, student)
    db.commit()

    links = (
        db.query(RoomStudent)
        .filter(RoomStudent.student_id == int(student_id))
        .order_by(RoomStudent.id.desc())
        .all()
    )
    result: List[RoomSummary] = []
    for link in links:
        room = db.query(Room).filter(Room.id == link.room_id).first()
        if not room:
            continue
        teacher = db.query(User).filter(User.id == room.teacher_id).first()
        result.append(
            RoomSummary(
                id=int(room.id),
                name=room.name,
                subject=room.subject,
                code=room.code,
                teacher_id=int(room.teacher_id),
                teacher_name=teacher.full_name if teacher else "—",
            )
        )
    return result


@app.get("/rooms/{room_id}/dashboard", response_model=RoomDashboardResponse)
def room_dashboard(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == int(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Комната id={room_id} не найдена.")

    teacher = db.query(User).filter(User.id == room.teacher_id).first()
    now = datetime.utcnow()

    links = db.query(RoomStudent).filter(RoomStudent.room_id == room.id).all()
    student_ids = [int(l.student_id) for l in links]
    users = (
        db.query(User).filter(User.id.in_(student_ids)).all()
        if student_ids
        else []
    )
    users_by_id = {int(u.id): u for u in users}

    # Последнее затраченное время по любому сабмишену ученика в этой комнате
    assignment_ids = [int(a.id) for a in room.assignments]
    last_times: Dict[int, int] = {}
    if assignment_ids and student_ids:
        subs = (
            db.query(Submission)
            .filter(
                Submission.assignment_id.in_(assignment_ids),
                Submission.student_id.in_(student_ids),
            )
            .order_by(Submission.submitted_at.desc())
            .all()
        )
        for sub in subs:
            sid = int(sub.student_id)
            if sid not in last_times:
                last_times[sid] = int(sub.time_spent_seconds or 0)

    students: List[StudentPresence] = []
    for sid in student_ids:
        u = users_by_id.get(sid)
        if not u:
            continue
        students.append(
            StudentPresence(
                student_id=sid,
                full_name=u.full_name,
                status=_presence_label(u.last_active, now),
                last_active=u.last_active,
                last_time_spent_seconds=last_times.get(sid),
            )
        )
    students.sort(key=lambda s: s.full_name.lower())

    # Тепловая карта: % ошибок по номерам среди всех сданных работ
    error_counts: Dict[str, int] = {}
    total_attempts: Dict[str, int] = {}
    if assignment_ids:
        all_subs = (
            db.query(Submission)
            .filter(Submission.assignment_id.in_(assignment_ids))
            .all()
        )
        for sub in all_subs:
            diag = sub.diagnostic or {}
            for task_num, info in diag.items():
                if not isinstance(info, dict) or info.get("unchecked") or info.get("correct") is None:
                    continue
                total_attempts[task_num] = int(total_attempts.get(task_num, 0)) + 1
                if not info.get("correct"):
                    error_counts[task_num] = int(error_counts.get(task_num, 0)) + 1

    heatmap: List[HeatmapItem] = []
    for task_num in sorted(total_attempts.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
        total = int(total_attempts[task_num])
        errors = int(error_counts.get(task_num, 0))
        pct = round((errors / total) * 100.0, 1) if total > 0 else 0.0
        heatmap.append(
            HeatmapItem(
                task_number=str(task_num),
                error_percent=float(pct),
                errors=errors,
                total=total,
            )
        )

    assignments_out: List[AssignmentSummary] = []
    for a in sorted(room.assignments, key=lambda x: x.id, reverse=True):
        count = db.query(Submission).filter(Submission.assignment_id == a.id).count()
        assignments_out.append(
            AssignmentSummary(
                id=int(a.id),
                title=a.title,
                fipi_url=a.fipi_url,
                total_tasks_part1=int(a.total_tasks_part1),
                created_at=a.created_at,
                submissions_count=int(count),
            )
        )

    return RoomDashboardResponse(
        id=int(room.id),
        name=room.name,
        subject=room.subject,
        code=room.code,
        teacher_id=int(room.teacher_id),
        teacher_name=teacher.full_name if teacher else "—",
        students=students,
        heatmap=heatmap,
        assignments=assignments_out,
    )


# ---------------------------------------------------------------------------
# Assignments & Submissions
# ---------------------------------------------------------------------------


@app.post("/assignments/create", response_model=AssignmentResponse, status_code=201)
def create_assignment(payload: AssignmentCreateRequest, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == int(payload.room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена.")

    # Нормализуем ключи: строковые номера заданий
    fipi_keys = {str(k): str(v).strip() for k, v in (payload.fipi_keys or {}).items() if str(v).strip()}
    # Ключи необязательны: без них работа принимается, автопроверка выключена.

    url = (payload.fipi_url or "").strip() or None
    if url and not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Ссылка ФИПИ должна начинаться с http:// или https://")

    total = int(payload.total_tasks_part1)
    assignment = Assignment(
        room_id=int(room.id),
        title=payload.title.strip(),
        fipi_url=url,
        fipi_keys=fipi_keys,
        total_tasks_part1=total,
        created_at=datetime.utcnow(),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@app.get("/rooms/{room_id}/assignments", response_model=List[AssignmentPublicResponse])
def list_room_assignments(
    room_id: int,
    student_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Список вариантов комнаты БЕЗ ключей (для выбора учеником)."""
    room = db.query(Room).filter(Room.id == int(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена.")

    rows = (
        db.query(Assignment)
        .filter(Assignment.room_id == int(room_id))
        .order_by(Assignment.id.desc())
        .all()
    )

    result: List[AssignmentPublicResponse] = []
    for a in rows:
        already = False
        primary = None
        secondary = None
        if student_id is not None:
            sub = (
                db.query(Submission)
                .filter(
                    Submission.assignment_id == a.id,
                    Submission.student_id == int(student_id),
                )
                .first()
            )
            if sub:
                already = True
                primary = int(sub.primary_score)
                secondary = int(sub.secondary_score)
        result.append(
            AssignmentPublicResponse(
                id=int(a.id),
                room_id=int(a.room_id),
                title=a.title,
                fipi_url=a.fipi_url,
                total_tasks_part1=int(a.total_tasks_part1),
                created_at=a.created_at,
                already_submitted=already,
                primary_score=primary,
                secondary_score=secondary,
            )
        )
    return result


@app.get("/assignments/{assignment_id}/public", response_model=AssignmentPublicResponse)
def get_assignment_public(assignment_id: int, student_id: Optional[int] = None, db: Session = Depends(get_db)):
    assignment = db.query(Assignment).filter(Assignment.id == int(assignment_id)).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Вариант не найден.")
    already = False
    primary = None
    secondary = None
    if student_id is not None:
        sub = (
            db.query(Submission)
            .filter(
                Submission.assignment_id == assignment.id,
                Submission.student_id == int(student_id),
            )
            .first()
        )
        if sub:
            already = True
            primary = int(sub.primary_score)
            secondary = int(sub.secondary_score)
    return AssignmentPublicResponse(
        id=int(assignment.id),
        room_id=int(assignment.room_id),
        title=assignment.title,
        fipi_url=assignment.fipi_url,
        total_tasks_part1=int(assignment.total_tasks_part1),
        created_at=assignment.created_at,
        already_submitted=already,
        primary_score=primary,
        secondary_score=secondary,
    )


@app.post("/submissions/submit", response_model=SubmissionResponse, status_code=201)
def submit_work(payload: SubmissionSubmitRequest, db: Session = Depends(get_db)):
    student = _get_user_or_404(db, payload.student_id)
    if student.role != "student":
        raise HTTPException(status_code=403, detail="Сдавать работу может только ученик.")

    assignment = db.query(Assignment).filter(Assignment.id == int(payload.assignment_id)).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Вариант не найден.")

    room = db.query(Room).filter(Room.id == assignment.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната варианта не найдена.")

    membership = (
        db.query(RoomStudent)
        .filter(RoomStudent.room_id == room.id, RoomStudent.student_id == student.id)
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Вы не состоите в этой комнате.")

    answers = {str(k): str(v).strip() for k, v in (payload.answers_part1 or {}).items()}
    diagnostic, auto_checked = build_diagnostic(assignment.fipi_keys or {}, answers)
    if auto_checked:
        primary, secondary = calculate_scores(room.subject, diagnostic)
    else:
        primary, secondary = 0, 0

    existing = (
        db.query(Submission)
        .filter(
            Submission.assignment_id == int(assignment.id),
            Submission.student_id == int(student.id),
        )
        .first()
    )

    photos = list(payload.photo_urls_part2 or [])
    time_spent = int(payload.time_spent_seconds or 0)

    if existing:
        existing.answers_part1 = answers
        existing.photo_urls_part2 = photos
        existing.time_spent_seconds = time_spent
        existing.primary_score = int(primary)
        existing.secondary_score = int(secondary)
        existing.diagnostic = diagnostic
        existing.submitted_at = datetime.utcnow()
        submission = existing
    else:
        submission = Submission(
            assignment_id=int(assignment.id),
            student_id=int(student.id),
            answers_part1=answers,
            photo_urls_part2=photos,
            time_spent_seconds=time_spent,
            primary_score=int(primary),
            secondary_score=int(secondary),
            diagnostic=diagnostic,
            submitted_at=datetime.utcnow(),
        )
        db.add(submission)

    _touch_user(db, student)
    db.commit()
    db.refresh(submission)

    return SubmissionResponse(
        id=int(submission.id),
        assignment_id=int(submission.assignment_id),
        student_id=int(submission.student_id),
        answers_part1=submission.answers_part1 or {},
        photo_urls_part2=submission.photo_urls_part2 or [],
        time_spent_seconds=int(submission.time_spent_seconds),
        primary_score=int(submission.primary_score),
        secondary_score=int(submission.secondary_score),
        diagnostic=submission.diagnostic or {},
        submitted_at=submission.submitted_at,
        subject=room.subject,
        assignment_title=assignment.title,
        auto_checked=bool(auto_checked),
    )


@app.get("/submissions/student/{student_id}/assignment/{assignment_id}", response_model=Optional[SubmissionResponse])
def get_student_submission(student_id: int, assignment_id: int, db: Session = Depends(get_db)):
    sub = (
        db.query(Submission)
        .filter(
            Submission.student_id == int(student_id),
            Submission.assignment_id == int(assignment_id),
        )
        .first()
    )
    if not sub:
        return None
    assignment = db.query(Assignment).filter(Assignment.id == sub.assignment_id).first()
    room = db.query(Room).filter(Room.id == assignment.room_id).first() if assignment else None
    auto_checked = bool(assignment and (assignment.fipi_keys or {}))
    return SubmissionResponse(
        id=int(sub.id),
        assignment_id=int(sub.assignment_id),
        student_id=int(sub.student_id),
        answers_part1=sub.answers_part1 or {},
        photo_urls_part2=sub.photo_urls_part2 or [],
        time_spent_seconds=int(sub.time_spent_seconds),
        primary_score=int(sub.primary_score),
        secondary_score=int(sub.secondary_score),
        diagnostic=sub.diagnostic or {},
        submitted_at=sub.submitted_at,
        subject=room.subject if room else None,
        assignment_title=assignment.title if assignment else None,
        auto_checked=auto_checked,
    )


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
