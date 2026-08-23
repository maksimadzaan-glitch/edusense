"""Импорт finish-пака ОГЭ math (JSON от контент-агента) → assets + PG.

Запуск из корня проекта:
  python -m backend.scripts.import_oge_math_finish
  python -m backend.scripts.import_oge_math_finish --json path/to/pack.json
  python -m backend.scripts.import_oge_math_finish --skip-seed

Шаги:
  1) сохранить/прочитать raw JSON в packs/oge_math/imports/
  2) context_blocks/plan_uchastka_01.json + plan SVG
  3) SVG 23–25 в assets/figures/part2/
  4) upsert context + prototypes 1–25 в Postgres (если POSTGRES_URL)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.services.figures import is_safe_pack_svg, svg_plan
from backend.services.prompts import polish_fipi_text
from backend.universal.packs.loader import pack_dir, sync_pack_to_pg

PACK_ID = "oge_math"


def _post_polish(text: str) -> str:
    """Дочистка типичных хвостов после polish_fipi_text (\\le, {,}, ^\\circ)."""
    s = str(text or "")
    if not s:
        return s
    s = s.replace("{,}", ",")
    s = re.sub(r"\^?\\?circ\b", "°", s)
    s = re.sub(r"\bcirc\b", "°", s)
    # не трогать слова вроде «лесенка» — только короткие TeX-остатки
    s = re.sub(r"(?<![A-Za-zА-Яа-яёЁ])le(?![A-Za-zА-Яа-яёЁ])", "≤", s)
    s = re.sub(r"(?<![A-Za-zА-Яа-яёЁ])leq(?![A-Za-zА-Яа-яёЁ])", "≤", s)
    s = re.sub(r"(?<![A-Za-zА-Яа-яёЁ])ge(?![A-Za-zА-Яа-яёЁ])", "≥", s)
    s = re.sub(r"(?<![A-Za-zА-Яа-яёЁ])geq(?![A-Za-zА-Яа-яёЁ])", "≥", s)
    s = re.sub(r"(?<![A-Za-zА-Яа-яёЁ])neq(?![A-Za-zА-Яа-яёЁ])", "≠", s)
    s = re.sub(r"(?<![A-Za-zА-Яа-яёЁ])infty(?![A-Za-zА-Яа-яёЁ])", "∞", s)
    s = re.sub(r"(?<![A-Za-zА-Яа-яёЁ])inf(?![A-Za-zА-Яа-яёЁ])", "∞", s)
    s = re.sub(r"\^{([^{}]+)}", r"^\1", s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r" +([.,;:!?])", r"\1", s)
    return s.strip()


def polish_pack_text(value: str) -> str:
    return _post_polish(polish_fipi_text(value))

IMPORT_NAME = "oge_math_finish_v1.json"
CONTEXT_ID = "plan_uchastka_01"
TITLE_PREFIX = "finish_v1"

# План согласован с ответами: дом=3, сарай=5, баня=4, теплица=1; гараж=7, огород=2.
# Клетка 2 м; дом 21 клетка → 84 м²; гараж 12 → 48 м²; площадка 4×4 → 64 м².
# Дом↔гараж: катеты 4 и 3 клетки → 10 м.
PLAN_FIGURE_PARAMS: dict[str, Any] = {
    "title": "План домохозяйства",
    "width": 16,
    "height": 10,
    "cell_m": 2,
    "gate": {"side": "bottom", "at": 8, "width": 2},
    "rooms": [
        {"id": "2", "label": "2", "name": "Огород", "x": 0, "y": 0, "w": 5, "h": 4},
        {"id": "1", "label": "1", "name": "Теплица", "x": 1, "y": 1, "w": 2, "h": 2},
        {"id": "3", "label": "3", "name": "Жилой дом", "x": 8, "y": 0, "w": 7, "h": 3},
        {"id": "7", "label": "7", "name": "Гараж", "x": 0, "y": 6, "w": 4, "h": 3},
        {"id": "5", "label": "5", "name": "Сарай", "x": 4, "y": 6, "w": 2, "h": 2},
        {"id": "4", "label": "4", "name": "Баня", "x": 10, "y": 7, "w": 3, "h": 3},
    ],
}

PROMPT_BY_TOPIC: dict[str, str] = {
    "practical_context_matching": "Сопоставление объектов плана с цифрами. Сохрани тип ответа — последовательность цифр.",
    "practical_context_tiles": "Подсчёт плитки/упаковок по плану. Ответ — целое число.",
    "practical_context_area": "Площадь объекта по клеткам и масштабу. Ответ в м².",
    "practical_context_distance": "Расстояние по прямой между объектами плана (Пифагор). Ответ в метрах.",
    "practical_context_choice": "Выбор/окупаемость по таблице тарифов. Ответ — число.",
    "algebra_fractions": "Вычисление с обыкновенными и десятичными дробями. Сохрани тип.",
    "algebra_number_line": "Точка на координатной прямой. Сохрани варианты ответа.",
    "algebra_powers_roots": "Степени и корни. Сохрани тип выражения.",
    "algebra_equations": "Уравнение; при нескольких корнях — по условию. Ответ — число.",
    "probability": "Классическая вероятность. Допустимы 0.1 и 0,1.",
    "algebra_functions_graphs": "Соответствие графиков и формул. Ответ — последовательность цифр.",
    "algebra_formula_eval": "Подстановка в формулу. Ответ — число.",
    "algebra_inequalities": "Решение неравенства / выбор промежутка. Ответ — номер варианта.",
    "algebra_progressions": "Арифметическая/геометрическая прогрессия. Ответ — число.",
    "geometry_triangles": "Треугольник: элементы, медиана, углы. Ответ — число.",
    "geometry_circles": "Окружность / вписанный четырёхугольник. Ответ в градусах или длине.",
    "geometry_quadrilaterals": "Ромб/параллелограмм/трапеция. Ответ — число.",
    "geometry_grid": "Фигура на клетчатой бумаге. Ответ — число.",
    "geometry_statements": "Верное утверждение. Ответ — номер.",
    "algebra_part2_equations": "Уравнение ч.2 с полным решением. Сохрани тип.",
    "algebra_part2_word_problems": "Текстовая задача ч.2. Сохрани ход решения.",
    "algebra_part2_function_plots": "График + параметр. Ученик строит сам; figure не нужен.",
    "geometry_part2_calc": "Планиметрия на вычисление. Чертёж к условию обязателен.",
    "geometry_part2_proof": "Геометрическое доказательство. Чертёж к условию обязателен.",
    "geometry_part2_hard": "Сложная планиметрия. Чертёж к условию обязателен.",
}

FIGURE_OVERRIDES: dict[int, dict[str, Any]] = {
    7: {
        "figure_kind": "numberline",
        "figure_params": {
            "min": 5,
            "max": 8,
            "points": [{"x": 6.48, "label": "A"}],
            "label": "точка A между 6 и 7",
        },
    },
    11: {
        "figure_kind": None,
        "figure_params": None,
    },
    18: {
        "figure_kind": "grid",
        "figure_params": {
            "cols": 10,
            "rows": 6,
            "title": "трапеция",
            "polygons": [[[1, 1], [8, 1], [6, 4], [3, 4]]],
        },
    },
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


def _ensure_geo_classes(svg: str) -> str:
    """Добавить class=\"geo-fig fipi-fig\" на корневой <svg>, если нет."""
    s = (svg or "").strip()
    if not s.lower().startswith("<svg"):
        return s
    if re.search(r'class\s*=\s*["\'][^"\']*\bgeo-fig\b', s, re.I) and re.search(
        r'class\s*=\s*["\'][^"\']*\bfipi-fig\b', s, re.I
    ):
        return s

    def _inject(m: re.Match[str]) -> str:
        tag = m.group(0)
        cm = re.search(r'class\s*=\s*([\'"])(.*?)\1', tag, re.I)
        if cm:
            classes = cm.group(2).split()
            for need in ("geo-fig", "fipi-fig"):
                if need not in classes:
                    classes.append(need)
            new_cls = " ".join(classes)
            return re.sub(
                r'class\s*=\s*[\'"].*?[\'"]',
                f'class="{new_cls}"',
                tag,
                count=1,
                flags=re.I,
            )
        return tag[:-1] + ' class="geo-fig fipi-fig">'

    return re.sub(r"<svg\b[^>]*>", _inject, s, count=1, flags=re.I)


def _solution_text(task: dict[str, Any], *, part: int) -> str | None:
    sol = task.get("solution")
    full = None
    if isinstance(sol, dict):
        full = _opt_text(sol.get("text"))
    elif isinstance(sol, str):
        full = _opt_text(sol)
    hint = _opt_text(task.get("solution_hint"))
    if part == 2 and full:
        raw = full
    elif full and hint:
        raw = f"{hint}\n\n{full}"
    else:
        raw = full or hint
    return polish_pack_text(raw) if raw else None


def _prompt_for(task: dict[str, Any]) -> str:
    topic = str(task.get("topic_id") or "").strip()
    num = int(task["task_number"])
    base = PROMPT_BY_TOPIC.get(topic)
    if base:
        return base
    return f"Задание ОГЭ №{num}. Сохрани тип КИМ и корректный ответ."


def _prototype_title(task: dict[str, Any]) -> str:
    num = int(task["task_number"])
    topic = str(task.get("topic_id") or "task").strip()
    return f"{TITLE_PREFIX} · {num} · {topic}"


def _answer_type(task: dict[str, Any], *, part: int) -> str | None:
    raw = _opt_text(task.get("answer_type"))
    if not raw:
        return "number" if part == 1 else "string"
    if raw.lower() in ("detailed", "extended", "free"):
        return "string"
    return raw


def default_import_path(root: Path) -> Path:
    return root / "imports" / IMPORT_NAME


def build_plan_context(
    src_block: dict[str, Any],
    tasks_1_5: list[dict[str, Any]],
) -> dict[str, Any]:
    desc = str(src_block.get("description_text") or "").strip()
    out_tasks: list[dict[str, Any]] = []
    for task in tasks_1_5:
        num = int(task["task_number"])
        stmt = polish_pack_text(str(task.get("statement") or ""))
        # Контекст не подмешивается generate'ом — вшиваем описание в текст 1–5.
        text = f"{desc}\n\n{stmt}".strip() if desc else stmt
        answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
        acceptable = task.get("acceptable_answers")
        if acceptable is None and answer:
            acceptable = [answer]
        out_tasks.append(
            {
                "task_number": num,
                "part": 1,
                "prototype_title": _prototype_title(task),
                "prompt_instruction": _prompt_for(task),
                "template_text": text,
                "template_answer": answer,
                "template_solution": _solution_text(task, part=1),
                "difficulty": _opt_text(task.get("difficulty")),
                "answer_type": _answer_type(task, part=1),
                "max_score": int(task.get("max_score") or 1),
                "acceptable_answers": acceptable,
                "figure_kind": "plan",
                "figure_params": PLAN_FIGURE_PARAMS,
            }
        )
    return {
        "context_id": CONTEXT_ID,
        "title": str(src_block.get("title") or "План домохозяйства").strip(),
        "description_text": desc,
        "figure_kind": "plan",
        "figure_params": PLAN_FIGURE_PARAMS,
        "exam_code": "OGE",
        "subject_code": "math",
        "tasks": out_tasks,
    }


def _part2_figure_payload(
    task: dict[str, Any],
    *,
    rel_url: str,
    svg: str,
) -> tuple[dict[str, Any], str]:
    src_fd = task.get("figure_data") if isinstance(task.get("figure_data"), dict) else {}
    steps = src_fd.get("steps") if isinstance(src_fd.get("steps"), list) else []
    fig_data = {
        "has_condition_figure": True,
        "has_solution_figure": bool(src_fd.get("has_solution_figure", True)),
        "figure_type": "svg_file",
        "main_figure_url": rel_url,
        "steps": steps,
    }
    # dark_mode urls игнорируем — файлов нет
    return fig_data, svg


def convert_standalone_task(task: dict[str, Any]) -> dict[str, Any]:
    num = int(task["task_number"])
    part = 1 if num <= 19 else 2
    stmt = polish_pack_text(str(task.get("statement") or ""))
    answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
    acceptable = task.get("acceptable_answers")
    if acceptable is None and answer:
        acceptable = [answer]

    row: dict[str, Any] = {
        "task_number": num,
        "part": part,
        "prototype_title": _prototype_title(task),
        "prompt_instruction": _prompt_for(task),
        "template_text": stmt,
        "template_answer": answer,
        "template_solution": _solution_text(task, part=part),
        "difficulty": _opt_text(task.get("difficulty")),
        "answer_type": _answer_type(task, part=part),
        "max_score": int(task.get("max_score") or (2 if part == 2 else 1)),
        "acceptable_answers": acceptable,
        "figure_kind": None,
        "figure_params": None,
        "figure_data": None,
        "figure_svg": None,
        "context_id": None,
    }

    if num in FIGURE_OVERRIDES:
        ov = FIGURE_OVERRIDES[num]
        row["figure_kind"] = ov.get("figure_kind")
        row["figure_params"] = ov.get("figure_params")

    if num in (23, 24, 25):
        fd = task.get("figure_data") if isinstance(task.get("figure_data"), dict) else {}
        svg_raw = str(fd.get("svg_content") or "").strip()
        svg = _ensure_geo_classes(svg_raw)
        asset_name = f"q{num}_001_main.svg"
        rel_url = f"/packs/{PACK_ID}/assets/figures/part2/{asset_name}"
        fig_data, svg_out = _part2_figure_payload(task, rel_url=rel_url, svg=svg)
        row["figure_kind"] = "asset"
        row["figure_data"] = fig_data
        row["figure_svg"] = svg_out if is_safe_pack_svg(svg_out) else svg_out
        row["_svg_filename"] = asset_name
        row["_svg_body"] = svg_out

    # 20–22: без декоративных картинок
    if num in (20, 21, 22):
        row["figure_kind"] = None
        row["figure_params"] = None
        row["figure_data"] = None
        row["figure_svg"] = None

    return row


def write_assets(
    root: Path,
    *,
    plan_params: dict[str, Any],
    standalone: list[dict[str, Any]],
) -> dict[str, Any]:
    plans_dir = root / "assets" / "plans"
    part2_dir = root / "assets" / "figures" / "part2"
    plans_dir.mkdir(parents=True, exist_ok=True)
    part2_dir.mkdir(parents=True, exist_ok=True)

    plan_svg = svg_plan(plan_params)
    plan_path = plans_dir / f"{CONTEXT_ID}.svg"
    plan_note = "not_generated"
    if plan_svg:
        plan_svg = _ensure_geo_classes(plan_svg)
        plan_path.write_text(plan_svg, encoding="utf-8")
        plan_note = f"wrote {plan_path.relative_to(root).as_posix()} ({len(plan_svg)} bytes)"
    else:
        plan_note = "svg_plan returned None (missing rooms?)"

    svg_written: list[str] = []
    for row in standalone:
        body = row.pop("_svg_body", None)
        name = row.pop("_svg_filename", None)
        if body and name:
            path = part2_dir / str(name)
            path.write_text(str(body), encoding="utf-8")
            svg_written.append(path.relative_to(root).as_posix())
            # убедиться, что figure_svg в row остался
            if not row.get("figure_svg"):
                row["figure_svg"] = body

    return {"plan_svg": plan_note, "part2_svg": svg_written}


def write_context_file(root: Path, block: dict[str, Any]) -> Path:
    cdir = root / "context_blocks"
    cdir.mkdir(parents=True, exist_ok=True)
    path = cdir / f"{CONTEXT_ID}.json"
    # figure_params не дублируем в каждом task при записи — loader берёт с блока,
    # но оставляем на задачах для явности (как в dacha).
    path.write_text(json.dumps(block, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def bump_pack_info(root: Path, *, version: str = "1.1.0") -> None:
    path = root / "pack_info.json"
    if not path.is_file():
        return
    info = json.loads(path.read_text(encoding="utf-8"))
    info["version"] = version
    sources = info.get("sources")
    if isinstance(sources, list):
        tag = f"imports/{IMPORT_NAME}"
        if tag not in sources:
            sources.append(tag)
    path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def seed_standalone(db, rows: list[dict[str, Any]]) -> dict[str, int]:
    from sqlalchemy import select

    from backend.db.pg_models import ExamType, Subject, TaskPrototype

    subj = db.scalar(select(Subject).where(Subject.code == "math"))
    if subj is None:
        db.add(Subject(code="math", name="Математика"))
    exam = db.scalar(select(ExamType).where(ExamType.code == "OGE"))
    if exam is None:
        db.add(ExamType(code="OGE", name="ОГЭ"))
    db.flush()

    inserted = updated = 0
    for p in rows:
        num = int(p["task_number"])
        part = int(p["part"])
        title = str(p["prototype_title"]).strip()
        exists = db.scalar(
            select(TaskPrototype).where(
                TaskPrototype.subject_code == "math",
                TaskPrototype.exam_code == "OGE",
                TaskPrototype.task_number == num,
                TaskPrototype.prototype_title == title,
            )
        )
        fields = dict(
            part=part,
            prompt_instruction=str(p["prompt_instruction"]).strip(),
            template_text=_opt_text(p.get("template_text")),
            template_answer=_opt_text(p.get("template_answer")),
            template_solution=_opt_text(p.get("template_solution")),
            figure_kind=_opt_text(p.get("figure_kind")),
            figure_params=_json_or_none(p.get("figure_params")),
            figure_data=_json_or_none(p.get("figure_data")),
            figure_svg=_opt_text(p.get("figure_svg")),
            context_id=_opt_text(p.get("context_id")),
            answer_type=_opt_text(p.get("answer_type")),
            max_score=int(p["max_score"]) if p.get("max_score") is not None else None,
            acceptable_answers=_json_or_none(p.get("acceptable_answers")),
        )
        if exists:
            for k, v in fields.items():
                setattr(exists, k, v)
            updated += 1
        else:
            db.add(
                TaskPrototype(
                    subject_code="math",
                    exam_code="OGE",
                    task_number=num,
                    prototype_title=title,
                    **fields,
                )
            )
            inserted += 1
    return {"prototypes_inserted": inserted, "prototypes_updated": updated}


def run(*, json_path: Path | None = None, skip_seed: bool = False) -> dict[str, Any]:
    root = pack_dir(PACK_ID)
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
    if len(tasks) != 25:
        print(f"WARNING: ожидалось 25 tasks, получено {len(tasks)}")

    blocks = list(raw.get("context_blocks") or [])
    src_block = next((b for b in blocks if b.get("context_id") == CONTEXT_ID), None)
    if src_block is None and blocks:
        src_block = blocks[0]
    if src_block is None:
        raise SystemExit("В JSON нет context_blocks")

    tasks_by_num = {int(t["task_number"]): t for t in tasks}
    tasks_1_5 = [tasks_by_num[n] for n in range(1, 6) if n in tasks_by_num]
    if len(tasks_1_5) != 5:
        raise SystemExit(f"Нужны задания 1–5 для контекста, есть {[t['task_number'] for t in tasks_1_5]}")

    context = build_plan_context(src_block, tasks_1_5)
    ctx_path = write_context_file(root, context)

    standalone = [convert_standalone_task(tasks_by_num[n]) for n in range(6, 26) if n in tasks_by_num]
    assets = write_assets(root, plan_params=PLAN_FIGURE_PARAMS, standalone=standalone)
    bump_pack_info(root)

    summary: dict[str, Any] = {
        "import_json": str(dest),
        "context_file": str(ctx_path),
        "context_id": CONTEXT_ID,
        "standalone_tasks": len(standalone),
        "assets": assets,
        "seed": None,
    }

    if skip_seed:
        print("import_oge_math_finish (files only):", json.dumps(summary, ensure_ascii=False))
        return summary

    from backend.db.pg import init_pg_tables, is_postgres_configured, session_factory

    if not is_postgres_configured():
        print("WARNING: POSTGRES_URL не задан — файлы записаны, seed пропущен")
        print("import_oge_math_finish:", json.dumps(summary, ensure_ascii=False))
        return summary

    init_pg_tables()
    SessionLocal = session_factory()
    db = SessionLocal()
    try:
        pack_summary = sync_pack_to_pg(db, pack_id=PACK_ID, root=root)
        stand_summary = seed_standalone(db, standalone)
        db.commit()
        summary["seed"] = {
            **pack_summary,
            "standalone_inserted": stand_summary["prototypes_inserted"],
            "standalone_updated": stand_summary["prototypes_updated"],
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("import_oge_math_finish done:", json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import OGE math finish pack")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Путь к исходному JSON (иначе imports/oge_math_finish_v1.json)",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Только файлы, без записи в Postgres",
    )
    args = parser.parse_args()
    run(json_path=args.json, skip_seed=bool(args.skip_seed))


if __name__ == "__main__":
    main()
