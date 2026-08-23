"""Лёгкая вариация заданий банка через LLM (числа/формулировки) с откатом к оригиналу."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

from backend.services import gigachat
from backend.services.llm import AI_PROVIDER

# выключить: BANK_VARY=0
_VARY_ENABLED = os.getenv("BANK_VARY", "1").strip().lower() not in {"0", "false", "no", "off"}


def _llm_ready() -> bool:
    provider = (AI_PROVIDER or "gigachat").strip().lower()
    if provider == "deepseek":
        return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())
    return bool(os.getenv("GIGACHAT_CREDENTIALS", "").strip())


def _norm_answer(s: str) -> str:
    t = (s or "").strip().lower().replace(",", ".")
    t = re.sub(r"\s+", "", t)
    return t


def _looks_valid(original: dict[str, Any], varied: dict[str, Any]) -> bool:
    text = str(varied.get("text") or "").strip()
    answer = str(varied.get("answer") or "").strip()
    if len(text) < 8 or not answer:
        return False
    # запрет сломанного LaTeX / мусора
    bad = ("\\begin", "\\frac", "$", "```", "{cases}")
    if any(b in text for b in bad):
        return False
    part = int(original.get("part") or 1)
    if part == 1 and len(answer) > 80:
        return False
    # ответ должен быть «ключом», не эссе
    if "\n" in answer and part == 1:
        return False
    return True


async def _chat_json(prompt: str) -> Optional[str]:
    """Один короткий запрос к активному провайдеру; None если недоступен."""
    provider = (AI_PROVIDER or "gigachat").strip().lower()
    system = (
        "Ты помощник по школьным заданиям ЕГЭ/ОГЭ. "
        "Отвечай ТОЛЬКО валидным JSON без markdown."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    try:
        if provider == "deepseek":
            # deepseek не экспортирует низкоуровневый chat — пропускаем вариацию
            return None
        if provider in {"gigachat", "giga", "sber"}:
            import httpx

            async with httpx.AsyncClient(timeout=45.0, verify=gigachat._verify()) as client:
                token = await gigachat.get_access_token(client)
                payload = {
                    "model": gigachat.GIGACHAT_MODEL,
                    "messages": messages,
                    "temperature": 0.35,
                    "stream": False,
                }
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                response = await client.post(
                    f"{gigachat.GIGACHAT_BASE_URL}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code >= 400:
                    return None
                body = response.json()
                return body["choices"][0]["message"]["content"]
    except Exception:
        return None
    return None


def _extract_json_array(raw: str) -> Optional[list]:
    if not raw:
        return None
    text = raw.strip()
    # срезать markdown fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else None
    except json.JSONDecodeError:
        m = re.search(r"\[[\s\S]*\]", text)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
            return data if isinstance(data, list) else None
        except json.JSONDecodeError:
            return None


async def vary_questions(questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Лёгкая вариация: слегка меняет числа/формулировки, сохраняет структуру ответа.
    При любой ошибке или битом результате — исходные задания.
    """
    if not questions or not _VARY_ENABLED or not _llm_ready():
        return questions

    # не раздуваем latency: максимум 12 заданий за раз
    batch = questions[:12]
    payload = [
        {
            "i": i,
            "text": q.get("text"),
            "answer": q.get("answer"),
            "part": int(q.get("part") or 1),
            "topic": q.get("topic"),
        }
        for i, q in enumerate(batch)
    ]
    prompt = (
        "Ниже JSON-массив школьных заданий. Для каждого слегка измени формулировку "
        "и/или числа так, чтобы задание осталось того же типа и сложности. "
        "Пересчитай answer, чтобы он был ВЕРНЫМ для нового условия. "
        "Не меняй тип ответа (краткий ключ / развёрнутый ключ). "
        "Формулы только школьные: 3x²−4x+5, √(x+1), [[2|3]]. Без LaTeX \\begin/\\frac/$.\n"
        "Верни JSON-массив той же длины: [{\"i\":0,\"text\":\"...\",\"answer\":\"...\"}, ...]\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )

    raw = await _chat_json(prompt)
    arr = _extract_json_array(raw or "")
    if not arr or len(arr) != len(batch):
        return questions

    by_i: dict[int, dict[str, Any]] = {}
    for item in arr:
        if not isinstance(item, dict):
            continue
        try:
            i = int(item.get("i"))
        except (TypeError, ValueError):
            continue
        by_i[i] = item

    out = [dict(q) for q in questions]
    for i, orig in enumerate(batch):
        item = by_i.get(i)
        if not item:
            continue
        candidate = {
            **orig,
            "text": str(item.get("text") or "").strip(),
            "answer": str(item.get("answer") or "").strip(),
        }
        if not _looks_valid(orig, candidate):
            continue
        # если LLM «забыл» пересчитать и ответ пустой/мусор — откат
        if not _norm_answer(candidate["answer"]):
            continue
        out[i] = candidate
    return out
