"""Автосборка оригинального варианта ОГЭ русский в банк (не в момент экзамена)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.scripts.oge_rus_convert import convert_variant

_ROOT = Path(__file__).resolve().parents[2]
_IMPORTS = _ROOT / "backend" / "universal" / "packs" / "oge_rus" / "imports"

_BANNED = (
    "хлорид натрия",
    "наилю",
    "наили",
    "универсального рецепта",
    "яковлев",
    "паустовск",
    "железников",
    "лиханов",
    "казаков ю",
)

_TEMAS = (
    "память",
    "труд",
    "слово",
    "дом",
    "дорога",
    "музыка",
    "учитель",
    "совесть",
    "зима",
    "письмо",
)

_SYSTEM = (
    "Ты составляешь оригинальный учебный КИМ ОГЭ русский 1–13. "
    "Не копируй ФИПИ, Решу ОГЭ, Сдам ГИА. Верни только JSON-объект."
)


def _user_prompt(tema: str, variant_id: str) -> str:
    return f"""Тема: {tema}
variant_id: {variant_id}

JSON-схема (заполни целиком):
{{
  "variant_id": "{variant_id}",
  "title": "ОГЭ · Русский · {tema}",
  "source_notes": "Оригинальный учебный вариант. Не ФИПИ.",
  "listening_text": {{
    "id": "izl_{variant_id}",
    "title": "Текст, начинающийся словами «…»",
    "author": "Учебный текст",
    "audio_script": "3 абзаца, 180-250 слов, 3 микротемы, без (1)(2)",
    "min_words": 70,
    "max_score": 7
  }},
  "grammar_text": {{
    "id": "grammar_{variant_id}",
    "content": "(1) … (2) … (3) … (4) … (5) … факт, не сюжет"
  }},
  "reading_text": {{
    "id": "text_{variant_id}",
    "author": "Учебный текст",
    "note": "",
    "content": "(1)…(35) свой рассказ, 32-40 предложений, финал — мораль"
  }},
  "tasks": [
    {{"task_number": 2, "topic": "syntax_basis", "statement": "5 пунктов основ по grammar, часть неверных", "correct_answer": "345", "max_score": 1, "solution_hint": ""}},
    {{"task_number": 3, "topic": "syntax_analysis", "statement": "5 утверждений о grammar", "correct_answer": "123", "max_score": 1, "solution_hint": ""}},
    {{"task_number": 4, "topic": "punctuation_matching", "statement": "Установите соответствие…", "matching": {{"left": [{{"id":"А","text":"правило"}},{{"id":"Б","text":"правило"}},{{"id":"В","text":"правило"}}], "right": [{{"id":"1","text":"пример"}},{{"id":"2","text":"пример"}},{{"id":"3","text":"пример"}},{{"id":"4","text":"лишний"}},{{"id":"5","text":"лишний"}}]}}, "correct_answer": "123", "max_score": 1, "solution_hint": "А→1 Б→2 В→3"}},
    {{"task_number": 5, "topic": "punctuation_placement", "statement": "Расставьте знаки… предложение с (1)(2)(3)", "correct_answer": "12", "max_score": 1, "solution_hint": ""}},
    {{"task_number": 6, "topic": "spelling_explanation", "statement": "5 слов + объяснение, 1-2 неверных", "correct_answer": "13", "max_score": 1, "solution_hint": ""}},
    {{"task_number": 7, "topic": "spelling_letters", "statement": "пропуски (1).. буква И или Е", "correct_answer": "13", "max_score": 1, "solution_hint": ""}},
    {{"task_number": 8, "topic": "grammar_form", "statement": "форма слова в скобках", "correct_answer": "слово", "acceptable_answers": ["слово"], "max_score": 1, "solution_hint": ""}},
    {{"task_number": 9, "topic": "phrase_transformation", "statement": "управление → согласование", "correct_answer": "…", "acceptable_answers": ["…"], "max_score": 1, "solution_hint": ""}},
    {{"task_number": 10, "topic": "text_comprehension", "statement": "5 тезисов по рассказу, 2 ложных", "correct_answer": "135", "max_score": 1, "solution_hint": ""}},
    {{"task_number": 11, "topic": "expressive_means", "statement": "5 цитат, сравнение или метафора", "correct_answer": "24", "max_score": 1, "solution_hint": ""}},
    {{"task_number": 12, "topic": "lexical_analysis", "statement": "в предложениях N-M найдите слово…", "correct_answer": "слово", "acceptable_answers": ["слово"], "max_score": 1, "solution_hint": ""}},
    {{"task_number": 13, "topic": "essay_writing", "options": [
      {{"type": "13.1", "title": "Лингвистическое сочинение", "statement": "вопрос про язык текста, ≥70 слов"}},
      {{"type": "13.2", "title": "Сочинение по цитате", "statement": "смысл финала: точная цитата из конца рассказа"}},
      {{"type": "13.3", "title": "Сочинение на морально-этическую тему", "statement": "Что такое …?"}}
    ], "max_score": 7, "solution_hint": "Одно из 13.1–13.3"}}
  ]
}}

Правила: ключи 2–7 и 10–11 — цифры по возрастанию без пробелов; 4 — три цифры АБВ; рассказ 32–40 номеров (1)…; изложение без номеров; три текста разные; не используй соль/Наилю/Яковлева/«Универсального рецепта»."""


def _extract_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("В ответе модели нет JSON")
    data = json.loads(text[start : end + 1])
    if not isinstance(data, dict):
        raise ValueError("JSON должен быть объектом")
    return data


def _blob(variant: dict[str, Any]) -> str:
    return json.dumps(variant, ensure_ascii=False).lower()


def validate_variant(variant: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    blob = _blob(variant)
    for bad in _BANNED:
        if bad in blob:
            errors.append(f"похоже на чужой банк: {bad}")
    reading = ""
    rt = variant.get("reading_text")
    if isinstance(rt, dict):
        reading = str(rt.get("content") or "")
    n_sent = len(re.findall(r"\(\d+\)", reading))
    if n_sent < 28:
        errors.append(f"в рассказе мало предложений: {n_sent} (нужно ≥32)")
    listen = ""
    lt = variant.get("listening_text")
    if isinstance(lt, dict):
        listen = str(lt.get("audio_script") or lt.get("text") or "")
    words = len(re.findall(r"[А-Яа-яЁёA-Za-z]+", listen))
    if words < 120:
        errors.append(f"изложение короткое: {words} слов")
    try:
        convert_variant(variant)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


def _unique_id(tema: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", tema.lower())
    if len(slug) < 3:
        slug = datetime.now().strftime("a%m%d%H%M")
    base = f"oge_rus_var_{slug[:20]}"
    cid = base
    n = 2
    while (_IMPORTS / f"{cid}.json").is_file() or (
        _ROOT / "backend" / "universal" / "packs" / "oge_rus" / "context_blocks" / f"{cid}.json"
    ).is_file():
        cid = f"{base}_{n}"
        n += 1
    return cid


async def draft_variant(tema: str) -> dict[str, Any]:
    from backend.universal.variant_builder import _call_llm

    vid = _unique_id(tema)
    raw = await _call_llm(_SYSTEM, _user_prompt(tema, vid), timeout=180.0)
    variant = _extract_json(raw)
    variant["variant_id"] = vid
    variant.setdefault("title", f"ОГЭ · Русский · {tema}")
    variant.setdefault("source_notes", "Оригинальный учебный вариант. Автосборка.")
    errors = validate_variant(variant)
    if errors:
        fix = (
            "Исправь JSON. Ошибки:\n- "
            + "\n- ".join(errors[:8])
            + "\nВерни только исправленный JSON целиком."
        )
        raw2 = await _call_llm(_SYSTEM, fix + "\n\n" + json.dumps(variant, ensure_ascii=False), timeout=180.0)
        variant = _extract_json(raw2)
        variant["variant_id"] = vid
        errors = validate_variant(variant)
        if errors:
            raise RuntimeError("Модель не собрала валидный вариант: " + "; ".join(errors[:6]))
    return variant


def save_import(variant: dict[str, Any]) -> Path:
    _IMPORTS.mkdir(parents=True, exist_ok=True)
    vid = str(variant.get("variant_id") or "oge_rus_var_auto")
    path = _IMPORTS / f"{vid}.json"
    path.write_text(json.dumps(variant, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


async def _make_audio(variant: dict[str, Any]) -> str | None:
    from backend.scripts.generate_oge_rus_audio import (
        AUDIO_DIR,
        _audio_url_for,
        _seed_pg,
        _set_audio_url_on_block,
        _slug,
        _synth,
    )

    listen = variant.get("listening_text") if isinstance(variant.get("listening_text"), dict) else {}
    text = str(listen.get("audio_script") or listen.get("text") or "").strip()
    if len(text) < 40:
        return None
    cid = str(variant.get("variant_id") or "")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    mp3 = AUDIO_DIR / f"{_slug(cid)}.mp3"
    ok, engine = await _synth(text, mp3)
    if not ok:
        return None
    url = _audio_url_for(mp3, cid, engine=engine)
    listen["audio_url"] = url
    variant["listening_text"] = listen
    save_import(variant)
    ctx = (
        _ROOT
        / "backend"
        / "universal"
        / "packs"
        / "oge_rus"
        / "context_blocks"
        / f"{cid}.json"
    )
    if ctx.is_file():
        block = json.loads(ctx.read_text(encoding="utf-8"))
        _set_audio_url_on_block(block, url)
        ctx.write_text(json.dumps(block, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        _seed_pg(cid, url)
    except Exception:
        pass
    return url


async def autogen_one(*, tema: str | None = None, audio: bool = True, seed: bool = True) -> dict[str, Any]:
    tema = (tema or "").strip() or _TEMAS[datetime.now().timetuple().tm_yday % len(_TEMAS)]
    variant = await draft_variant(tema)
    path = save_import(variant)
    seed_info = None
    if seed:
        from backend.scripts.import_oge_rus_variants import run as import_run

        seed_info = import_run(json_path=path, skip_seed=False)
    audio_url = None
    if audio:
        audio_url = await _make_audio(variant)
    return {
        "ok": True,
        "variant_id": variant.get("variant_id"),
        "title": variant.get("title"),
        "tema": tema,
        "import_json": str(path),
        "audio_url": audio_url,
        "seed": seed_info,
    }


async def autogen_many(count: int = 1, *, tema: str | None = None) -> dict[str, Any]:
    n = max(1, min(int(count or 1), 3))
    made: list[dict[str, Any]] = []
    errors: list[str] = []
    for i in range(n):
        t = tema if tema else _TEMAS[(datetime.now().timetuple().tm_yday + i) % len(_TEMAS)]
        try:
            made.append(await autogen_one(tema=t))
        except Exception as exc:
            errors.append(f"{t}: {exc}")
    return {"ok": bool(made), "created": made, "errors": errors}
