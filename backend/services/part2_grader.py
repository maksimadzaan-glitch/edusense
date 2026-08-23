"""Проверка развёрнутых заданий ОГЭ математики (№20–25) по критериям ФИПИ."""

from __future__ import annotations

import re
from typing import Any, Optional

FIPI_PART2: dict[int, dict[str, Any]] = {
    20: {
        "title": "№20 · уравнение / выражение",
        "max": 2,
        "criteria": [
            "2 балла: верное решение с обоснованием; ОДЗ указана и учтена, если есть дробь, корень, логарифм; получен верный ответ.",
            "1 балл: верный метод, но вычислительная ошибка ИЛИ потерян посторонний корень / не указаны ограничения (например x ≠ 3), при этом идея верна.",
            "0 баллов: решение не по задаче, только ответ без шагов, или грубая ошибка в методе.",
        ],
    },
    21: {
        "title": "№21 · текстовая задача",
        "max": 2,
        "criteria": [
            "2 балла: верная математическая модель и верный ответ с пояснением.",
            "1 балл: верная модель (уравнение/система), ошибка в вычислениях или не доведён ответ.",
            "0 баллов: неверная модель или решение отсутствует.",
        ],
    },
    22: {
        "title": "№22 · функция / график / исследование",
        "max": 2,
        "criteria": [
            "2 балла: верные шаги и ответ, область определения учтена.",
            "1 балл: верный ход с вычислительной ошибкой или неполнотой ОДЗ.",
            "0 баллов: ход не соответствует условию.",
        ],
    },
    23: {
        "title": "№23 · геометрия (вычисление)",
        "max": 2,
        "criteria": [
            "2 балла: верное решение с опорой на свойства фигур, верный ответ.",
            "1 балл: верный геометрический ход, ошибка в вычислении или неполное обоснование.",
            "0 баллов: неверная конфигурация или нет решения.",
        ],
    },
    24: {
        "title": "№24 · геометрия (доказательство / вычисление)",
        "max": 2,
        "criteria": [
            "2 балла: доказательство или вычисление с полным обоснованием.",
            "1 балл: идея верна, пропущено обоснование ключевого шага или арифметическая ошибка.",
            "0 баллов: доказательство не проведено / ход неверен.",
        ],
    },
    25: {
        "title": "№25 · геометрия повышенной сложности",
        "max": 2,
        "criteria": [
            "2 балла: полное обоснованное решение и верный ответ.",
            "1 балл: существенное продвижение (верная идея), решение не доведено или с ошибкой в конце.",
            "0 баллов: нет продвижения по задаче.",
        ],
    },
}


def fipi_rubric_for(task_num: int, extra: Optional[str] = None) -> str:
    spec = FIPI_PART2.get(int(task_num or 0)) or {
        "title": "Часть 2 · развёрнутый ответ",
        "max": 2,
        "criteria": [
            "2 балла: верное обоснованное решение и ответ.",
            "1 балл: верный ход с недочётом (ОДЗ, вычисление, обоснование).",
            "0 баллов: решение неверно или отсутствует.",
        ],
    }
    lines = [str(spec["title"]), f"Максимум: {spec['max']} балла."]
    lines.extend(str(c) for c in spec["criteria"])
    extra_s = str(extra or "").strip()
    if extra_s:
        lines.append("Дополнительно от учителя / варианта:")
        lines.append(extra_s)
    return "\n".join(lines)


def _norm(text: str) -> str:
    s = str(text or "").strip().lower().replace("ё", "е")
    s = s.replace(",", ".")
    s = re.sub(r"\s+", "", s)
    return s


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    s = str(value or "").strip().lower()
    return s in {"1", "true", "yes", "да", "ok", "ок"}


def _extract_answer_tail(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        return ""
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    tail = lines[-1] if lines else raw
    tail = re.sub(r"^(ответ[:\s]*)", "", tail, flags=re.I)
    return tail.strip()


MATH_GRADE_SYSTEM = """Ты эксперт ОГЭ математики (ФИПИ, 9 класс). Проверяешь ТОЛЬКО часть 2 (№20–25).

Сначала прочитай рукопись, потом поставь флаги. Балл выводи из флагов, не «на глаз».

Шкала ФИПИ (всегда 0 / 1 / 2):
- 2: верный метод, верные вычисления, верный ответ, обоснование достаточное; если в условии дробь/корень/лог — ОДЗ указана и учтена.
- 1: метод верный (модель/ход по задаче), но вычислительная ошибка, потерян корень, не указана ОДЗ, неполное обоснование ИЛИ ответ верный, а хода нет / ход обрывается.
- 0: неверная модель, решение не по условию, только ответ без шагов и без фото-хода, пусто, или фото не читается.

Жёсткие правила:
1. Не ставь 2 за один совпавший ответ без шагов.
2. Не ставь 0, если метод верный, а арифметика сломалась — это 1.
3. Эквивалентные формы ответа считай верными (2 и 2.0, 1/2 и 0.5, x=3 и 3, множество корней в любом порядке).
4. Зачёркнутое на фото игнорируй. Читай дроби, степени, знаки ≠.
5. Если фото неразборчиво и печатного текста нет — photo_unreadable=true, score=0, не выдумывай ход.
6. model_solution — эталон ЭТОЙ задачи (школьная запись + ОДЗ + ответ), не пересказ ученика.
7. Сочинения не пиши. Без markdown.

Верни ТОЛЬКО JSON:
{
  "transcript": "что прочитал с фото/текста",
  "final_answer_student": "краткий ответ ученика или пусто",
  "answers_equivalent": true,
  "method_ok": true,
  "arithmetic_ok": true,
  "odz_required": false,
  "odz_ok": true,
  "justification_ok": true,
  "photo_unreadable": false,
  "score": 0,
  "fipi_reason": "для учителя: что дало балл, ОДЗ/корни/модель",
  "student_feedback": "доброжелательно, что дописать",
  "model_solution": "полное решение"
}"""


def _score_math_from_checks(data: dict[str, Any], fallback_score: int) -> int:
    if _as_bool(data.get("photo_unreadable")) and not str(data.get("transcript") or "").strip():
        return 0
    method_ok = _as_bool(data.get("method_ok"))
    arith_ok = _as_bool(data.get("arithmetic_ok"))
    eq = _as_bool(data.get("answers_equivalent"))
    odz_required = _as_bool(data.get("odz_required"))
    odz_ok = _as_bool(data.get("odz_ok")) if odz_required else True
    just_ok = _as_bool(data.get("justification_ok"))
    if not method_ok and not eq:
        return 0
    if method_ok and arith_ok and eq and odz_ok and just_ok:
        return 2
    if method_ok or (eq and just_ok):
        return 1
    if eq and not method_ok:
        return 1
    try:
        raw = int(data.get("score"))
    except (TypeError, ValueError):
        raw = int(fallback_score)
    return 0 if raw not in (0, 1, 2) else raw


def heuristic_grade(
    *,
    task_text: str,
    student_answer: str,
    correct_solution: str,
    fipi_rubric: str,
    task_num: int = 0,
) -> dict[str, Any]:
    ans = str(student_answer or "").strip()
    key = str(correct_solution or "").strip()
    if not ans:
        return {
            "score": 0,
            "fipi_reason": "Решение не представлено — по критериям ФИПИ 0 баллов.",
            "student_feedback": "Запишите ход решения, не только ответ. Если есть дробь или корень — укажите ОДЗ.",
            "model_solution": str(correct_solution or "").strip()[:4000],
            "source": "heuristic",
        }
    key_tail = _extract_answer_tail(key)
    got_norm = _norm(ans)
    key_norm = _norm(key_tail)
    has_odz = bool(re.search(r"одз|x\s*≠|x\s*!=|знаменател|x\s*≠", ans, re.I))
    long_enough = len(ans) >= 60
    if key_norm and key_norm in got_norm:
        if long_enough and (has_odz or "одз" not in (fipi_rubric or "").lower()):
            reason = "Верный ответ и есть ход решения. Ограничения/ОДЗ выглядят учтёнными."
            score = 2
        else:
            reason = "Верный ответ, но по критериям ФИПИ не хватает полного обоснования или ОДЗ (например, ограничения на знаменатель)."
            score = 1
        return {
            "score": score,
            "fipi_reason": reason,
            "student_feedback": "Проверьте, что выписаны все шаги и ограничения (ОДЗ). Учитель может поставить 2 балла, если обоснование полное.",
            "model_solution": str(correct_solution or "").strip()[:4000],
            "source": "heuristic",
        }
    return {
        "score": 0,
        "fipi_reason": "Ответ не совпадает с эталоном; автоматическая сверка не увидела верный ход.",
        "student_feedback": "Сверьте шаги с критериями: модель, преобразования, ОДЗ, ответ. Учитель перечитает решение и может изменить балл.",
        "model_solution": str(correct_solution or "").strip()[:4000],
        "source": "heuristic",
    }


async def grade_part2_task(
    *,
    task_text: str,
    student_answer: str,
    correct_solution: str,
    fipi_rubric: Optional[str] = None,
    task_num: int = 0,
    photo_data_url: Optional[str] = None,
) -> dict[str, Any]:
    rubric = str(fipi_rubric or "").strip() or fipi_rubric_for(task_num)
    max_score = int((FIPI_PART2.get(int(task_num or 0)) or {}).get("max") or 2)
    photo = str(photo_data_url or "").strip()
    fallback = heuristic_grade(
        task_text=task_text,
        student_answer=student_answer,
        correct_solution=correct_solution,
        fipi_rubric=rubric,
        task_num=task_num,
    )
    if not str(student_answer or "").strip() and not photo:
        return fallback
    from backend.services.llm import LLMError, complete_json

    system = MATH_GRADE_SYSTEM
    photo_note = (
        "К решению приложено фото тетради. Сначала транскрибируй рукопись (формулы, ОДЗ, ответ), "
        "затем ставь флаги. Печатный текст ниже может быть пустым.\n"
        if photo
        else ""
    )
    user = (
        f"Номер КИМ: {task_num or '—'}\n"
        f"Максимум баллов: {max_score}\n"
        f"{photo_note}\n"
        f"Критерии ФИПИ по номеру:\n{rubric}\n\n"
        f"Условие:\n{str(task_text or '')[:4000]}\n\n"
        f"Эталон / верное решение:\n{str(correct_solution or '')[:4000] or '(нет эталона — оцени по условию и флагам)'}\n\n"
        f"Решение ученика (текст):\n{str(student_answer or '')[:4000] or '(только фото)'}\n"
    )
    try:
        data = await complete_json(
            system=system,
            user=user,
            temperature=0.0,
            image_data_url=photo or None,
        )
    except LLMError:
        if photo and not str(student_answer or "").strip():
            return {
                "score": 0,
                "fipi_reason": "Не удалось прочитать фото. Откройте снимок и поставьте балл вручную.",
                "student_feedback": "Учитель проверит решение по фото.",
                "model_solution": str(correct_solution or "").strip()[:4000],
                "source": "heuristic",
            }
        return fallback
    if not isinstance(data, dict):
        data = {}
    score = _score_math_from_checks(data, int(fallback["score"]))
    reason = str(data.get("fipi_reason") or fallback["fipi_reason"]).strip()[:800]
    flags = []
    if _as_bool(data.get("method_ok")):
        flags.append("метод верный")
    else:
        flags.append("метод неверный")
    if _as_bool(data.get("answers_equivalent")):
        flags.append("ответ совпал")
    if _as_bool(data.get("odz_required")):
        flags.append("ОДЗ нужна: " + ("учтена" if _as_bool(data.get("odz_ok")) else "нет"))
    if _as_bool(data.get("photo_unreadable")):
        flags.append("фото плохо читается")
    if flags:
        flag_line = "Чек-лист: " + "; ".join(flags) + "."
        if flag_line not in reason:
            reason = (reason + " " + flag_line).strip()[:800]
    feedback = str(data.get("student_feedback") or fallback["student_feedback"]).strip()[:800]
    solution = str(data.get("model_solution") or data.get("solution") or "").strip()[:4000]
    if not solution:
        solution = str(correct_solution or "").strip()[:4000]
    return {
        "score": score,
        "fipi_reason": reason,
        "student_feedback": feedback,
        "model_solution": solution,
        "source": "llm",
    }


async def write_math_solution(
    *,
    task_text: str,
    correct_solution: str = "",
    task_num: int = 0,
    photo_data_url: Optional[str] = None,
) -> dict[str, Any]:
    """Полное решение для учителя/разбора. Только математика, не во время экзамена."""
    from backend.services.llm import LLMError, complete_json

    spec = FIPI_PART2.get(int(task_num or 0)) or {}
    title = str(spec.get("title") or f"№{task_num or '—'}")
    system = (
        "Ты учитель ОГЭ математики. Пишешь полное решение для 9 класса. "
        "Только математика: ОДЗ, преобразования, обоснование, ответ. Не сочинение. "
        "Если в условии дробь, корень или логарифм — выпиши ОДЗ отдельной строкой. "
        "Верни ТОЛЬКО JSON: {\"solution\":\"...\",\"answer\":\"...\"}. "
        "solution — школьная запись. answer — короткий итог. Без markdown."
    )
    user = (
        f"{title}\n\n"
        f"Условие:\n{str(task_text or '')[:4000]}\n\n"
        f"Ключ / эталон, если есть:\n{str(correct_solution or '')[:2000] or '(нет)'}\n"
    )
    photo = str(photo_data_url or "").strip() or None
    try:
        data = await complete_json(
            system=system,
            user=user,
            temperature=0.2,
            image_data_url=photo,
        )
    except LLMError as exc:
        key = str(correct_solution or "").strip()
        if key:
            return {"solution": key, "answer": key.splitlines()[-1].strip(), "source": "key"}
        raise RuntimeError(str(exc)) from exc
    solution = str(data.get("solution") or "").strip()[:4000]
    answer = str(data.get("answer") or "").strip()[:400]
    if not solution:
        solution = str(correct_solution or "").strip()
    return {"solution": solution, "answer": answer, "source": "llm"}
