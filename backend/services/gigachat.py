"""Клиент GigaChat API (OAuth + chat/completions)."""

from __future__ import annotations

import base64
import os
import time
import uuid
from typing import Any, Optional

import httpx

from backend.services.prompts import (
    SYSTEM_PROMPT,
    LLMParseError,
    build_user_prompt,
    extract_questions,
)

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS", "").strip()
GIGACHAT_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS").strip()
GIGACHAT_MODEL = os.getenv("GIGACHAT_MODEL", "GigaChat-2").strip()
GIGACHAT_BASE_URL = os.getenv("GIGACHAT_BASE_URL", "https://api.giga.chat").rstrip("/")
GIGACHAT_AUTH_URL = os.getenv(
    "GIGACHAT_AUTH_URL",
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
)
GIGACHAT_VERIFY_SSL = os.getenv("GIGACHAT_VERIFY_SSL", "false").lower() in {
    "1",
    "true",
    "yes",
}

_token_cache: dict[str, Any] = {"access_token": None, "expires_at": 0.0}


class GigaChatError(RuntimeError):
    pass


def _verify() -> bool:
    return GIGACHAT_VERIFY_SSL


async def _fetch_access_token(client: httpx.AsyncClient) -> str:
    if not GIGACHAT_CREDENTIALS:
        raise GigaChatError(
            "Не задан GIGACHAT_CREDENTIALS. Получите ключ в кабинете Sber и добавьте в .env"
        )

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {GIGACHAT_CREDENTIALS}",
    }
    try:
        response = await client.post(
            GIGACHAT_AUTH_URL,
            headers=headers,
            data={"scope": GIGACHAT_SCOPE},
        )
    except httpx.HTTPError as exc:
        raise GigaChatError(f"Сеть OAuth GigaChat: {exc}") from exc

    if response.status_code >= 400:
        raise GigaChatError(f"GigaChat OAuth HTTP {response.status_code}: {response.text[:400]}")

    body = response.json()
    token = body.get("access_token")
    expires_at = body.get("expires_at")
    if not token:
        raise GigaChatError("GigaChat OAuth не вернул access_token")

    # expires_at приходит в миллисекундах unix time
    if isinstance(expires_at, (int, float)) and expires_at > 10_000_000_000:
        _token_cache["expires_at"] = float(expires_at) / 1000.0 - 60
    elif isinstance(expires_at, (int, float)):
        _token_cache["expires_at"] = float(expires_at) - 60
    else:
        _token_cache["expires_at"] = time.time() + 25 * 60

    _token_cache["access_token"] = token
    return token


def decode_image_data_url(data_url: str) -> tuple[bytes, str, str]:
    raw = str(data_url or "").strip()
    if not raw.startswith("data:") or "," not in raw:
        raise GigaChatError("Фото должно быть data URL")
    header, b64 = raw.split(",", 1)
    mime = "image/jpeg"
    if ":" in header:
        mime = header.split(";")[0].split(":", 1)[-1].strip() or mime
    if mime not in {"image/jpeg", "image/jpg", "image/png", "image/bmp", "image/tiff"}:
        mime = "image/jpeg"
    try:
        blob = base64.b64decode(b64)
    except Exception as exc:
        raise GigaChatError("Не удалось прочитать фото") from exc
    if not blob:
        raise GigaChatError("Пустое фото")
    ext = "jpg" if "jpeg" in mime or mime.endswith("jpg") else mime.split("/")[-1]
    return blob, mime, f"solution.{ext}"


async def upload_image_data_url(client: httpx.AsyncClient, data_url: str) -> str:
    blob, mime, name = decode_image_data_url(data_url)
    token = await get_access_token(client)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    files = {"file": (name, blob, mime)}
    response = await client.post(
        f"{GIGACHAT_BASE_URL}/v1/files",
        headers=headers,
        files=files,
        data={"purpose": "general"},
    )
    if response.status_code == 401:
        _token_cache["access_token"] = None
        token = await get_access_token(client)
        headers["Authorization"] = f"Bearer {token}"
        response = await client.post(
            f"{GIGACHAT_BASE_URL}/v1/files",
            headers=headers,
            files=files,
            data={"purpose": "general"},
        )
    if response.status_code >= 400:
        raise GigaChatError(f"GigaChat files HTTP {response.status_code}: {response.text[:400]}")
    body = response.json() if response.content else {}
    file_id = str((body or {}).get("id") or "").strip()
    if not file_id:
        raise GigaChatError("GigaChat не вернул id файла")
    return file_id


async def chat_content(
    messages: list[dict[str, Any]],
    *,
    temperature: float = 0.2,
    image_data_url: Optional[str] = None,
) -> str:
    """Один запрос chat/completions → текст ответа. Фото — через attachments."""
    async with httpx.AsyncClient(timeout=120.0, verify=_verify()) as client:
        payload_messages = [dict(m) for m in messages]
        if image_data_url:
            file_id = await upload_image_data_url(client, image_data_url)
            attached = False
            for msg in reversed(payload_messages):
                if str(msg.get("role") or "") == "user":
                    msg["attachments"] = [file_id]
                    attached = True
                    break
            if not attached:
                payload_messages.append(
                    {"role": "user", "content": "Фото решения ученика.", "attachments": [file_id]}
                )
        token = await get_access_token(client)
        payload = {
            "model": GIGACHAT_MODEL,
            "messages": payload_messages,
            "temperature": temperature,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = await client.post(
            f"{GIGACHAT_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        if response.status_code == 401:
            _token_cache["access_token"] = None
            token = await get_access_token(client)
            headers["Authorization"] = f"Bearer {token}"
            response = await client.post(
                f"{GIGACHAT_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.status_code == 429:
            raise GigaChatError(
                "Слишком много запросов к GigaChat. Подождите 10–20 секунд и попробуйте снова."
            )
        if response.status_code >= 400:
            raise GigaChatError(f"GigaChat HTTP {response.status_code}: {response.text[:500]}")
        body = response.json()
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GigaChatError("Неожиданный ответ GigaChat") from exc


async def get_access_token(client: httpx.AsyncClient) -> str:
    token: Optional[str] = _token_cache.get("access_token")
    expires_at = float(_token_cache.get("expires_at") or 0)
    if token and time.time() < expires_at:
        return token
    return await _fetch_access_token(client)


async def generate_questions(
    *,
    exam: str,
    subject: str,
    difficulty: str = "medium",
    count: int = 4,
    user_prompt: str | None = None,
) -> list[dict[str, Any]]:
    count = max(1, min(int(count or 4), 50))
    if not user_prompt:
        user_prompt = build_user_prompt(
            exam=exam, subject=subject, difficulty=difficulty, count=count
        )

    async def _chat(client: httpx.AsyncClient, messages: list[dict[str, str]], temperature: float) -> str:
        token = await get_access_token(client)
        payload = {
            "model": GIGACHAT_MODEL,
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        response = await client.post(
            f"{GIGACHAT_BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        if response.status_code == 401:
            _token_cache["access_token"] = None
            token = await get_access_token(client)
            headers["Authorization"] = f"Bearer {token}"
            response = await client.post(
                f"{GIGACHAT_BASE_URL}/v1/chat/completions",
                headers=headers,
                json=payload,
            )
        if response.status_code == 429:
            raise GigaChatError(
                "Слишком много запросов к GigaChat. Подождите 10–20 секунд и попробуйте снова."
            )
        if response.status_code >= 400:
            raise GigaChatError(f"GigaChat HTTP {response.status_code}: {response.text[:500]}")
        body = response.json()
        try:
            return body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GigaChatError("Неожиданный ответ GigaChat") from exc

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        async with httpx.AsyncClient(timeout=150.0, verify=_verify()) as client:
            content = await _chat(client, messages, temperature=0.55)
            try:
                return extract_questions(content)
            except LLMParseError:
                # второй заход: жёстко просим только JSON-массив
                repair = [
                    {
                        "role": "system",
                        "content": (
                            "Верни ТОЛЬКО валидный JSON-массив задач без markdown. "
                            "Формулы школьные: 3x²−4x+5, √(x+1), [[2|3]]. "
                            "ЗАПРЕЩЕНО: \\begin, \\frac, $, LaTeX. Системы текстом: «2x+y=7 и x−y=2»."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Исправь ответ в чистый JSON-массив из {count} задач для {exam}/{subject}. "
                            f"Предыдущий ответ был битый. Вот он:\n{content[:3500]}"
                        ),
                    },
                ]
                content2 = await _chat(client, repair, temperature=0.2)
                try:
                    return extract_questions(content2)
                except LLMParseError as exc:
                    raise GigaChatError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise GigaChatError(f"Сеть GigaChat: {exc}") from exc
