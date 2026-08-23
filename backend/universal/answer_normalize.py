"""Нормализация ответов части 1 ОГЭ/ЕГЭ (краткий ответ).

Правила (школьный бланк):
  - запятая → точка (десятичные);
  - убрать пробелы;
  - унифицировать минус (типографский − / длинное тире → ASCII -);
  - trim + lower для текстовых ключей.
"""

from __future__ import annotations

from typing import Any
import re


def normalize_answer(value: Any) -> str:
    """Привести ответ ученика / ключ к сравнимому виду."""
    text = str(value or "").strip().lower()
    text = text.replace(",", ".")
    text = text.replace(" ", "")
    text = text.replace("\u00a0", "")  # nbsp
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = text.replace("∪", "u").replace("\\cup", "u")
    text = text.replace("∞", "inf")
    text = text.replace("+inf", "inf")
    text = text.replace("$", "")
    text = re.sub(r"^\[\[(-?\d+(?:\.\d+)?)\|(-?\d+(?:\.\d+)?)\]\]$", r"\1/\2", text)
    if len(text) == 1:
        text = text.translate(_CYR_LATIN)
    return text


_CYR_LATIN = str.maketrans(
    {
        "а": "a",
        "с": "c",
        "е": "e",
        "о": "o",
        "р": "p",
        "х": "x",
        "у": "y",
        "к": "k",
        "т": "t",
        "в": "b",
        "н": "h",
        "м": "m",
    }
)


def _as_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        pass
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)/(-?\d+(?:\.\d+)?)", str(value or ""))
    if not m:
        return None
    try:
        den = float(m.group(2))
        if den == 0:
            return None
        return float(m.group(1)) / den
    except (TypeError, ValueError):
        return None


def answers_equal(a: Any, b: Any, *, rtol: float = 1e-9, atol: float = 1e-6) -> bool:
    """Сравнить два ответа части 1 после нормализации.

    Сначала строковое равенство; если оба числа — мягкое float-сравнение.
    """
    na = normalize_answer(a)
    nb = normalize_answer(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    fa, fb = _as_float(na), _as_float(nb)
    if fa is None or fb is None:
        return False
    return abs(fa - fb) <= max(atol, rtol * max(abs(fa), abs(fb)))


def matches_any(student: Any, correct: Any, acceptable: list[Any] | None = None) -> bool:
    """Верно, если student совпадает с correct или любым из acceptable_answers."""
    keys: list[Any] = [correct]
    if acceptable:
        keys.extend(acceptable)
    return any(answers_equal(student, k) for k in keys if k is not None and str(k).strip())


def _digits_only(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def digits_any_order_equal(student: Any, correct: Any) -> bool:
    """ОГЭ русский 2/3/5/6/7/10/11: цифры в любом порядке (как в бланке)."""
    sa = normalize_answer(student)
    sb = normalize_answer(correct)
    da, db = _digits_only(sa), _digits_only(sb)
    if not da or not db:
        return False
    if da != sa.replace(".", "") or db != sb.replace(".", ""):
        return False
    return "".join(sorted(da)) == "".join(sorted(db))


def oge_rus_digits_any_order(question: dict[str, Any] | None) -> bool:
    """Типы с множественным выбором цифр — не соответствие (№4) и не слово (8/9/12)."""
    q = question if isinstance(question, dict) else {}
    p = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    if not p.get("oge_rus"):
        return False
    try:
        kim = int(p.get("kim_type") or q.get("num") or q.get("task_number") or 0)
    except (TypeError, ValueError):
        kim = 0
    return kim in (2, 3, 5, 6, 7, 10, 11)


if __name__ == "__main__":
    assert normalize_answer(" 3,5 ") == "3.5"
    assert normalize_answer("−2") == "-2"
    assert answers_equal("3,5", "3.5")
    assert answers_equal("15.4", "15,4")
    assert answers_equal("-2", "−2")
    assert not answers_equal("3,5", "3.6")
    assert matches_any("3412", "3412", ["3412"])
    assert digits_any_order_equal("351", "135")
    assert digits_any_order_equal("24", "42")
    assert not digits_any_order_equal("13", "135")
    assert oge_rus_digits_any_order({"num": 11, "payload": {"oge_rus": True, "kim_type": 11}})
    assert not oge_rus_digits_any_order({"num": 4, "payload": {"oge_rus": True, "kim_type": 4}})
    print("answer_normalize: OK")
