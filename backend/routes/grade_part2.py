"""ИИ-проверка части 2: математика №20–25, изложение и сочинение."""

from __future__ import annotations

from typing import Any, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.deps.auth import require_teacher_or_student
from backend.models import User

from backend.services.part2_grader import fipi_rubric_for, grade_part2_task, write_math_solution
from backend.services.rus_grader import grade_izlozhenie, grade_sochinenie

router = APIRouter(tags=["grade-part2"])


class GradePart2Request(BaseModel):
    taskText: str = ""
    studentAnswer: str = ""
    correctSolution: str = ""
    fipiRubric: Optional[str] = None
    taskNum: Optional[int] = Field(None, ge=1, le=40)
    photoDataUrl: Optional[str] = None
    # aliases
    task_text: Optional[str] = None
    student_answer: Optional[str] = None
    correct_solution: Optional[str] = None
    fipi_rubric: Optional[str] = None
    task_num: Optional[int] = None
    photo_data_url: Optional[str] = None


class GradePart2Out(BaseModel):
    score: int
    fipi_reason: str
    student_feedback: str
    source: str = "llm"
    model_solution: str = ""


class MathSolutionRequest(BaseModel):
    taskText: str = ""
    correctSolution: str = ""
    taskNum: Optional[int] = Field(None, ge=1, le=40)
    photoDataUrl: Optional[str] = None
    task_text: Optional[str] = None
    correct_solution: Optional[str] = None
    task_num: Optional[int] = None
    photo_data_url: Optional[str] = None


class MathSolutionOut(BaseModel):
    solution: str
    answer: str = ""
    source: str = "llm"


class GradeRusRequest(BaseModel):
    kind: Literal["izlozhenie", "sochinenie"] = "izlozhenie"
    taskText: str = ""
    studentAnswer: str = ""
    sourceText: str = ""
    photoDataUrl: Optional[str] = None
    task_text: Optional[str] = None
    student_answer: Optional[str] = None
    source_text: Optional[str] = None
    photo_data_url: Optional[str] = None


class GradeRusOut(BaseModel):
    score: int
    max_score: int = 7
    fipi_reason: str
    student_feedback: str
    source: str = "llm"
    criteria: dict[str, int] = Field(default_factory=dict)


def _pick(*vals: Any) -> str:
    for v in vals:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


@router.post("/api/v1/grade-part2", response_model=GradePart2Out)
async def grade_part2(
    payload: GradePart2Request,
    _user: User = Depends(require_teacher_or_student),
):
    num = payload.taskNum if payload.taskNum is not None else payload.task_num
    try:
        task_num = int(num or 0)
    except (TypeError, ValueError):
        task_num = 0
    rubric = _pick(payload.fipiRubric, payload.fipi_rubric) or fipi_rubric_for(task_num)
    result = await grade_part2_task(
        task_text=_pick(payload.taskText, payload.task_text),
        student_answer=_pick(payload.studentAnswer, payload.student_answer),
        correct_solution=_pick(payload.correctSolution, payload.correct_solution),
        fipi_rubric=rubric,
        task_num=task_num,
        photo_data_url=_pick(payload.photoDataUrl, payload.photo_data_url) or None,
    )
    return GradePart2Out(
        score=int(result.get("score") or 0),
        fipi_reason=str(result.get("fipi_reason") or ""),
        student_feedback=str(result.get("student_feedback") or ""),
        source=str(result.get("source") or "heuristic"),
        model_solution=str(result.get("model_solution") or ""),
    )


@router.post("/api/v1/grade-rus", response_model=GradeRusOut)
async def grade_rus(
    payload: GradeRusRequest,
    _user: User = Depends(require_teacher_or_student),
):
    """Проверка сжатого изложения (№1) или сочинения (№13). Сочинение за ученика не пишется."""
    kwargs = {
        "task_text": _pick(payload.taskText, payload.task_text),
        "source_text": _pick(payload.sourceText, payload.source_text),
        "student_answer": _pick(payload.studentAnswer, payload.student_answer),
        "photo_data_url": _pick(payload.photoDataUrl, payload.photo_data_url) or None,
    }
    if payload.kind == "sochinenie":
        result = await grade_sochinenie(**kwargs)
    else:
        result = await grade_izlozhenie(**kwargs)
    criteria = result.get("criteria") if isinstance(result.get("criteria"), dict) else {}
    clean: dict[str, int] = {}
    for key, val in criteria.items():
        try:
            clean[str(key)[:8]] = int(val)
        except (TypeError, ValueError):
            continue
    return GradeRusOut(
        score=int(result.get("score") or 0),
        max_score=int(result.get("max_score") or 7),
        fipi_reason=str(result.get("fipi_reason") or ""),
        student_feedback=str(result.get("student_feedback") or ""),
        source=str(result.get("source") or "heuristic"),
        criteria=clean,
    )


@router.post("/api/v1/math-solution", response_model=MathSolutionOut)
async def math_solution(
    payload: MathSolutionRequest,
    _user: User = Depends(require_teacher_or_student),
):
    """Полный ход решения — только математика, для учителя и разбора после сдачи."""
    num = payload.taskNum if payload.taskNum is not None else payload.task_num
    try:
        task_num = int(num or 0)
    except (TypeError, ValueError):
        task_num = 0
    task_text = _pick(payload.taskText, payload.task_text)
    if not task_text:
        raise HTTPException(status_code=400, detail="Нужно условие задания")
    try:
        result = await write_math_solution(
            task_text=task_text,
            correct_solution=_pick(payload.correctSolution, payload.correct_solution),
            task_num=task_num,
            photo_data_url=_pick(payload.photoDataUrl, payload.photo_data_url) or None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return MathSolutionOut(
        solution=str(result.get("solution") or ""),
        answer=str(result.get("answer") or ""),
        source=str(result.get("source") or "llm"),
    )
