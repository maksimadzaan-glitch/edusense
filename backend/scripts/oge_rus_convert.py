"""Конвертация JSON-варианта ОГЭ русский → context_block + prototypes (КИМ 1–13)."""

from __future__ import annotations

from typing import Any

KIM_SLOTS = 13
TITLE_PREFIX = "v2"
TITLE_PREFIX_KIM = "kim"

IZLO_MARK = "<<<IZLOZHENIE>>>"
GRAMMAR_MARK = "<<<GRAMMAR>>>"
READ_MARK = "<<<READING>>>"

TOPIC_LABELS: dict[str, str] = {
    "summary_writing": "Сжатое изложение",
    "syntax_basis": "Грамматическая основа",
    "syntax_analysis": "Синтаксический анализ",
    "punctuation_matching": "Пунктуация: соответствие",
    "punctuation_placement": "Знаки препинания",
    "spelling_explanation": "Орфография: объяснение",
    "spelling_letters": "Орфография: вставка букв",
    "grammar_form": "Грамматические нормы",
    "phrase_transformation": "Словосочетание",
    "text_comprehension": "Содержание текста",
    "expressive_means": "Средства выразительности",
    "lexical_analysis": "Лексический анализ",
    "essay_writing": "Сочинение",
}

PROMPT_BY_TOPIC: dict[str, str] = {
    "summary_writing": "Сжатое изложение по прослушанному тексту. Сохрани критерии и объём.",
    "syntax_basis": "Грамматическая основа. Ответ — номера без пробелов.",
    "syntax_analysis": "Синтаксический анализ предложений. Ответ — номера.",
    "punctuation_matching": "Соответствие правил и примеров. Ответ — три цифры (АБВ).",
    "punctuation_placement": "Расстановка знаков препинания. Ответ — цифры.",
    "spelling_explanation": "Орфографический анализ. Ответ — номера.",
    "spelling_letters": "Вставка букв. Ответ — цифры.",
    "grammar_form": "Грамматическая форма слова. Ответ — слово/форма.",
    "phrase_transformation": "Замена словосочетания. Ответ — словосочетание.",
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
        payload["rubric"] = {
            "kind": "izlozhenie",
            "criteria": [
                {"id": "ik1", "title": "ИК1 · микротемы", "max": 2},
                {"id": "ik2", "title": "ИК2 · сжатие", "max": 3},
                {"id": "ik3", "title": "ИК3 · смысловая цельность", "max": 2},
            ],
        }
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
        payload["rubric"] = {
            "kind": "sochinenie",
            "criteria": [
                {"id": "sk1", "title": "СК1 · понимание текста / тезис", "max": 2},
                {"id": "sk2", "title": "СК2 · аргументы", "max": 3},
                {"id": "sk3", "title": "СК3 · композиция", "max": 2},
            ],
        }
    return payload


def convert_variant(variant: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """→ (context_block_dict, prototype_rows). КИМ-слоты 1..13."""
    if isinstance(variant.get("contexts"), dict) and not (
        isinstance(variant.get("listening_text"), dict)
        or isinstance(variant.get("izlozhenie"), dict)
    ):
        vid = str(variant.get("variant_id") or "").strip() or "?"
        raise ValueError(
            f"{vid}: legacy schema contexts+tasks (слоты ≠ КИМ 1–13). "
            "Используйте oge_rus_var_kim.json."
        )

    vid = str(variant.get("variant_id") or "").strip()
    if not vid:
        raise ValueError("variant без variant_id")
    title = str(variant.get("title") or vid).strip()

    listening = (
        variant.get("listening_text")
        if isinstance(variant.get("listening_text"), dict)
        else None
    )
    if listening is None and isinstance(variant.get("izlozhenie"), dict):
        listening = variant["izlozhenie"]
    listening = listening or {}

    grammar = (
        variant.get("grammar_text")
        if isinstance(variant.get("grammar_text"), dict)
        else {}
    )
    reading = (
        variant.get("reading_text")
        if isinstance(variant.get("reading_text"), dict)
        else {}
    )
    tasks = list(variant.get("tasks") or [])

    normalized_tasks: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        t = dict(task)
        num = int(t.get("task_number") or 0)
        topic = str(t.get("topic") or "").strip()
        if num == 12 and (topic == "essay_writing" or t.get("options")):
            has_real_12 = any(
                isinstance(x, dict)
                and int(x.get("task_number") or 0) == 12
                and str(x.get("topic") or "") != "essay_writing"
                and not x.get("options")
                for x in tasks
            )
            if not has_real_12:
                t["task_number"] = 13
                t["topic"] = "essay_writing"
        normalized_tasks.append(t)

    block = {
        "context_id": vid,
        "title": title,
        "description_text": build_context_description(
            listening=listening, grammar=grammar, reading=reading
        ),
        "audio_script": _opt_text(listening.get("audio_script"))
        or _opt_text(listening.get("text")),
        "audio_url": _opt_text(listening.get("audio_url") or listening.get("audio")),
        "grammar_content": _opt_text(grammar.get("content"))
        or _opt_text(grammar.get("text")),
        "reading_author": _opt_text(reading.get("author")),
        "reading_content": _opt_text(reading.get("content"))
        or _opt_text(reading.get("text")),
        "source_notes": _opt_text(variant.get("source_notes")),
    }

    title_prefix = TITLE_PREFIX_KIM if "kim" in vid else TITLE_PREFIX
    rows: list[dict[str, Any]] = []

    if listening:
        payload = _oge_rus_payload(kim_type=1, listening=listening)
        rows.append(
            {
                "task_number": 1,
                "part": 2,
                "prototype_title": _prototype_title(
                    variant_id=vid,
                    num=1,
                    topic="summary_writing",
                    title_prefix=title_prefix,
                ),
                "prompt_instruction": _prompt_for("summary_writing", 1),
                "template_text": _izlozhenie_template(listening),
                "template_answer": "Развёрнутый ответ (сжатое изложение)",
                "template_solution": (
                    "Критерии: ИК1 (микротемы), ИК2 (сжатие), ИК3 (смысловая цельность). "
                    f"Минимум слов: {int(listening.get('min_words') or 70)}."
                ),
                "difficulty": None,
                "answer_type": "detailed",
                "max_score": int(listening.get("max_score") or 7),
                "acceptable_answers": [],
                "figure_kind": None,
                "figure_params": payload,
                "context_id": vid,
                "source_id": _opt_text(listening.get("id")),
            }
        )

    for task in normalized_tasks:
        num = int(task["task_number"])
        if num == 1:
            continue
        topic = str(task.get("topic") or task.get("topic_id") or "task").strip()
        part = _part_for(num)
        matching = task.get("matching") if isinstance(task.get("matching"), dict) else None
        essay_opts = task.get("options") if isinstance(task.get("options"), list) else None

        if num == 13 or topic == "essay_writing":
            template_text = _essay_template(task)
            answer = "Развёрнутый ответ (сочинение)"
            max_score = int(task.get("max_score") or 7)
            part = 2
            topic = "essay_writing"
            payload = _oge_rus_payload(
                kim_type=13,
                reading=reading,
                essay_options=essay_opts,
                show_reading=False,
            )
        elif matching or topic == "punctuation_matching":
            template_text = _matching_statement(task)
            answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
            max_score = int(task.get("max_score") or 1)
            payload = _oge_rus_payload(kim_type=num, matching=matching)
        else:
            template_text = _opt_text(task.get("statement") or task.get("template_text"))
            answer = _opt_text(task.get("correct_answer") or task.get("template_answer"))
            max_score = int(task.get("max_score") or 1)
            payload = _oge_rus_payload(
                kim_type=num,
                grammar=grammar if num in (2, 3) else None,
                reading=reading if num in (10, 11, 12, 13) else None,
                show_grammar=(num == 2),
                show_reading=(num == 10),
            )

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
                "prototype_title": _prototype_title(
                    variant_id=vid, num=num, topic=topic, title_prefix=title_prefix
                ),
                "prompt_instruction": _prompt_for(topic, num),
                "template_text": template_text,
                "template_answer": answer,
                "template_solution": _opt_text(task.get("solution_hint")),
                "difficulty": _opt_text(task.get("difficulty")),
                "answer_type": "detailed" if part == 2 else "string",
                "max_score": max_score,
                "acceptable_answers": acceptable,
                "figure_kind": None,
                "figure_params": payload,
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
    if not (_opt_text(grammar.get("content")) or _opt_text(grammar.get("text"))):
        raise ValueError(f"{vid}: нужен grammar_text (отдельный текст для заданий 2–3)")
    return block, rows
