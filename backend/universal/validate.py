"""Валидация JSON-ответа LLM для universal-варианта."""

from __future__ import annotations

from typing import Any


class VariantValidationError(ValueError):
    pass


def validate_variant_payload(
    data: Any,
    *,
    subject_code: str,
    exam_code: str,
    expected_slots: list[tuple[int, int, str]],
) -> dict[str, Any]:
    """expected_slots: список (task_number, part, prototype_title)."""
    if not isinstance(data, dict):
        raise VariantValidationError("Ответ LLM должен быть JSON-объектом")

    if str(data.get("subject_code") or "") != subject_code:
        raise VariantValidationError(
            f"subject_code: ожидалось {subject_code!r}, получено {data.get('subject_code')!r}"
        )
    if str(data.get("exam_code") or "") != exam_code:
        raise VariantValidationError(
            f"exam_code: ожидалось {exam_code!r}, получено {data.get('exam_code')!r}"
        )

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        raise VariantValidationError("Поле tasks должно быть массивом")

    expected_numbers = [n for n, _, _ in expected_slots]
    if len(tasks) != len(expected_slots):
        raise VariantValidationError(
            f"Ожидалось {len(expected_slots)} заданий, получено {len(tasks)}"
        )

    by_num: dict[int, dict[str, Any]] = {}
    for raw in tasks:
        if not isinstance(raw, dict):
            raise VariantValidationError("Каждый элемент tasks должен быть объектом")
        try:
            num = int(raw.get("task_number"))
        except (TypeError, ValueError) as exc:
            raise VariantValidationError("task_number должен быть целым числом") from exc
        if num in by_num:
            raise VariantValidationError(f"Дублируется task_number={num}")
        by_num[num] = raw

    missing = [n for n in expected_numbers if n not in by_num]
    if missing:
        raise VariantValidationError(f"Нет заданий с номерами: {missing}")

    normalized: list[dict[str, Any]] = []
    for num, part, title in expected_slots:
        t = by_num[num]
        try:
            got_part = int(t.get("part"))
        except (TypeError, ValueError) as exc:
            raise VariantValidationError(f"Задание {num}: part должен быть 1 или 2") from exc
        if got_part not in (1, 2):
            raise VariantValidationError(f"Задание {num}: part должен быть 1 или 2")
        if got_part != part:
            # мягко принимаем part из прототипа
            got_part = part

        text = str(t.get("text") or "").strip()
        answer = str(t.get("answer") or "").strip()
        solution_raw = t.get("solution")
        if solution_raw is None or solution_raw == "":
            solution: str | None = None
        else:
            solution = str(solution_raw).strip() or None

        pl = t.get("payload") if isinstance(t.get("payload"), dict) else {}
        is_etalon = bool(t.get("etalon")) or bool(pl.get("etalon"))

        if not text:
            raise VariantValidationError(f"Задание {num}: пустой text")
        # Эталон part2 (изложение/сочинение): ключ = критерии, пустая строка допустима
        if not answer and not (is_etalon and got_part == 2):
            raise VariantValidationError(f"Задание {num}: пустой answer")
        if is_etalon and got_part == 2 and not answer:
            answer = ""  # критерии в UI / manual grading

        if got_part == 2:
            if not solution and not is_etalon:
                raise VariantValidationError(
                    f"Задание {num} (часть 2): solution обязателен и не может быть пустым"
                )
            if is_etalon and not solution:
                solution = None
        else:
            # part 1 — solution может быть null
            solution = solution  # keep if model provided, else None is fine

        proto_title = str(t.get("prototype_title") or title).strip() or title
        row: dict[str, Any] = {
            "task_number": num,
            "part": got_part,
            "prototype_title": proto_title,
            "text": text,
            "answer": answer,
            "solution": solution,
        }
        fk = t.get("figure_kind")
        if fk:
            row["figure_kind"] = str(fk).strip() or None
        fp = t.get("figure_params")
        if fp is not None and fp != "":
            row["figure_params"] = fp
        fd = t.get("figure_data")
        if fd is not None and fd != "":
            row["figure_data"] = fd
        fsvg = t.get("figure_svg")
        if isinstance(fsvg, str) and fsvg.strip():
            row["figure_svg"] = fsvg.strip()
        fpack = t.get("_figure_pack")
        if fpack:
            row["_figure_pack"] = str(fpack).strip()
        cid = t.get("context_id")
        if cid:
            row["context_id"] = str(cid).strip()
        ms = t.get("max_score")
        if ms is not None and str(ms).strip() != "":
            try:
                row["max_score"] = int(ms)
            except (TypeError, ValueError):
                pass
        # ОГЭ русский: listening/grammar/reading/matching/essay в payload
        pl = t.get("payload")
        if isinstance(pl, dict) and pl:
            row["payload"] = pl
        normalized.append(row)

    return {
        "subject_code": subject_code,
        "exam_code": exam_code,
        "tasks": normalized,
    }
