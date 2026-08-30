from pathlib import Path
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from backend.database import Base, SessionLocal, engine, ensure_sqlite_columns
from backend import models  # noqa: F401 — register ORM tables (incl. bank_tasks)
from backend.db.pg import init_pg_tables, is_postgres_configured
from backend.routes import (
    ai,
    analytics,
    assignments,
    auth,
    bank,
    class_create,
    classes,
    grade_part2,
    roster,
    student,
    tasks,
    universal,
)
from backend.services.bank import ensure_bank_seeded
from backend.services.session_tokens import warn_if_insecure_secret

# Optional: reserved for Telegram WebApp initData validation (not required for UI)
TELEGRAM_BOT_TOKEN = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()

warn_if_insecure_secret()

# Create tables (legacy + EduSense core + bank_tasks)
Base.metadata.create_all(bind=engine)
# Soft-migrate новых колонок assignments / submissions на уже существующей SQLite БД
ensure_sqlite_columns()

# PostgreSQL universal: create_all + soft-migrate новых колонок (context_id и т.п.)
if is_postgres_configured():
    try:
        init_pg_tables()
    except Exception:
        # PG недоступен при старте — generate вернёт понятную ошибку позже
        pass

# Сид проверенного банка заданий при старте
_db = SessionLocal()
try:
    ensure_bank_seeded(_db)
finally:
    _db.close()

app = FastAPI(title="EduSense API", version="1.2.0")


class NoCacheStaticMiddleware(BaseHTTPMiddleware):
    """Dev: не кэшировать JS/CSS — иначе UI-правки «не видны» после refresh."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        path = request.url.path or ""
        if path.startswith("/js/") or path.startswith("/css/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        return response


app.add_middleware(NoCacheStaticMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(classes.router)
app.include_router(roster.router)
app.include_router(analytics.router)
app.include_router(class_create.router)
app.include_router(ai.router)
app.include_router(bank.router)
app.include_router(assignments.router)
app.include_router(student.router)
app.include_router(universal.router)
app.include_router(tasks.router)
app.include_router(grade_part2.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
PACKS_DIR = Path(__file__).resolve().parent / "universal" / "packs"


@app.get("/manifest.json")
def serve_manifest():
    return FileResponse(
        FRONTEND_DIR / "manifest.json",
        media_type="application/manifest+json",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/sw.js")
def serve_service_worker():
    return FileResponse(
        FRONTEND_DIR / "sw.js",
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache",
            "Service-Worker-Allowed": "/",
        },
    )


@app.get("/install")
def serve_install():
    return FileResponse(FRONTEND_DIR / "install.html")


@app.get("/updates")
@app.get("/news")
def serve_updates():
    return FileResponse(FRONTEND_DIR / "updates.html")


@app.get("/shortcut")
def serve_shortcut(request: Request):
    """Windows internet shortcut — всегда кладёт файл в «Загрузки» браузера."""
    home = str(request.base_url)
    body = "[InternetShortcut]\r\nURL=" + home + "\r\n"
    return Response(
        content=body,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="EduSense.url"',
            "Cache-Control": "no-store",
        },
    )


@app.get("/")
def serve_index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/teacher")
def serve_teacher():
    return FileResponse(FRONTEND_DIR / "teacher.html")


@app.get("/teacher/{rest:path}")
def serve_teacher_spa(rest: str):
    return FileResponse(FRONTEND_DIR / "teacher.html")


@app.get("/student")
@app.get("/student/join")
@app.get("/student/dashboard")
def serve_student():
    return FileResponse(FRONTEND_DIR / "student.html")


@app.get("/student/work/{code}")
def serve_student_work(code: str):
    return FileResponse(FRONTEND_DIR / "student.html")


@app.get("/student/{rest:path}")
def serve_student_spa(rest: str):
    return FileResponse(FRONTEND_DIR / "student.html")


@app.get("/task-demo")
def serve_task_demo():
    raise HTTPException(status_code=404, detail="Not found")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "edusense",
        "telegram_token_configured": bool(TELEGRAM_BOT_TOKEN),
    }


app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
# Учебные MP3 изложения ОГЭ русский (TTS): /audio/oge_rus/<variant>.mp3
_AUDIO_DIR = FRONTEND_DIR / "audio"
_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=_AUDIO_DIR), name="audio")
# Pack assets (OGE math part2 figures и т.п.): /packs/oge_math/assets/...
if PACKS_DIR.is_dir():
    app.mount("/packs", StaticFiles(directory=PACKS_DIR), name="packs")

_SPA_SKIP_PREFIXES = (
    "/api/",
    "/css/",
    "/js/",
    "/assets/",
    "/audio/",
    "/packs/",
    "/docs",
    "/redoc",
    "/openapi.json",
)


@app.exception_handler(StarletteHTTPException)
async def spa_http_exception(request: Request, exc: StarletteHTTPException):
    """HTML fallback: reload /student/work/... must not return JSON 404."""
    if exc.status_code != 404:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    path = request.url.path or ""
    if any(path.startswith(p) for p in _SPA_SKIP_PREFIXES):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    if request.method not in ("GET", "HEAD"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    accept = (request.headers.get("accept") or "").lower()
    if "text/html" not in accept and "*/*" not in accept and accept:
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    if path.startswith("/teacher"):
        page = FRONTEND_DIR / "teacher.html"
    elif path.startswith("/student"):
        page = FRONTEND_DIR / "student.html"
    else:
        page = FRONTEND_DIR / "index.html"
    if page.is_file():
        return FileResponse(page)
    return JSONResponse({"detail": "Not Found"}, status_code=404)
