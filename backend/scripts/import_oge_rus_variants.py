"""Импорт ОГЭ русский — цельные варианты (КИМ типы 1–13).

Запуск из корня проекта:
  python -m backend.scripts.import_oge_rus_variants
  python -m backend.scripts.import_oge_rus_variants --json path/to/pack.json
  python -m backend.scripts.import_oge_rus_variants --json .../oge_rus_var_kim.json
  python -m backend.scripts.import_oge_rus_variants --skip-seed

Поддерживаемые схемы JSON:
  1) pack: {pack_info, variants:[{listening_text|izlozhenie, grammar_text,
     reading_text, tasks 2..13}]}
  2) single kim: {variant_id, listening_text, grammar_text, reading_text, tasks}
  3) legacy var_a: {variant_id, contexts, tasks} — неполный КИМ, пропускается
     при проверке слотов 1–13

Тексты разделены:
  listening_text → задание 1 (изложение / аудио)
  grammar_text   → задания 2–3
  reading_text   → задания 10–13

Generate выбирает один полный context_id со слотами 1..13 (vary=False).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.universal.packs.loader import pack_dir
from backend.scripts.oge_rus_convert import (  # noqa: E402
    GRAMMAR_MARK as _CONV_GRAMMAR_MARK,
    IZLO_MARK as _CONV_IZLO_MARK,
    KIM_SLOTS as _CONV_KIM_SLOTS,
    READ_MARK as _CONV_READ_MARK,
    convert_variant as convert_variant_kim,
)

PACK_ID = "oge_rus"
IMPORT_NAME = "oge_rus_variants_v2.json"
FULL_IMPORT_NAME = "oge_rus_variants_full.json"
SINGLE_IMPORT_NAME = "oge_rus_var_kim.json"
SUBJECT_CODE = "russian"
EXAM_CODE = "OGE"
TITLE_PREFIX = "v2"
TITLE_PREFIX_A = "a"
TITLE_PREFIX_KIM = "kim"
KIM_SLOTS = int(_CONV_KIM_SLOTS)
IZLO_MARK = _CONV_IZLO_MARK
GRAMMAR_MARK = _CONV_GRAMMAR_MARK
READ_MARK = _CONV_READ_MARK

# Источник type (var_a) → topic для подписей/prompt
TYPE_TO_TOPIC: dict[str, str] = {
    "GrammarBasis": "syntax_basis",
    "DashPunctuation": "punctuation_dash",
    "PunctuationSPP": "punctuation_commas",
    "SpellingExplanation": "spelling_explanation",
    "SpellingInsertion": "spelling_insertion",
    "GrammarForms": "grammar_forms",
    "PhraseTransformation": "phrase_transformation",
    "TextComprehension": "text_comprehension",
    "ExpressiveMeans": "expressive_means",
    "LexicalAnalysis": "lexical_analysis",
    "IzlozhenieWriting": "summary_writing",
    "EssayWriting": "essay_writing",
}

TOPIC_LABELS: dict[str, str] = {
    "summary_writing": "Сжатое изложение",
    "syntax_basis": "Грамматическая основа",
    "syntax_analysis_basis": "Грамматическая основа",
    "syntax_analysis": "Синтаксический анализ",
    "punctuation_dash": "Тире",
    "punctuation_commas": "Запятые",
    "punctuation_matching": "Пунктуация: соответствие",
    "punctuation_analysis": "Пунктуационный анализ",
    "punctuation_placement": "Знаки препинания",
    "spelling_explanation": "Орфография: объяснение",
    "spelling_letters": "Орфография: вставка букв",
    "spelling_analysis": "Орфографический анализ",
    "spelling_insertion": "Орфография: вставка букв",
    "grammar_form": "Грамматические нормы",
    "grammar_forms": "Грамматические нормы",
    "phrase_transformation": "Словосочетание",
    "syntax_phrase_transform": "Словосочетание",
    "text_comprehension": "Содержание текста",
    "expressive_means": "Средства выразительности",
    "lexical_analysis": "Лексический анализ",
    "essay_writing": "Сочинение",
}

PROMPT_BY_TOPIC: dict[str, str] = {
    "summary_writing": "Сжатое изложение по прослушанному тексту. Сохрани критерии и объём.",
    "syntax_basis": "Грамматическая основа. Ответ — номера без пробелов.",
    "syntax_analysis_basis": "Грамматическая основа. Ответ — номера без пробелов.",
    "syntax_analysis": "Синтаксический анализ предложений. Ответ — номера.",
    "punctuation_dash": "Тире. Ответ — цифры.",
    "punctuation_commas": "Запятые. Ответ — цифры.",
    "punctuation_matching": "Соответствие правил и примеров. Ответ — три цифры (АБВ).",
    "punctuation_analysis": "Пунктуационный анализ. Ответ — цифры.",
    "punctuation_placement": "Расстановка знаков препинания. Ответ — цифры.",
    "spelling_explanation": "Орфографический анализ. Ответ — номера.",
    "spelling_letters": "Вставка букв. Ответ — цифры.",
    "spelling_analysis": "Орфографический анализ. Ответ — номера.",
    "spelling_insertion": "Вставка букв. Ответ — цифры.",
    "grammar_form": "Грамматическая форма слова. Ответ — слово/форма.",
    "grammar_forms": "Грамматическая форма слова. Ответ — слово/форма.",
    "phrase_transformation": "Замена словосочетания. Ответ — словосочетание.",
    "syntax_phrase_transform": "Замена словосочетания. Ответ — словосочетание.",
    "text_comprehension": "Содержание текста. Ответ — номера.",
    "expressive_means": "Средства выразительности. Ответ — номера.",
    "lexical_analysis": "Лексический анализ. Ответ — слово/словосочетание.",
    "essay_writing": "Сочинение-рассуждение. Одна карточка с выбором 13.1/13.2/13.3.",
}


def _opt_text(value: object | None) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _json_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    s = str(value).strip()
    return s or None


def _part_for(num: int) -> int:
    return 2 if num in (1, 13) else 1


def _prompt_for(topic: str, num: int) -> str:
    base = PROMPT_BY_TOPIC.get(topic)
    if base:
        return base
    return f"Задание ОГЭ русский №{num}. Сохрани тип КИМ и корректный ответ."


def _prototype_title(
    *, variant_id: str, num: int, topic: str, title_prefix: str = TITLE_PREFIX
) -> str:
    label = TOPIC_LABELS.get(topic) or topic.replace("_", " ") or "Задание"
    return f"{label} · {title_prefix} · {variant_id} #{num}"


def build_context_description(
    *,
    listening: dict[str, Any],
    grammar: dict[str, Any],
    reading: dict[str, Any],
) -> str:
    """Структурированный текст: изложение + грамматика (2–3) + чтение (10–13)."""
    script = (
        _opt_text(listening.get("audio_script"))
        or _opt_text(listening.get("text"))
        or ""
    )
    grammar_body = _opt_text(grammar.get("content")) or _opt_text(grammar.get("text")) or ""
    author = _opt_text(reading.get("author")) or ""
    content = _opt_text(reading.get("content")) or _opt_text(reading.get("text")) or ""
    read_block = content
    if author:
        read_block = f"{author}\n\n{content}" if content else author
    note = _opt_text(reading.get("note"))
    if note and read_block:
        read_block = f"{read_block}\n\n{note}"
    return (
        f"{IZLO_MARK}\n{script}\n\n"
        f"{GRAMMAR_MARK}\n{grammar_body}\n\n"
        f"{READ_MARK}\n{read_block}"
    ).strip()


def _izlozhenie_template(izlo: dict[str, Any]) -> str:
    """Инструкция как на экзамене — без полного дампа скрипта в условие."""
    min_words = int(izlo.get("min_words") or 70)
    title = _opt_text(izlo.get("title")) or "Сжатое изложение"
    hint = _opt_text(izlo.get("audio_script")) or _opt_text(izlo.get("text")) or ""
    opener = ""
    if hint:
        first = hint.strip().split("\n", 1)[0].strip()
        if len(first) > 90:
            first = first[:87].rstrip() + "…"
        opener = f"Текст, начинающийся словами «{first}».\n\n"
    return (
        f"Тип 1. Сжатое изложение.\n"
        f"{title}\n\n"
        f"{opener}"
        f"Прослушайте текст и напишите сжатое изложение его содержания. "
        f"Исходный текст для сжатого изложения прослушивается 2 раза.\n\n"
        f"Учтите, что Вы должны передать главное содержание как микротемы, "
        f"так и всего текста в целом.\n\n"
        f"Объём изложения — не менее {min_words} слов.\n\n"
        f"Пишите изложение аккуратно, разборчивым почерком."
    ).strip()


def _essay_template(task: dict[str, Any]) -> str:
    options = task.get("options")
    if not isinstance(options, list) or not options:
        return _opt_text(task.get("statement")) or "Напишите сочинение-рассуждение."
    lines = [
        "Тип 13. Сочинение.",
        "Используя прочитанный текст, выполните ТОЛЬКО ОДНО из заданий "
        "(13.1, 13.2 или 13.3). Перед написанием сочинения запишите номер "
        "выбранного задания.",
        "",
    ]
    for opt in options:
        if not isinstance(opt, dict):
            continue
        kind = _opt_text(opt.get("type")) or "13.x"
        title = _opt_text(opt.get("title")) or ""
        statement = _opt_text(opt.get("statement")) or ""
        head = f"{kind}"
        if title:
            head = f"{kind} — {title}"
        lines.append(head)
        if statement:
            lines.append(statement)
        lines.append("")
    return "\n".join(lines).strip()


def _matching_statement(task: dict[str, Any]) -> str:
    base = _opt_text(task.get("statement")) or (
        "Установите соответствие между пунктуационными правилами и предложениями."
    )
    matching = task.get("matching") if isinstance(task.get("matching"), dict) else {}
    left = matching.get("left") if isinstance(matching.get("left"), list) else []
    right = matching.get("right") if isinstance(matching.get("right"), list) else []
    lines = [base, "", "ПУНКТУАЦИОННЫЕ ПРАВИЛА"]
    for item in left:
        if not isinstance(item, dict):
            continue
        lid = _opt_text(item.get("id")) or ""
        text = _opt_text(item.get("text")) or ""
        lines.append(f"{lid}) {text}".strip())
    lines.extend(["", "ПРЕДЛОЖЕНИЯ"])
    for item in right:
        if not isinstance(item, dict):
            continue
        rid = _opt_text(item.get("id")) or ""
        text = _opt_text(item.get("text")) or ""
        lines.append(f"{rid}) {text}".strip())
    lines.append("")
    lines.append("Ответ запишите как три цифры подряд (для А, Б, В).")
    return "\n".join(lines).strip()


def _oge_rus_payload(
    *,
    kim_type: int,
    listening: dict[str, Any] | None = None,
    grammar: dict[str, Any] | None = None,
    reading: dict[str, Any] | None = None,
    matching: dict[str, Any] | None = None,
    essay_options: list[Any] | None = None,
    show_grammar: bool = False,
    show_reading: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "oge_rus": True,
        "kim_type": int(kim_type),
        "ui": "oge_rus",
    }
    if kim_type == 1 and listening:
        script = (
            _opt_text(listening.get("audio_script"))
            or _opt_text(listening.get("text"))
            or ""
        )
        payload["listening_text"] = script
        payload["listening_title"] = _opt_text(listening.get("title"))
        payload["listening_author"] = _opt_text(listening.get("author"))
        audio = _opt_text(listening.get("audio_url") or listening.get("audio"))
        if audio:
            payload["audio_url"] = audio
        payload["listen_twice"] = True
        payload["hide_transcript_default"] = True
        payload["tts_fallback"] = True
        payload["ui"] = "listening"
    # Текст грамматики нужен и заданию 2, и 3 (UI показывает блок один раз над парой).
    if grammar and kim_type in (2, 3):
        payload["grammar_text"] = (
            _opt_text(grammar.get("content")) or _opt_text(grammar.get("text")) or ""
        )
        if show_grammar or kim_type == 2:
            payload["show_shared"] = "grammar"
    if show_reading and reading:
        author = _opt_text(reading.get("author")) or ""
        content = _opt_text(reading.get("content")) or _opt_text(reading.get("text")) or ""
        note = _opt_text(reading.get("note"))
        block = content
        if author:
            block = f"{author}\n\n{content}" if content else author
        if note:
            block = f"{block}\n\n{note}" if block else note
        payload["reading_text"] = block
        payload["show_shared"] = "reading"
    if matching:
        payload["matching"] = matching
        payload["ui"] = "matching"
    if essay_options:
        payload["essay_options"] = essay_options
        payload["ui"] = "essay_choice"
    return payload


def _is_single_variant_schema(raw: dict[str, Any]) -> bool:
    """Одиночный вариант: variant_id + tasks, без pack variants[]."""
    return (
        "variant_id" in raw
        and "tasks" in raw
        and "variants" not in raw
    )


def _is_kim_whole_schema(variant: dict[str, Any]) -> bool:
    """Цельный КИМ: listening/izlo + reading + tasks (не legacy contexts)."""
    has_listen = isinstance(variant.get("listening_text"), dict) or isinstance(
        variant.get("izlozhenie"), dict
    )
    has_read = isinstance(variant.get("reading_text"), dict)
    has_tasks = isinstance(variant.get("tasks"), list)
    return has_listen and has_read and has_tasks and not isinstance(
        variant.get("contexts"), dict
    )


def _remap_source_num_to_kim(src_num: int) -> int:
    """Источник: 11=изложение, 1..10=тесты, 12=сочинение → КИМ 1..12."""
    if src_num == 11:
        return 1
    if src_num == 12:
        return 12
    if 1 <= src_num <= 10:
        return src_num + 1
    raise ValueError(f"Неожиданный task_number источника: {src_num}")


def _lookup_context(
    contexts: dict[str, Any], ref: str | None
) -> dict[str, Any] | None:
    if not ref:
        return None
    key = str(ref).strip()
    if not key:
        return None
    ctx = contexts.get(key)
    return ctx if isinstance(ctx, dict) else None


def _format_context_prefix(ctx: dict[str, Any], *, kind: str) -> str:
    """Текст контекста для вшивания в template (чтение / изложение)."""
    title = _opt_text(ctx.get("title"))
    author = _opt_text(ctx.get("author"))
    text = _opt_text(ctx.get("text")) or ""
    if kind == "izlozhenie":
        head = title or "Текст для изложения"
        return f"Текст для изложения (аудиоскрипт)\nТема: {head}\n\n{text}".strip()
    parts: list[str] = ["Текст для чтения"]
    if author:
        parts.append(author)
    elif title:
        parts.append(title)
    if text:
        parts.append(text)
    return "\n\n".join(parts).strip()


def _prepend_context(body: str | None, prefix: str | None) -> str | None:
    b = (body or "").strip()
    p = (prefix or "").strip()
    if not p:
        return b or None
    if not b:
        return p
    head = p[:80]
    if head and head in b:
        return b
    return f"{p}\n\n{b}"


def convert_variant_a(variant: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Legacy — делегирует в convert_variant_kim (выбросит ValueError)."""
    return convert_variant_kim(variant)


def convert_variant(variant: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """→ (context_block_dict, prototype_rows). КИМ 1–13."""
    return convert_variant_kim(variant)


def _legacy_convert_variant_a_UNUSED(variant: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Схема var_a (contexts + tasks) → KIM-слоты 1..12, context_id = variant_id."""
    vid = str(variant.get("variant_id") or "").strip()
    if not vid:
        raise ValueError("variant без variant_id")
    title = str(variant.get("title") or vid).strip()
    contexts_raw = variant.get("contexts") if isinstance(variant.get("contexts"), dict) else {}
    contexts: dict[str, Any] = {
        str(k): v for k, v in contexts_raw.items() if isinstance(v, dict)
    }
    tasks = [t for t in (variant.get("tasks") or []) if isinstance(t, dict)]

    # Изложение и чтение для description: берём из слотов после remap
    izlo_ctx: dict[str, Any] | None = None
    read_ctx: dict[str, Any] | None = None
    for task in tasks:
        ttype = str(task.get("type") or "")
        cref = _opt_text(task.get("context_ref"))
        ctx = _lookup_context(contexts, cref)
        if ttype == "IzlozhenieWriting" and ctx is not None:
            izlo_ctx = ctx
        if ttype == "EssayWriting" and ctx is not None:
            read_ctx = ctx
    if izlo_ctx is None:
        for key, ctx in contexts.items():
            if str(key).startswith("izlozhenie"):
                izlo_ctx = ctx
                break
    if read_ctx is None:
        for key, ctx in contexts.items():
            if str(key).startswith("reading"):
                read_ctx = ctx
                break

    izlo_script = _opt_text((izlo_ctx or {}).get("text")) or ""
    # У var_a разные тексты по заданиям — префикс чтения вшит в template.
    # READ_MARK оставляем пустым, чтобы generate не подмешивал чужой текст.
    desc = f"{IZLO_MARK}\n{izlo_script}\n\n{READ_MARK}\n".strip()

    block = {
        "context_id": vid,
        "title": title,
        "description_text": desc,
        "audio_script": izlo_script or None,
        "reading_author": _opt_text((read_ctx or {}).get("author")),
        "reading_content": _opt_text((read_ctx or {}).get("text")),
        "contexts": contexts,
    }

    rows: list[dict[str, Any]] = []
    for task in tasks:
        src_num = int(task["task_number"])
        kim_num = _remap_source_num_to_kim(src_num)
        ttype = str(task.get("type") or "").strip()
        topic = TYPE_TO_TOPIC.get(ttype) or str(task.get("topic") or ttype or "task").strip()
        part = _part_for(kim_num)
        cref = _opt_text(task.get("context_ref"))
        ctx = _lookup_context(contexts, cref)
        statement = _opt_text(task.get("statement") or task.get("template_text"))

        if kim_num == 1 or ttype == "IzlozhenieWriting":
            izlo_for_tpl = {
                "audio_script": _opt_text((ctx or {}).get("text")) or izlo_script,
                "title": _opt_text((ctx or {}).get("title")) or "Сжатое изложение",
                "min_words": 70,
                "max_score": int(task.get("max_score") or 7),
            }
            template_text = _izlozhenie_template(izlo_for_tpl)
            answer = "Развёрнутый ответ (сжатое изложение)"
            max_score = int(task.get("max_score") or 7)
            part = 2
            solution = (
                "Критерии: ИК1 (микротемы), ИК2 (сжатие), ИК3 (смысловая цельность). "
                "Минимум слов: 70."
            )
            acceptable: list[Any] = []
        elif kim_num == 12 or ttype == "EssayWriting":
            template_text = _essay_template(task)
            if ctx is not None:
                template_text = _prepend_context(
                    template_text, _format_context_prefix(ctx, kind="reading")
                )
            answer = "Развёрнутый ответ (сочинение)"
            max_score = int(task.get("max_score") or 7)
            part = 2
            solution = _opt_text(task.get("solution_hint"))
            acceptable = []
        else:
            prefix = (
                _format_context_prefix(ctx, kind="reading") if ctx is not None else None
            )
            template_text = _prepend_context(statement, prefix)
            answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
            max_score = int(task.get("max_score") or 1)
            solution = _opt_text(task.get("solution_hint"))
            acceptable = []
            raw_acc = task.get("acceptable_answers")
            if isinstance(raw_acc, list):
                acceptable = list(raw_acc)
            if not acceptable and answer:
                acceptable = [answer]

        if not answer and part == 2:
            answer = "Развёрнутый ответ"

        rows.append(
            {
                "task_number": kim_num,
                "part": part,
                "prototype_title": _prototype_title(
                    variant_id=vid,
                    num=kim_num,
                    topic=topic,
                    title_prefix=TITLE_PREFIX_A,
                ),
                "prompt_instruction": _prompt_for(topic, kim_num),
                "template_text": template_text,
                "template_answer": answer,
                "template_solution": solution,
                "difficulty": _opt_text(task.get("difficulty")),
                "answer_type": "string",
                "max_score": max_score,
                "acceptable_answers": acceptable,
                "figure_kind": None,
                "figure_params": None,
                "context_id": vid,
                "source_id": _opt_text(task.get("id")) or f"{vid}_src{src_num}",
            }
        )

    rows.sort(key=lambda r: int(r["task_number"]))
    nums = {int(r["task_number"]) for r in rows}
    missing = sorted(set(range(1, KIM_SLOTS + 1)) - nums)
    if missing:
        raise ValueError(f"{vid}: после remap нет слотов {missing}")
    return block, rows


def _legacy_pack_convert_UNUSED(variant: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Устаревший конвертер 12 слотов — не используется (см. convert_variant_kim)."""
    raise RuntimeError("use convert_variant_kim")
    if isinstance(variant.get("contexts"), dict) and not isinstance(
        variant.get("izlozhenie"), dict
    ):
        return convert_variant_a(variant)

    vid = str(variant.get("variant_id") or "").strip()
    if not vid:
        raise ValueError("variant без variant_id")
    title = str(variant.get("title") or vid).strip()
    izlo = variant.get("izlozhenie") if isinstance(variant.get("izlozhenie"), dict) else {}
    reading = variant.get("reading_text") if isinstance(variant.get("reading_text"), dict) else {}
    tasks = list(variant.get("tasks") or [])

    block = {
        "context_id": vid,
        "title": title,
        "description_text": "",
        "audio_script": _opt_text(izlo.get("audio_script")),
        "reading_author": _opt_text(reading.get("author")),
        "reading_content": _opt_text(reading.get("content")),
    }

    rows: list[dict[str, Any]] = []

    # Task 1 — изложение
    if izlo:
        rows.append(
            {
                "task_number": 1,
                "part": 2,
                "prototype_title": _prototype_title(
                    variant_id=vid, num=1, topic="summary_writing"
                ),
                "prompt_instruction": _prompt_for("summary_writing", 1),
                "template_text": _izlozhenie_template(izlo),
                "template_answer": "Развёрнутый ответ (сжатое изложение)",
                "template_solution": (
                    "Критерии: ИК1 (микротемы), ИК2 (сжатие), ИК3 (смысловая цельность). "
                    f"Минимум слов: {int(izlo.get('min_words') or 70)}."
                ),
                "difficulty": None,
                "answer_type": "string",
                "max_score": int(izlo.get("max_score") or 7),
                "acceptable_answers": [],
                "figure_kind": None,
                "figure_params": None,
                "context_id": vid,
                "source_id": _opt_text(izlo.get("id")),
            }
        )

    for task in tasks:
        if not isinstance(task, dict):
            continue
        num = int(task["task_number"])
        topic = str(task.get("topic") or task.get("topic_id") or "task").strip()
        part = _part_for(num)
        if num == 12 or topic == "essay_writing":
            template_text = _essay_template(task)
            answer = "Развёрнутый ответ (сочинение)"
            max_score = int(task.get("max_score") or 7)
            part = 2
        else:
            template_text = _opt_text(task.get("statement") or task.get("template_text"))
            answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
            max_score = int(task.get("max_score") or 1)
        if not answer and part == 2:
            answer = "Развёрнутый ответ"
        acceptable: list[Any] = []
        raw_acc = task.get("acceptable_answers")
        if isinstance(raw_acc, list):
            acceptable = list(raw_acc)
        if not acceptable and answer and part == 1:
            acceptable = [answer]
        rows.append(
            {
                "task_number": num,
                "part": part,
                "prototype_title": _prototype_title(variant_id=vid, num=num, topic=topic),
                "prompt_instruction": _prompt_for(topic, num),
                "template_text": template_text,
                "template_answer": answer,
                "template_solution": _opt_text(task.get("solution_hint")),
                "difficulty": _opt_text(task.get("difficulty")),
                "answer_type": "string",
                "max_score": max_score,
                "acceptable_answers": acceptable,
                "figure_kind": None,
                "figure_params": None,
                "context_id": vid,
                "source_id": _opt_text(task.get("id")),
            }
        )

    rows.sort(key=lambda r: int(r["task_number"]))
    nums = {int(r["task_number"]) for r in rows}
    missing = sorted(set(range(1, KIM_SLOTS + 1)) - nums)
    if missing:
        raise ValueError(f"{vid}: нет слотов КИМ {missing} (нужны 1–{KIM_SLOTS})")
    empty = [
        int(r["task_number"])
        for r in rows
        if not str(r.get("template_text") or "").strip()
    ]
    if empty:
        raise ValueError(f"{vid}: пустой template_text у слотов {empty}")
    return block, rows


def write_context_file(root: Path, block: dict[str, Any], rows: list[dict[str, Any]]) -> Path:
    cdir = root / "context_blocks"
    cdir.mkdir(parents=True, exist_ok=True)
    cid = str(block["context_id"])
    tasks_out = []
    for row in rows:
        tasks_out.append(
            {
                "task_number": row["task_number"],
                "part": row["part"],
                "prototype_title": row["prototype_title"],
                "prompt_instruction": row["prompt_instruction"],
                "template_text": row["template_text"],
                "template_answer": row["template_answer"],
                "template_solution": row.get("template_solution"),
                "answer_type": row["answer_type"],
                "max_score": row["max_score"],
                "acceptable_answers": row["acceptable_answers"],
                "figure_kind": row.get("figure_kind"),
                "figure_params": row.get("figure_params"),
            }
        )
    payload = {
        "context_id": cid,
        "title": block["title"],
        "description_text": block["description_text"],
        "figure_kind": None,
        "figure_params": None,
        "exam_code": EXAM_CODE,
        "subject_code": SUBJECT_CODE,
        "tasks": tasks_out,
    }
    if block.get("audio_script"):
        payload["audio_script"] = block["audio_script"]
    if block.get("audio_url"):
        payload["audio_url"] = block["audio_url"]
    if block.get("grammar_content"):
        payload["grammar_text"] = block["grammar_content"]
    if block.get("reading_content"):
        payload["reading_content"] = block["reading_content"]
    if block.get("reading_author"):
        payload["reading_author"] = block["reading_author"]
    if block.get("source_notes"):
        payload["source_notes"] = block["source_notes"]
    path = cdir / f"{cid}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_pack_info(
    root: Path,
    pack_info_src: dict[str, Any] | None,
    *,
    complete_variant_ids: list[str] | None = None,
) -> Path:
    path = root / "pack_info.json"
    legacy_incomplete = [
        "oge_rus_var_01",
        "oge_rus_var_02",
        "oge_rus_var_03",
        "oge_rus_var_04",
        "oge_rus_var_05",
        "oge_rus_var_a",
    ]
    complete = list(complete_variant_ids or [])
    if not complete:
        complete = ["oge_rus_var_kim"]
    # полные КИМ первыми; legacy (неполные) — для справки, generate их не берёт
    variant_ids: list[str] = []
    for vid in complete + legacy_incomplete:
        if vid not in variant_ids:
            variant_ids.append(vid)
    info = {
        "pack_id": PACK_ID,
        "exam_code": EXAM_CODE,
        "subject_code": SUBJECT_CODE,
        "subject_name": "Русский язык",
        "exam_name": "ОГЭ",
        "kim_year": int((pack_info_src or {}).get("exam_year") or 2026),
        "title": "ОГЭ Русский язык — цельные варианты",
        "version": str((pack_info_src or {}).get("version") or "2.1.0"),
        "primary_max_score": 33,
        "slot_count": KIM_SLOTS,
        "parts": [
            {
                "part": 1,
                "task_numbers": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                "max_score_per_task": 1,
                "primary_total": 11,
                "answer_style": "short",
            },
            {
                "part": 2,
                "task_numbers": [1, 13],
                "max_scores": {"1": 7, "13": 7},
                "primary_total": 13,
                "answer_style": "extended",
                "notes": (
                    "Изложение (1) и сочинение (13); варианты 13.1/13.2/13.3 в одной карточке. "
                    "listening_text ≠ grammar_text ≠ reading_text."
                ),
            },
        ],
        "context_policy": "whole_variant — generate picks one context_id (variant), never mixes",
        "runtime": {
            "store": "postgres",
            "tables": ["context_blocks", "task_prototypes"],
            "seed_command": (
                f"python -m backend.scripts.import_oge_rus_variants "
                f"--json backend/universal/packs/oge_rus/imports/{FULL_IMPORT_NAME}"
            ),
            "generate": (
                "generate_variant(russian, OGE) — 13 слотов из одного полного oge_rus_var_*"
            ),
        },
        "sources": [
            "ФИПИ / структура Решу ОГЭ (типы 1–13)",
            f"imports/{FULL_IMPORT_NAME}",
            f"imports/{SINGLE_IMPORT_NAME}",
            f"imports/{IMPORT_NAME}",
        ],
        "variant_ids": variant_ids,
        "complete_variant_ids": complete,
        "upstream_pack_id": (pack_info_src or {}).get("pack_id"),
    }
    path.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def seed_pg(
    blocks: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Upsert только context_id из текущего импорта — другие варианты (и math) не трогаем."""
    from sqlalchemy import select

    from backend.db.pg import init_pg_tables, session_factory
    from backend.db.pg_models import ContextBlock, ExamType, Subject, TaskPrototype

    init_pg_tables()
    SessionLocal = session_factory()
    db = SessionLocal()
    try:
        subj = db.scalar(select(Subject).where(Subject.code == SUBJECT_CODE))
        if subj is None:
            db.add(Subject(code=SUBJECT_CODE, name="Русский язык"))
        else:
            subj.name = "Русский язык"
        exam = db.scalar(select(ExamType).where(ExamType.code == EXAM_CODE))
        if exam is None:
            db.add(ExamType(code=EXAM_CODE, name="ОГЭ"))
        else:
            exam.name = "ОГЭ"
        db.flush()

        target_cids = sorted(
            {
                str(b.get("context_id") or "").strip()
                for b in blocks
                if str(b.get("context_id") or "").strip()
            }
            | {
                str(r.get("context_id") or "").strip()
                for r in rows
                if str(r.get("context_id") or "").strip()
            }
        )
        stale_n = 0
        if target_cids:
            old_protos = db.scalars(
                select(TaskPrototype).where(
                    TaskPrototype.subject_code == SUBJECT_CODE,
                    TaskPrototype.exam_code == EXAM_CODE,
                    TaskPrototype.context_id.in_(target_cids),
                )
            ).all()
            for row in old_protos:
                db.delete(row)
                stale_n += 1
            db.flush()

        ctx_ins = ctx_upd = 0
        for block in blocks:
            cid = str(block.get("context_id") or "").strip()
            if not cid:
                continue
            title = str(block.get("title") or cid).strip()
            desc = _opt_text(block.get("description_text"))
            exists = db.scalar(
                select(ContextBlock).where(
                    ContextBlock.context_id == cid,
                    ContextBlock.subject_code == SUBJECT_CODE,
                    ContextBlock.exam_code == EXAM_CODE,
                )
            )
            if exists:
                exists.title = title
                exists.description_text = desc
                exists.figure_kind = None
                exists.figure_params = None
                ctx_upd += 1
            else:
                db.add(
                    ContextBlock(
                        context_id=cid,
                        title=title,
                        description_text=desc,
                        figure_kind=None,
                        figure_params=None,
                        subject_code=SUBJECT_CODE,
                        exam_code=EXAM_CODE,
                    )
                )
                ctx_ins += 1

        proto_ins = 0
        for p in rows:
            num = int(p["task_number"])
            title = str(p["prototype_title"]).strip()
            db.add(
                TaskPrototype(
                    subject_code=SUBJECT_CODE,
                    exam_code=EXAM_CODE,
                    task_number=num,
                    prototype_title=title,
                    part=int(p["part"]),
                    prompt_instruction=str(p["prompt_instruction"]).strip(),
                    template_text=_opt_text(p.get("template_text")),
                    template_answer=_opt_text(p.get("template_answer")),
                    template_solution=_opt_text(p.get("template_solution")),
                    figure_kind=None,
                    figure_params=_json_or_none(p.get("figure_params")),
                    figure_data=None,
                    figure_svg=None,
                    context_id=_opt_text(p.get("context_id")),
                    answer_type=_opt_text(p.get("answer_type")),
                    max_score=int(p["max_score"]) if p.get("max_score") is not None else None,
                    acceptable_answers=_json_or_none(p.get("acceptable_answers")),
                )
            )
            proto_ins += 1

        db.commit()
        return {
            "context_inserted": ctx_ins,
            "context_updated": ctx_upd,
            "prototypes_inserted": proto_ins,
            "prototypes_updated": 0,
            "stale_deleted": stale_n,
            "context_ids": target_cids,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def default_import_path(root: Path) -> Path:
    return root / "imports" / IMPORT_NAME


def _normalize_import_payload(raw: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any] | None, str]:
    """→ (variants, pack_info|None, schema_label)."""
    if _is_single_variant_schema(raw):
        return [raw], None, "single_var_a"
    if "variants" in raw:
        variants = [v for v in (raw.get("variants") or []) if isinstance(v, dict)]
        pack_info = raw.get("pack_info") if isinstance(raw.get("pack_info"), dict) else None
        return variants, pack_info, "pack_v2"
    raise SystemExit(
        "Ожидался pack {pack_info, variants} или single {variant_id, contexts, tasks}"
    )


def run(*, json_path: Path | None = None, skip_seed: bool = False) -> dict[str, Any]:
    root = pack_dir(PACK_ID)
    root.mkdir(parents=True, exist_ok=True)
    imports_dir = root / "imports"
    imports_dir.mkdir(parents=True, exist_ok=True)
    dest_default = default_import_path(root)

    if json_path is not None:
        src = Path(json_path)
        raw = json.loads(src.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise SystemExit("JSON должен быть объектом")
        if _is_single_variant_schema(raw):
            # одиночный kim-файл: не затираем pack full/v2
            dest = imports_dir / src.name
            if src.name == SINGLE_IMPORT_NAME:
                dest = imports_dir / SINGLE_IMPORT_NAME
        else:
            dest = imports_dir / FULL_IMPORT_NAME
            if src.name == IMPORT_NAME:
                dest = dest_default
        dest.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        full_path = imports_dir / FULL_IMPORT_NAME
        kim_path = imports_dir / SINGLE_IMPORT_NAME
        if full_path.is_file():
            dest = full_path
            raw = json.loads(dest.read_text(encoding="utf-8"))
        elif kim_path.is_file():
            dest = kim_path
            raw = json.loads(dest.read_text(encoding="utf-8"))
        elif dest_default.is_file():
            dest = dest_default
            raw = json.loads(dest.read_text(encoding="utf-8"))
        else:
            raise SystemExit(
                f"Нет файла импорта: {full_path}, {kim_path} или {dest_default}\n"
                "Положите JSON пака туда или укажите --json PATH"
            )

    if not isinstance(raw, dict):
        raise SystemExit("JSON должен быть объектом")

    variants, pack_info, schema = _normalize_import_payload(raw)
    blocks: list[dict[str, Any]] = []
    all_rows: list[dict[str, Any]] = []
    ctx_paths: list[Path] = []
    per_variant: list[dict[str, Any]] = []
    skipped: list[str] = []

    for variant in variants:
        try:
            block, rows = convert_variant(variant)
        except ValueError as exc:
            skipped.append(str(exc))
            print(f"skip variant: {exc}")
            continue
        blocks.append(block)
        all_rows.extend(rows)
        ctx_paths.append(write_context_file(root, block, rows))
        per_variant.append(
            {
                "variant_id": block["context_id"],
                "prototypes": len(rows),
                "task_numbers": sorted({int(r["task_number"]) for r in rows}),
                "parts": sorted({int(r["part"]) for r in rows}),
            }
        )

    if not blocks:
        raise SystemExit(
            "Ни один вариант не прошёл конвертацию КИМ 1–13. "
            f"Пропущено: {skipped or ['—']}. "
            f"Импортируйте {SINGLE_IMPORT_NAME}."
        )

    # pack_info обновляем при импорте полного пака или kim
    if schema in ("pack_v2", "single_var_a") or _is_single_variant_schema(raw):
        write_pack_info(
            root,
            pack_info,
            complete_variant_ids=[b["context_id"] for b in blocks],
        )
        readme = root / "README.md"
        readme.write_text(
            "# Pack: ОГЭ Русский язык (`oge_rus`)\n\n"
            "Цельные варианты КИМ **типы 1–13**:\n"
            "- 1 — сжатое изложение (`listening_text` + аудио/TTS)\n"
            "- 2–3 — грамматика по короткому `grammar_text`\n"
            "- 4 — соответствие (matching)\n"
            "- 5–9 — пунктуация / орфография / формы / словосочетание\n"
            "- 10–12 — задания к длинному `reading_text`\n"
            "- 13 — сочинение 13.1 / 13.2 / 13.3\n\n"
            "**Важно:** listening ≠ grammar ≠ reading — тексты не склеивать.\n\n"
            "**Правило generate:** один полный `context_id` со слотами 1–13 "
            "(vary=False, без перемешивания). Неполные `var_01`… / `var_a` "
            "в generate не попадают.\n\n"
            "## Seed\n\n"
            "```powershell\n"
            f"python -m backend.scripts.import_oge_rus_variants --json "
            f"backend/universal/packs/oge_rus/imports/{FULL_IMPORT_NAME}\n"
            "```\n\n"
            f"Полный пак: `imports/{FULL_IMPORT_NAME}` "
            f"(эталон структуры: `imports/{SINGLE_IMPORT_NAME}`)\n",
            encoding="utf-8",
        )

    summary: dict[str, Any] = {
        "schema": schema,
        "import_json": str(dest),
        "context_files": [str(p) for p in ctx_paths],
        "variants": per_variant,
        "skipped": skipped,
        "prototypes": len(all_rows),
        "task_numbers": sorted({int(r["task_number"]) for r in all_rows}),
        "seed": None,
    }

    if skip_seed:
        print("import_oge_rus_variants (files only):", json.dumps(summary, ensure_ascii=False))
        return summary

    from backend.db.pg import is_postgres_configured

    if not is_postgres_configured():
        print("WARNING: POSTGRES_URL не задан — файлы записаны, seed пропущен")
        print("import_oge_rus_variants:", json.dumps(summary, ensure_ascii=False))
        return summary

    summary["seed"] = seed_pg(blocks, all_rows)
    print("import_oge_rus_variants done:", json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Import OGE Russian whole-variant pack")
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help=(
            f"Путь к JSON: pack ({IMPORT_NAME}) или single ({SINGLE_IMPORT_NAME})"
        ),
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Только файлы, без записи в Postgres",
    )
    args = parser.parse_args()
    run(json_path=args.json, skip_seed=bool(args.skip_seed))


if __name__ == "__main__":
    main()
