"""Импорт универсальных заданий в PostgreSQL (таблица universal_tasks).

Запуск из корня проекта:
  python -m backend.scripts.import_tasks path/to.json
  python -m backend.scripts.import_tasks backend/universal/packs/tasks_template.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.db.pg import init_pg_tables, is_postgres_configured, session_factory
from backend.db.pg_models import Task
from backend.services.task_answers import TASK_TYPES

REQUIRED = ("id", "subject", "exam_type", "task_number", "type", "statement")


def _err(msg: str) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)


def _load_tasks(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        tasks = raw.get("tasks")
        if isinstance(tasks, list):
            return tasks
    raise ValueError("JSON must be a list of tasks or an object with key 'tasks'")


def validate_task(item: Any, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError(f"tasks[{index}]: expected object")
    for key in REQUIRED:
        if key not in item or item[key] is None or str(item[key]).strip() == "":
            raise ValueError(f"tasks[{index}]: missing required field {key!r}")

    tid = str(item["id"]).strip()
    if len(tid) > 64:
        raise ValueError(f"tasks[{index}]: id longer than 64 chars")

    exam = str(item["exam_type"]).strip().upper()
    if exam not in ("OGE", "EGE"):
        raise ValueError(f"tasks[{index}]: exam_type must be OGE|EGE, got {item['exam_type']!r}")

    t = str(item["type"]).strip().upper()
    if t not in TASK_TYPES:
        raise ValueError(f"tasks[{index}]: type must be one of {sorted(TASK_TYPES)}, got {item['type']!r}")

    try:
        num = int(item["task_number"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"tasks[{index}]: task_number must be int") from exc
    if num < 1:
        raise ValueError(f"tasks[{index}]: task_number must be >= 1")

    max_score = item.get("max_score", 1)
    try:
        ms = int(max_score)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"tasks[{index}]: max_score must be int") from exc
    if ms < 0:
        raise ValueError(f"tasks[{index}]: max_score must be >= 0")

    payload = item.get("payload")
    if payload is not None and not isinstance(payload, (dict, list, str)):
        raise ValueError(f"tasks[{index}]: payload must be object/array/string/null")

    return {
        "id": tid,
        "subject": str(item["subject"]).strip().upper(),
        "exam_type": exam,
        "task_number": num,
        "type": t,
        "statement": str(item["statement"]).strip(),
        "payload": payload,
        "correct_answer": str(item.get("correct_answer") or ""),
        "max_score": ms,
        "topic": (str(item["topic"]).strip() if item.get("topic") else None) or None,
        "difficulty": (str(item["difficulty"]).strip() if item.get("difficulty") else None) or None,
        "context_id": (str(item["context_id"]).strip() if item.get("context_id") else None) or None,
        "active": bool(item["active"]) if "active" in item else True,
    }


def upsert_task(db, data: dict[str, Any]) -> str:
    payload = data["payload"]
    if payload is None:
        payload_str = None
    elif isinstance(payload, (dict, list)):
        payload_str = json.dumps(payload, ensure_ascii=False)
    else:
        payload_str = str(payload)

    row = db.get(Task, data["id"])
    if row is None:
        row = Task(id=data["id"])
        db.add(row)
    row.subject = data["subject"]
    row.exam_type = data["exam_type"]
    row.task_number = data["task_number"]
    row.task_type = data["type"]
    row.statement = data["statement"]
    row.payload = payload_str
    row.correct_answer = data["correct_answer"]
    row.max_score = data["max_score"]
    row.topic = data["topic"]
    row.difficulty = data["difficulty"]
    row.context_id = data["context_id"]
    row.active = data["active"]
    return data["id"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import universal tasks into PostgreSQL")
    parser.add_argument("json_path", type=Path, help="Path to tasks JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, do not write")
    args = parser.parse_args(argv)

    path: Path = args.json_path
    if not path.is_file():
        _err(f"file not found: {path}")
        return 1

    try:
        raw_tasks = _load_tasks(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        _err(str(exc))
        return 1

    validated: list[dict[str, Any]] = []
    errors = 0
    for i, item in enumerate(raw_tasks):
        try:
            validated.append(validate_task(item, i))
        except ValueError as exc:
            _err(str(exc))
            errors += 1

    if errors:
        _err(f"validation failed: {errors} error(s)")
        return 1

    if not validated:
        _err("no tasks to import")
        return 1

    ids = [t["id"] for t in validated]
    if len(ids) != len(set(ids)):
        _err("duplicate ids in file")
        return 1

    print(f"Validated {len(validated)} task(s) from {path}")

    if args.dry_run:
        print("Dry-run OK — nothing written")
        return 0

    if not is_postgres_configured():
        _err("POSTGRES_URL not set")
        return 1

    try:
        init_pg_tables()
        SessionLocal = session_factory()
        db = SessionLocal()
        try:
            for data in validated:
                upsert_task(db, data)
                print(f"  upsert {data['id']} ({data['type']})")
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as exc:
        _err(f"import failed: {exc}")
        return 1

    print(f"OK: imported {len(validated)} task(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
