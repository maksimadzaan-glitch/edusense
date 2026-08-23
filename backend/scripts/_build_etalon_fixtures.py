"""One-shot: kim_specs + etalon fixtures from oge_rus_var_kim + math demo."""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PACKS = _ROOT / "backend" / "universal" / "packs"


def write_kim_specs() -> None:
    kim_dir = PACKS / "kim_specs"
    kim_dir.mkdir(parents=True, exist_ok=True)

    math_slots = []
    for n in range(1, 26):
        part = 2 if n >= 20 else 1
        math_slots.append(
            {
                "task_number": n,
                "part": part,
                "answer_type": "EXTENDED" if part == 2 else "SHORT_VALUE",
                "max_score": 2 if part == 2 else 1,
                "needs_passage": False,
                "needs_media": n in (1, 2, 3, 4, 5, 23, 24, 25),
                "matching": False,
            }
        )
    (kim_dir / "oge_math_2026.json").write_text(
        json.dumps(
            {
                "kim_spec_id": "oge_math_2026",
                "exam_code": "OGE",
                "subject_code": "math",
                "year": 2026,
                "slot_count": 25,
                "slots": math_slots,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    rus_slots = []
    for n in range(1, 14):
        part = 2 if n in (1, 13) else 1
        rus_slots.append(
            {
                "task_number": n,
                "part": part,
                "answer_type": "EXTENDED" if part == 2 else "SHORT_VALUE",
                "max_score": {1: 6, 13: 7}.get(n, 1),
                "needs_passage": n in (2, 3, 10, 11, 12, 13),
                "needs_media": n == 1,
                "matching": n == 4,
            }
        )
    (kim_dir / "oge_rus_2026.json").write_text(
        json.dumps(
            {
                "kim_spec_id": "oge_rus_2026",
                "exam_code": "OGE",
                "subject_code": "russian",
                "year": 2026,
                "slot_count": 13,
                "slots": rus_slots,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_rus_etalon() -> None:
    src = PACKS / "oge_rus" / "imports" / "oge_rus_var_kim.json"
    raw = json.loads(src.read_text(encoding="utf-8"))
    listening = raw["listening_text"]
    grammar = raw["grammar_text"]
    reading = raw["reading_text"]
    tasks_by_num = {int(t["task_number"]): t for t in raw["tasks"]}

    t1_statement = (
        "Прослушайте текст и выполните задание 1.\n"
        "Напишите сжатое изложение. Передайте главное содержание как каждой микротемы, "
        "так и всего текста в целом. "
        f"Объём изложения — не менее {listening.get('min_words', 70)} слов."
    )

    etalon_tasks: list[dict] = [
        {
            "task_number": 1,
            "part": 2,
            "type": "EXTENDED",
            "statement": t1_statement,
            "payload": {
                "oge_rus": True,
                "kim_type": 1,
                "ui": "listening",
                "listening_text": listening.get("audio_script") or "",
                "audio_url": listening.get("audio_url"),
                "min_words": listening.get("min_words", 70),
                "image_urls": [],
                "matching": None,
            },
            "figure_svg": None,
            "figure_kind": None,
            "correct_answer": "",
            "max_score": int(listening.get("max_score") or 6),
            "topic": "summary_writing",
            "context_id": "etalon_oge_rus_var_kim",
        }
    ]
    answers: dict[str, str] = {"1": ""}

    for n in range(2, 14):
        t = tasks_by_num[n]
        payload: dict = {
            "oge_rus": True,
            "kim_type": n,
            "ui": "oge_rus",
            "image_urls": [],
            "matching": None,
        }
        if n in (2, 3):
            payload["grammar_text"] = grammar.get("content") or ""
            if n == 2:
                payload["show_shared"] = "grammar"
        if n == 4 and t.get("matching"):
            payload["matching"] = t["matching"]
            payload["ui"] = "matching"
        if n in (10, 11, 12, 13):
            payload["reading_text"] = reading.get("content") or ""
            if reading.get("author"):
                payload["reading_author"] = reading["author"]
            if n == 10:
                payload["show_shared"] = "reading"
        if n == 13 and t.get("options"):
            payload["essay_options"] = t["options"]
            payload["ui"] = "essay_choice"
            payload["reading_text"] = reading.get("content") or ""

        ans = t.get("correct_answer")
        answers[str(n)] = "" if ans is None else str(ans)
        statement = t.get("statement") or ""
        if n == 13 and not statement:
            statement = (
                "Выполните только ОДНО из заданий: 13.1, 13.2 или 13.3. "
                "Напишите сочинение-рассуждение. Объём — не менее 70 слов."
            )
        etalon_tasks.append(
            {
                "task_number": n,
                "part": 2 if n == 13 else 1,
                "type": "EXTENDED" if n == 13 else "SHORT_VALUE",
                "statement": statement,
                "payload": payload,
                "figure_svg": None,
                "figure_kind": None,
                "correct_answer": "",
                "max_score": int(t.get("max_score") or (7 if n == 13 else 1)),
                "topic": t.get("topic") or "",
                "acceptable_answers": t.get("acceptable_answers"),
                "template_solution": t.get("solution_hint"),
                "context_id": "etalon_oge_rus_var_kim",
            }
        )

    etalon = {
        "version": 1,
        "etalon": True,
        "kim_spec_id": "oge_rus_2026",
        "exam_code": "OGE",
        "subject_code": "russian",
        "variant_code": "oge_rus_var_kim",
        "provenance": {
            "source": "manual_teacher",
            "year": 2026,
            "variant_code": "oge_rus_var_kim",
            "kim_spec_id": "oge_rus_2026",
            "content_hash": "",
            "imported_at": None,
        },
        "context": {
            "context_id": "etalon_oge_rus_var_kim",
            "title": "Эталон · ОГЭ русский · var_kim",
            "description_text": (
                "<<<IZLOZHENIE>>>\n"
                + (listening.get("audio_script") or "")
                + "\n\n<<<GRAMMAR>>>\n"
                + (grammar.get("content") or "")
                + "\n\n<<<READING>>>\n"
                + (reading.get("author") or "")
                + "\n\n"
                + (reading.get("content") or "")
            ).strip(),
            "etalon": True,
            "listening_text": listening,
            "grammar_text": grammar,
            "reading_text": reading,
        },
        "tasks": etalon_tasks,
        "keys_file": "keys/oge_rus_var_kim.keys.json",
    }

    fix_dir = PACKS / "oge_rus" / "fixtures" / "etalon"
    keys_dir = fix_dir / "keys"
    keys_dir.mkdir(parents=True, exist_ok=True)
    (keys_dir / "oge_rus_var_kim.keys.json").write_text(
        json.dumps(
            {"variant_code": "oge_rus_var_kim", "answers": answers},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (fix_dir / "oge_rus_var_kim.etalon.json").write_text(
        json.dumps(etalon, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_math_etalon() -> None:
    demo_img = "assets/etalon/demo_01/q01.svg"
    asset_dir = PACKS / "oge_math" / "assets" / "etalon" / "demo_01"
    asset_dir.mkdir(parents=True, exist_ok=True)
    (asset_dir / "q01.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 80" class="fipi-fig">'
        '<rect x="10" y="10" width="100" height="60" fill="none" stroke="#222" stroke-width="2"/>'
        '<text x="60" y="45" text-anchor="middle" font-size="14">AB=12</text></svg>\n',
        encoding="utf-8",
    )

    math_tasks = []
    math_answers: dict[str, str] = {}
    for n in range(1, 26):
        part = 2 if n >= 20 else 1
        max_score = 2 if n >= 20 else 1
        ans = str(n) if part == 1 else f"решение-{n}"
        math_answers[str(n)] = ans
        payload: dict = {"image_urls": [], "media": [], "matching": None}
        fig_kind = None
        if n == 1:
            payload["image_urls"] = [demo_img]
            payload["media"] = [
                {"kind": "image", "path": demo_img, "alt": "Рисунок к заданию 1"}
            ]
            fig_kind = "asset"
        stmt = (
            f"Эталонное задание ОГЭ математика №{n}. Найдите значение. Ответ: {ans}."
            if part == 1
            else f"Эталонное задание ОГЭ математика №{n} (часть 2). Решите задачу."
        )
        math_tasks.append(
            {
                "task_number": n,
                "part": part,
                "type": "EXTENDED" if part == 2 else "SHORT_VALUE",
                "statement": stmt,
                "payload": payload,
                "figure_svg": None,
                "figure_kind": fig_kind,
                "correct_answer": "",
                "max_score": max_score,
                "topic": f"slot_{n}",
                "context_id": "etalon_oge_math_demo_01",
            }
        )

    math_etalon = {
        "version": 1,
        "etalon": True,
        "kim_spec_id": "oge_math_2026",
        "exam_code": "OGE",
        "subject_code": "math",
        "variant_code": "oge_math_demo_01",
        "provenance": {
            "source": "demo2026",
            "year": 2026,
            "variant_code": "oge_math_demo_01",
            "kim_spec_id": "oge_math_2026",
            "content_hash": "",
            "imported_at": None,
        },
        "context": {
            "context_id": "etalon_oge_math_demo_01",
            "title": "Эталон · ОГЭ математика · demo",
            "description_text": "Демонстрационный эталонный вариант (слоты 1–25).",
            "etalon": True,
        },
        "tasks": math_tasks,
        "keys_file": "keys/oge_math_demo_01.keys.json",
    }

    fix_dir = PACKS / "oge_math" / "fixtures" / "etalon"
    (fix_dir / "keys").mkdir(parents=True, exist_ok=True)
    (fix_dir / "keys" / "oge_math_demo_01.keys.json").write_text(
        json.dumps(
            {"variant_code": "oge_math_demo_01", "answers": math_answers},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (fix_dir / "oge_math_demo_01.etalon.json").write_text(
        json.dumps(math_etalon, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write_kim_specs()
    write_rus_etalon()
    write_math_etalon()
    print("etalon fixtures + kim_specs ready")


if __name__ == "__main__":
    main()
