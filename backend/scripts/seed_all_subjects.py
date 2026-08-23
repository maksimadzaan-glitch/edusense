"""Сид PostgreSQL: subjects, exam_types, task_prototypes из JSON-спек.

Запуск из корня проекта:
  python -m backend.scripts.seed_all_subjects
  python -m backend.scripts.seed_all_subjects --reset

Требует POSTGRES_URL в .env.
После обновления спек с template_* обязательно --reset (или upsert обновит существующие).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import delete, select

# корень проекта в sys.path при прямом запуске файла
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.db.pg import init_pg_tables, is_postgres_configured, session_factory
from backend.db.pg_models import ExamType, Subject, TaskPrototype

SPECS_DIR = Path(__file__).resolve().parent.parent / "universal" / "specs"


def _load_specs(specs_dir: Path) -> list[dict]:
    if not specs_dir.is_dir():
        raise SystemExit(f"Нет каталога спек: {specs_dir}")
    files = sorted(specs_dir.glob("*.json"))
    if not files:
        raise SystemExit(
            f"В {specs_dir} нет *.json. Сгенерируйте: python -m backend.scripts._write_universal_specs"
        )
    out: list[dict] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SystemExit(f"{path.name}: ожидался JSON-объект")
        for key in ("subject_code", "subject_name", "exam_code", "exam_name", "prototypes"):
            if key not in data:
                raise SystemExit(f"{path.name}: отсутствует поле {key}")
        if not isinstance(data["prototypes"], list) or not data["prototypes"]:
            raise SystemExit(f"{path.name}: prototypes пуст")
        data["_source"] = path.name
        out.append(data)
    return out


def _opt_text(value: object | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _figure_params_json(value: object | None) -> str | None:
    """Нормализовать figure_params в JSON-строку для PG."""
    if value is None:
        return None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    s = str(value).strip()
    return s or None


def _figure_data_json(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    s = str(value).strip()
    return s or None


def _preload_figure_svg(p: dict) -> str | None:
    """Inline SVG из поля или из pack asset по figure_data.main_figure_url."""
    from backend.services.figures import is_safe_pack_svg, load_pack_figure_svg

    raw = _opt_text(p.get("figure_svg"))
    if raw and is_safe_pack_svg(raw):
        return raw
    fig_data = p.get("figure_data")
    if isinstance(fig_data, dict):
        url = str(fig_data.get("main_figure_url") or "").strip()
        if url:
            return load_pack_figure_svg(url, pack_id="oge_math")
    return None


def seed(*, reset: bool = False, specs_dir: Path = SPECS_DIR) -> dict:
    if not is_postgres_configured():
        raise SystemExit(
            "POSTGRES_URL не задан. Пример:\n"
            "  POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:5432/edusense_universal"
        )

    init_pg_tables()
    specs = _load_specs(specs_dir)
    SessionLocal = session_factory()
    db = SessionLocal()

    subjects_upserted = 0
    exams_upserted = 0
    prototypes_inserted = 0
    prototypes_updated = 0
    with_templates = 0

    try:
        if reset:
            db.execute(delete(TaskPrototype))
            db.commit()
            print("reset: task_prototypes очищены")

        for spec in specs:
            sc = str(spec["subject_code"]).strip()
            sn = str(spec["subject_name"]).strip()
            ec = str(spec["exam_code"]).strip().upper()
            en = str(spec["exam_name"]).strip()

            subj = db.scalar(select(Subject).where(Subject.code == sc))
            if subj is None:
                db.add(Subject(code=sc, name=sn))
                subjects_upserted += 1
            else:
                subj.name = sn

            exam = db.scalar(select(ExamType).where(ExamType.code == ec))
            if exam is None:
                db.add(ExamType(code=ec, name=en))
                exams_upserted += 1
            else:
                exam.name = en

            db.flush()

            spec_tpl = 0
            for p in spec["prototypes"]:
                num = int(p["task_number"])
                part = int(p["part"])
                if part not in (1, 2):
                    raise SystemExit(f"{spec['_source']}: task {num} — part должен быть 1 или 2")
                title = str(p["prototype_title"]).strip()
                instruction = str(p["prompt_instruction"]).strip()
                if not title or not instruction:
                    raise SystemExit(f"{spec['_source']}: task {num} — пустой title/instruction")

                tpl_text = _opt_text(p.get("template_text"))
                tpl_answer = _opt_text(p.get("template_answer"))
                tpl_solution = _opt_text(p.get("template_solution"))
                fig_kind = _opt_text(p.get("figure_kind"))
                fig_params = _figure_params_json(p.get("figure_params"))
                fig_data = _figure_data_json(p.get("figure_data"))
                fig_svg = _preload_figure_svg(p)
                if tpl_text and tpl_answer:
                    spec_tpl += 1
                    with_templates += 1

                exists = db.scalar(
                    select(TaskPrototype).where(
                        TaskPrototype.subject_code == sc,
                        TaskPrototype.exam_code == ec,
                        TaskPrototype.task_number == num,
                        TaskPrototype.prototype_title == title,
                    )
                )
                if exists:
                    exists.part = part
                    exists.prompt_instruction = instruction
                    exists.template_text = tpl_text
                    exists.template_answer = tpl_answer
                    exists.template_solution = tpl_solution
                    exists.figure_kind = fig_kind
                    exists.figure_params = fig_params
                    exists.figure_data = fig_data
                    exists.figure_svg = fig_svg
                    prototypes_updated += 1
                    continue

                db.add(
                    TaskPrototype(
                        subject_code=sc,
                        exam_code=ec,
                        task_number=num,
                        part=part,
                        prototype_title=title,
                        prompt_instruction=instruction,
                        template_text=tpl_text,
                        template_answer=tpl_answer,
                        template_solution=tpl_solution,
                        figure_kind=fig_kind,
                        figure_params=fig_params,
                        figure_data=fig_data,
                        figure_svg=fig_svg,
                    )
                )
                prototypes_inserted += 1

            print(
                f"OK {spec['_source']}: {sc}/{ec} — "
                f"{len(spec['prototypes'])} prototypes "
                f"({spec_tpl} с template_text)"
            )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    summary = {
        "specs": len(specs),
        "subjects_new": subjects_upserted,
        "exams_new": exams_upserted,
        "prototypes_inserted": prototypes_inserted,
        "prototypes_updated": prototypes_updated,
        "prototypes_with_templates": with_templates,
    }
    print("seed done:", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed universal PostgreSQL prototypes")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Удалить все task_prototypes перед сидом (subjects/exam_types сохраняются)",
    )
    parser.add_argument(
        "--specs-dir",
        type=Path,
        default=SPECS_DIR,
        help="Каталог JSON-спек",
    )
    args = parser.parse_args()
    seed(reset=bool(args.reset), specs_dir=args.specs_dir)


if __name__ == "__main__":
    main()
