"""ЕГЭ · Информатика — скелет банка (полный КИМ 27; ранние слоты с примерами)."""

from __future__ import annotations

from backend.bank_data.ege_profile_math import _t

TASKS: list[dict] = [
    _t(1, "Сколько единиц в двоичной записи числа 13?", "3", difficulty="easy", topic="Системы счисления", section="algebra"),
    _t(1, "Переведите число 1011₂ в десятичную систему.", "11", difficulty="easy", topic="Системы счисления", section="algebra"),
    _t(1, "Сколько единиц в двоичной записи числа 15?", "4", difficulty="easy", topic="Системы счисления", section="algebra"),
    _t(2, "Сколько различных строк длины 3 можно составить из символов A и B (буквы могут повторяться)?", "8", difficulty="medium", topic="Комбинаторика", section="algebra"),
    _t(2, "Вычислите значение выражения (в десятичной системе): 1·2³ + 0·2² + 1·2¹ + 1·2⁰.", "11", difficulty="easy", topic="Системы счисления", section="algebra"),
    _t(2, "Сколько различных чисел можно записать тремя битами?", "8", difficulty="easy", topic="Кодирование", section="algebra"),
    _t(3, "Для логического выражения A ∧ ¬A значение всегда равно… (0 или 1).", "0", difficulty="easy", topic="Логика", section="algebra"),
    _t(3, "Сколько различных значений может принимать бит?", "2", difficulty="easy", topic="Кодирование", section="algebra"),
    _t(3, "Чему равно A ∨ 1 для любого A (0 или 1)?", "1", difficulty="easy", topic="Логика", section="algebra"),
    _t(4, "Файл занимает 2 Кбайт. Сколько это байт?", "2048", difficulty="medium", topic="Информация", section="algebra"),
    _t(4, "Сколько бит в 1 байте?", "8", difficulty="easy", topic="Информация", section="algebra"),
    _t(4, "Сколько байт в 1 Кбайте (двоичная система, 2¹⁰)?", "1024", difficulty="easy", topic="Информация", section="algebra"),
    _t(5, "Исполнитель увеличивает число на 1 или умножает на 2. Из 1 получить 10. Каково наименьшее число команд?", "5", difficulty="hard", topic="Алгоритмы", section="algebra"),
    _t(6, "В массиве из 5 элементов записаны числа 3, 1, 4, 1, 5. Чему равна сумма элементов?", "14", difficulty="easy", topic="Массивы", section="algebra"),
]
