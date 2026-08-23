"""ЕГЭ · Биология — скелет банка (слоты КИМ 1–28; ранние слоты с примерами)."""

from __future__ import annotations

from backend.bank_data.ege_profile_math import _t

TASKS: list[dict] = [
    _t(1, "Сколько хромосом в соматической клетке человека (диплоидный набор)?", "46", difficulty="easy", topic="Цитология", section="algebra"),
    _t(1, "Сколько хромосом в гамете человека?", "23", difficulty="easy", topic="Цитология", section="algebra"),
    _t(2, "Основной источник энергии в клетке — молекула… (в ответе укажите аббревиатуру из 3 букв).", "АТФ", difficulty="easy", topic="Биохимия", section="algebra"),
    _t(3, "Органоид, в котором происходит фотосинтез, называется… (одно слово).", "хлоропласт", difficulty="medium", topic="Клетка", section="algebra"),
    _t(4, "Какой газ выделяют растения на свету при фотосинтезе? (формула из 2 символов).", "O2", difficulty="easy", topic="Фотосинтез", section="algebra"),
]
