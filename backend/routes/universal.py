"""API универсальной PostgreSQL-генерации вариантов."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.db.pg import is_postgres_configured
from backend.universal.variant_builder import UniversalGenerateError, generate_variant

router = APIRouter(prefix="/api/universal", tags=["universal"])


class UniversalGenerateRequest(BaseModel):
    subject_code: str = Field(..., examples=["math"])
    exam_code: str = Field(..., examples=["OGE"])
    vary: bool | None = None
    mode: str | None = Field(None, examples=["etalon"])
    difficulty: str | None = Field(None, examples=["easy", "medium", "hard"])


@router.get("/health")
def universal_health() -> dict[str, Any]:
    ok = is_postgres_configured()
    return {
        "ok": ok,
        "postgres_configured": ok,
        "message": None
        if ok
        else "POSTGRES_URL не задан — universal API недоступен (503 на /generate)",
    }


class OgeRusAutogenRequest(BaseModel):
    tema: str | None = None
    count: int = Field(1, ge=1, le=3)


@router.post("/oge-rus/autogen")
async def oge_rus_autogen(payload: OgeRusAutogenRequest) -> dict[str, Any]:
    """Оригинальный вариант в банк (не сборка экзамена). 1–2 минуты."""
    if not is_postgres_configured():
        raise HTTPException(status_code=503, detail="POSTGRES_URL не задан")
    from backend.services.oge_rus_autogen import autogen_many

    try:
        result = await autogen_many(payload.count, tema=payload.tema)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not result.get("ok"):
        raise HTTPException(
            status_code=502,
            detail="; ".join(result.get("errors") or ["не удалось собрать вариант"]),
        )
    return result


@router.post("/generate")
async def universal_generate(payload: UniversalGenerateRequest) -> dict[str, Any]:
    if not is_postgres_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "POSTGRES_URL не задан. Добавьте в .env, например: "
                "POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:5432/edusense_universal"
            ),
        )
    try:
        return await generate_variant(
            payload.subject_code,
            payload.exam_code,
            vary=payload.vary,
            mode=payload.mode,
            difficulty=payload.difficulty,
        )
    except UniversalGenerateError as exc:
        msg = str(exc)
        if "POSTGRES_URL" in msg:
            raise HTTPException(status_code=503, detail=msg) from exc
        if "Нет прототипов" in msg or "mode=etalon" in msg:
            raise HTTPException(status_code=404, detail=msg) from exc
        raise HTTPException(status_code=502, detail=msg) from exc
