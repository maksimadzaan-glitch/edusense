"""Залить бесплатный пул заданий 4–9 ОГЭ русский (без LLM).

  py -3 -m backend.scripts.seed_oge_rus_pool
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

POOL_ID = "oge_rus_pool_49"
POOL_PATH = (
    _ROOT
    / "backend"
    / "universal"
    / "packs"
    / "oge_rus"
    / "imports"
    / "oge_rus_pool_49.json"
)
SUBJECT = "russian"
EXAM = "OGE"


def _rows_from_pool() -> list[dict]:
    from backend.scripts.oge_rus_convert import (
        _matching_statement,
        _oge_rus_payload,
        _opt_text,
        _prompt_for,
        _prototype_title,
    )

    raw = json.loads(POOL_PATH.read_text(encoding="utf-8"))
    out: list[dict] = []
    for i, task in enumerate(raw.get("tasks") or [], start=1):
        num = int(task["task_number"])
        topic = str(task.get("topic") or "task")
        matching = task.get("matching") if isinstance(task.get("matching"), dict) else None
        if matching:
            text = _matching_statement(task)
            payload = _oge_rus_payload(kim_type=num, matching=matching)
        else:
            text = _opt_text(task.get("statement"))
            payload = _oge_rus_payload(kim_type=num)
        payload["subtype"] = _opt_text(task.get("subtype")) or topic
        payload["difficulty"] = str(task.get("difficulty") or "medium").strip().lower()
        answer = _opt_text(task.get("correct_answer"))
        acc = task.get("acceptable_answers")
        if not isinstance(acc, list) and answer:
            acc = [answer]
        out.append(
            {
                "task_number": num,
                "part": 1,
                "prototype_title": _prototype_title(
                    variant_id=f"{POOL_ID}_{i:02d}",
                    num=num,
                    topic=topic,
                    title_prefix="pool",
                ),
                "prompt_instruction": _prompt_for(topic, num),
                "template_text": text,
                "template_answer": answer,
                "template_solution": _opt_text(task.get("solution_hint")),
                "answer_type": "string",
                "max_score": 1,
                "acceptable_answers": acc or [],
                "figure_params": payload,
                "context_id": POOL_ID,
                "difficulty": payload["difficulty"],
            }
        )
    return out


def seed() -> dict:
    from sqlalchemy import select

    from backend.db.pg import init_pg_tables, is_postgres_configured, session_factory
    from backend.db.pg_models import TaskPrototype
    from backend.scripts.import_oge_rus_variants import _json_or_none, _opt_text

    if not is_postgres_configured():
        raise SystemExit("POSTGRES_URL не задан")
    rows = _rows_from_pool()
    init_pg_tables()
    db = session_factory()()
    try:
        old = list(
            db.scalars(
                select(TaskPrototype).where(
                    TaskPrototype.subject_code == SUBJECT,
                    TaskPrototype.exam_code == EXAM,
                    TaskPrototype.context_id == POOL_ID,
                )
            ).all()
        )
        for r in old:
            db.delete(r)
        db.flush()
        for p in rows:
            db.add(
                TaskPrototype(
                    subject_code=SUBJECT,
                    exam_code=EXAM,
                    task_number=int(p["task_number"]),
                    prototype_title=str(p["prototype_title"]),
                    part=1,
                    prompt_instruction=str(p["prompt_instruction"]),
                    template_text=_opt_text(p.get("template_text")),
                    template_answer=_opt_text(p.get("template_answer")),
                    template_solution=_opt_text(p.get("template_solution")),
                    figure_kind=None,
                    figure_params=_json_or_none(p.get("figure_params")),
                    context_id=POOL_ID,
                    answer_type="string",
                    max_score=1,
                    acceptable_answers=_json_or_none(p.get("acceptable_answers")),
                )
            )
        db.commit()
        return {"deleted": len(old), "inserted": len(rows), "context_id": POOL_ID}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    info = seed()
    print(json.dumps(info, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
