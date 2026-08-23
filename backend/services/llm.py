"""Фасад генерации: gigachat (по умолчанию) | deepseek."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from backend.services import deepseek, gigachat
from backend.services.prompts import build_missing_slots_prompt
from backend.services.subject_blueprints import slot_part

AI_PROVIDER = os.getenv("AI_PROVIDER", "gigachat").strip().lower()

# сколько слотов просим у LLM за один запрос
_SLOT_BATCH = 6


class LLMError(RuntimeError):
    pass


async def _call_provider(
    *,
    exam: str,
    subject: str,
    difficulty: str,
    count: int,
    user_prompt: str | None = None,
) -> list[dict[str, Any]]:
    provider = AI_PROVIDER or "gigachat"
    try:
        if provider == "deepseek":
            return await deepseek.generate_questions(
                exam=exam,
                subject=subject,
                difficulty=difficulty,
                count=count,
                user_prompt=user_prompt,
            )
        if provider in {"gigachat", "giga", "sber"}:
            return await gigachat.generate_questions(
                exam=exam,
                subject=subject,
                difficulty=difficulty,
                count=count,
                user_prompt=user_prompt,
            )
        raise LLMError(f"Неизвестный AI_PROVIDER: {provider}. Используйте gigachat|deepseek")
    except (gigachat.GigaChatError, deepseek.DeepSeekError) as exc:
        raise LLMError(str(exc)) from exc


async def generate_questions(
    *,
    exam: str,
    subject: str,
    difficulty: str = "medium",
    count: int = 4,
) -> list[dict[str, Any]]:
    return await _call_provider(
        exam=exam, subject=subject, difficulty=difficulty, count=count
    )


async def generate_questions_for_slots(
    *,
    exam: str,
    subject: str,
    difficulty: str = "medium",
    slots: list[int],
) -> list[dict[str, Any]]:
    """Сгенерировать задания строго для указанных номеров КИМ (батчами)."""
    if not slots:
        return []
    ordered = sorted({int(s) for s in slots if int(s) > 0})
    out: list[dict[str, Any]] = []

    for i in range(0, len(ordered), _SLOT_BATCH):
        batch = ordered[i : i + _SLOT_BATCH]
        prompt = build_missing_slots_prompt(
            exam=exam, subject=subject, difficulty=difficulty, slots=batch
        )
        try:
            qs = await _call_provider(
                exam=exam,
                subject=subject,
                difficulty=difficulty,
                count=len(batch),
                user_prompt=prompt,
            )
        except LLMError:
            continue

        # сопоставить по num / порядку
        by_num: dict[int, dict[str, Any]] = {}
        for q in qs:
            try:
                num = int(q.get("num") or 0)
            except (TypeError, ValueError):
                num = 0
            if num in batch and num not in by_num:
                by_num[num] = q

        unused = [q for q in qs if int(q.get("num") or 0) not in by_num]
        for slot in batch:
            if slot in by_num:
                q = by_num[slot]
            elif unused:
                q = unused.pop(0)
            else:
                continue
            q["num"] = slot
            q["part"] = int(slot_part(exam=exam, subject=subject, slot=slot))
            q["_slot"] = slot
            out.append(q)

    return out


async def enrich_bank_from_ai(
    db: Any,
    *,
    exam: str,
    subject: str,
    slots: list[int],
    difficulty: str = "medium",
    per_slot: int = 2,
) -> dict[str, Any]:
    """Сгенерировать кандидатов для слотов и вставить в bank_tasks при чистом разборе.

    Полезно для постепенного наполнения предметов. Не светит «банк» наружу.
    """
    from backend.services.bank import insert_bank_tasks

    want: list[int] = []
    for s in slots:
        want.extend([int(s)] * max(1, min(int(per_slot), 3)))

    generated = await generate_questions_for_slots(
        exam=exam, subject=subject, difficulty=difficulty, slots=want
    )
    # нормализуем slot
    for q in generated:
        q["slot"] = int(q.get("_slot") or q.get("num") or 0)
        q["difficulty"] = difficulty

    inserted = insert_bank_tasks(
        db, exam=exam, subject=subject, tasks=generated, source_tag_prefix="ai"
    )
    return {
        "requested_slots": sorted(set(int(s) for s in slots)),
        "generated": len(generated),
        "inserted": inserted,
    }


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise LLMError("Модель не вернула JSON")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise LLMError("JSON ответа не объект")
    return data


async def complete_json(
    *,
    system: str,
    user: str,
    temperature: float = 0.15,
    image_data_url: Optional[str] = None,
) -> dict[str, Any]:
    """Один JSON-объект от текущего провайдера. Фото уходит в GigaChat (attachments)."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    photo = str(image_data_url or "").strip() or None
    provider = (AI_PROVIDER or "gigachat").strip().lower()
    use_giga_vision = bool(photo and os.getenv("GIGACHAT_CREDENTIALS", "").strip())
    try:
        if use_giga_vision or provider in {"gigachat", "giga", "sber"}:
            kwargs: dict[str, Any] = {"temperature": temperature}
            if photo:
                kwargs["image_data_url"] = photo
            content = await gigachat.chat_content(messages, **kwargs)
        elif provider == "deepseek":
            content = await deepseek.chat_content(messages, temperature=temperature)
        else:
            content = await gigachat.chat_content(messages, temperature=temperature)
    except (gigachat.GigaChatError, deepseek.DeepSeekError) as exc:
        raise LLMError(str(exc)) from exc
    try:
        return _extract_json_object(content)
    except Exception as exc:
        raise LLMError(f"Не удалось разобрать ответ ИИ: {exc}") from exc
