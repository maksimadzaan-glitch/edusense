"""Нормализация exam/subject → ключи банка."""

from __future__ import annotations


def normalize_exam(exam: str) -> str:
    e = (exam or "").strip().lower()
    if e in {"ege", "егэ", "еге"}:
        return "ege"
    if e in {"oge", "огэ", "оге"}:
        return "oge"
    if e in {"vpr", "впр"}:
        return "vpr"
    return "school"


def normalize_subject_key(exam: str, subject: str) -> str:
    s = (subject or "").strip().lower()
    ex = normalize_exam(exam)

    if "информ" in s:
        return "informatics"
    if "рус" in s:
        return "russian"
    if "физик" in s:
        return "physics"
    if "хими" in s:
        return "chemistry"
    if "биол" in s:
        return "biology"
    if "истор" in s:
        return "history"
    if "обществ" in s:
        return "social"
    if "геог" in s:
        return "geography"
    if "литерат" in s:
        return "literature"
    if "иностр" in s or "англий" in s or "немец" in s or "француз" in s or "испан" in s:
        return "foreign"

    if "матем" in s or s in {"математика"}:
        if ex == "ege" and "базов" in s:
            return "base_math"
        if ex == "ege":
            return "profile_math"  # профильная по умолчанию
        if ex == "oge":
            return "oge_math"
        if ex == "vpr":
            return "vpr_math"
        return "school_math"

    return "other"
