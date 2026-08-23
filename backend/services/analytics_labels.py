"""Русские подписи тем/типов для аналитики (ОГЭ русский, математика)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional

# kim_type / topic slug → короткое русское название
TOPIC_LABELS_RU: dict[str, str] = {
    "summary_writing": "Сжатое изложение",
    "syntax_basis": "Грамматическая основа",
    "syntax_analysis_basis": "Грамматическая основа",
    "syntax_analysis": "Синтаксический анализ",
    "syntax_characteristics": "Синтаксический анализ",
    "punctuation_matching": "Пунктуация: соответствие",
    "punctuation_analysis": "Пунктуационный анализ",
    "punctuation_placement": "Знаки препинания",
    "punctuation_dash": "Тире",
    "punctuation_commas": "Запятые",
    "punctuation_spp": "Запятые в СПП",
    "spelling_explanation": "Орфография: объяснение",
    "spelling_letters": "Орфография: вставка букв",
    "grammar_form": "Грамматические нормы",
    "grammar_forms": "Грамматические нормы",
    "phrase_transformation": "Словосочетание",
    "syntax_phrase_transform": "Словосочетание",
    "text_comprehension": "Содержание текста",
    "expressive_means": "Средства выразительности",
    "lexical_analysis": "Лексический анализ",
    "essay_writing": "Сочинение",
    # humanized English leftovers from etalon titles
    "syntax basis": "Грамматическая основа",
    "syntax analysis": "Синтаксический анализ",
    "punctuation matching": "Пунктуация: соответствие",
    "punctuation placement": "Знаки препинания",
    "grammar form": "Грамматические нормы",
    "phrase transformation": "Словосочетание",
    "text comprehension": "Содержание текста",
    "expressive means": "Средства выразительности",
    "lexical analysis": "Лексический анализ",
    "summary writing": "Сжатое изложение",
    "essay writing": "Сочинение",
}

# ОГЭ русский: номер КИМ → тема (если topic пустой/английский)
OGE_RUS_NUM_LABELS: dict[int, str] = {
    1: "Сжатое изложение",
    2: "Грамматическая основа",
    3: "Синтаксический анализ",
    4: "Пунктуация: соответствие",
    5: "Знаки препинания",
    6: "Орфография: объяснение",
    7: "Орфография: вставка букв",
    8: "Грамматические нормы",
    9: "Словосочетание",
    10: "Содержание текста",
    11: "Средства выразительности",
    12: "Лексический анализ",
    13: "Сочинение",
}

_CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
_SMOKE_RE = re.compile(r"smoke", re.I)
_SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(?:[_\s]+[a-z0-9]+)+$", re.I)


def _looks_russian(value: str) -> bool:
    return bool(_CYRILLIC_RE.search(value or ""))


def _norm_slug(value: str) -> str:
    return re.sub(r"[\s_]+", "_", (value or "").strip().lower())


def _norm_spaced(value: str) -> str:
    return re.sub(r"[\s_]+", " ", (value or "").strip().lower())


def is_smoke_title(title: Optional[str]) -> bool:
    return bool(_SMOKE_RE.search(str(title or "")))


def translate_topic_slug(topic: Optional[str]) -> Optional[str]:
    raw = str(topic or "").strip()
    if not raw:
        return None
    if _looks_russian(raw):
        # уже русское — коротко обрежем «Было №N · …»
        cleaned = re.sub(r"^Было\s*№\d+\s*[·•\-–—]\s*", "", raw, flags=re.I).strip()
        return cleaned or raw
    # «syntax basis · etalon · …» → left part
    left = raw.split("·", 1)[0].strip() if "·" in raw else raw
    for key in (_norm_slug(left), _norm_spaced(left), left.lower(), raw.lower()):
        if key in TOPIC_LABELS_RU:
            return TOPIC_LABELS_RU[key]
    # underscore / spaced variants in full string
    slug = _norm_slug(left)
    spaced = _norm_spaced(left)
    if slug in TOPIC_LABELS_RU:
        return TOPIC_LABELS_RU[slug]
    if spaced in TOPIC_LABELS_RU:
        return TOPIC_LABELS_RU[spaced]
    if _SLUG_RE.match(left) or _SLUG_RE.match(raw):
        # неизвестный английский slug — не показываем как есть
        return None
    return raw if _looks_russian(raw) else None


def subject_is_russian(subject: Optional[str]) -> bool:
    s = (subject or "").strip().lower()
    return s in {"russian", "rus", "ru", "русский", "русский язык"}


def subject_is_math(subject: Optional[str]) -> bool:
    s = (subject or "").strip().lower()
    return s in {"math", "математика", "oge_math", "profile_math", "base_math", "vpr_math"}


def topic_label_for_num(
    num: int,
    topic: Optional[str],
    *,
    subject: Optional[str] = None,
    kim_type: Optional[int] = None,
) -> str:
    """Короткая русская тема для номера задания."""
    translated = translate_topic_slug(topic)
    if translated:
        return translated
    slot = int(kim_type or num or 0)
    if subject_is_russian(subject) and slot in OGE_RUS_NUM_LABELS:
        return OGE_RUS_NUM_LABELS[slot]
    if subject_is_math(subject):
        return f"Задание {num}" if num else "Задание"
    if slot in OGE_RUS_NUM_LABELS and not topic:
        return OGE_RUS_NUM_LABELS[slot]
    return f"Задание {num}" if num else "Задание"


def format_hard_flag(
    num: int,
    topic: Optional[str],
    wrong_pct: float,
    *,
    subject: Optional[str] = None,
    class_mode: bool = True,
) -> str:
    label = topic_label_for_num(num, topic, subject=subject)
    who = "класса" if class_mode else "ученика"
    pct = int(round(wrong_pct))
    return f"№{num} — {label} — {pct}% {who} ошиблись"


def display_assignment_title(
    title: Optional[str],
    created_at: Optional[datetime] = None,
    *,
    index: Optional[int] = None,
) -> str:
    """Чистый заголовок для тренда/селекта: «Вариант · дата», без Smoke junk."""
    raw = str(title or "").strip()
    date_s = ""
    if created_at is not None:
        try:
            date_s = created_at.strftime("%d.%m.%Y")
        except Exception:
            date_s = ""

    if is_smoke_title(raw) or not raw:
        base = f"Вариант {index}" if index else "Вариант"
        return f"{base} · {date_s}" if date_s else base

    # remediation / работа над ошибками — оставляем
    if "работ" in raw.lower() and "ошибк" in raw.lower():
        return f"{raw} · {date_s}" if date_s and date_s not in raw else raw

    # QA sandbox titles
    if re.search(r"\bqa\b|sandbox", raw, re.I):
        base = f"Вариант {index}" if index else "Вариант"
        return f"{base} · {date_s}" if date_s else base

    short = raw if len(raw) <= 48 else raw[:45] + "…"
    if date_s and date_s not in short:
        return f"{short} · {date_s}"
    return short


def build_teacher_summary(
    *,
    mode: str,
    participation_pct: Optional[float],
    submitters: int,
    roster: int,
    avg_percent: Optional[float],
    weakest_count: int,
) -> list[str]:
    lines: list[str] = []
    if mode == "student":
        if avg_percent is not None:
            lines.append(f"Результат ученика: {avg_percent}%.")
        else:
            lines.append("По выбранной работе ещё нет оценённой сдачи.")
        if weakest_count:
            lines.append(f"Слабых номеров: {weakest_count} — стоит дать работу над ошибками.")
        return lines

    if roster > 0 and participation_pct is not None:
        lines.append(
            f"Сдали {submitters} из {roster} ({participation_pct}%)."
        )
    elif submitters > 0:
        lines.append(f"Сдали {submitters} · список учеников не заполнен.")
    else:
        lines.append("Пока нет сдач по выбранной работе.")

    if avg_percent is not None:
        lines.append(f"Средний результат класса: {avg_percent}%.")
    elif submitters > 0:
        lines.append("Средний % появится после автопроверки.")

    return lines


def question_fingerprint(q: dict[str, Any]) -> str:
    text = str(q.get("text") or "").strip()
    ans = str(q.get("answer") or "").strip()
    return f"{text[:240]}|{ans[:80]}"
