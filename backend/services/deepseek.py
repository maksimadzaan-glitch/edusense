"""Клиент DeepSeek API (OpenAI-compatible)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from backend.services.prompts import (
    SYSTEM_PROMPT,
    LLMParseError,
    build_user_prompt,
    extract_questions,
)

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


class DeepSeekError(RuntimeError):
    pass


async def generate_questions(
    *,
    exam: str,
    subject: str,
    difficulty: str = "medium",
    count: int = 4,
    user_prompt: str | None = None,
) -> list[dict[str, Any]]:
    if not DEEPSEEK_API_KEY:
        raise DeepSeekError(
            "Не задан DEEPSEEK_API_KEY. Добавьте ключ в .env и перезапустите сервер."
        )

    count = max(1, min(int(count or 4), 50))
    if not user_prompt:
        user_prompt = build_user_prompt(
            exam=exam, subject=subject, difficulty=difficulty, count=count
        )

    payload: dict[str, Any] = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "thinking": {"type": "disabled"},
    }

    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=150.0) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise DeepSeekError(f"Сеть DeepSeek: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text[:500]
        raise DeepSeekError(f"DeepSeek HTTP {response.status_code}: {detail}")

    body = response.json()
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DeepSeekError("Неожиданный ответ DeepSeek") from exc

    try:
        return extract_questions(content)
    except LLMParseError as exc:
        raise DeepSeekError(str(exc)) from exc


async def chat_content(messages: list[dict[str, str]], *, temperature: float = 0.2) -> str:
    if not DEEPSEEK_API_KEY:
        raise DeepSeekError("Не задан DEEPSEEK_API_KEY.")
    payload: dict[str, Any] = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "temperature": temperature,
        "thinking": {"type": "disabled"},
    }
    url = f"{DEEPSEEK_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise DeepSeekError(f"Сеть DeepSeek: {exc}") from exc
    if response.status_code >= 400:
        raise DeepSeekError(f"DeepSeek HTTP {response.status_code}: {response.text[:500]}")
    body = response.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise DeepSeekError("Неожиданный ответ DeepSeek") from exc
