"""Маппинг teacher UI (exam_type + русское имя предмета) → universal codes.

Universal: subject_code (math, math_base, russian, …) + exam_code (EGE, OGE, VPR_8).
"""

from __future__ import annotations

from backend.services.bank_keys import normalize_exam


def map_teacher_to_universal(exam: str, subject: str) -> tuple[str, str] | None:
    """Вернуть (subject_code, exam_code) или None, если пары нет в universal."""
    ex = normalize_exam(exam)
    s = (subject or "").strip().lower()
    if not s:
        return None

    if ex == "ege":
        exam_code = "EGE"
    elif ex == "oge":
        exam_code = "OGE"
    elif ex == "vpr":
        exam_code = "VPR_8"
    else:
        return None

    # коды universal / английские алиасы (russian, math, …)
    code_aliases = {
        "russian": "russian",
        "rus": "russian",
        "ru": "russian",
        "math": "math",
        "mathematics": "math",
        "math_base": "math_base",
        "physics": "physics",
        "social": "social",
        "biology": "biology",
        "history": "history",
        "informatics": "informatics",
        "chemistry": "chemistry",
        "geography": "geography",
        "literature": "literature",
    }
    if s in code_aliases:
        return code_aliases[s], exam_code

    # математика — отдельно базовая / профильная / огэ / впр
    if "матем" in s:
        if ex == "ege" and "базов" in s:
            return "math_base", exam_code
        # Профильная математика, Математика (не базовая)
        return "math", exam_code
    # «ЕГЭ Профильная» / «Профильная» без слова «математика»
    if ex == "ege" and "профильн" in s and "базов" not in s:
        return "math", exam_code

    if "рус" in s or "russian" in s:
        return "russian", exam_code
    if "физик" in s:
        return "physics", exam_code
    if "обществ" in s:
        return "social", exam_code
    if "биол" in s:
        return "biology", exam_code
    if "истор" in s:
        return "history", exam_code
    if "информ" in s:
        return "informatics", exam_code
    if "хими" in s:
        return "chemistry", exam_code
    if "геог" in s:
        return "geography", exam_code
    if "литерат" in s:
        return "literature", exam_code

    return None
