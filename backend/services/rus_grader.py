"""Проверка изложения (№1) и сочинения (№13) ОГЭ русский по критериям ФИПИ."""

from __future__ import annotations

import re
from typing import Any, Optional

from backend.services.llm import LLMError, complete_json

IZLO_MAX = 7
SOCH_MAX = 7
LIT_MAX = 8


def _clamp_int(value: Any, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = lo
    return max(lo, min(hi, n))


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-zА-Яа-яЁё0-9\-]+", str(text or "")))


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    s = str(value or "").strip().lower()
    return s in {"1", "true", "yes", "да"}


def _list_of_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _literacy_band(errors: int) -> int:
    """ОГЭ ФИПИ, ГК: 0 ошибок = 2, 1–2 = 1, 3+ = 0."""
    n = max(0, int(errors))
    if n <= 0:
        return 2
    if n <= 2:
        return 1
    return 0


IZLO_SYSTEM = """Ты эксперт ОГЭ по русскому языку (ФИПИ). Проверяешь СЖАТОЕ ИЗЛОЖЕНИЕ, задание 1.

Сначала выпиши 3 микротемы исходного текста, потом сверь работу ученика. Баллы считай по правилам, не «на глаз».

ИК1 содержание (0–2):
- 2: переданы все микротемы исходника
- 1: пропущена или добавлена ровно одна микротема
- 0: пропущено/добавлено больше одной

ИК2 сжатие (0–3):
- 3: в каждой микротеме есть приём сжатия (обобщение, исключение, упрощение)
- 2: приёмы сжатия в двух микротемах
- 1: приём сжатия в одной микротеме
- 0: сжатия нет (переписано почти дословно или оборвано)

ИК3 цельность и связность (0–2):
- 2: нет логических ошибок, абзацы уместны
- 1: одна логическая ошибка и/или одно нарушение абзацного членения
- 0: две и более логические ошибки

Жёстко:
- Если меньше 70 слов — ИК1=ИК2=ИК3=0.
- Грамотность (ГК) сюда не включай.
- Если фото — сначала транскрибируй рукопись, зачёркнутое игнорируй.
- Не пиши изложение за ученика.

Верни ТОЛЬКО JSON:
{
  "transcript": "текст ученика как прочитан",
  "word_count": 0,
  "source_microthemes": ["...", "...", "..."],
  "kept_microthemes": ["..."],
  "missed_microthemes": ["..."],
  "added_microthemes": ["..."],
  "compressed_microtheme_count": 0,
  "logic_errors": 0,
  "ik1": 0, "ik2": 0, "ik3": 0,
  "fipi_reason": "для учителя: какие микротемы потеряны, сжатие",
  "student_feedback": "доброжелательно, что дописать"
}"""


SOCH_SYSTEM = """Ты эксперт ОГЭ по русскому языку (ФИПИ). Проверяешь СОЧИНЕНИЕ 13.1 / 13.2 / 13.3.

Сначала определи тип (13.1 тезис лингвиста, 13.2 фрагмент, 13.3 понятие). Потом критерии содержания. Грамотность не ставь.

СК1 тезис / понимание (0–2):
- 2: есть понятный ответ на задание, ученик понял формулировку
- 1: тезис есть, но неточный / уходит в сторону
- 0: нет тезиса или работа не по заданию

СК2 примеры-аргументы (0–3):
- 3: два уместных примера с пояснением (для 13.2 — из прочитанного текста; для 13.3 — один из текста и один из жизни/литературы допустим)
- 2: два примера, но один без пояснения, ИЛИ один полный пример с пояснением
- 1: примеры названы, но без пояснения / слабо связаны с тезисом
- 0: примеров нет, или сплошной пересказ текста без аргумента

СК3 цельность и композиция (0–2):
- 2: вступление — тезис — примеры — вывод, нет логических разрывов
- 1: одна логическая или композиционная ошибка
- 0: две и более, набор предложений без связи

Жёстко:
- Меньше 70 слов — СК1=СК2=СК3=0.
- Полностью переписанный исходный текст без комментария — все 0.
- Не пиши сочинение за ученика. Если фото — транскрибируй рукопись.

Верни ТОЛЬКО JSON:
{
  "transcript": "...",
  "word_count": 0,
  "task_type": "13.1",
  "has_thesis": true,
  "examples_with_comment": 0,
  "examples_without_comment": 0,
  "rewritten_source_only": false,
  "logic_errors": 0,
  "sk1": 0, "sk2": 0, "sk3": 0,
  "fipi_reason": "для учителя",
  "student_feedback": "доброжелательно"
}"""


LIT_SYSTEM = """Ты эксперт ОГЭ по русскому. Считай ОШИБКИ в изложении и сочинении суммарно. Не ставь баллы сам — только счётчики.

Считай по нормам ОГЭ: однотипные ошибки в одном слове — одна; не путай орфографию и пунктуацию.
Фактические ошибки (ФК1) — искажение имён, событий, смысла исходника.

Верни ТОЛЬКО JSON:
{
  "orth_errors": 0,
  "punct_errors": 0,
  "gram_errors": 0,
  "speech_errors": 0,
  "fact_errors": 0,
  "fipi_reason": "кратко: какие типы ошибок преобладают, 1–2 примера"
}"""


def _score_izlo(data: dict[str, Any], words: int) -> tuple[int, int, int]:
    if words < 70:
        return 0, 0, 0
    missed = _list_of_str(data.get("missed_microthemes"))
    added = _list_of_str(data.get("added_microthemes"))
    source = _list_of_str(data.get("source_microthemes"))
    kept = _list_of_str(data.get("kept_microthemes"))
    drift = len(missed) + len(added)
    if source and kept:
        drift = max(drift, max(0, len(source) - len(kept)) + len(added))
    if drift <= 0:
        ik1 = 2
    elif drift == 1:
        ik1 = 1
    else:
        ik1 = 0
    try:
        compressed = int(data.get("compressed_microtheme_count"))
    except (TypeError, ValueError):
        compressed = _clamp_int(data.get("ik2"), 0, 3)
    ik2 = 3 if compressed >= 3 else 2 if compressed == 2 else 1 if compressed == 1 else 0
    try:
        logic = int(data.get("logic_errors"))
    except (TypeError, ValueError):
        logic = 0
    ik3 = 2 if logic <= 0 else 1 if logic == 1 else 0
    return ik1, ik2, ik3


def _score_soch(data: dict[str, Any], words: int) -> tuple[int, int, int]:
    if words < 70 or _as_bool(data.get("rewritten_source_only")):
        return 0, 0, 0
    has_thesis = _as_bool(data.get("has_thesis"))
    try:
        with_c = int(data.get("examples_with_comment") or 0)
    except (TypeError, ValueError):
        with_c = 0
    try:
        without = int(data.get("examples_without_comment") or 0)
    except (TypeError, ValueError):
        without = 0
    if not has_thesis:
        sk1 = 0
    else:
        sk1 = _clamp_int(data.get("sk1"), 1, 2)
    if with_c >= 2:
        sk2 = 3
    elif with_c == 1 and without >= 1:
        sk2 = 2
    elif with_c == 1:
        sk2 = 2
    elif without >= 1:
        sk2 = 1
    else:
        sk2 = 0
    try:
        logic = int(data.get("logic_errors") or 0)
    except (TypeError, ValueError):
        logic = 0
    sk3 = 2 if logic <= 0 else 1 if logic == 1 else 0
    if sk1 == 0 and with_c == 0:
        return 0, 0, sk3 if words >= 70 else 0
    return sk1, sk2, sk3


def payload_source(q: dict[str, Any], *keys: str) -> str:
    pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
    for key in keys:
        val = pl.get(key) or q.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, dict):
            inner = (
                val.get("text")
                or val.get("script")
                or val.get("audio_script")
                or val.get("body")
                or ""
            )
            if str(inner).strip():
                return str(inner).strip()
    return ""


_payload_source = payload_source


async def grade_izlozhenie(
    *,
    task_text: str,
    source_text: str,
    student_answer: str,
    photo_data_url: Optional[str] = None,
) -> dict[str, Any]:
    photo = str(photo_data_url or "").strip()
    work = str(student_answer or "").strip()
    words = _word_count(work)
    if not work and not photo:
        return {
            "score": 0,
            "max_score": IZLO_MAX,
            "criteria": {"ik1": 0, "ik2": 0, "ik3": 0},
            "fipi_reason": "Изложение не представлено.",
            "student_feedback": "Напишите сжатое изложение не менее 70 слов.",
            "source": "heuristic",
        }
    system = IZLO_SYSTEM
    user = (
        f"Слов в работе (считай по этому числу, не пересчитывай сам): {words}\n\n"
        f"Инструкция задания:\n{str(task_text or '')[:2500]}\n\n"
        f"Исходный текст для изложения:\n{str(source_text or '')[:5000] or '(не передан — восстанови микротемы из работы осторожно)'}\n\n"
        f"Работа ученика:\n{work[:6000] or '(только фото)'}\n"
    )
    try:
        data = await complete_json(
            system=system, user=user, temperature=0.0, image_data_url=photo or None
        )
    except LLMError:
        return {
            "score": 0,
            "max_score": IZLO_MAX,
            "criteria": {"ik1": 0, "ik2": 0, "ik3": 0},
            "fipi_reason": "Не удалось проверить изложение автоматически.",
            "student_feedback": "Учитель проверит работу вручную.",
            "source": "heuristic",
        }
    if not isinstance(data, dict):
        data = {}
    transcript = str(data.get("transcript") or "").strip()
    if not work and transcript:
        words = _word_count(transcript)
    ik1, ik2, ik3 = _score_izlo(data, words)
    reason = str(data.get("fipi_reason") or "").strip()[:800]
    missed = _list_of_str(data.get("missed_microthemes"))
    if missed and "микротем" not in reason.lower():
        reason = (reason + " Пропущены: " + "; ".join(missed[:3]) + ".").strip()[:800]
    if words < 70:
        reason = (f"Меньше 70 слов ({words}) — ИК1–ИК3 = 0. " + reason).strip()[:800]
    return {
        "score": ik1 + ik2 + ik3,
        "max_score": IZLO_MAX,
        "criteria": {"ik1": ik1, "ik2": ik2, "ik3": ik3},
        "fipi_reason": reason,
        "student_feedback": str(data.get("student_feedback") or "")[:800],
        "source": "llm",
    }


async def grade_sochinenie(
    *,
    task_text: str,
    source_text: str,
    student_answer: str,
    photo_data_url: Optional[str] = None,
) -> dict[str, Any]:
    photo = str(photo_data_url or "").strip()
    work = str(student_answer or "").strip()
    words = _word_count(work)
    if not work and not photo:
        return {
            "score": 0,
            "max_score": SOCH_MAX,
            "criteria": {"sk1": 0, "sk2": 0, "sk3": 0},
            "fipi_reason": "Сочинение не представлено.",
            "student_feedback": "Напишите сочинение-рассуждение не менее 70 слов, с двумя примерами из текста.",
            "source": "heuristic",
        }
    system = SOCH_SYSTEM
    user = (
        f"Слов в работе (считай по этому числу): {words}\n\n"
        f"Задание:\n{str(task_text or '')[:3500]}\n\n"
        f"Текст для примеров:\n{str(source_text or '')[:5000] or '(не передан)'}\n\n"
        f"Сочинение ученика:\n{work[:8000] or '(только фото)'}\n"
    )
    try:
        data = await complete_json(
            system=system, user=user, temperature=0.0, image_data_url=photo or None
        )
    except LLMError:
        return {
            "score": 0,
            "max_score": SOCH_MAX,
            "criteria": {"sk1": 0, "sk2": 0, "sk3": 0},
            "fipi_reason": "Не удалось проверить сочинение автоматически.",
            "student_feedback": "Учитель проверит работу вручную.",
            "source": "heuristic",
        }
    if not isinstance(data, dict):
        data = {}
    transcript = str(data.get("transcript") or work).strip()
    if transcript and not work:
        words = _word_count(transcript)
    sk1, sk2, sk3 = _score_soch(data, words)
    reason = str(data.get("fipi_reason") or "").strip()[:800]
    if words < 70:
        reason = (f"Меньше 70 слов ({words}) — СК1–СК3 = 0. " + reason).strip()[:800]
    return {
        "score": sk1 + sk2 + sk3,
        "max_score": SOCH_MAX,
        "criteria": {"sk1": sk1, "sk2": sk2, "sk3": sk3},
        "fipi_reason": reason,
        "student_feedback": str(data.get("student_feedback") or "")[:800],
        "source": "llm",
    }


async def grade_literacy(
    *,
    izlo_text: str,
    soch_text: str,
) -> dict[str, Any]:
    """ГК1–ГК4 и ФК1 по обеим развёрнутым работам, 0–8."""
    blob = (str(izlo_text or "") + "\n\n" + str(soch_text or "")).strip()
    if len(blob) < 40:
        return {
            "gk1": 0,
            "gk2": 0,
            "gk3": 0,
            "gk4": 0,
            "fk1": 0,
            "literacy_score": 0,
            "fipi_reason": "Мало текста для оценки грамотности.",
            "source": "heuristic",
        }
    system = LIT_SYSTEM
    user = f"Тексты ученика (изложение + сочинение):\n{blob[:12000]}"
    try:
        data = await complete_json(system=system, user=user, temperature=0.0)
    except LLMError:
        return {
            "gk1": 0,
            "gk2": 0,
            "gk3": 0,
            "gk4": 0,
            "fk1": 0,
            "literacy_score": None,
            "fipi_reason": "Грамотность не выставлена автоматически.",
            "source": "heuristic",
        }
    if not isinstance(data, dict):
        data = {}

    def _err(key: str) -> int:
        try:
            return max(0, int(data.get(key) or 0))
        except (TypeError, ValueError):
            return 0

    gk1 = _literacy_band(_err("orth_errors"))
    gk2 = _literacy_band(_err("punct_errors"))
    gk3 = _literacy_band(_err("gram_errors"))
    gk4 = _literacy_band(_err("speech_errors"))
    fact = _err("fact_errors")
    fk1 = 2 if fact <= 0 else 1 if fact == 1 else 0
    total = gk1 + gk2 + gk3 + gk4
    reason = str(data.get("fipi_reason") or "").strip()[:800]
    counts = (
        f"Счёт: орф. {_err('orth_errors')}, пункт. {_err('punct_errors')}, "
        f"грамм. {_err('gram_errors')}, речь {_err('speech_errors')} "
        f"(ГК {total}/8; ФК1 {fk1})."
    )
    if counts not in reason:
        reason = (reason + " " + counts).strip()[:800]
    return {
        "gk1": gk1,
        "gk2": gk2,
        "gk3": gk3,
        "gk4": gk4,
        "fk1": fk1,
        "literacy_score": min(LIT_MAX, total),
        "fipi_reason": reason,
        "source": "llm",
    }
