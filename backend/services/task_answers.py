"""Нормализация и сравнение ответов универсального Task player.

Отдельно от backend.universal.answer_normalize (ОГЭ часть 1 / бланк).
"""

from __future__ import annotations

import re
from typing import Any

TASK_TYPES = frozenset(
    {
        "CHOICE_SINGLE",
        "CHOICE_MULTI",
        "MATCHING",
        "SHORT_VALUE",
        "FREE_RESPONSE",
    }
)

_SPACE_RE = re.compile(r"\s+")


def normalize_answer(s: Any, *, lower: bool = True) -> str:
    """Strip, collapse spaces; optionally lower. Preserve digit sequences like «134»."""
    text = str(s if s is not None else "").strip()
    text = text.replace("\u00a0", " ")
    text = _SPACE_RE.sub(" ", text)
    if lower:
        text = text.lower()
    return text


def _digits_only(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def _sorted_digits(s: str) -> str:
    return "".join(sorted(_digits_only(s)))


def answers_equal(user: Any, correct: Any, type: str) -> bool | None:
    """Сравнить ответ ученика с ключом по механике.

    FREE_RESPONSE — без автопроверки (None).
    CHOICE_MULTI — одни и те же цифры в любом порядке.
    Остальные — после normalize_answer.
    """
    t = str(type or "").strip().upper()
    if t == "FREE_RESPONSE":
        return None

    u = normalize_answer(user, lower=True)
    c = normalize_answer(correct, lower=True)
    if not c:
        return False

    if t == "CHOICE_MULTI":
        ud, cd = _sorted_digits(u), _sorted_digits(c)
        if not cd:
            return u == c
        return bool(ud) and ud == cd

    if t in ("CHOICE_SINGLE", "MATCHING", "SHORT_VALUE"):
        return u == c

    # неизвестный тип — мягкое сравнение после normalize
    return u == c


def score_answer(user: Any, correct: Any, type: str, max_score: int) -> tuple[bool | None, int]:
    """Вернуть (ok, score). Для FREE_RESPONSE: (None, 0)."""
    eq = answers_equal(user, correct, type)
    if eq is None:
        return None, 0
    ms = max(0, int(max_score or 0))
    return eq, (ms if eq else 0)


if __name__ == "__main__":
    assert normalize_answer("  A  B  ") == "a b"
    assert normalize_answer("134") == "134"
    assert answers_equal("134", "314", "CHOICE_MULTI") is True
    assert answers_equal("13", "134", "CHOICE_MULTI") is False
    assert answers_equal("2", "2", "CHOICE_SINGLE") is True
    assert answers_equal(" 3,5 ", "3,5", "SHORT_VALUE") is True
    assert answers_equal("ab", "ba", "MATCHING") is False
    assert answers_equal("anything", "x", "FREE_RESPONSE") is None
    print("task_answers: OK")
