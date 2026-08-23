"""ВПР · Математика."""

from __future__ import annotations

from backend.bank_data.ege_profile_math import _t

TASKS: list[dict] = [
    _t(1, "Вычислите: 48 : 6 + 5.", "13", difficulty="easy", topic="Арифметика"),
    _t(1, "Вычислите: 7 · 8 − 20.", "36", difficulty="easy", topic="Арифметика"),
    _t(2, "Найдите периметр квадрата со стороной 9.", "36", difficulty="easy", topic="Периметр", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(2, "Найдите площадь прямоугольника 5×6.", "30", difficulty="easy", topic="Площадь", section="planimetry", needs_figure=1, figure_kind="rect"),
    _t(3, "Сколько минут в 2 часах?", "120", difficulty="easy", topic="Единицы"),
    _t(3, "Сколько сантиметров в 3 метрах?", "300", difficulty="easy", topic="Единицы"),
    _t(4, "Найдите 10% от 90.", "9", difficulty="medium", topic="Проценты"),
    _t(4, "Число 40 увеличили на 25%. Найдите результат.", "50", difficulty="medium", topic="Проценты"),
]
