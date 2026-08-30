from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from backend.database import Base


# --- Legacy (onboarding / teacher cabinet) ---


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "teacher" | "student"
    subject = Column(String, nullable=True)

    classes = relationship("ClassRoom", back_populates="teacher")


class ClassRoom(Base):
    """Старый класс кабинета учителя (users → classes)."""

    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    access_code = Column(String, unique=True, nullable=False, index=True)
    exam_type = Column(String, nullable=False)  # vpr | oge | ege | school
    grade = Column(String, nullable=True)
    subject = Column(String, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    teacher = relationship("User", back_populates="classes")


# --- EduSense core API (Teachers / Classes / Assignments / Submissions) ---


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)

    classes = relationship("EduClass", back_populates="teacher", cascade="all, delete-orphan")


class EduClass(Base):
    """Таблица Classes из ТЗ (имя edu_classes, чтобы не конфликтовать с legacy classes)."""

    __tablename__ = "edu_classes"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)  # EDU-XXXX
    subject = Column(String, nullable=False)
    target_exam = Column(String, nullable=False)  # vpr | oge | ege | school

    teacher = relationship("Teacher", back_populates="classes")
    assignments = relationship(
        "Assignment", back_populates="classroom", cascade="all, delete-orphan"
    )
    roster = relationship(
        "ClassStudent", back_populates="classroom", cascade="all, delete-orphan"
    )


class ClassStudent(Base):
    """Лёгкий ростер класса (ФИО без полной auth ученика)."""

    __tablename__ = "class_students"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("edu_classes.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    student_uuid = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    classroom = relationship("EduClass", back_populates="roster")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("edu_classes.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False, index=True)  # EDU-XXXX для ученика
    # deadline / timer_minutes — канон в БД; API также принимает deadline_at / time_limit_minutes
    deadline = Column(DateTime, nullable=True)
    timer_minutes = Column(Integer, nullable=True)
    questions_json = Column(Text, nullable=False, default="[]")
    grading_mode = Column(String, nullable=False, default="ai_assist")
    # draft | active | closed
    status = Column(String, nullable=False, default="active")
    # флаг для будущего изоморфного shuffle вариантов (пока только хранение)
    shuffle_variants = Column(Boolean, nullable=False, default=False)
    accepting_submissions = Column(Boolean, nullable=False, default=True)
    # опциональный ожидаемый размер класса (пока null — прогресс без знаменателя)
    expected_students = Column(Integer, nullable=True)
    # easy | medium | hard — для ОГЭ русский: тексты 1/10–13 и сила 2–9
    difficulty = Column(String, nullable=True)
    # JSON: block_copy, hide_answers, allowed_students
    settings_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    classroom = relationship("EduClass", back_populates="assignments")
    submissions = relationship(
        "Submission", back_populates="assignment", cascade="all, delete-orphan"
    )


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    student_name = Column(String, nullable=False)
    student_uuid = Column(String(36), nullable=True, index=True)
    score = Column(Float, nullable=True)
    status = Column(String, nullable=False, default="pending")
    # pending | ai_reviewed | approved | graded
    answers_json = Column(Text, nullable=False, default="{}")
    ai_review_json = Column(Text, nullable=True)
    # ручная оценка / комментарий учителя (часть 2 и пр.)
    teacher_score = Column(Float, nullable=True)
    teacher_comment = Column(Text, nullable=True)
    teacher_reviewed_at = Column(DateTime, nullable=True)
    # если ученик отметил старт — длительность = created_at − started_at
    started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    assignment = relationship("Assignment", back_populates="submissions")


class BankTask(Base):
    """Проверенный банк заданий ФИПИ-стиля (по экзамену / предмету / слоту КИМ)."""

    __tablename__ = "bank_tasks"

    id = Column(Integer, primary_key=True, index=True)
    exam = Column(String, nullable=False, index=True)  # ege | oge | vpr | school
    subject_key = Column(String, nullable=False, index=True)  # profile_math | base_math | ...
    slot = Column(Integer, nullable=False, index=True)  # номер типа в КИМ (1..12)
    part = Column(Integer, nullable=False, default=1)
    difficulty = Column(String, nullable=False, default="medium")  # easy|medium|hard
    topic = Column(String, nullable=False)
    section = Column(String, nullable=False, default="algebra")
    task_type = Column(String, nullable=False, default="Краткий ответ")
    text = Column(Text, nullable=False)
    answer = Column(String, nullable=False)
    max_score = Column(Integer, nullable=False, default=1)
    needs_figure = Column(Integer, nullable=False, default=0)  # 0/1 sqlite-friendly
    figure_kind = Column(String, nullable=True)
    source_tag = Column(String, nullable=False, default="seed")
    is_active = Column(Integer, nullable=False, default=1)
