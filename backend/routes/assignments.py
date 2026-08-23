import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Assignment, ClassStudent, EduClass, Submission
from backend.schemas.edu import (
    AssignmentListItem,
    AssignmentOut,
    AssignmentPatchRequest,
    AssignmentPublishRequest,
    StudentAssignmentOut,
    StudentQuestionOut,
    SubmissionAnswerView,
    SubmissionCreateRequest,
    SubmissionGradePatch,
    SubmissionListItem,
    SubmissionOut,
    AnswerKeyItem,
)
from backend.services.classroom import ensure_edu_class, normalize_student_name
from backend.services.codes import generate_edu_code
from backend.services.deadlines import deadline_passed, utc_aware, utc_naive
from backend.services.figures import attach_figure
from backend.services.grade_calculator import LIT_MAX, attach_to_review, normalize_subject
from backend.services.math_mutator import personalize_questions
from backend.services.part2_draft import grade_submission_draft
from backend.services.rus_grader import payload_source
from backend.services.beta_limits import assert_can_issue_variant

router = APIRouter(prefix="/api/assignments", tags=["assignments"])


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return bool(value)


def _deadline_of(row: Assignment) -> Optional[datetime]:
    return getattr(row, "deadline", None)


def _timer_of(row: Assignment) -> Optional[int]:
    return getattr(row, "timer_minutes", None)


def _shuffle_of(row: Assignment) -> bool:
    return _as_bool(getattr(row, "shuffle_variants", False), False)


def _accepting_of(row: Assignment) -> bool:
    return _as_bool(getattr(row, "accepting_submissions", True), True)


def _deadline_passed(row: Assignment) -> bool:
    """True, если дедлайн задан и уже прошёл. Naive в БД = UTC."""
    return deadline_passed(_deadline_of(row))


def _expected_of(row: Assignment) -> Optional[int]:
    val = getattr(row, "expected_students", None)
    if val is None:
        return None
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _settings_of(row: Assignment) -> dict[str, Any]:
    raw = getattr(row, "settings_json", None)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _dump_settings(
    *,
    block_copy: bool = False,
    hide_answers: bool = False,
    allowed_students: Optional[list[str]] = None,
) -> Optional[str]:
    names: list[str] = []
    for raw in allowed_students or []:
        name = normalize_student_name(str(raw or ""))
        if len(name) >= 2 and name not in names:
            names.append(name)
    payload = {
        "block_copy": bool(block_copy),
        "hide_answers": bool(hide_answers),
        "allowed_students": names,
    }
    if not payload["block_copy"] and not payload["hide_answers"] and not names:
        return None
    return json.dumps(payload, ensure_ascii=False)


def _student_allowed(row: Assignment, name: str) -> bool:
    names = _settings_of(row).get("allowed_students") or []
    if not isinstance(names, list) or not names:
        return True
    key = normalize_student_name(name).casefold()
    if len(key) < 2:
        return False
    return any(normalize_student_name(str(n or "")).casefold() == key for n in names)


def _answers_locked(row: Assignment) -> bool:
    if not _as_bool(_settings_of(row).get("hide_answers"), False):
        return False
    if _deadline_of(row) is not None:
        return not _deadline_passed(row)
    return _accepting_of(row)


def _visible_ai_review(row: Assignment, review: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not review or _answers_locked(row):
        return None
    return review


def _duration_seconds(started_at: Optional[datetime], submitted_at: Optional[datetime]) -> Optional[int]:
    if not started_at or not submitted_at:
        return None
    try:
        delta = submitted_at - started_at
        secs = int(delta.total_seconds())
        return secs if secs >= 0 else None
    except Exception:
        return None


def _questions_by_num(questions_json: Optional[str | list]) -> dict[int, dict[str, Any]]:
    if isinstance(questions_json, list):
        raw = questions_json
    else:
        try:
            raw = json.loads(questions_json or "[]")
        except json.JSONDecodeError:
            raw = []
    if not isinstance(raw, list):
        return {}
    out: dict[int, dict[str, Any]] = {}
    for q in raw:
        if not isinstance(q, dict):
            continue
        try:
            num = int(q.get("num") or 0)
        except (TypeError, ValueError):
            continue
        if num:
            out[num] = q
    return out


def _question_solution(q: dict[str, Any], *, max_len: int = 2000) -> Optional[str]:
    for key in ("solution", "template_solution", "correct_solution", "explanation"):
        val = q.get(key)
        if val is not None and str(val).strip():
            s = str(val).strip()
            return s[: max_len - 1] + "…" if max_len and len(s) > max_len else s
    payload = q.get("payload")
    if isinstance(payload, dict):
        for key in ("explanation_template", "solution", "template_solution"):
            val = payload.get(key)
            if val is not None and str(val).strip():
                s = str(val).strip()
                return s[: max_len - 1] + "…" if max_len and len(s) > max_len else s
    return None


def _question_part(q: dict[str, Any], num: int) -> int:
    try:
        part = int(q.get("part") or 0)
    except (TypeError, ValueError):
        part = 0
    if part in (1, 2):
        return part
    return 2 if num >= 20 else 1


def _question_max_score(q: dict[str, Any], num: int, part: int) -> int:
    try:
        mx = int(q.get("max_score") or q.get("maxScore") or 0)
    except (TypeError, ValueError):
        mx = 0
    if mx > 0:
        return mx
    return 2 if part == 2 or num >= 20 else 1


def _review_items_by_num(review_json: Optional[str]) -> dict[int, dict[str, Any]]:
    try:
        review = json.loads(review_json or "{}")
    except json.JSONDecodeError:
        review = {}
    if not isinstance(review, dict):
        return {}
    items = review.get("items")
    if not isinstance(items, list):
        return {}
    out: dict[int, dict[str, Any]] = {}
    for it in items:
        if not isinstance(it, dict):
            continue
        try:
            num = int(it.get("num") or 0)
        except (TypeError, ValueError):
            continue
        if num:
            out[num] = it
    return out


def _status_for_earned(earned: float, max_score: float) -> str:
    if earned <= 0:
        return "wrong"
    if earned + 1e-9 >= float(max_score or 0):
        return "correct"
    return "partial"


def _review_has_pending(review: dict[str, Any]) -> bool:
    items = review.get("items")
    if not isinstance(items, list):
        return False
    for it in items:
        if not isinstance(it, dict):
            continue
        if "pending" in str(it.get("status") or "").lower():
            return True
    return False


def _criteria_blob(raw: Any) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, int] = {}
    for key, val in raw.items():
        name = str(key or "").strip().lower()[:8]
        if not name:
            continue
        try:
            out[name] = int(val)
        except (TypeError, ValueError):
            continue
        if len(out) >= 8:
            break
    return out


def _question_source_text(q: dict[str, Any], num: int) -> Optional[str]:
    if num == 1:
        text = payload_source(q, "listening_text")
    elif num == 13:
        text = payload_source(q, "reading_text", "source_text")
    else:
        return None
    return text or None


def _apply_item_score(
    review: dict[str, Any],
    q_by_num: dict[int, dict[str, Any]],
    item_num: int,
    item_earned: float,
    *,
    item_comment: Optional[str] = None,
    ai_grade: Optional[dict[str, Any]] = None,
) -> float:
    items = review.get("items")
    if not isinstance(items, list):
        items = []
        review["items"] = items
    found: Optional[dict[str, Any]] = None
    for it in items:
        if isinstance(it, dict):
            try:
                if int(it.get("num") or 0) == item_num:
                    found = it
                    break
            except (TypeError, ValueError):
                continue
    q = q_by_num.get(item_num) or {}
    part = _question_part(q, item_num)
    try:
        max_score = float(
            (found or {}).get("max_score")
            or q.get("max_score")
            or q.get("maxScore")
            or (2 if part == 2 or item_num >= 20 else 1)
        )
    except (TypeError, ValueError):
        max_score = 2.0 if part == 2 or item_num >= 20 else 1.0
    earned = max(0.0, min(max_score, float(item_earned)))
    if found is None:
        found = {"num": item_num, "max_score": max_score}
        items.append(found)
    found["max_score"] = max_score
    found["earned"] = earned
    found["status"] = _status_for_earned(earned, max_score)
    found["teacher_override"] = True
    if item_comment is not None:
        found["comment"] = str(item_comment).strip()
    if isinstance(ai_grade, dict) and ai_grade:
        found["ai_grade"] = {
            "score": ai_grade.get("score"),
            "fipi_reason": str(ai_grade.get("fipi_reason") or "")[:800],
            "student_feedback": str(ai_grade.get("student_feedback") or "")[:800],
            "model_solution": str(ai_grade.get("model_solution") or "")[:4000],
            "source": str(ai_grade.get("source") or "")[:40],
            "criteria": _criteria_blob(ai_grade.get("criteria")),
        }
    primary = 0.0
    for it in items:
        if not isinstance(it, dict):
            continue
        try:
            primary += float(it.get("earned") or 0)
        except (TypeError, ValueError):
            continue
    return primary


def _question_answer(q: dict[str, Any]) -> str:
    for key in ("answer", "correct_answer", "template_answer"):
        val = q.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    acc = q.get("acceptable_answers")
    if isinstance(acc, list) and acc:
        first = acc[0]
        if first is not None and str(first).strip():
            return str(first).strip()
    payload = q.get("payload")
    if isinstance(payload, dict):
        mv = payload.get("mutator_values")
        if isinstance(mv, dict) and mv.get("answer") is not None and str(mv.get("answer")).strip():
            return str(mv.get("answer")).strip()
        if payload.get("answer") is not None and str(payload.get("answer")).strip():
            return str(payload.get("answer")).strip()
    return ""


def _answers_for_teacher(
    answers_json: Optional[str],
    q_by_num: dict[int, dict[str, Any]],
    review_json: Optional[str] = None,
) -> list[SubmissionAnswerView]:
    try:
        data = json.loads(answers_json or "{}")
    except json.JSONDecodeError:
        data = {}
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []
    review_by_num = _review_items_by_num(review_json)
    out: list[SubmissionAnswerView] = []
    for a in items:
        if not isinstance(a, dict):
            continue
        try:
            num = int(a.get("num") or 0)
        except (TypeError, ValueError):
            continue
        if not num:
            continue
        photo = a.get("photo_data_url")
        has_photo = bool(photo)
        q = q_by_num.get(num) or {}
        part = _question_part(q, num)
        q_text = str(q.get("text") or "").strip()
        q_limit = 2000 if part == 2 else 600
        if len(q_text) > q_limit:
            q_text = q_text[: q_limit - 1] + "…"
        max_score = _question_max_score(q, num, part)
        rev = review_by_num.get(num) or {}
        earned_raw = rev.get("earned")
        try:
            earned = float(earned_raw) if earned_raw is not None else None
        except (TypeError, ValueError):
            earned = None
        ai_blob = rev.get("ai_grade") if isinstance(rev.get("ai_grade"), dict) else None
        out.append(
            SubmissionAnswerView(
                num=num,
                text=str(a.get("text") or "").strip(),
                has_photo=has_photo,
                photo_data_url=str(photo) if has_photo else None,
                question_text=q_text or None,
                topic=str(q.get("topic") or "").strip() or None,
                correct_answer=_question_answer(q) or None,
                part=part,
                solution=_question_solution(q),
                max_score=int(rev.get("max_score") or max_score),
                earned=earned,
                status=str(rev.get("status") or "").strip() or None,
                comment=str(rev.get("comment") or "").strip() or None,
                ai_grade=ai_blob,
                source_text=_question_source_text(q, num),
                teacher_override=bool(rev.get("teacher_override")),
            )
        )
    out.sort(key=lambda x: x.num)
    return out


def _submission_list_item(
    s: Submission,
    q_by_num: Optional[dict[int, dict[str, Any]]] = None,
) -> SubmissionListItem:
    return SubmissionListItem(
        id=s.id,
        student_name=s.student_name,
        score=s.score,
        max_score=_max_score_from_review(s.ai_review_json),
        status=s.status,
        submitted_at=s.created_at,
        started_at=getattr(s, "started_at", None),
        duration_seconds=_duration_seconds(getattr(s, "started_at", None), s.created_at),
        review_summary=_review_summary(s.ai_review_json),
        teacher_score=getattr(s, "teacher_score", None),
        teacher_comment=getattr(s, "teacher_comment", None),
        teacher_reviewed_at=getattr(s, "teacher_reviewed_at", None),
        answers=_answers_for_teacher(s.answers_json, q_by_num or {}, s.ai_review_json),
    )


def _resolve_deadline(payload: AssignmentPublishRequest | AssignmentPatchRequest) -> Optional[datetime]:
    return getattr(payload, "deadline_at", None) or getattr(payload, "deadline", None)


def _resolve_timer(payload: AssignmentPublishRequest | AssignmentPatchRequest) -> Optional[int]:
    return getattr(payload, "time_limit_minutes", None) or getattr(payload, "timer_minutes", None)


def _strip_answers(questions: list[dict[str, Any]]) -> list[StudentQuestionOut]:
    out: list[StudentQuestionOut] = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        fig_q = attach_figure(q)
        out.append(
            StudentQuestionOut(
                num=int(fig_q.get("num") or len(out) + 1),
                part=int(fig_q.get("part") or 1),
                type=str(fig_q.get("type") or "Краткий ответ"),
                topic=str(fig_q.get("topic") or "Общее"),
                text=str(fig_q.get("text") or ""),
                max_score=int(fig_q.get("max_score") or fig_q.get("maxScore") or 1),
                figure_kind=fig_q.get("figure_kind"),
                figure_svg=fig_q.get("figure_svg"),
                payload=fig_q.get("payload") if isinstance(fig_q.get("payload"), dict) else None,
                kim_order=bool(fig_q.get("kim_order")),
            )
        )
    return out


def _assignment_out(row: Assignment, classroom: Optional[EduClass] = None) -> AssignmentOut:
    try:
        questions = json.loads(row.questions_json or "[]")
    except json.JSONDecodeError:
        questions = []
    if not isinstance(questions, list):
        questions = []
    questions = [attach_figure(q) if isinstance(q, dict) else q for q in questions]
    deadline = utc_aware(_deadline_of(row))
    timer = _timer_of(row)

    settings = _settings_of(row)
    allowed = settings.get("allowed_students") if isinstance(settings.get("allowed_students"), list) else []
    return AssignmentOut(
        id=row.id,
        class_id=row.class_id,
        title=row.title,
        code=row.code,
        deadline=deadline,
        deadline_at=deadline,
        timer_minutes=timer,
        time_limit_minutes=timer,
        shuffle_variants=_shuffle_of(row),
        accepting_submissions=_accepting_of(row),
        expected_students=_expected_of(row),
        questions=questions,
        question_count=len(questions),
        grading_mode=row.grading_mode,
        status=row.status,
        class_code=classroom.code if classroom else None,
        subject=classroom.subject if classroom else None,
        target_exam=classroom.target_exam if classroom else None,
        student_url=f"/student?code={row.code}",
        block_copy=_as_bool(settings.get("block_copy"), False),
        hide_answers=_as_bool(settings.get("hide_answers"), False),
        answers_locked=_answers_locked(row),
        allowed_students=[str(n) for n in allowed if str(n).strip()] or None,
    )


def _latest_named_submission(db: Session, assignment_id: int, name: str) -> Optional[Submission]:
    key = normalize_student_name(name).casefold()
    if len(key) < 2:
        return None
    rows = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id)
        .order_by(Submission.id.desc())
        .all()
    )
    for row in rows:
        if normalize_student_name(row.student_name or "").casefold() == key:
            return row
    return None


def _parse_submission_answers(answers_json: Optional[str]) -> list[dict[str, Any]]:
    try:
        data = json.loads(answers_json or "{}")
    except json.JSONDecodeError:
        return []
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    return [a for a in items if isinstance(a, dict)]


def _regrade_submission(
    db: Session,
    sub: Submission,
    questions: list[dict[str, Any]],
    grading_mode: str,
    subject: Optional[str] = None,
) -> Submission:
    """Пересчитать авто-балл по сохранённым ответам (без новой попытки)."""
    if getattr(sub, "teacher_score", None) is not None:
        return sub
    answers = _parse_submission_answers(sub.answers_json)
    if not answers:
        return sub
    earned, total, review, status_val = _auto_check(questions, answers, grading_mode)
    review = attach_to_review(review, subject, score=earned)
    prev_score = sub.score
    prev_json = sub.ai_review_json or ""
    new_json = json.dumps(review, ensure_ascii=False)
    if prev_score == earned and prev_json == new_json:
        return sub
    if prev_score is not None and earned + 1e-9 < float(prev_score):
        return sub
    sub.score = earned
    sub.status = status_val
    sub.ai_review_json = new_json
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def _raw_questions(row: Assignment) -> list[dict[str, Any]]:
    try:
        questions = json.loads(row.questions_json or "[]")
    except json.JSONDecodeError:
        questions = []
    return questions if isinstance(questions, list) else []


def _personalized_question_list(
    row: Assignment,
    classroom: Optional[EduClass],
    student_name: Optional[str],
) -> tuple[list[dict[str, Any]], int]:
    questions = _raw_questions(row)
    name = normalize_student_name(student_name or "") if student_name else ""
    if not _shuffle_of(row) or len(name) < 2:
        return questions, 0
    subject = classroom.subject if classroom is not None else None
    subj = str(subject or "").strip().lower().replace("ё", "е")
    if "русск" in subj or subj in {"russian", "rus", "ru"}:
        try:
            from backend.universal.variant_builder import oge_rus_remix_test_for_seed

            remixed = oge_rus_remix_test_for_seed(
                questions,
                assignment_id=int(row.id),
                student_name=name,
                difficulty=getattr(row, "difficulty", None),
            )
            if remixed and len(remixed) >= 10:
                mutated, extra = personalize_questions(
                    remixed,
                    assignment_id=int(row.id),
                    student_name=name,
                    subject=subject,
                    enabled=True,
                )
                return mutated, extra + 1
        except Exception:
            pass
    return personalize_questions(
        questions,
        assignment_id=int(row.id),
        student_name=name,
        subject=subject,
        enabled=True,
    )


def _normalize_key(value: str) -> str:
    from backend.universal.answer_normalize import normalize_answer

    return normalize_answer(value)


def _auto_check(
    questions: list[dict[str, Any]],
    answers: list[dict[str, Any]],
    grading_mode: str,
) -> tuple[float, float, dict[str, Any], str]:
    from backend.universal.answer_normalize import (
        answers_equal,
        digits_any_order_equal,
        matches_any,
        oge_rus_digits_any_order,
    )

    by_num = {int(a.get("num")): a for a in answers if a.get("num") is not None}
    details: list[dict[str, Any]] = []
    earned = 0.0
    total = 0.0
    needs_teacher = False

    for q in questions:
        if not isinstance(q, dict):
            continue
        num = int(q.get("num") or 0)
        max_score = float(q.get("max_score") or q.get("maxScore") or 1)
        total += max_score
        ans = by_num.get(num) or {}
        student_text = str(ans.get("text") or "").strip()
        photo = ans.get("photo_data_url")
        key = str(q.get("answer") or "")
        part = int(q.get("part") or 1)
        acceptable = q.get("acceptable_answers")
        if isinstance(acceptable, str):
            try:
                import json as _json

                acceptable = _json.loads(acceptable)
            except Exception:
                acceptable = None
        extras: list[Any] = list(acceptable) if isinstance(acceptable, list) else []
        pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        mv = pl.get("mutator_values") if isinstance(pl.get("mutator_values"), dict) else {}
        if mv.get("answer") is not None:
            extras.append(mv.get("answer"))

        item: dict[str, Any] = {
            "num": num,
            "max_score": max_score,
            "earned": 0.0,
            "status": "pending",
            "comment": "",
        }

        if part == 1 and key and student_text and not photo:
            ok = matches_any(student_text, key, extras)
            if not ok and oge_rus_digits_any_order(q):
                ok = digits_any_order_equal(student_text, key)
                if not ok:
                    ok = any(digits_any_order_equal(student_text, k) for k in extras)
            if ok:
                item["earned"] = max_score
                item["status"] = "correct"
                item["comment"] = "Верно"
                earned += max_score
            else:
                item["status"] = "wrong"
                item["comment"] = "Неверно"
        elif photo or part == 2 or not key:
            needs_teacher = True
            if grading_mode == "autopilot" and photo:
                item["status"] = "ai_pending"
                item["comment"] = "Фото принято · нужна проверка"
            elif grading_mode == "ai_assist":
                item["status"] = "ai_pending"
                item["comment"] = "Ожидает AI + учителя"
            else:
                item["status"] = "manual_pending"
                item["comment"] = "Ожидает учителя"
        else:
            item["status"] = "empty"
            item["comment"] = "Нет ответа"

        details.append(item)

    review = {"items": details, "auto_score": earned, "max_score": total}
    if needs_teacher and grading_mode != "autopilot":
        status_val = "ai_reviewed" if grading_mode == "ai_assist" else "pending"
    elif needs_teacher:
        status_val = "ai_reviewed"
    else:
        status_val = "graded"
    return earned, total, review, status_val


def _questions_count(questions_json: Optional[str]) -> int:
    try:
        questions = json.loads(questions_json or "[]")
    except json.JSONDecodeError:
        return 0
    return len(questions) if isinstance(questions, list) else 0


def _review_summary(ai_review_json: Optional[str]) -> Optional[str]:
    if not ai_review_json:
        return None
    try:
        review = json.loads(ai_review_json)
    except json.JSONDecodeError:
        return None
    if not isinstance(review, dict):
        return None
    items = review.get("items")
    if not isinstance(items, list) or not items:
        auto = review.get("auto_score")
        mx = review.get("max_score")
        if auto is not None and mx is not None:
            return f"авто {auto}/{mx}"
        return None
    correct = sum(1 for it in items if isinstance(it, dict) and it.get("status") == "correct")
    wrong = sum(1 for it in items if isinstance(it, dict) and it.get("status") == "wrong")
    pending = sum(
        1
        for it in items
        if isinstance(it, dict)
        and str(it.get("status") or "").endswith("pending")
    )
    bits: list[str] = []
    if correct:
        bits.append(f"верно {correct}")
    if wrong:
        bits.append(f"ошибки {wrong}")
    if pending:
        bits.append(f"на проверке {pending}")
    return " · ".join(bits) if bits else None


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


def _get_assignment_row(db: Session, code: str, *, for_student: bool = False) -> Assignment:
    normalized = code.strip().upper()
    row = db.query(Assignment).filter(Assignment.code == normalized).first()

    if not row:
        classroom = db.query(EduClass).filter(EduClass.code == normalized).first()
        if classroom:
            q = db.query(Assignment).filter(Assignment.class_id == classroom.id)
            if for_student:
                q = q.filter(Assignment.status.in_(("active", "closed")))
            row = q.order_by(Assignment.id.desc()).first()

    if not row:
        raise HTTPException(status_code=404, detail="Работа с таким кодом не найдена")

    if for_student and row.status == "draft":
        raise HTTPException(status_code=404, detail="Работа с таким кодом не найдена")

    return row


@router.post("/publish", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def publish_assignment(payload: AssignmentPublishRequest, db: Session = Depends(get_db)):
    classroom = ensure_edu_class(db, class_id=payload.class_id, class_code=payload.class_code)
    assert_can_issue_variant(db, classroom.id)

    questions: list[dict[str, Any]] = []
    for i, q in enumerate(payload.questions, start=1):
        if not isinstance(q, dict) or not str(q.get("text") or "").strip():
            raise HTTPException(status_code=400, detail=f"Некорректная задача #{i}")
        # сохраняем полный dict (answer / acceptable_answers / payload) — strip только на student GET
        item = dict(q)
        if item.get("num") is None:
            item["num"] = i
        if item.get("part") is None:
            item["part"] = 1
        if item.get("max_score") is None and item.get("maxScore") is not None:
            item["max_score"] = item.get("maxScore")
        questions.append(attach_figure(item))

    try:
        code = generate_edu_code(db, Assignment, "code")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    deadline = utc_naive(_resolve_deadline(payload))
    timer = _resolve_timer(payload)

    roster_n = (
        db.query(ClassStudent).filter(ClassStudent.class_id == classroom.id).count()
    )
    allowed = [
        normalize_student_name(str(n or ""))
        for n in (payload.allowed_students or [])
        if len(normalize_student_name(str(n or ""))) >= 2
    ]
    expected = len(allowed) if allowed else (int(roster_n) if roster_n and roster_n > 0 else None)

    row = Assignment(
        class_id=classroom.id,
        title=payload.title.strip(),
        code=code,
        deadline=deadline,
        timer_minutes=timer,
        questions_json=json.dumps(questions, ensure_ascii=False),
        grading_mode=payload.grading_mode,
        status="active",
        shuffle_variants=bool(payload.shuffle_variants),
        difficulty=(payload.difficulty or "medium"),
        accepting_submissions=True,
        expected_students=expected,
        settings_json=_dump_settings(
            block_copy=bool(payload.block_copy),
            hide_answers=bool(payload.hide_answers),
            allowed_students=payload.allowed_students,
        ),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _assignment_out(row, classroom)


@router.patch("/{code}", response_model=AssignmentOut)
def patch_assignment(code: str, payload: AssignmentPatchRequest, db: Session = Depends(get_db)):
    row = _get_assignment_row(db, code, for_student=False)
    classroom = db.query(EduClass).filter(EduClass.id == row.class_id).first()

    deadline = utc_naive(_resolve_deadline(payload))
    if deadline is not None:
        row.deadline = deadline

    if payload.extend_deadline_days:
        base = utc_naive(row.deadline) or datetime.now(timezone.utc).replace(tzinfo=None)
        row.deadline = base + timedelta(days=int(payload.extend_deadline_days))

    timer = _resolve_timer(payload)
    if timer is not None:
        row.timer_minutes = timer

    if payload.shuffle_variants is not None:
        row.shuffle_variants = bool(payload.shuffle_variants)

    if payload.expected_students is not None:
        row.expected_students = payload.expected_students

    if payload.accepting_submissions is not None:
        row.accepting_submissions = bool(payload.accepting_submissions)
        if not row.accepting_submissions and row.status == "active":
            row.status = "closed"

    if payload.status is not None:
        row.status = payload.status
        if payload.status == "closed":
            row.accepting_submissions = False
        elif payload.status == "active":
            if payload.accepting_submissions is None:
                row.accepting_submissions = True
        elif payload.status == "draft":
            row.accepting_submissions = False

    db.commit()
    db.refresh(row)
    return _assignment_out(row, classroom)


@router.get("/by-class/{class_code}", response_model=list[AssignmentListItem])
def list_assignments_by_class(class_code: str, db: Session = Depends(get_db)):
    """Список выданных работ класса для экрана «Задания» у учителя."""
    classroom = ensure_edu_class(db, class_id=None, class_code=class_code)
    db.commit()  # сохранить мост legacy→EduClass, если создали

    counts = dict(
        db.query(Submission.assignment_id, func.count(Submission.id))
        .join(Assignment, Assignment.id == Submission.assignment_id)
        .filter(Assignment.class_id == classroom.id)
        .group_by(Submission.assignment_id)
        .all()
    )

    rows = (
        db.query(Assignment)
        .filter(Assignment.class_id == classroom.id)
        .order_by(Assignment.id.desc())
        .all()
    )

    # уникальные сдавшие — по нормализованному ФИО (без учёта регистра/пробелов)
    unique_by_assign: dict[int, set[str]] = {}
    today_counts: dict[int, int] = {}
    if rows:
        assign_ids = [r.id for r in rows]
        for sid, sname in (
            db.query(Submission.assignment_id, Submission.student_name)
            .filter(Submission.assignment_id.in_(assign_ids))
            .all()
        ):
            key = normalize_student_name(sname or "").casefold()
            if not key:
                continue
            unique_by_assign.setdefault(int(sid), set()).add(key)

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_naive = today_start.replace(tzinfo=None)
        for sid, cnt in (
            db.query(Submission.assignment_id, func.count(Submission.id))
            .filter(
                Submission.assignment_id.in_(assign_ids),
                Submission.created_at >= today_start_naive,
            )
            .group_by(Submission.assignment_id)
            .all()
        ):
            today_counts[int(sid)] = int(cnt or 0)

    out: list[AssignmentListItem] = []
    for row in rows:
        path = f"/student?code={row.code}"
        deadline = utc_aware(_deadline_of(row))
        timer = _timer_of(row)
        out.append(
            AssignmentListItem(
                id=row.id,
                code=row.code,
                title=row.title,
                subject=classroom.subject,
                exam=classroom.target_exam,
                status=row.status,
                grading_mode=row.grading_mode,
                created_at=row.created_at,
                deadline=deadline,
                deadline_at=deadline,
                timer_minutes=timer,
                time_limit_minutes=timer,
                shuffle_variants=_shuffle_of(row),
                accepting_submissions=_accepting_of(row),
                expected_students=_expected_of(row),
                student_url=path,
                student_path=path,
                submissions_count=int(counts.get(row.id) or 0),
                unique_submitters=len(unique_by_assign.get(row.id) or ()),
                questions_count=_questions_count(row.questions_json),
                submissions_today=int(today_counts.get(row.id) or 0),
            )
        )
    return out


@router.get("/{code}/submissions", response_model=list[SubmissionListItem])
def list_assignment_submissions(code: str, db: Session = Depends(get_db)):
    """Сдачи по коду работы — одна строка на ученика (последняя по id)."""
    row = _get_assignment_row(db, code, for_student=False)
    classroom = db.query(EduClass).filter(EduClass.id == row.class_id).first()

    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id == row.id)
        .order_by(Submission.id.desc())
        .all()
    )

    # dedupe: нормализованное ФИО → последняя сдача
    seen: set[str] = set()
    latest: list[Submission] = []
    for s in submissions:
        key = normalize_student_name(s.student_name or "").casefold()
        if not key or key in seen:
            continue
        seen.add(key)
        latest.append(s)

    out: list[SubmissionListItem] = []
    for s in latest:
        qs, _n = _personalized_question_list(row, classroom, s.student_name)
        out.append(_submission_list_item(s, _questions_by_num(qs)))
    return out


@router.get("/{code}/answer-key", response_model=list[AnswerKeyItem])
def get_assignment_answer_key(code: str, db: Session = Depends(get_db)):
    """Мастер-ключ варианта для учителя (без персонализации)."""
    row = _get_assignment_row(db, code, for_student=False)
    items: list[AnswerKeyItem] = []
    for q in _raw_questions(row):
        if not isinstance(q, dict):
            continue
        try:
            num = int(q.get("num") or 0)
        except (TypeError, ValueError):
            num = 0
        if not num:
            continue
        try:
            max_score = int(q.get("max_score") or q.get("maxScore") or 1)
        except (TypeError, ValueError):
            max_score = 1
        part = _question_part(q, num)
        answer = _question_answer(q)
        solution = _question_solution(q, max_len=12000)
        if part == 2 and not answer and solution:
            answer = solution
        items.append(
            AnswerKeyItem(
                num=num,
                topic=str(q.get("topic") or "").strip() or None,
                answer=answer,
                max_score=max_score,
                part=part,
                solution=solution,
            )
        )
    items.sort(key=lambda x: x.num)
    return items


@router.patch("/{code}/submissions/{submission_id}", response_model=SubmissionListItem)
def patch_submission_grade(
    code: str,
    submission_id: int,
    payload: SubmissionGradePatch,
    db: Session = Depends(get_db),
):
    """Ручная оценка и комментарий учителя по сдаче."""
    assignment_row = _get_assignment_row(db, code, for_student=False)
    sub = (
        db.query(Submission)
        .filter(Submission.id == submission_id, Submission.assignment_id == assignment_row.id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Сдача не найдена")

    classroom_pre = db.query(EduClass).filter(EduClass.id == assignment_row.class_id).first()
    qs, _n = _personalized_question_list(assignment_row, classroom_pre, sub.student_name)
    q_by_num = _questions_by_num(qs)

    try:
        review = json.loads(sub.ai_review_json) if sub.ai_review_json else {}
    except json.JSONDecodeError:
        review = {}
    if not isinstance(review, dict):
        review = {}

    touched = False
    if payload.item_num is not None and payload.item_earned is not None:
        primary = _apply_item_score(
            review,
            q_by_num,
            int(payload.item_num),
            float(payload.item_earned),
            item_comment=payload.item_comment,
            ai_grade=payload.ai_grade,
        )
        if normalize_subject(getattr(classroom_pre, "subject", None)) == "russian":
            try:
                lit = review.get("literacy_score")
                if lit is not None:
                    primary += max(0.0, min(float(LIT_MAX), float(lit)))
            except (TypeError, ValueError):
                pass
        sub.score = float(primary)
        sub.teacher_score = float(primary)
        touched = True
        if payload.status is None:
            sub.status = "ai_reviewed" if _review_has_pending(review) else "graded"
    if payload.teacher_score is not None:
        sub.teacher_score = float(payload.teacher_score)
        sub.score = float(payload.teacher_score)
        touched = True
    if payload.teacher_comment is not None:
        comment = str(payload.teacher_comment).strip()
        sub.teacher_comment = comment or None
        touched = True
    if payload.status is not None:
        sub.status = payload.status
        touched = True
    elif payload.teacher_score is not None and payload.item_num is None:
        sub.status = "graded"

    if touched:
        sub.teacher_reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        review = attach_to_review(
            review,
            getattr(classroom_pre, "subject", None),
            score=sub.score,
            teacher_score=getattr(sub, "teacher_score", None),
        )
        sub.ai_review_json = json.dumps(review, ensure_ascii=False)

    if not touched:
        raise HTTPException(status_code=400, detail="Укажите балл или комментарий")

    db.commit()
    db.refresh(sub)
    return _submission_list_item(sub, q_by_num)


@router.get("/{code}", response_model=AssignmentOut)
def get_assignment_by_code(
    code: str,
    student_name: Optional[str] = Query(None, max_length=120),
    db: Session = Depends(get_db),
):
    """Публичный GET для ученика: метаданные + вопросы без ключей ответов."""
    row = _get_assignment_row(db, code, for_student=True)
    classroom = db.query(EduClass).filter(EduClass.id == row.class_id).first()
    out = _assignment_out(row, classroom)
    name = normalize_student_name(student_name) if student_name else ""
    raw_questions, unique_changed = _personalized_question_list(
        row, classroom, name or None
    )
    if _shuffle_of(row) and len(name) >= 2:
        out.unique_applied = unique_changed > 0
        out.unique_changed = unique_changed
    etalon, exam_ui, provenance = _detect_etalon_meta(raw_questions)
    if not etalon and "эталон" in str(out.title or "").lower():
        etalon = True
        exam_ui = exam_ui or "etalon"
    subj = str(out.subject or "").lower().replace("ё", "е")
    if "матем" in subj or subj in ("math", "mathematics", "math_base"):
        if exam_ui == "oge_rus_kim":
            exam_ui = "etalon" if etalon else None
    stripped = _strip_answers(raw_questions)
    out.questions = [q.model_dump() for q in stripped]
    out.question_count = len(out.questions)
    out.etalon = etalon
    out.exam_ui = exam_ui
    out.provenance = provenance
    out.already_submitted = bool(name and _latest_named_submission(db, row.id, name))
    if name and not _student_allowed(row, name) and not out.already_submitted:
        raise HTTPException(
            status_code=403,
            detail="Эта работа выдана другим ученикам",
        )
    return out


def _detect_etalon_meta(questions: list[Any]) -> tuple[bool, Optional[str], Optional[dict[str, Any]]]:
    """Флаги эталона из заданий (payload / top-level), для бейджа ученика."""
    etalon = False
    exam_ui: Optional[str] = None
    provenance: Optional[dict[str, Any]] = None
    for q in questions:
        if not isinstance(q, dict):
            continue
        pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        if q.get("etalon") or pl.get("etalon") or q.get("exam_ui") == "etalon" or pl.get("exam_ui") == "etalon":
            etalon = True
        if not exam_ui:
            ui = q.get("exam_ui") or pl.get("exam_ui")
            if isinstance(ui, str) and ui.strip():
                exam_ui = ui.strip()
        if provenance is None:
            prov = q.get("provenance") if isinstance(q.get("provenance"), dict) else None
            if prov is None and isinstance(pl.get("provenance"), dict):
                prov = pl.get("provenance")
            if prov:
                provenance = prov
        if etalon and provenance and exam_ui:
            break
    if etalon and not exam_ui:
        exam_ui = "etalon"
    return etalon, exam_ui, provenance


@router.get("/{code}/student", response_model=StudentAssignmentOut)
def get_assignment_for_student(
    code: str,
    student_name: Optional[str] = Query(None, max_length=120),
    db: Session = Depends(get_db),
):
    """Вариант для ученика — без ключей ответов (совместимость со старым клиентом)."""
    full = get_assignment_by_code(code, student_name=student_name, db=db)
    questions = _strip_answers(full.questions)
    return StudentAssignmentOut(
        id=full.id,
        title=full.title,
        code=full.code,
        deadline=full.deadline,
        deadline_at=full.deadline_at,
        timer_minutes=full.timer_minutes,
        time_limit_minutes=full.time_limit_minutes,
        shuffle_variants=full.shuffle_variants,
        accepting_submissions=full.accepting_submissions,
        questions=questions,
        question_count=full.question_count or len(questions),
        grading_mode=full.grading_mode,
        status=full.status,
        subject=full.subject,
        target_exam=full.target_exam,
        etalon=bool(full.etalon),
        exam_ui=full.exam_ui,
        provenance=full.provenance,
        unique_applied=bool(full.unique_applied),
        unique_changed=int(full.unique_changed or 0),
        already_submitted=bool(full.already_submitted),
        block_copy=bool(full.block_copy),
        hide_answers=bool(full.hide_answers),
        answers_locked=bool(full.answers_locked),
    )


@router.post("/{code}/submit", response_model=SubmissionOut)
def submit_assignment(
    code: str,
    payload: SubmissionCreateRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Принять работу. Повторная сдача тем же ФИО не открывает новую попытку."""
    assignment_row = _get_assignment_row(db, code, for_student=True)
    if assignment_row.status == "closed" or not _accepting_of(assignment_row):
        raise HTTPException(status_code=403, detail="Приём работ закрыт")
    if _deadline_passed(assignment_row):
        raise HTTPException(status_code=403, detail="Срок сдачи истёк")
    if assignment_row.status == "draft":
        raise HTTPException(status_code=404, detail="Работа с таким кодом не найдена")

    student_name = normalize_student_name(payload.student_name)
    if len(student_name) < 2:
        raise HTTPException(status_code=400, detail="Укажите имя и фамилию")
    if not _student_allowed(assignment_row, student_name):
        raise HTTPException(status_code=403, detail="Эта работа выдана другим ученикам")

    classroom = db.query(EduClass).filter(EduClass.id == assignment_row.class_id).first()
    raw_questions, _n = _personalized_question_list(assignment_row, classroom, student_name)
    subject = getattr(classroom, "subject", None) if classroom is not None else None
    prev = _latest_named_submission(db, assignment_row.id, student_name)
    if prev is not None:
        prev = _regrade_submission(
            db, prev, raw_questions, assignment_row.grading_mode, subject
        )
        try:
            stored = json.loads(prev.answers_json or "{}")
        except json.JSONDecodeError:
            stored = {}
        if not isinstance(stored, dict):
            stored = {"items": stored if isinstance(stored, list) else []}
        try:
            review = json.loads(prev.ai_review_json or "{}") or {}
        except json.JSONDecodeError:
            review = {}
        if not isinstance(review, dict):
            review = {}
        try:
            total = float(review["max_score"]) if review.get("max_score") is not None else prev.score
        except (TypeError, ValueError):
            total = prev.score
        response.status_code = status.HTTP_200_OK
        return SubmissionOut(
            id=prev.id,
            assignment_id=prev.assignment_id,
            student_name=prev.student_name,
            score=prev.score,
            max_score=total,
            status=prev.status,
            answers=stored,
            ai_review=_visible_ai_review(assignment_row, review),
            started_at=prev.started_at,
            created_at=prev.created_at,
            duration_seconds=_duration_seconds(prev.started_at, prev.created_at),
            teacher_score=getattr(prev, "teacher_score", None),
            teacher_comment=getattr(prev, "teacher_comment", None),
            teacher_reviewed_at=getattr(prev, "teacher_reviewed_at", None),
            oge=review.get("oge") if isinstance(review, dict) else None,
            already_submitted=True,
        )

    answers = [a.model_dump() for a in payload.answers]

    # ограничим размер фото (~1.5MB data URL)
    for a in answers:
        photo = a.get("photo_data_url") or ""
        if photo and len(photo) > 2_000_000:
            raise HTTPException(status_code=400, detail=f"Фото к заданию №{a.get('num')} слишком большое")

    earned, total, review, status_val = _auto_check(
        raw_questions, answers, assignment_row.grading_mode
    )
    subject = getattr(classroom, "subject", None) if classroom is not None else None
    review = attach_to_review(review, subject, score=earned)

    # синхронизируем ростер класса (как при join), чтобы «кто не сдал» совпадал по ФИО
    name_key = student_name.casefold()
    if classroom is not None:
        roster_rows = (
            db.query(ClassStudent).filter(ClassStudent.class_id == classroom.id).all()
        )
        if not any(normalize_student_name(r.name).casefold() == name_key for r in roster_rows):
            db.add(ClassStudent(class_id=classroom.id, name=student_name))

    row = Submission(
        assignment_id=assignment_row.id,
        student_name=student_name,
        score=earned,
        status=status_val,
        answers_json=json.dumps({"items": answers}, ensure_ascii=False),
        ai_review_json=json.dumps(review, ensure_ascii=False),
        started_at=payload.started_at,
    )
    db.add(row)

    db.commit()
    db.refresh(row)

    out = SubmissionOut(
        id=row.id,
        assignment_id=row.assignment_id,
        student_name=row.student_name,
        score=row.score,
        max_score=total,
        status=row.status,
        answers={"items": answers},
        ai_review=_visible_ai_review(assignment_row, review),
        started_at=row.started_at,
        created_at=row.created_at,
        duration_seconds=_duration_seconds(row.started_at, row.created_at),
        teacher_score=getattr(row, "teacher_score", None),
        teacher_comment=getattr(row, "teacher_comment", None),
        teacher_reviewed_at=getattr(row, "teacher_reviewed_at", None),
        oge=review.get("oge") if isinstance(review, dict) else None,
        already_submitted=False,
    )
    response.status_code = status.HTTP_201_CREATED
    if str(assignment_row.grading_mode or "") in ("ai_assist", "autopilot"):
        background_tasks.add_task(grade_submission_draft, row.id)
    return out
