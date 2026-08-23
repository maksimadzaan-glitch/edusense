"""Импорт пака ОГЭ русский (JSON) → context_blocks + task_prototypes в PG.

Запуск из корня проекта:
  python -m backend.scripts.import_oge_rus
  python -m backend.scripts.import_oge_rus --json path/to/pack.json
  python -m backend.scripts.import_oge_rus --skip-seed
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

from backend.universal.packs.loader import pack_dir

PACK_ID = "oge_rus"
IMPORT_NAME = "oge_rus_v1.json"
SUBJECT_CODE = "russian"
EXAM_CODE = "OGE"
TITLE_PREFIX = "v1"

TOPIC_LABELS: dict[str, str] = {
    "summary_writing": "Сжатое изложение",
    "syntax_analysis_basis": "Грамматическая основа",
    "syntax_characteristics": "Синтаксический анализ",
    "punctuation_analysis": "Пунктуационный анализ",
    "punctuation_placement": "Знаки препинания",
    "spelling_analysis": "Орфографический анализ",
    "spelling_insertion": "Орфография: вставка букв",
    "grammar_forms": "Грамматические нормы",
    "syntax_phrase_transform": "Словосочетание",
    "text_comprehension": "Содержание текста",
    "expressive_means": "Средства выразительности",
    "lexical_analysis": "Лексический анализ",
    "essay_writing": "Сочинение",
}

PROMPT_BY_TOPIC: dict[str, str] = {
    "summary_writing": "Сжатое изложение по прослушанному тексту. Сохрани критерии и объём.",
    "syntax_analysis_basis": "Грамматическая основа. Ответ — номера без пробелов.",
    "syntax_characteristics": "Синтаксическая характеристика предложений. Ответ — номера.",
    "punctuation_analysis": "Пунктуационный анализ / соответствие. Ответ — цифры.",
    "punctuation_placement": "Расстановка знаков препинания. Ответ — цифры.",
    "spelling_analysis": "Орфографический анализ. Ответ — номера.",
    "spelling_insertion": "Вставка букв. Ответ — цифры.",
    "grammar_forms": "Грамматическая форма слова. Ответ — слово/форма.",
    "syntax_phrase_transform": "Замена словосочетания. Ответ — словосочетание.",
    "text_comprehension": "Содержание текста. Ответ — номера.",
    "expressive_means": "Средства выразительности. Ответ — номера.",
    "lexical_analysis": "Лексический анализ. Ответ — слово/словосочетание.",
    "essay_writing": "Сочинение-рассуждение. Сохрани тип 13.1/13.2/13.3 и критерии.",
}


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


def _solution_text(task: dict[str, Any]) -> str | None:
    sol = task.get("solution")
    full = None
    if isinstance(sol, dict):
        full = _opt_text(sol.get("text"))
    elif isinstance(sol, str):
        full = _opt_text(sol)
    hint = _opt_text(task.get("solution_hint"))
    if full and hint:
        return f"{hint}\n\n{full}"
    return full or hint


def _answer_type(task: dict[str, Any], *, part: int) -> str | None:
    raw = _opt_text(task.get("answer_type"))
    if not raw:
        return "string" if part == 2 else "string"
    if raw.lower() in ("detailed", "extended", "free"):
        return "string"
    return raw


def _part_for(num: int) -> int:
    return 2 if num in (1, 13) else 1


def _prompt_for(task: dict[str, Any]) -> str:
    topic = str(task.get("topic_id") or "").strip()
    num = int(task["task_number"])
    base = PROMPT_BY_TOPIC.get(topic)
    if base:
        return base
    return f"Задание ОГЭ русский №{num}. Сохрани тип КИМ и корректный ответ."


def _prototype_title(task: dict[str, Any]) -> str:
    num = int(task["task_number"])
    topic = str(task.get("topic_id") or "task").strip()
    idx = int(task.get("prototype_index") or 1)
    label = TOPIC_LABELS.get(topic) or topic.replace("_", " ")
    # человекочитаемая тема слева (для adapt.human_topic_from_title)
    return f"{label} · {TITLE_PREFIX} #{num}p{idx:02d}"


def _block_description(block: dict[str, Any]) -> str:
    text = _opt_text(block.get("text_content")) or _opt_text(block.get("description_text"))
    audio = _opt_text(block.get("audio_script"))
    if text:
        return text
    return audio or ""


def default_import_path(root: Path) -> Path:
    return root / "imports" / IMPORT_NAME


def convert_task(task: dict[str, Any]) -> dict[str, Any]:
    num = int(task["task_number"])
    part = _part_for(num)
    answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
    acceptable = task.get("acceptable_answers")
    if not isinstance(acceptable, list):
        acceptable = []
    if not acceptable and answer:
        acceptable = [answer]
    # part2 detailed: пустой acceptable ок, но answer нужен для pg_has_ready_templates
    if not answer and part == 2:
        answer = "Развёрнутый ответ"

    return {
        "task_number": num,
        "part": part,
        "prototype_title": _prototype_title(task),
        "prompt_instruction": _prompt_for(task),
        "template_text": _opt_text(task.get("statement") or task.get("template_text")),
        "template_answer": answer,
        "template_solution": _solution_text(task),
        "difficulty": _opt_text(task.get("difficulty")),
        "answer_type": _answer_type(task, part=part),
        "max_score": int(task.get("max_score") or (7 if num in (1, 13) else 1)),
        "acceptable_answers": acceptable,
        "figure_kind": None,
        "figure_params": None,
        "context_id": _opt_text(task.get("context_block_id") or task.get("context_id")),
        "source_id": _opt_text(task.get("id")),
    }


def write_context_files(
    root: Path,
    blocks: list[dict[str, Any]],
    converted: list[dict[str, Any]],
) -> list[Path]:
    cdir = root / "context_blocks"
    cdir.mkdir(parents=True, exist_ok=True)
    by_ctx: dict[str, list[dict[str, Any]]] = {}
    for row in converted:
        cid = row.get("context_id")
        if cid:
            by_ctx.setdefault(str(cid), []).append(row)

    written: list[Path] = []
    for block in blocks:
        cid = str(block.get("context_id") or "").strip()
        if not cid:
            continue
        desc = _block_description(block)
        tasks_out = []
        for row in by_ctx.get(cid, []):
            tasks_out.append(
                {
                    "task_number": row["task_number"],
                    "part": row["part"],
                    "prototype_title": row["prototype_title"],
                    "prompt_instruction": row["prompt_instruction"],
                    "template_text": row["template_text"],
                    "template_answer": row["template_answer"],
                    "template_solution": row["template_solution"],
                    "answer_type": row["answer_type"],
                    "max_score": row["max_score"],
                    "acceptable_answers": row["acceptable_answers"],
                    "figure_kind": None,
                }
            )
        if not tasks_out:
            # loader требует непустой tasks — минимальный stub-якорь
            tasks_out = [
                {
                    "task_number": 1 if cid.startswith("izlo") else 10,
                    "part": 2 if cid.startswith("izlo") else 1,
                    "prototype_title": f"{TITLE_PREFIX} · context · {cid}",
                    "prompt_instruction": f"Контекст {cid}",
                    "template_text": desc or cid,
                    "template_answer": "—",
                    "max_score": 1,
                }
            ]
        payload = {
            "context_id": cid,
            "title": str(block.get("title") or cid).strip(),
            "description_text": desc,
            "figure_kind": None,
            "figure_params": None,
            "exam_code": EXAM_CODE,
            "subject_code": SUBJECT_CODE,
            "tasks": tasks_out,
        }
        if block.get("audio_script"):
            payload["audio_script"] = block["audio_script"]
        path = cdir / f"{cid}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(path)
    return written


def write_pack_info(root: Path, pack_info_src: dict[str, Any] | None) -> Path:
    path = root / "pack_info.json"
    if path.is_file():
        return path
    info = {
        "pack_id": PACK_ID,
        "exam_code": EXAM_CODE,
        "subject_code": SUBJECT_CODE,
        "subject_name": "Русский язык",
        "exam_name": "ОГЭ",
        "kim_year": int((pack_info_src or {}).get("exam_year") or 2026),
        "title": "ОГЭ Русский язык — pack EduSense",
        "version": str((pack_info_src or {}).get("version") or "1.0.0"),
        "primary_max_score": int((pack_info_src or {}).get("max_primary_score") or 33),
        "sources": [f"imports/{IMPORT_NAME}"],
    }
    path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def seed_pg(
    blocks: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, int]:
    from sqlalchemy import select

    from backend.db.pg_models import ContextBlock, ExamType, Subject, TaskPrototype

    from backend.db.pg import init_pg_tables, session_factory

    init_pg_tables()
    SessionLocal = session_factory()
    db = SessionLocal()
    try:
        subj = db.scalar(select(Subject).where(Subject.code == SUBJECT_CODE))
        if subj is None:
            db.add(Subject(code=SUBJECT_CODE, name="Русский язык"))
        else:
            subj.name = "Русский язык"
        exam = db.scalar(select(ExamType).where(ExamType.code == EXAM_CODE))
        if exam is None:
            db.add(ExamType(code=EXAM_CODE, name="ОГЭ"))
        else:
            exam.name = "ОГЭ"
        db.flush()

        ctx_ins = ctx_upd = 0
        for block in blocks:
            cid = str(block.get("context_id") or "").strip()
            if not cid:
                continue
            title = str(block.get("title") or cid).strip()
            desc = _block_description(block) or None
            exists = db.scalar(
                select(ContextBlock).where(
                    ContextBlock.context_id == cid,
                    ContextBlock.subject_code == SUBJECT_CODE,
                    ContextBlock.exam_code == EXAM_CODE,
                )
            )
            if exists:
                exists.title = title
                exists.description_text = desc
                exists.figure_kind = None
                exists.figure_params = None
                ctx_upd += 1
            else:
                db.add(
                    ContextBlock(
                        context_id=cid,
                        title=title,
                        description_text=desc,
                        figure_kind=None,
                        figure_params=None,
                        subject_code=SUBJECT_CODE,
                        exam_code=EXAM_CODE,
                    )
                )
                ctx_ins += 1

        # убрать устаревшие слоты вне КИМ 1..13 (старый seed_all_subjects)
        stale = db.scalars(
            select(TaskPrototype).where(
                TaskPrototype.subject_code == SUBJECT_CODE,
                TaskPrototype.exam_code == EXAM_CODE,
                TaskPrototype.task_number > 13,
            )
        ).all()
        stale_n = 0
        for row in stale:
            db.delete(row)
            stale_n += 1

        proto_ins = proto_upd = 0
        for p in rows:
            num = int(p["task_number"])
            title = str(p["prototype_title"]).strip()
            exists = db.scalar(
                select(TaskPrototype).where(
                    TaskPrototype.subject_code == SUBJECT_CODE,
                    TaskPrototype.exam_code == EXAM_CODE,
                    TaskPrototype.task_number == num,
                    TaskPrototype.prototype_title == title,
                )
            )
            fields = dict(
                part=int(p["part"]),
                prompt_instruction=str(p["prompt_instruction"]).strip(),
                template_text=_opt_text(p.get("template_text")),
                template_answer=_opt_text(p.get("template_answer")),
                template_solution=_opt_text(p.get("template_solution")),
                figure_kind=None,
                figure_params=None,
                figure_data=None,
                figure_svg=None,
                context_id=_opt_text(p.get("context_id")),
                answer_type=_opt_text(p.get("answer_type")),
                max_score=int(p["max_score"]) if p.get("max_score") is not None else None,
                acceptable_answers=_json_or_none(p.get("acceptable_answers")),
            )
            if exists:
                for k, v in fields.items():
                    setattr(exists, k, v)
                proto_upd += 1
            else:
                db.add(
                    TaskPrototype(
                        subject_code=SUBJECT_CODE,
                        exam_code=EXAM_CODE,
                        task_number=num,
                        prototype_title=title,
                        **fields,
                    )
                )
                proto_ins += 1

        db.commit()
        return {
            "context_inserted": ctx_ins,
            "context_updated": ctx_upd,
            "prototypes_inserted": proto_ins,
            "prototypes_updated": proto_upd,
            "stale_deleted": stale_n,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run(*, json_path: Path | None = None, skip_seed: bool = False) -> dict[str, Any]:
    root = pack_dir(PACK_ID)
    root.mkdir(parents=True, exist_ok=True)
    imports_dir = root / "imports"
    imports_dir.mkdir(parents=True, exist_ok=True)
    dest = default_import_path(root)

    if json_path is not None:
        raw = json.loads(Path(json_path).read_text(encoding="utf-8"))
        dest.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif not dest.is_file():
        raise SystemExit(
            f"Нет файла импорта: {dest}\n"
            "Положите JSON пака туда или укажите --json PATH"
        )
    else:
        raw = json.loads(dest.read_text(encoding="utf-8"))

    if not isinstance(raw, dict) or "tasks" not in raw:
        raise SystemExit("Ожидался объект с полями pack_info / context_blocks / tasks")

    tasks = list(raw.get("tasks") or [])
    blocks = list(raw.get("context_blocks") or [])
    converted = [convert_task(t) for t in tasks]

    write_pack_info(root, raw.get("pack_info") if isinstance(raw.get("pack_info"), dict) else None)
    ctx_paths = write_context_files(root, blocks, converted)

    readme = root / "README.md"
    if not readme.is_file():
        readme.write_text(
            "# Pack oge_rus\n\n"
            "Seed: `python -m backend.scripts.import_oge_rus`\n",
            encoding="utf-8",
        )

    summary: dict[str, Any] = {
        "import_json": str(dest),
        "context_files": [str(p) for p in ctx_paths],
        "prototypes": len(converted),
        "task_numbers": sorted({int(r["task_number"]) for r in converted}),
        "seed": None,
    }

    if skip_seed:
        print("import_oge_rus (files only):", json.dumps(summary, ensure_ascii=False))
        return summary

    from backend.db.pg import is_postgres_configured

    if not is_postgres_configured():
        print("WARNING: POSTGRES_URL не задан — файлы записаны, seed пропущен")
        print("import_oge_rus:", json.dumps(summary, ensure_ascii=False))
        return summary

    summary["seed"] = seed_pg(blocks, converted)
    print("import_oge_rus done:", json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import OGE Russian pack")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Путь к исходному JSON (иначе imports/oge_rus_v1.json)",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Только файлы, без записи в Postgres",
    )
    parser.add_argument(
        "--variants",
        action="store_true",
        help="Импорт цельных вариантов (oge_rus_variants_v2.json) вместо line-based v1",
    )
    args = parser.parse_args()
    if args.variants:
        from backend.scripts.import_oge_rus_variants import run as run_variants

        run_variants(json_path=args.json, skip_seed=bool(args.skip_seed))
        return
    run(json_path=args.json, skip_seed=bool(args.skip_seed))


if __name__ == "__main__":
    main()
