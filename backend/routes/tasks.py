"""API универсальных заданий (player): list / get / check / import."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db.pg import get_pg_session, is_postgres_configured
from backend.db.pg_models import Task
from backend.services.demo_tasks import ensure_demo_tasks_seeded
from backend.services.task_answers import TASK_TYPES, score_answer

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

_PG_HINT = (
    "POSTGRES_URL не задан. Добавьте в .env, например: "
    "POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:5432/edusense_universal"
)


def get_pg_db():
    """Depends: 503 если PG не настроен, иначе session."""
    if not is_postgres_configured():
        raise HTTPException(status_code=503, detail=_PG_HINT)
    yield from get_pg_session()


def _parse_payload(raw: str | None) -> Any:
    if raw is None or not str(raw).strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def task_to_dict(row: Task, *, include_answer: bool = False) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": row.id,
        "subject": row.subject,
        "exam_type": row.exam_type,
        "task_number": row.task_number,
        "type": row.task_type,
        "statement": row.statement,
        "payload": _parse_payload(row.payload),
        "max_score": row.max_score,
        "topic": row.topic,
        "difficulty": row.difficulty,
        "context_id": row.context_id,
        "active": row.active,
    }
    if include_answer:
        data["correct_answer"] = row.correct_answer
    return data


class CheckRequest(BaseModel):
    task_id: str = Field(..., min_length=1)
    answer: str = ""


class ImportTaskItem(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    subject: str = Field(..., min_length=1)
    exam_type: str = Field(..., min_length=1)
    task_number: int
    type: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    payload: Any = None
    correct_answer: str = ""
    max_score: int = 1
    topic: str | None = None
    difficulty: str | None = None
    context_id: str | None = None
    active: bool = True


class ImportRequest(BaseModel):
    tasks: list[ImportTaskItem] = Field(default_factory=list)


def _validate_item(item: ImportTaskItem) -> None:
    exam = item.exam_type.strip().upper()
    if exam not in ("OGE", "EGE"):
        raise HTTPException(status_code=422, detail=f"exam_type must be OGE|EGE, got {item.exam_type!r}")
    t = item.type.strip().upper()
    if t not in TASK_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"type must be one of {sorted(TASK_TYPES)}, got {item.type!r}",
        )
    if item.task_number < 1:
        raise HTTPException(status_code=422, detail="task_number must be >= 1")
    if item.max_score < 0:
        raise HTTPException(status_code=422, detail="max_score must be >= 0")


def _upsert_task(db: Session, item: ImportTaskItem) -> str:
    _validate_item(item)
    exam = item.exam_type.strip().upper()
    t = item.type.strip().upper()
    payload_str: str | None
    if item.payload is None:
        payload_str = None
    elif isinstance(item.payload, (dict, list)):
        payload_str = json.dumps(item.payload, ensure_ascii=False)
    else:
        payload_str = str(item.payload)

    row = db.get(Task, item.id)
    if row is None:
        row = Task(id=item.id)
        db.add(row)
    row.subject = item.subject.strip().upper()
    row.exam_type = exam
    row.task_number = int(item.task_number)
    row.task_type = t
    row.statement = item.statement.strip()
    row.payload = payload_str
    row.correct_answer = str(item.correct_answer or "")
    row.max_score = int(item.max_score)
    row.topic = (item.topic or "").strip() or None
    row.difficulty = (item.difficulty or "").strip() or None
    row.context_id = (item.context_id or "").strip() or None
    row.active = bool(item.active)
    return item.id


@router.get("")
@router.get("/")
def list_tasks(
    subject: str | None = Query(None),
    exam_type: str | None = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_pg_db),
) -> dict[str, Any]:
    try:
        ensure_demo_tasks_seeded(db)
    except Exception:
        # Не валим список: отдадим пустой/текущий и сообщение на фронте
        db.rollback()
    q = db.query(Task)
    if subject:
        q = q.filter(Task.subject == subject.strip().upper())
    if exam_type:
        q = q.filter(Task.exam_type == exam_type.strip().upper())
    if active_only:
        q = q.filter(Task.active.is_(True))
    rows = q.order_by(Task.subject, Task.exam_type, Task.task_number, Task.id).all()
    return {"ok": True, "count": len(rows), "tasks": [task_to_dict(r) for r in rows]}


@router.post("/check")
def check_task(
    body: CheckRequest,
    db: Session = Depends(get_pg_db),
) -> dict[str, Any]:
    row = db.get(Task, body.task_id)
    if row is None or not row.active:
        raise HTTPException(status_code=404, detail=f"Task {body.task_id!r} not found")
    ok, score = score_answer(body.answer, row.correct_answer, row.task_type, row.max_score)
    return {
        "ok": ok,
        "score": score,
        "max_score": row.max_score,
        "type": row.task_type,
        "task_id": row.id,
    }


@router.post("/import")
def import_tasks(
    body: ImportRequest,
    db: Session = Depends(get_pg_db),
) -> dict[str, Any]:
    """Тонкий upsert API; основной путь — CLI `python -m backend.scripts.import_tasks`."""
    if not body.tasks:
        raise HTTPException(status_code=422, detail="tasks list is empty")
    ids: list[str] = []
    try:
        for item in body.tasks:
            ids.append(_upsert_task(db, item))
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "imported": len(ids), "ids": ids}


@router.get("/{task_id}")
def get_task(
    task_id: str,
    db: Session = Depends(get_pg_db),
) -> dict[str, Any]:
    row = db.get(Task, task_id)
    if row is None or not row.active:
        raise HTTPException(status_code=404, detail=f"Task {task_id!r} not found")
    return {"ok": True, "task": task_to_dict(row)}
