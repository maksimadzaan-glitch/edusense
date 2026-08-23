"""ЕГЭ · Химия — скелет банка (слоты КИМ 1–34; ранние слоты с примерами)."""

from __future__ import annotations

from backend.bank_data.ege_profile_math import _t

TASKS: list[dict] = [
    _t(1, "Сколько электронов в атоме натрия (Na, Z = 11)?", "11", difficulty="easy", topic="Строение атома", section="algebra"),
    _t(1, "Сколько протонов в ядре атома углерода (C, Z = 6)?", "6", difficulty="easy", topic="Строение атома", section="algebra"),
    _t(2, "Относительная атомная масса кислорода равна 16. Чему равна молярная масса O₂ (г/моль)?", "32", difficulty="easy", topic="Количество вещества", section="algebra"),
    _t(3, "В реакции 2H₂ + O₂ → 2H₂O сколько молекул воды образуется из 2 молекул водорода?", "2", difficulty="medium", topic="Реакции", section="algebra"),
    _t(4, "Валентность кислорода в воде H₂O равна…", "2", difficulty="easy", topic="Валентность", section="algebra"),
]
