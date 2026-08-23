"""Эталонный режим: hash, flags, kim_spec helpers (без LLM)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from backend.universal.packs.loader import PACKS_DIR

KIM_SPEC_SLOT_COUNTS: dict[str, int] = {
    "oge_math_2026": 25,
    "oge_rus_2026": 13,
}

SUBJECT_PACK: dict[str, str] = {
    "math": "oge_math",
    "russian": "oge_rus",
    "rus": "oge_rus",
    "ru": "oge_rus",
}


def kim_specs_dir() -> Path:
    return PACKS_DIR / "kim_specs"


def load_kim_spec(kim_spec_id: str) -> dict[str, Any]:
    path = kim_specs_dir() / f"{kim_spec_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"Нет kim_spec: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: ожидался объект")
    return data


def expected_slot_count(kim_spec_id: str, subject_code: str | None = None) -> int:
    if kim_spec_id in KIM_SPEC_SLOT_COUNTS:
        return KIM_SPEC_SLOT_COUNTS[kim_spec_id]
    try:
        spec = load_kim_spec(kim_spec_id)
        n = int(spec.get("slot_count") or len(spec.get("slots") or []))
        if n > 0:
            return n
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass
    sc = (subject_code or "").strip().lower()
    if sc == "math":
        return 25
    if sc in ("russian", "rus", "ru"):
        return 13
    raise ValueError(f"Неизвестная длина КИМ для {kim_spec_id!r} / {subject_code!r}")


def pack_id_for_subject(subject_code: str) -> str:
    sc = (subject_code or "").strip().lower()
    pack = SUBJECT_PACK.get(sc)
    if not pack:
        raise ValueError(f"Эталонный импорт поддерживает только math/russian, не {subject_code!r}")
    return pack


def canonical_content_for_hash(data: dict[str, Any]) -> dict[str, Any]:
    """Канон для content_hash: задания + медиа-метаданные, без imported_at."""
    tasks_out: list[dict[str, Any]] = []
    for t in data.get("tasks") or []:
        if not isinstance(t, dict):
            continue
        payload = t.get("payload") if isinstance(t.get("payload"), dict) else {}
        media = payload.get("media")
        image_urls = payload.get("image_urls")
        tasks_out.append(
            {
                "task_number": int(t.get("task_number") or 0),
                "part": int(t.get("part") or 1),
                "type": t.get("type"),
                "statement": t.get("statement") or "",
                "correct_answer": t.get("correct_answer") or "",
                "max_score": t.get("max_score"),
                "topic": t.get("topic"),
                "figure_kind": t.get("figure_kind"),
                "figure_svg": t.get("figure_svg"),
                "payload": {
                    "image_urls": list(image_urls or []) if isinstance(image_urls, list) else [],
                    "media": media if isinstance(media, list) else [],
                    "matching": payload.get("matching"),
                    "grammar_text": payload.get("grammar_text"),
                    "reading_text": payload.get("reading_text"),
                    "listening_text": payload.get("listening_text"),
                    "essay_options": payload.get("essay_options"),
                    "ui": payload.get("ui"),
                    "kim_type": payload.get("kim_type"),
                },
            }
        )
    tasks_out.sort(key=lambda x: int(x["task_number"]))
    ctx = data.get("context") if isinstance(data.get("context"), dict) else {}
    return {
        "version": data.get("version"),
        "etalon": True,
        "kim_spec_id": data.get("kim_spec_id"),
        "exam_code": data.get("exam_code"),
        "subject_code": data.get("subject_code"),
        "variant_code": data.get("variant_code"),
        "context": {
            "context_id": ctx.get("context_id"),
            "title": ctx.get("title"),
            "description_text": ctx.get("description_text"),
            "etalon": True,
        },
        "tasks": tasks_out,
        "keys": {
            str(t["task_number"]): str(t.get("correct_answer") or "")
            for t in tasks_out
        },
    }


def compute_content_hash(data: dict[str, Any]) -> str:
    canon = canonical_content_for_hash(data)
    blob = json.dumps(canon, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def parse_json_field(raw: Any) -> Any:
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
    if isinstance(parsed, str):
        try:
            return json.loads(parsed)
        except json.JSONDecodeError:
            return None
    return parsed


def context_is_etalon(figure_params: Any) -> bool:
    params = parse_json_field(figure_params)
    return isinstance(params, dict) and bool(params.get("etalon"))


def proto_is_etalon(figure_params: Any) -> bool:
    return context_is_etalon(figure_params)


# Демо-стаб oge_math_demo_01: плейсхолдеры «Эталонное задание…», не реальный банк.
# Нельзя отдавать учителю ни в default generate, ни как mode=etalon.
MATH_STUB_ETALON_CONTEXT_IDS: frozenset[str] = frozenset(
    {
        "etalon_oge_math_demo_01",
    }
)
MATH_STUB_ETALON_VARIANT_CODES: frozenset[str] = frozenset(
    {
        "oge_math_demo_01",
    }
)
_MATH_STUB_TEXT_MARKER = "Эталонное задание ОГЭ математика"


def is_stub_math_etalon_context(context_id: str | None) -> bool:
    cid = str(context_id or "").strip()
    return bool(cid) and cid in MATH_STUB_ETALON_CONTEXT_IDS


def is_stub_math_etalon_variant(variant_code: str | None) -> bool:
    vc = str(variant_code or "").strip()
    return bool(vc) and vc in MATH_STUB_ETALON_VARIANT_CODES


def figure_params_is_stub_math_etalon(figure_params: Any) -> bool:
    """True для демо-стаба math (context/variant/текст-маркер)."""
    params = parse_json_field(figure_params)
    if not isinstance(params, dict):
        return False
    if is_stub_math_etalon_variant(str(params.get("variant_code") or "")):
        return True
    prov = params.get("provenance")
    if isinstance(prov, dict) and is_stub_math_etalon_variant(
        str(prov.get("variant_code") or "")
    ):
        return True
    nested = params.get("payload") if isinstance(params.get("payload"), dict) else {}
    if isinstance(nested, dict):
        nprov = nested.get("provenance")
        if isinstance(nprov, dict) and is_stub_math_etalon_variant(
            str(nprov.get("variant_code") or "")
        ):
            return True
    return False


def text_is_stub_math_etalon(text: str | None) -> bool:
    return _MATH_STUB_TEXT_MARKER in str(text or "")


def filter_out_stub_math_etalon_ids(context_ids: list[str]) -> list[str]:
    return [c for c in context_ids if not is_stub_math_etalon_context(c)]


def resolve_pack_asset_url(pack_id: str, rel_path: str) -> str:
    """Относительный путь в паке → URL /packs/<pack>/..."""
    rel = (rel_path or "").strip().replace("\\", "/")
    if not rel:
        return ""
    if rel.startswith("/packs/") or rel.startswith("http://") or rel.startswith("https://"):
        return rel
    if rel.startswith("assets/"):
        return f"/packs/{pack_id}/{rel}"
    return f"/packs/{pack_id}/{rel.lstrip('/')}"


def normalize_image_urls(pack_id: str, urls: list[Any] | None) -> list[str]:
    out: list[str] = []
    for u in urls or []:
        s = resolve_pack_asset_url(pack_id, str(u or ""))
        if s:
            out.append(s)
    return out
