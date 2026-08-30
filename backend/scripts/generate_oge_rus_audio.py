"""Сгенерировать MP3 для изложения ОГЭ русский (edge-tts) и проставить audio_url.

Официальное аудио ФИПИ не распространяется. Здесь — учебный TTS по listening_text.

Пример:
  pip install edge-tts
  python -m backend.scripts.generate_oge_rus_audio
  python -m backend.scripts.generate_oge_rus_audio --seed-pg

Файлы: frontend/audio/oge_rus/<context_id>.mp3
URL:   /audio/oge_rus/<context_id>.mp3
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

AUDIO_DIR = _ROOT / "frontend" / "audio" / "oge_rus"
CTX_DIR = _ROOT / "backend" / "universal" / "packs" / "oge_rus" / "context_blocks"
IMPORTS_DIR = _ROOT / "backend" / "universal" / "packs" / "oge_rus" / "imports"
VOICE = "ru-RU-DmitryNeural"
# Альтернатива: ru-RU-SvetlanaNeural


def _slug(cid: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_\-]+", "_", cid.strip())
    return s or "oge_rus"


def _listening_from_block(block: dict[str, Any]) -> str:
    for task in block.get("tasks") or []:
        if int(task.get("task_number") or 0) != 1:
            continue
        fp = task.get("figure_params") if isinstance(task.get("figure_params"), dict) else {}
        text = str(fp.get("listening_text") or "").strip()
        if text:
            return text
    return str(block.get("audio_script") or "").strip()


def _gtts_sync(text: str, out_path: Path) -> bool:
    """gTTS → MP3 (нужен интернет)."""
    try:
        from gtts import gTTS  # type: ignore
    except ImportError:
        print("gTTS not installed (pip install gTTS)")
        return False
    try:
        tts = gTTS(text=text, lang="ru")
        tts.save(str(out_path))
        return out_path.is_file() and out_path.stat().st_size > 1000
    except Exception as exc:
        print(f"gTTS failed: {type(exc).__name__}: {exc}")
        return False


async def _synth(text: str, out_path: Path, *, voice: str = VOICE) -> tuple[bool, str]:
    """edge-tts (MP3 neural) → gTTS (MP3) → pyttsx3 (WAV last resort).

    Returns (ok, engine_name).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # убрать битый пустой файл от прошлого прогона
    if out_path.is_file() and out_path.stat().st_size < 500:
        try:
            out_path.unlink()
        except OSError:
            pass

    # 1) Microsoft Edge neural TTS
    # aiohttp+aiodns таймаутит DNS на Windows — подменяем DefaultResolver в connector
    try:
        from aiohttp.resolver import ThreadedResolver  # type: ignore
        import aiohttp.resolver as _ares  # type: ignore
        import aiohttp.connector as _aconn  # type: ignore

        _ares.DefaultResolver = ThreadedResolver  # type: ignore[attr-defined,misc]
        _aconn.DefaultResolver = ThreadedResolver  # type: ignore[attr-defined,misc]
    except Exception:
        pass
    try:
        import edge_tts  # type: ignore

        communicate = edge_tts.Communicate(text, voice, rate="-10%")
        await communicate.save(str(out_path))
        if out_path.is_file() and out_path.stat().st_size > 1000:
            # убрать старый robotic wav, если был
            wav_old = out_path.with_suffix(".wav")
            if wav_old.is_file():
                try:
                    wav_old.unlink()
                except OSError:
                    pass
            return True, f"edge-tts:{voice}"
    except Exception as exc:
        print(f"edge-tts unavailable: {type(exc).__name__}: {exc}")

    # 2) gTTS → настоящий MP3
    if await asyncio.to_thread(_gtts_sync, text, out_path):
        return True, "gTTS"

    # 3) Offline robotic fallback (WAV) — только если совсем нет сети
    wav_path = out_path.with_suffix(".wav")
    try:
        import pyttsx3  # type: ignore

        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.save_to_file(text, str(wav_path))
        engine.runAndWait()
        if wav_path.is_file() and wav_path.stat().st_size > 1000:
            if out_path.is_file():
                try:
                    out_path.unlink()
                except OSError:
                    pass
            return True, "pyttsx3-wav"
    except Exception as exc:
        print(f"pyttsx3 unavailable: {type(exc).__name__}: {exc}")
    return False, "none"


def _audio_url_for(path: Path, cid: str, engine: str = "") -> str:
    slug = _slug(cid)
    if engine == "pyttsx3-wav" or (
        path.with_suffix(".wav").is_file()
        and (not path.is_file() or path.stat().st_size < 500)
    ):
        return f"/audio/oge_rus/{slug}.wav"
    return f"/audio/oge_rus/{slug}.mp3"


def _set_audio_url_on_block(block: dict[str, Any], url: str) -> None:
    for task in block.get("tasks") or []:
        if int(task.get("task_number") or 0) != 1:
            continue
        fp = task.get("figure_params")
        if not isinstance(fp, dict):
            fp = {"oge_rus": True, "kim_type": 1, "ui": "listening"}
            task["figure_params"] = fp
        fp["audio_url"] = url
        fp.setdefault("tts_fallback", True)
        fp.setdefault("listen_twice", True)


def _patch_import_listening(path: Path, url: str) -> None:
    if not path.is_file():
        return
    raw = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    if isinstance(raw.get("listening_text"), dict):
        raw["listening_text"]["audio_url"] = url
        changed = True
    if "variants" in raw and isinstance(raw["variants"], list):
        for var in raw["variants"]:
            if isinstance(var.get("listening_text"), dict):
                var["listening_text"]["audio_url"] = url
                changed = True
    if changed:
        path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _seed_pg(context_id: str, url: str) -> None:
    from backend.db.pg import is_postgres_configured, session_factory
    from backend.universal.models import TaskPrototype
    from sqlalchemy import select

    if not is_postgres_configured():
        print("PG не настроен — пропуск seed")
        return
    SessionLocal = session_factory()
    db = SessionLocal()
    try:
        # Все задачи полного варианта: audio_url нужен на №1 и для enrich shared
        rows = list(
            db.scalars(
                select(TaskPrototype).where(
                    TaskPrototype.subject_code == "russian",
                    TaskPrototype.exam_code == "OGE",
                    TaskPrototype.context_id == context_id,
                )
            ).all()
        )
        updated = 0
        for row in rows:
            raw = row.figure_params
            params: dict[str, Any]
            if isinstance(raw, dict):
                params = dict(raw)
            elif isinstance(raw, str) and raw.strip():
                try:
                    params = json.loads(raw)
                except json.JSONDecodeError:
                    params = {"oge_rus": True}
            else:
                params = {"oge_rus": True}
            # На №1 всегда; на остальных — если уже было поле или listening
            tn = int(row.task_number or 0)
            if tn == 1 or params.get("audio_url") or params.get("listening_text"):
                params["audio_url"] = url
                params.setdefault("oge_rus", True)
                if tn == 1:
                    params.setdefault("ui", "listening")
                row.figure_params = json.dumps(params, ensure_ascii=False)
                updated += 1
        db.commit()
        print(f"PG updated audio_url for {context_id}: {updated}/{len(rows)} row(s)")
    finally:
        db.close()


async def run(*, seed_pg: bool, voice: str, only: list[str] | None = None, force: bool = False) -> int:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    skip = {
        "oge_rus_var_01.json",
        "oge_rus_var_02.json",
        "oge_rus_var_03.json",
        "oge_rus_var_04.json",
        "oge_rus_var_05.json",
        "oge_rus_var_a.json",
        "etalon_oge_rus_var_kim.json",
    }
    only_set = {str(x).strip() for x in (only or []) if str(x).strip()}
    blocks = sorted(
        p
        for p in CTX_DIR.glob("oge_rus_var_*.json")
        if p.name not in skip
    )
    if only_set:
        blocks = [p for p in blocks if p.stem in only_set]
    if not blocks:
        print("Нет context_blocks")
        return 1
    ok = 0
    for path in blocks:
        block = json.loads(path.read_text(encoding="utf-8"))
        cid = str(block.get("context_id") or path.stem)
        text = _listening_from_block(block)
        if len(text) < 40:
            print(f"skip {cid}: no listening_text")
            continue
        mp3 = AUDIO_DIR / f"{_slug(cid)}.mp3"
        wav = mp3.with_suffix(".wav")
        existing = None
        for cand in (mp3, wav):
            try:
                if cand.is_file() and cand.stat().st_size > 1000:
                    existing = cand
                    break
            except OSError:
                continue
        if existing and not force:
            url = _audio_url_for(existing, cid, engine="existing")
            print(f"skip {cid}: already {existing.name} ({existing.stat().st_size} bytes)")
            if seed_pg:
                _seed_pg(cid, url)
            ok += 1
            continue
        print(f"TTS {cid} -> {mp3.name} (voice={voice}) ...")
        ok_synth, engine = await _synth(text, mp3, voice=voice)
        if not ok_synth:
            print(f"FAIL {cid}")
            continue
        url = _audio_url_for(mp3, cid, engine=engine)
        size = 0
        for cand in (mp3, mp3.with_suffix(".wav")):
            if cand.is_file():
                size = max(size, cand.stat().st_size)
        _set_audio_url_on_block(block, url)
        path.write_text(json.dumps(block, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        imp = IMPORTS_DIR / f"{cid}.json"
        _patch_import_listening(imp, url)
        _patch_import_listening(IMPORTS_DIR / "oge_rus_variants_full.json", url)
        if seed_pg:
            _seed_pg(cid, url)
        ok += 1
        print(f"OK {cid} via {engine} ({size} bytes) {url}")
    print(f"done: {ok}/{len(blocks)}")
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description="OGE rus listening TTS → MP3")
    ap.add_argument("--seed-pg", action="store_true", help="Обновить figure_params в PostgreSQL")
    ap.add_argument("--voice", default=VOICE)
    ap.add_argument("--only", action="append", default=[], help="Только эти context_id (можно несколько)")
    ap.add_argument("--force", action="store_true", help="Перезаписать существующие файлы")
    args = ap.parse_args()
    return asyncio.run(
        run(
            seed_pg=bool(args.seed_pg),
            voice=str(args.voice),
            only=list(args.only or []),
            force=bool(args.force),
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
