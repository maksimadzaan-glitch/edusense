"""Банк проверенных заданий: сид (досев) и сборка варианта по слотам КИМ."""

from __future__ import annotations

import hashlib
import random
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.bank_data import (
    ege_base_math,
    ege_biology,
    ege_chemistry,
    ege_informatics,
    ege_physics,
    ege_profile_math,
    ege_russian,
    oge_math,
    oge_russian,
    vpr_math,
)
from backend.models import BankTask
from backend.services.bank_keys import normalize_exam, normalize_subject_key
from backend.services.figures import attach_figure
from backend.services.prompts import polish_answer_key, polish_fipi_text
from backend.services.subject_blueprints import kim_length, kim_slots, slot_part

# (exam, subject_key, tasks_module.TASKS)
_SEED_PACKS: list[tuple[str, str, list[dict]]] = [
    ("ege", "profile_math", ege_profile_math.TASKS),
    ("ege", "base_math", ege_base_math.TASKS),
    ("oge", "oge_math", oge_math.TASKS),
    ("vpr", "vpr_math", vpr_math.TASKS),
    ("ege", "informatics", ege_informatics.TASKS),
    ("ege", "russian", ege_russian.TASKS),
    ("ege", "physics", ege_physics.TASKS),
    ("ege", "chemistry", ege_chemistry.TASKS),
    ("ege", "biology", ege_biology.TASKS),
    ("oge", "russian", oge_russian.TASKS),
]


def _stable_key(exam: str, subject_key: str, t: dict) -> str:
    """Стабильный ключ задания для досева без дублей."""
    raw = f"{exam}|{subject_key}|{int(t.get('slot') or 0)}|{(t.get('text') or '').strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def _row_stable_key(row: BankTask) -> str:
    raw = f"{row.exam}|{row.subject_key}|{int(row.slot or 0)}|{(row.text or '').strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def ensure_bank_seeded(db: Session) -> dict[str, Any]:
    """Вставить недостающие задания из bank_data (не только при пустом банке)."""
    existing_keys: set[str] = set()
    for row in db.query(BankTask).all():
        existing_keys.add(_row_stable_key(row))
        tag = (row.source_tag or "").strip()
        if tag.startswith("seed:"):
            existing_keys.add(tag.split(":", 1)[1])

    inserted = 0
    for exam, subject_key, tasks in _SEED_PACKS:
        for t in tasks:
            key = _stable_key(exam, subject_key, t)
            if key in existing_keys:
                continue
            db.add(
                BankTask(
                    exam=exam,
                    subject_key=subject_key,
                    slot=int(t["slot"]),
                    part=int(t.get("part") or 1),
                    difficulty=str(t.get("difficulty") or "medium"),
                    topic=str(t.get("topic") or "Общее"),
                    section=str(t.get("section") or "algebra"),
                    task_type=str(
                        t.get("task_type")
                        or (
                            "Развёрнутый ответ"
                            if int(t.get("part") or 1) == 2
                            else "Краткий ответ"
                        )
                    ),
                    text=str(t["text"]),
                    answer=str(t["answer"]),
                    max_score=int(
                        t.get("max_score") or (2 if int(t.get("part") or 1) == 2 else 1)
                    ),
                    needs_figure=1 if t.get("needs_figure") else 0,
                    figure_kind=t.get("figure_kind"),
                    source_tag=f"seed:{key}",
                    is_active=1,
                )
            )
            existing_keys.add(key)
            inserted += 1
    if inserted:
        db.commit()
    total = db.query(func.count(BankTask.id)).scalar() or 0
    return {"seeded": inserted > 0, "inserted": inserted, "total": total}


def bank_stats(db: Session) -> dict[str, Any]:
    ensure_bank_seeded(db)
    rows = (
        db.query(BankTask.exam, BankTask.subject_key, func.count(BankTask.id))
        .filter(BankTask.is_active == 1)
        .group_by(BankTask.exam, BankTask.subject_key)
        .all()
    )
    by_key = [
        {"exam": exam, "subject_key": sk, "count": int(n)}
        for exam, sk, n in sorted(rows, key=lambda x: (x[0], x[1]))
    ]
    total = sum(x["count"] for x in by_key)
    return {"total": total, "by_exam_subject": by_key}


def _pick_for_slot(
    pool: list[BankTask],
    *,
    slot: int,
    difficulty: str,
    used_ids: set[int],
) -> Optional[BankTask]:
    candidates = [t for t in pool if t.slot == slot and t.id not in used_ids]
    if not candidates:
        return None
    pref = [t for t in candidates if (t.difficulty or "medium") == difficulty]
    choose_from = pref or candidates
    return random.choice(choose_from)


def _task_to_question(task: BankTask, num: int) -> dict[str, Any]:
    part = int(task.part or 1)
    row = {
        "num": num,
        "part": part,
        "type": str(
            task.task_type
            or ("Развёрнутый ответ" if part == 2 else "Краткий ответ")
        ),
        "topic": polish_fipi_text(task.topic or "Общее"),
        "section": task.section or "algebra",
        "text": polish_fipi_text(task.text or ""),
        "answer": polish_answer_key(task.answer or "", part=part),
        "max_score": int(task.max_score or (2 if part == 2 else 1)),
        "needs_figure": bool(task.needs_figure),
        "figure_kind": task.figure_kind,
        "_slot": int(task.slot or num),
    }
    return attach_figure(row)


def generate_from_bank(
    db: Session,
    *,
    exam: str,
    subject: str,
    difficulty: str = "medium",
    count: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Собрать вариант: ровно одно задание на каждый слот КИМ.

    Пустые слоты не заполняются «чем попало» — их догенерирует hybrid AI.
    meta.message — формулировки «генерации» для UI (без слова «банк»).
    """
    ensure_bank_seeded(db)

    ex = normalize_exam(exam)
    sk = normalize_subject_key(exam, subject)
    diff = (difficulty or "medium").strip().lower()
    if diff not in {"easy", "medium", "hard"}:
        diff = "medium"

    full = kim_length(exam=exam, subject=subject)
    if count is None:
        n = full
    else:
        n = max(1, min(int(count or 1), full, 50))

    pool = (
        db.query(BankTask)
        .filter(
            BankTask.exam == ex,
            BankTask.subject_key == sk,
            BankTask.is_active == 1,
        )
        .all()
    )
    available = len(pool)
    slots = kim_slots(exam=exam, subject=subject, count=n)

    by_slot: dict[int, dict[str, Any]] = {}
    used: set[int] = set()
    missing: list[int] = []

    for slot in slots:
        task = _pick_for_slot(pool, slot=slot, difficulty=diff, used_ids=used)
        if task is None:
            missing.append(slot)
            continue
        used.add(task.id)
        by_slot[slot] = _task_to_question(task, slot)

    # порядок КИМ; num/_slot = номер слота (canonicalize — только после merge в hybrid)
    questions = [by_slot[s] for s in slots if s in by_slot]
    for q in questions:
        slot = int(q.get("_slot") or q["num"])
        q["num"] = slot
        q["_slot"] = slot

    filled = len(questions)
    if filled >= n:
        msg = "Вариант сгенерирован"
    elif filled > 0:
        msg = f"Вариант сгенерирован ({filled} из {n} заданий)"
    else:
        msg = "Не удалось сгенерировать задания"

    meta = {
        "source": "hybrid",
        "exam_key": ex,
        "subject_key": sk,
        "available": available,
        "requested": n,
        "filled": filled,
        "missing_slots": missing,
        "message": msg,
    }
    return questions, meta


def insert_bank_tasks(
    db: Session,
    *,
    exam: str,
    subject: str,
    tasks: list[dict[str, Any]],
    source_tag_prefix: str = "ai",
) -> int:
    """Вставить проверенные задания в банк (для enrich_bank_from_ai)."""
    ex = normalize_exam(exam)
    sk = normalize_subject_key(exam, subject)
    inserted = 0
    existing = {
        _row_stable_key(r)
        for r in db.query(BankTask)
        .filter(BankTask.exam == ex, BankTask.subject_key == sk)
        .all()
    }
    for t in tasks:
        slot = int(t.get("slot") or t.get("num") or 0)
        if slot <= 0:
            continue
        text = str(t.get("text") or "").strip()
        answer = str(t.get("answer") or "").strip()
        if len(text) < 8 or not answer:
            continue
        part = int(t.get("part") or slot_part(exam=exam, subject=subject, slot=slot))
        row_like = {
            "slot": slot,
            "text": text,
            "answer": answer,
            "part": part,
        }
        key = _stable_key(ex, sk, row_like)
        if key in existing:
            continue
        db.add(
            BankTask(
                exam=ex,
                subject_key=sk,
                slot=slot,
                part=part,
                difficulty=str(t.get("difficulty") or "medium"),
                topic=str(t.get("topic") or "Общее"),
                section=str(t.get("section") or "algebra"),
                task_type=str(
                    t.get("type")
                    or t.get("task_type")
                    or ("Развёрнутый ответ" if part == 2 else "Краткий ответ")
                ),
                text=text,
                answer=answer,
                max_score=int(t.get("max_score") or (2 if part == 2 else 1)),
                needs_figure=1 if t.get("needs_figure") else 0,
                figure_kind=t.get("figure_kind"),
                source_tag=f"{source_tag_prefix}:{key}",
                is_active=1,
            )
        )
        existing.add(key)
        inserted += 1
    if inserted:
        db.commit()
    return inserted
