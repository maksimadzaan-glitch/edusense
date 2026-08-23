"""PostgreSQL ORM-модели для универсальной генерации вариантов."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.pg import PgBase


class Subject(PgBase):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    prototypes: Mapped[list[TaskPrototype]] = relationship(back_populates="subject")


class ExamType(PgBase):
    __tablename__ = "exam_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    prototypes: Mapped[list[TaskPrototype]] = relationship(back_populates="exam_type")


class ContextBlock(PgBase):
    """Общий текстовый/графический контекст для связанных заданий (ОГЭ матем. 1–5)."""

    __tablename__ = "context_blocks"
    __table_args__ = (
        UniqueConstraint(
            "context_id",
            "subject_code",
            "exam_code",
            name="uq_context_block_id_exam",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    context_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    figure_kind: Mapped[str | None] = mapped_column(String(50), nullable=True)
    figure_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    subject_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exam_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)


class TaskPrototype(PgBase):
    __tablename__ = "task_prototypes"
    __table_args__ = (
        UniqueConstraint(
            "subject_code",
            "exam_code",
            "task_number",
            "prototype_title",
            name="uq_prototype_slot_title",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("subjects.code"), nullable=False, index=True
    )
    exam_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("exam_types.code"), nullable=False, index=True
    )
    task_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    part: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 или 2
    prototype_title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_instruction: Mapped[str] = mapped_column(Text, nullable=False)
    # Готовые шаблоны КИМ (nullable для instruction-only спек)
    template_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    figure_kind: Mapped[str | None] = mapped_column(String(50), nullable=True)
    figure_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    # Part2 geometry extension: metadata + optional preloaded SVG
    figure_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    figure_svg: Mapped[str | None] = mapped_column(Text, nullable=True)  # inline SVG
    # Строковый ключ → context_blocks.context_id (тот же subject/exam)
    context_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    answer_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acceptable_answers: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list

    subject: Mapped[Subject] = relationship(back_populates="prototypes")
    exam_type: Mapped[ExamType] = relationship(back_populates="prototypes")


class Task(PgBase):
    """Универсальное задание (player): отдельная таблица, не путать с task_prototypes."""

    __tablename__ = "universal_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    exam_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    task_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    # column name "type" — механика ответа
    task_type: Mapped[str] = mapped_column("type", String(50), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    correct_answer: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    context_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
