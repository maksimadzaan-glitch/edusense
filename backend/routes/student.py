"""Кабинет ученика: join по коду класса/работы + список заданий."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Assignment, ClassStudent, EduClass, Submission
from backend.schemas.edu import (
    StudentJoinAssignmentOut,
    StudentJoinOut,
    StudentJoinRequest,
    StudentLeaderRowOut,
    StudentStatsOut,
    StudentTaskCardOut,
    StudentTasksOut,
)
from backend.routes.assignments import (
    _answers_locked,
    _settings_of,
    _student_allowed,
)
from backend.services.classroom import ensure_edu_class, normalize_student_name
from backend.services.deadlines import utc_aware
from backend.services.grade_calculator import result_from_review

router = APIRouter(prefix="/api/student", tags=["student"])


def _questions_count(questions_json: Optional[str]) -> int:
    try:
        data = json.loads(questions_json or "[]")
    except json.JSONDecodeError:
        return 0
    return len(data) if isinstance(data, list) else 0


def _accepting_of(row: Assignment) -> bool:
    if getattr(row, "accepting_submissions", True) is False:
        return False
    if str(getattr(row, "status", "") or "").lower() == "closed":
        return False
    return True


def _deadline_of(row: Assignment) -> Optional[datetime]:
    return getattr(row, "deadline", None)


def _timer_of(row: Assignment) -> Optional[int]:
    return getattr(row, "timer_minutes", None)


def _max_score_from_review(ai_review_json: Optional[str]) -> Optional[float]:
    if not ai_review_json:
        return None
    try:
        review = json.loads(ai_review_json)
    except json.JSONDecodeError:
        return None
    if isinstance(review, dict) and review.get("max_score") is not None:
        try:
            return float(review["max_score"])
        except (TypeError, ValueError):
            return None
    return None


def _parse_review(ai_review_json: Optional[str]) -> Optional[dict[str, Any]]:
    if not ai_review_json:
        return None
    try:
        review = json.loads(ai_review_json)
    except json.JSONDecodeError:
        return None
    return review if isinstance(review, dict) else None


def _review_summary(ai_review_json: Optional[str]) -> Optional[str]:
    review = _parse_review(ai_review_json)
    if not review:
        return None
    items = review.get("items")
    if not isinstance(items, list):
        return None
    correct = sum(1 for it in items if isinstance(it, dict) and it.get("status") == "correct")
    wrong = sum(1 for it in items if isinstance(it, dict) and it.get("status") == "wrong")
    pending = sum(
        1
        for it in items
        if isinstance(it, dict) and str(it.get("status") or "").endswith("pending")
    )
    bits: list[str] = []
    if correct:
        bits.append(f"верно {correct}")
    if wrong:
        bits.append(f"ошибки {wrong}")
    if pending:
        bits.append(f"на проверке {pending}")
    return " · ".join(bits) if bits else None


def _grade_from_scores(
    score: Optional[float],
    max_score: Optional[float],
    *,
    subject: Optional[str] = None,
    review: Optional[dict[str, Any]] = None,
    teacher_score: Optional[float] = None,
) -> Optional[str]:
    oge = result_from_review(subject, review, score=score, teacher_score=teacher_score)
    if oge.get("grade"):
        return str(oge["grade"])
    if score is None or max_score is None:
        return None
    try:
        mx = float(max_score)
        if mx <= 0:
            return None
        pct = 100.0 * float(score) / mx
    except (TypeError, ValueError):
        return None
    if pct >= 85:
        return "5"
    if pct >= 70:
        return "4"
    if pct >= 50:
        return "3"
    return "2"


def _score_percent(score: Optional[float], max_score: Optional[float]) -> Optional[float]:
    if score is None or max_score is None:
        return None
    try:
        mx = float(max_score)
        if mx <= 0:
            return None
        return round(100.0 * float(score) / mx, 1)
    except (TypeError, ValueError):
        return None


def _find_class_or_assignment(
    db: Session, code: str
) -> tuple[EduClass, Optional[Assignment], str]:
    """Вернуть (classroom, assignment|None, join_kind)."""
    normalized = (code or "").strip().upper()
    if not normalized:
        raise HTTPException(status_code=400, detail="Укажите код")

    assignment = db.query(Assignment).filter(Assignment.code == normalized).first()
    if assignment:
        if assignment.status == "draft":
            raise HTTPException(status_code=404, detail="Работа с таким кодом не найдена")
        classroom = db.query(EduClass).filter(EduClass.id == assignment.class_id).first()
        if not classroom:
            raise HTTPException(status_code=404, detail="Класс работы не найден")
        return classroom, assignment, "assignment"

    try:
        classroom = ensure_edu_class(db, class_code=normalized)
    except HTTPException:
        raise HTTPException(
            status_code=404, detail="Класс или работа с таким кодом не найдены"
        ) from None
    return classroom, None, "class"


def _ensure_roster(db: Session, classroom: EduClass, name: str) -> ClassStudent:
    """Добавить ученика в ростер, если ещё нет (сопоставление без учёта регистра)."""
    key = normalize_student_name(name).casefold()
    rows = db.query(ClassStudent).filter(ClassStudent.class_id == classroom.id).all()
    for row in rows:
        if normalize_student_name(row.name).casefold() == key:
            return row
    row = ClassStudent(class_id=classroom.id, name=normalize_student_name(name))
    db.add(row)
    db.flush()
    return row


def _assignment_brief(row: Assignment, classroom: EduClass) -> StudentJoinAssignmentOut:
    deadline = utc_aware(_deadline_of(row))
    timer = _timer_of(row)
    return StudentJoinAssignmentOut(
        id=row.id,
        code=row.code,
        title=row.title,
        status=row.status,
        accepting_submissions=_accepting_of(row),
        questions_count=_questions_count(row.questions_json),
        deadline=deadline,
        deadline_at=deadline,
        timer_minutes=timer,
        time_limit_minutes=timer,
        subject=classroom.subject,
    )


def _submission_matches_name(sub: Submission, name_key: str) -> bool:
    return normalize_student_name(sub.student_name).casefold() == name_key


def _short_student_name(name: str) -> str:
    parts = [p for p in str(name or "").split() if p]
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1][0]}."
    return str(name or "Ученик").strip() or "Ученик"


def _streak_from_days(days: set) -> int:
    if not days:
        return 0
    today = datetime.now(timezone.utc).date()
    cursor = today if today in days else today - timedelta(days=1)
    n = 0
    while cursor in days:
        n += 1
        cursor -= timedelta(days=1)
    return n


def _class_leaderboard(classroom: EduClass, subs: list[Submission], you_name: str) -> list[StudentLeaderRowOut]:
    you_key = normalize_student_name(you_name).casefold()
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    by_key: dict[str, dict[str, Any]] = {}

    def bucket(raw_name: str) -> dict[str, Any]:
        nm = normalize_student_name(raw_name)
        key = nm.casefold()
        if key not in by_key:
            by_key[key] = {
                "name": nm,
                "days": set(),
                "week_score": 0.0,
                "all_score": 0.0,
                "week_n": 0,
            }
        return by_key[key]

    for row in getattr(classroom, "roster", None) or []:
        if getattr(row, "name", None):
            bucket(row.name)
    bucket(you_name)

    for s in subs:
        b = bucket(s.student_name)
        created = utc_aware(getattr(s, "created_at", None))
        score = float(s.score or 0)
        b["all_score"] += score
        if created:
            b["days"].add(created.date())
            if created >= week_ago:
                b["week_score"] += score
                b["week_n"] += 1

    use_week = any(v["week_n"] > 0 for v in by_key.values())
    rows: list[dict[str, Any]] = []
    for v in by_key.values():
        score = v["week_score"] if use_week else v["all_score"]
        rows.append(
            {
                "name": v["name"],
                "short_name": _short_student_name(v["name"]),
                "xp": int(round(score * 100)),
                "streak": _streak_from_days(v["days"]),
                "you": v["name"].casefold() == you_key,
            }
        )
    rows.sort(key=lambda r: (-r["xp"], -r["streak"], r["name"].casefold()))
    return [StudentLeaderRowOut(rank=i, **row) for i, row in enumerate(rows, start=1)]


@router.post("/join", response_model=StudentJoinOut, status_code=status.HTTP_200_OK)
def student_join(payload: StudentJoinRequest, db: Session = Depends(get_db)):
    name = normalize_student_name(payload.name)
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Укажите имя и фамилию")

    classroom, assignment, join_kind = _find_class_or_assignment(db, payload.code)

    if assignment and not _accepting_of(assignment):
        raise HTTPException(
            status_code=403,
            detail={
                "message": "Приём ответов закрыт",
                "closed": True,
                "title": assignment.title,
                "subject": classroom.subject,
                "code": assignment.code,
                "class_code": classroom.code,
            },
        )

    _ensure_roster(db, classroom, name)
    db.commit()

    student_id = str(uuid.uuid4())
    return StudentJoinOut(
        student_id=student_id,
        student_name=name,
        class_code=classroom.code,
        class_name=classroom.name,
        subject=classroom.subject,
        exam=classroom.target_exam,
        assignment=_assignment_brief(assignment, classroom) if assignment else None,
        join_kind=join_kind,  # type: ignore[arg-type]
    )


@router.get("/tasks", response_model=StudentTasksOut)
def student_tasks(
    class_code: str = Query(..., min_length=3, max_length=32),
    student_name: str = Query(..., min_length=2, max_length=120),
    db: Session = Depends(get_db),
):
    name = normalize_student_name(student_name)
    name_key = name.casefold()
    if len(name) < 2:
        raise HTTPException(status_code=400, detail="Укажите имя ученика")

    classroom = ensure_edu_class(db, class_code=class_code)
    db.commit()

    assignments = (
        db.query(Assignment)
        .filter(
            Assignment.class_id == classroom.id,
            Assignment.status.in_(("active", "closed")),
        )
        .order_by(Assignment.id.desc())
        .all()
    )

    assign_ids = [a.id for a in assignments]
    subs: list[Submission] = []
    if assign_ids:
        subs = (
            db.query(Submission)
            .filter(Submission.assignment_id.in_(assign_ids))
            .order_by(Submission.id.desc())
            .all()
        )

    # последняя сдача ученика по каждой работе
    latest_by_assign: dict[int, Submission] = {}
    for s in subs:
        if not _submission_matches_name(s, name_key):
            continue
        if s.assignment_id not in latest_by_assign:
            latest_by_assign[s.assignment_id] = s

    active: list[StudentTaskCardOut] = []
    completed: list[StudentTaskCardOut] = []
    accuracy_samples: list[float] = []

    for row in assignments:
        if not _student_allowed(row, name) and row.id not in latest_by_assign:
            continue
        deadline = utc_aware(_deadline_of(row))
        timer = _timer_of(row)
        qcount = _questions_count(row.questions_json)
        sub = latest_by_assign.get(row.id)
        locked = _answers_locked(row)
        hide_answers = bool((_settings_of(row) or {}).get("hide_answers"))

        if sub is not None:
            from backend.routes.assignments import (
                _personalized_question_list,
                _regrade_submission,
            )

            qs, _n = _personalized_question_list(row, classroom, name)
            sub = _regrade_submission(
                db, sub, qs, row.grading_mode, classroom.subject
            )
            mx = _max_score_from_review(sub.ai_review_json)
            review = _parse_review(sub.ai_review_json)
            oge = result_from_review(
                classroom.subject,
                review,
                score=sub.score,
                teacher_score=getattr(sub, "teacher_score", None),
            )
            pct = _score_percent(sub.score, mx)
            if pct is not None:
                accuracy_samples.append(pct)
            completed.append(
                StudentTaskCardOut(
                    id=row.id,
                    code=row.code,
                    title=row.title,
                    subject=classroom.subject,
                    exam=classroom.target_exam,
                    status=row.status,
                    accepting_submissions=_accepting_of(row),
                    questions_count=qcount,
                    deadline=deadline,
                    deadline_at=deadline,
                    timer_minutes=timer,
                    time_limit_minutes=timer,
                    badge="done",
                    score=sub.score,
                    max_score=mx,
                    grade=_grade_from_scores(
                        sub.score,
                        mx,
                        subject=classroom.subject,
                        review=review,
                        teacher_score=getattr(sub, "teacher_score", None),
                    ),
                    submitted_at=sub.created_at,
                    submission_id=sub.id,
                    has_review=(
                        False
                        if locked
                        else (
                            bool(review and isinstance(review.get("items"), list))
                            or bool(
                                getattr(sub, "teacher_comment", None)
                                or getattr(sub, "teacher_score", None) is not None
                            )
                        )
                    ),
                    review_summary=None if locked else _review_summary(sub.ai_review_json),
                    ai_review=None if locked else review,
                    teacher_score=getattr(sub, "teacher_score", None),
                    teacher_comment=getattr(sub, "teacher_comment", None),
                    teacher_reviewed_at=getattr(sub, "teacher_reviewed_at", None),
                    oge=oge,
                    hide_answers=hide_answers,
                    answers_locked=locked,
                )
            )
            continue

        # без сдачи — в активные, если приём открыт
        if _accepting_of(row) and row.status == "active":
            active.append(
                StudentTaskCardOut(
                    id=row.id,
                    code=row.code,
                    title=row.title,
                    subject=classroom.subject,
                    exam=classroom.target_exam,
                    status=row.status,
                    accepting_submissions=True,
                    questions_count=qcount,
                    deadline=deadline,
                    deadline_at=deadline,
                    timer_minutes=timer,
                    time_limit_minutes=timer,
                    badge="new",
                    hide_answers=hide_answers,
                    answers_locked=locked,
                )
            )

    stats = StudentStatsOut(
        completed_count=len(completed),
        avg_accuracy=round(sum(accuracy_samples) / len(accuracy_samples), 1)
        if accuracy_samples
        else None,
    )

    return StudentTasksOut(
        class_code=classroom.code,
        class_name=classroom.name,
        subject=classroom.subject,
        exam=classroom.target_exam,
        student_name=name,
        active=active,
        completed=completed,
        stats=stats,
        leaderboard=_class_leaderboard(classroom, subs, name),
    )
