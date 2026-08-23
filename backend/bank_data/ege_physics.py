"""ЕГЭ · Физика — скелет банка (слоты КИМ 1–26; ранние слоты с примерами)."""

from __future__ import annotations

from backend.bank_data.ege_profile_math import _t

TASKS: list[dict] = [
    _t(1, "Тело движется равномерно со скоростью 5 м/с. Какой путь (в метрах) оно пройдёт за 4 с?", "20", difficulty="easy", topic="Кинематика", section="algebra"),
    _t(1, "Автомобиль проехал 90 км за 1,5 ч. Найдите среднюю скорость в км/ч.", "60", difficulty="easy", topic="Кинематика", section="algebra"),
    _t(2, "Сила 10 Н сообщает телу ускорение 2 м/с². Найдите массу тела в кг.", "5", difficulty="medium", topic="Динамика", section="algebra"),
    _t(2, "Тело массой 2 кг движется с ускорением 3 м/с². Найдите равнодействующую силу в Н.", "6", difficulty="easy", topic="Динамика", section="algebra"),
    _t(3, "Потенциальная энергия тела массой 2 кг на высоте 5 м равна… (g = 10 м/с²). Ответ в джоулях.", "100", difficulty="medium", topic="Энергия", section="algebra"),
    _t(4, "Сила тока 2 А, напряжение 12 В. Найдите сопротивление участка цепи в омах.", "6", difficulty="easy", topic="Электричество", section="algebra"),
]
