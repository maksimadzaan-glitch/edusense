"""Слоты заданий как в реальном КИМ — длины и типы по экзамену/предмету.

Документация целевых длин (ФИПИ-ориентир EduSense):
  ЕГЭ: profile_math=19, base_math=21, russian=27, informatics=27, physics=26,
       chemistry=34, biology=28, history=21, social=25, geography=29,
       literature=11, foreign=42
  ОГЭ: oge_math=25, russian=13, informatics=15, physics=25, chemistry=24,
       biology=26, history=24, social=24, geography=30, literature=5, foreign=34
  ВПР математика: 4–12 в зависимости от класса (у нас тренировочный блок 4)
"""

from __future__ import annotations

from backend.services.bank_keys import normalize_exam, normalize_subject_key

# (exam, subject_key) → полная длина КИМ
KIM_LENGTHS: dict[tuple[str, str], int] = {
    ("ege", "profile_math"): 19,
    ("ege", "base_math"): 21,
    ("ege", "russian"): 27,
    ("ege", "informatics"): 27,
    ("ege", "physics"): 26,
    ("ege", "chemistry"): 34,
    ("ege", "biology"): 28,
    ("ege", "history"): 21,
    ("ege", "social"): 25,
    ("ege", "geography"): 29,
    ("ege", "literature"): 11,
    ("ege", "foreign"): 42,
    ("oge", "oge_math"): 25,
    ("oge", "russian"): 13,
    ("oge", "informatics"): 15,
    ("oge", "physics"): 25,
    ("oge", "chemistry"): 24,
    ("oge", "biology"): 26,
    ("oge", "history"): 24,
    ("oge", "social"): 24,
    ("oge", "geography"): 30,
    ("oge", "literature"): 5,
    ("oge", "foreign"): 34,
    ("vpr", "vpr_math"): 4,
    ("vpr", "russian"): 8,
}

# граница part1|part2 (номер последнего задания части 1); None → всё part1
PART1_LAST: dict[tuple[str, str], int | None] = {
    ("ege", "profile_math"): 12,
    ("ege", "base_math"): 21,  # базовая — только краткие
    ("ege", "russian"): 26,
    ("ege", "informatics"): 27,
    ("ege", "physics"): 20,
    ("ege", "chemistry"): 28,
    ("ege", "biology"): 21,
    ("ege", "history"): 17,
    ("ege", "social"): 20,
    ("ege", "geography"): 27,
    ("ege", "literature"): 7,
    ("ege", "foreign"): 38,
    ("oge", "oge_math"): 19,
    ("oge", "russian"): 12,
    ("oge", "informatics"): 12,
    ("oge", "physics"): 19,
    ("oge", "chemistry"): 19,
    ("oge", "biology"): 21,
    ("oge", "history"): 20,
    ("oge", "social"): 20,
    ("oge", "geography"): 26,
    ("oge", "literature"): 3,
    ("oge", "foreign"): 30,
    ("vpr", "vpr_math"): 4,
}

# Краткие описания слотов для промптов (ключ → {slot: text})
_SLOT_SPECS: dict[tuple[str, str], dict[int, str]] = {
    ("ege", "profile_math"): {
        1: "простейшие уравнения/вычисления (целые, дроби, степени) — краткий ответ",
        2: "векторы / координаты / простейшая геометрия на плоскости",
        3: "планиметрия (треугольник, окружность, площадь) — figure_kind при необходимости",
        4: "теория вероятностей (выборка, монета, таблица)",
        5: "прикладная задача: проценты / движение / работа",
        6: "стереометрия (объём/площадь) — figure_kind=box3d|circle",
        7: "параметры / графики / чтение графика функции",
        8: "начала анализа: производная, касательная (краткий ответ)",
        9: "текстовая/прикладная задача / числа",
        10: "планиметрия сложнее / вписанные-описанные",
        11: "стереометрия / сечение",
        12: "задача с кратким ответом (уравнение, неравенство, исследование)",
        13: "уравнение (развёрнутый ответ) — part=2",
        14: "неравенство / система неравенств — part=2",
        15: "планиметрия с обоснованием — part=2",
        16: "стереометрия с обоснованием — part=2",
        17: "параметр / экстремум / производная — part=2",
        18: "система уравнений / числа — part=2",
        19: "экономическая / прикладная задача — part=2",
    },
    ("ege", "base_math"): {
        1: "арифметика / вычисления",
        2: "проценты / бытовые расчёты",
        3: "планиметрия: площади, периметры",
        4: "вероятность",
        5: "среднее / степени / текстовая",
        6: "графики и функции",
        7: "уравнения (линейные/квадратные)",
        8: "неравенства / числовая прямая",
        9: "геометрия: треугольники / Пифагор",
        10: "окружность / многоугольники",
        11: "стереометрия: объёмы куба/параллелепипеда",
        12: "проценты / скидки / вклад (проще)",
        13: "таблицы / диаграммы / данные",
        14: "движение / работа",
        15: "логика / выбор верного утверждения (числовой ответ)",
        16: "координатная плоскость / векторы (просто)",
        17: "преобразования выражений",
        18: "практическая геометрия (участок, комната)",
        19: "вероятность / комбинаторика (просто)",
        20: "функции: значение / нуль / график",
        21: "итоговая прикладная / комплексная краткая",
    },
    ("oge", "oge_math"): {
        1: "вычисления / дроби / степени",
        2: "уравнения",
        3: "планиметрия",
        4: "вероятность",
        5: "проценты / текстовые",
        6: "функции / графики",
        7: "геометрия / площади",
        8: "числа / прогрессии / НОД",
        9: "алгебраические выражения",
        10: "неравенства (краткий)",
        11: "треугольники / Пифагор",
        12: "окружность",
        13: "стереометрия (просто)",
        14: "координаты / график",
        15: "текстовая задача",
        16: "вероятность / статистика",
        17: "практическая геометрия",
        18: "системы (краткий ответ)",
        19: "итоговая краткая часть 1",
        20: "уравнение / система — part=2",
        21: "неравенство — part=2",
        22: "текстовая / экономическая — part=2",
        23: "планиметрия с обоснованием — part=2",
        24: "стереометрия / геометрия — part=2",
        25: "сложная алгебра / параметр (школьный) — part=2",
    },
}


def _keys(exam: str, subject: str) -> tuple[str, str]:
    return normalize_exam(exam), normalize_subject_key(exam, subject)


def kim_length(*, exam: str, subject: str) -> int:
    """Полная длина КИМ для exam+subject."""
    ex, sk = _keys(exam, subject)
    if (ex, sk) in KIM_LENGTHS:
        return KIM_LENGTHS[(ex, sk)]
    if ex == "ege":
        return 20
    if ex == "oge":
        return 15
    if ex == "vpr":
        return 8
    return 10


def part1_last(*, exam: str, subject: str) -> int:
    """Номер последнего задания части 1."""
    ex, sk = _keys(exam, subject)
    n = kim_length(exam=exam, subject=subject)
    if (ex, sk) in PART1_LAST:
        last = PART1_LAST[(ex, sk)]
        if last is None:
            return n
        return max(1, min(int(last), n))
    # эвристика: ~75% part1
    return max(1, (n * 3) // 4)


def kim_slots(*, exam: str, subject: str, count: int | None = None) -> list[int]:
    """Упорядоченные номера слотов КИМ (1..N), без циклического повтора."""
    full = kim_length(exam=exam, subject=subject)
    if count is None:
        n = full
    else:
        n = max(1, min(int(count or 1), full))
    return list(range(1, n + 1))


def slot_part(*, exam: str, subject: str, slot: int) -> int:
    ex, sk = _keys(exam, subject)
    # ОГЭ русский: изложение (1) и сочинение (13) — развёрнутый ответ
    if ex == "oge" and sk == "russian":
        return 2 if int(slot) in (1, 13) else 1
    return 1 if int(slot) <= part1_last(exam=exam, subject=subject) else 2


def slot_spec_line(*, exam: str, subject: str, slot: int) -> str:
    ex, sk = _keys(exam, subject)
    specs = _SLOT_SPECS.get((ex, sk), {})
    part = slot_part(exam=exam, subject=subject, slot=slot)
    if slot in specs:
        return f"{slot}) {specs[slot]}"
    return (
        f"{slot}) типичное задание КИМ «{subject}» ({exam}), "
        f"part={part} — {'краткий' if part == 1 else 'развёрнутый'} ответ"
    )


def blueprint_for(*, exam: str, subject: str, count: int, part1: int, part2: int) -> str:
    """Текст кодификатора/слотов для LLM-промпта."""
    ex, sk = _keys(exam, subject)
    slots = kim_slots(exam=exam, subject=subject, count=count)
    lines = [slot_spec_line(exam=exam, subject=subject, slot=s) for s in slots]

    if sk == "profile_math" and ex == "ege":
        header = "ПРОФИЛЬНАЯ МАТЕМАТИКА ЕГЭ — строго слоты КИМ:\n"
        footer = (
            "\npart=1: только краткий ответ (число/интервал). part=2: развёрнутый.\n"
            "ЗАПРЕЩЕНО: системы в \\begin{cases}, длинный LaTeX, задачи не из кодификатора ЕГЭ."
        )
        return header + "\n".join(lines) + footer

    if sk == "base_math" and ex == "ege":
        return (
            "БАЗОВАЯ МАТЕМАТИКА ЕГЭ — полный КИМ, краткие ответы:\n"
            + "\n".join(lines)
            + "\nБез параметров и без олимпиадной стереометрии."
        )

    if sk == "oge_math" and ex == "oge":
        return (
            "ОГЭ МАТЕМАТИКА — полный КИМ:\n"
            + "\n".join(lines)
            + "\nЧасть 1 — краткий ответ; часть 2 — с обоснованием."
        )

    if "informatics" in sk:
        return (
            "ИНФОРМАТИКА — слоты КИМ:\n"
            + "\n".join(lines)
            + "\nСистемы счисления, логика, алгоритмы, исполнители, массивы/строки, графы."
        )

    if sk == "russian":
        return (
            "РУССКИЙ ЯЗЫК — слоты КИМ:\n"
            + "\n".join(lines)
            + "\nОрфография, пунктуация, нормы, выразительные средства, текст."
        )

    return (
        f"Типичные задания кодификатора ФИПИ для «{subject}», экзамен {exam}.\n"
        + "\n".join(lines)
        + f"\nСначала part=1 (num ≤ {part1}), затем part=2. Разные темы, без однотипных шаблонов."
    )


def missing_slots_blueprint(*, exam: str, subject: str, slots: list[int]) -> str:
    """Промпт-фрагмент только для недостающих слотов."""
    lines = [slot_spec_line(exam=exam, subject=subject, slot=s) for s in slots]
    p1 = part1_last(exam=exam, subject=subject)
    return (
        f"Сгенерируй РОВНО {len(slots)} заданий строго для указанных номеров КИМ "
        f"(поле num = номер слота).\n"
        f"Экзамен: {exam}; предмет: {subject}.\n"
        f"part=1 если num≤{p1}, иначе part=2.\n"
        + "\n".join(lines)
    )
