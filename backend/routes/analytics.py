"""Аналитика класса: heatmap ошибок, тренд баллов, работа над ошибками."""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Assignment, ClassStudent, Submission
from backend.schemas.edu import (
    AssignmentOut,
    ClassAnalyticsOut,
    AnalyticsAssignmentOption,
    AnalyticsGradeRow,
    AnalyticsHeatItem,
    AnalyticsMarkBucket,
    AnalyticsParticipation,
    AnalyticsRiskStudent,
    AnalyticsTimeStats,
    AnalyticsTrendPoint,
    RemediationRequest,
    RnoPreviewOut,
    RnoPreviewRequest,
)
from backend.services.analytics_labels import (
    build_teacher_summary,
    display_assignment_title,
    format_hard_flag,
    is_smoke_title,
    question_fingerprint,
    subject_is_math,
    subject_is_russian,
    topic_label_for_num,
    translate_topic_slug,
)
from backend.services.classroom import ensure_edu_class, normalize_student_name
from backend.services.codes import generate_edu_code
from backend.services.figures import attach_figure
from backend.services.grade_calculator import (
    mark_from_scale,
    max_primary,
    part_scores_from_items,
    result_from_review,
    threshold_status_label,
)
from backend.services.rno_generator import (
    collect_failed_task_ids,
    generate_rno,
    rno_seed,
    rno_title,
)
from backend.services.beta_limits import assert_can_issue_variant

router = APIRouter(prefix="/api/classes", tags=["analytics"])


def _duration_seconds(started_at: Optional[datetime], submitted_at: Optional[datetime]) -> Optional[int]:
    if not started_at or not submitted_at:
        return None
    try:
        secs = int((submitted_at - started_at).total_seconds())
        return secs if secs >= 0 else None
    except Exception:
        return None


def _parse_questions(questions_json: Optional[str]) -> list[dict[str, Any]]:
    try:
        questions = json.loads(questions_json or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(questions, list):
        return []
    return [q for q in questions if isinstance(q, dict)]


def _kim_type_of(q: dict[str, Any], num: int) -> Optional[int]:
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    for key in ("kim_type", "source_num", "task_number"):
        raw = pl.get(key) if key != "task_number" else (q.get("task_number") or pl.get(key))
        try:
            v = int(raw)
            if v > 0:
                return v
        except (TypeError, ValueError):
            continue
    src = q.get("source_num")
    try:
        v = int(src) if src is not None else 0
        if v > 0:
            return v
    except (TypeError, ValueError):
        pass
    return num or None


def _topic_map(questions: list[dict[str, Any]], *, subject: Optional[str] = None) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for q in questions:
        try:
            num = int(q.get("num") or 0)
        except (TypeError, ValueError):
            continue
        if not num:
            continue
        kim = _kim_type_of(q, num)
        raw_topic = str(q.get("topic") or "").strip()
        mapping[num] = topic_label_for_num(num, raw_topic, subject=subject, kim_type=kim)
    return mapping


def _parse_review(ai_review_json: Optional[str]) -> Optional[dict[str, Any]]:
    if not ai_review_json:
        return None
    try:
        review = json.loads(ai_review_json)
    except json.JSONDecodeError:
        return None
    return review if isinstance(review, dict) else None


def _max_score_from_review(review: Optional[dict[str, Any]]) -> Optional[float]:
    if not review or review.get("max_score") is None:
        return None
    try:
        return float(review["max_score"])
    except (TypeError, ValueError):
        return None


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


def _answer_map(answers_json: Optional[str]) -> dict[int, str]:
    try:
        data = json.loads(answers_json or "{}")
    except json.JSONDecodeError:
        return {}
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return {}
    out: dict[int, str] = {}
    for a in items:
        if not isinstance(a, dict):
            continue
        try:
            num = int(a.get("num") or 0)
        except (TypeError, ValueError):
            continue
        text = str(a.get("text") or "").strip()
        if num and text:
            out[num] = text[:80]
    return out


def _oge_mark_from_percent(pct: float, subject: Optional[str]) -> int:
    max_p = max_primary(subject)
    primary = int(round(float(pct) / 100.0 * max_p))
    return int(mark_from_scale(primary, subject))


def _review_items(review: Optional[dict[str, Any]]) -> list[dict[str, Any]]:
    if not review:
        return []
    items = review.get("items")
    if not isinstance(items, list):
        return []
    return [it for it in items if isinstance(it, dict)]


def _pick_assignment(
    assignments: list[Assignment],
    assignment_code: Optional[str],
) -> Optional[Assignment]:
    if not assignments:
        return None
    if assignment_code:
        key = assignment_code.strip().upper()
        for a in assignments:
            if str(a.code).upper() == key:
                return a
    with_subs = [a for a in assignments if getattr(a, "_subs_count", 0) > 0]
    pool = with_subs or assignments
    return max(pool, key=lambda a: a.id)


def _build_heatmap(
    subs: list[Submission],
    topic_by_num: dict[int, str],
    *,
    subject: Optional[str] = None,
    class_mode: bool = True,
) -> tuple[list[AnalyticsHeatItem], list[int], list[str]]:
    stats: dict[int, Counter[str]] = defaultdict(Counter)
    wrong_names: dict[int, list[str]] = defaultdict(list)
    empty_names: dict[int, list[str]] = defaultdict(list)
    seen_wrong: dict[int, set[str]] = defaultdict(set)
    seen_empty: dict[int, set[str]] = defaultdict(set)
    wrong_answers: dict[int, Counter[str]] = defaultdict(Counter)
    for s in subs:
        review = _parse_review(s.ai_review_json)
        answers = _answer_map(getattr(s, "answers_json", None))
        name = normalize_student_name(s.student_name)
        name_key = name.casefold() if name else ""
        for it in _review_items(review):
            try:
                num = int(it.get("num") or 0)
            except (TypeError, ValueError):
                continue
            if not num:
                continue
            status = str(it.get("status") or "")
            if status == "correct":
                stats[num]["correct"] += 1
            elif status == "wrong":
                stats[num]["wrong"] += 1
                if name and name_key not in seen_wrong[num]:
                    seen_wrong[num].add(name_key)
                    wrong_names[num].append(name)
                given = answers.get(num) or str(it.get("given") or it.get("answer") or "").strip()
                if given:
                    wrong_answers[num][given[:80]] += 1
            elif status == "empty":
                stats[num]["empty"] += 1
                if name and name_key not in seen_empty[num]:
                    seen_empty[num].add(name_key)
                    empty_names[num].append(name)
            elif status.endswith("pending") or status in ("ai_pending", "manual_pending", "pending"):
                stats[num]["pending"] += 1
            else:
                stats[num]["pending"] += 1

    for num in topic_by_num:
        stats.setdefault(num, Counter())

    heatmap: list[AnalyticsHeatItem] = []
    for num in sorted(stats.keys()):
        c = stats[num]
        wrong = int(c.get("wrong") or 0)
        empty = int(c.get("empty") or 0)
        correct = int(c.get("correct") or 0)
        pending = int(c.get("pending") or 0)
        total = wrong + empty + correct + pending
        scored = wrong + empty + correct
        fail = wrong + empty
        wrong_pct = round(100.0 * fail / scored, 1) if scored else 0.0
        success_pct = round(100.0 * correct / scored, 1) if scored else None
        topic = topic_by_num.get(num) or topic_label_for_num(num, None, subject=subject)
        flag = None
        if scored and wrong_pct >= 40:
            flag = format_hard_flag(
                num, topic, wrong_pct, subject=subject, class_mode=class_mode
            )
        typical = None
        typical_n = 0
        top_wrong = wrong_answers.get(num)
        if top_wrong:
            ans, n = top_wrong.most_common(1)[0]
            typical, typical_n = ans, int(n)
        heatmap.append(
            AnalyticsHeatItem(
                num=num,
                topic=topic,
                wrong_count=wrong,
                empty_count=empty,
                correct_count=correct,
                pending_count=pending,
                total=total,
                wrong_pct=wrong_pct,
                success_pct=success_pct,
                flag=flag,
                wrong_students=wrong_names.get(num) or [],
                empty_students=empty_names.get(num) or [],
                typical_wrong=typical,
                typical_wrong_count=typical_n,
            )
        )

    # hardest first by error rate; «без ошибок» внизу
    with_errors = [h for h in heatmap if (h.wrong_count + h.empty_count) > 0]
    clean = [h for h in heatmap if (h.wrong_count + h.empty_count) == 0]
    with_errors.sort(key=lambda h: (h.wrong_pct, h.wrong_count + h.empty_count), reverse=True)
    clean.sort(key=lambda h: h.num)
    heatmap = with_errors + clean

    ranked = with_errors[:8]
    weakest = [h.num for h in ranked]
    flags = [
        h.flag
        or format_hard_flag(h.num, h.topic, h.wrong_pct, subject=subject, class_mode=class_mode)
        for h in ranked
        if h.wrong_pct >= 40
    ][:5]
    return heatmap, weakest, flags


def _pg_subject_exam(classroom) -> tuple[str, str]:
    exam = str(getattr(classroom, "target_exam", "") or "oge").strip().lower()
    exam_code = {"oge": "OGE", "ege": "EGE", "vpr": "VPR", "school": "SCHOOL"}.get(exam, "OGE")
    subject = str(getattr(classroom, "subject", "") or "")
    if subject_is_russian(subject):
        return "russian", exam_code
    if subject_is_math(subject):
        return "math", exam_code
    # fallback: try raw
    raw = subject.strip().lower()
    if raw in ("russian", "math"):
        return raw, exam_code
    return "math" if "матем" in raw else ("russian" if "рус" in raw else raw or "math"), exam_code


def _shuffle_options_inplace(q: dict[str, Any]) -> bool:
    """Перемешать варианты ответа, если есть. Возвращает True если изменили."""
    changed = False
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else None
    if pl:
        for key in ("options", "choices", "variants", "right", "left"):
            arr = pl.get(key)
            if isinstance(arr, list) and len(arr) > 1 and all(isinstance(x, (str, dict, int)) for x in arr):
                shuffled = list(arr)
                random.shuffle(shuffled)
                if shuffled != arr:
                    pl[key] = shuffled
                    changed = True
        q["payload"] = pl
    opts = q.get("options")
    if isinstance(opts, list) and len(opts) > 1:
        shuffled = list(opts)
        random.shuffle(shuffled)
        if shuffled != opts:
            q["options"] = shuffled
            changed = True
    return changed


def _proto_to_question(proto, *, display_num: int, source_num: int, subject_code: str, exam_code: str) -> dict[str, Any]:
    from backend.universal.adapt import human_topic_from_title
    from backend.universal.variant_builder import _task_from_proto

    task = _task_from_proto(proto, subject_code=subject_code, exam_code=exam_code)
    title = str(getattr(proto, "prototype_title", "") or "")
    topic = human_topic_from_title(title)
    topic = translate_topic_slug(topic) or topic_label_for_num(
        source_num, topic, subject=subject_code, kim_type=source_num
    )
    part = int(getattr(proto, "part", None) or task.get("part") or 1)
    row: dict[str, Any] = {
        "num": display_num,
        "part": part,
        "type": f"Тип {source_num}" if subject_code == "russian" else (
            "Развёрнутый ответ" if part == 2 else "Краткий ответ"
        ),
        "topic": f"Работа над ошибками · было №{source_num} · {topic}",
        "text": str(task.get("text") or ""),
        "answer": str(task.get("answer") or ""),
        "max_score": int(task["max_score"]) if task.get("max_score") is not None else (2 if part == 2 else 1),
        "needs_figure": bool(task.get("figure_kind") or task.get("figure_svg") or task.get("figure_data")),
        "figure_kind": task.get("figure_kind"),
        "figure_params": task.get("figure_params"),
    }
    if task.get("figure_data") is not None:
        row["figure_data"] = task["figure_data"]
    if task.get("figure_svg"):
        row["figure_svg"] = task["figure_svg"]
    payload = task.get("payload") if isinstance(task.get("payload"), dict) else {}
    payload = dict(payload or {})
    payload["source_num"] = source_num
    payload["remediation"] = True
    payload["remediation_alt"] = True
    if subject_code == "russian":
        payload.setdefault("oge_rus", True)
        payload.setdefault("kim_type", source_num)
        payload.setdefault("ui", "oge_rus")
    row["payload"] = payload
    if subject_code == "russian":
        row["kim_order"] = True
    return attach_figure(row)


def _pick_alternate_from_pg(
    *,
    subject_code: str,
    exam_code: str,
    slot: int,
    avoid_fp: str,
) -> Optional[dict[str, Any]]:
    try:
        from backend.db.pg import is_postgres_configured, pg_engine
        from backend.db.pg_models import TaskPrototype
        from sqlalchemy import select
        from sqlalchemy.orm import Session as PgSession
    except Exception:
        return None
    if not is_postgres_configured():
        return None
    try:
        engine = pg_engine()
    except Exception:
        return None
    session = PgSession(bind=engine)
    try:
        rows = session.execute(
            select(TaskPrototype).where(
                TaskPrototype.subject_code == subject_code,
                TaskPrototype.exam_code == exam_code,
                TaskPrototype.task_number == int(slot),
                TaskPrototype.template_text.isnot(None),
                TaskPrototype.template_answer.isnot(None),
            )
        ).scalars().all()
        candidates = []
        for p in rows:
            text = (p.template_text or "").strip()
            ans = (p.template_answer or "").strip()
            if not text or not ans:
                continue
            fp = f"{text[:240]}|{ans[:80]}"
            if fp == avoid_fp:
                continue
            candidates.append(p)
        if not candidates:
            return None
        # prefer different context_id when possible
        random.shuffle(candidates)
        return candidates[0]
    except Exception:
        return None
    finally:
        session.close()


def _pick_alternate_from_sqlite_bank(
    db: Session,
    *,
    exam: str,
    subject: str,
    slot: int,
    avoid_fp: str,
) -> Optional[dict[str, Any]]:
    try:
        from backend.models import BankTask
        from backend.services.bank import _task_to_question
        from backend.services.bank_keys import normalize_exam, normalize_subject_key
    except Exception:
        return None
    ex = normalize_exam(exam)
    sk = normalize_subject_key(exam, subject)
    pool = (
        db.query(BankTask)
        .filter(
            BankTask.exam == ex,
            BankTask.subject_key == sk,
            BankTask.slot == int(slot),
            BankTask.is_active == 1,
        )
        .all()
    )
    candidates = []
    for t in pool:
        q = _task_to_question(t, int(slot))
        if question_fingerprint(q) == avoid_fp:
            continue
        candidates.append(q)
    if not candidates:
        return None
    return random.choice(candidates)


def _clone_as_remediation(q: dict[str, Any], *, display_num: int, source_num: int) -> dict[str, Any]:
    out = dict(q)
    pl = dict(out.get("payload") or {}) if isinstance(out.get("payload"), dict) else {}
    pl["source_num"] = source_num
    pl["remediation"] = True
    out["payload"] = pl
    out["num"] = display_num
    topic = translate_topic_slug(str(out.get("topic") or "")) or str(out.get("topic") or f"№{source_num}")
    out["topic"] = f"Работа над ошибками · было №{source_num} · {topic}"
    _shuffle_options_inplace(out)
    return attach_figure(out)


def _pick_rno_alternate(db: Session, classroom, src: dict[str, Any], num: int) -> Optional[dict[str, Any]]:
    """Другой прототип того же слота КИМ, с сохранением исходного номера."""
    n = int(num or 0)
    if subject_is_russian(getattr(classroom, "subject", None)) and n in (1, 10, 11, 12, 13):
        return None
    avoid = question_fingerprint(src)
    slot = _kim_type_of(src, num) or num
    sc, ec = _pg_subject_exam(classroom)

    proto = _pick_alternate_from_pg(
        subject_code=sc, exam_code=ec, slot=int(slot), avoid_fp=avoid
    )
    if proto is not None:
        try:
            return _proto_to_question(
                proto,
                display_num=num,
                source_num=num,
                subject_code=sc,
                exam_code=ec,
            )
        except Exception:
            pass

    bank_q = _pick_alternate_from_sqlite_bank(
        db,
        exam=str(getattr(classroom, "target_exam", "oge") or "oge"),
        subject=str(getattr(classroom, "subject", "") or ""),
        slot=int(slot),
        avoid_fp=avoid,
    )
    if bank_q is not None:
        bank_q = dict(bank_q)
        pl = dict(bank_q.get("payload") or {}) if isinstance(bank_q.get("payload"), dict) else {}
        pl["source_num"] = num
        pl["remediation"] = True
        pl["remediation_alt"] = True
        bank_q["payload"] = pl
        bank_q["num"] = num
        topic = translate_topic_slug(str(bank_q.get("topic") or "")) or topic_label_for_num(
            num, bank_q.get("topic"), subject=getattr(classroom, "subject", None)
        )
        bank_q["topic"] = f"Работа над ошибками · было №{num} · {topic}"
        return attach_figure(bank_q)
    return None


def _build_remediation_questions(
    db: Session,
    classroom,
    source_questions: list[dict[str, Any]],
    pick_nums: list[int],
    *,
    source_title: str = "",
) -> tuple[list[dict[str, Any]], bool, int]:
    """Собрать РНО: другой прототип слота + мутатор с уникальными значениями."""
    result = generate_rno(
        source_questions,
        pick_nums,
        subject=getattr(classroom, "subject", None),
        source_title=source_title,
        seed=rno_seed(getattr(classroom, "code", ""), pick_nums, source_title),
        pick_alternate=lambda src, num: _pick_rno_alternate(db, classroom, src, num),
    )
    return (
        result["questions"],
        bool(result.get("used_alt")),
        int(result.get("mutated_count") or 0),
    )


def _remediation_gate(
    *,
    roster_names: list[str],
    submitter_keys: set[str],
    expected_students: Optional[int],
) -> tuple[bool, str]:
    """РНО можно собрать, как только есть сдачи. Не ждём весь список класса."""
    if not submitter_keys:
        return False, "Нужна хотя бы одна сдача с проверкой"
    roster_n = len(roster_names)
    missing = [
        n for n in roster_names if n.casefold() not in submitter_keys
    ]
    if missing and roster_n:
        shown = ", ".join(missing[:3])
        extra = "…" if len(missing) > 3 else ""
        return (
            True,
            f"Можно собрать РНО по сдавшим ({len(submitter_keys)} из {roster_n}). Ещё нет: {shown}{extra}",
        )
    expected = int(expected_students) if expected_students and expected_students > 0 else 0
    if expected and len(submitter_keys) < expected:
        return (
            True,
            f"Можно собрать РНО по сдавшим ({len(submitter_keys)} из {expected})",
        )
    return True, "Можно создать работу над ошибками"


@router.get("/{code}/analytics", response_model=ClassAnalyticsOut)
def class_analytics(
    code: str,
    assignment_code: Optional[str] = Query(None),
    student: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    classroom = ensure_edu_class(db, class_code=code)
    subject = getattr(classroom, "subject", None)
    roster_rows = (
        db.query(ClassStudent)
        .filter(ClassStudent.class_id == classroom.id)
        .order_by(ClassStudent.id.asc())
        .all()
    )
    roster_names = [normalize_student_name(r.name) for r in roster_rows if r.name]

    assignments = (
        db.query(Assignment)
        .filter(Assignment.class_id == classroom.id)
        .order_by(Assignment.id.desc())
        .all()
    )
    assign_ids = [a.id for a in assignments]
    all_subs: list[Submission] = []
    if assign_ids:
        all_subs = db.query(Submission).filter(Submission.assignment_id.in_(assign_ids)).all()

    subs_by_assign: dict[int, list[Submission]] = defaultdict(list)
    for s in all_subs:
        subs_by_assign[s.assignment_id].append(s)

    for a in assignments:
        setattr(a, "_subs_count", len(subs_by_assign.get(a.id) or []))

    student_names: list[str] = []
    seen: set[str] = set()
    for n in roster_names:
        key = n.casefold()
        if key not in seen:
            seen.add(key)
            student_names.append(n)
    for s in all_subs:
        n = normalize_student_name(s.student_name)
        if not n:
            continue
        key = n.casefold()
        if key not in seen:
            seen.add(key)
            student_names.append(n)

    mode = "student" if (student and str(student).strip()) else "class"
    student_filter = normalize_student_name(student) if mode == "student" else None
    student_key = student_filter.casefold() if student_filter else None

    def _filter_subs(rows: list[Submission]) -> list[Submission]:
        if not student_key:
            return rows
        out: list[Submission] = []
        for s in rows:
            name = normalize_student_name(s.student_name)
            if name and name.casefold() == student_key:
                out.append(s)
        return out

    # trend: chronological by created_at, skip pure smoke noise from chart
    chrono = sorted(
        assignments,
        key=lambda x: (x.created_at or datetime.min, x.id),
    )
    trend: list[AnalyticsTrendPoint] = []
    assign_options: list[AnalyticsAssignmentOption] = []
    variant_idx = 0
    for a in chrono:
        rows = _filter_subs(subs_by_assign.get(a.id) or [])
        percents: list[float] = []
        for s in rows:
            review = _parse_review(s.ai_review_json)
            pct = _score_percent(s.score, _max_score_from_review(review))
            if pct is not None:
                percents.append(pct)
        avg = round(sum(percents) / len(percents), 1) if percents else None
        variant_idx += 1
        nice_title = display_assignment_title(a.title, a.created_at, index=variant_idx)
        # exclude smoke-only points without real avg from trend chart
        include_in_trend = not (is_smoke_title(a.title) and avg is None)
        if include_in_trend:
            # still show smoke with avg, but with cleaned title
            if is_smoke_title(a.title):
                nice_title = display_assignment_title(None, a.created_at, index=variant_idx)
            trend.append(
                AnalyticsTrendPoint(
                    assignment_code=a.code,
                    title=nice_title,
                    created_at=a.created_at,
                    avg_percent=avg,
                    submissions_count=len(rows),
                )
            )
        assign_options.append(
            AnalyticsAssignmentOption(
                code=a.code,
                title=nice_title,
                created_at=a.created_at,
                submissions_count=len(subs_by_assign.get(a.id) or []),
                avg_percent=avg,
            )
        )
    assign_options = list(reversed(assign_options))

    selected = _pick_assignment(assignments, assignment_code)
    selected_subs: list[Submission] = []
    heatmap: list[AnalyticsHeatItem] = []
    weakest: list[int] = []
    flags: list[str] = []
    topic_by_num: dict[int, str] = {}
    if selected:
        topic_by_num = _topic_map(_parse_questions(selected.questions_json), subject=subject)
        selected_subs = _filter_subs(subs_by_assign.get(selected.id) or [])
        heatmap, weakest, flags = _build_heatmap(
            selected_subs,
            topic_by_num,
            subject=subject,
            class_mode=(mode == "class"),
        )

    avg_pool = selected_subs if selected else _filter_subs(all_subs)
    all_pcts: list[float] = []
    for s in avg_pool:
        review = _parse_review(s.ai_review_json)
        pct = _score_percent(s.score, _max_score_from_review(review))
        if pct is not None:
            all_pcts.append(pct)
    class_avg = round(sum(all_pcts) / len(all_pcts), 1) if all_pcts else None

    scope_subs = selected_subs if selected else _filter_subs(all_subs)
    submitter_keys = {
        normalize_student_name(s.student_name).casefold()
        for s in scope_subs
        if normalize_student_name(s.student_name)
    }
    roster_n = len(roster_names)
    submitters_n = len(submitter_keys)
    expected = getattr(selected, "expected_students", None) if selected else None
    try:
        expected_n = int(expected) if expected is not None else None
    except (TypeError, ValueError):
        expected_n = None
    denom = roster_n if roster_n > 0 else (expected_n if expected_n and expected_n > 0 else None)
    part_pct = round(100.0 * submitters_n / denom, 1) if denom else None

    ready, hint = _remediation_gate(
        roster_names=roster_names,
        submitter_keys=submitter_keys,
        expected_students=expected_n,
    )
    missing_roster = [n for n in roster_names if n.casefold() not in submitter_keys]
    all_submitted = bool(roster_n and not missing_roster)
    if not roster_n and expected_n:
        all_submitted = submitters_n >= expected_n
    # student-mode remediation: only that student must have submitted
    if mode == "student":
        if student_key and student_key in submitter_keys and weakest:
            ready, hint = True, "Можно создать персональную работу над ошибками"
            all_submitted = True
        elif not weakest:
            ready, hint = False, "Нет ошибок для работы над ошибками"
        else:
            ready, hint = False, "Нужна сдача ученика с проверкой"
            all_submitted = bool(student_key and student_key in submitter_keys)

    if not weakest:
        ready = False
        if not hint or "список" not in hint.lower():
            hint = "Пока нет ошибок для работы над ошибками — нужны сдачи с проверкой"

    summary_lines = build_teacher_summary(
        mode=mode,
        participation_pct=part_pct,
        submitters=submitters_n,
        roster=roster_n,
        avg_percent=class_avg,
        weakest_count=len(weakest),
    )

    durations: list[int] = []
    for s in scope_subs:
        d = _duration_seconds(getattr(s, "started_at", None), s.created_at)
        if d is not None:
            durations.append(d)
    time_stats = AnalyticsTimeStats(
        avg_duration_seconds=int(round(sum(durations) / len(durations))) if durations else None,
        samples=len(durations),
        per_task_available=False,
    )

    selected_title = None
    if selected:
        selected_title = display_assignment_title(selected.title, selected.created_at)

    submitted_students: list[str] = []
    seen_sub: set[str] = set()
    for s in scope_subs:
        n = normalize_student_name(s.student_name)
        k = n.casefold() if n else ""
        if n and k not in seen_sub:
            seen_sub.add(k)
            submitted_students.append(n)
    missing_students = [n for n in roster_names if n.casefold() not in submitter_keys]

    marks = Counter()
    cap = max_primary(subject)
    weak_by_key: dict[str, list[str]] = defaultdict(list)
    for h in heatmap:
        if h.success_pct is None or h.success_pct >= 50:
            continue
        label = f"№{h.num} {h.topic}" if h.topic else f"№{h.num}"
        for name in list(h.wrong_students or []) + list(h.empty_students or []):
            key = str(name or "").casefold()
            if key and label not in weak_by_key[key]:
                weak_by_key[key].append(label)

    latest_sub: dict[str, Submission] = {}
    for s in scope_subs:
        name = normalize_student_name(s.student_name)
        key = name.casefold() if name else ""
        if not key:
            continue
        prev = latest_sub.get(key)
        if prev is None or (s.id or 0) > (prev.id or 0):
            latest_sub[key] = s

    grade_rows: list[AnalyticsGradeRow] = []
    seen_grade: set[str] = set()
    for key, s in latest_sub.items():
        name = normalize_student_name(s.student_name)
        review = _parse_review(s.ai_review_json)
        oge = result_from_review(
            subject,
            review,
            score=s.score,
            teacher_score=getattr(s, "teacher_score", None),
        )
        grade = str(oge.get("grade") or "")
        if grade.isdigit():
            marks[int(grade)] += 1
        seen_grade.add(key)
        items = _review_items(review)
        part1_score, part2_score = part_scores_from_items(subject, items)
        grade_rows.append(
            AnalyticsGradeRow(
                name=name,
                submitted=True,
                primary=oge.get("score"),
                max_primary=int(oge.get("max_score") or cap),
                grade=grade or None,
                failed_geometry=bool(oge.get("failed_geometry")),
                failed_literacy=bool(oge.get("failed_literacy")),
                geometry_score=oge.get("geometry_score"),
                geometry_max=oge.get("geometry_max"),
                literacy_score=oge.get("literacy_score"),
                weak_topics=weak_by_key.get(key, [])[:4],
                geometry_tag=oge.get("geometry_tag"),
                literacy_tag=oge.get("literacy_tag"),
                part1_score=part1_score,
                part2_score=part2_score,
                threshold_status=threshold_status_label(
                    submitted=True,
                    failed_geometry=bool(oge.get("failed_geometry")),
                    failed_literacy=bool(oge.get("failed_literacy")),
                    geometry_tag=oge.get("geometry_tag"),
                    literacy_tag=oge.get("literacy_tag"),
                    subject=subject,
                ),
            )
        )
    for n in roster_names:
        key = n.casefold()
        if key in seen_grade:
            continue
        grade_rows.append(
            AnalyticsGradeRow(
                name=n,
                submitted=False,
                max_primary=cap,
                threshold_status="не сдал",
            )
        )
    grade_rows.sort(key=lambda r: (not r.submitted, r.name.casefold()))
    submitted_rows = [r for r in grade_rows if r.submitted and r.primary is not None]
    class_avg_primary = (
        round(sum(int(r.primary or 0) for r in submitted_rows) / len(submitted_rows), 1)
        if submitted_rows
        else None
    )
    grade_vals = [int(r.grade) for r in submitted_rows if r.grade and str(r.grade).isdigit()]
    class_avg_grade = round(sum(grade_vals) / len(grade_vals), 1) if grade_vals else None
    mark_distribution = [
        AnalyticsMarkBucket(mark=m, count=int(marks.get(m) or 0)) for m in (2, 3, 4, 5)
    ]

    red_nums = {
        h.num
        for h in heatmap
        if h.success_pct is not None and h.success_pct < 50
    }
    risk_hits: dict[str, list[int]] = defaultdict(list)
    risk_seen: dict[str, set[int]] = defaultdict(set)
    for h in heatmap:
        if h.num not in red_nums:
            continue
        for name in list(h.wrong_students or []) + list(h.empty_students or []):
            key = name.casefold()
            if h.num in risk_seen[key]:
                continue
            risk_seen[key].add(h.num)
            risk_hits[name].append(h.num)
    risk_students = [
        AnalyticsRiskStudent(name=name, red_count=len(nums), nums=nums)
        for name, nums in sorted(risk_hits.items(), key=lambda x: (-len(x[1]), x[0]))
        if len(nums) >= 2
    ][:6]

    compare_code = None
    compare_title = None
    if selected:
        prior: list[Assignment] = []
        for a in chrono:
            if a.id == selected.id:
                break
            prior.append(a)
        for a in reversed(prior):
            prev_subs = _filter_subs(subs_by_assign.get(a.id) or [])
            if not prev_subs:
                continue
            prev_topics = _topic_map(_parse_questions(a.questions_json), subject=subject)
            prev_heat, _, _ = _build_heatmap(
                prev_subs, prev_topics, subject=subject, class_mode=(mode == "class")
            )
            prev_ok = {h.num: h.success_pct for h in prev_heat}
            for h in heatmap:
                old = prev_ok.get(h.num)
                if h.success_pct is not None and old is not None:
                    h.delta_pct = round(h.success_pct - old, 1)
            compare_code = a.code
            compare_title = display_assignment_title(a.title, a.created_at)
            break

    db.commit()
    return ClassAnalyticsOut(
        class_code=classroom.code,
        mode=mode,
        student=student_filter if mode == "student" else None,
        students=student_names,
        assignments=assign_options,
        selected_assignment_code=selected.code if selected else None,
        selected_assignment_title=selected_title,
        class_avg_percent=class_avg,
        participation=AnalyticsParticipation(
            roster_count=roster_n,
            submitters_count=submitters_n,
            submissions_count=len(scope_subs),
            participation_pct=part_pct,
            expected_students=expected_n,
            all_submitted=all_submitted,
            missing_students=missing_students,
            submitted_students=submitted_students,
        ),
        heatmap=heatmap,
        weakest_nums=weakest,
        flags=flags,
        trend=trend,
        time=time_stats,
        summary_lines=summary_lines,
        remediation_ready=bool(ready and weakest),
        remediation_hint=hint,
        mark_distribution=mark_distribution,
        risk_students=risk_students,
        compare_assignment_code=compare_code,
        compare_assignment_title=compare_title,
        subject=subject,
        grade_rows=grade_rows,
        class_avg_primary=class_avg_primary,
        class_avg_grade=class_avg_grade,
    )


@router.post(
    "/{code}/analytics/remediation",
    response_model=AssignmentOut,
    status_code=201,
)
def create_remediation_assignment(
    code: str,
    payload: RemediationRequest,
    db: Session = Depends(get_db),
):
    """Создать «Работу над ошибками» — слабые слоты, по возможности другие прототипы."""
    from backend.routes.assignments import _assignment_out

    classroom = ensure_edu_class(db, class_code=code)
    assert_can_issue_variant(db, classroom.id)
    analytics = class_analytics(
        code=classroom.code,
        assignment_code=payload.assignment_code,
        student=payload.student,
        db=db,
    )
    if not analytics.selected_assignment_code:
        raise HTTPException(status_code=400, detail="Нет работ для анализа")
    if not analytics.remediation_ready:
        raise HTTPException(
            status_code=400,
            detail=analytics.remediation_hint
            or "Работа над ошибками пока недоступна",
        )
    if not analytics.weakest_nums:
        raise HTTPException(
            status_code=400,
            detail="Пока нет ошибок для работы над ошибками — нужны сдачи с проверкой",
        )

    source = (
        db.query(Assignment)
        .filter(
            Assignment.class_id == classroom.id,
            Assignment.code == analytics.selected_assignment_code,
        )
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Исходная работа не найдена")

    questions = _parse_questions(source.questions_json)
    by_num = {}
    for q in questions:
        try:
            num = int(q.get("num") or 0)
        except (TypeError, ValueError):
            continue
        if num:
            by_num[num] = q

    pick = [n for n in analytics.weakest_nums if n in by_num][: payload.max_tasks]
    if not pick:
        raise HTTPException(
            status_code=400,
            detail="Нет заданий с ошибками или пропусками — нужна проверка с разбором",
        )

    cloned, used_alt, mutated_count = _build_remediation_questions(
        db, classroom, questions, pick, source_title=analytics.selected_assignment_title or source.title or ""
    )
    if not cloned:
        raise HTTPException(status_code=400, detail="Не удалось собрать задания для работы над ошибками")

    try:
        new_code = generate_edu_code(db, Assignment, "code")
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    roster_n = db.query(ClassStudent).filter(ClassStudent.class_id == classroom.id).count()
    expected = int(roster_n) if roster_n and roster_n > 0 else None

    title = rno_title(analytics.selected_assignment_title or source.title or "Исходный тест")
    if analytics.student:
        who = f" · {analytics.student}"
        if len(title) + len(who) <= 200:
            title = title + who
    if len(title) > 200:
        title = title[:197] + "…"

    row = Assignment(
        class_id=classroom.id,
        title=title,
        code=new_code,
        deadline=None,
        timer_minutes=None,
        questions_json=json.dumps(cloned, ensure_ascii=False),
        grading_mode=payload.grading_mode,
        status="active",
        shuffle_variants=bool(used_alt),
        accepting_submissions=True,
        expected_students=expected,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    out = _assignment_out(row, classroom)
    out.unique_changed = int(mutated_count or 0)
    out.unique_applied = bool(used_alt or mutated_count)
    return out


@router.post(
    "/{code}/analytics/rno",
    response_model=RnoPreviewOut,
)
def preview_rno_assignment(
    code: str,
    payload: RnoPreviewRequest,
    db: Session = Depends(get_db),
):
    """Собрать предпросмотр «Работы над ошибками» без публикации задания."""
    classroom = ensure_edu_class(db, class_code=code)
    analytics = class_analytics(
        code=classroom.code,
        assignment_code=payload.assignment_code,
        student=payload.student,
        db=db,
    )
    if not analytics.selected_assignment_code:
        raise HTTPException(status_code=400, detail="Нет работ для анализа")

    source = (
        db.query(Assignment)
        .filter(
            Assignment.class_id == classroom.id,
            Assignment.code == analytics.selected_assignment_code,
        )
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Исходная работа не найдена")

    questions = _parse_questions(source.questions_json)
    by_num = {}
    for q in questions:
        try:
            num = int(q.get("num") or q.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        if num:
            by_num[num] = q

    subs = db.query(Submission).filter(Submission.assignment_id == source.id).all()
    student_key = ""
    if payload.student:
        student_key = normalize_student_name(payload.student).casefold()
        if student_key:
            subs = [
                s
                for s in subs
                if normalize_student_name(s.student_name).casefold() == student_key
            ]

    review_items: list[dict[str, Any]] = []
    for s in subs:
        review_items.extend(_review_items(_parse_review(s.ai_review_json)))

    if student_key:
        pick = collect_failed_task_ids(items=review_items)
    else:
        pick = collect_failed_task_ids(items=review_items, heatmap=analytics.heatmap)
    pick = [n for n in pick if n in by_num][: payload.max_tasks]
    if not pick:
        raise HTTPException(
            status_code=400,
            detail="Нет заданий с баллом ниже максимума — нужна проверка с разбором",
        )

    source_title = analytics.selected_assignment_title or source.title or "Исходный тест"
    result = generate_rno(
        questions,
        pick,
        subject=getattr(classroom, "subject", None),
        source_title=source_title,
        seed=rno_seed(classroom.code, source.code, student_key or "class"),
        pick_alternate=lambda src, num: _pick_rno_alternate(db, classroom, src, num),
    )
    if not result["questions"]:
        raise HTTPException(status_code=400, detail="Не удалось собрать задания для работы над ошибками")

    return RnoPreviewOut(
        title=result["title"],
        source_title=source_title,
        source_assignment_code=source.code,
        failed_nums=result["failed_nums"],
        questions=result["questions"],
        exam_ui=result.get("exam_ui"),
        mutated_count=int(result.get("mutated_count") or 0),
        used_alt=bool(result.get("used_alt")),
    )
