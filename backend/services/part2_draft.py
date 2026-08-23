"""После сдачи: ИИ считает баллы ч.2, заносит решения (математика), проверяет изложение и сочинение."""

from __future__ import annotations

import json
from typing import Any

from backend.database import SessionLocal
from backend.models import Assignment, EduClass, Submission
from backend.services.grade_calculator import LIT_MAX, attach_to_review, normalize_subject
from backend.services.part2_grader import grade_part2_task
from backend.services.rus_grader import (
    grade_izlozhenie,
    grade_literacy,
    grade_sochinenie,
    payload_source,
)


def _as_num(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_questions(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [q for q in raw if isinstance(q, dict)]
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return [q for q in data if isinstance(q, dict)] if isinstance(data, list) else []


def _parse_answers(raw: Any) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return []
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    return [a for a in items if isinstance(a, dict)]


def _status_for_earned(earned: float, max_score: float) -> str:
    if earned <= 0:
        return "wrong"
    if earned + 1e-9 >= float(max_score or 0):
        return "correct"
    return "partial"


def _ai_blob(result: dict[str, Any]) -> dict[str, Any]:
    criteria = result.get("criteria")
    return {
        "score": result.get("score"),
        "fipi_reason": str(result.get("fipi_reason") or "")[:800],
        "student_feedback": str(result.get("student_feedback") or "")[:800],
        "model_solution": str(result.get("model_solution") or "")[:4000],
        "source": str(result.get("source") or "llm"),
        "criteria": criteria if isinstance(criteria, dict) else {},
    }


def _apply_result(
    it: dict[str, Any],
    result: dict[str, Any],
    max_score: float,
    *,
    commit_score: bool,
) -> None:
    earned = _as_float(result.get("score"))
    cap = _as_float(max_score or it.get("max_score") or 0)
    earned = max(0.0, min(cap, earned))
    it["max_score"] = cap or it.get("max_score")
    it["ai_grade"] = _ai_blob(result)
    if result.get("fipi_reason"):
        it["comment"] = str(result.get("fipi_reason"))[:400]
    if commit_score:
        it["earned"] = earned
        it["status"] = _status_for_earned(earned, cap)
    elif not it.get("teacher_override"):
        it["status"] = "pending_teacher"


def _is_math_p2(num: int, q: dict[str, Any]) -> bool:
    part = _as_num(q.get("part") or (2 if num >= 20 else 1))
    return part == 2 or (20 <= num <= 25)


async def grade_submission_draft(submission_id: int) -> None:
    db = SessionLocal()
    try:
        row = db.query(Submission).filter(Submission.id == submission_id).first()
        if not row:
            return
        assignment = db.query(Assignment).filter(Assignment.id == row.assignment_id).first()
        if not assignment:
            return
        mode = str(getattr(assignment, "grading_mode", "") or "")
        if mode not in ("ai_assist", "autopilot"):
            return
        classroom = db.query(EduClass).filter(EduClass.id == assignment.class_id).first()
        subject = getattr(classroom, "subject", None) if classroom is not None else None
        kind = normalize_subject(subject)
        commit_score = mode == "autopilot"
        questions = _parse_questions(assignment.questions_json)
        by_num = {_as_num(q.get("num") or q.get("task_number")): q for q in questions}
        answers = {_as_num(a.get("num")): a for a in _parse_answers(row.answers_json)}
        try:
            review = json.loads(row.ai_review_json or "{}") or {}
        except json.JSONDecodeError:
            review = {}
        if not isinstance(review, dict):
            review = {}
        items = review.get("items")
        if not isinstance(items, list):
            return
        changed = False
        izlo_text = str((answers.get(1) or {}).get("text") or "").strip()
        soch_text = str((answers.get(13) or {}).get("text") or "").strip()

        for it in items:
            if not isinstance(it, dict):
                continue
            if it.get("teacher_override"):
                continue
            num = _as_num(it.get("num"))
            q = by_num.get(num) or {}
            ans = answers.get(num) or {}
            text = str(ans.get("text") or "").strip()
            photo = str(ans.get("photo_data_url") or "").strip()
            if not text and not photo:
                continue

            if kind == "russian" and num == 1:
                result = await grade_izlozhenie(
                    task_text=str(q.get("text") or ""),
                    source_text=payload_source(q, "listening_text"),
                    student_answer=text,
                    photo_data_url=photo or None,
                )
                _apply_result(it, result, float(it.get("max_score") or q.get("max_score") or 7), commit_score=commit_score)
                izlo_text = text
                changed = True
                continue
            if kind == "russian" and num == 13:
                result = await grade_sochinenie(
                    task_text=str(q.get("text") or ""),
                    source_text=payload_source(q, "reading_text", "source_text"),
                    student_answer=text,
                    photo_data_url=photo or None,
                )
                _apply_result(it, result, float(it.get("max_score") or q.get("max_score") or 7), commit_score=commit_score)
                soch_text = text
                changed = True
                continue
            if kind != "russian" and _is_math_p2(num, q):
                result = await grade_part2_task(
                    task_text=str(q.get("text") or ""),
                    student_answer=text,
                    correct_solution=str(q.get("solution") or q.get("answer") or ""),
                    task_num=num,
                    photo_data_url=photo or None,
                )
                _apply_result(it, result, float(it.get("max_score") or q.get("max_score") or 2), commit_score=commit_score)
                changed = True

        if kind == "russian" and (izlo_text or soch_text):
            lit = await grade_literacy(izlo_text=izlo_text, soch_text=soch_text)
            review["literacy"] = {
                "gk1": lit.get("gk1"),
                "gk2": lit.get("gk2"),
                "gk3": lit.get("gk3"),
                "gk4": lit.get("gk4"),
                "fk1": lit.get("fk1"),
                "fipi_reason": str(lit.get("fipi_reason") or "")[:800],
            }
            if lit.get("literacy_score") is not None:
                review["literacy_score"] = lit.get("literacy_score")
            changed = True

        if not changed:
            return
        primary = 0.0
        pending = False
        for it in items:
            if not isinstance(it, dict):
                continue
            primary += _as_float(it.get("earned"))
            if "pending" in str(it.get("status") or "").lower():
                pending = True
        if kind == "russian" and review.get("literacy_score") is not None and commit_score:
            primary += max(0.0, min(float(LIT_MAX), _as_float(review.get("literacy_score"))))
        review["auto_score"] = primary
        review = attach_to_review(review, subject, score=primary)
        row.score = primary
        row.ai_review_json = json.dumps(review, ensure_ascii=False)
        if mode == "autopilot" and not pending:
            row.status = "graded"
        else:
            row.status = "ai_reviewed"
        db.add(row)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
