import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.deps.auth import require_teacher, require_teacher_or_student
from backend.models import User
from backend.db.pg import is_postgres_configured
from backend.schemas.edu import AiGenerateRequest, AiGenerateResponse, QuestionOut
from backend.services.bank import bank_stats, ensure_bank_seeded
from backend.services.llm import LLMError, enrich_bank_from_ai
from backend.services.prompts import recommended_count
from backend.services.subject_blueprints import kim_slots
from backend.universal.adapt import pg_has_ready_templates, universal_variant_to_questions
from backend.universal.codes import map_teacher_to_universal
from backend.universal.variant_builder import UniversalGenerateError, generate_variant

router = APIRouter(prefix="/api/ai", tags=["ai"])

_NO_TEMPLATES = "Нет шаблонов для этого предмета/экзамена"


@router.get("/provider")
def ai_provider():
    return {"provider": os.getenv("AI_PROVIDER", "gigachat").strip().lower() or "gigachat"}


@router.get("/bank/stats")
def ai_bank_stats(db: Session = Depends(get_db)):
    return bank_stats(db)


@router.post("/enrich")
async def ai_enrich(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    _user: User = Depends(require_teacher),
):
    """Внутреннее пополнение банка кандидатами LLM (без «банк» в UI)."""
    exam = str(payload.get("exam") or "")
    subject = str(payload.get("subject") or "")
    if not exam or not subject:
        raise HTTPException(status_code=400, detail="Нужны exam и subject")
    slots = payload.get("slots")
    if not slots:
        slots = kim_slots(exam=exam, subject=subject, count=None)
    difficulty = str(payload.get("difficulty") or "medium")
    per_slot = int(payload.get("per_slot") or 2)
    ensure_bank_seeded(db)
    try:
        result = await enrich_bank_from_ai(
            db,
            exam=exam,
            subject=subject,
            slots=[int(s) for s in slots],
            difficulty=difficulty,
            per_slot=per_slot,
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"ok": True, "message": "Материалы для варианта подготовлены", **result}


def _user_message(filled: int, requested: int) -> str:
    if filled <= 0:
        return "Не удалось собрать вариант"
    if filled < requested:
        return f"Вариант собран ({filled} из {requested} заданий)"
    return "Вариант собран"


@router.post("/generate", response_model=AiGenerateResponse)
async def ai_generate(
    payload: AiGenerateRequest,
    _user: User = Depends(require_teacher),
):
    """Сборка варианта только из PostgreSQL-шаблонов (SQLite-банк не используется).

    AI = опциональная лёгкая вариация формулировок (`vary`, по умолчанию false).
    """
    # полный КИМ по умолчанию; старый «тест на ≤4» поднимаем до нормы предмета
    if payload.count is None or payload.count <= 4:
        count = recommended_count(payload.exam, payload.subject)
    else:
        count = int(payload.count)

    if not is_postgres_configured():
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL не настроен. Нужен POSTGRES_URL для сборки вариантов.",
        )

    mapped = map_teacher_to_universal(payload.exam, payload.subject)
    if not mapped:
        raise HTTPException(status_code=422, detail=_NO_TEMPLATES)

    subject_code, exam_code = mapped
    if not pg_has_ready_templates(subject_code, exam_code):
        # Частая причина: сервис без POSTGRES_URL или пустой банк
        detail = (
            f"{_NO_TEMPLATES} ({subject_code}/{exam_code}). "
            "Проверьте POSTGRES_URL в .env и seed банка на сервере."
        )
        raise HTTPException(status_code=404, detail=detail)

    mode = getattr(payload, "mode", None)
    is_etalon_req = (mode or "").strip().lower() == "etalon"
    try:
        variant = await generate_variant(
            subject_code,
            exam_code,
            vary=False if is_etalon_req else bool(payload.vary),
            mode=mode,
            difficulty=payload.difficulty,
        )
        slot_list = None
        if getattr(payload, "slots", None):
            try:
                slot_list = sorted({int(s) for s in payload.slots if int(s) > 0})
            except (TypeError, ValueError):
                slot_list = None
            if slot_list:
                count = None
        questions = universal_variant_to_questions(
            variant, count=count, slots=slot_list
        )
    except UniversalGenerateError as exc:
        msg = str(exc)
        # Не прячем причину — иначе на проде всегда одно «Нет шаблонов»
        code = 404 if (
            "Нет прототипов" in msg
            or "шаблон" in msg.lower()
            or "mode=etalon" in msg
            or "POSTGRES_URL" in msg
        ) else 502
        raise HTTPException(status_code=code, detail=msg) from exc
    except HTTPException:
        raise
    except Exception as exc:
        # Необработанные сбои (SQL/фигуры/адаптер) → 502 с текстом, не сырой 500
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка сборки варианта: {exc}",
        ) from exc

    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"Сборка вернула 0 заданий ({subject_code}/{exam_code})",
        )

    try:
        out_questions = [
            QuestionOut(**{k: v for k, v in q.items() if k != "_slot"}) for q in questions
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Некорректный формат заданий: {exc}",
        ) from exc

    exam_ui = None
    if subject_code in ("russian", "rus", "ru") and exam_code == "OGE":
        exam_ui = "oge_rus_kim"
        for q in out_questions:
            p = dict(q.payload or {})
            p.setdefault("oge_rus", True)
            p.setdefault("ui", p.get("ui") or "oge_rus")
            q.payload = p
    elif subject_code in ("math", "math_base"):
        # Жёсткая изоляция: math никогда не несёт oge_rus UI/тексты
        exam_ui = None
        for q in out_questions:
            if not q.payload:
                continue
            p = dict(q.payload)
            for key in (
                "oge_rus",
                "grammar_text",
                "listening_text",
                "reading_text",
                "essay_options",
                "matching",
            ):
                p.pop(key, None)
            if p.get("ui") in ("oge_rus", "listening", "essay_choice", "matching"):
                p.pop("ui", None)
            q.payload = p or None

    etalon = bool(variant.get("etalon"))
    provenance = variant.get("provenance") if isinstance(variant.get("provenance"), dict) else None
    bank = variant.get("bank") if isinstance(variant.get("bank"), dict) else None
    variant_label = str(variant.get("variant_label") or "").strip() or None
    if not variant_label and bank:
        variant_label = str(bank.get("label") or "").strip() or None
    bank_code = str((bank or {}).get("code") or "").strip() or None
    if etalon:
        # etalon ≠ oge_rus_kim; для русского exam_ui уже oge_rus_kim
        if exam_ui != "oge_rus_kim":
            exam_ui = "etalon"
        msg = "Эталонный вариант"
        if provenance and provenance.get("year"):
            msg = f"Эталонный вариант · {provenance.get('year')}"
        if provenance and provenance.get("variant_code"):
            msg = f"{msg} · {provenance.get('variant_code')}"
        if variant_label:
            msg = f"{msg} · {variant_label}"
    elif variant_label:
        msg = (
            f"{variant_label}. "
            f"Чтобы указать ошибку, напишите: {variant_label.split(' · ')[0]}, задание 11"
        )
    else:
        msg = _user_message(len(questions), count)

    return AiGenerateResponse(
        exam=payload.exam,
        subject=payload.subject,
        difficulty=payload.difficulty,
        questions=out_questions,
        source="hybrid",
        message=msg,
        bank_stats={
            "requested": count,
            "filled": len(questions),
            "via": "universal",
            "vary": False if etalon else bool(payload.vary),
            "etalon": etalon,
        },
        exam_ui=exam_ui,
        etalon=etalon,
        provenance=provenance,
        variant_label=variant_label,
        bank_code=bank_code,
        bank=bank,
    )
