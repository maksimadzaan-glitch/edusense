"""Адаптер universal PG-варианта → QuestionOut для teacher /api/ai/generate."""



from __future__ import annotations



import re
from typing import Any

from sqlalchemy import and_, func, select

from backend.db.pg import is_postgres_configured, session_factory

from backend.db.pg_models import TaskPrototype

from backend.services.figures import attach_figure, strip_math_figures

from backend.services.prompts import canonicalize_questions, polish_answer_key, polish_fipi_text


# Сырые id контекстов → человекочитаемая тема в UI (если title ещё «ctx:…»).
_CTX_TOPIC_FALLBACK = {
    "ctx:apt": "План квартиры",
    "ctx:dacha": "План участка",
    "ctx:tires": "Автомобильные шины",
    "apartment_2room": "План квартиры",
    "dacha_sosnovoe": "План участка",
    "tires_factory": "Автомобильные шины",
    "plan_uchastka_01": "План участка",
    "plan_dvor_01": "План местности",
    "stove_bath_01": "Печи для бани",
    "paper_sheets_01": "Листы бумаги",
    "bus_route_01": "Маршруты",
    "tariffs_mobile_01": "Тарифы связи",
    "umbrellas_shop_01": "Таблица товаров",
    "credit_deposit_01": "Вклад и кредит",
    "car_fuel_01": "Маршруты и топливо",
    "greenhouse_beds_01": "План участка",
    "linoleum_repair_01": "План квартиры",
    "parking_grid_01": "План местности",
    "izlozhenie_01": "Сжатое изложение",
    "text_read_01": "Текст для чтения",
}

OGE_MATH_SLOT_TOPICS = {
    1: "Практический блок",
    2: "Практический блок",
    3: "Практический блок",
    4: "Практический блок",
    5: "Практический блок",
    6: "Вычисления и дроби",
    7: "Числовая прямая",
    8: "Степени и корни",
    9: "Уравнения",
    10: "Теория вероятностей",
    11: "Графики функций",
    12: "Расчёты по формулам",
    13: "Неравенства",
    14: "Прогрессии",
    15: "Треугольники",
    16: "Окружность",
    17: "Четырёхугольники",
    18: "Клетчатая бумага",
    19: "Геометрические утверждения",
    20: "Уравнения и системы",
    21: "Текстовая задача",
    22: "График с параметром",
    23: "Геометрия на вычисление",
    24: "Геометрия на доказательство",
    25: "Сложная геометрия",
}

_EN_TOPIC_RU = {
    "practical_context_matching": "Сопоставление объектов плана",
    "practical_context_tiles": "Тротуарная плитка",
    "practical_context_area": "Площадь объекта",
    "practical_context_distance": "Расстояние по плану",
    "practical_context_choice": "Выбор выгодного варианта",
    "finish_v1": "План участка",
    "matching": "Сопоставление",
    "tiles": "Плитка",
    "area": "Площадь",
    "distance": "Расстояние",
    "choice": "Выбор",
    "lamps": "лампы",
    "slot": "Задание",
    "etalon": "Эталон",
    "mutator": "задание",
}


def _mostly_latin(text: str) -> bool:
    letters = re.findall(r"[A-Za-zА-Яа-яЁё]", text or "")
    if not letters:
        return False
    latin = sum(1 for c in letters if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    return latin / len(letters) > 0.45


def human_topic_from_title(title: str, task_number: int | None = None) -> str:
    """Тема для учителя/ученика: без сырых id и английских slug."""
    raw = str(title or "Задание").strip() or "Задание"
    low = raw.casefold()
    for en, ru in _EN_TOPIC_RU.items():
        if en in low:
            raw = re.sub(re.escape(en), ru, raw, flags=re.I)
    if "·" in raw:
        left, right = (p.strip() for p in raw.split("·", 1))
    else:
        left, right = raw, ""

    key = left.lower()
    if key in _CTX_TOPIC_FALLBACK:
        return _CTX_TOPIC_FALLBACK[key]

    id_like = bool(re.match(r"^(ctx|context)[:_]", left, re.I)) or bool(
        re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+", left)
    )
    if id_like:
        if right:
            human = re.sub(r"^\d+[a-z]?\s+", "", right, flags=re.I).strip()
            human = human.lstrip("· ").strip()
            if human and not _mostly_latin(human):
                return human
        if task_number and task_number in OGE_MATH_SLOT_TOPICS:
            return OGE_MATH_SLOT_TOPICS[task_number]
        return "Практическая задача"

    cleaned = re.sub(r"^[0-9]+[a-z]?\s*:\s*", "", left, flags=re.I).strip()
    if cleaned.casefold() in {"мутатор", "mutator"}:
        cleaned = (right.split("·")[0].strip() if right else "") or cleaned
        if task_number and task_number in OGE_MATH_SLOT_TOPICS:
            cleaned = OGE_MATH_SLOT_TOPICS[task_number]
    if _mostly_latin(cleaned):
        if task_number and task_number in OGE_MATH_SLOT_TOPICS:
            return OGE_MATH_SLOT_TOPICS[task_number]
        if right and not _mostly_latin(right):
            return right.split("·")[0].strip()
    return cleaned or left





def pg_has_ready_templates(subject_code: str, exam_code: str) -> bool:
    """True, если в PG есть хотя бы один прототип с template_text+answer для пары."""
    if not is_postgres_configured():
        return False
    sc = (subject_code or "").strip()
    ec = (exam_code or "").strip().upper()
    if not sc or not ec:
        return False
    try:
        SessionLocal = session_factory()
        db = SessionLocal()
        try:
            n = db.scalar(
                select(func.count())
                .select_from(TaskPrototype)
                .where(
                    and_(
                        TaskPrototype.subject_code == sc,
                        TaskPrototype.exam_code == ec,
                        TaskPrototype.template_text.isnot(None),
                        TaskPrototype.template_answer.isnot(None),
                        func.length(func.trim(TaskPrototype.template_text)) > 0,
                        func.length(func.trim(TaskPrototype.template_answer)) > 0,
                    )
                )
            )
            return int(n or 0) > 0
        finally:
            db.close()
    except Exception as exc:
        # Не маскируем под «нет шаблонов» — иначе путает с пустым банком
        import logging

        logging.getLogger(__name__).warning("pg_has_ready_templates(%s, %s): %s", sc, ec, exc)
        return False





def universal_variant_to_questions(

    variant: dict[str, Any],

    *,

    count: int | None = None,

    slots: list[int] | None = None,

) -> list[dict[str, Any]]:

    """Преобразовать ответ generate_variant в список dict для QuestionOut."""

    tasks = list(variant.get("tasks") or [])

    tasks.sort(key=lambda t: int(t.get("task_number") or 0))

    if slots:

        want = {int(s) for s in slots if int(s) > 0}

        tasks = [t for t in tasks if int(t.get("task_number") or 0) in want]

    elif count is not None and count > 0:

        tasks = tasks[: int(count)]



    subject_code = str(variant.get("subject_code") or "").strip().lower()

    exam_code = str(variant.get("exam_code") or "").strip().upper()

    oge_math = subject_code == "math" and exam_code == "OGE"
    oge_rus = subject_code in ("russian", "rus", "ru") and exam_code == "OGE"
    variant_etalon = bool(variant.get("etalon"))

    questions: list[dict[str, Any]] = []

    for i, t in enumerate(tasks, start=1):

        part = int(t.get("part") or 1)

        title = str(t.get("prototype_title") or "Задание").strip() or "Задание"
        payload_raw = t.get("payload") if isinstance(t.get("payload"), dict) else {}
        task_number = int(t.get("task_number") or i)
        payload_title = str(payload_raw.get("title") or "").strip()
        if payload_title and not _mostly_latin(payload_title):
            topic = payload_title
        else:
            topic = human_topic_from_title(title, task_number)
        is_etalon = (
            variant_etalon
            or bool(t.get("etalon"))
            or bool(payload_raw.get("etalon"))
        )

        # ОГЭ русский / эталон — без polish (сохраняем (1)(2)… и формулировки)
        if oge_rus or is_etalon:
            text = str(t.get("text") or "").strip()
            topic_out = topic
            answer = str(t.get("answer") or "")
        else:
            text = polish_fipi_text(str(t.get("text") or ""))
            topic_out = polish_fipi_text(topic)
            answer = polish_answer_key(str(t.get("answer") or ""), part=part)

        if not text:

            continue

        # эталон / ОГЭ — номера КИМ; иначе подряд 1..N для UI
        display_num = task_number if (oge_rus or oge_math or is_etalon) else i
        kim_type = task_number if oge_rus else None
        type_label = (
            f"Тип {kim_type}" if oge_rus and kim_type else (
                "Развёрнутый ответ" if part == 2 else "Краткий ответ"
            )
        )

        row: dict[str, Any] = {

            "num": display_num,

            "part": part,

            "type": type_label,

            "topic": topic_out,

            "section": None,

            "text": text,

            "answer": answer,

            "max_score": (
                int(t["max_score"]) if t.get("max_score") is not None else (2 if part == 2 else 1)
            ),

            "needs_figure": False,

            "figure_kind": t.get("figure_kind"),

            "figure_params": t.get("figure_params"),

            "task_number": task_number,

            "subject_code": subject_code,

            "exam_code": exam_code,

            "_slot": task_number,

            "_oge_math_figures": oge_math,

        }

        # kim_order — маркер UI ОГЭ русский; math-эталон хранит номера КИМ в num/task_number
        if oge_rus:
            row["kim_order"] = True
            row["_kim_order"] = True

        payload = t.get("payload") if isinstance(t.get("payload"), dict) else None
        if oge_rus:
            # Даже если в PG нет figure_params — отдаём минимальный payload для UI
            base = dict(payload or {})
            base.setdefault("oge_rus", True)
            base.setdefault("kim_type", task_number)
            base.setdefault("ui", base.get("ui") or "oge_rus")
            if is_etalon:
                base["etalon"] = True
            row["payload"] = base
        elif isinstance(payload, dict):
            row["payload"] = dict(payload)
            if is_etalon:
                row["payload"]["etalon"] = True
        elif is_etalon:
            row["payload"] = {"etalon": True}

        if t.get("figure_data") is not None:
            row["figure_data"] = t.get("figure_data")
        if t.get("figure_svg"):
            row["figure_svg"] = t.get("figure_svg")
        if t.get("_figure_pack"):
            row["_figure_pack"] = t.get("_figure_pack")
        elif oge_math and (
            t.get("figure_data") is not None
            or str(t.get("figure_kind") or "").strip().lower() == "asset"
        ):
            row["_figure_pack"] = "oge_math"

        if t.get("context_id"):
            row["context_id"] = t["context_id"]

        acc = t.get("acceptable_answers")
        if acc is not None:
            row["acceptable_answers"] = acc

        # solution / solution_hint — учителю на карточке; ученику не отдаём
        sol = str(t.get("solution") or "").strip()
        if sol:
            row["solution"] = sol

        if part == 2 and sol and not answer and not is_etalon:

            row["answer"] = polish_answer_key(sol, part=2)

        fig = strip_math_figures(row) if oge_rus else attach_figure(row)
        questions.append(fig)

    if oge_math:
        fold_oge_math_context_group(questions)

    if oge_rus:
        # Добить listening/grammar/reading из context_blocks, если payload урезан
        _fill_questions_oge_rus_from_contexts(
            questions, subject_code=subject_code, exam_code=exam_code
        )
        # Скопировать grammar/reading между слотами (старые seed без grammar на №3)
        _enrich_questions_oge_rus_shared(questions)
        try:
            from backend.universal.variant_builder import oge_rus_bank_meta

            bank_meta = None
            for q in questions:
                bank_meta = oge_rus_bank_meta(q.get("context_id"))
                if bank_meta:
                    break
                p0 = q.get("payload") if isinstance(q.get("payload"), dict) else {}
                if p0.get("bank_label"):
                    bank_meta = {
                        "code": p0.get("bank_code"),
                        "label": p0.get("bank_label"),
                        "name": p0.get("bank_name"),
                        "num": p0.get("bank_num"),
                        "band": p0.get("bank_band"),
                    }
                    break
            if bank_meta:
                for q in questions:
                    p = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
                    p.setdefault("bank_code", bank_meta.get("code"))
                    p.setdefault("bank_label", bank_meta.get("label"))
                    p.setdefault("bank_name", bank_meta.get("name"))
                    p.setdefault("bank_num", bank_meta.get("num"))
                    p.setdefault("bank_band", bank_meta.get("band"))
                    q["payload"] = p
        except Exception:
            pass

    for fig in questions:
        for k in (
            "figure_params",
            "figure_data",
            "task_number",
            "subject_code",
            "exam_code",
            "_slot",
            "_oge_math_figures",
            "_figure_pack",
            "context_id",
            "_kim_order",
        ):
            fig.pop(k, None)

    return canonicalize_questions(questions)


def _slot_num(q: dict[str, Any]) -> int:
    try:
        return int(q.get("num") or q.get("task_number") or 0)
    except (TypeError, ValueError):
        return 0


def fold_oge_math_context_group(questions: list[dict[str, Any]]) -> None:
    """Сюжет и чертёж 1–5 один раз в payload.math_context, не на каждой карточке."""
    from backend.universal.variant_builder import (
        OGE_MATH_CONTEXT_SLOTS,
        math_asset_id,
        strip_shared_story,
    )

    group = [q for q in questions if _slot_num(q) in OGE_MATH_CONTEXT_SLOTS]
    if len(group) < 2:
        return
    group.sort(key=_slot_num)
    first = group[0]
    p0 = first.get("payload") if isinstance(first.get("payload"), dict) else {}
    story = str(p0.get("shared_story") or "").strip()
    if not story:
        for q in group:
            pq = q.get("payload") if isinstance(q.get("payload"), dict) else {}
            story = str(pq.get("shared_story") or "").strip()
            if story:
                break
    title = str(p0.get("context_title") or first.get("topic") or "").strip()
    cid = str(
        p0.get("context_id") or first.get("context_id") or ""
    ).strip()
    svg = ""
    kind = None
    params = None
    for q in group:
        if not svg and str(q.get("figure_svg") or "").strip():
            svg = str(q.get("figure_svg") or "").strip()
            kind = q.get("figure_kind")
        pq = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        if not title:
            title = str(pq.get("context_title") or "").strip()
        if not cid:
            cid = str(pq.get("context_id") or q.get("context_id") or "").strip()
        fp = q.get("figure_params")
        if isinstance(fp, dict) and params is None:
            params = fp
    asset = str(p0.get("asset_id") or "").strip() or (
        math_asset_id(kind, params if isinstance(params, dict) else None) or ""
    )
    http_asset = asset.lower().startswith("http://") or asset.lower().startswith(
        "https://"
    )
    base_vars = p0.get("base_vars") if isinstance(p0.get("base_vars"), dict) else {}
    if not base_vars and isinstance(params, dict) and isinstance(params.get("base_vars"), dict):
        base_vars = dict(params["base_vars"])
    math_context = {
        "group_id": cid or "math_oge_1_5",
        "title": title,
        "story_text": story,
        "asset_id": asset or None,
        "base_vars": base_vars,
        "figure_kind": None if http_asset else (kind or ("asset" if svg else None)),
        "figure_svg": None if http_asset else (svg or None),
        "figure_url": asset if http_asset else None,
    }
    for q in group:
        p = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
        if story:
            p.setdefault("shared_story", story)
        if title:
            p.setdefault("context_title", title)
        if cid:
            p.setdefault("context_id", cid)
        if asset:
            p.setdefault("asset_id", asset)
        if base_vars:
            p.setdefault("base_vars", base_vars)
        p["math_context"] = math_context
        q["payload"] = p
        q["figure_svg"] = None
        q["figure_kind"] = None
        q.pop("solution_figure_svg", None)
        etalon = bool(q.get("etalon") or p.get("etalon"))
        if story and not etalon:
            q["text"] = strip_shared_story(str(q.get("text") or ""), story)


def _fill_questions_oge_rus_from_contexts(
    questions: list[dict[str, Any]],
    *,
    subject_code: str,
    exam_code: str,
) -> None:
    """Если grammar/listening/reading нет в payload — взять из description_text контекста."""
    ctx_ids = {
        str(q.get("context_id")).strip()
        for q in questions
        if q.get("context_id")
    }
    if not ctx_ids or not is_postgres_configured():
        return
    try:
        from backend.universal.variant_builder import (
            _context_description_map,
            _fill_oge_rus_shared_from_context,
        )

        db = session_factory()()
        try:
            descs = _context_description_map(
                db,
                subject_code=subject_code,
                exam_code=exam_code,
                context_ids=ctx_ids,
            )
        finally:
            db.close()
    except Exception:
        return
    if not descs:
        return
    for q in questions:
        cid = str(q.get("context_id") or "").strip()
        desc = descs.get(cid)
        if not desc:
            continue
        try:
            num = int(q.get("num") or q.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        base = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {
            "oge_rus": True,
            "kim_type": num,
            "ui": "oge_rus",
        }
        q["payload"] = _fill_oge_rus_shared_from_context(
            base, task_number=num, context_desc=desc
        )


def _enrich_questions_oge_rus_shared(questions: list[dict[str, Any]]) -> None:
    from backend.universal.variant_builder import _resolve_oge_rus_audio_url

    grammar = None
    reading = None
    listening = None
    audio_url = None
    for q in questions:
        try:
            num = int(q.get("num") or q.get("task_number") or 0)
        except (TypeError, ValueError):
            num = 0
        p = q.get("payload") if isinstance(q.get("payload"), dict) else {}
        if num in (2, 3) and not grammar and p.get("grammar_text"):
            grammar = str(p["grammar_text"])
        if num in (10, 11, 12, 13) and not reading and p.get("reading_text"):
            reading = str(p["reading_text"])
        if num == 1 and not listening and p.get("listening_text"):
            listening = str(p["listening_text"])
        if num == 1 and not audio_url and p.get("audio_url"):
            audio_url = str(p["audio_url"])
    for q in questions:
        try:
            num = int(q.get("num") or q.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        p = dict(q.get("payload") or {}) if isinstance(q.get("payload"), dict) else {}
        p.setdefault("oge_rus", True)
        p.setdefault("kim_type", num)
        cid = str(q.get("context_id") or p.get("context_id") or "").strip()
        if cid:
            p["context_id"] = cid
        if num == 1 and listening:
            p.setdefault("listening_text", listening)
            p.setdefault("ui", "listening")
            resolved = _resolve_oge_rus_audio_url(cid or q.get("context_id"), p.get("audio_url") or audio_url)
            if resolved:
                p["audio_url"] = resolved
            else:
                p.pop("audio_url", None)
        if num in (2, 3) and grammar:
            p["grammar_text"] = grammar
            if num == 2:
                p.setdefault("show_shared", "grammar")
        if num in (10, 11, 12, 13) and reading:
            p.setdefault("reading_text", reading)
            if num == 10:
                p.setdefault("show_shared", "reading")
        if p:
            q["payload"] = p


