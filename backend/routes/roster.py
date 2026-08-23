"""Ростер класса и карточки учеников для экрана «Ученики»."""

from __future__ import annotations

import asyncio
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database import SessionLocal, get_db
from backend.models import Assignment, ClassStudent, Submission
from backend.schemas.edu import (
    RosterEntryOut,
    RosterOut,
    RosterPutRequest,
    StudentCardOut,
    StudentsListOut,
)
from backend.services.analytics_labels import translate_topic_slug
from backend.services.classroom import ensure_edu_class, normalize_student_name

router = APIRouter(prefix="/api/classes", tags=["roster"])


def _parse_names(raw: list[str]) -> list[str]:
    """Разобрать список ФИО: уникальные, порядок сохранения, без пустых."""
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        for part in str(item or "").replace(";", "\n").splitlines():
            name = normalize_student_name(part)
            if not name:
                continue
            key = name.casefold()
            if key in seen:
                continue
            seen.add(key)
            out.append(name)
    return out


def _topic_map_from_questions(questions_json: Optional[str]) -> dict[int, str]:
    try:
        questions = json.loads(questions_json or "[]")
    except json.JSONDecodeError:
        return {}
    if not isinstance(questions, list):
        return {}
    mapping: dict[int, str] = {}
    for q in questions:
        if not isinstance(q, dict):
            continue
        try:
            num = int(q.get("num") or 0)
        except (TypeError, ValueError):
            continue
        if not num:
            continue
        topic = str(q.get("topic") or "").strip()
        if topic:
            mapping[num] = topic
    return mapping


def _weak_topics_from_review(
    ai_review_json: Optional[str], topic_by_num: dict[int, str]
) -> list[str]:
    if not ai_review_json:
        return []
    try:
        review = json.loads(ai_review_json)
    except json.JSONDecodeError:
        return []
    if not isinstance(review, dict):
        return []
    items = review.get("items")
    if not isinstance(items, list):
        return []
    tags: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        status = str(it.get("status") or "")
        if status not in ("wrong", "empty"):
            continue
        try:
            num = int(it.get("num") or 0)
        except (TypeError, ValueError):
            num = 0
        topic = topic_by_num.get(num) if num else None
        if topic:
            tags.append(translate_topic_slug(topic) or topic)
        elif num:
            tags.append(f"№{num}")
    return tags


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


def _sync_expected_students(db: Session, class_id: int, count: int) -> None:
    """Проставить expected_students = длина ростера на работах класса."""
    if count < 1:
        return
    rows = db.query(Assignment).filter(Assignment.class_id == class_id).all()
    for row in rows:
        row.expected_students = count


def _entry_out(row: ClassStudent) -> RosterEntryOut:
    return RosterEntryOut(
        id=row.id,
        name=row.name,
        created_at=row.created_at,
    )


def _roster_payload(classroom, rows: list[ClassStudent]) -> RosterOut:
    entries = [_entry_out(r) for r in rows]
    names = [e.name for e in entries]
    return RosterOut(
        class_code=classroom.code,
        names=names,
        entries=entries,
        count=len(names),
    )


@router.get("/{code}/roster", response_model=RosterOut)
def get_roster(code: str, db: Session = Depends(get_db)):
    classroom = ensure_edu_class(db, class_code=code)
    rows = (
        db.query(ClassStudent)
        .filter(ClassStudent.class_id == classroom.id)
        .order_by(ClassStudent.id.asc())
        .all()
    )
    db.commit()
    return _roster_payload(classroom, rows)


@router.put("/{code}/roster", response_model=RosterOut)
def put_roster(code: str, payload: RosterPutRequest, db: Session = Depends(get_db)):
    classroom = ensure_edu_class(db, class_code=code)
    names = _parse_names(payload.names or [])
    wanted_keys = {name.casefold() for name in names}

    existing = (
        db.query(ClassStudent).filter(ClassStudent.class_id == classroom.id).all()
    )
    existing_by_key = {
        normalize_student_name(row.name).casefold(): row for row in existing
    }

    for key, row in list(existing_by_key.items()):
        if key not in wanted_keys:
            db.delete(row)
    db.flush()

    now = datetime.utcnow()
    for name in names:
        key = name.casefold()
        row = existing_by_key.get(key)
        if row is None:
            db.add(ClassStudent(class_id=classroom.id, name=name, created_at=now))
        else:
            row.name = name

    _sync_expected_students(db, classroom.id, len(names))
    db.commit()

    rows = (
        db.query(ClassStudent)
        .filter(ClassStudent.class_id == classroom.id)
        .order_by(ClassStudent.id.asc())
        .all()
    )
    return _roster_payload(classroom, rows)


@router.get("/{code}/students", response_model=StudentsListOut)
def list_students(code: str, db: Session = Depends(get_db)):
    classroom = ensure_edu_class(db, class_code=code)
    roster_rows = (
        db.query(ClassStudent)
        .filter(ClassStudent.class_id == classroom.id)
        .order_by(ClassStudent.id.asc())
        .all()
    )
    roster_names = [r.name for r in roster_rows]
    roster_keys = {normalize_student_name(n).casefold(): n for n in roster_names}

    assignments = (
        db.query(Assignment).filter(Assignment.class_id == classroom.id).all()
    )
    assign_by_id = {a.id: a for a in assignments}
    topic_maps = {
        a.id: _topic_map_from_questions(a.questions_json) for a in assignments
    }

    subs: list[Submission] = []
    if assign_by_id:
        subs = (
            db.query(Submission)
            .filter(Submission.assignment_id.in_(list(assign_by_id.keys())))
            .all()
        )

    # key -> aggregates
    agg_scores: dict[str, list[float]] = defaultdict(list)
    agg_percents: dict[str, list[float]] = defaultdict(list)
    agg_counts: Counter[str] = Counter()
    agg_last: dict[str, datetime] = {}
    agg_topics: dict[str, Counter[str]] = defaultdict(Counter)
    display_name: dict[str, str] = dict(roster_keys)

    for s in subs:
        name = normalize_student_name(s.student_name)
        if not name:
            continue
        key = name.casefold()
        if key not in display_name:
            display_name[key] = name
        agg_counts[key] += 1
        if s.score is not None:
            try:
                agg_scores[key].append(float(s.score))
            except (TypeError, ValueError):
                pass
        mx = _max_score_from_review(s.ai_review_json)
        pct = _score_percent(s.score, mx)
        if pct is not None:
            agg_percents[key].append(pct)
        when = s.created_at
        if when and (key not in agg_last or when > agg_last[key]):
            agg_last[key] = when
        topics = _weak_topics_from_review(
            s.ai_review_json, topic_maps.get(s.assignment_id) or {}
        )
        for t in topics:
            agg_topics[key][t] += 1

    # порядок: ростер, затем сдавшие вне ростера
    ordered_keys: list[str] = []
    for n in roster_names:
        k = normalize_student_name(n).casefold()
        if k not in ordered_keys:
            ordered_keys.append(k)
    for k in display_name:
        if k not in ordered_keys:
            ordered_keys.append(k)

    students: list[StudentCardOut] = []
    for key in ordered_keys:
        scores = agg_scores.get(key) or []
        percents = agg_percents.get(key) or []
        weak = [
            translate_topic_slug(t) or t
            for t, _ in agg_topics.get(key, Counter()).most_common(5)
        ]
        students.append(
            StudentCardOut(
                name=display_name[key],
                in_roster=key in roster_keys,
                avg_score=round(sum(scores) / len(scores), 2) if scores else None,
                avg_percent=round(sum(percents) / len(percents), 1) if percents else None,
                submissions_count=int(agg_counts.get(key) or 0),
                weak_topics=weak,
                last_activity_at=agg_last.get(key),
            )
        )

    db.commit()
    return StudentsListOut(
        class_code=classroom.code,
        roster_count=len(roster_names),
        students=students,
    )


@router.get("/{code}/live")
async def live_class_roster(code: str):
    """SSE: имена учеников, как только кто-то ввёл код на телефоне."""

    async def events():
        last = None
        while True:
            db = SessionLocal()
            try:
                classroom = ensure_edu_class(db, class_code=code)
                rows = (
                    db.query(ClassStudent)
                    .filter(ClassStudent.class_id == classroom.id)
                    .order_by(ClassStudent.id.asc())
                    .all()
                )
                names = [r.name for r in rows]
                payload = json.dumps(
                    {"names": names, "count": len(names)},
                    ensure_ascii=False,
                )
            except HTTPException:
                payload = json.dumps({"names": [], "count": 0, "error": True})
            except Exception:
                payload = last or json.dumps({"names": [], "count": 0})
            finally:
                db.close()

            if payload != last:
                yield f"data: {payload}\n\n"
                last = payload
            else:
                yield ": ping\n\n"
            await asyncio.sleep(1.5)

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
