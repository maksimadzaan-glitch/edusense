"""Сборка полного варианта КИМ из PostgreSQL-шаблонов + лёгкая LLM-вариация.

Поток:
  1) выбрать случайный прототип на каждый task_number;
  2) собрать вариант из template_text / template_answer (+ solution);
  3) опционально слегка изменить числа/формулировки батчами ≤6;
  4) при сбое вариации — исходный шаблон.

Полная генерация всего КИМ одним мега-промптом НЕ используется.
"""

from __future__ import annotations

import copy
import json
import os
import random
import re
from pathlib import Path
from typing import Any, Callable

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.pg import init_pg_tables, is_postgres_configured, session_factory
from backend.db.pg_models import ContextBlock, TaskPrototype
from backend.universal.etalon import (
    context_is_etalon,
    figure_params_is_stub_math_etalon,
    filter_out_stub_math_etalon_ids,
    is_stub_math_etalon_context,
    parse_json_field,
    proto_is_etalon,
    text_is_stub_math_etalon,
)
from backend.universal.validate import VariantValidationError, validate_variant_payload

AI_PROVIDER = os.getenv("AI_PROVIDER", "gigachat").strip().lower()
VARY_BATCH_SIZE = 6
SINGLE_TASK_TIMEOUT = 60.0

ProgressFn = Callable[[str], None]

VARY_SYSTEM = (
    "Ты помощник по школьным заданиям ЕГЭ/ОГЭ. "
    "Слегка меняешь числа и формулировки, сохраняя тип задания. "
    "Отвечай ТОЛЬКО валидным JSON без markdown."
)

SINGLE_TASK_SYSTEM = """Ты — методист ФИПИ. Сгенерируй ОДНО задание КИМ.
Верни СТРОГО JSON-объект без markdown:
{"text":"...","answer":"...","solution":null}
Для part=2 поле solution — непустой текст решения на русском.
Формулы только «бумажным» видом: 3x²−4x+5, √(x+1). Без LaTeX."""


class UniversalGenerateError(RuntimeError):
    pass


def _vary_enabled() -> bool:
    for key in ("UNIVERSAL_VARY", "BANK_VARY"):
        raw = os.getenv(key)
        if raw is not None and raw.strip() != "":
            return raw.strip().lower() not in {"0", "false", "no", "off"}
    return True


def _progress(cb: ProgressFn | None, msg: str) -> None:
    if cb is not None:
        cb(msg)


def _extract_json_object(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        raise VariantValidationError("Пустой ответ LLM")
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError as exc:
            raise VariantValidationError(f"Не удалось разобрать JSON: {exc}") from exc
    raise VariantValidationError("В ответе LLM нет JSON-объекта")


def _extract_json_array(raw: str) -> list | None:
    if not raw:
        return None
    text = raw.strip()
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


def _has_template(proto: TaskPrototype) -> bool:
    text = (proto.template_text or "").strip()
    # part2 / изложение: ключ может быть пустым — для эталона достаточно текста
    answer = (proto.template_answer or "").strip()
    if text and answer:
        return True
    params = parse_json_field(getattr(proto, "figure_params", None))
    etalon = isinstance(params, dict) and bool(params.get("etalon"))
    if etalon:
        # сочинение: statement может быть в essay_options
        if text:
            return True
        if isinstance(params, dict) and (
            params.get("essay_options") or params.get("listening_text")
        ):
            return True
    return False


def _etalon_context_ids(
    db: Session,
    *,
    subject_code: str,
    exam_code: str,
    candidate_ids: list[str],
) -> list[str]:
    """Подмножество context_id с figure_params.etalon=true."""
    if not candidate_ids:
        return []
    rows = db.scalars(
        select(ContextBlock).where(
            ContextBlock.subject_code == subject_code,
            ContextBlock.exam_code == exam_code,
            ContextBlock.context_id.in_(sorted(set(candidate_ids))),
        )
    ).all()
    etalon: list[str] = []
    for r in rows:
        if context_is_etalon(getattr(r, "figure_params", None)):
            etalon.append(str(r.context_id))
    # также: прототипы с etalon в figure_params (если context без флага)
    return etalon


def _proto_etalon_context_ids(rows: list[TaskPrototype], complete: list[str]) -> list[str]:
    by_ctx: dict[str, bool] = {}
    for r in rows:
        cid = _context_id_of(r)
        if not cid or cid not in complete:
            continue
        if proto_is_etalon(getattr(r, "figure_params", None)):
            by_ctx[cid] = True
    return sorted(by_ctx.keys())


def _context_provenance_map(
    db: Session,
    *,
    subject_code: str,
    exam_code: str,
    context_ids: set[str],
) -> dict[str, dict[str, Any]]:
    ids = {c for c in context_ids if c}
    if not ids:
        return {}
    rows = db.scalars(
        select(ContextBlock).where(
            ContextBlock.subject_code == subject_code,
            ContextBlock.exam_code == exam_code,
            ContextBlock.context_id.in_(sorted(ids)),
        )
    ).all()
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        params = parse_json_field(getattr(r, "figure_params", None))
        if not isinstance(params, dict):
            continue
        prov = params.get("provenance")
        if isinstance(prov, dict):
            out[str(r.context_id)] = dict(prov)
        elif params.get("etalon"):
            out[str(r.context_id)] = {
                "source": params.get("source"),
                "variant_code": params.get("variant_code"),
                "kim_spec_id": params.get("kim_spec_id"),
                "content_hash": params.get("content_hash"),
            }
    return out


async def _chat_deepseek(system: str, user: str, *, timeout: float = 90.0) -> str:
    from backend.services import deepseek

    if not deepseek.DEEPSEEK_API_KEY:
        raise UniversalGenerateError(
            "Не задан DEEPSEEK_API_KEY. Добавьте ключ в .env или смените AI_PROVIDER."
        )
    payload = {
        "model": deepseek.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.35,
        "thinking": {"type": "disabled"},
    }
    headers = {
        "Authorization": f"Bearer {deepseek.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{deepseek.DEEPSEEK_BASE_URL}/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise UniversalGenerateError(f"Сеть DeepSeek: {exc}") from exc
    if response.status_code >= 400:
        raise UniversalGenerateError(
            f"DeepSeek HTTP {response.status_code}: {response.text[:500]}"
        )
    body = response.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise UniversalGenerateError("Неожиданный ответ DeepSeek") from exc


async def _chat_openai(system: str, user: str, *, timeout: float = 90.0) -> str:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise UniversalGenerateError(
            "Не задан OPENAI_API_KEY. Добавьте ключ в .env или смените AI_PROVIDER."
        )
    base = (os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = (os.getenv("OPENAI_MODEL") or "gpt-4o-mini").strip()
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.35,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{base}/chat/completions", headers=headers, json=payload)
    except httpx.HTTPError as exc:
        raise UniversalGenerateError(f"Сеть OpenAI: {exc}") from exc
    if response.status_code >= 400:
        raise UniversalGenerateError(
            f"OpenAI HTTP {response.status_code}: {response.text[:500]}"
        )
    body = response.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise UniversalGenerateError("Неожиданный ответ OpenAI") from exc


async def _chat_gigachat(system: str, user: str, *, timeout: float = 90.0) -> str:
    from backend.services import gigachat

    try:
        async with httpx.AsyncClient(timeout=timeout, verify=gigachat._verify()) as client:
            token = await gigachat.get_access_token(client)
            payload = {
                "model": gigachat.GIGACHAT_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
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
            if response.status_code == 401:
                gigachat._token_cache["access_token"] = None
                token = await gigachat.get_access_token(client)
                headers["Authorization"] = f"Bearer {token}"
                response = await client.post(
                    f"{gigachat.GIGACHAT_BASE_URL}/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
    except httpx.HTTPError as exc:
        raise UniversalGenerateError(f"Сеть GigaChat: {exc}") from exc
    except gigachat.GigaChatError as exc:
        raise UniversalGenerateError(str(exc)) from exc

    if response.status_code >= 400:
        raise UniversalGenerateError(
            f"GigaChat HTTP {response.status_code}: {response.text[:500]}"
        )
    body = response.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise UniversalGenerateError("Неожиданный ответ GigaChat") from exc


async def _call_llm(system: str, user: str, *, timeout: float = 90.0) -> str:
    provider = (os.getenv("AI_PROVIDER") or AI_PROVIDER or "gigachat").strip().lower()
    errors: list[str] = []

    if provider in {"deepseek"}:
        order = ["deepseek", "openai", "gigachat"]
    elif provider in {"openai", "gpt"}:
        order = ["openai", "deepseek", "gigachat"]
    else:
        order = ["gigachat", "deepseek", "openai"]

    for name in order:
        try:
            if name == "deepseek":
                return await _chat_deepseek(system, user, timeout=timeout)
            if name == "openai":
                return await _chat_openai(system, user, timeout=timeout)
            if name == "gigachat":
                return await _chat_gigachat(system, user, timeout=timeout)
        except UniversalGenerateError as exc:
            errors.append(f"{name}: {exc}")
            continue
    raise UniversalGenerateError("Не удалось вызвать LLM. " + " | ".join(errors[:3]))


def _looks_valid_varied(original: dict[str, Any], varied: dict[str, Any]) -> bool:
    text = str(varied.get("text") or "").strip()
    answer = str(varied.get("answer") or "").strip()
    if len(text) < 8 or not answer:
        return False
    bad = ("\\begin", "\\frac", "$", "```", "{cases}")
    if any(b in text for b in bad):
        return False
    part = int(original.get("part") or 1)
    if part == 1 and len(answer) > 80:
        return False
    if "\n" in answer and part == 1:
        return False
    if part == 2:
        sol = str(varied.get("solution") or "").strip()
        if not sol:
            return False
    return True


OGE_MATH_CONTEXT_SLOTS = frozenset({1, 2, 3, 4, 5})

# Строковый реестр чертежей 1–5: в БД только id, SVG рисует figures.py.
MATH_ASSET_BY_THEME = {
    "wheel": "TireDiagram",
    "paper": "PaperFormatDiagram",
    "stove": "StoveDiagram",
    "travel": "TravelMapDiagram",
    "route": "TravelMapDiagram",
    "umbrella": "UmbrellaDiagram",
}
OGE_MATH_GEOMETRY_SLOTS = frozenset({23, 24, 25})
# 15 вариантов: 5 лёгких + 5 обычных + 5 сложных. Сюжеты 1–5 — семь видов ОГЭ.
OGE_MATH_BANK_CATALOG: dict[str, dict[str, Any]] = {
    "tires_factory": {"band": "Лёгкий", "band_id": "easy", "code": "Л1", "num": 1, "name": "Шины", "plot": "шины"},
    "apartment_2room": {"band": "Лёгкий", "band_id": "easy", "code": "Л2", "num": 2, "name": "Квартира", "plot": "квартира"},
    "dacha_sosnovoe": {"band": "Лёгкий", "band_id": "easy", "code": "Л3", "num": 3, "name": "Дача", "plot": "участок"},
    "paper_sheets_01": {"band": "Лёгкий", "band_id": "easy", "code": "Л4", "num": 4, "name": "Бумага", "plot": "бумага"},
    "tariffs_mobile_01": {"band": "Лёгкий", "band_id": "easy", "code": "Л5", "num": 5, "name": "Тарифы", "plot": "тарифы"},
    "stove_bath_01": {"band": "Обычный", "band_id": "medium", "code": "О1", "num": 1, "name": "Печи", "plot": "печи"},
    "plan_uchastka_01": {"band": "Обычный", "band_id": "medium", "code": "О2", "num": 2, "name": "Участок", "plot": "участок"},
    "bus_route_01": {"band": "Обычный", "band_id": "medium", "code": "О3", "num": 3, "name": "Маршруты", "plot": "маршруты"},
    "plan_dvor_01": {"band": "Обычный", "band_id": "medium", "code": "О4", "num": 4, "name": "Местность", "plot": "маршруты"},
    "greenhouse_beds_01": {"band": "Обычный", "band_id": "medium", "code": "О5", "num": 5, "name": "Теплица", "plot": "участок"},
    "linoleum_repair_01": {"band": "Сложный", "band_id": "hard", "code": "С1", "num": 1, "name": "Линолеум", "plot": "квартира"},
    "parking_grid_01": {"band": "Сложный", "band_id": "hard", "code": "С2", "num": 2, "name": "Парковка", "plot": "маршруты"},
    "car_fuel_01": {"band": "Сложный", "band_id": "hard", "code": "С3", "num": 3, "name": "Топливо", "plot": "маршруты"},
    "umbrellas_shop_01": {"band": "Сложный", "band_id": "hard", "code": "С4", "num": 4, "name": "Зонты", "plot": "тарифы"},
    "credit_deposit_01": {"band": "Сложный", "band_id": "hard", "code": "С5", "num": 5, "name": "Вклад", "plot": "тарифы"},
}
# ОГЭ русский: цельный вариант — слоты 1..13 (изложение + тесты + сочинение)
OGE_RUS_VARIANT_SLOTS = frozenset(range(1, 14))
# Текст для чтения — задания 10–13; грамматика — 2–3 (отдельный короткий текст)
OGE_RUS_READING_SLOTS = frozenset({10, 11, 12, 13})
OGE_RUS_GRAMMAR_SLOTS = frozenset({2, 3})
# 1 + 2–3 + 10–13 из одного варианта; 4–9 — из пула подтипов.
OGE_RUS_LOCKED_SLOTS = frozenset({1, 2, 3, 10, 11, 12, 13})
OGE_RUS_FREE_SLOTS = frozenset({4, 5, 6, 7, 8, 9})
# Ученику: 1 и 10–13 как у класса; 2–9 — те же правила, другие формулировки.
OGE_RUS_STUDENT_REMIX_SLOTS = OGE_RUS_GRAMMAR_SLOTS | OGE_RUS_FREE_SLOTS
OGE_RUS_POOL_ID = "oge_rus_pool_49"
OGE_RUS_CONTEXT_DIFFICULTY = {
    "oge_rus_var_friendship": "easy",
    "oge_rus_var_nature": "easy",
    "oge_rus_var_dobrota": "easy",
    "oge_rus_var_semya": "easy",
    "oge_rus_var_chestnost": "easy",
    "oge_rus_var_uchitel": "easy",
    "oge_rus_var_pismo": "easy",
    "oge_rus_var_leto": "easy",
    "oge_rus_var_park": "easy",
    "oge_rus_var_hobbi": "easy",
    "oge_rus_var_books": "medium",
    "oge_rus_var_courage": "medium",
    "oge_rus_var_sovest": "medium",
    "oge_rus_var_vremya": "medium",
    "oge_rus_var_slovo": "medium",
    "oge_rus_var_dom": "medium",
    "oge_rus_var_muzyka": "medium",
    "oge_rus_var_pamyat": "medium",
    "oge_rus_var_trud": "medium",
    "oge_rus_var_gorod": "medium",
    "oge_rus_var_dostoinstvo": "hard",
    "oge_rus_var_dolg": "hard",
    "oge_rus_var_istina": "hard",
    "oge_rus_var_molchanie": "hard",
    "oge_rus_var_iskusstvo": "hard",
    "oge_rus_var_svoboda": "hard",
    "oge_rus_var_lichnost": "hard",
    "oge_rus_var_sochuvstvie": "hard",
    "oge_rus_var_nasledie": "hard",
    "oge_rus_var_vybor": "hard",
}
OGE_RUS_IZLO_MIN_WORDS = {"easy": 70, "medium": 70, "hard": 80}
OGE_RUS_ESSAY_MIN_WORDS = {"easy": 70, "medium": 70, "hard": 90}
OGE_RUS_IZLO_MARK = "<<<IZLOZHENIE>>>"
OGE_RUS_GRAMMAR_MARK = "<<<GRAMMAR>>>"
OGE_RUS_READ_MARK = "<<<READING>>>"

# subject_code + exam_code → длина КИМ (не путать с bank_keys subject_key)
_KIM_SLOT_CAPS: dict[tuple[str, str], int] = {
    ("math", "OGE"): 25,
    ("russian", "OGE"): 13,
    ("math", "EGE"): 19,
    ("math_base", "EGE"): 21,
    ("russian", "EGE"): 27,
}


def _kim_slot_cap(subject_code: str, exam_code: str) -> int | None:
    """Макс. номер слота для пары codes; None = брать все номера из PG."""
    sc = (subject_code or "").strip().lower()
    ec = (exam_code or "").strip().upper()
    return _KIM_SLOT_CAPS.get((sc, ec))


def _is_stub_math_proto(proto: TaskPrototype) -> bool:
    """Демо-эталон oge_math_demo_01 — плейсхолдеры, не реальный pack."""
    if is_stub_math_etalon_context(_context_id_of(proto)):
        return True
    if text_is_stub_math_etalon(getattr(proto, "template_text", None)):
        return True
    return figure_params_is_stub_math_etalon(getattr(proto, "figure_params", None))


_OGE_MATH_KITS: dict[str, dict[str, str]] | None = None
_OGE_MATH_KITS_PATH = (
    Path(__file__).resolve().parent / "packs" / "oge_math" / "oge_math_kits.json"
)


def _load_oge_math_kits() -> dict[str, dict[str, str]]:
    global _OGE_MATH_KITS
    if _OGE_MATH_KITS is not None:
        return _OGE_MATH_KITS
    out: dict[str, dict[str, str]] = {}
    try:
        raw = json.loads(_OGE_MATH_KITS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _OGE_MATH_KITS = {}
        return _OGE_MATH_KITS
    kits = raw.get("kits") if isinstance(raw, dict) else None
    if isinstance(kits, dict):
        for cid, slots in kits.items():
            if not isinstance(slots, dict):
                continue
            mapped: dict[str, str] = {}
            for num, code in slots.items():
                key = str(num).strip()
                val = str(code or "").strip()
                if key and val:
                    mapped[key] = val
            if mapped:
                out[str(cid).strip()] = mapped
    _OGE_MATH_KITS = out
    return _OGE_MATH_KITS


def _oge_math_kit_slots(context_id: str | None) -> dict[str, str]:
    cid = str(context_id or "").strip()
    if not cid:
        return {}
    return dict(_load_oge_math_kits().get(cid) or {})


def _math_subtype_of(proto: TaskPrototype) -> str:
    params = _parse_proto_json(getattr(proto, "figure_params", None))
    if isinstance(params, dict):
        code = str(params.get("subtype_code") or "").strip()
        if code:
            return code
    return ""


def _math_proto_fits_slot(proto: TaskPrototype) -> bool:
    """Отсечь чужой тип КИМ, оставшийся в PG после смены номера/заголовка."""
    try:
        num = int(getattr(proto, "task_number", 0) or 0)
    except (TypeError, ValueError):
        return True
    title = str(getattr(proto, "prototype_title", "") or "").lower()
    text = str(getattr(proto, "template_text", "") or "").lower()
    blob = f"{title} {text}"
    if num == 19:
        if any(k in blob for k in ("вероят", "монет", "орёл", "карандаш")):
            return False
        if "найдите третий угол" in blob or "сумма углов треугольника" in title:
            return False
    if num == 21:
        if "алгебраическое уравнение" in title:
            return False
        if "решите уравнение" in blob and any(k in blob for k in ("x^2", "x²", "квадратн")):
            return False
    if num == 10:
        if "геометрическ" in title and "вероят" not in blob:
            return False
    return True


def _context_id_of(proto: TaskPrototype) -> str | None:
    raw = getattr(proto, "context_id", None)
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _parse_proto_json(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    s = str(raw).strip()
    if not s:
        return None
    try:
        parsed = json.loads(s)
    except json.JSONDecodeError:
        return None
    # Иногда в PG лежит дважды сериализованный JSON-строкой
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            return None
    return parsed


def _proto_has_plan_figure(proto: TaskPrototype) -> bool:
    """True, если у прототипа есть plan с rooms (дачa/квартира)."""
    kind = (getattr(proto, "figure_kind", None) or "").strip().lower()
    params = _parse_proto_json(getattr(proto, "figure_params", None))
    rooms = params.get("rooms") if isinstance(params, dict) else None
    has_rooms = isinstance(rooms, list) and bool(rooms)
    if kind == "plan" and has_rooms:
        return True
    return has_rooms


def _proto_has_attachable_figure(proto: TaskPrototype) -> bool:
    """True, если есть SVG / figure_data с URL / простой kind для attach."""
    if (getattr(proto, "figure_svg", None) or "").strip():
        return True
    fig_data = _parse_proto_json(getattr(proto, "figure_data", None))
    if isinstance(fig_data, dict) and str(fig_data.get("main_figure_url") or "").strip():
        return True
    kind = (getattr(proto, "figure_kind", None) or "").strip().lower()
    if kind == "asset":
        return isinstance(fig_data, dict) and bool(fig_data)
    if kind in ("rect", "triangle", "circle", "plan", "grid", "numberline"):
        if kind == "plan":
            return _proto_has_plan_figure(proto)
        return True
    return False


def _context_description_map(
    db: Session,
    *,
    subject_code: str,
    exam_code: str,
    context_ids: set[str],
) -> dict[str, str]:
    """context_id → description_text для подмешивания в условие."""
    meta = _context_meta_map(
        db,
        subject_code=subject_code,
        exam_code=exam_code,
        context_ids=context_ids,
    )
    return {
        cid: str(row.get("story_text") or "").strip()
        for cid, row in meta.items()
        if str(row.get("story_text") or "").strip()
    }


def _context_meta_map(
    db: Session,
    *,
    subject_code: str,
    exam_code: str,
    context_ids: set[str],
) -> dict[str, dict[str, Any]]:
    """context_id → title / сюжет / figure для Parent-Child блока 1–5."""
    ids = {c for c in context_ids if c}
    if not ids:
        return {}
    rows = db.scalars(
        select(ContextBlock).where(
            ContextBlock.subject_code == subject_code,
            ContextBlock.exam_code == exam_code,
            ContextBlock.context_id.in_(sorted(ids)),
        )
    ).all()
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        fp = _parse_proto_json(getattr(r, "figure_params", None))
        if fp is not None and not isinstance(fp, dict):
            fp = None
        out[str(r.context_id)] = {
            "title": (getattr(r, "title", None) or "").strip(),
            "story_text": (getattr(r, "description_text", None) or "").strip(),
            "figure_kind": (getattr(r, "figure_kind", None) or "").strip() or None,
            "figure_params": fp if isinstance(fp, dict) else None,
        }
    return out


def math_asset_id(
    figure_kind: str | None,
    params: dict[str, Any] | None = None,
) -> str | None:
    """Идентификатор чертежа для TaskAssetViewer (не сырой SVG в БД)."""
    p = params if isinstance(params, dict) else {}
    raw = str(p.get("asset_id") or "").strip()
    if raw:
        return raw
    theme = str(p.get("theme") or p.get("scheme") or "").strip().lower()
    if theme in MATH_ASSET_BY_THEME:
        return MATH_ASSET_BY_THEME[theme]
    kind = (figure_kind or "").strip().lower()
    if kind == "plan":
        return "PlanDiagram"
    if kind == "scheme" and theme:
        return theme
    return None


def _norm_story_text(value: str) -> str:
    t = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    t = t.replace("ё", "е").replace("Ё", "Е")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def strip_shared_story(text: str, story: str | None) -> str:
    """Убрать общий сюжет из начала вопроса, если он туда попал."""
    body = (text or "").strip()
    desc = (story or "").strip()
    if not body or not desc:
        return body
    original = body

    def _cut(src: str, prefix: str) -> str | None:
        ns, np = _norm_story_text(src), _norm_story_text(prefix)
        if not np or len(np) < 12 or not ns.startswith(np):
            return None
        start = max(1, len(prefix) - 16)
        for i in range(start, len(src) + 1):
            if _norm_story_text(src[:i]) == np:
                return src[i:].lstrip(" \n\t")
        return src[len(prefix) :].lstrip(" \n\t") if src.startswith(prefix) else None

    cut = _cut(body, desc)
    if cut is not None:
        body = cut
    else:
        for para in [p.strip() for p in re.split(r"\n\s*\n", desc) if p.strip()]:
            nxt = _cut(body, para)
            if nxt is None:
                break
            body = nxt
        m = re.match(r"^(.+?[.!?…])(\s+|$)", desc)
        if m:
            nxt = _cut(body, m.group(1))
            if nxt is not None:
                body = nxt
    body = (body or "").strip()
    if len(body) < 16:
        return original
    return body


def _with_context_prefix(text: str, context_desc: str | None) -> str:
    """Префикс текста задания описанием контекста (изложение / текст для чтения)."""
    body = (text or "").strip()
    desc = (context_desc or "").strip()
    if not desc:
        return body
    if not body:
        return desc
    # не дублировать, если шаблон уже содержит начало контекста
    head = desc[:80]
    if head and head in body:
        return body
    return f"{desc}\n\n{body}"


def _split_oge_rus_context(
    desc: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Из структурированного description_text → (izlozhenie, grammar, reading)."""
    raw = (desc or "").strip()
    if not raw:
        return None, None, None
    has_marks = (
        OGE_RUS_IZLO_MARK in raw
        or OGE_RUS_GRAMMAR_MARK in raw
        or OGE_RUS_READ_MARK in raw
    )
    if not has_marks:
        return None, None, raw

    izlo: str | None = None
    grammar: str | None = None
    reading: str | None = None

    parts: dict[str, str] = {}
    marks = [
        (raw.find(OGE_RUS_IZLO_MARK), "izlo", OGE_RUS_IZLO_MARK),
        (raw.find(OGE_RUS_GRAMMAR_MARK), "grammar", OGE_RUS_GRAMMAR_MARK),
        (raw.find(OGE_RUS_READ_MARK), "read", OGE_RUS_READ_MARK),
    ]
    marks = [(i, k, m) for i, k, m in marks if i >= 0]
    marks.sort(key=lambda x: x[0])
    for idx, (pos, key, mark) in enumerate(marks):
        start = pos + len(mark)
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(raw)
        parts[key] = raw[start:end].strip()
    izlo = parts.get("izlo") or None
    grammar = parts.get("grammar") or None
    reading = parts.get("read") or None
    return izlo, grammar, reading


def _oge_rus_prefix_for_slot(task_number: int, context_desc: str | None) -> str | None:
    """Префикс по номеру: НЕ вшиваем тексты в каждое задание — UI показывает shared blocks.

    Раньше reading клеился в №2 и 9–12; теперь тексты разделены и отдаются через payload.
    """
    # Сознательно None: grammar/reading/listening живут в figure_params.payload / UI
    _ = (task_number, context_desc)
    return None


def _oge_rus_payload_from_proto(proto: TaskPrototype) -> dict[str, Any] | None:
    params = _parse_proto_json(getattr(proto, "figure_params", None))
    if isinstance(params, dict) and params.get("oge_rus"):
        return dict(params)
    return None


def _oge_rus_local_audio_url(context_id: str | None) -> str | None:
    """Если в frontend/audio/oge_rus лежит MP3/WAV варианта — отдать URL плееру."""
    cid = (context_id or "").strip()
    if not cid:
        return None
    slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", cid) or "oge_rus"
    audio_dir = Path(__file__).resolve().parents[2] / "frontend" / "audio" / "oge_rus"
    for ext in ("mp3", "wav"):
        path = audio_dir / f"{slug}.{ext}"
        try:
            if path.is_file() and path.stat().st_size > 1000:
                return f"/audio/oge_rus/{slug}.{ext}"
        except OSError:
            continue
    return None


def _oge_rus_audio_file_ok(url: str | None) -> bool:
    """True, если /audio/oge_rus/... указывает на реальный файл > 1 КБ."""
    u = (url or "").strip()
    if not u.startswith("/audio/"):
        return False
    rel = u.lstrip("/").replace("\\", "/")
    if ".." in rel.split("/"):
        return False
    path = Path(__file__).resolve().parents[2] / "frontend" / rel
    try:
        return path.is_file() and path.stat().st_size > 1000
    except OSError:
        return False


def _resolve_oge_rus_audio_url(context_id: str | None, existing: str | None = None) -> str | None:
    """Живой файл на диске важнее битой ссылки из JSON."""
    local = _oge_rus_local_audio_url(context_id)
    if local:
        return local
    if _oge_rus_audio_file_ok(existing):
        return str(existing).strip()
    return None


def _fill_oge_rus_shared_from_context(
    payload: dict[str, Any],
    *,
    task_number: int,
    context_desc: str | None,
) -> dict[str, Any]:
    """Дополнить listening/grammar/reading из description_text контекста, если в figure_params пусто."""
    izlo, grammar, reading = _split_oge_rus_context(context_desc)
    out = dict(payload)
    num = int(task_number)
    if num == 1 and izlo and not out.get("listening_text"):
        out["listening_text"] = izlo
        out.setdefault("ui", "listening")
    if num in (2, 3) and grammar and not out.get("grammar_text"):
        out["grammar_text"] = grammar
        if num == 2:
            out.setdefault("show_shared", "grammar")
    if num in (10, 11, 12) and reading and not out.get("reading_text"):
        out["reading_text"] = reading
        if num == 10:
            out.setdefault("show_shared", "reading")
    return out


def _enrich_oge_rus_shared_across_tasks(tasks: list[dict[str, Any]]) -> None:
    """Скопировать grammar_text на слоты 2–3 и reading_text на 10–12 (UI + устойчивость к старым seed)."""
    grammar = None
    reading = None
    audio_url = None
    listening = None
    for t in tasks:
        try:
            num = int(t.get("task_number") or 0)
        except (TypeError, ValueError):
            num = 0
        p = t.get("payload") if isinstance(t.get("payload"), dict) else {}
        if num in (2, 3) and not grammar and p.get("grammar_text"):
            grammar = str(p["grammar_text"])
        if num in (10, 11, 12, 13) and not reading and p.get("reading_text"):
            reading = str(p["reading_text"])
        if num == 1 and not listening and p.get("listening_text"):
            listening = str(p["listening_text"])
        if num == 1 and not audio_url and p.get("audio_url"):
            audio_url = str(p["audio_url"])
    for t in tasks:
        try:
            num = int(t.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        p = dict(t.get("payload") or {}) if isinstance(t.get("payload"), dict) else {"oge_rus": True}
        p.setdefault("oge_rus", True)
        p.setdefault("kim_type", num)
        changed = False
        if num in (2, 3) and grammar:
            if p.get("grammar_text") != grammar:
                p["grammar_text"] = grammar
                changed = True
            if num == 2 and p.get("show_shared") != "grammar":
                p["show_shared"] = "grammar"
                changed = True
        if num in (10, 11, 12) and reading:
            if p.get("reading_text") != reading:
                p["reading_text"] = reading
                changed = True
            if num == 10 and p.get("show_shared") != "reading":
                p["show_shared"] = "reading"
                changed = True
        if num == 1:
            if listening and not p.get("listening_text"):
                p["listening_text"] = listening
                changed = True
            if audio_url and not p.get("audio_url"):
                p["audio_url"] = audio_url
                changed = True
            resolved = _resolve_oge_rus_audio_url(t.get("context_id"), p.get("audio_url"))
            if resolved:
                if p.get("audio_url") != resolved:
                    p["audio_url"] = resolved
                    changed = True
            elif p.get("audio_url"):
                p.pop("audio_url", None)
                changed = True
            if cid := str(t.get("context_id") or "").strip():
                if p.get("context_id") != cid:
                    p["context_id"] = cid
                    changed = True
        if num == 13 and reading and not p.get("reading_text"):
            # Сочинение опирается на прочитанный текст — держим ссылку в payload для UI.
            p["reading_text"] = reading
            changed = True
        if num == 1:
            t["max_score"] = 7
            if not isinstance(p.get("rubric"), dict) or p.get("rubric", {}).get("kind") != "izlozhenie":
                p["rubric"] = {
                    "kind": "izlozhenie",
                    "criteria": [
                        {"id": "ik1", "title": "ИК1 · микротемы", "max": 2},
                        {"id": "ik2", "title": "ИК2 · сжатие", "max": 3},
                        {"id": "ik3", "title": "ИК3 · смысловая цельность", "max": 2},
                    ],
                    "literacy": [
                        {"id": "gk1", "title": "ГК1 · орфография", "max": 2},
                        {"id": "gk2", "title": "ГК2 · пунктуация", "max": 2},
                        {"id": "gk3", "title": "ГК3 · грамматика", "max": 2},
                        {"id": "gk4", "title": "ГК4 · речь", "max": 2},
                    ],
                    "note": "Содержание изложения — 7. Грамотность ГК1–ГК4 ставится один раз за изложение и сочинение вместе (макс. 8). Первичный балл работы: 7+11+7+8 = 33.",
                }
                changed = True
        if num == 13:
            t["max_score"] = 7
            if not isinstance(p.get("rubric"), dict) or p.get("rubric", {}).get("kind") != "sochinenie":
                p["rubric"] = {
                    "kind": "sochinenie",
                    "criteria": [
                        {"id": "sk1", "title": "СК1 · понимание текста / тезис", "max": 2},
                        {"id": "sk2", "title": "СК2 · аргументы", "max": 3},
                        {"id": "sk3", "title": "СК3 · композиция", "max": 2},
                    ],
                }
                changed = True
        if changed or "payload" not in t:
            t["payload"] = p


def _stamp_math_context_payload(
    out: dict[str, Any],
    *,
    context_desc: str | None,
    context_meta: dict[str, Any] | None,
) -> None:
    """Общий сюжет 1–5 — в payload, не в каждом тексте вопроса."""
    meta = context_meta if isinstance(context_meta, dict) else {}
    story = str(meta.get("story_text") or context_desc or "").strip()
    title = str(meta.get("title") or "").strip()
    fp = out.get("figure_params") if isinstance(out.get("figure_params"), dict) else None
    if fp is None and isinstance(meta.get("figure_params"), dict):
        fp = meta["figure_params"]
        if not out.get("figure_params"):
            out["figure_params"] = fp
    if not out.get("figure_kind") and meta.get("figure_kind"):
        out["figure_kind"] = meta["figure_kind"]
    payload = dict(out.get("payload") or {}) if isinstance(out.get("payload"), dict) else {}
    if story:
        payload["shared_story"] = story
    if title:
        payload["context_title"] = title
    cid = str(out.get("context_id") or "").strip()
    if cid:
        payload["context_id"] = cid
    asset = math_asset_id(out.get("figure_kind"), fp if isinstance(fp, dict) else None)
    if asset:
        payload["asset_id"] = asset
    if isinstance(fp, dict) and isinstance(fp.get("base_vars"), dict):
        payload["base_vars"] = dict(fp["base_vars"])
    if payload:
        out["payload"] = payload
    if story and not out.get("_etalon"):
        out["text"] = strip_shared_story(str(out.get("text") or ""), story)


def _task_from_proto(
    proto: TaskPrototype,
    *,
    context_desc: str | None = None,
    context_meta: dict[str, Any] | None = None,
    subject_code: str | None = None,
    exam_code: str | None = None,
) -> dict[str, Any]:
    part = int(proto.part)
    sc = (subject_code or getattr(proto, "subject_code", "") or "").strip().lower()
    ec = (exam_code or getattr(proto, "exam_code", "") or "").strip().upper()
    is_etalon_proto = proto_is_etalon(getattr(proto, "figure_params", None))
    slot_num = int(proto.task_number)
    math_group = sc == "math" and ec == "OGE" and slot_num in OGE_MATH_CONTEXT_SLOTS
    prefix = context_desc
    if sc == "russian" and ec == "OGE":
        prefix = _oge_rus_prefix_for_slot(slot_num, context_desc)
    if is_etalon_proto:
        # эталон: statement дословно, без префикса context.description
        prefix = None
    if math_group:
        # сюжет один раз в ContextBlock UI, не клеим в каждый из 1–5
        prefix = None
    text = _with_context_prefix((proto.template_text or "").strip(), prefix)
    answer = (proto.template_answer or "").strip()
    solution_raw = (proto.template_solution or "").strip()
    solution: str | None
    if part == 2:
        if is_etalon_proto:
            # эталон: не выдумывать solution
            solution = solution_raw or None
        else:
            solution = solution_raw or (
                f"Решение.\n"
                f"1) Исходим из условия задания.\n"
                f"2) Выполняем необходимые преобразования.\n"
                f"3) Ответ: {answer}."
            )
    else:
        solution = solution_raw or None
    fig_kind = (getattr(proto, "figure_kind", None) or "").strip() or None
    fig_params = _parse_proto_json(getattr(proto, "figure_params", None))
    if fig_params is not None and not isinstance(fig_params, (dict, list)):
        # невалидный JSON — оставить сырую строку как раньше
        raw_fp = str(getattr(proto, "figure_params", None) or "").strip()
        fig_params = raw_fp or None
    fig_data = _parse_proto_json(getattr(proto, "figure_data", None))
    if fig_data is not None and not isinstance(fig_data, dict):
        fig_data = None
    fig_svg = (getattr(proto, "figure_svg", None) or "").strip() or None
    out: dict[str, Any] = {
        "task_number": int(proto.task_number),
        "part": part,
        "prototype_title": proto.prototype_title,
        "text": text,
        "answer": answer,
        "solution": solution,
        "prompt_instruction": proto.prompt_instruction,
        "figure_kind": fig_kind,
        "figure_params": fig_params,
        "_from_template": True,
        "context_id": _context_id_of(proto),
        "max_score": (
            int(getattr(proto, "max_score"))
            if getattr(proto, "max_score", None) is not None
            else None
        ),
    }
    acc_raw = getattr(proto, "acceptable_answers", None)
    if acc_raw:
        parsed_acc = _parse_proto_json(acc_raw)
        if isinstance(parsed_acc, list):
            out["acceptable_answers"] = parsed_acc
        elif isinstance(acc_raw, str) and acc_raw.strip().startswith("["):
            try:
                import json as _json

                parsed_acc = _json.loads(acc_raw)
                if isinstance(parsed_acc, list):
                    out["acceptable_answers"] = parsed_acc
            except Exception:
                pass
    if fig_data is not None:
        out["figure_data"] = fig_data
    if fig_svg:
        out["figure_svg"] = fig_svg
    if fig_kind == "asset" or fig_data is not None:
        out["_figure_pack"] = "oge_math"
    rus_payload = _oge_rus_payload_from_proto(proto)
    if rus_payload is not None:
        if sc == "russian" and ec == "OGE":
            rus_payload = _fill_oge_rus_shared_from_context(
                rus_payload,
                task_number=int(proto.task_number),
                context_desc=context_desc,
            )
        out["payload"] = rus_payload
        # figure_params с oge_rus не для чертежей
        out["figure_params"] = None
        out["figure_kind"] = None
        out.pop("figure_svg", None)
        out.pop("figure_data", None)
        out.pop("_figure_pack", None)
    elif sc == "russian" and ec == "OGE":
        # Минимальный payload, если в PG нет figure_params
        base = _fill_oge_rus_shared_from_context(
            {"oge_rus": True, "kim_type": int(proto.task_number), "ui": "oge_rus"},
            task_number=int(proto.task_number),
            context_desc=context_desc,
        )
        out["payload"] = base
        out["figure_params"] = None
        out["figure_kind"] = None
        out.pop("figure_svg", None)
        out.pop("figure_data", None)
        out.pop("_figure_pack", None)
    elif isinstance(fig_params, dict) and fig_params.get("mutator_logic"):
        payload = dict(out.get("payload") or {}) if isinstance(out.get("payload"), dict) else {}
        payload["mutator_logic"] = fig_params["mutator_logic"]
        payload["mutator_template"] = str(
            fig_params.get("template") or (proto.template_text or "")
        ).strip()
        expl = fig_params.get("explanation_template") or solution_raw
        if expl:
            payload["explanation_template"] = str(expl)
        out["payload"] = payload
        clean_fp = {
            k: v
            for k, v in fig_params.items()
            if k not in {"mutator_logic", "template", "explanation_template"}
        }
        out["figure_params"] = clean_fp or None
        if not clean_fp and not fig_kind:
            out["figure_kind"] = None
    elif isinstance(fig_params, dict) and (
        fig_params.get("etalon") or isinstance(fig_params.get("payload"), dict)
    ):
        # Эталон math (и др.): payload.image_urls / media живут в figure_params
        nested = fig_params.get("payload") if isinstance(fig_params.get("payload"), dict) else None
        payload = dict(nested or {})
        payload.setdefault("etalon", bool(fig_params.get("etalon")))
        if fig_params.get("image_urls") and not payload.get("image_urls"):
            payload["image_urls"] = list(fig_params.get("image_urls") or [])
        if fig_params.get("media") and not payload.get("media"):
            payload["media"] = list(fig_params.get("media") or [])
        if isinstance(fig_params.get("provenance"), dict):
            payload.setdefault("provenance", fig_params["provenance"])
        out["payload"] = payload
        out["_etalon"] = True
    if proto_is_etalon(getattr(proto, "figure_params", None)):
        out["_etalon"] = True
    if isinstance(fig_params, dict) and sc == "math":
        payload = dict(out.get("payload") or {}) if isinstance(out.get("payload"), dict) else {}
        for key in ("subtype_code", "title", "tags", "difficulty"):
            if fig_params.get(key) is not None:
                payload.setdefault(key, fig_params[key])
        if payload:
            out["payload"] = payload
    if math_group:
        _stamp_math_context_payload(
            out, context_desc=context_desc, context_meta=context_meta
        )
    return out



def _complete_context_ids(
    rows: list[TaskPrototype],
    *,
    slots: frozenset[int] = OGE_MATH_CONTEXT_SLOTS,
) -> list[str]:
    """context_id, у которых есть шаблон на каждый слот из slots."""
    by_ctx: dict[str, set[int]] = {}
    for r in rows:
        cid = _context_id_of(r)
        if not cid or not _has_template(r):
            continue
        num = int(r.task_number)
        if num in slots:
            by_ctx.setdefault(cid, set()).add(num)
    return sorted(cid for cid, nums in by_ctx.items() if slots <= nums)


def _prefer_plan_contexts(
    rows: list[TaskPrototype],
    complete: list[str],
) -> list[str]:
    """Среди полных контекстов предпочесть каталог из 15 блоков, иначе планы."""
    catalog = [cid for cid in complete if cid in OGE_MATH_BANK_CATALOG]
    if catalog:
        return catalog
    with_plan: list[str] = []
    for cid in complete:
        if any(
            _context_id_of(r) == cid and _proto_has_plan_figure(r)
            for r in rows
        ):
            with_plan.append(cid)
    return with_plan or complete


def oge_math_bank_meta(context_id: str | None) -> dict[str, Any] | None:
    cid = str(context_id or "").strip()
    if not cid:
        return None
    row = OGE_MATH_BANK_CATALOG.get(cid)
    if not row:
        return None
    return {
        "band": row["band"],
        "code": row["code"],
        "num": row["num"],
        "name": row["name"],
        "plot": row.get("plot") or row["name"],
        "band_id": row.get("band_id") or "medium",
        "label": f"{row['band']} №{row['num']} · {row['name']}",
        "context_id": cid,
    }


def _oge_math_bank_from_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    cid = ""
    for t in tasks:
        try:
            n = int(t.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        if n == 1 and t.get("context_id"):
            cid = str(t.get("context_id") or "").strip()
            break
    if not cid:
        for t in tasks:
            c = str(t.get("context_id") or "").strip()
            if c in OGE_MATH_BANK_CATALOG:
                cid = c
                break
    return oge_math_bank_meta(cid)


def _stamp_oge_math_bank(tasks: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    for t in tasks:
        p = dict(t.get("payload") or {}) if isinstance(t.get("payload"), dict) else {}
        p["bank_code"] = meta["code"]
        p["bank_label"] = meta["label"]
        p["bank_name"] = meta["name"]
        p["bank_num"] = meta["num"]
        p["bank_band"] = meta["band"]
        p["bank_plot"] = meta.get("plot")
        p["difficulty"] = meta.get("band_id") or p.get("difficulty")
        t["payload"] = p


def _attach_oge_math_bank(validated: dict[str, Any], tasks: list[dict[str, Any]]) -> None:
    meta = _oge_math_bank_from_tasks(tasks)
    if not meta:
        return
    _stamp_oge_math_bank(validated.get("tasks") or tasks, meta)
    validated["bank"] = meta
    validated["variant_label"] = meta["label"]


def _pick_from_context(
    rows: list[TaskPrototype],
    context_id: str,
    *,
    slots: frozenset[int] = OGE_MATH_CONTEXT_SLOTS,
    rng: random.Random | None = None,
) -> list[TaskPrototype]:
    """По одному прототипу на каждый слот из выбранного context_block."""
    by_num: dict[int, list[TaskPrototype]] = {}
    for r in rows:
        if _context_id_of(r) != context_id:
            continue
        num = int(r.task_number)
        if num in slots and _has_template(r):
            by_num.setdefault(num, []).append(r)
    picked: list[TaskPrototype] = []
    choice = (rng or random).choice
    for num in sorted(slots):
        pool = by_num.get(num) or []
        if not pool:
            raise UniversalGenerateError(
                f"Контекст {context_id!r}: нет шаблона для задания {num}"
            )
        picked.append(choice(pool))
    return picked


def _complete_oge_rus_variant_ids(rows: list[TaskPrototype]) -> list[str]:
    """context_id вариантов, у которых есть шаблоны на все слоты 1..13."""
    return _complete_context_ids(rows, slots=OGE_RUS_VARIANT_SLOTS)


# Полные КИМ 1–13 (сочинение); неполные 12-slot packs (var_01…/var_a) исключаем из пула.
# В generate только вычитанные. Остальные JSON лежат в imports/ до следующей пачки.
OGE_RUS_VERIFIED = frozenset(
    {
        "oge_rus_var_chestnost",
        "oge_rus_var_dobrota",
        "oge_rus_var_uchitel",
        "oge_rus_var_semya",
        "oge_rus_var_pismo",
        "oge_rus_var_sovest",
        "oge_rus_var_slovo",
        "oge_rus_var_pamyat",
        "oge_rus_var_vremya",
        "oge_rus_var_dom",
        "oge_rus_var_dostoinstvo",
        "oge_rus_var_istina",
        "oge_rus_var_vybor",
        "oge_rus_var_dolg",
        "oge_rus_var_molchanie",
        "oge_rus_var_nature",
        "oge_rus_var_leto",
        "oge_rus_var_park",
        "oge_rus_var_hobbi",
        "oge_rus_var_trud",
        "oge_rus_var_gorod",
        "oge_rus_var_iskusstvo",
        "oge_rus_var_svoboda",
        "oge_rus_var_lichnost",
        "oge_rus_var_sochuvstvie",
        "oge_rus_var_nasledie",
    }
)
OGE_RUS_PREFERRED_VARIANTS = OGE_RUS_VERIFIED
# Грамматика 2–3 из КИМ — узнаваемый текст про соль; в обычной сборке не крутим.
OGE_RUS_SALT_CONTEXTS = frozenset({"oge_rus_var_kim", "etalon_oge_rus_var_kim"})

# Стабильные номера полки: учитель пишет «База №1, задание 11» / «Б1, №11».
OGE_RUS_BANK_CATALOG: dict[str, dict[str, Any]] = {
    "oge_rus_var_chestnost": {"band": "База", "code": "Б1", "num": 1, "name": "Честность"},
    "oge_rus_var_dobrota": {"band": "База", "code": "Б2", "num": 2, "name": "Доброта"},
    "oge_rus_var_uchitel": {"band": "База", "code": "Б3", "num": 3, "name": "Учитель"},
    "oge_rus_var_semya": {"band": "База", "code": "Б4", "num": 4, "name": "Семья"},
    "oge_rus_var_pismo": {"band": "База", "code": "Б5", "num": 5, "name": "Письмо"},
    "oge_rus_var_sovest": {"band": "КИМ", "code": "К1", "num": 1, "name": "Совесть"},
    "oge_rus_var_slovo": {"band": "КИМ", "code": "К2", "num": 2, "name": "Слово"},
    "oge_rus_var_pamyat": {"band": "КИМ", "code": "К3", "num": 3, "name": "Память"},
    "oge_rus_var_vremya": {"band": "КИМ", "code": "К4", "num": 4, "name": "Время"},
    "oge_rus_var_dom": {"band": "КИМ", "code": "К5", "num": 5, "name": "Дом"},
    "oge_rus_var_dostoinstvo": {"band": "Хардкор", "code": "Х1", "num": 1, "name": "Достоинство"},
    "oge_rus_var_istina": {"band": "Хардкор", "code": "Х2", "num": 2, "name": "Истина"},
    "oge_rus_var_vybor": {"band": "Хардкор", "code": "Х3", "num": 3, "name": "Выбор"},
    "oge_rus_var_dolg": {"band": "Хардкор", "code": "Х4", "num": 4, "name": "Долг"},
    "oge_rus_var_molchanie": {"band": "Хардкор", "code": "Х5", "num": 5, "name": "Молчание"},
}


def oge_rus_bank_meta(context_id: str | None) -> dict[str, Any] | None:
    cid = str(context_id or "").strip()
    if not cid:
        return None
    row = OGE_RUS_BANK_CATALOG.get(cid)
    if row:
        return {
            "band": row["band"],
            "code": row["code"],
            "num": row["num"],
            "name": row["name"],
            "label": f"{row['band']} №{row['num']} · {row['name']}",
            "context_id": cid,
        }
    if cid in OGE_RUS_SALT_CONTEXTS:
        return {
            "band": "Эталон",
            "code": "Э1",
            "num": 1,
            "name": "Соль",
            "label": "Эталон №1 · Соль",
            "context_id": cid,
        }
    return None


def _oge_rus_bank_from_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    cid = ""
    for t in tasks:
        try:
            n = int(t.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        if n == 1 and t.get("context_id"):
            cid = str(t.get("context_id") or "").strip()
            break
    if not cid:
        for t in tasks:
            c = str(t.get("context_id") or "").strip()
            if c in OGE_RUS_BANK_CATALOG or c in OGE_RUS_SALT_CONTEXTS:
                cid = c
                break
    return oge_rus_bank_meta(cid)


def _stamp_oge_rus_bank(tasks: list[dict[str, Any]], meta: dict[str, Any]) -> None:
    for t in tasks:
        p = dict(t.get("payload") or {}) if isinstance(t.get("payload"), dict) else {}
        p["bank_code"] = meta["code"]
        p["bank_label"] = meta["label"]
        p["bank_name"] = meta["name"]
        p["bank_num"] = meta["num"]
        p["bank_band"] = meta["band"]
        t["payload"] = p


def _attach_oge_rus_bank(validated: dict[str, Any], tasks: list[dict[str, Any]]) -> None:
    meta = _oge_rus_bank_from_tasks(tasks)
    if not meta:
        return
    _stamp_oge_rus_bank(validated.get("tasks") or tasks, meta)
    validated["bank"] = meta
    validated["variant_label"] = meta["label"]


def _prefer_oge_rus_complete(complete: list[str]) -> list[str]:
    """Только вычитанные полные варианты (без сырого банка и без соли)."""
    preferred = [c for c in complete if c in OGE_RUS_PREFERRED_VARIANTS]
    return preferred or list(complete)


def _norm_math_diff(raw: str | None) -> str:
    d = (raw or "medium").strip().lower().replace("ё", "е")
    if d in {"easy", "легкий", "база", "base"}:
        return "easy"
    if d in {"hard", "сложный", "хардкор", "hardcore"}:
        return "hard"
    return "medium"


def _math_diff_of_proto(proto: TaskPrototype) -> str:
    col = (getattr(proto, "difficulty", None) or "").strip().lower()
    if col in {"easy", "medium", "hard"}:
        return col
    params = _parse_proto_json(getattr(proto, "figure_params", None))
    if isinstance(params, dict):
        pd = str(params.get("difficulty") or "").strip().lower()
        if pd in {"easy", "medium", "hard"}:
            return pd
        if params.get("mutator_logic"):
            return "easy"
    title = str(getattr(proto, "prototype_title", "") or "")
    if re.match(r"^\d+m\s*:", title):
        return "easy"
    cid = _context_id_of(proto) or ""
    row = OGE_MATH_BANK_CATALOG.get(cid)
    if row:
        return str(row.get("band_id") or "medium")
    return "medium"


def _filter_math_ctx_by_diff(context_ids: list[str], want: str) -> list[str]:
    pref = [
        c
        for c in context_ids
        if OGE_MATH_BANK_CATALOG.get(c, {}).get("band_id") == want
    ]
    return pref or list(context_ids)


def _norm_rus_diff(raw: str | None) -> str:
    d = (raw or "medium").strip().lower()
    if d in {"easy", "база", "base"}:
        return "easy"
    if d in {"hard", "хардкор", "hardcore"}:
        return "hard"
    return "medium"


def _rus_diff_of_proto(proto: TaskPrototype) -> str:
    col = (getattr(proto, "difficulty", None) or "").strip().lower()
    if col in {"easy", "medium", "hard"}:
        return col
    params = _parse_proto_json(getattr(proto, "figure_params", None))
    if isinstance(params, dict):
        pd = str(params.get("difficulty") or "").strip().lower()
        if pd in {"easy", "medium", "hard"}:
            return pd
    cid = _context_id_of(proto) or ""
    return OGE_RUS_CONTEXT_DIFFICULTY.get(cid, "medium")


def _filter_rus_by_diff(items: list, want: str):
    if not items:
        return items
    pref = [x for x in items if _rus_diff_of_proto(x) == want]
    if pref:
        return pref
    if want != "medium":
        mid = [x for x in items if _rus_diff_of_proto(x) == "medium"]
        if mid:
            return mid
    return items


def _filter_ctx_by_diff(context_ids: list[str], want: str) -> list[str]:
    pref = [c for c in context_ids if OGE_RUS_CONTEXT_DIFFICULTY.get(c, "medium") == want]
    if pref:
        return pref
    if want != "medium":
        mid = [c for c in context_ids if OGE_RUS_CONTEXT_DIFFICULTY.get(c, "medium") == "medium"]
        if mid:
            return mid
    return list(context_ids)


def _oge_rus_subtype_of(proto: TaskPrototype) -> str:
    params = _parse_proto_json(getattr(proto, "figure_params", None))
    if isinstance(params, dict):
        st = str(params.get("subtype") or "").strip()
        if st:
            return st
    try:
        num = int(getattr(proto, "task_number", 0) or 0)
    except (TypeError, ValueError):
        num = 0
    return f"slot{num}"


def _pick_oge_rus_pool_slots(
    rows: list[TaskPrototype],
    *,
    want: str,
    rng: random.Random,
) -> list[TaskPrototype]:
    """Одно задание на слот 4–9 из пула: тот же уровень, разные подтипы."""
    picked: list[TaskPrototype] = []
    used: set[str] = set()
    for num in sorted(OGE_RUS_FREE_SLOTS):
        cand = [
            r
            for r in rows
            if int(r.task_number) == num
            and _has_template(r)
            and (_context_id_of(r) or "") == OGE_RUS_POOL_ID
        ]
        cand = _filter_rus_by_diff(cand, want)
        if not cand:
            cand = [
                r
                for r in rows
                if int(r.task_number) == num
                and _has_template(r)
                and (_context_id_of(r) or "") == OGE_RUS_POOL_ID
            ]
        if not cand:
            raise UniversalGenerateError(
                f"Пул 4–9 пуст для задания {num}. "
                "Запустите: python -m backend.scripts.seed_oge_rus_pool"
            )
        fresh = [r for r in cand if _oge_rus_subtype_of(r) not in used]
        choice = rng.choice(fresh or cand)
        used.add(_oge_rus_subtype_of(choice))
        picked.append(choice)
    return picked


def _apply_oge_rus_difficulty(tasks: list[dict[str, Any]], difficulty: str) -> None:
    """Жёстче изложение/сочинение на hard: больше слов, строже формулировка."""
    want = _norm_rus_diff(difficulty)
    izlo_n = OGE_RUS_IZLO_MIN_WORDS[want]
    essay_n = OGE_RUS_ESSAY_MIN_WORDS[want]
    for t in tasks:
        try:
            num = int(t.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        p = dict(t.get("payload") or {}) if isinstance(t.get("payload"), dict) else {}
        p["difficulty"] = want
        if num == 1:
            p["min_words"] = izlo_n
            text = str(t.get("text") or "")
            text = re.sub(r"не менее\s+\d+\s+слов", f"не менее {izlo_n} слов", text, flags=re.I)
            text = re.sub(r"Минимум слов:\s*\d+", f"Минимум слов: {izlo_n}", text, flags=re.I)
            t["text"] = text
        if num == 13:
            p["min_words"] = essay_n
            text = str(t.get("text") or "")
            text = re.sub(r"не менее\s+\d+\s+слов", f"не менее {essay_n} слов", text, flags=re.I)
            t["text"] = text
            opts = p.get("essay_options")
            if isinstance(opts, list):
                new_opts = []
                for opt in opts:
                    if not isinstance(opt, dict):
                        new_opts.append(opt)
                        continue
                    o = dict(opt)
                    st = str(o.get("statement") or "")
                    st = re.sub(r"не менее\s+\d+\s+слов", f"не менее {essay_n} слов", st, flags=re.I)
                    if want == "hard" and o.get("type") == "13.1" and "синтаксическ" not in st.lower():
                        st = st.rstrip() + " Опирайтесь на тропы и синтаксис, не только на пересказ."
                    o["statement"] = st
                    new_opts.append(o)
                p["essay_options"] = new_opts
        t["payload"] = p


_NUM_OPT_LINE_RE = re.compile(r"(?m)^(\d+)\)\s*(.+)$")
_OGE_RUS_SHUFFLE_SLOTS = frozenset({2, 3, 4, 6, 10, 11})


def _is_prefix_digit_key(answer: str, n_options: int) -> bool:
    """Ключ вида 12 / 123 / 1234 — «верные стоят первыми»."""
    digits = "".join(ch for ch in str(answer or "") if ch.isdigit())
    if not digits or n_options < 2:
        return False
    uniq = "".join(sorted(set(digits)))
    if len(uniq) >= n_options:
        return False
    expected = "".join(str(i) for i in range(1, len(uniq) + 1))
    return uniq == expected


def _rewrite_numbered_options(stem: str, items: list[str]) -> str:
    lines = [f"{i}) {txt}" for i, txt in enumerate(items, start=1)]
    stem = (stem or "").rstrip()
    return f"{stem}\n" + "\n".join(lines) if stem else "\n".join(lines)


def _shuffle_matching_payload(
    matching: dict[str, Any],
    answer: str,
    rng: random.Random,
) -> tuple[dict[str, Any], str] | None:
    left = [x for x in (matching.get("left") or []) if isinstance(x, dict)]
    right = [x for x in (matching.get("right") or []) if isinstance(x, dict)]
    if len(left) < 2 or len(right) < 3:
        return None
    old_id_to_text = {str(x.get("id") or "").strip(): str(x.get("text") or "") for x in right}
    ans_digits = [ch for ch in str(answer or "") if ch.isdigit()]
    if len(ans_digits) != len(left):
        return None
    letter_to_text: dict[str, str] = {}
    for i, row in enumerate(left):
        lid = str(row.get("id") or "").strip()
        old_id = ans_digits[i]
        letter_to_text[lid] = old_id_to_text.get(old_id, "")
        if not letter_to_text[lid]:
            return None
    texts = [str(x.get("text") or "") for x in right]
    n = len(texts)
    new_texts = list(texts)
    new_answer = str(answer)
    for _ in range(16):
        order = list(range(n))
        rng.shuffle(order)
        if order == list(range(n)):
            order = order[1:] + order[:1]
        new_texts = [texts[i] for i in order]
        text_to_new: dict[str, str] = {}
        for i, txt in enumerate(new_texts, start=1):
            text_to_new.setdefault(txt, str(i))
        digits: list[str] = []
        ok = True
        for row in left:
            lid = str(row.get("id") or "").strip()
            nid = text_to_new.get(letter_to_text[lid])
            if not nid:
                ok = False
                break
            digits.append(nid)
        if not ok:
            continue
        cand = "".join(digits)
        if cand != "123" and cand != str(answer):
            new_answer = cand
            break
        new_answer = cand
    new_right = [{"id": str(i), "text": txt} for i, txt in enumerate(new_texts, start=1)]
    out = dict(matching)
    out["left"] = left
    out["right"] = new_right
    return out, new_answer


def _shuffle_numbered_choice(
    text: str,
    answer: str,
    rng: random.Random,
) -> tuple[str, str] | None:
    raw = str(text or "").replace("\r\n", "\n")
    found = list(_NUM_OPT_LINE_RE.finditer(raw))
    if len(found) < 3:
        return None
    stem = raw[: found[0].start()].rstrip()
    old_ids = [m.group(1) for m in found]
    items = [m.group(2).strip() for m in found]
    n = len(items)
    correct = [ch for ch in str(answer or "") if ch.isdigit()]
    if not correct or any(c not in old_ids for c in correct):
        return None
    new_items = list(items)
    new_answer = str(answer)
    orig_sorted = "".join(sorted(correct))
    for _ in range(16):
        order = list(range(n))
        rng.shuffle(order)
        if order == list(range(n)):
            order = order[1:] + order[:1]
        new_items = [items[i] for i in order]
        old_to_new = {old_ids[old_i]: str(new_i + 1) for new_i, old_i in enumerate(order)}
        mapped = [old_to_new[c] for c in correct]
        cand = "".join(sorted(mapped, key=lambda x: int(x)))
        if not _is_prefix_digit_key(cand, n) and cand != orig_sorted:
            new_answer = cand
            break
        new_answer = cand
    return _rewrite_numbered_options(stem, new_items), new_answer


def _shuffle_oge_rus_choice_keys(
    tasks: list[dict[str, Any]],
    *,
    rng: random.Random | None = None,
) -> None:
    """Смешать варианты 2/3/4/6/10/11, чтобы ключ не был всегда 123."""
    rnd = rng or random.Random()
    for t in tasks:
        try:
            num = int(t.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        if num not in _OGE_RUS_SHUFFLE_SLOTS:
            continue
        p = dict(t.get("payload") or {}) if isinstance(t.get("payload"), dict) else {}
        answer = str(t.get("answer") or "")
        matching = p.get("matching") if isinstance(p.get("matching"), dict) else None
        if num == 4 and matching:
            shuffled = _shuffle_matching_payload(matching, answer, rnd)
            if shuffled:
                new_m, new_a = shuffled
                p["matching"] = new_m
                p["ui"] = "matching"
                t["answer"] = new_a
                t["acceptable_answers"] = [new_a]
                left_ids = [
                    str(x.get("id") or "") for x in (new_m.get("left") or []) if isinstance(x, dict)
                ]
                hint = " · ".join(
                    f"{lid}→{new_a[i]}" for i, lid in enumerate(left_ids) if i < len(new_a)
                )
                t["solution"] = hint or t.get("solution")
                t["payload"] = p
            continue
        shuffled = _shuffle_numbered_choice(str(t.get("text") or ""), answer, rnd)
        if not shuffled:
            continue
        new_text, new_a = shuffled
        t["text"] = new_text
        t["answer"] = new_a
        t["acceptable_answers"] = [new_a]
        t["solution"] = f"Верно {new_a}."
        t["payload"] = p


def _pick_prototypes(
    db: Session,
    subject_code: str,
    exam_code: str,
    *,
    mode: str | None = None,
    rng: random.Random | None = None,
    difficulty: str | None = None,
) -> list[TaskPrototype]:
    rows = list(
        db.scalars(
            select(TaskPrototype).where(
                TaskPrototype.subject_code == subject_code,
                TaskPrototype.exam_code == exam_code,
            )
        ).all()
    )
    if not rows:
        raise UniversalGenerateError(
            f"Нет прототипов в PostgreSQL для {subject_code}/{exam_code}. "
            "Запустите seed: python -m backend.scripts.seed_all_subjects --reset"
        )

    by_num: dict[int, list[TaskPrototype]] = {}
    for r in rows:
        by_num.setdefault(int(r.task_number), []).append(r)

    slot_cap = _kim_slot_cap(subject_code, exam_code)
    if slot_cap is not None:
        by_num = {n: ps for n, ps in by_num.items() if 1 <= n <= slot_cap}

    require_etalon = (mode or "").strip().lower() == "etalon"
    full_slots = frozenset(range(1, (slot_cap or 0) + 1)) if slot_cap else frozenset()

    # ОГЭ русский: только цельный вариант (не мешать задания разных текстов)
    if subject_code == "russian" and exam_code == "OGE":
        complete = _complete_oge_rus_variant_ids(rows)
        if not complete:
            raise UniversalGenerateError(
                "Нет полных вариантов ОГЭ русский (нужен context_id со слотами 1–13). "
                "Запустите: python -m backend.scripts.import_oge_rus_variants "
                "--json backend/universal/packs/oge_rus/imports/oge_rus_variants_full.json"
            )
        etalon_ids = _etalon_context_ids(
            db, subject_code=subject_code, exam_code=exam_code, candidate_ids=complete
        )
        if not etalon_ids:
            etalon_ids = _proto_etalon_context_ids(rows, complete)
        if require_etalon and not etalon_ids:
            raise UniversalGenerateError(
                "mode=etalon: нет эталонных вариантов ОГЭ русский. "
                "Импорт: python -m backend.scripts.import_fipi_variant "
                "backend/universal/packs/oge_rus/fixtures/etalon/oge_rus_var_kim.etalon.json"
            )
        # Обычная сборка — все полные КИМ (kim/friendship/books/nature/courage).
        # Эталон только при явном mode=etalon, иначе учитель всегда видел один вариант.
        pool = etalon_ids if require_etalon else _prefer_oge_rus_complete(complete)
        if not pool:
            pool = list(complete)
        want = _norm_rus_diff(difficulty)
        text_pool = _filter_ctx_by_diff(pool, want)
        chosen_ctx = (rng or random).choice(text_pool)
        if require_etalon:
            return _pick_from_context(rows, chosen_ctx, slots=OGE_RUS_VARIANT_SLOTS, rng=rng)
        locked = _pick_from_context(rows, chosen_ctx, slots=OGE_RUS_LOCKED_SLOTS, rng=rng)
        free = _pick_oge_rus_pool_slots(rows, want=want, rng=rng or random)
        return sorted(locked + free, key=lambda r: int(r.task_number))

    use_context = subject_code == "math" and exam_code == "OGE"
    context_picked: dict[int, TaskPrototype] = {}
    math_kit: dict[str, str] = {}
    if use_context:
        # Эталон math: только по явному mode=etalon и только NON-stub.
        # Раньше любой etalon_full (в т.ч. oge_math_demo_01) перехватывал
        # обычную генерацию — учитель получал плейсхолдеры вместо банка.
        if full_slots:
            complete_full = filter_out_stub_math_etalon_ids(
                _complete_context_ids(rows, slots=full_slots)
            )
            etalon_full = filter_out_stub_math_etalon_ids(
                _etalon_context_ids(
                    db,
                    subject_code=subject_code,
                    exam_code=exam_code,
                    candidate_ids=complete_full,
                )
            )
            if not etalon_full:
                etalon_full = filter_out_stub_math_etalon_ids(
                    _proto_etalon_context_ids(rows, complete_full)
                )
            if require_etalon:
                if not etalon_full:
                    raise UniversalGenerateError(
                        "mode=etalon: нет реального эталона ОГЭ математика "
                        "(демо-стаб oge_math_demo_01 исключён из пула). "
                        "Соберите обычный вариант без режима эталона — из банка шаблонов."
                    )
                chosen_ctx = (rng or random).choice(etalon_full)
                return _pick_from_context(rows, chosen_ctx, slots=full_slots, rng=rng)

        complete = filter_out_stub_math_etalon_ids(_complete_context_ids(rows))
        if complete:
            # 15 вариантов по сложности: лёгкий / обычный / сложный
            preferred = _prefer_plan_contexts(rows, complete)
            want = _norm_math_diff(difficulty)
            preferred = _filter_math_ctx_by_diff(preferred, want)
            chosen_ctx = (rng or random).choice(preferred)
            math_kit = _oge_math_kit_slots(chosen_ctx)
            for proto in _pick_from_context(rows, chosen_ctx, rng=rng):
                context_picked[int(proto.task_number)] = proto

    if require_etalon:
        raise UniversalGenerateError(
            f"mode=etalon: нет эталонных прототипов для {subject_code}/{exam_code}"
        )

    picked: list[TaskPrototype] = []
    for num in sorted(by_num.keys()):
        if num in context_picked:
            picked.append(context_picked[num])
            continue
        pool = by_num[num]
        # стаб-эталон math никогда не попадает в обычную сборку
        if use_context:
            non_stub = [p for p in pool if not _is_stub_math_proto(p)]
            if non_stub:
                pool = non_stub
        # для слотов 1–5 при наличии контекстов не мешаем «чужие» одиночные прототипы
        if use_context and context_picked and num in OGE_MATH_CONTEXT_SLOTS:
            pool = [p for p in pool if _context_id_of(p) is None] or pool
        with_tpl = [p for p in pool if _has_template(p)]
        candidates = with_tpl or pool
        if use_context:
            real_cands = [p for p in candidates if not _is_stub_math_proto(p)]
            if not real_cands:
                raise UniversalGenerateError(
                    f"Нет реальных шаблонов ОГЭ математика для задания {num} "
                    "(демо-стаб oge_math_demo_01 исключён). Проверьте seed банка."
                )
            candidates = real_cands
            fitted = [p for p in candidates if _math_proto_fits_slot(p)]
            if fitted:
                candidates = fitted
        # 6–19: сначала подтип из комплекта сюжета 1–5, иначе полоса сложности
        kit_hit = False
        if use_context and 6 <= num <= 19 and math_kit:
            want_sub = math_kit.get(str(num), "")
            if want_sub:
                tagged = [p for p in candidates if _math_subtype_of(p) == want_sub]
                if tagged:
                    candidates = tagged
                    kit_hit = True
        if use_context and 6 <= num <= 19 and not kit_hit:
            want = _norm_math_diff(difficulty)
            tagged = [p for p in candidates if _math_diff_of_proto(p) == want]
            if tagged:
                candidates = tagged
        # 23–25: предпочесть прототипы с figure_data / SVG / asset
        if use_context and num in OGE_MATH_GEOMETRY_SLOTS:
            with_fig = [p for p in candidates if _proto_has_attachable_figure(p)]
            if with_fig:
                candidates = with_fig
        chosen = (rng or random).choice(candidates)
        picked.append(chosen)
    return picked


async def _generate_single_task(slot: TaskPrototype) -> dict[str, Any]:
    """Last resort: одно задание по prompt_instruction (не полный вариант)."""
    user = (
        f"subject={slot.subject_code}, exam={slot.exam_code}, "
        f"task_number={slot.task_number}, part={slot.part}, "
        f"title={slot.prototype_title}\n"
        f"Инструкция: {slot.prompt_instruction}\n"
        "Верни только JSON-объект {text, answer, solution}."
    )
    content = await _call_llm(SINGLE_TASK_SYSTEM, user, timeout=SINGLE_TASK_TIMEOUT)
    raw = _extract_json_object(content)
    text = str(raw.get("text") or "").strip()
    answer = str(raw.get("answer") or "").strip()
    if not text or not answer:
        raise UniversalGenerateError(
            f"LLM не смог сгенерировать задание #{slot.task_number} "
            f"({slot.prototype_title}). Добавьте template_text в спеки и пересидте."
        )
    part = int(slot.part)
    sol_raw = raw.get("solution")
    if part == 2:
        solution = str(sol_raw or "").strip() or (
            f"Решение.\nОтвет: {answer}."
        )
    else:
        solution = str(sol_raw).strip() if sol_raw else None
    return {
        "task_number": int(slot.task_number),
        "part": part,
        "prototype_title": slot.prototype_title,
        "text": text,
        "answer": answer,
        "solution": solution,
        "prompt_instruction": slot.prompt_instruction,
        "_from_template": False,
    }


async def _assemble_base_tasks(
    slots: list[TaskPrototype],
    *,
    progress: ProgressFn | None = None,
    context_descs: dict[str, str] | None = None,
    context_meta: dict[str, dict[str, Any]] | None = None,
    subject_code: str | None = None,
    exam_code: str | None = None,
    forbid_llm: bool = False,
) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    missing = 0
    ctx_map = context_descs or {}
    meta_map = context_meta or {}
    for slot in slots:
        if _has_template(slot):
            cid = _context_id_of(slot)
            tasks.append(
                _task_from_proto(
                    slot,
                    context_desc=ctx_map.get(cid) if cid else None,
                    context_meta=meta_map.get(cid) if cid else None,
                    subject_code=subject_code or getattr(slot, "subject_code", None),
                    exam_code=exam_code or getattr(slot, "exam_code", None),
                )
            )
        else:
            if forbid_llm or proto_is_etalon(getattr(slot, "figure_params", None)):
                raise UniversalGenerateError(
                    f"Эталон: нет шаблона для слота #{slot.task_number} "
                    f"({getattr(slot, 'prototype_title', '')}) — LLM запрещён"
                )
            missing += 1
            _progress(
                progress,
                f"нет шаблона для #{slot.task_number} — одиночная генерация (last resort)",
            )
            tasks.append(await _generate_single_task(slot))
    if missing:
        _progress(progress, f"last-resort LLM для слотов без шаблона: {missing}")
    return tasks


async def _vary_batch(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Лёгкая вариация батча; при любой ошибке — исходные задания."""
    payload = []
    for i, q in enumerate(batch):
        item: dict[str, Any] = {
            "i": i,
            "text": q.get("text"),
            "answer": q.get("answer"),
            "part": int(q.get("part") or 1),
            "hint": (q.get("prompt_instruction") or "измени числа, сохрани тип и корректный ответ"),
        }
        if int(q.get("part") or 1) == 2:
            item["solution"] = q.get("solution")
        payload.append(item)

    prompt = (
        "Ниже JSON-массив школьных заданий. Для каждого слегка измени формулировку "
        "и/или числа так, чтобы задание осталось того же типа и сложности. "
        "Пересчитай answer (и solution для part=2), чтобы они были ВЕРНЫМИ для нового условия. "
        "Не меняй тип ответа. Формулы: 3x²−4x+5, √(x+1), [[2|3]]. Без LaTeX.\n"
        "Верни JSON-массив той же длины: "
        "[{\"i\":0,\"text\":\"...\",\"answer\":\"...\""
        ",\"solution\":null_or_string}, ...]\n\n"
        f"{json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        raw = await _call_llm(VARY_SYSTEM, prompt, timeout=45.0)
    except UniversalGenerateError:
        return batch

    arr = _extract_json_array(raw or "")
    if not arr or len(arr) != len(batch):
        return batch

    by_i: dict[int, dict[str, Any]] = {}
    for item in arr:
        if not isinstance(item, dict):
            continue
        try:
            i = int(item.get("i"))
        except (TypeError, ValueError):
            continue
        by_i[i] = item

    out = [dict(q) for q in batch]
    for i, orig in enumerate(batch):
        item = by_i.get(i)
        if not item:
            continue
        candidate = {
            **orig,
            "text": str(item.get("text") or "").strip(),
            "answer": str(item.get("answer") or "").strip(),
        }
        if int(orig.get("part") or 1) == 2:
            sol = str(item.get("solution") or "").strip()
            candidate["solution"] = sol or orig.get("solution")
        if not _looks_valid_varied(orig, candidate):
            continue
        out[i] = candidate
    return out


async def _maybe_vary_tasks(
    tasks: list[dict[str, Any]],
    *,
    vary: bool | None = None,
    progress: ProgressFn | None = None,
) -> list[dict[str, Any]]:
    enabled = _vary_enabled() if vary is None else bool(vary)
    if not tasks or not enabled:
        return tasks

    result = [dict(t) for t in tasks]
    for start in range(0, len(result), VARY_BATCH_SIZE):
        chunk = result[start : start + VARY_BATCH_SIZE]
        _progress(
            progress,
            f"вариация батча {start + 1}–{start + len(chunk)} из {len(result)}",
        )
        varied = await _vary_batch(chunk)
        result[start : start + len(chunk)] = varied
    return result


async def generate_variant(
    subject_code: str,
    exam_code: str,
    *,
    vary: bool | None = None,
    mode: str | None = None,
    difficulty: str | None = None,
    progress: ProgressFn | None = None,
) -> dict[str, Any]:
    """Собрать вариант: шаблоны из PG → опциональная лёгкая вариация → валидация.

    vary: явный флаг с API/UI. Если None — fallback на UNIVERSAL_VARY / BANK_VARY.
    mode: ``etalon`` — только эталонные context/prototype; vary принудительно off.
    """
    if not is_postgres_configured():
        raise UniversalGenerateError(
            "POSTGRES_URL не задан. Добавьте POSTGRES_URL в .env для universal-генерации."
        )

    subject_code = (subject_code or "").strip()
    exam_code = (exam_code or "").strip().upper()
    if not subject_code or not exam_code:
        raise UniversalGenerateError("Нужны subject_code и exam_code")

    mode_norm = (mode or "").strip().lower() or None

    # create_all + ALTER IF NOT EXISTS — чтобы новые колонки (context_id и др.)
    # не валили SELECT на старой БД без отдельной миграции / seed.
    try:
        init_pg_tables()
    except Exception as exc:
        raise UniversalGenerateError(
            f"Не удалось подготовить схему PostgreSQL: {exc}"
        ) from exc

    SessionLocal = session_factory()
    db = SessionLocal()
    try:
        slots = _pick_prototypes(
            db, subject_code, exam_code, mode=mode_norm, difficulty=difficulty
        )
        ctx_ids = {_context_id_of(s) for s in slots if _context_id_of(s)}
        context_meta = _context_meta_map(
            db,
            subject_code=subject_code,
            exam_code=exam_code,
            context_ids=ctx_ids,
        )
        context_descs = {
            cid: str(row.get("story_text") or "").strip()
            for cid, row in context_meta.items()
            if str(row.get("story_text") or "").strip()
        }
        provenance_by_ctx = _context_provenance_map(
            db,
            subject_code=subject_code,
            exam_code=exam_code,
            context_ids=ctx_ids,
        )
        etalon_ctx = filter_out_stub_math_etalon_ids(
            _etalon_context_ids(
                db,
                subject_code=subject_code,
                exam_code=exam_code,
                candidate_ids=sorted(ctx_ids),
            )
        )
    finally:
        db.close()

    is_etalon = bool(etalon_ctx) or any(
        proto_is_etalon(getattr(s, "figure_params", None))
        and not _is_stub_math_proto(s)
        for s in slots
    )
    if mode_norm == "etalon":
        is_etalon = True

    tasks = await _assemble_base_tasks(
        slots,
        progress=progress,
        context_descs=context_descs,
        context_meta=context_meta,
        subject_code=subject_code,
        exam_code=exam_code,
        forbid_llm=is_etalon,
    )
    from_templates = sum(1 for t in tasks if t.get("_from_template"))
    # Эталон: vary запрещён (игнорируем env и явный vary=True)
    if is_etalon:
        vary_on = False
        if vary:
            _progress(progress, "etalon: vary проигнорирован (запрещён)")
    else:
        vary_on = _vary_enabled() if vary is None else bool(vary)
    _progress(
        progress,
        f"собрано из шаблонов: {from_templates}; вариация: {'on' if vary_on else 'off'}"
        + ("; etalon" if is_etalon else ""),
    )

    if vary_on:
        tasks = await _maybe_vary_tasks(tasks, vary=True, progress=progress)

    if subject_code == "math" and exam_code == "OGE" and not is_etalon:
        from backend.services.math_mutator import fill_math_templates

        n_mut = fill_math_templates(tasks, rng=random.Random())
        if n_mut:
            _progress(progress, f"math mutator templates: {n_mut}")

    if subject_code in ("russian", "rus", "ru") and exam_code == "OGE":
        _enrich_oge_rus_shared_across_tasks(tasks)
        _apply_oge_rus_difficulty(tasks, difficulty or "medium")
        if not is_etalon:
            _shuffle_oge_rus_choice_keys(tasks, rng=random.Random())

    payload_tasks = []
    for t in tasks:
        item = {
            "task_number": t["task_number"],
            "part": t["part"],
            "prototype_title": t["prototype_title"],
            "text": t["text"],
            "answer": t["answer"],
            "solution": t.get("solution"),
        }
        if t.get("figure_kind"):
            item["figure_kind"] = t["figure_kind"]
        if t.get("figure_params") is not None:
            item["figure_params"] = t["figure_params"]
        if t.get("figure_data") is not None:
            item["figure_data"] = t["figure_data"]
        if t.get("figure_svg"):
            item["figure_svg"] = t["figure_svg"]
        if t.get("_figure_pack"):
            item["_figure_pack"] = t["_figure_pack"]
        if t.get("context_id"):
            item["context_id"] = t["context_id"]
        if t.get("max_score") is not None:
            item["max_score"] = t["max_score"]
        if t.get("payload") is not None:
            item["payload"] = t["payload"]
        if t.get("acceptable_answers") is not None:
            item["acceptable_answers"] = t["acceptable_answers"]
        if is_etalon or t.get("_etalon"):
            item["etalon"] = True
            cid = t.get("context_id")
            if cid and cid in provenance_by_ctx:
                item["provenance"] = provenance_by_ctx[cid]
                if isinstance(item.get("payload"), dict):
                    item["payload"].setdefault("provenance", provenance_by_ctx[cid])
                    item["payload"]["etalon"] = True
        payload_tasks.append(item)

    ctx_ids = {t.get("context_id") for t in payload_tasks if t.get("context_id")}
    if ctx_ids:
        _progress(progress, f"context_blocks: {', '.join(sorted(ctx_ids))}")

    raw = {
        "subject_code": subject_code,
        "exam_code": exam_code,
        "tasks": payload_tasks,
    }
    expected = [(t["task_number"], t["part"], t["prototype_title"]) for t in payload_tasks]
    try:
        validated = validate_variant_payload(
            raw,
            subject_code=subject_code,
            exam_code=exam_code,
            expected_slots=expected,
        )
    except VariantValidationError as exc:
        raise UniversalGenerateError(f"Валидация варианта: {exc}") from exc
    if subject_code in ("russian", "rus", "ru") and exam_code == "OGE":
        validated["exam_ui"] = "oge_rus_kim"
        _attach_oge_rus_bank(validated, payload_tasks)
    if subject_code == "math" and exam_code == "OGE":
        _attach_oge_math_bank(validated, payload_tasks)
    if is_etalon:
        validated["etalon"] = True
        validated["exam_ui"] = validated.get("exam_ui") or "etalon"
        # единый provenance с первого контекста
        for cid in sorted(ctx_ids):
            if cid in provenance_by_ctx:
                validated["provenance"] = provenance_by_ctx[cid]
                break
        if not validated.get("provenance"):
            for t in payload_tasks:
                if isinstance(t.get("provenance"), dict):
                    validated["provenance"] = t["provenance"]
                    break
    return validated


def _variant_from_template_slots(
    db: Session,
    slots: list[TaskPrototype],
    *,
    subject_code: str,
    exam_code: str,
    difficulty: str | None = None,
    rng: random.Random | None = None,
) -> dict[str, Any] | None:
    """Собрать вариант только из шаблонов PG, без LLM."""
    if not slots:
        return None
    ctx_ids = {_context_id_of(s) for s in slots if _context_id_of(s)}
    context_meta = _context_meta_map(
        db,
        subject_code=subject_code,
        exam_code=exam_code,
        context_ids=ctx_ids,
    )
    context_descs = {
        cid: str(row.get("story_text") or "").strip()
        for cid, row in context_meta.items()
        if str(row.get("story_text") or "").strip()
    }
    tasks: list[dict[str, Any]] = []
    for slot in slots:
        if not _has_template(slot):
            return None
        cid = _context_id_of(slot)
        tasks.append(
            _task_from_proto(
                slot,
                context_desc=context_descs.get(cid) if cid else None,
                context_meta=context_meta.get(cid) if cid else None,
                subject_code=subject_code,
                exam_code=exam_code,
            )
        )
    if subject_code in ("russian", "rus", "ru") and exam_code == "OGE":
        _enrich_oge_rus_shared_across_tasks(tasks)
        _apply_oge_rus_difficulty(tasks, difficulty or "medium")
        _shuffle_oge_rus_choice_keys(tasks, rng=rng)
    if subject_code == "math" and exam_code == "OGE":
        from backend.services.math_mutator import fill_math_templates

        fill_math_templates(tasks, rng=rng or random.Random())
    payload_tasks = []
    for t in tasks:
        item = {
            "task_number": t["task_number"],
            "part": t["part"],
            "prototype_title": t["prototype_title"],
            "text": t["text"],
            "answer": t["answer"],
            "solution": t.get("solution"),
        }
        for key in (
            "figure_kind",
            "figure_params",
            "figure_data",
            "figure_svg",
            "context_id",
            "max_score",
            "payload",
            "acceptable_answers",
        ):
            if t.get(key) is not None:
                item[key] = t[key]
        payload_tasks.append(item)
    raw = {
        "subject_code": subject_code,
        "exam_code": exam_code,
        "tasks": payload_tasks,
    }
    expected = [(t["task_number"], t["part"], t["prototype_title"]) for t in payload_tasks]
    try:
        validated = validate_variant_payload(
            raw,
            subject_code=subject_code,
            exam_code=exam_code,
            expected_slots=expected,
        )
    except VariantValidationError:
        return None
    if subject_code in ("russian", "rus", "ru") and exam_code == "OGE":
        validated["exam_ui"] = "oge_rus_kim"
        _attach_oge_rus_bank(validated, payload_tasks)
    if subject_code == "math" and exam_code == "OGE":
        _attach_oge_math_bank(validated, payload_tasks)
    return validated


def oge_rus_remix_test_for_seed(
    base_questions: list[dict[str, Any]],
    *,
    assignment_id: int,
    student_name: str,
    difficulty: str | None = None,
) -> list[dict[str, Any]] | None:
    """Изложение (1) и сочинение+чтение (10–13) как у учителя.
    Тест 2–9 — те же типы правил, другие формулировки под ученика.
    """
    if not is_postgres_configured():
        return None
    name = str(student_name or "").strip()
    if len(name) < 2:
        return None
    base = [copy.deepcopy(q) for q in (base_questions or []) if isinstance(q, dict)]
    if len(base) < 10:
        return None
    from backend.services.math_mutator import seed_int
    from backend.universal.adapt import universal_variant_to_questions

    rng = random.Random(seed_int(int(assignment_id), name) ^ 0xA11CE)
    SessionLocal = session_factory()
    db = SessionLocal()
    try:
        rows = list(
            db.scalars(
                select(TaskPrototype).where(
                    TaskPrototype.subject_code == "russian",
                    TaskPrototype.exam_code == "OGE",
                )
            ).all()
        )
        if not rows:
            return None
        orig_ctx = ""
        for q in base:
            n = 0
            try:
                n = int(q.get("num") or q.get("task_number") or 0)
            except (TypeError, ValueError):
                n = 0
            if n in (1, 13, 10):
                pl = q.get("payload") if isinstance(q.get("payload"), dict) else {}
                orig_ctx = str(pl.get("context_id") or q.get("context_id") or "").strip()
                if orig_ctx:
                    break
        want = _norm_rus_diff(difficulty)
        picked: list[TaskPrototype] = []
        complete = _complete_oge_rus_variant_ids(rows)
        others = [c for c in complete if c and c != orig_ctx]
        if others:
            grammar_ctx = rng.choice(others)
            try:
                picked.extend(
                    _pick_from_context(rows, grammar_ctx, slots=OGE_RUS_GRAMMAR_SLOTS, rng=rng)
                )
            except UniversalGenerateError:
                picked = [p for p in picked if int(p.task_number) not in OGE_RUS_GRAMMAR_SLOTS]
        try:
            picked.extend(_pick_oge_rus_pool_slots(rows, want=want, rng=rng))
        except UniversalGenerateError:
            pass
        if not picked:
            return None
        variant = _variant_from_template_slots(
            db,
            picked,
            subject_code="russian",
            exam_code="OGE",
            difficulty=difficulty,
            rng=rng,
        )
    except Exception:
        return None
    finally:
        db.close()
    if not variant:
        return None
    alt = universal_variant_to_questions(variant)
    alt_by: dict[int, dict[str, Any]] = {}
    for q in alt or []:
        if not isinstance(q, dict):
            continue
        try:
            n = int(q.get("num") or q.get("task_number") or 0)
        except (TypeError, ValueError):
            continue
        if n in OGE_RUS_STUDENT_REMIX_SLOTS:
            alt_by[n] = q
    if not alt_by:
        return None
    out: list[dict[str, Any]] = []
    for q in base:
        try:
            n = int(q.get("num") or q.get("task_number") or 0)
        except (TypeError, ValueError):
            out.append(q)
            continue
        if n in alt_by:
            repl = copy.deepcopy(alt_by[n])
            orig_text = str(q.get("text") or "").strip()
            if orig_text and orig_text == str(repl.get("text") or "").strip():
                out.append(q)
            else:
                out.append(repl)
        else:
            out.append(q)
    out.sort(key=lambda x: int(x.get("num") or x.get("task_number") or 0))
    return out if len(out) >= 10 else None


def oge_rus_questions_for_seed(
    *,
    assignment_id: int,
    student_name: str,
    difficulty: str | None = None,
) -> list[dict[str, Any]] | None:
    """Устарело: не подменять изложение/сочинение. Оставлено для совместимости."""
    return None
