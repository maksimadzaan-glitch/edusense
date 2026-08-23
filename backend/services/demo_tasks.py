"""Автосид демо-заданий из tasks_template.json для /task-demo."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from backend.db.pg_models import Task
from backend.services.task_answers import TASK_TYPES

_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "universal" / "packs" / "tasks_template.json"
)


def _upsert_row(db: Session, item: dict[str, Any]) -> None:
    tid = str(item["id"]).strip()
    payload = item.get("payload")
    if payload is None:
        payload_str = None
    elif isinstance(payload, (dict, list)):
        payload_str = json.dumps(payload, ensure_ascii=False)
    else:
        payload_str = str(payload)

    row = db.get(Task, tid)
    if row is None:
        row = Task(id=tid)
        db.add(row)
    row.subject = str(item["subject"]).strip().upper()
    row.exam_type = str(item["exam_type"]).strip().upper()
    row.task_number = int(item["task_number"])
    row.task_type = str(item["type"]).strip().upper()
    row.statement = str(item["statement"]).strip()
    row.payload = payload_str
    row.correct_answer = str(item.get("correct_answer") or "")
    row.max_score = int(item.get("max_score") or 1)
    row.topic = (str(item["topic"]).strip() if item.get("topic") else None) or None
    row.difficulty = (str(item["difficulty"]).strip() if item.get("difficulty") else None) or None
    row.context_id = (str(item["context_id"]).strip() if item.get("context_id") else None) or None
    row.active = bool(item["active"]) if "active" in item else True


def _iter_template_items() -> list[dict[str, Any]]:
    raw = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict) and isinstance(raw.get("tasks"), list):
        items = raw["tasks"]
    else:
        raise ValueError("tasks_template.json: expected list or {tasks: [...]}")

    out: list[dict[str, Any]] = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"tasks[{i}]: expected object")
        t = str(item.get("type") or "").strip().upper()
        exam = str(item.get("exam_type") or "").strip().upper()
        if t not in TASK_TYPES:
            raise ValueError(f"tasks[{i}]: bad type {t!r}")
        if exam not in ("OGE", "EGE"):
            raise ValueError(f"tasks[{i}]: bad exam_type {exam!r}")
        if not item.get("id") or not item.get("statement"):
            raise ValueError(f"tasks[{i}]: missing id/statement")
        out.append(item)
    return out


def ensure_demo_tasks_seeded(db: Session) -> dict[str, Any]:
    """Если активных universal tasks нет — импортировать шаблон."""
    active = db.query(Task).filter(Task.active.is_(True)).count()
    if active > 0:
        return {"seeded": False, "inserted": 0, "total": active}

    if not _TEMPLATE.is_file():
        return {"seeded": False, "inserted": 0, "total": 0, "error": "template missing"}

    items = _iter_template_items()
    for item in items:
        _upsert_row(db, item)
    db.commit()
    total = db.query(Task).filter(Task.active.is_(True)).count()
    return {"seeded": True, "inserted": len(items), "total": total}
