"""Загрузка filesystem-паков → PostgreSQL (context_blocks + task_prototypes).

Pack layout (пример oge_math):
  packs/<pack_id>/
    pack_info.json
    topics.json
    context_blocks/*.json   # один блок = общий план/текст + tasks 1..N
    tasks/part1|part2/      # опциональные тонкие индексы / samples

Runtime store — Postgres. Generate читает только PG.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.pg_models import ContextBlock, ExamType, Subject, TaskPrototype

PACKS_DIR = Path(__file__).resolve().parent


def pack_dir(pack_id: str = "oge_math") -> Path:
    return PACKS_DIR / pack_id


def _opt_text(value: object | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _json_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    s = str(value).strip()
    return s or None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_pack_info(root: Path) -> dict[str, Any]:
    path = root / "pack_info.json"
    if not path.is_file():
        raise FileNotFoundError(f"Нет pack_info.json: {path}")
    data = _load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: ожидался объект")
    return data


def iter_context_blocks(root: Path) -> list[dict[str, Any]]:
    cdir = root / "context_blocks"
    if not cdir.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(cdir.glob("*.json")):
        data = _load_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"{path.name}: ожидался объект context_block")
        if not data.get("context_id"):
            raise ValueError(f"{path.name}: нет context_id")
        tasks = data.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise ValueError(f"{path.name}: пустой tasks")
        data["_source"] = path.name
        out.append(data)
    return out


def _ensure_subject_exam(
    db: Session,
    *,
    subject_code: str,
    subject_name: str,
    exam_code: str,
    exam_name: str,
) -> None:
    subj = db.scalar(select(Subject).where(Subject.code == subject_code))
    if subj is None:
        db.add(Subject(code=subject_code, name=subject_name))
    else:
        subj.name = subject_name

    exam = db.scalar(select(ExamType).where(ExamType.code == exam_code))
    if exam is None:
        db.add(ExamType(code=exam_code, name=exam_name))
    else:
        exam.name = exam_name
    db.flush()


def _upsert_context_block(
    db: Session,
    block: dict[str, Any],
    *,
    subject_code: str,
    exam_code: str,
) -> tuple[str, bool]:
    cid = str(block["context_id"]).strip()
    title = str(block.get("title") or cid).strip()
    desc = _opt_text(block.get("description_text"))
    fig_kind = _opt_text(block.get("figure_kind"))
    fig_params = _json_or_none(block.get("figure_params"))

    exists = db.scalar(
        select(ContextBlock).where(
            ContextBlock.context_id == cid,
            ContextBlock.subject_code == subject_code,
            ContextBlock.exam_code == exam_code,
        )
    )
    if exists:
        exists.title = title
        exists.description_text = desc
        exists.figure_kind = fig_kind
        exists.figure_params = fig_params
        return cid, False

    db.add(
        ContextBlock(
            context_id=cid,
            title=title,
            description_text=desc,
            figure_kind=fig_kind,
            figure_params=fig_params,
            subject_code=subject_code,
            exam_code=exam_code,
        )
    )
    return cid, True


def _upsert_linked_task(
    db: Session,
    task: dict[str, Any],
    *,
    subject_code: str,
    exam_code: str,
    context_id: str,
    block_figure_kind: str | None,
    block_figure_params: str | None,
) -> str:
    num = int(task["task_number"])
    part = int(task.get("part") or 1)
    title = str(task["prototype_title"]).strip()
    instruction = str(
        task.get("prompt_instruction")
        or f"Задание {num} контекста {context_id}. Сохрани тип и корректный ответ."
    ).strip()
    answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
    text = _opt_text(task.get("template_text"))
    solution = _opt_text(task.get("template_solution"))
    answer_type = _opt_text(task.get("answer_type"))
    max_score = task.get("max_score")
    max_score_i = int(max_score) if max_score is not None else (2 if part == 2 else 1)
    acceptable = task.get("acceptable_answers")
    if acceptable is None and answer:
        acceptable = [answer]
    acceptable_json = _json_or_none(acceptable)

    # Фигура: из задания, иначе общая с context_block
    fig_kind = _opt_text(task.get("figure_kind")) or block_figure_kind
    fig_params = _json_or_none(task.get("figure_params")) or block_figure_params

    exists = db.scalar(
        select(TaskPrototype).where(
            TaskPrototype.subject_code == subject_code,
            TaskPrototype.exam_code == exam_code,
            TaskPrototype.task_number == num,
            TaskPrototype.prototype_title == title,
        )
    )
    fields = dict(
        part=part,
        prompt_instruction=instruction,
        template_text=text,
        template_answer=answer,
        template_solution=solution,
        figure_kind=fig_kind,
        figure_params=fig_params,
        context_id=context_id,
        answer_type=answer_type,
        max_score=max_score_i,
        acceptable_answers=acceptable_json,
    )
    if exists:
        for k, v in fields.items():
            setattr(exists, k, v)
        return "updated"

    db.add(
        TaskPrototype(
            subject_code=subject_code,
            exam_code=exam_code,
            task_number=num,
            prototype_title=title,
            **fields,
        )
    )
    return "inserted"


def sync_pack_to_pg(
    db: Session,
    *,
    pack_id: str = "oge_math",
    root: Path | None = None,
) -> dict[str, Any]:
    """Загрузить pack → context_blocks + связанные task_prototypes."""
    root = root or pack_dir(pack_id)
    if not root.is_dir():
        raise FileNotFoundError(f"Нет каталога пака: {root}")

    info = load_pack_info(root)
    subject_code = str(info.get("subject_code") or "math").strip()
    exam_code = str(info.get("exam_code") or "OGE").strip().upper()
    subject_name = str(info.get("subject_name") or "Математика").strip()
    exam_name = str(info.get("exam_name") or exam_code).strip()

    _ensure_subject_exam(
        db,
        subject_code=subject_code,
        subject_name=subject_name,
        exam_code=exam_code,
        exam_name=exam_name,
    )

    blocks = iter_context_blocks(root)
    ctx_new = 0
    ctx_upd = 0
    proto_ins = 0
    proto_upd = 0

    for block in blocks:
        cid, created = _upsert_context_block(
            db, block, subject_code=subject_code, exam_code=exam_code
        )
        if created:
            ctx_new += 1
        else:
            ctx_upd += 1

        fig_kind = _opt_text(block.get("figure_kind"))
        fig_params = _json_or_none(block.get("figure_params"))

        for task in block["tasks"]:
            action = _upsert_linked_task(
                db,
                task,
                subject_code=subject_code,
                exam_code=exam_code,
                context_id=cid,
                block_figure_kind=fig_kind,
                block_figure_params=fig_params,
            )
            if action == "inserted":
                proto_ins += 1
            else:
                proto_upd += 1

    summary = {
        "pack_id": pack_id,
        "subject_code": subject_code,
        "exam_code": exam_code,
        "context_blocks": len(blocks),
        "context_inserted": ctx_new,
        "context_updated": ctx_upd,
        "prototypes_inserted": proto_ins,
        "prototypes_updated": proto_upd,
    }
    return summary
